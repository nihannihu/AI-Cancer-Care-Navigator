import sys
sys.path.append('.')

from passlib.context import CryptContext

# Test bcrypt with the exact configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)

password = "123456"
print(f"Password: {password}")
print(f"Password length: {len(password)}")
print(f"Password bytes: {len(password.encode('utf-8'))}")

try:
    hashed = pwd_context.hash(password)
    print(f"Success! Hashed: {hashed[:50]}...")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
