import os
import re
import time
import requests

BASE_URL = "https://raw.githubusercontent.com/turbot/steampipe-plugin-github/main/docs/tables"

TABLES = [
    "github_my_repository",                      # Repository (personal account) -- core inventory
    "github_repository",                         # Repository (org-scoped) -- core inventory
    "github_branch_protection",                  # Repository -- branch protection, requires_review
    "github_repository_ruleset",                 # Repository -- newer rules engine, may supersede branch protection
    "github_organization_ruleset",               # Repository (org-wide rules)
    "github_repository_collaborator",            # Repository -- direct collaborator access review
    "github_code_owner",                         # Repository -- CODEOWNERS enforcement
    "github_community_profile",                  # Repository -- SECURITY.md / LICENSE / CoC presence

    "github_repository_vulnerability_alert",     # Vulnerability -- Dependabot alerts (per repo)
    "github_organization_dependabot_alert",      # Vulnerability -- Dependabot alerts (org rollup)
    "github_repository_dependabot_alert",        # Vulnerability -- may duplicate above, verify per plugin version
    "github_repository_sbom",                    # Vulnerability -- SBOM / dependency evidence

    "github_organization_member",                # Identity -- org membership, admin flags
    "github_organization_external_identity",     # Identity -- SSO/SAML linkage
    "github_user",                               # Identity -- user profile data
    "github_my_organization",                    # Identity (personal account context)

    "github_team",                               # Group -- team structure
    "github_team_member",                        # Group -- team membership
    "github_team_repository",                    # Group -- team repo access mapping

    "github_actions_repository_secret",          # Secret -- Actions secret existence/naming
    "github_actions_organization_variable",      # Secret/config -- org-level Actions variables
    "github_actions_repository_variable",        # Secret/config -- repo-level Actions variables

    "github_workflow",                           # Pipeline -- CI/CD workflow inventory
    "github_actions_repository_workflow_run",    # Pipeline -- execution history, approval gates
    "github_actions_repository_workflow_job",    # Pipeline -- job-level detail, runner exposure
    "github_actions_repository_runner",          # Pipeline -- self-hosted runner inventory
    "github_repository_environment",             # Pipeline/Deployment -- environment protection rules

    "github_audit_log",                          # Logging -- org-level audit trail (org accounts only)

    "github_package",                            # Artifact/Package -- package registry inventory
    "github_package_version",                    # Artifact/Package -- package version detail
    "github_actions_artifact",                   # Artifact/Package -- CI build artifacts

    "github_repository_deployment",              # Deployment -- deployment records
]

OUTPUT_ROOT = "queries"

os.makedirs(OUTPUT_ROOT, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ### Heading followed by the next sql+postgres block
PATTERN = re.compile(
    r"###\s+(.*?)\n.*?```sql\+postgres\s*(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

for table in TABLES:
    url = f"{BASE_URL}/{table}.md"

    print(f"Fetching {table}...")

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        markdown = response.text

        matches = PATTERN.findall(markdown)

        if not matches:
            print("❌ No queries found.")
            continue

        table_dir = os.path.join(OUTPUT_ROOT, table)
        os.makedirs(table_dir, exist_ok=True)

        for heading, query in matches:

            # Convert heading into a safe filename
            filename = heading.lower().strip()
            filename = re.sub(r"[^\w\s-]", "", filename)
            filename = re.sub(r"\s+", "_", filename)

            output_file = os.path.join(table_dir, f"{filename}.sql")

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(query.strip())

        print(f"✅ Saved {len(matches)} queries.")

        time.sleep(0.5)

    except Exception as e:
        print(f"❌ {table}: {e}")
