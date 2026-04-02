
import sys
from unittest.mock import MagicMock

# MOCK ML LIBRARIES BEFORE IMPORTING APP
# This prevents ImportError: No module named 'tensorflow'
sys.modules["tensorflow"] = MagicMock()
sys.modules["tensorflow.keras"] = MagicMock()
sys.modules["tensorflow.keras.models"] = MagicMock()
sys.modules["tensorflow.keras.applications"] = MagicMock()
sys.modules["tensorflow.keras.applications.densenet"] = MagicMock()
sys.modules["tensorflow.keras.applications.mobilenet_v2"] = MagicMock()
sys.modules["tensorflow.keras.preprocessing"] = MagicMock()
sys.modules["tensorflow.keras.preprocessing.image"] = MagicMock()

# Mock internal model utils to avoid actual model loading
mock_model_utils = MagicMock()
mock_model_utils.BreastCancerModel = MagicMock()
sys.modules["ml.model_utils"] = mock_model_utils

mock_seg_utils = MagicMock()
# Mock internal model utils
sys.modules["ml.model_utils"] = mock_model_utils

mock_seg_utils = MagicMock()
sys.modules["ml.segmentation_utils"] = mock_seg_utils

# EXTENSIVE MOCKING FOR GOOGLE LIBS
# We need to mock the entire hierarchy to prevent "is not a package" errors
mock_google = MagicMock()
sys.modules["google"] = mock_google
sys.modules["google.generativeai"] = MagicMock()
sys.modules["google.oauth2"] = MagicMock()
sys.modules["google.oauth2.service_account"] = MagicMock()
sys.modules["google.ai"] = MagicMock()
sys.modules["google.ai.generativelanguage"] = MagicMock()
sys.modules["google.api_core"] = MagicMock()
sys.modules["google.api_core.client_options"] = MagicMock()
sys.modules["googleapiclient"] = MagicMock()
sys.modules["googleapiclient.discovery"] = MagicMock()

# Mock Pandas and Sklearn
sys.modules["pandas"] = MagicMock()
sys.modules["sklearn"] = MagicMock()
sys.modules["sklearn.ensemble"] = MagicMock()
sys.modules["sklearn.metrics"] = MagicMock()
sys.modules["sklearn.preprocessing"] = MagicMock()
sys.modules["sklearn.model_selection"] = MagicMock()

from fastapi.testclient import TestClient
from app_main import app
from pathlib import Path

# Setup Mock Models in App State
app.model = MagicMock()
app.model.predict_label.return_value = ("BENIGN", 0.1)
app.model.predict_stage.return_value = "Stage 0"

app.segmentor = MagicMock()
app.segmentor.predict_mask.return_value = (None, None)

# Patch the global variables in app_main if they are used directly
import app_main
app_main.model = app.model
app_main.segmentor = app.segmentor

client = TestClient(app)

MOCK_IMAGE_PATH = Path("static/validation_samples/s1_org.png")

def test_routes_exist():
    print("Testing routes exist...")
    response = client.get("/")
    assert response.status_code == 200
    print("✓ Routes exist pass")

def test_upload_validation_no_file():
    print("Testing validation no file...")
    response = client.post("/pcp/upload", data={
        "patient_name": "Test",
        "patient_email": "t@t.com",
        "patient_phone": "123",
        "modality": "xray"
    })
    assert response.status_code == 422
    print("✓ Validation no file pass")

# Security Tests
def test_security_invalid_extension():
    print("Testing security invalid extension...")
    response = client.post("/pcp/upload", 
        data={
            "patient_name": "Bad File",
            "patient_email": "bad@test.com",
            "patient_phone": "123",
            "modality": "xray"
        },
        files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    )
    assert response.status_code == 200
    assert "Invalid file type" in response.text
    print("✓ Security invalid extension pass")

if __name__ == "__main__":
    try:
        test_routes_exist()
        test_upload_validation_no_file()
        test_security_invalid_extension()
        print("\nALL TESTS PASSED SUCCESSFULLY! ✅")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\nERROR RUNNING TESTS: {e}")
        exit(1)

def test_routes_exist():
    response = client.get("/")
    assert response.status_code == 200

def test_upload_validation_no_file():
    response = client.post("/pcp/upload", data={
        "patient_name": "Test",
        "patient_email": "t@t.com",
        "patient_phone": "123",
        "modality": "xray"
    })
    assert response.status_code == 422

# Security Tests
def test_security_invalid_extension():
    response = client.post("/pcp/upload", 
        data={
            "patient_name": "Bad File",
            "patient_email": "bad@test.com",
            "patient_phone": "123",
            "modality": "xray"
        },
        files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    )
    assert response.status_code == 200
    assert "Invalid file type" in response.text
