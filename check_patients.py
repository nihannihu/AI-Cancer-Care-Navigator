import os
from dotenv import load_dotenv
import pymongo

# Load environment variables
load_dotenv('.env.python')

# Connect to MongoDB
client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
db = client.get_default_database()
cases = db['onco_cases']

print('All patient emails in database:')
cases_list = list(cases.find({}, {'patient_email': 1, 'patient_name': 1}))
for case in cases_list:
    print(f'  Name: {case.get("patient_name", "Unknown")}, Email: {case.get("patient_email", "Unknown")}')