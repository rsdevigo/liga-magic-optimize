"""Card list file reader."""

from __future__ import annotations

from pathlib import Path

from cube_budget.core.exceptions import CardReadError
from cube_budget.core.models import Card
from cube_budget.services.name_normalizer import NameNormalizer


class CardReader:
    """Reads and validates card list files (one card per line)."""

    SUPPORTED_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "cp1252")

    def __init__(self, normalizer: NameNormalizer | None = None):
        self._normalizer = normalizer or NameNormalizer()

    def read(self, file_path: str | Path) -> list[Card]:
        path = Path(file_path)
        if not path.exists():
            raise CardReadError(f"File not found: {path}")

        if not path.is_file():
            raise CardReadError(f"Not a file: {path}")

        content = self._read_with_encoding(path)
        lines = content.splitlines()

        if not lines:
            raise CardReadError(f"File is empty: {path}")

        raw_names = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                raw_names.append(stripped)

        if not raw_names:
            raise CardReadError(f"No valid card names found in: {path}")

        return self._normalizer.normalize_batch(raw_names)

    def _read_with_encoding(self, path: Path) -> str:
        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                return path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise CardReadError(f"Could not decode file with supported encodings: {path}")
