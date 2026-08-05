import asyncio
from sqlalchemy import delete, select
from app.core.database import DBSessionManager
from app.models.framework import Framework
from app.models.requirement import Requirement


async def seed_gdpr():
    async with DBSessionManager.session() as session:
        name = "GDPR"
        framework_result = await session.execute(
            select(Framework).where(Framework.name == name)
        )
        framework = framework_result.scalar_one_or_none()
        if not framework:
            framework = Framework(
                name=name,
                description="General Data Protection Regulation",
                version="2016",
            )
            session.add(framework)
            await session.flush()
            print(f"Created framework: {name}")
        else:
            print(f"Framework '{name}' already exists, refreshing requirements...")
            framework.description = "General Data Protection Regulation"
            framework.version = "2016"

        # Parse the GDPR question file
        requirements = []
        with open("gdpr_gen.txt") as f:
            content = f.read()

        # Split by double newlines (blank-line separated paragraphs)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        for i, para in enumerate(paragraphs, start=1):
            code = f"GDPR-{i:03d}"
            name_text = para.split("?")[0] + "?" if "?" in para else para
            name_text = (name_text[:200] + "...") if len(name_text) > 200 else name_text
            requirements.append(
                {
                    "code": code,
                    "name": name_text,
                    "description": para,
                }
            )

        # Remove old requirements for this framework
        await session.execute(
            delete(Requirement).where(Requirement.framework_id == framework.id)
        )

        # Insert new requirements
        for data in requirements:
            req = Requirement(
                framework_id=framework.id,
                code=data["code"],
                name=data["name"],
                description=data["description"],
            )
            session.add(req)

        await session.commit()
        print(f"Seeded {len(requirements)} GDPR requirements successfully.")


if __name__ == "__main__":
    asyncio.run(seed_gdpr())
