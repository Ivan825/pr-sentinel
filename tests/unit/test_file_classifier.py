from pr_sentinel.classifier.file_classifier import FileClassifier
from pr_sentinel.core.enums import FileCategory


def test_classifies_auth_security_backend_file() -> None:
    classifier = FileClassifier()

    categories = classifier.classify_path("src/main/java/com/app/security/JwtAuthFilter.java")

    assert FileCategory.AUTH in categories
    assert FileCategory.SECURITY in categories
    assert FileCategory.BACKEND in categories


def test_classifies_api_controller_file() -> None:
    classifier = FileClassifier()

    categories = classifier.classify_path("src/main/java/com/app/order/OrderController.java")

    assert FileCategory.API in categories
    assert FileCategory.BACKEND in categories


def test_classifies_database_repository_file() -> None:
    classifier = FileClassifier()

    categories = classifier.classify_path("src/main/java/com/app/order/OrderRepository.java")

    assert FileCategory.DATABASE in categories
    assert FileCategory.BACKEND in categories


def test_classifies_dependency_file() -> None:
    classifier = FileClassifier()

    categories = classifier.classify_path("package.json")

    assert FileCategory.DEPENDENCY in categories


def test_classifies_config_file() -> None:
    classifier = FileClassifier()

    categories = classifier.classify_path("src/main/resources/application.yml")

    assert FileCategory.CONFIG in categories


def test_classifies_github_workflow_as_infra_and_config() -> None:
    classifier = FileClassifier()

    categories = classifier.classify_path(".github/workflows/ci.yml")

    assert FileCategory.INFRA in categories
    assert FileCategory.CONFIG in categories


def test_classifies_test_file() -> None:
    classifier = FileClassifier()

    categories = classifier.classify_path("src/test/java/com/app/AuthFilterTest.java")

    assert FileCategory.TEST in categories


def test_classifies_documentation_file() -> None:
    classifier = FileClassifier()

    categories = classifier.classify_path("README.md")

    assert FileCategory.DOCUMENTATION in categories