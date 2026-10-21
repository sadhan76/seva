"""
Authentication and Role-Based Access Control (RBAC) Module
=========================================================
Handles:
- Password hashing & verification with Bcrypt
- JWT Token creation, signing, and verification
- Current user authentication dependency
- Role verification (Farmer vs Procurement Staff)
- Trusted staff account administrative bootstrapping
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

from database import get_users_collection, get_farmers_collection

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "namma_vivasayi_jwt_super_secret_dev_key_2026_secured")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and verify the bearer token,
    loading the active user from MongoDB.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    users_collection = get_users_collection()
    if users_collection is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service currently unavailable.",
        )

    from bson import ObjectId
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or removed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Format user doc and strip password hash
    user["id"] = str(user.pop("_id"))
    user.pop("hashed_password", None)
    return user


async def require_farmer(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Ensures the authenticated user has the 'farmer' role."""
    if current_user.get("role") != "farmer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to registered farmers only.",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Soft authentication dependency: returns the authenticated user if a valid
    Bearer token is provided, or None if no token is present.
    Raises 401 only for malformed/expired tokens (not for missing tokens).
    """
    if not credentials or not credentials.credentials:
        return None  # Anonymous access allowed
    try:
        payload = decode_access_token(credentials.credentials)
    except HTTPException:
        return None  # Invalid token treated as anonymous

    user_id = payload.get("sub")
    if not user_id:
        return None

    users_collection = get_users_collection()
    if users_collection is None:
        return None

    from bson import ObjectId
    try:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None

    if not user:
        return None

    user["id"] = str(user.pop("_id"))
    user.pop("hashed_password", None)
    return user


async def require_staff(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Ensures the authenticated user has the 'staff' role."""
    if current_user.get("role") != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorized procurement centre staff only.",
        )
    return current_user


async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Ensures the authenticated user has administrative or staff privileges to curate official content."""
    if current_user.get("role") not in ["admin", "staff"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorized administrators and nodal officers only.",
        )
    return current_user


async def bootstrap_staff_account():
    """
    Administrative process: Seeds an authorized Procurement Staff account
    based on trusted configuration if it doesn't already exist.
    """
    users_collection = get_users_collection()
    if users_collection is None:
        return

    staff_phone = os.getenv("STAFF_BOOTSTRAP_PHONE", "9842012345")
    staff_pwd = os.getenv("STAFF_BOOTSTRAP_PASSWORD", "MandiStaff@2026")
    staff_name = os.getenv("STAFF_BOOTSTRAP_NAME", "Ramesh Kumar (Procurement Inspector)")
    staff_mandi = os.getenv("STAFF_BOOTSTRAP_MANDI", "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)")

    existing_staff = await users_collection.find_one({"phone": staff_phone})
    if not existing_staff:
        hashed = hash_password(staff_pwd)
        staff_doc = {
            "name": staff_name,
            "phone": staff_phone,
            "role": "staff",
            "mandiName": staff_mandi,
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "preferredLanguage": "en",
            "hashed_password": hashed,
            "createdAt": datetime.utcnow().strftime("%d %b %Y, %I:%M %p"),
            "isActive": True
        }
        await users_collection.insert_one(staff_doc)
        print(f"[Auth] Bootstrapped authorized staff account: {staff_phone} ({staff_name})")
    else:
        if "Thanjavur Regulated Market" in existing_staff.get("mandiName", ""):
            await users_collection.update_one(
                {"_id": existing_staff["_id"]},
                {"$set": {"mandiName": "Thanjavur Direct Procurement Centre #3 (Pillaiyarpatti)"}}
            )

    # Also ensure default demo farmer account exists for quick-fill / demonstration
    demo_farmer_phone = "9876543299"
    existing_farmer = await users_collection.find_one({"phone": demo_farmer_phone})
    if not existing_farmer:
        f_hash = hash_password("FarmerPassword@123")
        farmer_doc = {
            "name": "Murugesan K.",
            "phone": demo_farmer_phone,
            "role": "farmer",
            "farmerId": "TN-AGRI-2026-9281",
            "village": "Pillaiyarpatti",
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "country": "India",
            "totalLandAcres": 4,
            "primaryCrop": "Paddy Grade A",
            "soilType": "Alluvial Clay Loam",
            "irrigationSources": ["Borewell / Tube Well", "Canal"],
            "preferredLanguage": "ta",
            "hashed_password": f_hash,
            "createdAt": datetime.utcnow().strftime("%d %b %Y, %I:%M %p"),
            "isActive": True
        }
        await users_collection.insert_one(farmer_doc)
        farmers_col = get_farmers_collection()
        if farmers_col is not None:
            await farmers_col.update_one(
                {"farmerId": farmer_doc["farmerId"]},
                {"$set": farmer_doc},
                upsert=True
            )
        print(f"[Auth] Bootstrapped demo farmer account: {demo_farmer_phone} (Murugesan K.)")
