"""Module for handling pyproject.toml files using Pydantic models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from pydantic import BaseModel

if TYPE_CHECKING:
    from bear_dereth.files.toml.file_handler import TomlData


class PyProjectToml(BaseModel):
    """Pydantic model for pyproject.toml files.

    Simplified representation focusing on common project metadata.
    For full pyproject.toml support, use the raw TOML data.
    """

    model_config = {"extra": "ignore"}

    name: str
    version: str | None = None
    dynamic: list[str] | None = None
    description: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    dependencies: list[str] | None = None

    def model_post_init(self, context: Any) -> None:
        """Clean up dependencies after initialization."""
        if self.dependencies:
            cleaned: list = []
            for dep in self.dependencies:
                if isinstance(dep, str):
                    clean_name: str = dep.split(" ")[0].split(">=")[0].split("==")[0].split("<=")[0]
                    cleaned.append(clean_name)
            self.dependencies = cleaned
        return super().model_post_init(context)

    @classmethod
    def from_toml_data(cls, data: TomlData) -> Self:
        """Create PyProjectToml from parsed TOML data.

        Args:
            data: Full pyproject.toml data dictionary

        Returns:
            PyProjectToml instance with extracted project data
        """
        project_data: dict = data.get("project", {})
        authors: list = project_data.get("authors", [])
        first_author: dict[str, str] = authors[0] if authors else {}

        return cls(
            name=project_data.get("name", ""),
            version=project_data.get("version"),
            dynamic=project_data.get("dynamic"),
            description=project_data.get("description"),
            author_name=first_author.get("name") if first_author else None,
            author_email=first_author.get("email") if first_author else None,
            dependencies=project_data.get("dependencies"),
        )
