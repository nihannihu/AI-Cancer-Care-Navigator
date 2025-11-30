import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def clear_all_users():
    MONGODB_URI = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client["onco_navigator"]
    users_collection = db["patient_users"]
    
    # Delete ALL users
    result = await users_collection.delete_many({})
    print(f"Deleted {result.deleted_count} user(s) from database")
    
    # Verify empty
    count = await users_collection.count_documents({})
    print(f"Remaining users in database: {count}")

if __name__ == "__main__":
    asyncio.run(clear_all_users())
