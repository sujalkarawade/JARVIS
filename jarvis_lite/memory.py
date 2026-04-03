from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MemoryStore:
    """Simple JSON-backed memory store for user facts."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding="utf-8")
            return {}

        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Reset a broken file instead of crashing the whole assistant.
            self.file_path.write_text("{}", encoding="utf-8")
            return {}

    def _save(self) -> None:
        self.file_path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def normalize_key(key: str) -> str:
        return " ".join(key.strip().lower().split())

    def remember(self, key: str, value: str) -> None:
        normalized_key = self.normalize_key(key)
        self.data[normalized_key] = value.strip()
        self._save()

    def recall(self, key: str) -> str | None:
        normalized_key = self.normalize_key(key)
        value = self.data.get(normalized_key)
        if isinstance(value, str):
            return value
        return None

    def forget(self, key: str) -> bool:
        normalized_key = self.normalize_key(key)
        if normalized_key in self.data:
            del self.data[normalized_key]
            self._save()
            return True
        return False

    def all_memories(self) -> dict[str, Any]:
        return dict(self.data)
