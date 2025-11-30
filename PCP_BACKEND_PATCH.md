# PCP Backend Update - Manual Patch Instructions

## What This Fixes
This update enables the PCP portal to save patient email and phone, which allows the system to link X-ray uploads to patient accounts.

## File to Edit
`app_main.py`

## Change 1: Update Function Signature (Line 85-89)

**FIND THIS:**
```python
async def pcp_upload(
    request: Request,
    patient_name: str = Form(...),
    file: UploadFile = File(...),
) -> HTMLResponse:
```

**REPLACE WITH:**
```python
async def pcp_upload(
    request: Request,
    patient_name: str = Form(...),
    patient_email: str = Form(...),
    patient_phone: str = Form(...),
    file: UploadFile = File(...),
) -> HTMLResponse:
```

## Change 2: Update Database Save (Line 134-145)

**FIND THIS:**
```python
            doc = {
                "case_id": case_id,
                "patient_name": patient_name,
                "risk_label": label,
                "risk_score": float(score),
                "status": case.status,
            }
            if image_url:
                doc["image_url"] = image_url
            await db_cases.insert_one(doc)
```

**REPLACE WITH:**
```python
            doc = {
                "case_id": case_id,
                "patient_name": patient_name,
                "patient_email": patient_email,
                "patient_phone": patient_phone,
                "risk_label": label,
                "risk_score": float(score),
                "status": case.status,
                "upload_date": datetime.now().isoformat(),
            }
            if image_url:
                doc["image_url"] = image_url
            await db_cases.insert_one(doc)
```

## How It Works After This Change

1. **PCP uploads X-ray** with patient info:
   - Name: "Ravi"
   - Email: "nihanmohammed95@gmail.com"
   - Phone: "9845325913"

2. **System saves to database** with email

3. **Patient registers** with same email

4. **Dashboard matches by email** and shows THEIR data!

## Test After Applying

1. Go to `/pcp`
2. Fill in:
   - Patient Name: Ravi
   - Patient Email: nihanmohammed95@gmail.com
   - Patient Phone: 9845325913
   - Upload an X-ray image
3. Patient logs in → sees THEIR diagnosis!
