# LinkedIn Service

A FastAPI microservice for fetching and processing LinkedIn profile data.

## Features

- **LinkedIn Profile Fetching**: Retrieve complete LinkedIn profiles using public IDs
- **Data Transformation**: Convert LinkedIn data to structured resume format
- **Multiple Authentication Methods**: Support for static cookies, dynamic cookie generation, and credential-based authentication
- **Cookie Management**: Automatic cookie validation and refresh capabilities
- **TOTP Support**: Two-factor authentication support for enhanced security
- **Error Handling**: Comprehensive error handling and logging

## Authentication Methods

### 1. Static Cookies (Recommended)
Use existing LinkedIn session cookies for authentication:

```bash
LI_AT=your_li_at_cookie_value
LI_JSESSIONID=your_jsessionid_cookie_value
```

### 2. Dynamic Cookie Generation
Automatically generate fresh cookies using browser automation:

```bash
LI_USER=your_linkedin_email
LI_PASS=your_linkedin_password
LI_TOTP_SECRET=your_totp_secret  # Optional, for 2FA
```

**Features:**
- Browser automation using Selenium
- Automatic TOTP code generation for 2FA
- Fallback to cookie refresh if browser automation fails
- Headless mode support

### 3. Credential-based Authentication
Direct username/password authentication (may require 2FA):

```bash
LI_USER=your_linkedin_email
LI_PASS=your_linkedin_password
LI_TOTP_SECRET=your_totp_secret  # Required for 2FA
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```bash
# Static cookies (preferred)
LI_AT=your_li_at_cookie_value
LI_JSESSIONID=your_jsessionid_cookie_value

# OR Dynamic cookie generation
LI_USER=your_linkedin_email
LI_PASS=your_linkedin_password
LI_TOTP_SECRET=your_totp_secret  # Optional

# Service configuration
LINKEDIN_TIMEOUT=30
LINKEDIN_MAX_RETRIES=3
```

3. Run the service:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Profile Fetching

#### `POST /fetch-profile`
Fetch a LinkedIn profile by public ID.

**Request:**
```json
{
    "public_id": "avi-mitra",
    "use_cookies": true
}
```

**Response:**
```json
{
    "success": true,
    "message": "LinkedIn profile fetched successfully",
    "data": {
        "firstName": "Avi",
        "lastName": "Mitra",
        "headline": "Strategy & Analytics Manager",
        "summary": "...",
        "experience": [...],
        "education": [...],
        "skills": [...]
    }
}
```

### Data Transformation

#### `POST /transform-profile`
Transform LinkedIn profile data to resume format.

**Request:**
```json
{
    "profile_data": {...}
}
```

**Response:**
```json
{
    "success": true,
    "message": "Profile transformed successfully",
    "data": {
        "personal_info": {...},
        "experience": [...],
        "education": [...],
        "skills": [...]
    }
}
```

### Pipeline Operations

#### `POST /run-pipeline`
Run the complete LinkedIn pipeline (fetch + transform).

**Request:**
```json
{
    "public_id": "avi-mitra",
    "use_cookies": true
}
```

### Cookie Management

#### `GET /test-dynamic-cookies`
Test dynamic cookie generation configuration.

**Response:**
```json
{
    "user_provided": true,
    "password_provided": true,
    "totp_secret_provided": true,
    "message": "Dynamic cookie generation endpoint available"
}
```

#### `POST /generate-dynamic-cookies`
Generate fresh cookies using browser automation.

**Response:**
```json
{
    "success": true,
    "message": "Dynamic cookies generated successfully",
    "cookies": {
        "li_at": "generated_li_at_value",
        "jsessionid": "generated_jsessionid_value",
        "total_cookies": 15
    }
}
```

## Authentication Flow

1. **Static Cookies**: If `LI_AT` and `LI_JSESSIONID` are provided, use them directly
2. **Dynamic Generation**: If static cookies are not available, attempt browser automation
3. **Cookie Refresh**: If dynamic generation fails, try to refresh existing cookies
4. **Credential Fallback**: As a last resort, use direct credential authentication

## Error Handling

The service provides detailed error messages for various scenarios:

- **Authentication Errors**: Invalid credentials, expired cookies, 2FA challenges
- **Network Errors**: Timeout, connection issues
- **Data Errors**: Invalid profile IDs, missing data
- **Browser Errors**: Chrome not found, automation failures

## Development

### Running Tests
```bash
# Test cookie refresh functionality
python test_cookie_refresh.py

# Test dynamic cookie generation
python test_dynamic_cookies.py
```

### Docker Support
```bash
# Build image
docker build -t linkedin-service .

# Run container
docker run -p 8000:8000 --env-file .env linkedin-service
```

## Dependencies

- **FastAPI**: Web framework
- **linkedin-api**: LinkedIn API client
- **selenium**: Browser automation for dynamic cookies
- **webdriver-manager**: Chrome driver management
- **pyotp**: TOTP code generation for 2FA
- **requests**: HTTP client
- **pydantic**: Data validation

## Security Notes

- Store sensitive credentials in environment variables
- Use TOTP secrets for enhanced security
- Regularly rotate cookies
- Monitor authentication logs
- Consider using cookie refresh for long-running services 