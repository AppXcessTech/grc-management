#!/usr/bin/env python3
"""Explore GitHub Steampipe table schemas."""
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

    test_tables = [
        'github_my_repository',
        'github_repository', 
        'github_my_organization',
        'github_user',
        'github_organization_member',
    ]
    
    for table in test_tables:
        # Try to get columns
        sql = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position;"
        cmd = ['steampipe', 'query', sql, '--install-dir', temp_dir, '--output', 'json']
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                rows = data.get('rows', [])
                print(f'\n{table} columns:')
                for row in rows:
                    print(f'  {row.get("column_name")} ({row.get("data_type")})')
            else:
                print(f'\n{table}: error getting columns - {res.stderr[:100]}')
        except Exception as e:
            print(f'\n{table}: {e}')
