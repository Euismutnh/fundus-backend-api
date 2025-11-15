import re
import secrets
import string
from typing import Optional, Union, Dict
from datetime import datetime, timedelta, date
import hashlib


def generate_random_string(length: int = 32) -> str:
    """Generate random string for tokens"""
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(length)
    )


# def validate_email(email: str) -> bool:

#     # Basic checks
#     if not email or not isinstance(email, str):
#         return False

#     # Remove leading/trailing whitespace
#     email = email.strip()

#     # Must contain exactly one @
#     if email.count("@") != 1:
#         return False

#     # Check for spaces
#     if " " in email:
#         return False

#     # Split into local and domain parts
#     try:
#         local, domain = email.rsplit("@", 1)
#     except ValueError:
#         return False

#     # Local part validation
#     if not local or len(local) > 64:  # RFC 5321
#         return False

#     # Local part cannot start or end with dot
#     if local.startswith(".") or local.endswith("."):
#         return False

#     # No consecutive dots in local part
#     if ".." in local:
#         return False

#     # Local part pattern: must start with alphanumeric
#     local_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9._%+-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$"
#     if not re.match(local_pattern, local):
#         return False

#     # Domain validation
#     if not domain or len(domain) > 255:  # RFC 5321
#         return False

#     # Domain must contain at least one dot
#     if "." not in domain:
#         return False

#     # No consecutive dots in domain
#     if ".." in domain:
#         return False

#     # Domain cannot start or end with dot or hyphen
#     if domain.startswith(".") or domain.endswith("."):
#         return False
#     if domain.startswith("-") or domain.endswith("-"):
#         return False

#     # Domain pattern validation (support subdomain)
#     domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
#     if not re.match(domain_pattern, domain):
#         return False

#     # All checks passed
#     return True


def validate_phone_number(phone: str) -> bool:

    if not phone or not isinstance(phone, str):
        return False

    pattern = r"^08\d{8,13}$"
    return re.match(pattern, phone) is not None


def validate_password_strength(password: str) -> Dict:

    result = {"is_valid": True, "errors": []}

    if len(password) < 8:
        result["is_valid"] = False
        result["errors"].append("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        result["is_valid"] = False
        result["errors"].append("Password must contain at least one uppercase letter")

    if not re.search(r"[a-z]", password):
        result["is_valid"] = False
        result["errors"].append("Password must contain at least one lowercase letter")

    if not re.search(r"\d", password):
        result["is_valid"] = False
        result["errors"].append("Password must contain at least one number")

    # Special character is recommended but not required
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result["errors"].append(
            "Password should contain at least one special character (recommended)"
        )

    return result


def validate_patient_code(code: str) -> bool:

    if not code or not isinstance(code, str):
        return False

    code = code.strip()
    if not code or len(code) > 50:
        return False

    return True


def validate_date_of_birth(dob: date) -> Dict:

    today = datetime.now().date()

    if dob > today:
        return {"is_valid": False, "error": "Date of birth cannot be in the future"}

    age = calculate_age(dob)
    if age < 0 or age > 150:
        return {"is_valid": False, "error": "Invalid age (must be between 0-150 years)"}

    return {"is_valid": True, "error": None}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    filename = re.sub(r"[^\w\s.-]", "", filename)
    filename = re.sub(r"[-\s]+", "-", filename)
    return filename.strip("-")


def generate_file_hash(file_content: bytes) -> str:
    """Generate SHA-256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()


def format_file_size(size_bytes: Union[int, float]) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f}{size_names[i]}"


def is_safe_url(url: str, allowed_hosts: Optional[list] = None) -> bool:
    """Check if URL is safe for redirects"""
    if not url:
        return False

    if not url.startswith(("http://", "https://")):
        return False

    if allowed_hosts:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.netloc in allowed_hosts

    return True


def calculate_age(birth_date: Union[date, datetime]) -> int:
    """Calculate age from birth date"""
    today = datetime.now().date()
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()

    age = today.year - birth_date.year
    if today.month < birth_date.month or (
        today.month == birth_date.month and today.day < birth_date.day
    ):
        age -= 1

    return age


def mask_email(email: str) -> str:
    """Mask email for privacy (e.g., j***@example.com)"""
    if "@" not in email:
        return email

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]

    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number for privacy (e.g., 081234***890)"""
    if len(phone) <= 6:
        return phone

    return phone[:6] + "*" * max(0, (len(phone) - 9)) + phone[-3:]
