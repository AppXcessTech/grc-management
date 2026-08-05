import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import engine, DBSessionManager
from app.models.role import Role
from app.models.enums import RoleName
from app.models.permission import Permission
from app.models.enums import PermissionAction

from app.models.organization import Organization
from app.models.user import User
from app.models.user_role import UserRole
from app.models.enums import UserStatus
from app.models.asset_category import AssetCategory

from app.models.asset import Asset
from app.models.people_asset import PeopleAsset
from app.models.platform_user import PlatformUser
from app.models.platform_role import PlatformRole
from app.models.platform_user_role import PlatformUserRole
from app.core.security import get_password_hash

from app.models.framework import Framework
from app.models.requirement import Requirement
from app.models.control import Control
from app.models.control_mapping import ControlMapping
from app.models.enums import ComplianceStatus
import re
import os

def parse_full_iso_file(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r') as f:
        text = f.read()

    requirements = []
    blocks = text.split("--------------------------------------------------------------------------------")

    pending_code = None
    pending_name = None

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue

        first = lines[0]

        # Check if this block starts with a code line like "4.3 | ISMS Scope"
        code_match = re.match(r'^([\d\.]+)\s*\|\s*(.*)', first)
        if code_match:
            # Save the previous pending requirement if any
            if pending_code:
                requirements.append({
                    'code': pending_code,
                    'name': pending_name,
                    'description': None,
                    'status': None,
                })
            pending_code = code_match.group(1).strip()
            pending_name = code_match.group(2).strip()
            continue

        # This block has the status line and description for the pending requirement
        if pending_code:
            desc_lines = []
            for l in lines:
                if l.startswith("Status Options:"):
                    continue
                if l.startswith("====") or l.startswith("----"):
                    continue
                desc_lines.append(l)

            requirements.append({
                'code': pending_code,
                'name': pending_name,
                'description': ' '.join(desc_lines) if desc_lines else None,
                'status': None,
            })
            pending_code = None
            pending_name = None

    # Flush last pending
    if pending_code:
        requirements.append({
            'code': pending_code,
            'name': pending_name,
            'description': None,
            'status': None,
        })

    return requirements


def parse_iso_controls_file(file_path):
    """Parse iso_27001.txt into control dicts with code, name, description."""
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r') as f:
        text = f.read()

    controls = []
    lines = text.split('\n')
    # Section headers to skip (not actual controls)
    section_headers = {"Organizational controls", "People controls", "Physical controls", "Technological controls"}

    current_code = None
    current_name_parts = []
    current_desc_parts = []
    state = "IDLE"

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "© ISO/IEC 2022" in line or "ISO/IEC 27001:2022(E)" in line:
            continue

        # Match control codes: "5.1 Policies..." or "5.5.Contact with..."
        match = re.match(r'^(\d+\.\d+)\.?(.*)', line)
        if match:
            code = match.group(1)
            rest = match.group(2).strip()

            # Skip section headers like "6.People controls"
            if rest in section_headers:
                continue

            # Save previous if we have one
            if current_code and current_desc_parts:
                controls.append({
                    'code': current_code,
                    'name': ' '.join(current_name_parts),
                    'description': ' '.join(current_desc_parts),
                })

            current_code = code
            current_name_parts = [rest] if rest else []
            current_desc_parts = []
            state = "COLLECTING_NAME"
            continue

        if line == "Control":
            state = "COLLECTING_DESC"
            continue

        if state == "COLLECTING_NAME":
            current_name_parts.append(line)
        elif state == "COLLECTING_DESC":
            current_desc_parts.append(line)

    if current_code and current_desc_parts:
        controls.append({
            'code': current_code,
            'name': ' '.join(current_name_parts),
            'description': ' '.join(current_desc_parts),
        })

    return controls


async def seed_data():
    async with DBSessionManager.session() as session:
        # 1. Seed Organizations
        org_result = await session.execute(select(Organization).where(Organization.slug == "default-org"))
        org = org_result.scalar_one_or_none()
        if not org:
            org = Organization(
                name="Default Organization",
                slug="default-org",
                domain="appxcess.com"
            )
            session.add(org)
        
        hybrid_org_result = await session.execute(select(Organization).where(Organization.slug == "hybrid"))
        hybrid_org = hybrid_org_result.scalar_one_or_none()
        if not hybrid_org:
            hybrid_org = Organization(
                name="Hybrid Corp",
                slug="hybrid",
                domain="hybrid.com"
            )
            session.add(hybrid_org)
        
        await session.flush() # Get org IDs
        
        # 2. Seed Roles
        roles_map = {}
        for role_name in RoleName:
            role_result = await session.execute(select(Role).where(Role.name == role_name))
            role = role_result.scalar_one_or_none()
            if not role:
                role = Role(name=role_name, display_name=role_name.value.replace("_", " ").title(), is_system=True)
                session.add(role)
                await session.flush()
            roles_map[role_name] = role
        
        # 3. Seed Permissions
        permissions = [
            ("control", PermissionAction.view, "View Controls"),
            ("policy", PermissionAction.edit, "Edit Policies"),
            ("evidence", PermissionAction.create, "Upload Evidence"),
            ("risk", PermissionAction.create, "Create Risks"),
            ("vendor", PermissionAction.approve, "Approve Vendors"),
        ]
        
        for resource, action, description in permissions:
            perm_result = await session.execute(
                select(Permission).where(Permission.resource == resource, Permission.action == action)
            )
            if not perm_result.scalar_one_or_none():
                perm = Permission(resource=resource, action=action, description=description)
                session.add(perm)
        
        # 4. Seed Admin Users
        # Default Admin
        user_result = await session.execute(select(User).where(User.email == "admin@appxcess.com"))
        admin_user = user_result.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                organization_id=org.id,
                email="admin@appxcess.com",
                first_name="Admin",
                last_name="User",
                status=UserStatus.active,
                hashed_password=get_password_hash("admin@123")
            )
            session.add(admin_user)
            await session.flush()
            
            admin_role = UserRole(user_id=admin_user.id, role_id=roles_map[RoleName.super_admin].id)
            session.add(admin_role)
        else:
            admin_user.hashed_password = get_password_hash("admin@123")

        # Hybrid Customer Admin
        hybrid_user_result = await session.execute(select(User).where(User.email == "admin@hybrid.com"))
        hybrid_admin = hybrid_user_result.scalar_one_or_none()
        if not hybrid_admin:
            hybrid_admin = User(
                organization_id=hybrid_org.id,
                email="admin@hybrid.com",
                first_name="Hybrid",
                last_name="Admin",
                status=UserStatus.active,
                hashed_password=get_password_hash("hybrid@123")
            )
            session.add(hybrid_admin)
            await session.flush()
            
            hybrid_role = UserRole(user_id=hybrid_admin.id, role_id=roles_map[RoleName.super_admin].id)
            session.add(hybrid_role)
        else:
            hybrid_admin.hashed_password = get_password_hash("hybrid@123")

        await session.flush()

        # 5. Seed Asset Categories
        categories = [
            ("People", "Employees, contractors, interns, and other personnel"),
            ("Device", "Laptops, desktops, mobile devices, kiosks, and endpoint hardware"),
            ("Server", "Physical servers, virtual machines, and cloud compute instances"),
            ("Application", "SaaS applications, business systems, and software services"),
            ("Database", "Database instances, data warehouses, and data stores"),
            ("Cloud Resource", "Cloud infrastructure, accounts, and platform services"),
            ("Vendor", "Third-party vendors, suppliers, and service providers"),
            ("Network", "Firewalls, routers, switches, VPNs, and network infrastructure"),
            ("Storage", "NAS, SAN, cloud storage, backup repositories, and archive systems"),
            ("Development", "Source code repos, CI/CD pipelines, and development tooling"),
            ("Security", "Identity systems, endpoint security, SIEM, and security tools"),
            ("Information", "Customer data, intellectual property, financial records, and documents"),
            ("Cryptographic", "Encryption keys, certificates, API keys, and secrets"),
            ("Physical", "Offices, data centers, server rooms, and access control systems"),
            ("Communication", "Email, Slack, Teams, Zoom, and telephony systems"),
            ("Backup", "Backup systems, disaster recovery sites, and replication infrastructure"),
            ("Compliance", "Policies, controls, audit evidence, and training records"),
            ("AI", "AI platforms, LLMs, AI agents, and prompt repositories"),
            ("Business Process", "Onboarding, offboarding, incident response, and risk management processes"),
        ]
        cat_objs = {}
        for cat_name, cat_desc in categories:
            cat_result = await session.execute(select(AssetCategory).where(AssetCategory.name == cat_name))
            cat = cat_result.scalar_one_or_none()
            if not cat:
                cat = AssetCategory(name=cat_name, description=cat_desc)
                session.add(cat)
                await session.flush()
            cat_objs[cat_name] = cat

        # 6. Seed Assets
        assets_data = [
            ("MacBook Pro M2", "Developer laptop", cat_objs["Device"], "hybrid@123", "Critical"),
            ("Production DB", "Main application database", cat_objs["Database"], "hybrid@123", "Critical"),
            ("AWS EC2 Instance", "Web server instance", cat_objs["Cloud Resource"], "hybrid@123", "High"),
            ("HR System", "Personnel management system", cat_objs["Application"], "hybrid@123", "Medium"),
        ]

        for name, desc, cat, admin_pw, crit in assets_data:
            a_result = await session.execute(select(Asset).where(Asset.name == name))
            if not a_result.scalar_one_or_none():
                asset = Asset(
                    organization_id=hybrid_org.id,
                    name=name,
                    description=desc,
                    category_id=cat.id,
                    criticality=crit,
                    risk_level="Medium",
                    owner_id=hybrid_admin.id,
                )
                session.add(asset)

        # 7. Seed People Assets
        people_data = [
            ("Alice Johnson", "alice@hybrid.com", "Administrator", "Engineering", "Engineering Manager", "Critical"),
            ("Bob Smith", "bob@hybrid.com", "Developer", "Engineering", "Senior Developer", "High"),
            ("Carol Williams", "carol@hybrid.com", "Security Personnel", "Security", "Security Analyst", "Critical"),
            ("David Brown", "david@hybrid.com", "Employee", "Finance", "Financial Analyst", "Medium"),
            ("Eve Davis", "eve@hybrid.com", "Contractor", "Engineering", "UI/UX Contractor", "Low"),
        ]
        for name, email, atype, dept, title, _ in people_data:
            existing = await session.execute(
                select(PeopleAsset).where(PeopleAsset.name == name, PeopleAsset.organization_id == hybrid_org.id)
            )
            if not existing.scalar_one_or_none():
                session.add(PeopleAsset(
                    organization_id=hybrid_org.id,
                    name=name,
                    email=email,
                    asset_type=atype,
                    department=dept,
                    job_title=title,
                    status="Active",
                    created_by=hybrid_admin.id,
                ))
        # 8. Seed Platform Admin
        platform_user_result = await session.execute(select(PlatformUser).where(PlatformUser.email == "admin@appxcess.com"))
        platform_user = platform_user_result.scalar_one_or_none()
        if not platform_user:
            platform_user = PlatformUser(
                email="admin@appxcess.com",
                hashed_password=get_password_hash("admin@123"),
                full_name="AppXcess Super Admin",
                is_active=True
            )
            session.add(platform_user)
            await session.flush()
            
            # Seed Platform Role
            platform_role_result = await session.execute(select(PlatformRole).where(PlatformRole.name == "platform_super_admin"))
            platform_role = platform_role_result.scalar_one_or_none()
            if not platform_role:
                platform_role = PlatformRole(
                    name="platform_super_admin",
                    description="Full access to platform administration"
                )
                session.add(platform_role)
                await session.flush()
            
            session.add(PlatformUserRole(user_id=platform_user.id, role_id=platform_role.id))
        else:
            platform_user.hashed_password = get_password_hash("admin@123")

        # 9. Seed Compliance Frameworks
        frameworks_data = [
            ("SOC 2", "System and Organization Controls 2", "2017"),
            ("ISO 27001", "Information Security Management Systems", "2022"),
            ("GDPR", "General Data Protection Regulation", "2016"),
            ("HIPAA", "Health Insurance Portability and Accountability Act", "1996"),
            ("PCI DSS", "Payment Card Industry Data Security Standard", "4.0"),
            ("NIST CSF", "NIST Cybersecurity Framework", "2.0"),
            ("CIS Controls", "Center for Internet Security Critical Security Controls", "v8"),
            ("CSA CCM", "Cloud Security Alliance Cloud Controls Matrix", "v4")
        ]

        for name, desc, version in frameworks_data:
            f_result = await session.execute(select(Framework).where(Framework.name == name))
            framework = f_result.scalar_one_or_none()
            if not framework:
                framework = Framework(name=name, description=desc, version=version)
                session.add(framework)
                await session.flush()
            else:
                framework.description = desc
                framework.version = version
            
            # Special handling for ISO 27001 if file exists
            if name == "ISO 27001":
                iso_reqs = parse_full_iso_file('full_iso.txt')
                if iso_reqs:
                    print(f"Refreshing ISO 27001 requirements ({len(iso_reqs)} found)...")
                    from sqlalchemy import delete
                    await session.execute(delete(Requirement).where(Requirement.framework_id == framework.id))
                    for data in iso_reqs:
                        req = Requirement(
                            framework_id=framework.id,
                            code=data['code'],
                            name=data['name'],
                            description=data['description'],
                            status=data['status'],
                        )
                        session.add(req)
                    await session.flush()

                    # Seed controls from iso_27001.txt
                    iso_controls = parse_iso_controls_file('iso_27001.txt')
                    if iso_controls:
                        print(f"Seeding {len(iso_controls)} ISO 27001 controls...")
                        for cdata in iso_controls:
                            existing = await session.execute(
                                select(Control).where(Control.code == cdata['code'], Control.organization_id == org.id)
                            )
                            if not existing.scalar_one_or_none():
                                ctrl = Control(
                                    organization_id=org.id,
                                    code=cdata['code'],
                                    name=cdata['name'],
                                    description=cdata['description'],
                                    status=ComplianceStatus.not_applicable,
                                )
                                session.add(ctrl)
                        await session.flush()

                    # Link ISO-pattern controls to requirements via ControlMapping
                    print("Creating ControlMappings for ISO 27001...")
                    all_ctrl_result = await session.execute(
                        select(Control).where(Control.organization_id == org.id)
                    )
                    all_req_result = await session.execute(
                        select(Requirement).where(Requirement.framework_id == framework.id)
                    )
                    all_controls = all_ctrl_result.scalars().all()
                    all_reqs = all_req_result.scalars().all()

                    # Only map controls that match ISO pattern (e.g. "5.1", "8.34")
                    iso_controls = [c for c in all_controls if re.match(r'^\d+\.\d+$', c.code)]
                    iso_control_ids = [c.id for c in iso_controls]

                    # Delete existing mappings for ISO controls
                    if iso_control_ids:
                        from sqlalchemy import delete
                        await session.execute(
                            delete(ControlMapping).where(ControlMapping.control_id.in_(iso_control_ids))
                        )
                        await session.flush()

                    req_by_code: dict[str, Requirement] = {r.code: r for r in all_reqs}
                    default_req = all_reqs[0] if all_reqs else None

                    for ctrl in iso_controls:
                        matched = req_by_code.get(ctrl.code)
                        if not matched:
                            for req_code, req in req_by_code.items():
                                if ctrl.code.startswith(req_code + '.') or ctrl.code == req_code:
                                    matched = req
                                    break
                        if not matched:
                            matched = default_req
                        if matched:
                            session.add(ControlMapping(control_id=ctrl.id, requirement_id=matched.id))
                    await session.flush()

                    continue # Skip the default requirement logic
            
            # Default requirement logic for other frameworks or if ISO file missing
            req_check = await session.execute(
                select(Requirement).where(Requirement.framework_id == framework.id).limit(1)
            )
            if not req_check.scalar_one_or_none():
                req = Requirement(
                    framework_id=framework.id,
                    code="REQ-001",
                    name=f"Sample {name} Requirement",
                    description=f"This is a placeholder requirement for {name}."
                )
                session.add(req)

        try:
            await session.commit()
            print("Successfully seeded organization, roles, permissions, admin user, assets, and platform staff")
        except Exception as e:
            await session.rollback()
            print(f"Error seeding data: {e}")

if __name__ == "__main__":
    asyncio.run(seed_data())
