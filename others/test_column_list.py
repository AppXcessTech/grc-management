#!/usr/bin/env python3
"""Test which columns work for my_repository and verify qualifier queries."""
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

    # Get columns for my_repository excluding custom_properties
    cols_to_exclude = ['custom_properties', 'sp_connection_name', 'sp_ctx', '_ctx']
    
    sql = "SELECT column_name FROM information_schema.columns WHERE table_name = 'github_my_repository' ORDER BY ordinal_position;"
    cmd = ['steampipe', 'query', sql, '--install-dir', temp_dir, '--output', 'json']
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    data = json.loads(res.stdout)
    all_cols = [r['column_name'] for r in data.get('rows', [])]
    safe_cols = [c for c in all_cols if c not in cols_to_exclude]
    print(f"Total columns: {len(all_cols)}, Safe columns: {len(safe_cols)}")
    
    # Test with safe columns
    cols_str = ', '.join(safe_cols)
    sql2 = f"SELECT {cols_str} FROM github_my_repository;"
    cmd2 = ['steampipe', 'query', sql2, '--install-dir', temp_dir, '--output', 'json']
    res2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
    
    if res2.returncode == 0:
        data2 = json.loads(res2.stdout)
        rows = data2.get('rows', [])
        print(f"\ngithub_my_repository: {len(rows)} rows")
        for r in rows:
            print(f"  name_with_owner={r.get('name_with_owner')}, owner_login={r.get('owner_login')}, name={r.get('name')}")
        
        # Extract context
        name_with_owners = [r['name_with_owner'] for r in rows if r.get('name_with_owner')]
        owner_logins = set(r['owner_login'] for r in rows if r.get('owner_login'))
        print(f"\nRepos ({len(name_with_owners)}): {name_with_owners}")
        print(f"Owners: {owner_logins}")
        
        # Test querying org-scoped table with qualifier
        for org in owner_logins:
            print(f"\n--- Testing org-scoped queries for '{org}' ---")
            
            # github_organization_member
            sql3 = f"select login, role, organization from github_organization_member where organization = '{org}';"
            cmd3 = ['steampipe', 'query', sql3, '--install-dir', temp_dir, '--output', 'json']
            res3 = subprocess.run(cmd3, capture_output=True, text=True, timeout=60)
            if res3.returncode == 0:
                data3 = json.loads(res3.stdout)
                members = data3.get('rows', [])
                print(f"  github_organization_member: {len(members)} members")
                for m in members[:3]:
                    print(f"    login={m.get('login')}, role={m.get('role')}")
            else:
                print(f"  github_organization_member: ERROR {res3.stderr[:100]}")
            
            # github_team with org qualifier
            sql4 = f"select slug, name, organization from github_team where organization = '{org}';"
            cmd4 = ['steampipe', 'query', sql4, '--install-dir', temp_dir, '--output', 'json']
            res4 = subprocess.run(cmd4, capture_output=True, text=True, timeout=60)
            if res4.returncode == 0:
                data4 = json.loads(res4.stdout)
                teams = data4.get('rows', [])
                print(f"  github_team: {len(teams)} teams")
                for t in teams[:3]:
                    print(f"    slug={t.get('slug')}, name={t.get('name')}")
            else:
                print(f"  github_team: ERROR {res4.stderr[:100]}")
        
        # Test repo-scoped tables
        for nwo in name_with_owners[:2]:  # Just test first 2
            print(f"\n--- Testing repo-scoped queries for '{nwo}' ---")
            
            # github_branch_protection
            sql5 = f"select * from github_branch_protection where repository_full_name = '{nwo}';"
            cmd5 = ['steampipe', 'query', sql5, '--install-dir', temp_dir, '--output', 'json']
            res5 = subprocess.run(cmd5, capture_output=True, text=True, timeout=60)
            if res5.returncode == 0:
                data5 = json.loads(res5.stdout)
                bp = data5.get('rows', [])
                print(f"  github_branch_protection: {len(bp)} rows")
            else:
                print(f"  github_branch_protection: ERROR {res5.stderr[:100]}")
            
            # github_repository with full_name
            sql6 = f"select full_name, name from github_repository where full_name = '{nwo}';"
            cmd6 = ['steampipe', 'query', sql6, '--install-dir', temp_dir, '--output', 'json']
            res6 = subprocess.run(cmd6, capture_output=True, text=True, timeout=60)
            if res6.returncode == 0:
                data6 = json.loads(res6.stdout)
                repo = data6.get('rows', [])
                print(f"  github_repository: {len(repo)} rows")
            else:
                print(f"  github_repository: ERROR {res6.stderr[:100]}")
        
        # Test github_user with login
        my_login = list(owner_logins)[0] if owner_logins else ''
        if my_login:
            print(f"\n--- Testing github_user for '{my_login}' ---")
            sql7 = f"select login, name, email from github_user where login = '{my_login}';"
            cmd7 = ['steampipe', 'query', sql7, '--install-dir', temp_dir, '--output', 'json']
            res7 = subprocess.run(cmd7, capture_output=True, text=True, timeout=60)
            if res7.returncode == 0:
                data7 = json.loads(res7.stdout)
                users = data7.get('rows', [])
                print(f"  github_user: {len(users)} rows")
    else:
        print(f"Error: {res2.stderr[:500]}")
