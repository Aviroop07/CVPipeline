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

# PDF generation settings
PDF_FONT_SIZE = 10
PDF_HEADING_FONT_SIZE = 12
PDF_TITLE_FONT_SIZE = 14

# PDF margin settings (in points, 72 points = 1 inch)
PDF_MARGIN_TOP = 20
PDF_MARGIN_BOTTOM = 20
PDF_MARGIN_LEFT = 20
PDF_MARGIN_RIGHT = 20

# Legacy margin setting for backward compatibility
PDF_MARGIN = 40

PDF_LINE_SPACING = 1

# borb element spacing configuration (in points)
# Margins control gaps around elements (before/after spacing)
PDF_ELEMENT_MARGIN_TOP = 0      # Default top margin for most elements
PDF_ELEMENT_MARGIN_BOTTOM = 0   # Default bottom margin for most elements
PDF_ELEMENT_MARGIN_LEFT = 0     # Default left margin for elements
PDF_ELEMENT_MARGIN_RIGHT = 0    # Default right margin for elements

# Section-specific spacing
PDF_SECTION_MARGIN_TOP = 0      # Space before section headings
PDF_SECTION_MARGIN_BOTTOM = 0   # Space after section headings
PDF_HEADER_MARGIN_BOTTOM = 0    # Space after name/contact header
PDF_ITEM_MARGIN_BOTTOM = 0      # Space after work/education/project items

# Text element spacing
PDF_PARAGRAPH_MARGIN_BOTTOM = 0 # Space after regular paragraphs
PDF_BULLET_MARGIN_BOTTOM = 0    # Space after bullet points
PDF_SUBITEM_MARGIN_BOTTOM = 0   # Space after sub-items (like GPA)

# Line spacing within paragraphs
PDF_PARAGRAPH_LEADING = None  # Fixed leading for paragraphs (None for automatic)
PDF_PARAGRAPH_LEADING_MULT = 0 # Multiplied leading (relative to font size)

# Spacer sizes for explicit gaps
PDF_SPACER_SMALL = 4           # Small spacer (4 pt)
PDF_SPACER_MEDIUM = 8          # Medium spacer (8 pt) 
PDF_SPACER_LARGE = 16          # Large spacer (16 pt)

# Legacy section spacing (deprecated - use margin-based approach)
PDF_SECTION_SPACING = 0 # Space between sections in points

# File names and paths
RESUME_JSON_FILE = "resume.json"
RESUME_PDF_FILE = "Aviroop Mitra Resume.pdf"
LINKEDIN_RAW_FILE = "linkedin_raw.json"

# Prompt files
RANK_ITEMS_PROMPT = "rank_items.txt"
CATEGORIZE_SKILLS_PROMPT = "categorize_skills.txt"
FILTER_SKILLS_PROMPT = "filter_skills.txt"
EXTRACT_POINTS_PROMPT = "extract_points.txt"

# Directory names
DATA_DIR = "data"
PROMPTS_DIR = "prompts"

# New tight leading multiplier for minimal PDF whitespace
PDF_TIGHT_LEADING_MULT = 0.6