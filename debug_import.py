import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

try:
    print("Attempting to import patient_app.router...")
    from patient_app.router import patient_app_router
    print("Successfully imported patient_app_router")
    print("Routes:", [route.path for route in patient_app_router.routes])
except Exception as e:
    print(f"FAILED to import: {e}")
    import traceback
    traceback.print_exc()
