#!/usr/bin/env python3
"""
LinkedIn Cookie Refresher

This module provides functionality to validate and refresh LinkedIn cookies
without requiring browser automation.
"""

import os
import logging
import requests
from typing import Dict, Optional, Tuple
from requests.cookies import RequestsCookieJar
import dotenv

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

class CookieRefresher:
    """LinkedIn cookie refresher and validator"""
    
    def __init__(self):
        """Initialize the cookie refresher"""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
    
    def validate_cookies(self, li_at: str, jsessionid: str) -> Tuple[bool, str]:
        """
        Validate existing LinkedIn cookies
        
        Args:
            li_at (str): LinkedIn li_at cookie value
            jsessionid (str): LinkedIn JSESSIONID cookie value
            
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        try:
            # Set up cookies
            cookie_jar = RequestsCookieJar()
            cookie_jar.set("li_at", li_at, domain=".linkedin.com", path="/")
            cookie_jar.set("JSESSIONID", jsessionid, domain=".linkedin.com", path="/")
            
            self.session.cookies = cookie_jar
            
            # Test cookies by accessing LinkedIn feed
            log.info("🔍 Validating cookies by accessing LinkedIn feed...")
            response = self.session.get("https://www.linkedin.com/feed/", timeout=10)
            
            if response.status_code == 200:
                # Check if we're actually logged in by looking for feed content
                if "feed" in response.url.lower() or "mynetwork" in response.url.lower():
                    log.info("✅ Cookies are valid and working")
                    return True, "Cookies are valid"
                else:
                    log.warning("⚠️ Cookies may be expired - redirected to login")
                    return False, "Cookies expired - redirected to login"
            elif response.status_code == 302:
                # Redirected to login page
                log.warning("⚠️ Cookies expired - redirected to login")
                return False, "Cookies expired - redirected to login"
            else:
                log.warning(f"⚠️ Unexpected response: {response.status_code}")
                return False, f"Unexpected response: {response.status_code}"
                
        except Exception as e:
            log.error(f"❌ Error validating cookies: {e}")
            return False, f"Validation error: {e}"
    
    def refresh_cookies(self, li_at: str, jsessionid: str) -> Tuple[bool, str, Optional[RequestsCookieJar]]:
        """
        Attempt to refresh cookies by making requests to LinkedIn
        
        Args:
            li_at (str): LinkedIn li_at cookie value
            jsessionid (str): LinkedIn JSESSIONID cookie value
            
        Returns:
            Tuple[bool, str, Optional[RequestsCookieJar]]: (success, message, refreshed_cookies)
        """
        try:
            # Set up initial cookies
            cookie_jar = RequestsCookieJar()
            cookie_jar.set("li_at", li_at, domain=".linkedin.com", path="/")
            cookie_jar.set("JSESSIONID", jsessionid, domain=".linkedin.com", path="/")
            
            self.session.cookies = cookie_jar
            
            # Make a request to refresh the session
            log.info("🔄 Attempting to refresh cookies...")
            response = self.session.get("https://www.linkedin.com/", timeout=10)
            
            # Check if we got new cookies
            new_li_at = self.session.cookies.get("li_at")
            new_jsessionid = self.session.cookies.get("JSESSIONID")
            
            if new_li_at and new_jsessionid:
                log.info("✅ Cookies refreshed successfully")
                return True, "Cookies refreshed", self.session.cookies
            else:
                log.warning("⚠️ No new cookies received")
                return False, "No new cookies received", None
                
        except Exception as e:
            log.error(f"❌ Error refreshing cookies: {e}")
            return False, f"Refresh error: {e}", None
    
    def get_cookie_status(self, li_at: str, jsessionid: str) -> Dict:
        """
        Get comprehensive status of LinkedIn cookies
        
        Args:
            li_at (str): LinkedIn li_at cookie value
            jsessionid (str): LinkedIn JSESSIONID cookie value
            
        Returns:
            Dict: Cookie status information
        """
        try:
            # Validate cookies
            is_valid, validation_message = self.validate_cookies(li_at, jsessionid)
            
            # Try to refresh if not valid
            if not is_valid:
                refresh_success, refresh_message, refreshed_cookies = self.refresh_cookies(li_at, jsessionid)
                
                return {
                    "original_valid": False,
                    "validation_message": validation_message,
                    "refresh_attempted": True,
                    "refresh_success": refresh_success,
                    "refresh_message": refresh_message,
                    "has_refreshed_cookies": refreshed_cookies is not None
                }
            else:
                return {
                    "original_valid": True,
                    "validation_message": validation_message,
                    "refresh_attempted": False,
                    "refresh_success": None,
                    "refresh_message": None,
                    "has_refreshed_cookies": False
                }
                
        except Exception as e:
            return {
                "error": str(e),
                "original_valid": False,
                "validation_message": f"Error: {e}",
                "refresh_attempted": False,
                "refresh_success": False,
                "refresh_message": f"Error: {e}",
                "has_refreshed_cookies": False
            } 