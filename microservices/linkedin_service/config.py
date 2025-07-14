import os
from typing import List

# Month abbreviations for date formatting
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Service configuration
SERVICE_NAME = "LinkedIn Service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8001

# LinkedIn API configuration
LINKEDIN_TIMEOUT = 30  # seconds
LINKEDIN_MAX_RETRIES = 3

# Environment variable names
ENV_LI_AT = "LI_AT"
ENV_LI_JSESSIONID = "LI_JSESSIONID"
ENV_LI_USER = "LI_USER"
ENV_LI_PASS = "LI_PASS"
ENV_LI_TOTP_SECRET = "LI_TOTP_SECRET"
ENV_LI_PID = "LI_PID"

# Required environment variables for authentication
REQUIRED_ENV_VARS = [ENV_LI_PID]

# Optional environment variables (for fallback authentication)
OPTIONAL_ENV_VARS = [ENV_LI_AT, ENV_LI_JSESSIONID, ENV_LI_USER, ENV_LI_PASS, ENV_LI_TOTP_SECRET]

def get_required_env_var(var_name: str) -> str:
    """Get a required environment variable or raise an error"""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Missing required environment variable: {var_name}")
    return value

def get_optional_env_var(var_name: str) -> str:
    """Get an optional environment variable"""
    return os.getenv(var_name, "")

def validate_environment() -> bool:
    """Validate that all required environment variables are set"""
    try:
        for var in REQUIRED_ENV_VARS:
            get_required_env_var(var)
        return True
    except ValueError as e:
        print(f"Environment validation failed: {e}")
        return False 