import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def clear_user(username):
    MONGODB_URI = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client["onco_navigator"]
    users_collection = db["patient_users"]
    
    result = await users_collection.delete_many({"username": username})
    print(f"Deleted {result.deleted_count} user(s) with username: {username}")
    
    # List all users
    users = await users_collection.find().to_list(length=100)
    print(f"\nRemaining users: {len(users)}")
    for user in users:
        print(f"  - {user.get('username')} ({user.get('email')})")

if __name__ == "__main__":
    asyncio.run(clear_user("nihan9t9"))
