"""Data models for canonical mapping rules loaded from YAML files."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonicalMappingRule:
    """A rule that maps a source resource type to a canonical asset model."""

    source_table: str
    canonical_category: str
    provider: str
    token_type: str = "fine_grained"
    canonical_id_template: str | None = None
    mappings: dict[str, Any] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)
    required_fields: list[str] = field(default_factory=list)
    version: int = 1
    last_modified: str | None = None
    owner: str | None = None
