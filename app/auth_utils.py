

import os
from datetime import datetime, timedelta
from jose import jwt, JWTError

# Handle bcrypt version compatibility
try:
    from passlib.context import CryptContext
    # Force use of bcrypt backend and ignore version warnings
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    # Test if it works
    test_hash = pwd_context.hash("test")
    pwd_context.verify("test", test_hash)
except Exception as e:
    print(f"Passlib bcrypt error: {e}, falling back to direct bcrypt")
    # Fallback for bcrypt version issues
    import bcrypt
    
    class SimpleBcryptContext:
        def hash(self, password: str) -> str:
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        def verify(self, password: str, hashed: str) -> bool:
            try:
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            except Exception:
                return False
    
    pwd_context = SimpleBcryptContext()

from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def hash_password(password: str) -> str:
	return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
	return pwd_context.verify(password, hashed)

def create_access_token(data: dict, expires_delta: timedelta):
	to_encode = data.copy()
	expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt

def verify_token(token: str):
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		# Check if token has expired
		exp_timestamp = payload.get("exp")
		if exp_timestamp:
			current_timestamp = datetime.utcnow().timestamp()
			if current_timestamp > exp_timestamp:
				return None  # Token has expired
		return payload
	except JWTError as e:
		print(f"JWT Error: {e}")  # For debugging
		return None
	except Exception as e:
		print(f"Token verification error: {e}")  # For debugging
		return None
