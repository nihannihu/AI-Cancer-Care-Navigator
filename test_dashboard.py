import os
from dotenv import load_dotenv
import pymongo
import urllib.parse

# Load environment variables
load_dotenv('.env.python')

# Parse the database name from the URI
def get_database_name_from_uri(uri):
    # Extract the database name from the URI
    try:
        # Split the URI to get the database name
        parsed = urllib.parse.urlparse(uri)
        path_parts = parsed.path.strip('/').split('/')
        if path_parts and path_parts[0]:
            return path_parts[0]
    except:
        pass
    return "climate-sustainability"  # Default fallback

# Connect to MongoDB using the same approach as the patient app
MONGODB_URI = os.getenv('MONGODB_URI')
client = pymongo.MongoClient(MONGODB_URI)
db_name = get_database_name_from_uri(MONGODB_URI)
db = client[db_name]
pcp_cases = db["onco_cases"]

# Simulate the dashboard query
patient_email = "nihanmohammed95@gmail.com"
patient_username = "nihan9t9"

print(f"Testing dashboard logic for user: {patient_username}, email: {patient_email}")

# First try to find cases using patient email
print(f"Searching for cases with email: {patient_email}")
cursor = pcp_cases.find({"patient_email": patient_email})
pcp_cases_list = list(cursor)  # Get all cases
print(f"Found {len(pcp_cases_list)} cases with email")

# If no cases found with email, try with patient name (username)
if not pcp_cases_list:
    print(f"No cases found with email, searching with username: {patient_username}")
    cursor = pcp_cases.find({"patient_name": patient_username})
    pcp_cases_list = list(cursor)  # Get all cases
    print(f"Found {len(pcp_cases_list)} cases with username")

# Sort by timestamp to get the most recent first
pcp_cases_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
print(f"Sorted cases list, total: {len(pcp_cases_list)}")

if pcp_cases_list:
    print("\nLatest case details:")
    latest_case = pcp_cases_list[0]
    print(f"  Case ID: {latest_case.get('case_id')}")
    print(f"  Patient Name: {latest_case.get('patient_name')}")
    print(f"  Patient Email: {latest_case.get('patient_email')}")
    print(f"  Risk Label: {latest_case.get('risk_label')}")
    print(f"  Risk Score: {latest_case.get('risk_score')}")
    print(f"  Timestamp: {latest_case.get('timestamp')}")
else:
    print("No cases found")