from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class LinkedInAuthRequest(BaseModel):
    """Request model for LinkedIn authentication"""
    public_id: str = Field(..., description="LinkedIn public profile ID")
    use_cookies: bool = Field(True, description="Use cookie-based authentication if available")

class LinkedInProfileResponse(BaseModel):
    """Response model for LinkedIn profile data"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Profile data if successful")
    error: Optional[str] = Field(None, description="Error message if failed")

class ResumeDataResponse(BaseModel):
    """Response model for transformed resume data"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Resume data if successful")
    error: Optional[str] = Field(None, description="Error message if failed")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field("1.0.0", description="Service version") 