from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class CanonicalAssetData:
    organization_id: int
    provider: str
    provider_resource_id: str
    canonical_type: str
    display_name: str | None
    account_id: str | None
    region: str | None
    owner: str | None
    tags: dict | None
    status: str | None
    environment: str | None = None
    data_classification: str | None = None
    source_connection_id: str | None = None
    details: dict | None = None
    raw_resource_id: int | None = None
    discovered_at: datetime | None = None
    last_seen_at: datetime | None = None
    deleted_at: datetime | None = None


@dataclass
class RelationshipData:
    organization_id: int
    source_provider_resource_id: str
    target_provider_resource_id: str
    relationship_type: str
    extras: dict | None


class BaseMapper(ABC):
    provider: str

    @abstractmethod
    def map(
        self, organization_id: int, raw_resources: list, existing_assets: dict
    ) -> tuple[list[CanonicalAssetData], list[RelationshipData]]:
        ...
