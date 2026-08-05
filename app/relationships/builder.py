from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset_relationship import AssetRelationship
from app.models.canonical_asset import CanonicalAsset

from app.mappers import RelationshipData


class RelationshipBuilder:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def resolve_and_store(
        self, organization_id: int, relationships: list
    ) -> list[AssetRelationship]:
        assets_by_provider_id: dict[str, int] = {}
        result = await self.db.execute(
            select(CanonicalAsset).where(
                CanonicalAsset.organization_id == organization_id,
                CanonicalAsset.provider == "AWS",
            )
        )
        for asset in result.scalars().all():
            assets_by_provider_id[asset.provider_resource_id] = asset.id

        stored: list[AssetRelationship] = []
        for rel in relationships:
            source_id = assets_by_provider_id.get(rel.source_provider_resource_id)
            target_id = assets_by_provider_id.get(rel.target_provider_resource_id)
            if not source_id or not target_id:
                continue

            exists = await self.db.execute(
                select(AssetRelationship).where(
                    AssetRelationship.organization_id == organization_id,
                    AssetRelationship.source_asset_id == source_id,
                    AssetRelationship.target_asset_id == target_id,
                    AssetRelationship.relationship_type == rel.relationship_type,
                )
            )
            if exists.scalar_one_or_none():
                continue

            ar = AssetRelationship(
                organization_id=organization_id,
                source_asset_id=source_id,
                target_asset_id=target_id,
                relationship_type=rel.relationship_type,
                extras=rel.extras,
            )
            self.db.add(ar)
            stored.append(ar)

        await self.db.commit()
        return stored
