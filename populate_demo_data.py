
import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add current directory to path to import local modules
sys.path.append(os.getcwd())

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    print("Error: MONGODB_URI not found in .env")
    exit(1)

client = AsyncIOMotorClient(MONGODB_URI)
db = client.get_default_database()

async def seed_timeline_for_email(email, db):
    timeline_coll = db["medical_timeline"]
    # Clear existing timeline for this user
    await timeline_coll.delete_many({"patient_email": email})
    
    events = [
        {
            "patient_email": email,
            "date": "2024-01-15",
            "type": "Diagnosis",
            "details": "Initial consultation with Dr. Sharma. Reported lump in left breast."
        },
        {
            "patient_email": email,
            "date": "2024-01-20",
            "type": "Procedure",
            "details": "Ultrasound guided biopsy performed."
        },
        {
            "patient_email": email,
            "date": "2024-01-25",
            "type": "Lab Result",
            "details": "Pathology confirms Invasive Ductal Carcinoma (Grade 2)."
        },
        {
            "patient_email": email,
            "date": "2024-02-01",
            "type": "Treatment",
            "details": "Started neo-adjuvant chemotherapy (AC regimen cycle 1)."
        }
    ]
    
    await timeline_coll.insert_many(events)
    print(f"Inserted {len(events)} timeline events for {email}.")

    # Insert a Mock PCP Case (for AI Insights)
    cases_coll = db["onco_cases"]
    existing_case = await cases_coll.find_one({"patient_email": email})
    
    if not existing_case:
        mock_case = {
            "case_id": 999 if email == "demo@example.com" else 998,
            "patient_name": "Demo Patient" if email == "demo@example.com" else "Admin Patient",
            "patient_email": email,
            "risk_label": "High_Risk",
            "risk_score": 0.85,
            "status": "REVIEWED",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notes": "Generated demo case"
        }
        await cases_coll.insert_one(mock_case)
        print(f"Inserted mock PCP case for {email}.")
    else:
        print(f"PCP case already exists for {email}.")

async def seed_data():
    print("Seeding demo data...")
    
    # 1. Create a generic demo user
    username = "demo"
    password = "demo123"
    patient_email = "demo@example.com"
    
    try:
        from patient_app.auth import get_password_hash
        hashed_password = get_password_hash(password)
        
        users_coll = db["patient_users"]
        existing_user = await users_coll.find_one({"username": username})
        
        if not existing_user:
            await users_coll.insert_one({
                "username": username,
                "email": patient_email,
                "password": hashed_password,
                "created_at": datetime.now()
            })
            print(f"✅ Created demo user: {username} / {password}")
        else:
            print(f"ℹ️ Demo user '{username}' already exists (Password: demo123).")
            
        # 2. Also seed for the admin email in .env
        target_email = os.getenv("ADMIN_EMAIL", "nihanmohammed95@gmail.com")
        print(f"Targeting email: {target_email}")
        
        # Seed timeline for BOTH demo and admin
        for email in [patient_email, target_email]:
            await seed_timeline_for_email(email, db)
            
    except Exception as e:
        print(f"❌ Error creating data: {e}")
        import traceback
        traceback.print_exc()

    print("✅ Seed data populated successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
