#!/usr/bin/env python3
"""Test which columns are safe for my_repository by testing binary search."""
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

    # Get all columns
    sql = "SELECT column_name FROM information_schema.columns WHERE table_name = 'github_my_repository' ORDER BY ordinal_position;"
    cmd = ['steampipe', 'query', sql, '--install-dir', temp_dir, '--output', 'json']
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(res.stdout)
    all_cols = [r['column_name'] for r in data.get('rows', [])]
    
    # Columns we know cause issues
    known_bad = ['custom_properties', 'hooks', 'sp_connection_name', 'sp_ctx', '_ctx']
    
    # Try essential columns only first
    essential = ['name', 'name_with_owner', 'owner_login', 'id', 'node_id', 
                 'description', 'url', 'visibility', 'is_private', 'is_fork',
                 'is_in_organization', 'created_at', 'updated_at', 'pushed_at',
                 'primary_language', 'license_info', 'default_branch_ref',
                 'topics', 'fork_count', 'stargazer_count']
    
    cols_str = ', '.join(essential)
    sql2 = f"SELECT {cols_str} FROM github_my_repository;"
    cmd2 = ['steampipe', 'query', sql2, '--install-dir', temp_dir, '--output', 'json']
    res2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
    
    if res2.returncode == 0:
        data2 = json.loads(res2.stdout)
        rows = data2.get('rows', [])
        print(f"SUCCESS! github_my_repository: {len(rows)} rows using essential columns")
        for r in rows:
            print(f"  name_with_owner={r.get('name_with_owner')}, owner_login={r.get('owner_login')}")
        
        # Now test qualifier queries
        name_with_owners = [r['name_with_owner'] for r in rows if r.get('name_with_owner')]
        owner_logins = set(r['owner_login'] for r in rows if r.get('owner_login'))
        
        # Test org-scoped
        for org in owner_logins:
            print(f"\n--- Organization: {org} ---")
            
            # github_organization_member
            sql3 = f"select * from github_organization_member where organization = '{org}';"
            cmd3 = ['steampipe', 'query', sql3, '--install-dir', temp_dir, '--output', 'json']
            res3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=60)
            if res3.returncode == 0:
                rows3 = json.loads(res3.stdout).get('rows', [])
                print(f"  github_organization_member: {len(rows3)} members")
            else:
                print(f"  github_organization_member: {res3.stderr[:100]}")
            
            # github_team
            sql3b = f"select * from github_team where organization = '{org}';"
            cmd3b = ['steampipe', 'query', sql3b, '--install-dir', temp_dir, '--output', 'json']
            res3b = subprocess.run(cmd3b, capture_output=True, text=True, timeout=60)
            if res3b.returncode == 0:
                rows3b = json.loads(res3b.stdout).get('rows', [])
                print(f"  github_team: {len(rows3b)} teams")
            else:
                print(f"  github_team: {res3b.stderr[:100]}")
        
        # Test repo-scoped
        for nwo in name_with_owners[:3]:
            print(f"\n--- Repository: {nwo} ---")
            for tbl in ['github_branch_protection', 'github_code_owner', 
                        'github_actions_repository_secret', 'github_repository_ruleset',
                        'github_repository_deployment', 'github_repository_environment']:
                sql4 = f"select * from {tbl} where repository_full_name = '{nwo}';"
                cmd4 = ['steampipe', 'query', sql4, '--install-dir', temp_dir, '--output', 'json']
                try:
                    res4 = subprocess.run(cmd4, capture_output=True, text=True, timeout=30)
                    if res4.returncode == 0:
                        rows4 = json.loads(res4.stdout).get('rows', [])
                        print(f"  {tbl}: {len(rows4)} rows")
                    else:
                        print(f"  {tbl}: ERROR {res4.stderr[:80]}")
                except subprocess.TimeoutExpired:
                    print(f"  {tbl}: TIMEOUT")
    else:
        print(f"Essential columns failed: {res2.stderr[:500]}")
        
        # Try even more minimal
        min_cols = ['name', 'name_with_owner', 'owner_login', 'id', 'node_id']
        sql5 = f"SELECT {', '.join(min_cols)} FROM github_my_repository;"
        cmd5 = ['steampipe', 'query', sql5, '--install-dir', temp_dir, '--output', 'json']
        res5 = subprocess.run(cmd5, capture_output=True, text=True, timeout=120)
        if res5.returncode == 0:
            print(f"Minimal columns worked! {len(json.loads(res5.stdout).get('rows', []))} rows")
        else:
            print(f"Minimal also failed: {res5.stderr[:500]}")
