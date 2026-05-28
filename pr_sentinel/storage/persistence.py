from pr_sentinel.core.models import AnalysisResult
from pr_sentinel.storage.analysis_repository import AnalysisRepository
from pr_sentinel.storage.database import SessionLocal


def persist_analysis_result(result: AnalysisResult) -> int:
    with SessionLocal() as db:
        repository = AnalysisRepository(db)
        record = repository.save_analysis(result)
        return record.id