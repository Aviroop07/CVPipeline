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
RANK_ITEMS_PROMPT = "rank_items.txt"
CATEGORIZE_SKILLS_PROMPT = "categorize_skills.txt"
FILTER_SKILLS_PROMPT = "filter_skills.txt"
EXTRACT_POINTS_PROMPT = "extract_points.txt"

# Directory names
DATA_DIR = "data"
PROMPTS_DIR = "prompts"
ASSETS_DIR = "assets"



# HTML generation settings
HTML_FONT_FAMILY = "'Times New Roman', Times, serif"
HTML_FONT_SIZE_BASE = "13px"
HTML_FONT_SIZE_NAME = "20px"
HTML_FONT_SIZE_SECTION = "15px"
HTML_FONT_SIZE_CONTACT = "13px"
HTML_LINE_HEIGHT = "1.3"

# HTML margin/padding settings (in pixels)
HTML_BODY_PADDING = "3px"
HTML_BODY_PADDING_MOBILE = "2px"
HTML_BODY_MARGIN_LEFT = "35px"
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