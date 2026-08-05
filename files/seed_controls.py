import asyncio

from sqlalchemy import select

from app.core.database import DBSessionManager
from app.core.security import get_password_hash
from app.models.control import Control
from app.models.control_mapping import ControlMapping
from app.models.enums import ComplianceStatus
from app.models.framework import Framework
from app.models.organization import Organization
from app.models.requirement import Requirement
from app.models.user import User
from app.models.user_role import UserRole
from app.models.enums import RoleName, UserStatus
from app.models.role import Role


async def seed_controls():
    async with DBSessionManager.session() as session:
        # Get or create default org
        org_result = await session.execute(
            select(Organization).where(Organization.slug == "default-org")
        )
        org = org_result.scalar_one_or_none()
        if not org:
            print("No default-org found, creating...")
            org = Organization(name="Default Organization", slug="default-org")
            session.add(org)
            await session.flush()

        # Ensure admin user exists
        user_result = await session.execute(
            select(User).where(User.email == "admin@appxcess.com")
        )
        admin = user_result.scalar_one_or_none()
        if not admin:
            role_result = await session.execute(
                select(Role).where(Role.name == RoleName.super_admin)
            )
            role = role_result.scalar_one_or_none()

            admin = User(
                organization_id=org.id,
                email="admin@appxcess.com",
                first_name="Admin",
                last_name="User",
                status=UserStatus.active,
                hashed_password=get_password_hash("admin@123"),
            )
            session.add(admin)
            await session.flush()

            if role:
                session.add(UserRole(user_id=admin.id, role_id=role.id))

        # Get all frameworks
        result = await session.execute(select(Framework).order_by(Framework.id))
        frameworks = result.scalars().all()

        total_controls = 0
        for fw in frameworks:
            # Get requirements for this framework
            result = await session.execute(
                select(Requirement).where(Requirement.framework_id == fw.id).order_by(Requirement.code)
            )
            requirements = result.scalars().all()

            if not requirements:
                print(f"  {fw.name}: no requirements, skipping")
                continue

            for req in requirements:
                # Create a control for each requirement with a matching code
                control_code = f"{fw.name[:3].upper()}-{req.code}"

                ctrl_result = await session.execute(
                    select(Control).where(
                        Control.organization_id == org.id,
                        Control.code == control_code,
                    )
                )
                control = ctrl_result.scalar_one_or_none()

                if not control:
                    control = Control(
                        organization_id=org.id,
                        code=control_code,
                        name=f"{fw.name}: {req.name}",
                        description=req.description,
                        status=ComplianceStatus.not_applicable,
                    )
                    session.add(control)
                    await session.flush()

                # Check if mapping exists
                mapping_result = await session.execute(
                    select(ControlMapping).where(
                        ControlMapping.control_id == control.id,
                        ControlMapping.requirement_id == req.id,
                    )
                )
                if not mapping_result.scalar_one_or_none():
                    session.add(
                        ControlMapping(control_id=control.id, requirement_id=req.id)
                    )

                total_controls += 1

        await session.commit()
        print(f"Seeded {total_controls} controls with mappings across {len(frameworks)} frameworks.")


if __name__ == "__main__":
    asyncio.run(seed_controls())
