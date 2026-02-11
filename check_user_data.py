import asyncio
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def check_user_data():
    try:
        from patient_app.auth import get_db
        
        # Get database connection
        db = get_db()
        
        # Get all users
        users = await db['patient_users'].find().to_list(length=10)
        
        print("User data in database:")
        print("-" * 50)
        
        for user in users:
            print(f"Username: {user.get('username')}")
            print(f"Email: {user.get('email')}")
            print(f"Patient ID: {user.get('patient_id')}")
            print(f"All data: {user}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Error checking user data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_data())