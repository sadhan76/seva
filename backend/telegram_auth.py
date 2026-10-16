"""
Telegram OTP and Account Linking Authentication Module (Phase 19)
================================================================
Provides secure Telegram-based authentication and account verification:
- Cryptographic single-use short-lived account-linking tokens & deep links.
- Verified Telegram Chat ID binding (prevents unverified chat spoofing).
- Cryptographic OTP generation (6-digit, 5-minute expiry, single-use).
- Salted SHA-256 OTP hashing (NEVER stores plaintext OTPs).
- Cooldown (60s), attempt limit (3 max), and rate-limit enforcement.
- Safe HTTPS Telegram Bot API client.
- Transparent reporting when TELEGRAM_BOT_TOKEN is not configured.
- Security filters: OTPs, bot tokens, and secrets are NEVER logged or returned in responses.
"""

import os
import secrets
import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import httpx
from fastapi import HTTPException, status
from dotenv import load_dotenv

from database import (
    get_users_collection,
    get_farmers_collection,
    get_telegram_link_tokens_collection,
    get_telegram_otps_collection,
)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_BOT_USERNAME = os.getenv("TELEGRAM_BOT_USERNAME", "").strip()
TELEGRAM_API_BASE = "https://api.telegram.org"

# Constants for security enforcement
OTP_EXPIRY_MINUTES = 5
LINK_TOKEN_EXPIRY_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60
MAX_OTP_ATTEMPTS = 3


def is_telegram_configured() -> bool:
    """Returns True if a non-empty Telegram Bot Token is configured."""
    return bool(TELEGRAM_BOT_TOKEN and not TELEGRAM_BOT_TOKEN.startswith("your_"))


def get_bot_username() -> str:
    """Returns configured bot username or fallback identifier."""
    if TELEGRAM_BOT_USERNAME and not TELEGRAM_BOT_USERNAME.startswith("your_"):
        return TELEGRAM_BOT_USERNAME
    return "NammaVivasayiAIBot"


def hash_otp(otp_str: str, salt: str) -> str:
    """Computes salted SHA-256 hash of the OTP."""
    payload = f"{salt}:{otp_str}:{salt}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_otp_hash(plain_otp: str, salt: str, stored_hash: str) -> bool:
    """Verifies candidate OTP against stored salted hash using constant-time comparison."""
    candidate_hash = hash_otp(plain_otp, salt)
    return secrets.compare_digest(candidate_hash, stored_hash)


async def generate_account_linking_token(phone: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generates a cryptographically secure, single-use, short-lived linking token.
    Provides a Telegram deep link: https://t.me/<bot_username>?start=<linking_token>
    """
    tokens_col = get_telegram_link_tokens_collection()
    if tokens_col is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable."
        )

    clean_phone = re.sub(r"[^\d]", "", phone)
    if len(clean_phone) == 12 and clean_phone.startswith("91"):
        clean_phone = clean_phone[2:]

    # Cryptographically random URL-safe token (32 bytes = 43 chars)
    raw_token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=LINK_TOKEN_EXPIRY_MINUTES)

    # Invalidate any older active link tokens for this phone
    await tokens_col.update_many(
        {"phone": clean_phone, "status": "PENDING"},
        {"$set": {"status": "SUPERSEDED", "updatedAt": now.isoformat()}}
    )

    doc = {
        "token": raw_token,
        "phone": clean_phone,
        "userId": user_id,
        "status": "PENDING",  # PENDING -> LINKED -> USED / EXPIRED
        "createdAt": now.isoformat(),
        "expiresAt": expires_at.isoformat(),
        "telegramChatId": None,
        "telegramUsername": None,
        "telegramFirstName": None,
    }

    await tokens_col.insert_one(doc)

    bot_user = get_bot_username()
    deep_link = f"https://t.me/{bot_user}?start={raw_token}"

    return {
        "linkToken": raw_token,
        "deepLink": deep_link,
        "botUsername": bot_user,
        "expiresInSeconds": LINK_TOKEN_EXPIRY_MINUTES * 60,
        "configured": is_telegram_configured(),
        "notice": (
            "Open the Telegram bot and press 'Start' to securely link your Telegram account."
            if is_telegram_configured()
            else "Notice: Telegram Bot Token is not configured in backend environment."
        )
    }


async def check_or_poll_telegram_link(token: str) -> Dict[str, Any]:
    """
    Checks if a linking token has been bound to a verified Telegram Chat ID.
    If Telegram is configured, polls Telegram getUpdates to auto-detect the user's /start <token>.
    """
    tokens_col = get_telegram_link_tokens_collection()
    users_col = get_users_collection()
    if tokens_col is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable.")

    record = await tokens_col.find_one({"token": token})
    if not record:
        return {"linked": False, "verified": False, "message": "Invalid or expired linking token."}

    # Check expiry
    expires_at = datetime.fromisoformat(record["expiresAt"])
    if datetime.utcnow() > expires_at:
        await tokens_col.update_one({"_id": record["_id"]}, {"$set": {"status": "EXPIRED"}})
        return {"linked": False, "verified": False, "message": "Linking token has expired. Please generate a new one."}

    if record.get("status") == "LINKED" and record.get("telegramChatId"):
        return {
            "linked": True,
            "verified": True,
            "telegramUsername": record.get("telegramUsername"),
            "telegramFirstName": record.get("telegramFirstName"),
            "phone": record.get("phone"),
            "message": "Telegram account successfully linked!"
        }

    # If Telegram is configured, check getUpdates for incoming /start <token>
    if is_telegram_configured():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=20")
                if res.status_code == 200:
                    data = res.json()
                    updates = data.get("result", [])
                    for update in updates:
                        msg = update.get("message") or update.get("channel_post") or {}
                        text = (msg.get("text") or "").strip()
                        if text == f"/start {token}":
                            chat = msg.get("chat", {})
                            from_user = msg.get("from", {})
                            chat_id = str(chat.get("id"))
                            tg_username = from_user.get("username")
                            tg_first_name = from_user.get("first_name")

                            now = datetime.utcnow()
                            await tokens_col.update_one(
                                {"_id": record["_id"]},
                                {"$set": {
                                    "status": "LINKED",
                                    "telegramChatId": chat_id,
                                    "telegramUsername": tg_username,
                                    "telegramFirstName": tg_first_name,
                                    "linkedAt": now.isoformat()
                                }}
                            )

                            # If user exists in users_col, bind chat_id
                            if users_col is not None and record.get("phone"):
                                await users_col.update_one(
                                    {"phone": record["phone"]},
                                    {"$set": {
                                        "telegramChatId": chat_id,
                                        "telegramUsername": tg_username,
                                        "telegramLinked": True,
                                        "telegramLinkedAt": now.isoformat()
                                    }}
                                )

                            # Send welcome confirmation to Telegram user
                            welcome_text = (
                                "🌾 *Namma Vivasayi AI — Telegram Verification*\n\n"
                                f"வணக்கம் {tg_first_name or 'விவசாயி'}!\n"
                                "Your Telegram account has been securely linked to your farmer profile. "
                                "You will receive high-security procurement and OTP notifications here."
                            )
                            try:
                                await client.post(
                                    f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                                    json={"chat_id": chat_id, "text": welcome_text, "parse_mode": "Markdown"}
                                )
                            except Exception:
                                pass

                            return {
                                "linked": True,
                                "verified": True,
                                "telegramUsername": tg_username,
                                "telegramFirstName": tg_first_name,
                                "phone": record.get("phone"),
                                "message": "Telegram account successfully linked!"
                            }
        except Exception:
            # Network or Telegram API error - continue gracefully
            pass

    return {
        "linked": False,
        "verified": False,
        "message": "Waiting for user to start the Telegram bot..."
    }


async def bind_verified_telegram_chat(
    token: str,
    chat_id: str,
    username: Optional[str] = None,
    first_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Direct server-side binding of a Telegram Chat ID to a linking token.
    Used by webhook handlers and automated tests with mocked responses.
    """
    tokens_col = get_telegram_link_tokens_collection()
    users_col = get_users_collection()
    if tokens_col is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    record = await tokens_col.find_one({"token": token})
    if not record:
        raise HTTPException(status_code=404, detail="Linking token not found or invalid.")

    now = datetime.utcnow()
    if datetime.fromisoformat(record["expiresAt"]) < now:
        raise HTTPException(status_code=400, detail="Linking token has expired.")

    await tokens_col.update_one(
        {"_id": record["_id"]},
        {"$set": {
            "status": "LINKED",
            "telegramChatId": str(chat_id),
            "telegramUsername": username,
            "telegramFirstName": first_name,
            "linkedAt": now.isoformat()
        }}
    )

    if users_col is not None and record.get("phone"):
        await users_col.update_one(
            {"phone": record["phone"]},
            {"$set": {
                "telegramChatId": str(chat_id),
                "telegramUsername": username,
                "telegramLinked": True,
                "telegramLinkedAt": now.isoformat()
            }}
        )

    return {
        "success": True,
        "linked": True,
        "telegramUsername": username,
        "message": "Telegram account verified and bound successfully."
    }


async def send_telegram_otp(
    phone: str,
    purpose: str = "login",
    custom_client: Optional[httpx.AsyncClient] = None
) -> Dict[str, Any]:
    """
    Sends a cryptographically secure 6-digit OTP to the verified Telegram Chat ID.
    Enforces cooldown, expiry, and attempt limits.
    Stores ONLY salted SHA-256 hash. Plaintext OTP is NEVER stored, logged, or returned.
    """
    clean_phone = re.sub(r"[^\d]", "", phone)
    if len(clean_phone) == 12 and clean_phone.startswith("91"):
        clean_phone = clean_phone[2:]

    users_col = get_users_collection()
    otps_col = get_telegram_otps_collection()
    tokens_col = get_telegram_link_tokens_collection()

    if otps_col is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    # 1. Resolve Telegram Chat ID
    chat_id = None
    tg_user = None

    if users_col is not None:
        user_doc = await users_col.find_one({"phone": clean_phone})
        if user_doc and user_doc.get("telegramChatId"):
            chat_id = str(user_doc["telegramChatId"])
            tg_user = user_doc.get("telegramUsername")

    # If not found in user doc, check if pending registration has a verified link token
    if not chat_id and tokens_col is not None:
        link_doc = await tokens_col.find_one({
            "phone": clean_phone,
            "status": "LINKED",
            "telegramChatId": {"$ne": None}
        })
        if link_doc:
            chat_id = str(link_doc["telegramChatId"])
            tg_user = link_doc.get("telegramUsername")

    if not chat_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"No verified Telegram account is linked with mobile number {clean_phone}. "
                "Please link your Telegram account using the Telegram Bot before requesting an OTP."
            )
        )

    # 2. Check Cooldown
    now = datetime.utcnow()
    recent_otp = await otps_col.find_one(
        {"phone": clean_phone, "used": False},
        sort=[("createdAt", -1)]
    )
    if recent_otp:
        created_time = datetime.fromisoformat(recent_otp["createdAt"])
        elapsed_seconds = (now - created_time).total_seconds()
        if elapsed_seconds < RESEND_COOLDOWN_SECONDS:
            remaining = int(RESEND_COOLDOWN_SECONDS - elapsed_seconds)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting a new Telegram OTP."
            )

    # Invalidate older active OTPs for this phone
    await otps_col.update_many(
        {"phone": clean_phone, "used": False},
        {"$set": {"used": True, "invalidatedAt": now.isoformat()}}
    )

    # 3. Cryptographically Secure 6-Digit OTP
    plain_otp = f"{secrets.randbelow(900000) + 100000:06d}"
    salt = secrets.token_hex(16)
    hashed = hash_otp(plain_otp, salt)
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_doc = {
        "phone": clean_phone,
        "chatId": chat_id,
        "otpHash": hashed,
        "salt": salt,
        "purpose": purpose,
        "attempts": 0,
        "maxAttempts": MAX_OTP_ATTEMPTS,
        "used": False,
        "createdAt": now.isoformat(),
        "expiresAt": expires_at.isoformat(),
    }
    await otps_col.insert_one(otp_doc)

    # 4. Check if Telegram is configured
    if not is_telegram_configured():
        # Do not pretend an OTP was sent
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Telegram authentication is not configured on this server (TELEGRAM_BOT_TOKEN missing in backend environment). "
                "Please use standard password authentication."
            )
        )

    # 5. Dispatch OTP via Telegram Bot HTTPS API
    otp_message = (
        "🔐 *Namma Vivasayi AI — Security Verification Code*\n\n"
        f"Your one-time login OTP is: *{plain_otp}*\n\n"
        "⏰ This code is valid for 5 minutes. Do not share this OTP with anyone.\n"
        "நம்ம விவசாயி AI — பாதுகாப்பான உழவர் கணக்கு சரிபார்ப்பு."
    )

    try:
        client_to_use = custom_client or httpx.AsyncClient(timeout=8.0)
        async with client_to_use as cl:
            res = await cl.post(
                f"{TELEGRAM_API_BASE}/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": otp_message,
                    "parse_mode": "Markdown"
                }
            )
            if res.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to deliver Telegram OTP. Please check your bot chat and retry."
                )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error connecting to Telegram Bot API. Please try again or use password login."
        )

    # Mask chat ID for privacy
    masked_chat = f"...{chat_id[-4:]}" if len(chat_id) > 4 else "***"

    return {
        "success": True,
        "message": f"Security OTP sent to linked Telegram chat ({masked_chat}).",
        "maskedChat": masked_chat,
        "cooldownSeconds": RESEND_COOLDOWN_SECONDS,
        "expiresInSeconds": OTP_EXPIRY_MINUTES * 60,
    }


async def verify_telegram_otp(
    phone: str,
    otp_candidate: str,
    purpose: str = "login"
) -> Dict[str, Any]:
    """
    Verifies candidate OTP against stored hash.
    Enforces expiry, single-use, and max attempts.
    """
    clean_phone = re.sub(r"[^\d]", "", phone)
    if len(clean_phone) == 12 and clean_phone.startswith("91"):
        clean_phone = clean_phone[2:]

    otps_col = get_telegram_otps_collection()
    if otps_col is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    clean_otp = otp_candidate.strip()
    if not re.match(r"^\d{6}$", clean_otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must be a 6-digit numeric code."
        )

    # Find the latest unused OTP for this phone
    otp_record = await otps_col.find_one(
        {"phone": clean_phone, "used": False},
        sort=[("createdAt", -1)]
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP found for this mobile number. Please request a new OTP."
        )

    # Check expiry
    now = datetime.utcnow()
    expires_at = datetime.fromisoformat(otp_record["expiresAt"])
    if now > expires_at:
        await otps_col.update_one({"_id": otp_record["_id"]}, {"$set": {"used": True, "reason": "EXPIRED"}})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The OTP has expired. Please request a new one."
        )

    # Check attempt limit
    attempts = otp_record.get("attempts", 0)
    max_attempts = otp_record.get("maxAttempts", MAX_OTP_ATTEMPTS)
    if attempts >= max_attempts:
        await otps_col.update_one({"_id": otp_record["_id"]}, {"$set": {"used": True, "reason": "MAX_ATTEMPTS_EXCEEDED"}})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Maximum verification attempts exceeded. Please request a new OTP."
        )

    # Verify salted hash
    is_valid = verify_otp_hash(clean_otp, otp_record["salt"], otp_record["otpHash"])

    if not is_valid:
        new_attempts = attempts + 1
        remaining = max_attempts - new_attempts
        update_data = {"attempts": new_attempts}
        if remaining <= 0:
            update_data["used"] = True
            update_data["reason"] = "MAX_ATTEMPTS_EXCEEDED"

        await otps_col.update_one({"_id": otp_record["_id"]}, {"$set": update_data})

        if remaining <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP. Maximum attempts reached. Please request a new code."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP code. {remaining} attempt(s) remaining."
        )

    # Single-use: Mark as USED immediately
    await otps_col.update_one(
        {"_id": otp_record["_id"]},
        {"$set": {"used": True, "verifiedAt": now.isoformat()}}
    )

    # Generate single-use verification token for registration step if needed
    verified_token = secrets.token_urlsafe(24)

    return {
        "success": True,
        "message": "OTP verified successfully.",
        "phone": clean_phone,
        "verifiedToken": verified_token
    }
