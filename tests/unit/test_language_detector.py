from pr_sentinel.classifier.language_detector import detect_language


def test_detect_language_by_extension() -> None:
    assert detect_language("src/main/java/com/app/AuthFilter.java") == "Java"
    assert detect_language("src/app.py") == "Python"
    assert detect_language("src/index.ts") == "TypeScript"
    assert detect_language("src/App.tsx") == "TypeScript"
    assert detect_language("cmd/server/main.go") == "Go"
    assert detect_language("src/lib.rs") == "Rust"
    assert detect_language("src/main.cpp") == "C++"
    assert detect_language("src/main.c") == "C"
    assert detect_language("README.md") == "Markdown"


def test_detect_language_by_special_filename() -> None:
    assert detect_language("Dockerfile") == "Dockerfile"
    assert detect_language("Dockerfile.prod") == "Dockerfile"
    assert detect_language("pom.xml") == "Maven XML"
    assert detect_language("package.json") == "JSON"
    assert detect_language("requirements.txt") == "Python Requirements"
    assert detect_language("docker-compose.yml") == "Docker Compose"
    assert detect_language("Jenkinsfile") == "Jenkins"


def test_detect_language_config_and_env_files() -> None:
    assert detect_language(".env") == "Env"
    assert detect_language(".env.example") == "Env"
    assert detect_language(".env.production") == "Env"
    assert detect_language("vite.config.ts") == "TypeScript"
    assert detect_language("next.config.js") == "JavaScript"


def test_detect_language_unknown_returns_none() -> None:
    assert detect_language("unknownfile") is None