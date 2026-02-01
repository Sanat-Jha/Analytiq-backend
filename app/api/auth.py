

from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.models import User, AuthRequest, AuthResponse
from app.auth_utils import create_access_token, hash_password, verify_password
from app.db import create_user, get_user_by_email
import uuid

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")



@router.post("/signup", response_model=User)
async def signup(auth: AuthRequest):
	if get_user_by_email(auth.email):
		raise HTTPException(status_code=400, detail="Email already registered")
	user_id = str(uuid.uuid4())
	hashed = hash_password(auth.password)
	create_user(user_id, auth.email, hashed)
	user = get_user_by_email(auth.email)
	if user == None:
		raise HTTPException(status_code=500, detail="User creation failed")
	return User(id=user["id"], email=user["email"], created_at=str(user["created_at"]))

@router.post("/login", response_model=AuthResponse)
async def login(auth: AuthRequest):
	user = get_user_by_email(auth.email)
	if not user or not verify_password(auth.password, user["hashed_password"]):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
	# Create longer-lasting token for better UX (24 hours instead of 1 hour)
	token = create_access_token({"sub": user["id"], "email": user["email"]}, expires_delta=timedelta(hours=24))
	return AuthResponse(access_token=token)

@router.get("/validate")
async def validate_token(token: str = Depends(oauth2_scheme)):
	"""Validate if the current token is still valid"""
	from app.auth_utils import verify_token
	payload = verify_token(token)
	if not payload or "sub" not in payload:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
	
	# Get user info to return
	user = get_user_by_email(payload["email"])
	if not user:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
	
	return {
		"valid": True,
		"user": {
			"id": user["id"],
			"email": user["email"]
		},
		"expires_at": payload.get("exp")
	}

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(token: str = Depends(oauth2_scheme)):
	"""Refresh an existing token"""
	from app.auth_utils import verify_token, create_access_token
	payload = verify_token(token)
	if not payload or "sub" not in payload:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
	
	# Create new token with fresh expiry
	new_token = create_access_token(
		{"sub": payload["sub"], "email": payload["email"]}, 
		expires_delta=timedelta(hours=24)
	)
	return AuthResponse(access_token=new_token)
