"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserResponse, MessageResponse
from app.services.auth_service import AuthService
from app.core.security import decode_refresh_token
from app.core.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    try:
        svc = AuthService()
        result = svc.register(name=request.name, email=request.email, password=request.password)
        return result["tokens"]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    try:
        svc = AuthService()
        result = svc.login(email=request.email, password=request.password)
        return result["tokens"]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest):
    payload = decode_refresh_token(request.refresh_token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    try:
        svc = AuthService()
        tokens = svc.refresh_tokens(user_id)
        return tokens
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return UserResponse(
        id=current_user["_id"],
        name=current_user["name"],
        email=current_user["email"],
        avatar_url=current_user.get("avatar_url"),
        created_at=current_user["created_at"].isoformat() if hasattr(current_user["created_at"], "isoformat") else str(current_user["created_at"]),
    )
