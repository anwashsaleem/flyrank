import os
from typing import Annotated
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from supabase import create_client, Client
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from the a4 folder
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("WARNING: SUPABASE_URL or SUPABASE_KEY is missing from environment variables.")

supabase: Client = create_client(
    SUPABASE_URL or "https://placeholder.supabase.co", 
    SUPABASE_KEY or "placeholder-key"
)

app = FastAPI(
    title="FlyRank Auth API",
    version="4.0",
    description="Secure Authentication & Protected Routes with Supabase Auth & JWT"
)

security = HTTPBearer()

# --- Pydantic Schemas ---

class UserCredentials(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

# --- Auth Dependency (Guard / Middleware) ---

def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required"
        )
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return {"user": user_response.user, "token": token}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

# --- Public Endpoints ---

@app.get("/")
def root():
    return {"message": "Auth API running", "docs": "/docs"}

@app.get("/public/info", status_code=status.HTTP_200_OK)
def public_info():
    return {"message": "Welcome stranger! This info is public."}

# --- Auth Endpoints ---

@app.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(credentials: UserCredentials):
    try:
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sign up failed"
            )
        return {
            "message": "User created successfully",
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "created_at": str(response.user.created_at)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/auth/login", status_code=status.HTTP_200_OK)
def login(credentials: UserCredentials):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login credentials"
            )
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "token_type": "bearer",
            "user": {
                "id": response.user.id,
                "email": response.user.email
            }
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login credentials"
        )

@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(auth_data: Annotated[dict, Depends(get_current_user)]):
    try:
        token = auth_data["token"]
        supabase.auth.sign_out(token)
        return
    except Exception:
        return

# --- Protected Endpoints ---

@app.get("/protected/profile", status_code=status.HTTP_200_OK)
def get_profile(auth_data: Annotated[dict, Depends(get_current_user)]):
    user = auth_data["user"]
    return {
        "id": user.id,
        "email": user.email,
        "created_at": str(user.created_at),
        "app_metadata": user.app_metadata,
        "user_metadata": user.user_metadata
    }

@app.get("/protected/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard(auth_data: Annotated[dict, Depends(get_current_user)]):
    user = auth_data["user"]
    return {
        "status": "active",
        "email": user.email,
        "audits_completed": 12,
        "seo_score": 94
    }