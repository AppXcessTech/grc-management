import os
import re
import time
import requests

BASE_URL = "https://raw.githubusercontent.com/theapsgroup/steampipe-plugin-gitlab/main/docs/tables"

TABLES = [
    "gitlab_project",
    "gitlab_my_project",
    "gitlab_project_protected_branch",
    "gitlab_project_repository",
    "gitlab_setting",
    "gitlab_group",
    "gitlab_group_subgroup",
    "gitlab_group_project",
    "gitlab_group_member",
    "gitlab_project_member",
    "gitlab_user",
    "gitlab_user_event",
    "gitlab_application",
    "gitlab_group_variable",
    "gitlab_project_variable",
    "gitlab_instance_variable",
    "gitlab_project_container_registry",
    "gitlab_project_pipeline",
    "gitlab_project_pipeline_detail",
    "gitlab_project_job",
    "gitlab_project_deployment",
    "gitlab_hook",
    "gitlab_group_access_request",
    "gitlab_project_access_request",
    "gitlab_group_push_rule",
]


OUTPUT_ROOT = "gitlab_queries"

os.makedirs(OUTPUT_ROOT, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ### Heading followed by the next sql+postgres block
PATTERN = re.compile(
    r"###\s+(.*?)\s*\n(?:.*?\n)*?```sql(?:\+postgres)?\s*\n(.*?)```",
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
