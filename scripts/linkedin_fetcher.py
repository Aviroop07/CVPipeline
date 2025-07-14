#!/usr/bin/env python3
"""
LinkedIn data fetching module.

This module provides functions to authenticate with LinkedIn and fetch profile data.
"""

import json, os, pathlib, sys, dotenv, logging
from linkedin_api import Linkedin
from requests.cookies import RequestsCookieJar
import config
import api_cache

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / config.DATA_DIR
DST = OUT / config.LINKEDIN_RAW_FILE

def authenticate_linkedin():
    """
    Authenticate with LinkedIn using cookies or credentials.
    
    Returns:
        Linkedin: Authenticated LinkedIn API client
        
    Raises:
        SystemExit: If authentication fails or required environment variables are missing
    """
    try:
        dotenv.load_dotenv()
        user = os.environ["LI_USER"]
        pwd = os.environ["LI_PASS"]
        # TOTP secret may be used internally by linkedin-api for 2FA
        os.environ.get("LI_TOTP_SECRET", "")
        
        # Debug: log environment variables in use
        log.debug("🔧 Environment variables:")
        for var in (
            "LI_USER",
            "LI_PASS", 
            "LI_TOTP_SECRET",
            "LI_AT",
            "LI_JSESSIONID",
            "LI_PID",
        ):
            log.debug(f"  {var} = {os.getenv(var)}")
    except KeyError as miss:
        sys.exit(f"✖ missing env var {miss}")

    try:
        log.info("🔐 Authenticating with LinkedIn via cookies...")

        li_at = os.getenv("LI_AT", "").strip()
        jsessionid = os.getenv("LI_JSESSIONID", "").strip()

        if li_at and jsessionid:
            # Build a cookie jar with existing session cookies
            jar = RequestsCookieJar()
            jar.set("li_at", li_at, domain=".linkedin.com", path="/")
            jar.set("JSESSIONID", jsessionid, domain=".linkedin.com", path="/")

            # Initialize LinkedIn API with cookie jar (username/password are unused in this case)
            api = Linkedin("", "", cookies=jar)
            log.info("✅ Authenticated via cookies")
        else:
            # Fallback to username/password auth (may trigger 2FA challenge)
            log.info("🔐 Cookies not provided – falling back to username/password auth. This may be less reliable on GitHub Actions.")
            api = Linkedin(user, pwd)
            log.info("✅ Authenticated via credentials")
            
        return api
        
    except Exception as e:
        log.error(f"❌ Authentication Error: {e}")
        log.error(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def fetch_profile_data(api, public_id):
    """
    Fetch comprehensive profile data from LinkedIn.
    
    Args:
        api (Linkedin): Authenticated LinkedIn API client
        public_id (str): LinkedIn public profile ID
        
    Returns:
        dict: Complete profile data including contact info, skills, and experiences
        
    Raises:
        Exception: If any API call fails
    """
    try:
        log.info("📄 Fetching profile...")
        
        # Use cached API call if enabled
        if config.API_CACHE_ENABLED:
            profile = api_cache.cached_api_call(
                "linkedin_profile",
                {"public_id": public_id},
                api.get_profile,
                public_id=public_id
            )
        else:
            profile = api.get_profile(public_id=public_id)
        
        log.info("✅ Profile fetched successfully")
        
        log.info("📇 Fetching contact info...")
        if config.API_CACHE_ENABLED:
            profile["contact_info"] = api_cache.cached_api_call(
                "linkedin_contact_info",
                {"public_id": profile["public_id"]},
                api.get_profile_contact_info,
                public_id=profile["public_id"]
            )
        else:
            profile["contact_info"] = api.get_profile_contact_info(
                public_id=profile["public_id"]
            )
        log.info("✅ Contact info fetched successfully")
        
        log.info("🛠️ Fetching skills info...")
        if config.API_CACHE_ENABLED:
            profile["skills"] = api_cache.cached_api_call(
                "linkedin_skills",
                {"public_id": profile["public_id"]},
                api.get_profile_skills,
                public_id=profile["public_id"]
            )
        else:
            profile["skills"] = api.get_profile_skills(
                public_id=profile["public_id"]
            )
        log.info("✅ Skills info fetched successfully")
        
        log.info("💼 Fetching experiences info...")
        if config.API_CACHE_ENABLED:
            profile["experiences"] = api_cache.cached_api_call(
                "linkedin_experiences",
                {"urn_id": profile["urn_id"]},
                api.get_profile_experiences,
                urn_id=profile["urn_id"]
            )
        else:
            profile["experiences"] = api.get_profile_experiences(
                urn_id=profile["urn_id"]
            )
        log.info("✅ Experiences info fetched successfully")
        
        return profile
        
    except Exception as e:
        log.error(f"❌ Error fetching profile data: {e}")
        log.error(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise

def save_linkedin_data(profile_data, output_path=None):
    """
    Save LinkedIn profile data to JSON file.
    
    Args:
        profile_data (dict): Profile data to save
        output_path (pathlib.Path, optional): Custom output path. Defaults to configured path.
        
    Returns:
        pathlib.Path: Path where data was saved
    """
    if output_path is None:
        OUT.mkdir(exist_ok=True)
        output_path = DST
    
    output_path.write_text(
        json.dumps(profile_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info(f"✅ wrote {output_path.relative_to(ROOT)}")
    return output_path

def fetch_linkedin_data():
    """
    Complete LinkedIn data fetching pipeline.
    
    Returns:
        dict: Fetched profile data
        
    Raises:
        SystemExit: If any step fails
    """
    try:
        # Authenticate
        api = authenticate_linkedin()
        
        # Fetch profile data
        public_id = os.environ["LI_PID"]
        profile_data = fetch_profile_data(api, public_id)
        
        # Save data
        save_linkedin_data(profile_data)
        
        return profile_data
        
    except Exception as e:
        log.error(f"❌ LinkedIn fetching failed: {e}")
        sys.exit(1)

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    fetch_linkedin_data()

if __name__ == "__main__":
    main() 