"""Local file-based storage backend for scaffold persistence."""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from platformdirs import user_data_dir
from . import PersistenceBackend


class LocalStorage(PersistenceBackend):
    """File-based local storage backend (default).

    Stores scaffold states as JSON files in user data directory.

    Location:
        Linux/macOS: ~/.local/share/egregore/scaffolds/
        Windows: %USERPROFILE%\\AppData\\Local\\egregore\\scaffolds\\
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize local storage.

        Args:
            base_dir: Custom storage directory (defaults to user data dir)
        """
        if base_dir is None:
            # DRY: Use same platformdirs approach as ContextHistory
            base_dir = Path(user_data_dir("egregore")) / "scaffolds"

        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a scaffold key."""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_dir / f"{safe_key}.json"

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save state to JSON file."""
        file_path = self._get_file_path(key)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load state from JSON file."""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def delete(self, key: str) -> None:
        """Delete JSON file."""
        file_path = self._get_file_path(key)

        if file_path.exists():
            file_path.unlink()

    def exists(self, key: str) -> bool:
        """Check if JSON file exists."""
        return self._get_file_path(key).exists()
