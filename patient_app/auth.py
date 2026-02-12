from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGODB_URI, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
import os
import urllib.parse

# Switch to pbkdf2_sha256 to avoid bcrypt's 72-byte limit and dependency issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="patient/login")

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

# Create a function to get the database to avoid circular imports
def get_db():
    client = AsyncIOMotorClient(MONGODB_URI)
    db_name = get_database_name_from_uri(MONGODB_URI)
    return client[db_name]

# Get the database and collections
db = get_db()
users_collection = db["patient_users"]

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return user
