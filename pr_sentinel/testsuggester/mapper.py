from pathlib import PurePosixPath

from pr_sentinel.core.enums import FileCategory
from pr_sentinel.core.models import ChangedFile, TestRecommendation


class TestRecommendationMapper:
    def recommend_for_changed_files(
        self,
        changed_files: list[ChangedFile],
    ) -> list[TestRecommendation]:
        changed_file_paths = {file.filename for file in changed_files}
        test_files_changed = self._extract_changed_test_files(changed_files)

        recommendations: list[TestRecommendation] = []

        for changed_file in changed_files:
            if self._should_skip_file(changed_file):
                continue

            candidates = self._candidate_tests_for_file(changed_file.filename)
            matching_changed_tests = [
                candidate for candidate in candidates if candidate in changed_file_paths
            ]

            recommended_tests = matching_changed_tests or candidates

            reason = self._build_reason(
                changed_file=changed_file,
                matching_changed_tests=matching_changed_tests,
                test_files_changed=test_files_changed,
            )

            recommendations.append(
                TestRecommendation(
                    source_file=changed_file.filename,
                    recommended_tests=recommended_tests,
                    reason=reason,
                )
            )

        return recommendations

    def _should_skip_file(self, changed_file: ChangedFile) -> bool:
        return (
            FileCategory.TEST in changed_file.categories
            or FileCategory.DOCUMENTATION in changed_file.categories
            or changed_file.filename.lower().endswith(
                (
                    ".md",
                    ".txt",
                    ".rst",
                    ".adoc",
                    ".lock",
                )
            )
        )

    def _extract_changed_test_files(self, changed_files: list[ChangedFile]) -> set[str]:
        return {
            changed_file.filename
            for changed_file in changed_files
            if FileCategory.TEST in changed_file.categories
        }
    
    def candidate_tests_for_file(self, file_path: str) -> list[str]:
        return self._candidate_tests_for_file(file_path)
    
    def _candidate_tests_for_file(self, file_path: str) -> list[str]:
        normalized = file_path.replace("\\", "/")
        path = PurePosixPath(normalized)
        filename = path.name

        if filename.endswith(".java"):
            return self._java_test_candidates(normalized)

        if filename.endswith(".py"):
            return self._python_test_candidates(normalized)

        if filename.endswith((".js", ".jsx", ".ts", ".tsx")):
            return self._javascript_test_candidates(normalized)

        return self._generic_test_candidates(normalized)

    def _java_test_candidates(self, file_path: str) -> list[str]:
        path = PurePosixPath(file_path)
        class_name = path.stem

        candidates: list[str] = []

        if "src/main/java/" in file_path:
            test_path = file_path.replace("src/main/java/", "src/test/java/")
            test_path = test_path.removesuffix(".java")
            candidates.append(f"{test_path}Test.java")
            candidates.append(f"{test_path}IT.java")
            candidates.append(f"{test_path}IntegrationTest.java")
        else:
            parent = str(path.parent)
            candidates.append(f"{parent}/{class_name}Test.java")
            candidates.append(f"{parent}/{class_name}IT.java")

        return self._dedupe(candidates)

    def _python_test_candidates(self, file_path: str) -> list[str]:
        path = PurePosixPath(file_path)
        filename = path.name

        candidates: list[str] = []

        if filename.startswith("test_"):
            return []

        if file_path.startswith("src/"):
            without_src = file_path.removeprefix("src/")
            candidates.append(f"tests/test_{without_src}")
            candidates.append(f"tests/{without_src.removesuffix('.py')}_test.py")

        candidates.append(f"tests/test_{filename}")
        candidates.append(f"test_{filename}")

        parent = str(path.parent)
        candidates.append(f"{parent}/test_{filename}")
        candidates.append(f"{parent}/{path.stem}_test.py")

        return self._dedupe(candidates)

    def _javascript_test_candidates(self, file_path: str) -> list[str]:
        path = PurePosixPath(file_path)
        stem = path.stem
        suffix = path.suffix
        parent = str(path.parent)

        if ".test." in file_path or ".spec." in file_path:
            return []

        candidates = [
            f"{parent}/{stem}.test{suffix}",
            f"{parent}/{stem}.spec{suffix}",
            f"{parent}/__tests__/{stem}.test{suffix}",
            f"{parent}/__tests__/{stem}.spec{suffix}",
        ]

        if file_path.startswith("src/"):
            without_src = file_path.removeprefix("src/")
            candidates.append(f"tests/{without_src.removesuffix(suffix)}.test{suffix}")
            candidates.append(f"tests/{without_src.removesuffix(suffix)}.spec{suffix}")

        return self._dedupe(candidates)

    def _generic_test_candidates(self, file_path: str) -> list[str]:
        path = PurePosixPath(file_path)
        parent = str(path.parent)
        stem = path.stem
        suffix = path.suffix

        return self._dedupe(
            [
                f"{parent}/{stem}Test{suffix}",
                f"{parent}/{stem}_test{suffix}",
                f"tests/{stem}_test{suffix}",
            ]
        )

    def _build_reason(
        self,
        changed_file: ChangedFile,
        matching_changed_tests: list[str],
        test_files_changed: set[str],
    ) -> str:
        categories = ", ".join(category.value for category in changed_file.categories)

        if matching_changed_tests:
            return (
                "Matching test file was changed in this PR. Recommended for validation "
                f"because source categories are: {categories}."
            )

        if test_files_changed:
            return (
                "Source file changed, but no directly matching test file was modified. "
                f"Other test files changed in this PR: {', '.join(sorted(test_files_changed))}."
            )

        return (
            "Source file changed, but no test files were modified in this PR. "
            f"Review recommended tests because source categories are: {categories}."
        )

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []

        for value in values:
            if value in seen:
                continue

            seen.add(value)
            deduped.append(value)

        return deduped