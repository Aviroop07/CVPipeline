# Resume Generation Pipeline

An automated resume generation system that fetches LinkedIn profile data, transforms it to JSON-Resume format, enhances it with AI processing, and generates a professional PDF resume.

## 🏗️ Architecture

The project is built with a **modular architecture** where each major functionality is separated into dedicated modules:

### Core Modules

- **`linkedin_fetcher.py`** - LinkedIn authentication and profile data fetching
- **`linkedin_transformer.py`** - Transform LinkedIn data to JSON-Resume format
- **`openai_processor.py`** - AI-powered resume enhancement (skill filtering, categorization, ranking)
- **`pdf_generator.py`** - Professional PDF generation using borb library
- **`pipeline.py`** - Unified orchestration script that runs the complete pipeline

## 🚀 Quick Start

### Using the Unified Pipeline (Recommended)

```bash
# Full pipeline: LinkedIn → Transform → OpenAI → PDF
python scripts/pipeline.py

# Skip LinkedIn fetch, use existing data
python scripts/pipeline.py --skip-linkedin

# Skip OpenAI processing
python scripts/pipeline.py --skip-openai

# Only generate PDF from existing JSON
python scripts/pipeline.py --skip-linkedin --skip-openai

# Verbose logging
python scripts/pipeline.py --verbose
```

### Using Individual Modules

```bash
# Step 1: Fetch LinkedIn data
python scripts/linkedin_fetcher.py

# Step 2: Transform to JSON-Resume format
python scripts/linkedin_transformer.py

# Step 3: Enhance with OpenAI
python scripts/openai_processor.py

# Step 4: Generate PDF
python scripts/pdf_generator.py
```

## 📋 Prerequisites

### Dependencies

Install required packages:

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file with your credentials:

```env
# LinkedIn Authentication
LI_USER=your_linkedin_email
LI_PASS=your_linkedin_password
LI_TOTP_SECRET=your_2fa_secret  # Optional
LI_AT=your_li_at_cookie         # Preferred method
LI_JSESSIONID=your_jsessionid   # Preferred method
LI_PID=your_public_profile_id

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
```

**Note**: Cookie-based authentication (`LI_AT` and `LI_JSESSIONID`) is more reliable than username/password, especially in automated environments.

## 🔧 Configuration

All settings are centralized in `scripts/config.py`:

```python
# OpenAI Settings
OPENAI_MODEL = "o4-mini"
OPENAI_REASONING_EFFORT = "high"
OPENAI_TEMPERATURE = 1

# PDF Settings
PDF_FONT_SIZE = 10
PDF_HEADING_FONT_SIZE = 12
PDF_TITLE_FONT_SIZE = 14
PDF_MARGIN_TOP = 30
PDF_MARGIN_BOTTOM = 30
PDF_MARGIN_LEFT = 30
PDF_MARGIN_RIGHT = 30
PDF_SECTION_SPACING = 4

# File Names
RESUME_JSON_FILE = "resume.json"
RESUME_PDF_FILE = "Aviroop_Mitra_Resume.pdf"
LINKEDIN_RAW_FILE = "linkedin_raw.json"
```

## 📁 Project Structure

```
my-resume/
├── scripts/
│   ├── config.py                    # Centralized configuration
│   ├── pipeline.py                  # 🎯 Unified pipeline orchestrator
│   ├── linkedin_fetcher.py          # 🔗 LinkedIn data fetching
│   ├── linkedin_transformer.py      # 🔄 Data transformation
│   ├── openai_processor.py          # 🤖 AI-powered enhancement
│   └── pdf_generator.py             # 📄 PDF generation
├── data/
│   └── linkedin_raw.json            # Raw LinkedIn profile data
├── prompts/
│   ├── categorize_skills.txt        # AI prompt for skill categorization
│   ├── extract_points.txt           # AI prompt for bullet point extraction
│   ├── filter_skills.txt            # AI prompt for skill filtering
│   └── rank_items.txt               # AI prompt for section ranking
├── resume.json                      # JSON-Resume formatted data
├── Aviroop_Mitra_Resume.pdf         # Final PDF output
└── requirements.txt                 # Python dependencies
```

## 🤖 AI Enhancement Features

The OpenAI processor provides intelligent resume enhancement:

### Skill Processing
- **Filtering**: Removes irrelevant or duplicate skills
- **Categorization**: Groups skills into logical categories (Programming Languages, Frameworks, Cloud Technologies, etc.)
- **Ranking**: Orders skills by relevance and importance

### Content Enhancement
- **Bullet Point Extraction**: Converts long descriptions into concise bullet points
- **Section Ranking**: Reorders work experience, projects, and achievements by relevance
- **Date Formatting**: Standardizes date ranges (e.g., "Jan, 2020 – Present")

### Customizable Prompts
All AI prompts are stored in the `prompts/` directory and can be customized:
- `filter_skills.txt` - Controls which skills to keep
- `categorize_skills.txt` - Defines skill categorization logic
- `rank_items.txt` - Sets ranking criteria for sections
- `extract_points.txt` - Guides bullet point extraction

## 📄 PDF Generation

The PDF generator creates professional resumes with:

- **Times New Roman** font family for professional appearance
- **Clickable hyperlinks** for LinkedIn, company, and school URLs
- **Optimized spacing** with configurable margins and section gaps
- **Italic dates** and **bold headers** for better visual hierarchy
- **Clean layout** with consistent formatting and ink blue hyperlinks
- **Unicode handling** for special characters
- **Compact content** with continuous paragraphs instead of bullet points

## 🔄 GitHub Actions Workflow

The project includes automated resume updates via GitHub Actions:

```yaml
# .github/workflows/update-resume.yml
# Runs daily at 09:00 IST or manually via workflow_dispatch
# Uses the unified pipeline.py for streamlined execution
```

## 🛠️ Development

### Adding New Modules

To add new functionality:

1. Create a new module in `scripts/`
2. Define clear functions with proper docstrings
3. Add configuration constants to `config.py`
4. Update `pipeline.py` to include the new step
5. Follow the established modular pattern

### Testing Individual Components

Each module can be imported and tested independently:

```python
from scripts.linkedin_fetcher import fetch_linkedin_data
from scripts.openai_processor import filter_skills_with_openai
from scripts.pdf_generator import create_pdf_document
```

## 📊 Pipeline Output

The pipeline provides detailed logging and progress tracking:

```
🚀 Starting Resume Generation Pipeline
📁 Working directory: /path/to/resume
⚙️  Configuration: LinkedIn=Fetch, OpenAI=Process

============================================================
STEP 1/4: FETCH LINKEDIN DATA
============================================================
📝 Authenticate with LinkedIn and fetch profile information
✅ LinkedIn data fetched completed successfully

============================================================
STEP 2/4: TRANSFORM DATA  
============================================================
📝 Convert LinkedIn profile data to JSON-Resume format
✅ Data transformation completed successfully

============================================================
STEP 3/4: OPENAI ENHANCEMENT
============================================================
📝 Filter skills, categorize, rank sections, and extract bullet points
[INFO] Filtering 56 skills via OpenAI
[INFO] Kept 24/56 skills after filtering
[INFO] Categorizing 24 skills via OpenAI
[INFO] Received 7 skill categories
✅ OpenAI enhancement completed successfully

============================================================
STEP 4/4: GENERATE PDF
============================================================
📝 Create professional PDF resume using borb library
✅ PDF generation completed successfully

============================================================
PIPELINE SUMMARY
============================================================
⏱️  Total time: 201.28 seconds
✅ Steps completed: 4/4
🎉 Resume generation pipeline completed successfully!
📄 PDF saved to: Aviroop_Mitra_Resume.pdf
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the modular architecture
4. Test with the pipeline script
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details. 