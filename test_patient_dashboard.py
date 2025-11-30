import requests
import json

# Test the patient registration
register_url = "http://127.0.0.1:8000/patient/register"
register_data = {
    "username": "testuser",
    "password": "testpassword123",
    "email": "testuser@example.com"
}

print("Registering test user...")
try:
    register_response = requests.post(register_url, data=register_data)
    print(f"Registration Status: {register_response.status_code}")
    print(f"Registration Response: {register_response.text}")
except Exception as e:
    print(f"Registration Error: {e}")

# Test the patient login
login_url = "http://127.0.0.1:8000/patient/login"
login_data = {
    "username": "testuser",
    "password": "testpassword123"
}

print("\nLogging in test user...")
try:
    login_response = requests.post(login_url, data=login_data)
    print(f"Login Status: {login_response.status_code}")
    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get("access_token")
        print(f"Access Token: {token[:20]}..." if token else "No token received")
        
        # Test the patient dashboard
        dashboard_url = "http://127.0.0.1:8000/patient/dashboard"
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\nAccessing patient dashboard...")
        dashboard_response = requests.get(dashboard_url, headers=headers)
        print(f"Dashboard Status: {dashboard_response.status_code}")
        if dashboard_response.status_code == 200:
            dashboard_result = dashboard_response.json()
            print("Dashboard Data:")
            print(json.dumps(dashboard_result, indent=2))
        else:
            print(f"Dashboard Error: {dashboard_response.text}")
    else:
        print(f"Login Error: {login_response.text}")
except Exception as e:
    print(f"Login/Dashboard Error: {e}")

print("\nTest completed.")