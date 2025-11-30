from passlib.context import CryptContext

# Test with exact same configuration as auth.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

passwords = ["123456", "test", "a"*100]

for password in passwords:
    print(f"\nTesting password: '{password}' (length: {len(password)}, bytes: {len(password.encode('utf-8'))})")
    
    # Manual truncation like in router.py
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
        print(f"  Truncated to: {len(password)} chars, {len(password.encode('utf-8'))} bytes")
    
    try:
        hashed = pwd_context.hash(password)
        print(f"  ✓ SUCCESS: {hashed[:50]}...")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
