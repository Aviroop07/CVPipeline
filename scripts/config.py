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