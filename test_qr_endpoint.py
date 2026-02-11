import asyncio
import httpx
from patient_app.auth import create_access_token, users_collection
from datetime import timedelta

async def test_qr_endpoint():
    """Test the QR code endpoint directly"""
    try:
        # First, let's get a user token
        user = await users_collection.find_one({"username": "nihan9t9"})
        if not user:
            print("User nihan9t9 not found")
            return
            
        # Create a token for the user
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user["username"]}, expires_delta=access_token_expires
        )
        
        print(f"User found: {user['username']}")
        print(f"Patient ID: {user.get('patient_id', 'Not set')}")
        
        # Test the dashboard endpoint
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get("http://localhost:8000/patient/dashboard", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("Dashboard response received successfully")
                print(f"Patient: {data.get('patient')}")
                print(f"QR Code data present: {'qr_code' in data}")
                if 'qr_code' in data:
                    print(f"QR Code length: {len(data['qr_code']) if data['qr_code'] else 0}")
                    if data['qr_code']:
                        print("QR Code generated successfully!")
                        print(f"QR Code preview: {data['qr_code'][:50]}...")
                    else:
                        print("QR Code is None or empty")
                else:
                    print("QR Code field not in response")
                
                # Print user data for debugging
                print(f"Full user data: {user}")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"Error testing QR endpoint: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qr_endpoint())