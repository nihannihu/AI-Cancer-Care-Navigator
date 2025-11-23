"""
Script to create sample patient data linked to real X-ray analysis
This creates the complete patient journey for demo purposes
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

load_dotenv()

async def create_sample_patient_data():
    MONGODB_URI = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client["onco_navigator"]
    
    # Collections
    pcp_cases = db["pcp_cases"]
    patient_users = db["patient_users"]
    prescriptions = db["prescriptions"]
    consultations = db["consultations"]
    
    print("Creating sample patient data for Ravi...")
    
    # 1. Create PCP Case (simulating what PCP uploaded)
    pcp_case = {
        "case_id": "case_ravi_001",
        "patient_name": "Ravi",
        "patient_email": "nihanmohammed95@gmail.com",
        "patient_phone": "+91-9845325913",
        "uploaded_image": "jpeg/1.3.6.1.4.1.9590.100.1.2.100522099512256189513864912954167862869",
        "upload_date": (datetime.now() - timedelta(days=15)).isoformat(),
        "pcp_name": "Dr. Kumar",
        "pcp_location": "Rural Health Center, Karnataka",
        "ai_analysis": {
            "risk_level": "High",
            "risk_score": 8,
            "diagnosis": "Stage II Invasive Ductal Carcinoma (Breast Cancer)",
            "confidence": 0.87,
            "tumor_size": "2.3 cm",
            "lymph_nodes": "Suspicious - requires biopsy",
            "survival_prediction": "With immediate treatment, 5-year survival rate is 85-90%. Early intervention is critical.",
            "recommendations": [
                "Immediate referral to oncologist",
                "Biopsy to confirm lymph node involvement",
                "Begin chemotherapy within 2 weeks",
                "Consider lumpectomy followed by radiation"
            ]
        },
        "status": "patient_registered",
        "forwarded_to_oncologist": True,
        "oncologist_id": "dr_sharma"
    }
    
    # Insert or update PCP case
    await pcp_cases.delete_many({"patient_email": "nihanmohammed95@gmail.com"})
    result = await pcp_cases.insert_one(pcp_case)
    print(f"✓ Created PCP case: {pcp_case['case_id']}")
    
    # 2. Update patient user account to link to case
    await patient_users.update_one(
        {"email": "nihanmohammed95@gmail.com"},
        {
            "$set": {
                "linked_case_id": pcp_case["case_id"],
                "patient_name": "Ravi",
                "phone": "+91-9845325913",
                "diagnosis": pcp_case["ai_analysis"]["diagnosis"],
                "diagnosis_date": pcp_case["upload_date"]
            }
        }
    )
    print(f"✓ Linked patient account 'nihan9t9' to case")
    
    # 3. Create Oncologist Consultation Record
    consultation = {
        "consultation_id": "consult_001",
        "patient_id": "pat_nihan9t9",
        "patient_email": "nihanmohammed95@gmail.com",
        "doctor_name": "Dr. Sharma",
        "doctor_specialization": "Oncologist",
        "date": (datetime.now() - timedelta(days=10)).isoformat(),
        "notes": "Reviewed PCP case. Confirmed Stage II breast cancer. Recommended immediate chemotherapy followed by surgery.",
        "treatment_plan": "Chemotherapy (4 cycles) → Lumpectomy → Radiation",
        "next_appointment": (datetime.now() + timedelta(days=7)).isoformat()
    }
    
    await consultations.delete_many({"patient_email": "nihanmohammed95@gmail.com"})
    await consultations.insert_one(consultation)
    print(f"✓ Created oncologist consultation record")
    
    # 4. Create Prescription (Medicine Tracker)
    prescription = {
        "prescription_id": "rx_001",
        "patient_id": "pat_nihan9t9",
        "patient_email": "nihanmohammed95@gmail.com",
        "prescribed_by": "Dr. Sharma",
        "prescribed_date": (datetime.now() - timedelta(days=8)).isoformat(),
        "medications": [
            {
                "drug_name": "Tamoxifen",
                "dosage": "20mg",
                "frequency": "Once daily",
                "duration_days": 90,
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "instructions": "Take with food. Continue for 3 months.",
                "remaining_count": 83
            },
            {
                "drug_name": "Ondansetron",
                "dosage": "8mg",
                "frequency": "As needed",
                "duration_days": 30,
                "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
                "instructions": "For nausea. Take 30 minutes before chemotherapy.",
                "remaining_count": 28
            }
        ],
        "status": "active"
    }
    
    await prescriptions.delete_many({"patient_email": "nihanmohammed95@gmail.com"})
    await prescriptions.insert_one(prescription)
    print(f"✓ Created prescription records")
    
    # 5. Create Medical Timeline Events
    timeline_events = [
        {
            "patient_id": "pat_nihan9t9",
            "date": pcp_case["upload_date"],
            "type": "Diagnosis",
            "details": f"Diagnosed with {pcp_case['ai_analysis']['diagnosis']} at Rural Health Center"
        },
        {
            "patient_id": "pat_nihan9t9",
            "date": (datetime.now() - timedelta(days=12)).isoformat(),
            "type": "Referral",
            "details": "Referred to Dr. Sharma (Oncologist) for specialized care"
        },
        {
            "patient_id": "pat_nihan9t9",
            "date": consultation["date"],
            "type": "Consultation",
            "details": "Initial consultation with Dr. Sharma - Treatment plan established"
        },
        {
            "patient_id": "pat_nihan9t9",
            "date": prescription["prescribed_date"],
            "type": "Prescription",
            "details": "Prescribed Tamoxifen 20mg and Ondansetron 8mg"
        },
        {
            "patient_id": "pat_nihan9t9",
            "date": (datetime.now() - timedelta(days=3)).isoformat(),
            "type": "Lab Test",
            "details": "Blood work completed - WBC: 3.2, Hemoglobin: 11.0"
        }
    ]
    
    timeline_collection = db["medical_timeline"]
    await timeline_collection.delete_many({"patient_id": "pat_nihan9t9"})
    await timeline_collection.insert_many(timeline_events)
    print(f"✓ Created {len(timeline_events)} timeline events")
    
    print("\n" + "="*60)
    print("✅ Sample patient data created successfully!")
    print("="*60)
    print(f"\nPatient: Ravi")
    print(f"Email: nihanmohammed95@gmail.com")
    print(f"Account: nihan9t9")
    print(f"Diagnosis: {pcp_case['ai_analysis']['diagnosis']}")
    print(f"Risk Score: {pcp_case['ai_analysis']['risk_score']}/10")
    print(f"Linked Case: {pcp_case['case_id']}")
    print(f"\nTimeline Events: {len(timeline_events)}")
    print(f"Prescriptions: {len(prescription['medications'])} medications")
    print(f"Consultations: 1 with Dr. Sharma")
    print("\n✅ Patient dashboard will now show REAL data!")

if __name__ == "__main__":
    asyncio.run(create_sample_patient_data())
