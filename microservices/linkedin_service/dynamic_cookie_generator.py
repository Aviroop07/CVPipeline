#!/usr/bin/env python3
"""
Dynamic LinkedIn Cookie Generator

This module provides functionality to dynamically authenticate with LinkedIn
and extract fresh session cookies using browser automation.
"""

import os
import time
import logging
import pyotp
from typing import Dict, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from requests.cookies import RequestsCookieJar

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

class DynamicCookieGenerator:
    """Dynamic LinkedIn cookie generator using browser automation"""
    
    def __init__(self, headless: bool = True):
        """
        Initialize the cookie generator
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        self.headless = headless
        self.driver = None
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Add other options for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            # Disable images and CSS for faster loading
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.notifications": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Try to find Chrome in common locations
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
            ]
            
            chrome_found = False
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_options.binary_location = path
                    chrome_found = True
                    log.info(f"✅ Found Chrome at: {path}")
                    break
            
            if not chrome_found:
                log.warning("⚠️ Chrome not found in common locations, trying default...")
            
            # Set up ChromeDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            return driver
            
        except Exception as e:
            log.error(f"❌ Failed to set up Chrome driver: {e}")
            raise Exception(f"Chrome setup failed: {e}. Please ensure Chrome is installed.")
    
    def authenticate_and_get_cookies(self, username: str, password: str, totp_secret: str = None) -> Tuple[bool, str, Optional[RequestsCookieJar]]:
        """
        Authenticate with LinkedIn and extract cookies
        
        Args:
            username (str): LinkedIn username/email
            password (str): LinkedIn password
            totp_secret (str, optional): TOTP secret for 2FA
            
        Returns:
            Tuple[bool, str, Optional[RequestsCookieJar]]: (success, message, cookies)
        """
        try:
            log.info("🚀 Starting dynamic cookie generation...")
            
            # Set up driver
            self.driver = self._setup_driver()
            
            # Navigate to LinkedIn login page
            log.info("📱 Navigating to LinkedIn login page...")
            self.driver.get("https://www.linkedin.com/login")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Enter username
            log.info("👤 Entering username...")
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            username_field.send_keys(username)
            
            # Enter password
            log.info("🔐 Entering password...")
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click sign in button
            log.info("🔑 Clicking sign in button...")
            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            sign_in_button.click()
            
            # Handle 2FA if needed
            if totp_secret:
                log.info("🔐 2FA detected, handling TOTP challenge...")
                success = self._handle_totp_challenge(totp_secret)
                if not success:
                    return False, "Failed to handle TOTP challenge", None
            
            # Wait for successful login (redirect to feed or profile)
            log.info("⏳ Waiting for successful authentication...")
            try:
                # Wait for either feed page or profile page
                WebDriverWait(self.driver, 15).until(
                    EC.any_of(
                        EC.url_contains("linkedin.com/feed"),
                        EC.url_contains("linkedin.com/in/"),
                        EC.url_contains("linkedin.com/mynetwork"),
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test-id='nav-settings__dropdown-trigger']"))
                    )
                )
                log.info("✅ Authentication successful!")
            except Exception as e:
                log.error(f"❌ Authentication failed: {e}")
                return False, f"Authentication failed: {e}", None
            
            # Extract cookies
            log.info("🍪 Extracting cookies...")
            cookies = self._extract_cookies()
            
            if not cookies:
                return False, "Failed to extract cookies", None
            
            log.info("✅ Cookie extraction successful!")
            return True, "Authentication and cookie extraction successful", cookies
            
        except Exception as e:
            log.error(f"❌ Error during authentication: {e}")
            return False, f"Authentication error: {e}", None
        finally:
            if self.driver:
                self.driver.quit()
    
    def _handle_totp_challenge(self, totp_secret: str) -> bool:
        """
        Handle TOTP challenge during authentication
        
        Args:
            totp_secret (str): TOTP secret for generating codes
            
        Returns:
            bool: True if TOTP challenge was handled successfully
        """
        try:
            log.info("🔐 Handling TOTP challenge...")
            
            # Wait for TOTP input field with multiple possible selectors
            totp_selectors = [
                (By.ID, "pin-input"),
                (By.NAME, "pin"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='code']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='Code']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='verification']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='Verification']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='6-digit']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='6 digit']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='authentication']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='Authentication']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='security']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='Security']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='code']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='Code']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='verification']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='Verification']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='6-digit']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='6 digit']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='authentication']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='Authentication']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='security']"),
                (By.CSS_SELECTOR, "input[type='text'][placeholder*='Security']"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'code')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Code')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'verification')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Verification')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, '6-digit')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, '6 digit')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'authentication')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Authentication')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'security')]"),
                (By.XPATH, "//input[@type='text' and contains(@placeholder, 'Security')]"),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[@type='password']"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input"),
                (By.XPATH, "//input")
            ]
            
            totp_field = None
            for selector_type, selector_value in totp_selectors:
                try:
                    log.debug(f"🔍 Trying TOTP selector: {selector_type} = {selector_value}")
                    totp_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    log.info(f"✅ Found TOTP field with selector: {selector_type} = {selector_value}")
                    break
                except Exception as e:
                    log.debug(f"❌ Selector failed: {selector_type} = {selector_value}")
                    continue
            
            if not totp_field:
                log.error("❌ Could not find TOTP input field with any selector")
                
                # Debug: Show page source and all input fields
                log.info("🔍 Debug: Current page URL: " + self.driver.current_url)
                log.info("🔍 Debug: Page title: " + self.driver.title)
                
                # Get all input fields for debugging
                all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                log.info(f"🔍 Debug: Found {len(all_inputs)} input fields on page:")
                for i, inp in enumerate(all_inputs):
                    try:
                        input_type = inp.get_attribute("type") or "unknown"
                        input_id = inp.get_attribute("id") or "no-id"
                        input_name = inp.get_attribute("name") or "no-name"
                        input_placeholder = inp.get_attribute("placeholder") or "no-placeholder"
                        log.info(f"   Input {i+1}: type={input_type}, id={input_id}, name={input_name}, placeholder={input_placeholder}")
                    except Exception as e:
                        log.info(f"   Input {i+1}: Error getting attributes: {e}")
                
                # Get page source for debugging
                try:
                    page_source = self.driver.page_source
                    log.info(f"🔍 Debug: Page source length: {len(page_source)} characters")
                    # Save page source to file for inspection
                    with open("linkedin_totp_page.html", "w", encoding="utf-8") as f:
                        f.write(page_source)
                    log.info("🔍 Debug: Page source saved to linkedin_totp_page.html")
                except Exception as e:
                    log.error(f"❌ Error getting page source: {e}")
                
                return False
            
            # Generate TOTP code
            totp = pyotp.TOTP(totp_secret)
            totp_code = totp.now()
            log.info(f"🔐 Generated TOTP code: {totp_code}")
            
            # Wait for TOTP field to be interactable
            log.info("🔐 Waiting for TOTP field to be interactable...")
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input"))
                )
            except Exception as e:
                log.warning(f"⚠️ Could not wait for element to be clickable: {e}")
            
            # Enter TOTP code with better error handling
            log.info("🔐 Entering TOTP code...")
            try:
                # Try to clear the field first
                try:
                    totp_field.clear()
                except Exception as e:
                    log.warning(f"⚠️ Could not clear field: {e}")
                
                # Try to send keys
                totp_field.send_keys(totp_code)
                log.info("✅ TOTP code entered successfully")
            except Exception as e:
                log.error(f"❌ Error entering TOTP code: {e}")
                log.info("🔄 Trying alternative method...")
                
                # Try JavaScript injection as fallback
                try:
                    self.driver.execute_script(f"arguments[0].value = '{totp_code}';", totp_field)
                    log.info("✅ TOTP code entered via JavaScript")
                except Exception as js_error:
                    log.error(f"❌ JavaScript injection also failed: {js_error}")
                    return False
            
            # Wait a moment for the code to be processed
            time.sleep(1)
            
            # Try to find and click verify button with multiple selectors
            verify_selectors = [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "button:contains('Verify')"),
                (By.CSS_SELECTOR, "button:contains('Submit')"),
                (By.XPATH, "//button[contains(text(), 'Verify')]"),
                (By.XPATH, "//button[contains(text(), 'Submit')]"),
                (By.XPATH, "//button[@type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']")
            ]
            
            verify_button = None
            for selector_type, selector_value in verify_selectors:
                try:
                    log.debug(f"🔍 Trying verify button selector: {selector_type} = {selector_value}")
                    verify_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    log.info(f"✅ Found verify button with selector: {selector_type} = {selector_value}")
                    break
                except Exception as e:
                    log.debug(f"❌ Verify button selector failed: {selector_type} = {selector_value}")
                    continue
            
            if verify_button:
                log.info("🔑 Clicking verify button...")
                verify_button.click()
            else:
                log.warning("⚠️ Could not find verify button, trying Enter key...")
                # Try pressing Enter key
                from selenium.webdriver.common.keys import Keys
                totp_field.send_keys(Keys.RETURN)
            
            # Wait for verification to complete
            log.info("⏳ Waiting for verification to complete...")
            time.sleep(5)
            
            # Check if we're redirected to a successful page
            current_url = self.driver.current_url
            log.info(f"🔍 Current URL after TOTP: {current_url}")
            
            if "feed" in current_url.lower() or "mynetwork" in current_url.lower():
                log.info("✅ TOTP verification successful!")
                return True
            else:
                log.warning("⚠️ TOTP verification may have failed - not redirected to expected page")
                return True  # Still return True as the code was submitted
            
        except Exception as e:
            log.error(f"❌ Error handling TOTP challenge: {e}")
            log.debug(f"❌ TOTP exception details: {type(e).__name__}: {str(e)}")
            return False
    
    def _extract_cookies(self) -> Optional[RequestsCookieJar]:
        """
        Extract cookies from the browser session
        
        Returns:
            Optional[RequestsCookieJar]: Cookie jar with LinkedIn cookies
        """
        try:
            cookie_jar = RequestsCookieJar()
            
            # Get all cookies from the browser
            selenium_cookies = self.driver.get_cookies()
            
            # Convert Selenium cookies to RequestsCookieJar
            for cookie in selenium_cookies:
                cookie_jar.set(
                    cookie['name'],
                    cookie['value'],
                    domain=cookie.get('domain', ''),
                    path=cookie.get('path', '/')
                )
            
            # Verify we have the essential cookies
            essential_cookies = ['li_at', 'JSESSIONID']
            missing_cookies = [cookie for cookie in essential_cookies if cookie not in [c.name for c in cookie_jar]]
            
            if missing_cookies:
                log.warning(f"⚠️ Missing essential cookies: {missing_cookies}")
                return None
            
            log.info(f"🍪 Extracted {len(selenium_cookies)} cookies")
            return cookie_jar
            
        except Exception as e:
            log.error(f"❌ Error extracting cookies: {e}")
            return None
    
    def get_cookies_from_credentials(self, username: str, password: str, totp_secret: str = None) -> Optional[RequestsCookieJar]:
        """
        Convenience method to get cookies from credentials
        
        Args:
            username (str): LinkedIn username/email
            password (str): LinkedIn password
            totp_secret (str, optional): TOTP secret for 2FA
            
        Returns:
            Optional[RequestsCookieJar]: Cookie jar with LinkedIn cookies
        """
        success, message, cookies = self.authenticate_and_get_cookies(username, password, totp_secret)
        
        if success:
            return cookies
        else:
            log.error(f"❌ Failed to get cookies: {message}")
            return None 