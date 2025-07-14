from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from datetime import datetime
from typing import Optional

from models import (
    LinkedInAuthRequest, LinkedInProfileResponse, 
    ResumeDataResponse, HealthResponse
)
from config import SERVICE_NAME, SERVICE_VERSION, SERVICE_PORT, validate_environment, get_required_env_var
from linkedin_client import LinkedInClient
from resume_transformer import ResumeTransformer

# Initialize FastAPI app
app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    description="LinkedIn profile data fetching and transformation service"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
import dotenv
dotenv.load_dotenv()

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("linkedin_service.log")
    ]
)
log = logging.getLogger(__name__)

# Set all loggers to DEBUG level
logging.getLogger("linkedin_client").setLevel(logging.DEBUG)
logging.getLogger("resume_transformer").setLevel(logging.DEBUG)
logging.getLogger("dynamic_cookie_generator").setLevel(logging.DEBUG)
logging.getLogger("cookie_refresher").setLevel(logging.DEBUG)
logging.getLogger("linkedin_api").setLevel(logging.DEBUG)
logging.getLogger("requests").setLevel(logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.DEBUG)

# Global instances
linkedin_client = LinkedInClient()
resume_transformer = ResumeTransformer()

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    log.info(f"🚀 Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    
    # Validate environment variables
    if not validate_environment():
        log.error("❌ Environment validation failed")
        raise RuntimeError("Missing required environment variables")
    
    log.info("✅ Environment validation passed")

@app.get("/", response_model=dict)
def read_root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "fetch_profile": "/fetch-profile",
            "transform_resume": "/transform-resume",
            "full_pipeline": "/full-pipeline"
        }
    }

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version=SERVICE_VERSION
    )

@app.post("/fetch-profile", response_model=LinkedInProfileResponse)
async def fetch_linkedin_profile(request: LinkedInAuthRequest):
    """
    Fetch LinkedIn profile data
    
    Args:
        request: LinkedIn authentication request with public_id
        
    Returns:
        LinkedInProfileResponse: Profile data or error message
    """
    try:
        log.info(f"📄 Fetching LinkedIn profile for: {request.public_id}")
        
        # Debug: Check environment variables
        totp_secret = os.getenv("LI_TOTP_SECRET", "").strip()
        user = os.getenv("LI_USER", "").strip()
        log.info(f"🔍 Debug - TOTP secret provided: {'Yes' if totp_secret else 'No'}")
        log.info(f"🔍 Debug - Username provided: {'Yes' if user else 'No'}")
        log.info(f"🔍 Debug - Using cookies: {request.use_cookies}")
        
        # Authenticate with LinkedIn
        auth_success, auth_error = linkedin_client.authenticate(use_cookies=request.use_cookies)
        
        if not auth_success:
            return LinkedInProfileResponse(
                success=False,
                message="LinkedIn authentication failed",
                error=auth_error
            )
        
        # Fetch profile data
        profile_data = linkedin_client.fetch_profile_data(request.public_id)
        
        if not profile_data:
            return LinkedInProfileResponse(
                success=False,
                message="Failed to fetch profile data",
                error="Profile data is empty or null"
            )
        
        log.info("✅ LinkedIn profile fetched successfully")
        
        return LinkedInProfileResponse(
            success=True,
            message="LinkedIn profile fetched successfully",
            data=profile_data
        )
        
    except Exception as e:
        log.error(f"❌ Error fetching LinkedIn profile: {e}")
        return LinkedInProfileResponse(
            success=False,
            message="Failed to fetch LinkedIn profile",
            error=str(e)
        )

@app.post("/transform-resume", response_model=ResumeDataResponse)
async def transform_to_resume(profile_data: dict):
    """
    Transform LinkedIn profile data to JSON-Resume format
    
    Args:
        profile_data: Raw LinkedIn profile data
        
    Returns:
        ResumeDataResponse: Transformed resume data or error message
    """
    try:
        log.info("🔄 Transforming LinkedIn data to JSON-Resume format")
        
        # Transform the data
        resume_data = resume_transformer.transform_linkedin_to_resume(profile_data)
        
        log.info("✅ LinkedIn data transformed successfully")
        
        return ResumeDataResponse(
            success=True,
            message="LinkedIn data transformed to JSON-Resume format",
            data=resume_data
        )
        
    except Exception as e:
        log.error(f"❌ Error transforming LinkedIn data: {e}")
        return ResumeDataResponse(
            success=False,
            message="Failed to transform LinkedIn data",
            error=str(e)
        )

@app.post("/full-pipeline", response_model=ResumeDataResponse)
async def full_linkedin_pipeline(request: LinkedInAuthRequest):
    """
    Complete LinkedIn pipeline: fetch profile and transform to resume format
    
    Args:
        request: LinkedIn authentication request with public_id
        
    Returns:
        ResumeDataResponse: Transformed resume data or error message
    """
    try:
        log.info(f"🚀 Starting full LinkedIn pipeline for: {request.public_id}")
        
        # Step 1: Fetch LinkedIn profile
        profile_response = await fetch_linkedin_profile(request)
        
        if not profile_response.success:
            return ResumeDataResponse(
                success=False,
                message="Failed to fetch LinkedIn profile",
                error=profile_response.error
            )
        
        # Step 2: Transform to resume format
        resume_response = await transform_to_resume(profile_response.data)
        
        if not resume_response.success:
            return ResumeDataResponse(
                success=False,
                message="Failed to transform LinkedIn data",
                error=resume_response.error
            )
        
        log.info("✅ Full LinkedIn pipeline completed successfully")
        
        return resume_response
        
    except Exception as e:
        log.error(f"❌ Error in full LinkedIn pipeline: {e}")
        return ResumeDataResponse(
            success=False,
            message="Failed to complete LinkedIn pipeline",
            error=str(e)
        )

@app.get("/test-totp", response_model=dict)
def test_totp():
    """Test TOTP functionality"""
    try:
        totp_secret = os.getenv("LI_TOTP_SECRET", "").strip()
        user = os.getenv("LI_USER", "").strip()
        
        return {
            "totp_secret_provided": bool(totp_secret),
            "user_provided": bool(user),
            "totp_secret_length": len(totp_secret) if totp_secret else 0,
            "linkedin_client_type": type(linkedin_client).__name__,
            "message": "TOTP test endpoint working"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "TOTP test failed"
        }

@app.get("/test-dynamic-cookies", response_model=dict)
def test_dynamic_cookies():
    """Test dynamic cookie generation functionality"""
    try:
        user = os.getenv("LI_USER", "").strip()
        pwd = os.getenv("LI_PASS", "").strip()
        totp_secret = os.getenv("LI_TOTP_SECRET", "").strip()
        
        return {
            "user_provided": bool(user),
            "password_provided": bool(pwd),
            "totp_secret_provided": bool(totp_secret),
            "message": "Dynamic cookie generation endpoint available"
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Dynamic cookie test failed"
        }

@app.post("/generate-dynamic-cookies", response_model=dict)
async def generate_dynamic_cookies():
    """Generate dynamic cookies using browser automation"""
    try:
        from dynamic_cookie_generator import DynamicCookieGenerator
        
        user = os.getenv("LI_USER", "").strip()
        pwd = os.getenv("LI_PASS", "").strip()
        totp_secret = os.getenv("LI_TOTP_SECRET", "").strip()
        
        if not user or not pwd:
            return {
                "success": False,
                "message": "Username and password required for dynamic cookie generation",
                "error": "Missing credentials"
            }
        
        log.info("🚀 Starting dynamic cookie generation via API...")
        
        # Create dynamic cookie generator
        cookie_generator = DynamicCookieGenerator(headless=True)
        
        # Generate cookies
        success, message, cookies = cookie_generator.authenticate_and_get_cookies(
            username=user,
            password=pwd,
            totp_secret=totp_secret if totp_secret else None
        )
        
        if success and cookies:
            # Extract essential cookies
            li_at = None
            jsessionid = None
            
            for cookie in cookies:
                if cookie.name == 'li_at':
                    li_at = cookie.value
                elif cookie.name == 'JSESSIONID':
                    jsessionid = cookie.value
            
            return {
                "success": True,
                "message": "Dynamic cookies generated successfully",
                "cookies": {
                    "li_at": li_at,
                    "jsessionid": jsessionid,
                    "total_cookies": len(cookies)
                }
            }
        else:
            return {
                "success": False,
                "message": "Failed to generate dynamic cookies",
                "error": message
            }
            
    except Exception as e:
        log.error(f"❌ Error in dynamic cookie generation: {e}")
        return {
            "success": False,
            "message": "Dynamic cookie generation failed",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level="info"
    ) 