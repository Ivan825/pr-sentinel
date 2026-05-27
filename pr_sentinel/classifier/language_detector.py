from pathlib import Path

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    # Backend / general-purpose languages
    ".java": "Java",
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".swift": "Swift",
    ".rb": "Ruby",
    ".php": "PHP",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang Header",
    ".fs": "F#",
    ".fsx": "F#",
    ".dart": "Dart",
    ".lua": "Lua",
    ".r": "R",
    ".m": "Objective-C",
    ".mm": "Objective-C++",

    # Web / frontend
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".vue": "Vue",
    ".svelte": "Svelte",

    # Data / config
    ".json": "JSON",
    ".jsonc": "JSONC",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".xml": "XML",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".conf": "Config",
    ".properties": "Properties",
    ".env": "Env",
    ".csv": "CSV",
    ".tsv": "TSV",

    # Database / query
    ".sql": "SQL",
    ".graphql": "GraphQL",
    ".gql": "GraphQL",

    # Documentation
    ".md": "Markdown",
    ".mdx": "MDX",
    ".txt": "Text",
    ".rst": "reStructuredText",
    ".adoc": "AsciiDoc",

    # Shell / scripts
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".fish": "Shell",
    ".ps1": "PowerShell",
    ".bat": "Batch",
    ".cmd": "Batch",

    # Infra / DevOps
    ".dockerfile": "Dockerfile",
    ".tf": "Terraform",
    ".tfvars": "Terraform Variables",
    ".hcl": "HCL",
    ".nomad": "Nomad",
    ".gradle": "Gradle",
    ".groovy": "Groovy",

    # Build / project files
    ".lock": "Lockfile",
    ".mod": "Go Module",
    ".sum": "Go Checksum",
}


SPECIAL_FILENAME_LANGUAGE_MAP: dict[str, str] = {
    # Docker / containers
    "dockerfile": "Dockerfile",
    "containerfile": "Containerfile",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    "compose.yml": "Docker Compose",
    "compose.yaml": "Docker Compose",

    # Build systems
    "makefile": "Makefile",
    "cmakelists.txt": "CMake",
    "build.gradle": "Gradle",
    "settings.gradle": "Gradle",
    "gradlew": "Shell",
    "mvnw": "Shell",
    "pom.xml": "Maven XML",

    # JavaScript / TypeScript package files
    "package.json": "JSON",
    "package-lock.json": "JSON",
    "yarn.lock": "Yarn Lock",
    "pnpm-lock.yaml": "PNPM Lock",
    "bun.lockb": "Bun Lock",
    "tsconfig.json": "JSON",
    "jsconfig.json": "JSON",
    "next.config.js": "JavaScript",
    "next.config.mjs": "JavaScript",
    "vite.config.js": "JavaScript",
    "vite.config.ts": "TypeScript",
    "webpack.config.js": "JavaScript",
    "tailwind.config.js": "JavaScript",
    "postcss.config.js": "JavaScript",

    # Python project files
    "requirements.txt": "Python Requirements",
    "requirements-dev.txt": "Python Requirements",
    "pyproject.toml": "TOML",
    "poetry.lock": "Poetry Lock",
    "pipfile": "TOML",
    "pipfile.lock": "JSON",
    "setup.py": "Python",
    "setup.cfg": "Config",

    # Go / Rust
    "go.mod": "Go Module",
    "go.sum": "Go Checksum",
    "cargo.toml": "TOML",
    "cargo.lock": "Cargo Lock",

    # CI/CD
    "jenkinsfile": "Jenkins",
    ".gitlab-ci.yml": "GitLab CI",
    ".gitlab-ci.yaml": "GitLab CI",
    "azure-pipelines.yml": "Azure Pipelines",
    "azure-pipelines.yaml": "Azure Pipelines",
    "bitbucket-pipelines.yml": "Bitbucket Pipelines",

    # Formatting / linting
    ".prettierrc": "JSON",
    ".eslintrc": "JSON",
    ".eslintrc.json": "JSON",
    ".eslintrc.js": "JavaScript",
    ".flake8": "INI",
    ".pylintrc": "INI",
    "ruff.toml": "TOML",
    "mypy.ini": "INI",
    "pytest.ini": "INI",

    # Environment
    ".env": "Env",
    ".env.example": "Env",
    ".env.local": "Env",
    ".env.production": "Env",
    ".env.development": "Env",

    # Documentation
    "readme": "Text",
    "readme.md": "Markdown",
    "license": "Text",
    "changelog.md": "Markdown",
}


def detect_language(file_path: str) -> str | None:
    path = Path(file_path)
    filename = path.name.lower()

    if filename in SPECIAL_FILENAME_LANGUAGE_MAP:
        return SPECIAL_FILENAME_LANGUAGE_MAP[filename]

    # Handles names like Dockerfile.prod, .env.staging, etc.
    if filename.startswith("dockerfile"):
        return "Dockerfile"

    if filename.startswith(".env"):
        return "Env"

    if filename.endswith(".config.js"):
        return "JavaScript"

    if filename.endswith(".config.ts"):
        return "TypeScript"

    return EXTENSION_LANGUAGE_MAP.get(path.suffix.lower())