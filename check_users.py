import os
from dotenv import load_dotenv
import pymongo

# Load environment variables
load_dotenv('.env.python')

# Connect to MongoDB
client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
db = client['onco_navigator']  # Patient app uses this database
users = db['patient_users']

print('All registered users in database:')
users_list = list(users.find({}, {'username': 1, 'email': 1}))
for user in users_list:
    print(f'  Username: {user.get("username", "Unknown")}, Email: {user.get("email", "Unknown")}')