# Resume Generation Pipeline

An intelligent, automated resume generation system that fetches LinkedIn profile data, enriches it with AI enhancement and entity search, validates all URLs, and generates professional HTML and PDF resumes with configurable styling.

## 🏗️ Architecture

The project uses a **6-step modular pipeline** architecture where each step is a dedicated, reusable module with comprehensive logging and error handling:

### Pipeline Steps

1. **LinkedIn Data Fetching** (`linkedin_fetcher.py`) - Authenticate and fetch comprehensive profile data
2. **Data Transformation** (`linkedin_transformer.py`) - Convert to JSON-Resume format with async company/school URL lookups
3. **AI Enhancement** (`openai_processor.py`) - Intelligent skill filtering, experience extraction, and tech highlighting  
4. **URL Validation** (`url_validator.py`) - Validate all URLs and remove broken links
5. **HTML Generation** (`html_generator.py`) - Create responsive, professional HTML with configurable styling
6. **PDF Generation** (`pdf_generator.py`) - Convert HTML to print-ready PDF using Playwright

### Core Modules

- **`pipeline.py`** - Unified orchestration script that runs the complete 6-step pipeline
- **`config.py`** - Centralized configuration for styling, fonts, AI models, and behavior settings
- **`entity_search.py`** - Google Knowledge Graph integration for company/school URL discovery
- **`url_validator.py`** - Async URL validation with bulk processing and timeout handling
- **`linkedin_transformer.py`** - Async transformation with multiple fallback mechanisms
- **`openai_processor.py`** - AI-powered content enhancement with async processing

## 🚀 Quick Start

### Complete Pipeline (Recommended)

```bash
# Full 6-step pipeline: LinkedIn → Transform → AI → Validate → HTML → PDF
python scripts/pipeline.py

# Skip LinkedIn fetch, use existing data
python scripts/pipeline.py --skip-linkedin

# Skip AI processing, generate from raw data
python scripts/pipeline.py --skip-openai

# Generate only HTML and PDF from existing JSON
python scripts/pipeline.py --skip-linkedin --skip-openai

# Verbose logging for debugging
python scripts/pipeline.py --verbose
```

### Individual Steps

```bash
# Step 1: Fetch LinkedIn data
python scripts/linkedin_fetcher.py

# Step 2: Transform to JSON-Resume format (includes async URL lookups)
python scripts/linkedin_transformer.py

# Step 3: AI enhancement with async processing
python scripts/openai_processor.py

# Step 4: Validate all URLs
python scripts/url_validator.py

# Step 5: Generate HTML
python scripts/html_generator.py

# Step 6: Generate PDF
python scripts/pdf_generator.py
```

## 📋 Prerequisites

### Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

**Required packages:**
- `linkedin-api` - LinkedIn profile data fetching
- `python-dotenv` - Environment variable management
- `pyotp` - Two-factor authentication support
- `openai` - AI-powered content enhancement
- `playwright` - HTML to PDF conversion
- `httpx` - Async HTTP client for URL validation
- `requests` - HTTP requests for entity search

### Environment Variables

Create a `.env` file with your credentials:

```env
# LinkedIn Authentication (Cookie method preferred)
LI_AT=your_li_at_cookie         # Most reliable for automation
LI_JSESSIONID=your_jsessionid   # Required with LI_AT
LI_PID=your_public_profile_id   # Your LinkedIn public profile ID

# LinkedIn Fallback (Username/Password)
LI_USER=your_linkedin_email     # Fallback method
LI_PASS=your_linkedin_password  # May trigger 2FA
LI_TOTP_SECRET=your_2fa_secret  # Optional for 2FA

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Google Knowledge Graph API (for company/school lookups)
GOOGLE_KG_API=your_google_kg_api_key
```

**Authentication Methods:**
- **Preferred**: Cookie-based (`LI_AT` + `LI_JSESSIONID`) - More reliable for automation
- **Fallback**: Username/password - May require 2FA verification

## 🎨 Configuration & Styling

All styling and behavior is controlled through `scripts/config.py`:

### Font & Typography
```python
FONT_FAMILY_NAME = "HelveticaNeue"           # Custom font family
HTML_FONT_SIZE_BASE = "13px"                  # Body text
HTML_FONT_SIZE_NAME = "20px"                  # Name header
HTML_FONT_SIZE_SECTION = "15px"               # Section headings
HTML_LINE_HEIGHT = "1.3"                     # Line spacing
```

### Layout & Spacing
```python
HTML_BODY_MARGIN_LEFT = "35px"               # Left page margin
HTML_SECTION_MARGIN_TOP = "10px"             # Gap before sections
HTML_DATE_PADDING_LEFT = "10px"              # Date indentation
HTML_CONTAINER_PADDING = "5px"               # Content padding
```

### Color Scheme
```python
HTML_COLOR_PRIMARY = "#2c3e50"               # Headers and main text
HTML_COLOR_SECONDARY = "#666"                # Secondary text
HTML_COLOR_LINK = "#0066cc"                  # Links and accent color
HTML_COLOR_ACCENT = "#7f8c8d"                # Dates and metadata
```

### AI Processing
```python
OPENAI_MODEL = "o4-mini"                     # AI model for enhancement
OPENAI_REASONING_EFFORT = "high"             # Processing thoroughness
POINT_WORD_THRESHOLD = 100                   # Trigger for bullet extraction
```

## 📁 Project Structure

```
my-resume/
├── scripts/
│   ├── config.py                    # 🎛️ Centralized configuration
│   ├── pipeline.py                  # 🎯 6-step pipeline orchestrator
│   ├── linkedin_fetcher.py          # 🔗 LinkedIn authentication & data fetching
│   ├── linkedin_transformer.py      # 🔄 Async JSON-Resume transformation
│   ├── entity_search.py             # 🌐 Google Knowledge Graph integration
│   ├── openai_processor.py          # 🤖 AI-powered content enhancement
│   ├── url_validator.py             # ✅ Async URL validation system
│   ├── html_generator.py            # 🌐 HTML generation with external CSS
│   └── pdf_generator.py             # 📄 HTML-to-PDF conversion
├── assets/
│   ├── fonts/                       # HelveticaNeue font family collection
│   ├── index.html                   # Generated HTML resume
│   ├── styles.css                   # Generated CSS with config values
│   └── Aviroop Mitra Resume.pdf     # Generated PDF resume
├── data/
│   ├── linkedin_raw.json            # Raw LinkedIn profile data
│   └── resume.json                  # JSON-Resume formatted data
├── prompts/
│   ├── extract_points.txt           # AI bullet point extraction prompt
│   ├── filter_skills.txt            # AI skill filtering and categorization
│   ├── experience_extraction.txt    # AI experience project extraction
│   ├── experience_examples.json     # Examples for experience extraction
│   ├── highlight_tech.txt           # AI tech highlighting prompt
│   └── highlight_examples.json      # Examples for tech highlighting
├── requirements.txt                 # Python dependencies
└── .github/workflows/
    └── update-resume.yml            # Automated weekly updates
```

## 🚀 Enhanced Features

### Multi-Layer URL Discovery System
- **Google Knowledge Graph**: Primary source for official company/school websites
- **LinkedIn Direct Search**: Fallback using LinkedIn's `get_company`/`get_school` functions
- **LinkedIn Search Results**: Secondary fallback searching multiple results with name validation
- **Profile URN Fallback**: Extracts URN IDs from experience data for profile-based lookups
- **URL Validation**: Validates all discovered URLs with async HTTP requests and removes broken links

### Async Processing Architecture
- **Concurrent Entity Processing**: Work experiences and education entries processed simultaneously
- **Bulk URL Validation**: All URLs validated concurrently with configurable concurrency limits
- **Synchronous Search Order**: Within each entity, maintains reliable search order: Google KG → LinkedIn direct → LinkedIn search → Profile fallback
- **Exception Handling**: Graceful fallbacks when individual searches fail

### Intelligent Name Matching
- **Fuzzy Matching**: Sophisticated algorithm handling exact matches, suffixes, containment, and word overlap
- **Configurable Similarity**: Adjustable threshold for name matching confidence
- **Multi-Language Support**: Handles various name formats and company name variations

### AI-Powered Content Enhancement
- **Experience Project Extraction**: Converts work experience descriptions into structured project data
- **Tech Skills Highlighting**: Identifies and emphasizes technical skills and quantitative metrics  
- **Smart Skill Filtering**: Removes irrelevant skills and categorizes into logical groups
- **Bullet Point Optimization**: Transforms verbose descriptions into crisp, action-oriented points

## 🤖 AI Enhancement Features

### Advanced Content Processing
- **Project Extraction**: Uses few-shot learning with examples to extract structured project data from experience descriptions
- **Tech Highlighting**: Identifies technical skills, quantitative impacts, and metrics using example-based learning
- **Skill Categorization**: Groups skills into categories like "Programming Languages", "Cloud & DevOps", "Databases", etc.
- **Smart Bullet Points**: Converts long descriptions into 2-6 crisp bullet points with action verbs

### Async AI Processing Pipeline
```python
# Phase 1: Independent operations run concurrently
skills_task = filter_and_categorize_skills_async(skills)
experience_tasks = [extract_experience_projects_async(exp) for exp in experiences]

# Phase 2: Tech highlighting after project extraction
tech_highlight_tasks = [highlight_tech_skills_async(project) for project in projects]

# Phase 3: All results combined efficiently
```

### Customizable AI Prompts
All AI behavior is controlled through editable prompt files with examples:
- `filter_skills.txt` - ReAct-style prompt with tool calling simulation for skill curation
- `experience_extraction.txt` - Project extraction with structured JSON output format
- `experience_examples.json` - Real-world examples for few-shot learning
- `highlight_tech.txt` - Technical skill and metric identification
- `highlight_examples.json` - Examples showing desired highlighting patterns

## 🌐 HTML & PDF Generation

### Professional HTML Output
- **Custom Font Integration**: Full HelveticaNeue font family with @font-face declarations
- **Responsive Design**: Optimized for desktop, mobile, and print media
- **Tech Highlighting**: AI-identified technical terms displayed in italic bold
- **Extracted Projects**: Sub-projects from work experience displayed in nested layout
- **Clean Typography**: Minimal spacing with professional hierarchy

### Advanced PDF Features
- **Playwright Engine**: Browser-based rendering with perfect HTML fidelity
- **Print Optimization**: @media print styles for clean page breaks
- **Font Preservation**: Maintains custom fonts in PDF output
- **Clickable Links**: All URLs remain functional in PDF
- **A4 Layout**: Professional document formatting

### Dynamic Styling System
```python
# Auto-generated CSS with config values
@font-face declarations for HelveticaNeue variants
Responsive breakpoints and mobile optimization
Configurable color scheme and spacing
Print media queries for PDF generation
```

## ⚡ GitHub Actions Automation

Automated weekly resume updates with smart change detection:

```yaml
# Runs every Sunday at 09:00 IST (03:30 UTC)
# Manual trigger available via workflow_dispatch  
# Uses cookie-based authentication for reliability
# Commits changes only if content is updated
```

**Enhanced Workflow Features:**
- **Weekly Schedule**: Automatic updates every Sunday to keep resume current
- **Manual Trigger**: On-demand generation via GitHub Actions UI
- **Smart Commits**: Only commits when actual changes are detected in data/ and assets/
- **Environment Security**: Uses GitHub Secrets for all sensitive credentials
- **Error Handling**: Continues pipeline even if individual steps fail

## 🛠️ Development & Customization

### Pipeline Logging
Professional logging system with appropriate levels:
```python
log.info("✅ LinkedIn data fetched successfully")
log.warning("⚠️ LinkedIn name mismatch for Company XYZ")
log.error("❌ Authentication Error: Invalid credentials")
log.debug("🔍 Checking result 1: Company Name")
```

### Adding Custom Entity Sources
```python
# Extend entity_search.py
def custom_company_search(name: str) -> Tuple[str, str]:
    # Your custom search logic
    return url, entity_id

# Add to search chain in linkedin_transformer.py
```

### URL Validation Configuration
```python
# In url_validator.py
MAX_CONCURRENT_VALIDATIONS = 10    # Concurrent requests
DEFAULT_TIMEOUT = 10.0             # Request timeout
REDIRECT_LIMIT = 5                 # Max redirects to follow
```

### Custom AI Prompts
1. **Edit Prompt Files**: Modify files in `prompts/` directory with your requirements
2. **Add Examples**: Update `*_examples.json` files with domain-specific examples
3. **Test Changes**: Run individual AI processing: `python scripts/openai_processor.py`
4. **Iterate**: Refine prompts based on output quality

## 📊 Pipeline Output Example

```
🚀 Starting Resume Generation Pipeline
📁 Working directory: /path/to/resume
⚙️  Configuration: LinkedIn=Fetch, OpenAI=Process

============================================================
STEP 1/6: FETCH LINKEDIN DATA
============================================================
📝 Authenticate with LinkedIn and fetch profile information
[INFO] 🔐 Authenticating with LinkedIn via cookies...
[INFO] ✅ Authenticated via cookies
[INFO] 📄 Fetching profile...
[INFO] ✅ Profile fetched successfully
✅ LinkedIn data fetched completed successfully

============================================================
STEP 2/6: TRANSFORM DATA  
============================================================
📝 Convert LinkedIn profile data to JSON-Resume format
[INFO] 🚀 Processing 2 work experiences and 3 education entries concurrently...
[INFO] 🔍 Google KG search for company: Neurologic-ai
[INFO] ✅ Found Google KG URL for Neurologic-ai: https://www.linkedin.com/company/neurologicai/
[INFO] ✅ Google KG URL validated for Neurologic-ai
✅ Data transformation completed successfully

============================================================
STEP 3/6: OPENAI ENHANCEMENT
============================================================
📝 Filter skills, categorize, and extract bullet points
[INFO] Processing resume data with OpenAI API (async)...
[INFO] Phase 1: Starting independent OpenAI operations...
[INFO] Filtering 47 skills via OpenAI (async)
[INFO] Phase 2: Processing experience extraction results...
[INFO] Extracting experience projects via OpenAI (async) (1247 chars)
[INFO] Extracted 2 projects from experience
[INFO] Phase 3: Running tech highlighting for extracted projects...
[INFO] Highlighting tech skills via OpenAI (async) (312 chars)
[INFO] Extracted 5 tech highlights
✅ OpenAI enhancement completed successfully

============================================================
STEP 4/6: VALIDATE URLS
============================================================
📝 Check all URLs are accessible and remove broken ones
[INFO] Validating 5 URLs from resume data...
[INFO] Starting bulk URL validation with max 10 concurrent requests
[INFO] ✅ https://www.linkedin.com/company/neurologicai/ - OK (200)
[INFO] ✅ http://www.pwc.com - OK (200)  
[INFO] Validation complete: 5/5 URLs are valid
✅ URL validation completed successfully

============================================================
STEP 5/6: GENERATE HTML
============================================================
📝 Create professional HTML resume with responsive design
[INFO] Generating HTML resume and CSS...
[INFO] CSS file generated → assets/styles.css
[INFO] HTML resume generated → assets/index.html
✅ HTML generation completed successfully

============================================================
STEP 6/6: GENERATE PDF
============================================================
📝 Create PDF resume from HTML using Playwright
[INFO] Generating PDF from HTML with Playwright...
[INFO] PDF generated using Playwright → assets/Aviroop Mitra Resume.pdf
✅ PDF generation completed successfully

============================================================
PIPELINE SUMMARY
============================================================
⏱️  Total time: 62.34 seconds
✅ Steps completed: 6/6
🎉 Resume generation pipeline completed successfully!
📄 HTML saved to: assets/index.html
📄 PDF saved to: assets/Aviroop Mitra Resume.pdf
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** following the modular architecture
4. **Test with pipeline**: `python scripts/pipeline.py --verbose`
5. **Submit a pull request**

### Contribution Guidelines
- Maintain the 6-step modular architecture
- Add configuration options to `config.py` for new features  
- Use proper logging levels (info/warning/error/debug)
- Update prompts and examples for AI behavior changes
- Test async processing and error handling
- Follow existing code style and documentation patterns

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details. 