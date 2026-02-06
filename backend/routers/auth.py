"""
Authentication API router (simple single-user auth).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
import uuid

from database import get_db
from models.device import Device
from config import settings
from schemas.auth_schema import TokenRequest, TokenResponse, HealthResponse
from schemas.sync_schema import DeviceRegisterRequest, DeviceRegisterResponse
from services.weaviate_service import get_weaviate_service, WeaviateService

router = APIRouter()


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


@router.post("/token", response_model=TokenResponse)
def get_token(request: TokenRequest):
    """Simple password authentication for single-user system."""
    if request.password != settings.simple_password:
        raise HTTPException(status_code=401, detail="Invalid password")

    access_token = create_access_token(
        data={"sub": "user"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/devices/register", response_model=DeviceRegisterResponse)
def register_device(
    request: DeviceRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new device."""
    device_id = str(uuid.uuid4())

    device = Device(
        id=device_id,
        device_name=request.device_name,
        device_type=request.device_type
    )
    db.add(device)
    db.commit()

    return DeviceRegisterResponse(
        device_id=device_id,
        message="Device registered successfully"
    )


@router.get("/health", response_model=HealthResponse)
def health_check(weaviate: WeaviateService = Depends(get_weaviate_service)):
    """Health check endpoint."""
    services_status = {
        "database": True,  # If we got here, DB is working
        "weaviate": weaviate.is_ready(),
    }

    overall_status = "healthy" if all(services_status.values()) else "unhealthy"

    return HealthResponse(
        status=overall_status,
        services=services_status,
        version=settings.app_version
    )
