from pr_sentinel.core.enums import FileCategory, FileChangeStatus
from pr_sentinel.core.models import ChangedFile
from pr_sentinel.testsuggester.mapper import TestRecommendationMapper


def test_recommends_java_test_candidates() -> None:
    mapper = TestRecommendationMapper()

    candidates = mapper.candidate_tests_for_file(
        "src/main/java/com/app/order/OrderService.java"
    )

    assert "src/test/java/com/app/order/OrderServiceTest.java" in candidates
    assert "src/test/java/com/app/order/OrderServiceIT.java" in candidates


def test_recommends_python_test_candidates() -> None:
    mapper = TestRecommendationMapper()

    candidates = mapper.candidate_tests_for_file("src/pr_sentinel/core/config.py")

    assert "tests/test_pr_sentinel/core/config.py" in candidates
    assert "tests/pr_sentinel/core/config_test.py" in candidates


def test_recommends_javascript_test_candidates() -> None:
    mapper = TestRecommendationMapper()

    candidates = mapper.candidate_tests_for_file("src/components/Button.tsx")

    assert "src/components/Button.test.tsx" in candidates
    assert "src/components/Button.spec.tsx" in candidates


def test_recommend_for_changed_files_skips_test_files() -> None:
    changed_files = [
        ChangedFile(
            filename="src/test/java/com/app/order/OrderServiceTest.java",
            status=FileChangeStatus.MODIFIED,
            categories=[FileCategory.TEST],
        )
    ]

    recommendations = TestRecommendationMapper().recommend_for_changed_files(changed_files)

    assert recommendations == []


def test_recommend_for_changed_files_detects_missing_matching_test() -> None:
    changed_files = [
        ChangedFile(
            filename="src/main/java/com/app/order/OrderService.java",
            status=FileChangeStatus.MODIFIED,
            categories=[FileCategory.BACKEND],
        )
    ]

    recommendations = TestRecommendationMapper().recommend_for_changed_files(changed_files)

    assert len(recommendations) == 1
    assert recommendations[0].source_file == "src/main/java/com/app/order/OrderService.java"
    assert (
        "src/test/java/com/app/order/OrderServiceTest.java"
        in recommendations[0].recommended_tests
    )
    assert "no test files were modified" in recommendations[0].reason.lower()