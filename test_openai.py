import os
import httpx
from dotenv import load_dotenv

# Load environment variables from both .env and .env.python
load_dotenv(".env")
load_dotenv(".env.python", override=True)

# Get the API key (prioritize .env.python but fall back to .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key exists: {bool(OPENAI_API_KEY)}")

# Check which file the key came from
key_from_python = os.getenv("OPENAI_API_KEY", "")
key_from_env = ""
if os.path.exists(".env"):
    with open(".env", "r") as f:
        content = f.read()
        if "OPENAI_API_KEY=" in content:
            # Extract key from .env file
            import re
            match = re.search(r'OPENAI_API_KEY=(.+)', content)
            if match:
                key_from_env = match.group(1)

print(f"Key from .env.python: {key_from_python[:15] + '...' if key_from_python else 'None'}")
print(f"Key from .env: {key_from_env[:15] + '...' if key_from_env else 'None'}")
print(f"Currently loaded key: {OPENAI_API_KEY[:15] + '...' if OPENAI_API_KEY else 'None'}")

# Let's try to get a new key from user input or use a placeholder
print("\nBoth API keys are hitting quota limits. You'll need to:")
print("1. Get a new OpenAI API key from https://platform.openai.com/api-keys")
print("2. Update it in your .env.python file")
print("3. Restart your servers")

# For testing purposes, let's just verify the key format is correct
if OPENAI_API_KEY and OPENAI_API_KEY.startswith("sk-proj-"):
    print("\nAPI Key format looks correct (sk-proj-...)")
else:
    print("\nAPI Key format may be incorrect")
    
print("\nTo fix the quota issue:")
print("1. Log in to your OpenAI account at https://platform.openai.com/")
print("2. Check your billing and usage limits")
print("3. Consider upgrading your plan or waiting for quota reset")