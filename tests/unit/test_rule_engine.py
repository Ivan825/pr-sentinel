from pr_sentinel.core.enums import FileCategory, FileChangeStatus
from pr_sentinel.core.models import ChangedFile, DiffHunk, DiffLine, PullRequestInfo
from pr_sentinel.engine.pipeline import AnalysisPipeline


def _make_pr_with_file(changed_file: ChangedFile) -> PullRequestInfo:
    return PullRequestInfo(
        repo_full_name="example/repo",
        pr_number=1,
        title="Risky PR",
        author="ivan",
        base_branch="main",
        head_branch="feature",
        html_url="https://github.com/example/repo/pull/1",
        changed_files=[changed_file],
    )


def test_hardcoded_secret_rule_detects_added_github_token() -> None:
    changed_file = ChangedFile(
        filename="src/config.ts",
        status=FileChangeStatus.MODIFIED,
        additions=1,
        deletions=0,
        changes=1,
        language="TypeScript",
        categories=[FileCategory.CONFIG],
        hunks=[
            DiffHunk(
                old_start=1,
                old_count=0,
                new_start=1,
                new_count=1,
                lines=[
                    DiffLine(
                        old_line_no=None,
                        new_line_no=1,
                        content='const token = "ghp_abcdefghijklmnopqrstuvwxyz123456";',
                        line_type="added",
                    )
                ],
            )
        ],
    )

    result = AnalysisPipeline().analyze(_make_pr_with_file(changed_file))

    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "SEC_001_HARDCODED_SECRET"
    assert result.findings[0].source == "DETERMINISTIC"
    assert result.risk_score is not None
    assert result.risk_score.score > 0


def test_permission_check_removed_rule_detects_deleted_auth_line() -> None:
    changed_file = ChangedFile(
        filename="src/main/java/com/app/security/AuthFilter.java",
        status=FileChangeStatus.MODIFIED,
        additions=0,
        deletions=1,
        changes=1,
        language="Java",
        categories=[FileCategory.AUTH, FileCategory.SECURITY, FileCategory.BACKEND],
        hunks=[
            DiffHunk(
                old_start=20,
                old_count=1,
                new_start=20,
                new_count=0,
                lines=[
                    DiffLine(
                        old_line_no=20,
                        new_line_no=None,
                        content=(
                            "if (!hasPermission(user, resource)) "
                            "throw new ForbiddenException();"
                        ),
                        line_type="deleted",
                    )
                ],
            )
        ],
    )

    result = AnalysisPipeline().analyze(_make_pr_with_file(changed_file))
    rule_ids = {finding.rule_id for finding in result.findings}

    assert "AUTH_001_PERMISSION_CHECK_REMOVED" in rule_ids
    assert "TEST_001_RISKY_SOURCE_WITHOUT_MATCHING_TEST" in rule_ids
    assert all(finding.source == "DETERMINISTIC" for finding in result.findings)


def test_dependency_file_changed_rule_detects_package_json_change() -> None:
    changed_file = ChangedFile(
        filename="package.json",
        status=FileChangeStatus.MODIFIED,
        additions=3,
        deletions=1,
        changes=4,
        language="JSON",
        categories=[FileCategory.DEPENDENCY],
        hunks=[],
    )

    result = AnalysisPipeline().analyze(_make_pr_with_file(changed_file))

    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "DEP_001_DEPENDENCY_FILE_CHANGED"
    assert result.findings[0].source == "DETERMINISTIC"


def test_cors_wildcard_rule_detects_added_wildcard_origin() -> None:
    changed_file = ChangedFile(
        filename="src/main/resources/application.yml",
        status=FileChangeStatus.MODIFIED,
        additions=1,
        deletions=0,
        changes=1,
        language="YAML",
        categories=[FileCategory.CONFIG],
        hunks=[
            DiffHunk(
                old_start=10,
                old_count=0,
                new_start=10,
                new_count=1,
                lines=[
                    DiffLine(
                        old_line_no=None,
                        new_line_no=10,
                        content="allowed-origins: '*'",
                        line_type="added",
                    )
                ],
            )
        ],
    )

    result = AnalysisPipeline().analyze(_make_pr_with_file(changed_file))

    assert len(result.findings) == 1
    assert result.findings[0].rule_id == "CFG_001_CORS_WILDCARD_ENABLED"


def test_raw_sql_concatenation_rule_detects_added_query_concat() -> None:
    changed_file = ChangedFile(
        filename="src/main/java/com/app/UserRepository.java",
        status=FileChangeStatus.MODIFIED,
        additions=1,
        deletions=0,
        changes=1,
        language="Java",
        categories=[FileCategory.DATABASE, FileCategory.BACKEND],
        hunks=[
            DiffHunk(
                old_start=30,
                old_count=0,
                new_start=30,
                new_count=1,
                lines=[
                    DiffLine(
                        old_line_no=None,
                        new_line_no=30,
                        content='"select * from users where id = " + userId',
                        line_type="added",
                    )
                ],
            )
        ],
    )

    result = AnalysisPipeline().analyze(_make_pr_with_file(changed_file))
    rule_ids = {finding.rule_id for finding in result.findings}

    assert "SEC_002_RAW_SQL_CONCATENATION" in rule_ids
    assert "TEST_001_RISKY_SOURCE_WITHOUT_MATCHING_TEST" in rule_ids


def test_risky_source_without_matching_test_rule_detects_missing_test() -> None:
    changed_file = ChangedFile(
        filename="src/main/java/com/app/order/OrderService.java",
        status=FileChangeStatus.MODIFIED,
        additions=5,
        deletions=2,
        changes=7,
        language="Java",
        categories=[FileCategory.BACKEND],
        hunks=[],
    )

    result = AnalysisPipeline().analyze(_make_pr_with_file(changed_file))

    assert any(
        finding.rule_id == "TEST_001_RISKY_SOURCE_WITHOUT_MATCHING_TEST"
        for finding in result.findings
    )
    assert result.test_recommendations