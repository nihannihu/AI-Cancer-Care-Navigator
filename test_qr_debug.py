import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment variables
os.environ['APP_URL'] = 'http://localhost:8000'
os.environ['MONGODB_URI'] = 'mongodb+srv://nihan:Killer888beats@nihan.3jzvm5.mongodb.net/climate-sustainability?retryWrites=true&w=majority&appName=nihan'

def test_qr_code_generation():
    """Test QR code generation directly"""
    try:
        # Import after setting environment variables
        from patient_app.dashboard import QRCodeGenerator
        
        # Test data
        test_data = "http://localhost:8000/patient/profile/pat_testuser"
        print(f"Generating QR code for: {test_data}")
        
        # Generate QR code
        qr_code = QRCodeGenerator.generate_qr(test_data)
        
        if qr_code:
            print(f"QR code generated successfully!")
            print(f"QR code length: {len(qr_code)}")
            print(f"QR code starts with: {qr_code[:50]}...")
            return True
        else:
            print("QR code generation failed - returned None")
            return False
            
    except Exception as e:
        print(f"Error generating QR code: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_router_qr_logic():
    """Test the QR code logic from the router"""
    try:
        import os
        from patient_app.dashboard import QRCodeGenerator
        
        # Test the same logic used in the router
        app_url = os.getenv("APP_URL", "http://localhost:8000")
        patient_id = "pat_testuser"
        
        print(f"Testing router QR logic:")
        print(f"  app_url: {app_url}")
        print(f"  patient_id: {patient_id}")
        
        if not app_url or not patient_id:
            print("Missing required data for QR code")
            return False
            
        qr_data = f"{app_url}/patient/profile/{patient_id}"
        print(f"  qr_data: {qr_data}")
        
        qr_image = QRCodeGenerator.generate_qr(qr_data)
        print(f"  qr_image generated: {qr_image is not None}")
        if qr_image:
            print(f"  qr_image length: {len(qr_image)}")
        
        return qr_image is not None
        
    except Exception as e:
        print(f"Error in router QR logic: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Testing QR Code Generation ===")
    print()
    
    print("1. Direct QR Code Generation Test:")
    result1 = test_qr_code_generation()
    print()
    
    print("2. Router Logic Test:")
    result2 = test_router_qr_logic()
    print()
    
    if result1 and result2:
        print("✅ All tests passed! QR code generation should work.")
    else:
        print("❌ Some tests failed. There may be an issue with QR code generation.")