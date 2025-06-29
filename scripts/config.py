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
POINT_WORD_THRESHOLD = 50

# PDF generation settings
PDF_FONT_SIZE = 10
PDF_HEADING_FONT_SIZE = 14
PDF_TITLE_FONT_SIZE = 18
PDF_MARGIN = 50
PDF_LINE_SPACING = 1.2
PDF_SECTION_SPACING = 8  # Space between sections in points

# File names and paths
RESUME_JSON_FILE = "resume.json"
RESUME_MD_FILE = "resume.md"
RESUME_PDF_FILE = "Aviroop_Mitra_Resume.pdf"
LINKEDIN_RAW_FILE = "linkedin_raw.json"
TEMPLATE_FILE = "resume.md.j2"

# Prompt files
RANK_ITEMS_PROMPT = "rank_items.txt"
CATEGORIZE_SKILLS_PROMPT = "categorize_skills.txt"
FILTER_SKILLS_PROMPT = "filter_skills.txt"
EXTRACT_POINTS_PROMPT = "extract_points.txt"

# Directory names
DATA_DIR = "data"
PROMPTS_DIR = "prompts"
TEMPLATES_DIR = "templates"