
import os
from dotenv import load_dotenv

load_dotenv()
print(f"ADMIN_EMAIL={os.getenv('ADMIN_EMAIL')}")
