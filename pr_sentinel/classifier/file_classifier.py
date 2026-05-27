from pathlib import PurePosixPath

from pr_sentinel.classifier.language_detector import detect_language
from pr_sentinel.core.enums import FileCategory
from pr_sentinel.core.models import ChangedFile

AUTH_KEYWORDS = {
    "auth",
    "authentication",
    "authorization",
    "jwt",
    "token",
    "security",
    "permission",
    "permissions",
    "role",
    "roles",
    "login",
    "logout",
    "session",
    "oauth",
    "password",
}

API_KEYWORDS = {
    "controller",
    "route",
    "routes",
    "api",
    "endpoint",
    "handler",
    "resource",
    "dto",
    "request",
    "response",
    "schema",
}

DATABASE_KEYWORDS = {
    "repository",
    "dao",
    "entity",
    "model",
    "migration",
    "migrations",
    "schema",
    "sql",
    "database",
    "db",
    "query",
}

TEST_KEYWORDS = {
    "test",
    "tests",
    "spec",
    "__tests__",
    "integrationtest",
    "unittest",
}

CONFIG_FILENAMES = {
    ".env",
    ".env.example",
    ".env.local",
    "application.yml",
    "application.yaml",
    "application.properties",
    "config.yml",
    "config.yaml",
    "settings.yml",
    "settings.yaml",
    "vercel.json",
    "netlify.toml",
    "tsconfig.json",
    "next.config.js",
    "vite.config.js",
    "webpack.config.js",
    "pytest.ini",
    "mypy.ini",
    "ruff.toml",
    "pyproject.toml",
}

DEPENDENCY_FILENAMES = {
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "pipfile",
    "pipfile.lock",
}

INFRA_KEYWORDS = {
    "docker",
    "dockerfile",
    "docker-compose",
    "compose",
    "jenkins",
    "github",
    "workflow",
    "workflows",
    "nginx",
    "kubernetes",
    "k8s",
    "helm",
    "terraform",
    "ansible",
    "deploy",
    "deployment",
    "ci",
    "cd",
}

FRONTEND_KEYWORDS = {
    "frontend",
    "client",
    "ui",
    "components",
    "pages",
    "app",
    "styles",
    "css",
    "scss",
    "tailwind",
}

BACKEND_KEYWORDS = {
    "backend",
    "server",
    "service",
    "services",
    "controller",
    "repository",
    "entity",
    "middleware",
    "handler",
    "api",
}

DOCUMENTATION_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".adoc",
}


class FileClassifier:
    def classify(self, changed_file: ChangedFile) -> ChangedFile:
        language = detect_language(changed_file.filename)
        categories = self.classify_path(changed_file.filename)

        changed_file.language = language
        changed_file.categories = categories

        return changed_file

    def classify_many(self, changed_files: list[ChangedFile]) -> list[ChangedFile]:
        return [self.classify(changed_file) for changed_file in changed_files]

    def classify_path(self, file_path: str) -> list[FileCategory]:
        normalized = file_path.replace("\\", "/").lower()
        path = PurePosixPath(normalized)
        filename = path.name
        parts = set(path.parts)
        suffix = path.suffix

        categories: set[FileCategory] = set()

        if suffix in DOCUMENTATION_EXTENSIONS:
            categories.add(FileCategory.DOCUMENTATION)

        if filename in DEPENDENCY_FILENAMES:
            categories.add(FileCategory.DEPENDENCY)

        if filename in CONFIG_FILENAMES:
            categories.add(FileCategory.CONFIG)

        if ".github" in parts or "workflows" in parts:
            categories.add(FileCategory.INFRA)
            categories.add(FileCategory.CONFIG)

        if "src/test" in normalized or "tests/" in normalized or "__tests__" in parts:
            categories.add(FileCategory.TEST)

        if any(keyword in normalized for keyword in AUTH_KEYWORDS):
            categories.add(FileCategory.AUTH)
            categories.add(FileCategory.SECURITY)

        if any(keyword in normalized for keyword in API_KEYWORDS):
            categories.add(FileCategory.API)

        if any(keyword in normalized for keyword in DATABASE_KEYWORDS):
            categories.add(FileCategory.DATABASE)

        if any(keyword in normalized for keyword in INFRA_KEYWORDS):
            categories.add(FileCategory.INFRA)

        if any(keyword in normalized for keyword in FRONTEND_KEYWORDS):
            categories.add(FileCategory.FRONTEND)

        if any(keyword in normalized for keyword in BACKEND_KEYWORDS):
            categories.add(FileCategory.BACKEND)

        if self._looks_like_backend_source(filename, normalized):
            categories.add(FileCategory.BACKEND)

        if self._looks_like_frontend_source(filename, normalized):
            categories.add(FileCategory.FRONTEND)

        if not categories:
            categories.add(FileCategory.UNKNOWN)

        return sorted(categories, key=lambda category: category.value)

    def _looks_like_backend_source(self, filename: str, normalized_path: str) -> bool:
        backend_extensions = (".java", ".py", ".go", ".kt", ".cs", ".rb", ".php")

        if filename.endswith(backend_extensions):
            return True

        backend_path_markers = (
            "src/main/",
            "server/",
            "backend/",
            "api/",
        )

        return any(marker in normalized_path for marker in backend_path_markers)

    def _looks_like_frontend_source(self, filename: str, normalized_path: str) -> bool:
        frontend_extensions = (".tsx", ".jsx", ".css", ".scss")

        if filename.endswith(frontend_extensions):
            return True

        frontend_path_markers = (
            "src/components/",
            "src/pages/",
            "src/app/",
            "client/",
            "frontend/",
            "ui/",
        )

        return any(marker in normalized_path for marker in frontend_path_markers)