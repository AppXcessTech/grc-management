#!/usr/bin/env python3
"""Test the GitHub import end-to-end via the API."""
import json
import sys
import time
import httpx
import jwt
from datetime import datetime, timezone, timedelta

BASE_URL = "http://127.0.0.1:8000"
SECRET_KEY = "super-secret-key-change-me"
ALGORITHM = "HS256"

# --- Step 1: Create a valid JWT token ---
print("=" * 60)
print("STEP 1: Create auth token for admin@hybrid.com (super_admin, org_id=3)")
print("=" * 60)

payload = {
    "sub": "admin@hybrid.com",
    "exp": datetime.now(timezone.utc) + timedelta(hours=1)
}
token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(f"  Token created: {token[:40]}...")
headers = {"Authorization": f"Bearer {token}"}

# --- Step 2: Test the token by listing assets ---
print("\n" + "=" * 60)
print("STEP 2: Test authentication")
print("=" * 60)

try:
    resp = httpx.get(f"{BASE_URL}/api/assets/", headers=headers, timeout=10)
    print(f"  GET /api/assets/ -> {resp.status_code}")
    if resp.status_code == 200:
        print("  Authentication works!")
    else:
        print(f"  Auth failed: {resp.text[:300]}")
        sys.exit(1)
except Exception as e:
    print(f"  Error: {e}")
    sys.exit(1)

# --- Step 3: Test GitHub connection ---
print("\n" + "=" * 60)
print("STEP 3: Test GitHub connection")
print("=" * 60)

try:
    resp = httpx.post(f"{BASE_URL}/api/integrations/github/test", headers=headers, timeout=30)
    print(f"  POST /api/integrations/github/test -> {resp.status_code}")
    print(f"    Response: {json.dumps(resp.json(), indent=4)}")
except Exception as e:
    print(f"  Error: {e}")

# --- Step 4: Start sync ---
print("\n" + "=" * 60)
print("STEP 4: Start GitHub import (sync)")
print("=" * 60)

try:
    resp = httpx.post(f"{BASE_URL}/api/integrations/github/sync", headers=headers, timeout=15)
    print(f"  POST /api/integrations/github/sync -> {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"    Response: {json.dumps(result, indent=4)}")
        job_id = result.get("job_id")
        
        if job_id:
            # --- Step 5: Poll for status ---
            print(f"\n{'=' * 60}")
            print("STEP 5: Poll sync status")
            print("=" * 60)
            
            max_polls = 120  # 10 minutes max
            poll_interval = 5  # seconds
            start_time = time.time()
            
            for i in range(max_polls):
                time.sleep(poll_interval)
                elapsed = int(time.time() - start_time)
                try:
                    status_resp = httpx.get(
                        f"{BASE_URL}/api/integrations/github/sync-status/{job_id}",
                        headers=headers,
                        timeout=10,
                    )
                    if status_resp.status_code == 200:
                        status = status_resp.json()
                        print(f"  [{elapsed}s] status={status.get('status')} "
                              f"progress={status.get('progress')}% "
                              f"resources_found={status.get('resources_found')} "
                              f"assets_stored={status.get('assets_stored')} "
                              f"phase={status.get('phase')} "
                              f"msg={status.get('message','')[:60]}")
                        
                        if status.get("status") in ("completed", "error"):
                            print(f"\n  FINAL STATUS:")
                            # Pretty print key fields
                            for key in ['status', 'progress', 'phase', 'message', 
                                        'resources_discovered', 'assets_stored', 
                                        'relationships_created', 'error', 'warnings']:
                                val = status.get(key)
                                if val:
                                    if isinstance(val, list) and len(val) > 3:
                                        print(f"    {key}: {val[:3]}... ({len(val)} total)")
                                    else:
                                        print(f"    {key}: {val}")
                            break
                    else:
                        print(f"  [{elapsed}s] Error {status_resp.status_code}: {status_resp.text[:200]}")
                except Exception as e:
                    print(f"  [{elapsed}s] Exception: {e}")
            else:
                print(f"\n  Timed out after 10 minutes")
    else:
        print(f"    Error: {resp.text[:500]}")
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

# --- Step 6: Check assets created ---
print("\n" + "=" * 60)
print("STEP 6: Check created assets")
print("=" * 60)

try:
    resp = httpx.get(f"{BASE_URL}/api/assets/", headers=headers, timeout=10)
    if resp.status_code == 200:
        all_assets = resp.json()
        print(f"  Total assets: {len(all_assets)}")
        
        # Count by source
        sources = {}
        for a in all_assets:
            src = a.get('source', 'unknown')
            sources[src] = sources.get(src, 0) + 1
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"    {src}: {count} assets")
        
        # Show first 5 assets
        print(f"\n  Recent assets (first 5):")
        for a in all_assets[:5]:
            print(f"    - {a.get('display_name')} [{a.get('canonical_type')}] source={a.get('source')}")
    else:
        print(f"  Error: {resp.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
