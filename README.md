# Resume Generation Pipeline

An intelligent, automated resume generation system that transforms LinkedIn profile data into professional, AI-enhanced resumes with validated URLs and multiple output formats.

## 🎯 Main Objective

**Problem**: Manually creating and maintaining professional resumes is time-consuming and often results in inconsistent formatting, outdated information, and missed opportunities to highlight relevant skills and achievements.

**Solution**: This pipeline automatically fetches your LinkedIn profile, enhances it with AI-powered content optimization, validates all URLs, and generates professional HTML and PDF resumes with consistent styling.

## 🔧 Key Technologies & Their Roles

### Core Technologies
- **LinkedIn API** (`linkedin-api`) - Fetches comprehensive profile data including work experience, education, skills, and contact information
- **OpenAI API** (`openai`) - AI-powered content enhancement including skill filtering, experience extraction, and technical highlighting
- **Google Knowledge Graph API** - Discovers official company and school website URLs for professional linking
- **GitHub API** (`PyGithub`) - Processes GitHub repositories to extract project information from README files
- **Playwright** - Converts HTML resumes to high-quality PDF documents with perfect formatting

### Supporting Technologies
- **httpx** - Async HTTP client for bulk URL validation and API calls
- **python-dotenv** - Environment variable management for secure credential handling
- **requests** - HTTP requests for entity search and API integrations

## 🏗️ Architecture Structure

The project follows a **6-step modular pipeline** where each step is a dedicated, reusable module:

```
LinkedIn Data → Transform → AI Enhance → Validate URLs → Generate HTML → Generate PDF
     ↓              ↓           ↓            ↓              ↓              ↓
linkedin_fetcher  linkedin_   openai_     url_validator  html_generator pdf_generator
                  transformer processor
```

### Pipeline Steps
1. **LinkedIn Fetcher** - Authenticates and fetches comprehensive profile data
2. **Data Transformer** - Converts to JSON-Resume format with async URL lookups
3. **AI Processor** - Enhances content with skill filtering, project extraction, and tech highlighting
4. **URL Validator** - Validates all URLs and removes broken links
5. **HTML Generator** - Creates responsive, professional HTML with configurable styling
6. **PDF Generator** - Converts HTML to print-ready PDF using Playwright

### Key Features
- **Async Processing** - Concurrent operations for faster execution
- **Multi-Layer URL Discovery** - Google KG → LinkedIn → Profile fallback
- **AI-Powered Enhancement** - Smart content optimization with customizable prompts
- **Configurable Styling** - Centralized configuration for fonts, colors, and layout
- **Error Resilience** - Graceful fallbacks and comprehensive error handling

## 🚀 How to Use

### Prerequisites
```bash
pip install -r requirements.txt
playwright install chromium
```

### Environment Setup
Create a `.env` file with your credentials:
```env
# LinkedIn Authentication (Cookie method preferred)
LI_AT=your_li_at_cookie
LI_JSESSIONID=your_jsessionid
LI_PID=your_public_profile_id

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# GitHub API (optional)
PAT_GITHUB=your_github_personal_access_token

# Google Knowledge Graph API (optional)
GOOGLE_KG_API=your_google_kg_api_key
```

### Quick Start
```bash
# Complete pipeline: LinkedIn → Transform → AI → Validate → HTML → PDF
python scripts/pipeline.py

# Skip LinkedIn fetch, use existing data
python scripts/pipeline.py --skip-linkedin

# Skip AI processing
python scripts/pipeline.py --skip-openai

# Generate only HTML and PDF from existing JSON
python scripts/pipeline.py --skip-linkedin --skip-openai --skip-github
```

### Individual Steps
```bash
# Step 1: Fetch LinkedIn data
python scripts/linkedin_fetcher.py

# Step 2: Transform to JSON-Resume format
python scripts/linkedin_transformer.py

# Step 3: AI enhancement
python scripts/openai_processor.py

# Step 4: Validate URLs
python scripts/url_validator.py

# Step 5: Generate HTML
python scripts/html_generator.py

# Step 6: Generate PDF
python scripts/pdf_generator.py
```

### Output Files
- `assets/index.html` - Professional HTML resume
- `assets/styles.css` - Generated CSS with config values
- `assets/Aviroop Mitra Resume.pdf` - Print-ready PDF resume
- `data/resume.json` - JSON-Resume formatted data

### Configuration
All styling and behavior is controlled through `scripts/config.py`:
- Font family and sizes
- Color scheme and spacing
- AI model settings
- Layout preferences

## 📁 Project Structure
```
CVPipeline/
├── scripts/           # Core pipeline modules
├── assets/           # Generated HTML, CSS, and PDF files
├── data/             # LinkedIn raw data and JSON resume
├── prompts/          # AI prompt templates and examples
└── requirements.txt  # Python dependencies
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the modular architecture
4. Test with the pipeline
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License. 