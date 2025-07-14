import os
import logging
import pyotp
import requests
from typing import Dict, Any, Optional, Tuple
from linkedin_api import Linkedin
from linkedin_api.client import Client, ChallengeException
from requests.cookies import RequestsCookieJar
import dotenv
from config import (
    ENV_LI_AT, ENV_LI_JSESSIONID, ENV_LI_USER, ENV_LI_PASS, 
    ENV_LI_TOTP_SECRET, LINKEDIN_TIMEOUT, LINKEDIN_MAX_RETRIES
)
from dynamic_cookie_generator import DynamicCookieGenerator
from cookie_refresher import CookieRefresher

# Initialize logger
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
)
log = logging.getLogger(__name__)

class TOTPClient(Client):
    """Extended LinkedIn client with TOTP support"""
    
    def __init__(self, totp_secret: str = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.totp_secret = totp_secret
        if totp_secret:
            self.totp = pyotp.TOTP(totp_secret)
    
    def _do_authentication_request(self, username: str, password: str):
        """
        Authenticate with LinkedIn, handling TOTP challenges.
        """
        self._set_session_cookies(self._request_session_cookies())

        payload = {
            "session_key": username,
            "session_password": password,
            "JSESSIONID": self.session.cookies["JSESSIONID"],
        }

        # If we have TOTP secret, try including it in the initial request
        if self.totp_secret:
            totp_code = self.totp.now()
            log.info(f"🔐 Including TOTP code in initial request: {totp_code}")
            payload["totp_code"] = totp_code
            payload["challenge_type"] = "TOTP"

        res = requests.post(
            f"{Client.LINKEDIN_BASE_URL}/uas/authenticate",
            data=payload,
            cookies=self.session.cookies,
            headers=Client.AUTH_REQUEST_HEADERS,
            proxies=self.proxies,
        )

        data = res.json()
        log.info(f"🔍 Initial authentication response: {data}")

        if data and data["login_result"] != "PASS":
            # Handle 2FA challenge
            if data["login_result"] == "CHALLENGE" and self.totp_secret:
                log.info("🔐 2FA challenge detected, attempting TOTP authentication...")
                return self._handle_totp_challenge(username, data)
            else:
                raise ChallengeException(data["login_result"])

        if res.status_code == 401:
            raise UnauthorizedException()

        if res.status_code != 200:
            raise Exception()

        self._set_session_cookies(res.cookies)
        self._cookie_repository.save(res.cookies, username)
    
    def _handle_totp_challenge(self, username: str, challenge_data: Dict):
        """
        Handle TOTP challenge by generating and submitting the TOTP code.
        """
        try:
            log.info(f"🔍 Challenge data: {challenge_data}")
            
            # Generate current TOTP code
            totp_code = self.totp.now()
            log.info(f"🔐 Generated TOTP code: {totp_code}")
            
            # Try different payload formats based on LinkedIn's API
            # Format 1: Standard TOTP challenge
            totp_payload = {
                "session_key": username,
                "JSESSIONID": self.session.cookies["JSESSIONID"],
                "challenge_id": challenge_data.get("challenge_id", ""),
                "challenge_type": "TOTP",
                "totp_code": totp_code,
            }
            
            log.info(f"🔍 TOTP payload: {totp_payload}")
            
            res = requests.post(
                f"{Client.LINKEDIN_BASE_URL}/uas/authenticate",
                data=totp_payload,
                cookies=self.session.cookies,
                headers=Client.AUTH_REQUEST_HEADERS,
                proxies=self.proxies,
            )
            
            log.info(f"🔍 TOTP response status: {res.status_code}")
            log.info(f"🔍 TOTP response headers: {dict(res.headers)}")
            
            try:
                data = res.json()
                log.info(f"🔍 TOTP response data: {data}")
            except:
                log.info(f"🔍 TOTP response text: {res.text}")
                data = {}
            
            # Check for successful authentication
            if data and data.get("login_result") == "PASS":
                log.info("✅ TOTP authentication successful")
                self._set_session_cookies(res.cookies)
                self._cookie_repository.save(res.cookies, username)
                return
            
            # If first attempt failed, try alternative payload format
            log.info("🔄 First TOTP attempt failed, trying alternative format...")
            
            # Format 2: Alternative TOTP challenge format
            totp_payload_alt = {
                "session_key": username,
                "JSESSIONID": self.session.cookies["JSESSIONID"],
                "challenge_id": challenge_data.get("challenge_id", ""),
                "challenge_type": "TOTP",
                "totp_code": totp_code,
                "login_result": "CHALLENGE",  # Some APIs expect this
            }
            
            log.info(f"🔍 Alternative TOTP payload: {totp_payload_alt}")
            
            res_alt = requests.post(
                f"{Client.LINKEDIN_BASE_URL}/uas/authenticate",
                data=totp_payload_alt,
                cookies=self.session.cookies,
                headers=Client.AUTH_REQUEST_HEADERS,
                proxies=self.proxies,
            )
            
            log.info(f"🔍 Alternative TOTP response status: {res_alt.status_code}")
            
            try:
                data_alt = res_alt.json()
                log.info(f"🔍 Alternative TOTP response data: {data_alt}")
            except:
                log.info(f"🔍 Alternative TOTP response text: {res_alt.text}")
                data_alt = {}
            
            # Check for successful authentication in alternative response
            if data_alt and data_alt.get("login_result") == "PASS":
                log.info("✅ TOTP authentication successful (alternative format)")
                self._set_session_cookies(res_alt.cookies)
                self._cookie_repository.save(res_alt.cookies, username)
                return
            
            # If both attempts failed, check if we got a different success indicator
            success_indicators = ["PASS", "SUCCESS", "OK", "AUTHENTICATED"]
            for indicator in success_indicators:
                if data and data.get("login_result") == indicator:
                    log.info(f"✅ TOTP authentication successful (indicator: {indicator})")
                    self._set_session_cookies(res.cookies)
                    self._cookie_repository.save(res.cookies, username)
                    return
                if data_alt and data_alt.get("login_result") == indicator:
                    log.info(f"✅ TOTP authentication successful (alternative, indicator: {indicator})")
                    self._set_session_cookies(res_alt.cookies)
                    self._cookie_repository.save(res_alt.cookies, username)
                    return
            
            # If we get here, both attempts failed
            log.error(f"❌ TOTP authentication failed - both attempts failed")
            log.error(f"❌ First response: {data}")
            log.error(f"❌ Alternative response: {data_alt}")
            raise ChallengeException(f"TOTP authentication failed after multiple attempts")
                
        except Exception as e:
            log.error(f"❌ Error during TOTP challenge: {e}")
            log.error(f"❌ Error type: {type(e).__name__}")
            import traceback
            log.error(f"❌ Traceback: {traceback.format_exc()}")
            raise ChallengeException(f"TOTP challenge failed: {e}")

class LinkedInClient:
    """LinkedIn API client for fetching profile data"""
    
    def __init__(self):
        """Initialize the LinkedIn client"""
        self.api = None
        self._load_environment()
    
    def _load_environment(self):
        """Load environment variables from .env file"""
        dotenv.load_dotenv()
    
    def authenticate(self, use_cookies: bool = True) -> Tuple[bool, str]:
        """
        Authenticate with LinkedIn using cookies or credentials.
        
        Args:
            use_cookies (bool): Whether to use cookie-based authentication
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            if use_cookies:
                return self._authenticate_with_cookies()
            else:
                return self._authenticate_with_credentials()
        except Exception as e:
            error_msg = f"Authentication Error: {e}"
            log.error(f"❌ {error_msg}")
            return False, error_msg
    
    def _authenticate_with_cookies(self) -> Tuple[bool, str]:
        """Authenticate using dynamic cookie generation (bypassing static cookies)"""
        try:
            log.info("🚀 Forcing dynamic cookie generation (bypassing static cookies)...")
            
            # Skip static cookies entirely and go straight to dynamic generation
            return self._authenticate_with_dynamic_cookies()
                
        except Exception as e:
            error_msg = f"Dynamic cookie authentication failed: {e}"
            log.error(f"❌ {error_msg}")
            log.debug(f"❌ Exception details: {type(e).__name__}: {str(e)}")
            return False, error_msg
    
    def _authenticate_with_dynamic_cookies(self) -> Tuple[bool, str]:
        """Authenticate using dynamic cookie generation with browser automation"""
        try:
            user = os.getenv(ENV_LI_USER, "").strip()
            pwd = os.getenv(ENV_LI_PASS, "").strip()
            totp_secret = os.getenv(ENV_LI_TOTP_SECRET, "").strip()
            
            log.debug(f"🔍 Dynamic cookie generation - User available: {'Yes' if user else 'No'}")
            log.debug(f"🔍 Dynamic cookie generation - Password available: {'Yes' if pwd else 'No'}")
            log.debug(f"🔍 Dynamic cookie generation - TOTP secret available: {'Yes' if totp_secret else 'No'}")
            
            if not user or not pwd:
                error_msg = "Username and password required for dynamic cookie generation"
                log.error(f"❌ {error_msg}")
                log.debug(f"❌ Missing credentials - User: {bool(user)}, Password: {bool(pwd)}")
                return False, error_msg
            
            log.info("🚀 Starting dynamic cookie generation with browser automation...")
            
            # Try dynamic cookie generation with browser automation
            try:
                log.debug("🔄 Attempting browser automation for dynamic cookie generation...")
                # Create dynamic cookie generator
                cookie_generator = DynamicCookieGenerator(headless=True)
                
                # Generate cookies
                cookies = cookie_generator.get_cookies_from_credentials(
                    username=user,
                    password=pwd,
                    totp_secret=totp_secret if totp_secret else None
                )
                
                if cookies:
                    log.debug(f"✅ Dynamic cookies generated successfully - {len(cookies)} cookies")
                    # Initialize LinkedIn API with dynamic cookies
                    self.api = Linkedin("", "", cookies=cookies)
                    log.info("✅ Authenticated via dynamic cookies")
                    return True, ""
                else:
                    error_msg = "Dynamic cookie generation returned no cookies"
                    log.error(f"❌ {error_msg}")
                    return False, error_msg
                    
            except Exception as e:
                error_msg = f"Dynamic cookie generation failed: {e}"
                log.error(f"❌ {error_msg}")
                log.debug(f"❌ Dynamic generation exception: {type(e).__name__}: {str(e)}")
                return False, error_msg
            
        except Exception as e:
            error_msg = f"Dynamic cookie authentication failed: {e}"
            log.error(f"❌ {error_msg}")
            log.debug(f"❌ Dynamic auth exception: {type(e).__name__}: {str(e)}")
            return False, error_msg
    
    def _authenticate_with_credentials(self) -> Tuple[bool, str]:
        """Authenticate using LinkedIn username/password with TOTP support"""
        try:
            user = os.getenv(ENV_LI_USER, "").strip()
            pwd = os.getenv(ENV_LI_PASS, "").strip()
            
            if not user or not pwd:
                error_msg = "Username and password not provided in environment variables"
                log.error(f"❌ {error_msg}")
                return False, error_msg
            
            # Check for TOTP secret for 2FA
            totp_secret = os.environ.get(ENV_LI_TOTP_SECRET, "").strip()
            if totp_secret:
                log.info("🔐 TOTP secret found - 2FA authentication enabled")
                log.debug(f"TOTP secret length: {len(totp_secret)}")
            else:
                log.warning("⚠️ No TOTP secret provided - 2FA challenges may fail")
            
            log.info("🔐 Attempting credential authentication...")
            log.debug(f"Using username: {user}")
            log.debug(f"TOTP secret provided: {'Yes' if totp_secret else 'No'}")
            
            # Create a custom LinkedIn instance with TOTP support
            if totp_secret:
                # Use our patched client with TOTP support
                client = TOTPClient(totp_secret=totp_secret, debug=True)
                client.authenticate(user, pwd)
                
                # Create LinkedIn API wrapper with our authenticated client
                self.api = Linkedin.__new__(Linkedin)
                self.api.client = client
                self.api.logger = logging.getLogger(__name__)
                
                # Copy necessary methods from Linkedin class
                self.api._fetch = Linkedin._fetch.__get__(self.api, Linkedin)
                self.api._post = Linkedin._post.__get__(self.api, Linkedin)
                self.api._cookies = Linkedin._cookies.__get__(self.api, Linkedin)
                self.api._headers = Linkedin._headers.__get__(self.api, Linkedin)
                
                log.info("✅ Authenticated via credentials with TOTP")
                return True, ""
            else:
                # Fallback to original LinkedIn API (may fail with 2FA)
                self.api = Linkedin(user, pwd)
                log.info("✅ Authenticated via credentials (no TOTP)")
                return True, ""
            
        except ChallengeException as e:
            error_msg = f"LinkedIn 2FA challenge: {e}"
            log.error(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = self._parse_authentication_error(e)
            log.error(f"❌ {error_msg}")
            log.error(f"❌ Full error: {e}")
            log.error(f"❌ Error type: {type(e).__name__}")
            return False, error_msg
    
    def _parse_authentication_error(self, error: Exception) -> str:
        """Parse authentication errors and provide helpful messages"""
        error_str = str(error).upper()
        
        if "CHALLENGE" in error_str:
            return "LinkedIn requires 2FA verification. TOTP authentication is complex and may not work reliably. Please use cookie-based authentication (recommended) by setting LI_AT and LI_JSESSIONID environment variables."
        elif "INVALID_CREDENTIALS" in error_str or "WRONG_PASSWORD" in error_str:
            return "Invalid username or password. Please check your LinkedIn credentials."
        elif "ACCOUNT_LOCKED" in error_str or "SUSPICIOUS_ACTIVITY" in error_str:
            return "LinkedIn account is locked or flagged for suspicious activity. Please check your LinkedIn account status."
        elif "RATE_LIMIT" in error_str or "TOO_MANY_REQUESTS" in error_str:
            return "Rate limit exceeded. Please wait before trying again."
        elif "NETWORK" in error_str or "CONNECTION" in error_str:
            return "Network connection error. Please check your internet connection."
        else:
            return f"Authentication failed: {error}"
    
    def fetch_profile_data(self, public_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch comprehensive profile data from LinkedIn.
        
        Args:
            public_id (str): LinkedIn public profile ID
            
        Returns:
            Optional[Dict[str, Any]]: Complete profile data or None if failed
        """
        if not self.api:
            log.error("❌ Not authenticated. Call authenticate() first.")
            return None
        
        try:
            log.info("📄 Fetching profile...")
            profile = self.api.get_profile(public_id=public_id)
            log.info("✅ Profile fetched successfully")
            
            log.info("📇 Fetching contact info...")
            profile["contact_info"] = self.api.get_profile_contact_info(
                public_id=profile["public_id"]
            )
            log.info("✅ Contact info fetched successfully")
            
            log.info("🛠️ Fetching skills info...")
            profile["skills"] = self.api.get_profile_skills(
                public_id=profile["public_id"]
            )
            log.info("✅ Skills info fetched successfully")
            
            log.info("💼 Fetching experiences info...")
            profile["experiences"] = self.api.get_profile_experiences(
                urn_id=profile["urn_id"]
            )
            log.info("✅ Experiences info fetched successfully")
            
            return profile
            
        except Exception as e:
            log.error(f"❌ Error fetching profile data: {e}")
            return None
    
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated"""
        return self.api is not None 