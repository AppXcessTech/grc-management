import os
import re
import time
import requests

BASE_URL = "https://raw.githubusercontent.com/turbot/steampipe-plugin-bitbucket/refs/heads/main/docs/tables"

TABLES = [
    "bitbucket_repository",              # Repository
    "bitbucket_my_repository",           # Repository
    "bitbucket_branch_restriction",      # Repository (branch protection equivalent)
    "bitbucket_project",                 # Application
    "bitbucket_my_project",              # Application
    "bitbucket_workspace",               # Organization
    "bitbucket_my_workspace",            # Organization
    "bitbucket_workspace_member",        # Group
]


OUTPUT_ROOT = "./"

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
