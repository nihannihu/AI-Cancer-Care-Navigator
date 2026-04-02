import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_main import app

client = TestClient(app)

# Test Data
MOCK_IMAGE_PATH = Path("static/validation_samples/s1_org.png")

def test_routes_exist():
    """Verify core routes are accessible"""
    response = client.get("/")
    assert response.status_code == 200
    response = client.get("/pcp")
    assert response.status_code == 200

def test_file_upload_validation_no_file():
    """Test validation when no file is sent"""
    response = client.post("/pcp/upload", data={
        "patient_name": "Test Patient",
        "patient_email": "test@example.com",
        "patient_phone": "1234567890",
        "modality": "xray"
    })
    # FastAPI returns 422 for missing required fields
    assert response.status_code == 422 

def test_upload_xray_routing():
    """Test X-Ray upload routing (Should Skip Segmentation)"""
    if not MOCK_IMAGE_PATH.exists():
        pytest.skip("Mock image not found")

    with open(MOCK_IMAGE_PATH, "rb") as f:
        response = client.post("/pcp/upload", 
            data={
                "patient_name": "Test XRay",
                "patient_email": "xray@test.com",
                "patient_phone": "123",
                "modality": "xray"
            },
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert response.status_code == 200
    assert "Scan Result" in response.text
    # Classification result should be present
    assert "Risk Assessment" in response.text
    # Segmentation message for skip should be present
    assert "Segmentation analysis is skipped" in response.text

def test_upload_ultrasound_routing():
    """Test Ultrasound upload routing (Should Run Segmentation)"""
    if not MOCK_IMAGE_PATH.exists():
        pytest.skip("Mock image not found")

    with open(MOCK_IMAGE_PATH, "rb") as f:
        response = client.post("/pcp/upload", 
            data={
                "patient_name": "Test Ultrasound",
                "patient_email": "ultra@test.com",
                "patient_phone": "123",
                "modality": "ultrasound"
            },
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert response.status_code == 200
    # Segmentation overlay should be present
    assert "AI Segmentation Mask" in response.text

def test_security_invalid_extension():
    """Test file extension validation"""
    response = client.post("/pcp/upload", 
        data={
            "patient_name": "Bad File",
            "patient_email": "bad@test.com",
            "patient_phone": "123",
            "modality": "xray"
        },
        files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    )
    
    # Expecting our error page
    assert response.status_code == 200
    assert "Invalid file type" in response.text

def test_security_corrupted_file():
    """Test corrupted image handling"""
    response = client.post("/pcp/upload", 
        data={
            "patient_name": "Corrupt File",
            "patient_email": "bad@test.com",
            "patient_phone": "123",
            "modality": "xray"
        },
        files={"file": ("test.png", b"NOT_AN_IMAGE_DATA", "image/png")}
    )
    
    assert response.status_code == 200
    assert "Corrupted or invalid image file" in response.text
