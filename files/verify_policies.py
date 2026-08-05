import asyncio
import httpx
import os

BASE_URL = "http://localhost:8000/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
POLICIES_URL = f"{BASE_URL}/policies"

async def verify():
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("Logging in...")
        response = await client.post(
            LOGIN_URL,
            data={"username": "admin@appxcess.com", "password": "admin@123"}
        )
        if response.status_code != 200:
            print(f"Login failed: {response.text}")
            return
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get user info to get org_id
        # We know org_id is likely 1 from seed
        org_id = 1
        
        # 2. Create Policy
        print("Creating policy...")
        response = await client.post(
            POLICIES_URL + "/",
            json={
                "name": "Information Security Policy",
                "description": "Main ISMS policy",
                "category": "information_security",
                "organization_id": org_id
            },
            headers=headers
        )
        if response.status_code != 201:
            print(f"Policy creation failed: {response.text}")
            return
        
        policy = response.json()
        policy_id = policy["id"]
        print(f"Policy created with ID: {policy_id}")
        
        # 3. List Policies
        print("Listing policies...")
        response = await client.get(POLICIES_URL + "/", headers=headers)
        print(f"Found {len(response.json())} policies")
        
        # 4. Upload Policy Version
        print("Uploading policy version...")
        with open("test_policy.txt", "w") as f:
            f.write("This is a test policy document.")
            
        with open("test_policy.txt", "rb") as f:
            response = await client.post(
                f"{POLICIES_URL}/{policy_id}/versions",
                data={"notes": "Initial version"},
                files={"file": ("test_policy.txt", f, "text/plain")},
                headers=headers
            )
        
        os.remove("test_policy.txt")
        
        if response.status_code != 201:
            print(f"Version upload failed: {response.text}")
            return
        
        version = response.json()
        version_id = version["id"]
        print(f"Version created with ID: {version_id}")
        
        # 5. Publish Version
        print("Publishing version...")
        response = await client.post(
            f"{POLICIES_URL}/versions/{version_id}/publish",
            headers=headers
        )
        if response.status_code != 200:
            print(f"Publish failed: {response.text}")
            return
        print("Version published")
        
        # 6. Acknowledge Policy
        print("Acknowledging policy...")
        response = await client.post(
            f"{POLICIES_URL}/versions/{version_id}/acknowledge",
            headers=headers
        )
        if response.status_code != 201:
            print(f"Acknowledgement failed: {response.text}")
            return
        print("Policy acknowledged")
        
        # 7. List Acknowledgements
        print("Listing acknowledgements...")
        response = await client.get(
            f"{POLICIES_URL}/{policy_id}/acknowledgements",
            headers=headers
        )
        print(f"Found {len(response.json())} acknowledgements")
        
        print("Verification completed successfully!")

if __name__ == "__main__":
    asyncio.run(verify())
