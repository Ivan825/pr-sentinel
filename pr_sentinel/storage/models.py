from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pr_sentinel.storage.database import Base

JSON_VARIANT = JSON().with_variant(JSONB, "postgresql")


class RepositoryRecord(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    default_branch: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    analyses: Mapped[list["AnalysisRecord"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )


class AnalysisRecord(Base):
    __tablename__ = "analyses"
    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "pr_number",
            "head_branch",
            "created_at",
            name="uq_analysis_repo_pr_head_created",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), nullable=False)

    pr_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    pr_title: Mapped[str] = mapped_column(String(500), nullable=False)
    pr_author: Mapped[str] = mapped_column(String(255), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    head_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    html_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    findings_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    test_recommendations_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deterministic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_adjustment: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    risk_band: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    raw_result: Mapped[dict[str, object]] = mapped_column(JSON_VARIANT, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    repository: Mapped[RepositoryRecord] = relationship(back_populates="analyses")
    findings: Mapped[list["FindingRecord"]] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
    )


class FindingRecord(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id"), nullable=False)

    rule_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="DETERMINISTIC")

    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    analysis: Mapped[AnalysisRecord] = relationship(back_populates="findings")