# Resume Generation Pipeline

An intelligent, automated resume generation system that fetches LinkedIn profile data, transforms it using AI enhancement, and generates professional HTML and PDF resumes with configurable styling.

## 🏗️ Architecture

The project uses a **5-step modular pipeline** architecture where each step is a dedicated, reusable module:

### Pipeline Steps

1. **LinkedIn Data Fetching** (`linkedin_fetcher.py`) - Authenticate and fetch comprehensive profile data
2. **Data Transformation** (`linkedin_transformer.py`) - Convert to JSON-Resume format with company/school lookups
3. **AI Enhancement** (`openai_processor.py`) - Intelligent skill filtering, categorization, and content optimization
4. **HTML Generation** (`html_generator.py`) - Create responsive, professional HTML with configurable styling
5. **PDF Generation** (`pdf_generator.py`) - Convert HTML to print-ready PDF using WeasyPrint

### Core Modules

- **`pipeline.py`** - Unified orchestration script that runs the complete 5-step pipeline
- **`config.py`** - Centralized configuration for all styling, fonts, spacing, and behavior settings
- **`html_generator.py`** - Generates HTML resumes with external CSS and configurable design
- **`pdf_generator.py`** - Creates PDFs from HTML using WeasyPrint with margin optimization

## 🚀 Quick Start

### Complete Pipeline (Recommended)

```bash
# Full 5-step pipeline: LinkedIn → Transform → AI → HTML → PDF
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

# Step 2: Transform to JSON-Resume format
python scripts/linkedin_transformer.py

# Step 3: AI enhancement
python scripts/openai_processor.py

# Step 4: Generate HTML
python scripts/html_generator.py

# Step 5: Generate PDF
python scripts/pdf_generator.py
```

## 📋 Prerequisites

### Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `linkedin-api` - LinkedIn profile data fetching
- `python-dotenv` - Environment variable management
- `pyotp` - Two-factor authentication support
- `openai` - AI-powered content enhancement
- `weasyprint` - HTML to PDF conversion

### Environment Variables

Create a `.env` file with your credentials:

```env
# LinkedIn Authentication (Cookie method preferred)
LI_AT=your_li_at_cookie         # Most reliable
LI_JSESSIONID=your_jsessionid   # Required with LI_AT
LI_PID=your_public_profile_id   # Your LinkedIn public profile ID

# LinkedIn Fallback (Username/Password)
LI_USER=your_linkedin_email     # Fallback method
LI_PASS=your_linkedin_password  # May trigger 2FA
LI_TOTP_SECRET=your_2fa_secret  # Optional for 2FA

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
```

**Authentication Methods:**
- **Preferred**: Cookie-based (`LI_AT` + `LI_JSESSIONID`) - More reliable for automation
- **Fallback**: Username/password - May require 2FA verification

## 🎨 Configuration & Styling

All styling and behavior is controlled through `scripts/config.py`:

### Font & Typography
```python
HTML_FONT_FAMILY = "'Times New Roman', Times, serif"
HTML_FONT_SIZE_BASE = "13px"        # Body text
HTML_FONT_SIZE_NAME = "20px"        # Name header
HTML_FONT_SIZE_SECTION = "15px"     # Section headings
HTML_FONT_SIZE_CONTACT = "13px"     # Contact information
HTML_LINE_HEIGHT = "1.3"           # Line spacing
```

### Layout & Spacing
```python
HTML_BODY_MARGIN_LEFT = "35px"      # Left page margin
HTML_SECTION_MARGIN_TOP = "10px"    # Gap before sections
HTML_DATE_PADDING_LEFT = "10px"     # Date indentation
HTML_CONTAINER_PADDING = "5px"      # Content padding
```

### Color Scheme
```python
HTML_COLOR_PRIMARY = "#2c3e50"      # Headers and main text
HTML_COLOR_SECONDARY = "#666"       # Secondary text
HTML_COLOR_LINK = "#0066cc"         # Links and accent color
HTML_COLOR_ACCENT = "#7f8c8d"       # Dates and metadata
```

### AI Processing
```python
OPENAI_MODEL = "o4-mini"            # AI model for enhancement
OPENAI_REASONING_EFFORT = "high"    # Processing thoroughness
POINT_WORD_THRESHOLD = 100          # Trigger for bullet extraction
```

## 📁 Project Structure

```
my-resume/
├── scripts/
│   ├── config.py                    # 🎛️ Centralized configuration
│   ├── pipeline.py                  # 🎯 5-step pipeline orchestrator
│   ├── linkedin_fetcher.py          # 🔗 LinkedIn authentication & data fetching
│   ├── linkedin_transformer.py      # 🔄 JSON-Resume transformation + lookups
│   ├── openai_processor.py          # 🤖 AI-powered content enhancement
│   ├── html_generator.py            # 🌐 HTML generation with external CSS
│   └── pdf_generator.py             # 📄 HTML-to-PDF conversion
├── assets/
│   ├── index.html                   # Generated HTML resume
│   ├── styles.css                   # Generated CSS with config values
│   └── Aviroop Mitra Resume.pdf     # Generated PDF resume
├── data/
│   ├── linkedin_raw.json            # Raw LinkedIn profile data
│   └── resume.json                  # JSON-Resume formatted data
├── prompts/
│   ├── categorize_skills.txt        # AI skill categorization prompt
│   ├── extract_points.txt           # AI bullet point extraction prompt
│   ├── filter_skills.txt            # AI skill filtering prompt
│   └── rank_items.txt               # AI section ranking prompt
├── requirements.txt                 # Python dependencies
└── .github/workflows/
    └── update-resume.yml            # Automated daily updates
```

## 🤖 AI Enhancement Features

### Intelligent Content Processing
- **Skill Filtering**: Removes irrelevant, duplicate, or outdated skills
- **Smart Categorization**: Groups skills into logical categories (Programming, Cloud, Frameworks, etc.)
- **Content Ranking**: Reorders work experience, projects, and achievements by relevance
- **Bullet Point Extraction**: Converts verbose descriptions into crisp, action-oriented bullet points

### Enhanced Data Integration
- **Company Lookups**: Automatically finds LinkedIn company URLs and public IDs
- **School Lookups**: Resolves educational institution LinkedIn profiles
- **Date Standardization**: Formats all dates consistently (e.g., "Jan, 2020 – Present")
- **Link Enhancement**: Creates clickable hyperlinks for all external references

### Customizable AI Prompts
All AI behavior is controlled through editable prompt files:
- `filter_skills.txt` - Defines skill relevance criteria
- `categorize_skills.txt` - Sets categorization logic and groupings
- `rank_items.txt` - Establishes ranking criteria for sections
- `extract_points.txt` - Guides bullet point extraction and formatting

## 🌐 HTML & PDF Generation

### Professional HTML Output
- **Responsive Design**: Optimized for desktop and mobile viewing
- **External CSS**: Clean separation with configurable `styles.css`
- **Clickable Links**: LinkedIn profiles, company pages, project URLs
- **Semantic Structure**: Proper HTML5 semantic elements
- **Compact Layout**: Minimal whitespace with professional typography

### PDF Generation Features
- **WeasyPrint Engine**: High-quality HTML-to-PDF conversion
- **Print Optimization**: Margin control and page break handling
- **Font Preservation**: Maintains typography and styling
- **Link Preservation**: Clickable URLs in PDF output
- **A4 Page Format**: Standard professional document sizing

### Styling Highlights
- **Typography**: Professional Times New Roman font family
- **Color Scheme**: Ink blue links with dark gray text
- **Layout**: Consistent spacing with configurable margins
- **Sections**: Clear hierarchy with uppercase section headers
- **Bullet Points**: AI-extracted points rendered as clean HTML lists

## ⚡ GitHub Actions Automation

Automated daily resume updates via GitHub Actions:

```yaml
# Runs weekly on Sundays at 09:00 IST (03:30 UTC)
# Manual trigger available via workflow_dispatch
# Uses cookie-based authentication for reliability
# Commits changes only if content is updated
```

**Workflow Features:**
- **Weekly Schedule**: Automatic updates every Sunday to keep resume current
- **Manual Trigger**: On-demand generation via GitHub Actions UI
- **Smart Commits**: Only commits when actual changes are detected
- **Environment Security**: Uses GitHub Secrets for credentials

## 🛠️ Development

### Adding Custom Styling

1. **Modify Configuration**: Update values in `scripts/config.py`
2. **Regenerate CSS**: Run `python scripts/html_generator.py`
3. **Preview Changes**: Open `assets/index.html` in browser
4. **Generate PDF**: Run `python scripts/pdf_generator.py`

### Extending AI Prompts

1. **Edit Prompt Files**: Modify files in `prompts/` directory
2. **Test Changes**: Run `python scripts/openai_processor.py`
3. **Review Output**: Check generated `resume.json`
4. **Iterate**: Refine prompts based on results

### Pipeline Customization

Each module exports main functions that can be imported and used independently:

```python
from scripts.linkedin_fetcher import fetch_linkedin_data
from scripts.openai_processor import filter_skills_with_openai
from scripts.html_generator import generate_html_resume_file
```

## 📊 Pipeline Output Example

```
🚀 Starting Resume Generation Pipeline
📁 Working directory: /path/to/resume
⚙️  Configuration: LinkedIn=Fetch, OpenAI=Process

============================================================
STEP 1/5: FETCH LINKEDIN DATA
============================================================
📝 Authenticate with LinkedIn and fetch profile information
✅ LinkedIn data fetched completed successfully

============================================================
STEP 2/5: TRANSFORM DATA
============================================================
📝 Convert LinkedIn profile data to JSON-Resume format
🔍 Searching for company: PwC India
✅ Found LinkedIn URL for PwC India: https://www.linkedin.com/company/pwc/
✅ Data transformation completed successfully

============================================================
STEP 3/5: OPENAI ENHANCEMENT
============================================================
📝 Filter skills, categorize, rank sections, and extract bullet points
[INFO] Filtering 56 skills via OpenAI
[INFO] Kept 24/56 skills after filtering
[INFO] Categorizing 24 skills via OpenAI
[INFO] Received 7 skill categories
✅ OpenAI enhancement completed successfully

============================================================
STEP 4/5: GENERATE HTML
============================================================
📝 Create professional HTML resume with responsive design
[INFO] HTML resume generated → assets/index.html
[INFO] CSS file generated → assets/styles.css
✅ HTML generation completed successfully

============================================================
STEP 5/5: GENERATE PDF
============================================================
📝 Create PDF resume from HTML using WeasyPrint
[INFO] PDF generated → assets/Aviroop Mitra Resume.pdf
✅ PDF generation completed successfully

============================================================
PIPELINE SUMMARY
============================================================
⏱️  Total time: 187.42 seconds
✅ Steps completed: 5/5
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
- Maintain the modular architecture
- Add configuration options to `config.py` for new features
- Update prompts for AI behavior changes
- Test the complete pipeline before submitting
- Follow existing code style and documentation patterns

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details. 