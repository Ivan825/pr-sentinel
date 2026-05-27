from pr_sentinel.core.models import ChangedFile
from pr_sentinel.diff.parser import PatchParser


class ChangedFileDiffParser:
    def __init__(self, patch_parser: PatchParser | None = None) -> None:
        self.patch_parser = patch_parser or PatchParser()

    def parse_changed_file(self, changed_file: ChangedFile) -> ChangedFile:
        changed_file.hunks = self.patch_parser.parse_patch(changed_file.patch)
        return changed_file

    def parse_changed_files(self, changed_files: list[ChangedFile]) -> list[ChangedFile]:
        return [self.parse_changed_file(changed_file) for changed_file in changed_files]