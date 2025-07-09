# Centralised configuration for resume generation utilities


# OpenAI chat model to use
OPENAI_MODEL = "o4-mini"

# OpenAI reasoning effort setting for the model
OPENAI_REASONING_EFFORT = "high"

# Default temperature for deterministic outputs
OPENAI_TEMPERATURE = 1

# Month abbreviations for date formatting
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# Word count threshold above which we ask OpenAI to extract bullet points
POINT_WORD_THRESHOLD = 100



# File names and paths
RESUME_JSON_FILE = "resume.json"
RESUME_PDF_FILE = "Aviroop Mitra Resume.pdf"
RESUME_HTML_FILE = "index.html"
LINKEDIN_RAW_FILE = "linkedin_raw.json"

# Prompt files
FILTER_SKILLS_PROMPT = "filter_skills.txt"
EXTRACT_POINTS_PROMPT = "extract_points.txt"
EXPERIENCE_EXTRACTION_PROMPT = "experience_extraction.txt"
HIGHLIGHT_TECH_PROMPT = "highlight_tech.txt"

# Directory names
DATA_DIR = "data"
PROMPTS_DIR = "prompts"
ASSETS_DIR = "assets"



# Font configuration for @font-face declarations
FONT_FAMILY_NAME = "HelveticaNeue"
FONT_REGULAR_URL = "fonts/HelveticaNeueLTStd-Roman.otf"
FONT_ITALIC_URL = "fonts/HelveticaNeueLTStd-It.otf"
FONT_BOLD_URL = "fonts/HelveticaNeueLTStd-Md.otf"  # Using Medium for better readability
FONT_BOLD_ITALIC_URL = "fonts/HelveticaNeueLTStd-MdIt.otf"  # Medium Italic for bold italic

# Additional font weights for enhanced typography (optional)
FONT_LIGHT_URL = "fonts/HelveticaNeueLTStd-Lt.otf"  # For subtle elements
FONT_MEDIUM_URL = "fonts/HelveticaNeueLTStd-Md.otf"  # For section headers
FONT_EXTRA_BOLD_URL = "fonts/HelveticaNeueLTStd-Bd.otf"  # For name header

FONT_FORMAT = "opentype"  # "opentype" for .otf, "truetype" for .ttf, "woff2" for web fonts

# HTML generation settings - using configurable font family
HTML_FONT_FAMILY = f"'{FONT_FAMILY_NAME}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
HTML_FONT_SIZE_BASE = "12px"
HTML_FONT_SIZE_NAME = "18px"
HTML_FONT_SIZE_SECTION = "14px"
HTML_FONT_SIZE_CONTACT = "12px"
HTML_LINE_HEIGHT = "1.3"

# HTML margin/padding settings (in pixels)
HTML_BODY_PADDING = "3px"
HTML_BODY_PADDING_MOBILE = "2px"
HTML_BODY_MARGIN_LEFT = "35px"
HTML_BODY_MARGIN_RIGHT = "20px"
HTML_CONTAINER_PADDING = "5px"
HTML_CONTAINER_PADDING_MOBILE = "3px"
HTML_SECTION_MARGIN_TOP = "10px"
HTML_SECTION_MARGIN_BOTTOM = "4px"
HTML_ITEM_MARGIN_BOTTOM = "3px"
HTML_HEADER_MARGIN_BOTTOM = "5px"
HTML_HEADER_PADDING_BOTTOM = "3px"
HTML_DATE_PADDING_LEFT = "10px"

# HTML color scheme
HTML_COLOR_PRIMARY = "#2c3e50"
HTML_COLOR_SECONDARY = "#666"
HTML_COLOR_LINK = "#0066cc"
HTML_COLOR_ACCENT = "#7f8c8d"
HTML_COLOR_BORDER = "#e0e0e0"
HTML_COLOR_SECTION_BORDER = "#bdc3c7"

# HTML responsive breakpoint
HTML_MOBILE_BREAKPOINT = "768px"

# Google knowledge graph API details
KG_URL = "https://kgsearch.googleapis.com/v1/entities:search"


# Github details
GITHUB_URL = "https://github.com"
README_FILE = "README.md"
GITHUB_USERNAME = "Aviroop07"  # Default GitHub username