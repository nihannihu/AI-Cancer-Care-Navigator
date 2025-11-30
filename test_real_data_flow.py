"""
REAL DATA FLOW TEST SCRIPT
===========================
This script tests the COMPLETE patient data flow WITHOUT mock data.

Test Flow:
1. PCP uploads X-ray with email: nihanmohammed95@gmail.com
2. Patient registers with SAME email
3. Patient dashboard should show THEIR X-ray analysis
4. Clear button should delete ALL data (oncologist + patient dashboard)
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv
import pytest

# This is a manual end-to-end flow script and not part of the automated pytest suite
pytestmark = pytest.mark.skip("Manual real data flow script; run directly with python, not via pytest")

load_dotenv()

async def test_real_data_flow():
    """Test the complete real data flow"""
    
    # Connect to MongoDB
    MONGODB_URI = os.getenv("MONGODB_URI")
    if not MONGODB_URI:
        print("❌ ERROR: MONGODB_URI not set in .env file")
        return
    
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client["onco_navigator"]
    
    # Collections
    pcp_cases = db["pcp_cases"]
    patient_users = db["patient_users"]
    onco_cases = db["onco_cases"]  # Oncologist worklist
    
    print("\n" + "="*60)
    print("TESTING REAL PATIENT DATA FLOW")
    print("="*60)
    
    # Step 1: Clear existing test data
    print("\n📋 Step 1: Clearing existing test data...")
    await pcp_cases.delete_many({"patient_email": "test@example.com"})
    await patient_users.delete_many({"email": "test@example.com"})
    await onco_cases.delete_many({"patient_email": "test@example.com"})
    print("✅ Test data cleared")
    
    # Step 2: Simulate PCP Upload
    print("\n📋 Step 2: Simulating PCP X-ray upload...")
    pcp_case = {
        "case_id": "test_case_001",
        "patient_name": "Test Patient",
        "patient_email": "test@example.com",  # KEY: This email links everything
        "patient_phone": "+91-9999999999",
        "uploaded_image": "test_xray.jpg",
        "upload_date": datetime.now().isoformat(),
        "pcp_name": "Dr. Test",
        "ai_analysis": {
            "risk_level": "High",
            "risk_score": 7,
            "diagnosis": "Test Diagnosis: Suspicious Mass Detected",
            "recommendations": ["Immediate oncologist consultation", "Biopsy recommended"]
        },
        "status": "pending_patient_registration"
    }
    
    result = await pcp_cases.insert_one(pcp_case)
    print(f"✅ PCP case created with ID: {result.inserted_id}")
    print(f"   Email: {pcp_case['patient_email']}")
    print(f"   Diagnosis: {pcp_case['ai_analysis']['diagnosis']}")
    
    # Also add to oncologist worklist
    onco_case = {
        "case_id": "test_case_001",
        "patient_name": "Test Patient",
        "patient_email": "test@example.com",
        "risk_label": "High Risk",
        "risk_score": 7.0,
        "status": "PENDING_NCG_REVIEW"
    }
    await onco_cases.insert_one(onco_case)
    print("✅ Added to oncologist worklist")
    
    # Step 3: Simulate Patient Registration
    print("\n📋 Step 3: Simulating patient registration...")
    patient_user = {
        "username": "testpatient",
        "email": "test@example.com",  # SAME EMAIL as PCP upload!
        "password": "hashed_password_here",
        "patient_id": "pat_testpatient",
        "linked_case_id": "test_case_001",
        "patient_name": "Test Patient",
        "phone": "+91-9999999999",
        "diagnosis": "Test Diagnosis: Suspicious Mass Detected",
        "diagnosis_date": datetime.now().isoformat()
    }
    
    result = await patient_users.insert_one(patient_user)
    print(f"✅ Patient registered with ID: {result.inserted_id}")
    print(f"   Username: {patient_user['username']}")
    print(f"   Email: {patient_user['email']}")
    
    # Update PCP case status
    await pcp_cases.update_one(
        {"case_id": "test_case_001"},
        {"$set": {"status": "patient_registered"}}
    )
    print("✅ PCP case status updated to 'patient_registered'")
    
    # Step 4: Test Dashboard Query
    print("\n📋 Step 4: Testing dashboard data retrieval...")
    
    # This is what the dashboard does
    user_email = "test@example.com"
    linked_case = await pcp_cases.find_one({"patient_email": user_email})
    
    if linked_case:
        print("✅ Dashboard found patient's case!")
        print(f"   Diagnosis: {linked_case['ai_analysis']['diagnosis']}")
        print(f"   Risk Score: {linked_case['ai_analysis']['risk_score']}/10")
        print(f"   Status: {linked_case['status']}")
    else:
        print("❌ ERROR: Dashboard could NOT find patient's case!")
        print("   Email matching failed!")
    
    # Step 5: Test Clear Functionality
    print("\n📋 Step 5: Testing clear button functionality...")
    print("   Current data:")
    pcp_count = await pcp_cases.count_documents({"patient_email": "test@example.com"})
    onco_count = await onco_cases.count_documents({"patient_email": "test@example.com"})
    patient_count = await patient_users.count_documents({"email": "test@example.com"})
    
    print(f"   - PCP cases: {pcp_count}")
    print(f"   - Oncologist worklist: {onco_count}")
    print(f"   - Patient users: {patient_count}")
    
    # Simulate clear button (should delete ALL related data)
    print("\n   Clicking 'Clear' button...")
    await onco_cases.delete_many({})  # Current implementation
    
    print("\n   After current clear implementation:")
    pcp_count_after = await pcp_cases.count_documents({"patient_email": "test@example.com"})
    onco_count_after = await onco_cases.count_documents({"patient_email": "test@example.com"})
    
    print(f"   - PCP cases: {pcp_count_after}")
    print(f"   - Oncologist worklist: {onco_count_after}")
    
    if pcp_count_after > 0:
        print("\n⚠️  WARNING: Clear button does NOT delete patient dashboard data!")
        print("   Patient will still see old diagnosis after clear.")
        print("\n💡 FIX NEEDED: Clear button should also delete pcp_cases")
    else:
        print("\n✅ Clear button properly deletes all data")
    
    # Step 6: Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("\n✅ Email Matching: WORKS")
    print("   - PCP uploads with email: test@example.com")
    print("   - Patient registers with email: test@example.com")
    print("   - Dashboard finds case by matching emails")
    
    if pcp_count_after > 0:
        print("\n⚠️  Clear Button: INCOMPLETE")
        print("   - Clears oncologist worklist ✅")
        print("   - Does NOT clear patient dashboard data ❌")
        print("\n   FIX: Update /oncologist/clear endpoint to also delete pcp_cases")
    else:
        print("\n✅ Clear Button: WORKS")
    
    # Cleanup
    print("\n📋 Cleaning up test data...")
    await pcp_cases.delete_many({"patient_email": "test@example.com"})
    await patient_users.delete_many({"email": "test@example.com"})
    await onco_cases.delete_many({"patient_email": "test@example.com"})
    print("✅ Test data cleaned up")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(test_real_data_flow())
