"""
Security utilities for FinanceAI
"""
import os
import hashlib
import secrets
from typing import Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time
from collections import defaultdict

# Rate limiting storage (in production, use Redis)
request_counts = defaultdict(list)

security = HTTPBearer(auto_error=False)

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def hash_user_id(user_id: str) -> str:
    """Hash user ID for privacy"""
    salt = os.getenv("SECRET_KEY", "default-salt")
    return hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()[:16]

def validate_user_id(user_id: str) -> bool:
    """Validate user ID format"""
    if not user_id or len(user_id) > 50:
        return False
    # Allow alphanumeric and underscores only
    return user_id.replace("_", "").replace("-", "").isalnum()

def rate_limit_check(client_ip: str, limit: int = 100, window: int = 60) -> bool:
    """Simple rate limiting (use Redis in production)"""
    now = time.time()
    
    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < window
    ]
    
    # Check if limit exceeded
    if len(request_counts[client_ip]) >= limit:
        return False
    
    # Add current request
    request_counts[client_ip].append(now)
    return True

def get_client_ip(request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

async def verify_rate_limit(request):
    """Rate limiting dependency"""
    client_ip = get_client_ip(request)
    
    if not rate_limit_check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return True

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = "".join(char for char in text if char.isprintable())
    
    # Limit length
    return sanitized[:max_length]

def validate_amount(amount: float) -> bool:
    """Validate transaction amount"""
    return 0 <= amount <= 1000000  # Max $1M per transaction

class SecurityHeaders:
    """Add security headers to responses"""
    
    @staticmethod
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response