#!/usr/bin/env python3
"""Test Steampipe GitHub queries with and without qualifiers."""
import json
import tempfile
import subprocess
from pathlib import Path

with open('data/github_config/org_3.json') as f:
    cfg = json.load(f)
token = cfg.get('github_token', '')

with tempfile.TemporaryDirectory() as temp_dir:
    steampipe_home = Path.home() / '.steampipe'
    for folder in ['plugins', 'db', 'internal']:
        src = steampipe_home / folder
        dst = Path(temp_dir) / folder
        if src.exists() and not dst.exists():
            dst.symlink_to(src, target_is_directory=True)

    config_dir = Path(temp_dir) / 'config'
    config_dir.mkdir(parents=True, exist_ok=True)
    spc = f'''connection "github" {{
  plugin = "github"
  token  = "{token}"
}}
'''
    (config_dir / 'github.spc').write_text(spc)

    tests = [
        # my_repository with explicit columns (avoids custom_property_values issue)
        ("select full_name, name, owner_login, description from github_my_repository;",
         "my_repo (explicit cols)"),
        
        # my_organization
        ("select * from github_my_organization;",
         "my_org"),
        
        # my_repository with select *
        ("select * from github_my_repository limit 1;",
         "my_repo (select *)"),
    ]

    for sql, label in tests:
        cmd = ['steampipe', 'query', sql, '--install-dir', temp_dir, '--output', 'json']
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                rows = data.get('rows', [])
                print(f'{label}: {len(rows)} rows')
                if rows:
                    print(f'  First row keys: {list(rows[0].keys())[:10]}')
                    print(f'  full_name: {rows[0].get("full_name", "N/A")}')
                    print(f'  owner_login: {rows[0].get("owner_login", "N/A")}')
                    print(f'  organization: {rows[0].get("organization", "N/A")}')
            else:
                print(f'{label}: ERROR rc={res.returncode}')
                stderr = res.stderr[:300] if res.stderr else ''
                print(f'  Stderr: {stderr}')
        except subprocess.TimeoutExpired:
            print(f'{label}: TIMEOUT')
        except json.JSONDecodeError as e:
            print(f'{label}: JSON ERROR: {e}')
            print(f'  stdout starts with: {res.stdout[:200]}')
