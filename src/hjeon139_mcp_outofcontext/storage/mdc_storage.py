"""MDC storage layer for markdown files with YAML frontmatter."""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _validate_name(name: str) -> None:
    """Validate that name is filename-safe.

    Args:
        name: Name to validate

    Raises:
        ValueError: If name is not filename-safe
    """
    if not name:
        raise ValueError("Name cannot be empty")
    # Filename-safe: alphanumeric, hyphens, underscores only
    if not re.match(r"^[a-zA-Z0-9_-]+$", name):
        raise ValueError(
            f"Name '{name}' must contain only alphanumeric characters, hyphens, and underscores"
        )


class MDCStorage:
    """Storage layer for markdown files with YAML frontmatter."""

    def __init__(self, storage_path: str | None = None) -> None:
        """Initialize MDC storage.

        Args:
            storage_path: Path to storage directory. Defaults to .out_of_context/contexts/ in project root
        """
        if storage_path is None:
            default_path = Path(".out_of_context") / "contexts"
            storage_path = os.getenv("OUT_OF_CONTEXT_STORAGE_PATH", str(default_path))

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_context(self, name: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Save a single context as .mdc file.

        Args:
            name: Context name (filename-safe)
            text: Markdown content (body)
            metadata: Optional metadata dict (goes in YAML frontmatter)

        Raises:
            ValueError: If name is not filename-safe
        """
        _validate_name(name)

        # Prepare metadata with defaults
        meta = metadata or {}
        if "name" not in meta:
            meta["name"] = name
        if "created_at" not in meta:
            meta["created_at"] = datetime.now().isoformat()

        # Check if exists (for warning)
        file_path = self.storage_path / f"{name}.mdc"
        exists = file_path.exists()
        if exists:
            logger.warning(f"Overwriting existing context: {name}")

        # Write file with YAML frontmatter + markdown body
        self._write_mdc_file(file_path, meta, text)

    def save_contexts(self, contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Save multiple contexts (bulk operation).

        Args:
            contexts: List of dicts, each with 'name', 'text', optional 'metadata'

        Returns:
            List of result dicts with 'name', 'success', optional 'error'
        """
        results: list[dict[str, Any]] = []
        for ctx in contexts:
            name = ctx.get("name")
            text = ctx.get("text", "")
            metadata = ctx.get("metadata")

            if not name:
                results.append({"name": None, "success": False, "error": "Missing 'name' field"})
                continue

            try:
                self.save_context(name, text, metadata)
                results.append({"name": name, "success": True})
            except Exception as e:
                logger.error(f"Failed to save context '{name}': {e}")
                results.append({"name": name, "success": False, "error": str(e)})

        return results

    def load_context(self, name: str) -> dict[str, Any] | None:
        """Load a single context from .mdc file.

        Args:
            name: Context name

        Returns:
            Dict with 'text' (markdown body) and 'metadata' (from frontmatter), or None if not found
        """
        _validate_name(name)
        file_path = self.storage_path / f"{name}.mdc"

        if not file_path.exists():
            return None

        try:
            return self._read_mdc_file(file_path)
        except Exception as e:
            logger.error(f"Failed to load context '{name}': {e}")
            return None

    def load_contexts(self, names: list[str]) -> list[dict[str, Any] | None]:
        """Load multiple contexts (bulk operation).

        Args:
            names: List of context names

        Returns:
            List of dicts (same format as load_context) or None for missing contexts
        """
        results: list[dict[str, Any] | None] = []
        for name in names:
            try:
                result = self.load_context(name)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to load context '{name}': {e}")
                results.append(None)

        return results

    def list_contexts(self) -> list[dict[str, Any]]:
        """List all contexts.

        Returns:
            List of dicts with 'name', 'created_at', 'preview' (first 100 chars)
        """
        contexts: list[dict[str, Any]] = []

        for file_path in self.storage_path.glob("*.mdc"):
            name = file_path.stem
            try:
                data = self._read_mdc_file(file_path)
                if data:
                    metadata = data.get("metadata", {})
                    text = data.get("text", "")
                    preview = text[:100] if text else ""

                    contexts.append(
                        {
                            "name": name,
                            "created_at": metadata.get("created_at", ""),
                            "preview": preview,
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to read context file '{file_path}': {e}")

        # Sort by created_at (newest first)
        contexts.sort(
            key=lambda x: x.get("created_at", ""), reverse=True
        )  # Empty string sorts last

        return contexts

    def delete_context(self, name: str) -> None:
        """Delete a single context.

        Args:
            name: Context name

        Raises:
            ValueError: If name is not filename-safe or context doesn't exist
        """
        _validate_name(name)
        file_path = self.storage_path / f"{name}.mdc"

        if not file_path.exists():
            raise ValueError(f"Context '{name}' not found")

        try:
            file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to delete context '{name}': {e}")
            raise

    def delete_contexts(self, names: list[str]) -> list[dict[str, Any]]:
        """Delete multiple contexts (bulk operation).

        Args:
            names: List of context names

        Returns:
            List of result dicts with 'name', 'success', optional 'error'
        """
        results: list[dict[str, Any]] = []
        for name in names:
            try:
                self.delete_context(name)
                results.append({"name": name, "success": True})
            except Exception as e:
                logger.error(f"Failed to delete context '{name}': {e}")
                results.append({"name": name, "success": False, "error": str(e)})

        return results

    def search_contexts(self, query: str) -> list[dict[str, Any]]:
        """Search contexts by query string.

        Args:
            query: Search query (searches in both frontmatter and markdown body)

        Returns:
            List of matching contexts with 'name', 'text', 'metadata', 'matches' (where query was found)
        """
        if not query:
            return []

        query_lower = query.lower()
        matches: list[dict[str, Any]] = []

        for file_path in self.storage_path.glob("*.mdc"):
            try:
                data = self._read_mdc_file(file_path)
                if not data:
                    continue

                name = file_path.stem
                text = data.get("text", "")
                metadata = data.get("metadata", {})

                # Search in text and metadata
                found_in_text = query_lower in text.lower()
                found_in_metadata = any(
                    query_lower in str(v).lower() for v in metadata.values() if v
                )

                if found_in_text or found_in_metadata:
                    match_locations = []
                    if found_in_text:
                        match_locations.append("text")
                    if found_in_metadata:
                        match_locations.append("metadata")

                    matches.append(
                        {
                            "name": name,
                            "text": text,
                            "metadata": metadata,
                            "matches": match_locations,
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to search context file '{file_path}': {e}")

        return matches

    def _write_mdc_file(self, file_path: Path, metadata: dict[str, Any], text: str) -> None:
        """Write .mdc file with YAML frontmatter and markdown body.

        Args:
            file_path: Path to write file
            metadata: Metadata dict for frontmatter
            text: Markdown content for body
        """
        # Write YAML frontmatter
        frontmatter = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        frontmatter = frontmatter.strip()

        # Write file: frontmatter + separator + markdown body
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(frontmatter)
            f.write("\n---\n\n")
            f.write(text)

    def _read_mdc_file(self, file_path: Path) -> dict[str, Any] | None:
        """Read .mdc file and parse YAML frontmatter + markdown body.

        Args:
            file_path: Path to read file

        Returns:
            Dict with 'metadata' and 'text', or None on error
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse frontmatter (between --- delimiters)
            if not content.startswith("---\n"):
                # No frontmatter, treat entire content as text
                return {"metadata": {}, "text": content}

            # Find end of frontmatter
            parts = content.split("---\n", 2)
            if len(parts) < 3:
                # Malformed, treat as text only
                return {"metadata": {}, "text": content}

            frontmatter_str = parts[1]
            text = parts[2].lstrip("\n")  # Remove leading newline after ---, preserve trailing

            # Parse YAML frontmatter
            try:
                metadata = yaml.safe_load(frontmatter_str) or {}
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse frontmatter in '{file_path}': {e}")
                metadata = {}

            return {"metadata": metadata, "text": text}

        except Exception as e:
            logger.error(f"Failed to read mdc file '{file_path}': {e}")
            return None
