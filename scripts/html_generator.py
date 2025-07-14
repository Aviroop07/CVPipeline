#!/usr/bin/env python3
"""
HTML resume generation module.

This module provides functions to generate HTML resumes from JSON resume data.
"""

import json
import pathlib
import sys
import logging
from typing import List, Dict, Any
import config
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESUME_JSON = ROOT / config.DATA_DIR / config.RESUME_JSON_FILE
HTML_OUT = ROOT / config.ASSETS_DIR / "index.html"

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean text for HTML output.
    
    Args:
        text (str): Input text to clean
        
    Returns:
        str: Cleaned text with HTML entities escaped
    """
    if not text:
        return text
    
    # Escape HTML entities
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#39;")
    
    return text

def render_highlighted_text(text: str, highlights: List[str] = None) -> str:
    """Render text with highlighted technical terms.
    
    Args:
        text (str): Text to render
        highlights (List[str], optional): List of terms to highlight
        
    Returns:
        str: HTML with highlighted terms
    """
    if not highlights:
        return clean_text(text)
    
    # Clean the text first
    cleaned_text = clean_text(text)
    
    # Apply highlights (case-insensitive)
    for highlight in highlights:
        if highlight:
            # Escape the highlight term for regex
            escaped_highlight = re.escape(highlight)
            # Replace with highlighted version
            pattern = re.compile(escaped_highlight, re.IGNORECASE)
            cleaned_text = pattern.sub(f'<em class="highlight">{highlight}</em>', cleaned_text)
    
    return cleaned_text

def generate_css_file() -> str:
    """Generate CSS file content using config values.
    
    Returns:
        str: CSS content for styles.css file
    """
    css = f"""/* Professional Resume Styles - Generated from config.py */

/* Font Face Declarations */"""

    # Add regular font face if URL is provided
    if config.FONT_REGULAR_URL:
        css += f"""
@font-face {{
    font-family: "{config.FONT_FAMILY_NAME}";
    src: url("{config.FONT_REGULAR_URL}") format("{config.FONT_FORMAT}");
    font-weight: 400;
    font-style: normal;
    font-display: swap;
}}"""

    # Add italic font face if URL is provided
    if config.FONT_ITALIC_URL:
        css += f"""

@font-face {{
    font-family: "{config.FONT_FAMILY_NAME}";
    src: url("{config.FONT_ITALIC_URL}") format("{config.FONT_FORMAT}");
    font-weight: 400;
    font-style: italic;
    font-display: swap;
}}"""

    # Add bold font face if URL is provided
    if config.FONT_BOLD_URL:
        css += f"""

@font-face {{
    font-family: "{config.FONT_FAMILY_NAME}";
    src: url("{config.FONT_BOLD_URL}") format("{config.FONT_FORMAT}");
    font-weight: 700;
    font-style: normal;
    font-display: swap;
}}"""

    # Add bold italic font face if URL is provided
    if hasattr(config, 'FONT_BOLD_ITALIC_URL') and config.FONT_BOLD_ITALIC_URL:
        css += f"""

@font-face {{
    font-family: "{config.FONT_FAMILY_NAME}";
    src: url("{config.FONT_BOLD_ITALIC_URL}") format("{config.FONT_FORMAT}");
    font-weight: 700;
    font-style: italic;
    font-display: swap;
}}"""

    # Add light font face if URL is provided
    if hasattr(config, 'FONT_LIGHT_URL') and config.FONT_LIGHT_URL:
        css += f"""

@font-face {{
    font-family: "{config.FONT_FAMILY_NAME}";
    src: url("{config.FONT_LIGHT_URL}") format("{config.FONT_FORMAT}");
    font-weight: 300;
    font-style: normal;
    font-display: swap;
}}"""

    # Add medium font face if URL is provided
    if hasattr(config, 'FONT_MEDIUM_URL') and config.FONT_MEDIUM_URL:
        css += f"""

@font-face {{
    font-family: "{config.FONT_FAMILY_NAME}";
    src: url("{config.FONT_MEDIUM_URL}") format("{config.FONT_FORMAT}");
    font-weight: 500;
    font-style: normal;
    font-display: swap;
}}"""

    # Add extra bold font face if URL is provided
    if hasattr(config, 'FONT_EXTRA_BOLD_URL') and config.FONT_EXTRA_BOLD_URL:
        css += f"""

@font-face {{
    font-family: "{config.FONT_FAMILY_NAME}";
    src: url("{config.FONT_EXTRA_BOLD_URL}") format("{config.FONT_FORMAT}");
    font-weight: 800;
    font-style: normal;
    font-display: swap;
}}"""

    css += f"""

/* Reset default page margins for PDF generation */
@page {{
    size: A4;
    margin: 0;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

html, body {{
    margin: 0;
    padding: 0;
}}

body {{
        font-family: "{config.HTML_FONT_FAMILY}";
        line-height: {config.HTML_LINE_HEIGHT};
        color: {config.HTML_COLOR_PRIMARY};
        background-color: #ffffff;
        max-width: 800px;
        margin: 0;
        margin-left: {config.HTML_BODY_MARGIN_LEFT};
        margin-right: {config.HTML_BODY_MARGIN_RIGHT};
        padding: {config.HTML_BODY_PADDING};
        font-size: {config.HTML_FONT_SIZE_BASE_FALLBACK}; /* Fallback for older browsers */
        font-size: {config.HTML_FONT_SIZE_BASE};
    }}

.container {{
    background: white;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
    padding: {config.HTML_CONTAINER_PADDING};
    border-radius: 8px;
}}

/* Header Styles */
.header {{
    text-align: center;
    margin-bottom: {config.HTML_HEADER_MARGIN_BOTTOM};
    padding-bottom: {config.HTML_HEADER_PADDING_BOTTOM};
}}

    .name {{
        font-size: {config.HTML_FONT_SIZE_NAME_FALLBACK}; /* Fallback for older browsers */
        font-size: {config.HTML_FONT_SIZE_NAME};
        font-weight: bold;
        color: {config.HTML_COLOR_PRIMARY};
        margin-bottom: 10px;
    }}

    .contact-info {{
        font-size: {config.HTML_FONT_SIZE_CONTACT_FALLBACK}; /* Fallback for older browsers */
        font-size: {config.HTML_FONT_SIZE_CONTACT};
        color: {config.HTML_COLOR_SECONDARY};
        line-height: 1.4;
    }}

.contact-info a {{
    color: {config.HTML_COLOR_LINK};
    text-decoration: none;
}}

.contact-info a:hover {{
    text-decoration: underline;
}}

/* Section Styles */
.section {{
    margin-top: {config.HTML_SECTION_MARGIN_TOP};
    margin-bottom: 0;
}}

.section:first-child {{
    margin-top: 0;
}}

    .section-title {{
        font-size: {config.HTML_FONT_SIZE_SECTION_FALLBACK}; /* Fallback for older browsers */
        font-size: {config.HTML_FONT_SIZE_SECTION};
        font-weight: bold;
        color: {config.HTML_COLOR_PRIMARY};
        text-transform: uppercase;
        margin-bottom: 0;
        padding-bottom: 0;
    }}

/* Item Styles */
.item {{
    margin-bottom: 0;
    padding-bottom: 0;
}}

.item:last-child {{
    margin-bottom: 0;
    padding-bottom: 0;
}}

.item-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0;
    flex-wrap: wrap;
}}

.item-title {{
    flex: 1;
    font-weight: bold;
    color: {config.HTML_COLOR_PRIMARY};
}}

.item-date {{
    font-style: italic;
    color: {config.HTML_COLOR_ACCENT};
    white-space: nowrap;
    margin-left: 0;
    padding-left: {config.HTML_DATE_PADDING_LEFT};
}}

.item-description {{
    margin-top: 0;
    color: #444;
    line-height: 1.5;
}}

.item-points {{
    margin-top: 0;
    padding-left: 15px;
}}

.item-points li {{
    margin-bottom: 0;
    color: #444;
    line-height: 1.4;
}}

/* Link Styles */
.company-link,
.school-link {{
    color: {config.HTML_COLOR_LINK};
    text-decoration: none;
    font-weight: bold;
}}

.company-link:hover,
.school-link:hover {{
    text-decoration: underline;
}}

.project-link {{
    color: #000000;
    text-decoration: underline;
    font-weight: normal;
}}

.project-link:hover {{
    text-decoration: underline;
}}

.company-name,
.school-name,
.project-name {{
    font-weight: bold;
    color: {config.HTML_COLOR_LINK};
}}

.position,
.degree {{
    color: {config.HTML_COLOR_PRIMARY};
    font-weight: bold;
}}

.gpa {{
    color: {config.HTML_COLOR_SECONDARY};
    font-weight: normal;
    font-style: italic;
}}

/* Skills Section */
.skill-category {{
    margin-bottom: 0;
    line-height: 1.4;
}}

.skill-category-name {{
    font-weight: bold;
    color: {config.HTML_COLOR_LINK};
}}

.skill-list {{
    color: #444;
}}

/* Awards Section */
.award-title {{
    font-weight: bold;
    color: {config.HTML_COLOR_LINK};
}}

.award-issuer {{
    font-weight: bold;
    color: {config.HTML_COLOR_PRIMARY};
}}

/* Extracted Projects (Sub-projects) */
.extracted-projects {{
    margin-top: 8px;
}}

.sub-project {{
    margin-bottom: {config.HTML_ITEM_MARGIN_BOTTOM};
    padding-left: 15px;
    border-left: 2px solid {config.HTML_COLOR_BORDER};
}}

.sub-project:last-child {{
    margin-bottom: 0;
}}

.sub-project-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0;
    flex-wrap: wrap;
}}

.sub-project-title {{
    color: {config.HTML_COLOR_LINK};
    font-weight: normal;
}}

.sub-project-company {{
    color: {config.HTML_COLOR_PRIMARY};
    font-weight: normal;
}}

.sub-project-description {{
    margin-top: 0;
    color: #444;
    line-height: 1.5;
}}

/* Ensure all dates are italic with higher specificity */
.item-date,
.sub-project .item-date,
.sub-project-header .item-date {{
    font-style: italic !important;
}}

/* Tech Highlighting */
em.highlight,
.sub-project-description em.highlight,
.item-description em.highlight,
.extracted-projects em.highlight {{
    font-style: italic !important;
    font-weight: bold !important;
}}

/* Responsive Design */
@media (max-width: {config.HTML_MOBILE_BREAKPOINT}) {{
    body {{
        padding: {config.HTML_BODY_PADDING_MOBILE};
    }}
    
    .container {{
        padding: {config.HTML_CONTAINER_PADDING_MOBILE};
    }}
    
    .name {{
        font-size: {config.HTML_FONT_SIZE_NAME_MOBILE_FALLBACK}; /* Fallback for older browsers */
        font-size: {config.HTML_FONT_SIZE_NAME_MOBILE};
    }}
    
    .item-header {{
        flex-direction: column;
        align-items: flex-start;
    }}
    
    .item-date {{
        margin-left: 0;
        margin-top: 2px;
        font-style: italic;
    }}
    
    .contact-info {{
        font-size: {config.HTML_FONT_SIZE_CONTACT_MOBILE_FALLBACK}; /* Fallback for older browsers */
        font-size: {config.HTML_FONT_SIZE_CONTACT_MOBILE};
    }}
    
    .sub-project {{
        padding-left: 10px;
    }}
}}

@media print {{
    body {{
        max-width: none;
        padding: 0;
        background: white;
    }}
    
    .container {{
        box-shadow: none;
        padding: 20px;
    }}
    
    .section {{
        page-break-inside: avoid;
    }}
    
    .item {{
        page-break-inside: avoid;
    }}
}}
"""
    return css

def generate_html_resume(data: Dict[str, Any]) -> str:
    """Generate HTML resume from resume data.
    
    Args:
        data (Dict): Resume data in JSON-Resume format
        
    Returns:
        str: Complete HTML document
    """
    basics = data.get("basics", {})
    work = data.get("work", [])
    education = data.get("education", [])
    projects = data.get("projects", [])
    skills_by_category = data.get("skills_by_category", {})
    awards = data.get("awards", [])
    
    # Start building HTML (no linebreaks)
    html = f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{clean_text(basics.get("name", "Resume"))}</title><link rel="stylesheet" href="styles.css"></head><body><div class="container"><header class="header"><h1 class="name">{clean_text(basics.get("name", ""))}</h1><div class="contact-info">'
    
    # Contact information
    contact_parts = []
    if basics.get("email"):
        contact_parts.append(f'<a href="mailto:{clean_text(basics["email"])}">{clean_text(basics["email"])}</a>')
    if basics.get("phone"):
        contact_parts.append(f'<span>{clean_text(basics["phone"])}</span>')
    if basics.get("location"):
        contact_parts.append(f'<span>{clean_text(basics["location"])}</span>')
    if basics.get("public_id"):
        contact_parts.append(f'<a href="https://www.linkedin.com/in/{basics["public_id"]}" target="_blank">LinkedIn</a>')
    
    html += " | ".join(contact_parts)
    html += '</div></header><main class="content">'
    
    # Work Experience Section
    if work:
        html += '<section class="section"><h2 class="section-title">Professional Experience</h2>'
        for job in work:
            html += '<div class="item"><div class="item-header"><div class="item-title">'
            if job.get("url"):
                html += f'<a href="{clean_text(job["url"])}" target="_blank" class="company-link">{clean_text(job.get("name", ""))}</a>'
            else:
                html += f'<span class="company-name">{clean_text(job.get("name", ""))}</span>'
            
            if job.get("position"):
                html += f' | <span class="position">{clean_text(job["position"])}</span>'
            
            html += '</div>'
            
            if job.get("period"):
                html += f'<div class="item-date">{clean_text(job["period"])}</div>'
            
            html += '</div>'
            
            # Render extracted projects only (no original points or summary)
            if job.get("extracted_projects"):
                html += '<div class="extracted-projects">'
                for i, project in enumerate(job["extracted_projects"]):
                    if project.get("title"):
                        html += f'<div class="sub-project">'
                        html += f'<div class="sub-project-header">'
                        html += f'<div class="item-title">'
                        html += f'<span class="sub-project-title">{clean_text(project["title"])}</span>'
                        
                        # Add company if different from parent company
                        if project.get("company") and project["company"] != job.get("name"):
                            html += f' | <span class="sub-project-company">{clean_text(project["company"])}</span>'
                        
                        html += '</div>'
                        
                        # Add duration using the same format as main experience
                        if project.get("duration"):
                            duration = project["duration"]
                            start_month = None
                            start_year = None
                            end_month = None
                            end_year = None
                            
                            if duration.get("start"):
                                start = duration["start"]
                                if start.get("month") and start.get("year"):
                                    start_month = start["month"]
                                    start_year = start["year"]
                                elif start.get("year"):
                                    start_year = start["year"]
                            
                            if duration.get("end"):
                                end = duration["end"]
                                if end.get("month") and end.get("year"):
                                    end_month = end["month"]
                                    end_year = end["year"]
                                elif end.get("year"):
                                    end_year = end["year"]
                            
                            if start_month and start_year:
                                start_month_name = config.MONTHS[start_month - 1] if 1 <= start_month <= 12 else str(start_month)
                                
                                if end_month and end_year:
                                    end_month_name = config.MONTHS[end_month - 1] if 1 <= end_month <= 12 else str(end_month)
                                    
                                    # Same month and year
                                    if start_month == end_month and start_year == end_year:
                                        date_range = f"{start_month_name}, {start_year}"
                                    # Same year, different months
                                    elif start_year == end_year:
                                        date_range = f"{start_month_name} – {end_month_name}, {start_year}"
                                    # Different years
                                    else:
                                        date_range = f"{start_month_name}, {start_year} – {end_month_name}, {end_year}"
                                elif end_year and not end_month:
                                    # End year only, no month
                                    date_range = f"{start_month_name}, {start_year} – {end_year}"
                                else:
                                    # No end date
                                    date_range = f"{start_month_name}, {start_year} – Present"
                                
                                html += f'<div class="item-date">{clean_text(date_range)}</div>'
                            elif start_year:
                                # Start year only, no month
                                if end_year:
                                    date_range = f"{start_year} – {end_year}"
                                else:
                                    date_range = f"{start_year} – Present"
                                html += f'<div class="item-date">{clean_text(date_range)}</div>'
                        
                        html += '</div>'
                        
                        # Add description if available
                        if project.get("description"):
                            description = clean_text(project["description"])
                            
                            # Apply tech highlighting if available
                            if project.get("tech_highlights"):
                                # Sort highlights by length (longest first) to avoid partial replacements
                                highlights = sorted(project["tech_highlights"], key=len, reverse=True)
                                for highlight in highlights:
                                    # Clean the highlight text for comparison
                                    clean_highlight = clean_text(highlight)
                                    if clean_highlight in description:
                                        # Wrap the highlight in italic tags
                                        highlighted = f'<em class="highlight">{clean_highlight}</em>'
                                        description = description.replace(clean_highlight, highlighted)
                            
                            html += f'<div class="sub-project-description">{description}</div>'
                        
                        html += '</div>'
                html += '</div>'
            
            html += '</div>'
        
        html += '</section>'
    
    # Education Section
    if education:
        html += '<section class="section"><h2 class="section-title">Education</h2>'
        for edu in education:
            html += '<div class="item"><div class="item-header"><div class="item-title">'
            if edu.get("url"):
                html += f'<a href="{clean_text(edu["url"])}" target="_blank" class="school-link">{clean_text(edu.get("institution", ""))}</a>'
            else:
                html += f'<span class="school-name">{clean_text(edu.get("institution", ""))}</span>'
            
            degree_parts = []
            if edu.get("studyType"):
                degree_parts.append(edu["studyType"])
            if edu.get("area"):
                degree_parts.append(f"in {edu['area']}")
            
            if degree_parts:
                html += f' | <span class="degree">{clean_text(" ".join(degree_parts))}</span>'
            
            # Add GPA to the same line if available
            if edu.get("score"):
                html += f' | <span class="gpa">GPA: {clean_text(edu["score"])}</span>'
            
            html += '</div>'
            
            if edu.get("period"):
                html += f'<div class="item-date">{clean_text(edu["period"])}</div>'
            
            html += '</div>'
            
            html += '</div>'
        
        html += '</section>'
    
    # Projects Section
    if projects:
        html += '<section class="section"><h2 class="section-title">Projects</h2>'
        for project in projects:
            html += '<div class="item"><div class="item-header"><div class="item-title">'
            
            # Project name as plain text
            html += f'<span class="project-name">{clean_text(project.get("name", ""))}</span>'
            
            # Add GitHub link with pipe delimiter if URL exists
            if project.get("url"):
                html += f' | <a href="{clean_text(project["url"])}" target="_blank" class="project-link">GitHub</a>'
            
            html += '</div>'
            
            if project.get("period"):
                html += f'<div class="item-date">{clean_text(project["period"])}</div>'
            
            html += '</div>'
            
            if project.get("points"):
                if len(project["points"]) == 1:
                    # Single point - render as paragraph, not list
                    point = project["points"][0]
                    if isinstance(point, dict) and "text" in point:
                        # New highlighted format
                        html += f'<div class="item-description">{render_highlighted_text(point["text"], point.get("highlights"))}</div>'
                    else:
                        # Old string format
                        html += f'<div class="item-description">{clean_text(point)}</div>'
                else:
                    # Multiple points - render as bulleted list
                    html += '<ul class="item-points">'
                    for point in project["points"]:
                        if isinstance(point, dict) and "text" in point:
                            # New highlighted format
                            html += f'<li>{render_highlighted_text(point["text"], point.get("highlights"))}</li>'
                        else:
                            # Old string format
                            html += f'<li>{clean_text(point)}</li>'
                    html += '</ul>'
            elif project.get("description"):
                html += f'<div class="item-description">{clean_text(project["description"])}</div>'
            
            html += '</div>'
        
        html += '</section>'
    
    # Skills Section
    if skills_by_category:
        html += '<section class="section"><h2 class="section-title">Skills</h2>'
        for category, skills in skills_by_category.items():
            if skills:
                html += f'<div class="skill-category"><span class="skill-category-name">{clean_text(category)}:</span> <span class="skill-list">{clean_text(", ".join(skills))}</span></div>'
        html += '</section>'
    
    # Awards Section
    if awards:
        html += '<section class="section"><h2 class="section-title">Awards & Achievements</h2>'
        for award in awards:
            html += '<div class="item"><div class="item-header"><div class="item-title"><span class="award-title">'
            html += clean_text(award.get("title", ""))
            html += '</span>'
            
            # Add issuer/awarder with | delimiter
            if award.get("issuer") or award.get("awarder"):
                issuer = award.get("issuer") or award.get("awarder")
                html += f' | <span class="award-issuer">{clean_text(issuer)}</span>'
            
            # Add any score/ranking/details with | delimiter
            if award.get("score"):
                html += f' | <span class="gpa">Score: {clean_text(award["score"])}</span>'
            elif award.get("ranking"):
                html += f' | <span class="gpa">Rank: {clean_text(award["ranking"])}</span>'
            elif award.get("details"):
                html += f' | <span class="gpa">{clean_text(award["details"])}</span>'
            
            # Add summary to the same line if available
            if award.get("summary"):
                html += f' | <span class="gpa">{clean_text(award["summary"])}</span>'
            
            html += '</div>'
            
            if award.get("date"):
                html += f'<div class="item-date">{clean_text(award["date"])}</div>'
            
            html += '</div>'
            
            html += '</div>'
        
        html += '</section>'
    
    # Close HTML
    html += '</main></div></body></html>'
    
    return html

def load_resume_data(input_path=None):
    """Load resume data from JSON file.
    
    Args:
        input_path (pathlib.Path, optional): Custom input path. Defaults to configured path.
        
    Returns:
        dict: Resume data
        
    Raises:
        SystemExit: If file doesn't exist
    """
    if input_path is None:
        input_path = RESUME_JSON
        
    if not input_path.exists():
        log.error(f"{config.RESUME_JSON_FILE} not found – aborting")
        sys.exit(1)

    log.info(f"Loading {config.RESUME_JSON_FILE}")
    return json.loads(input_path.read_text(encoding="utf-8"))

def save_html_resume(html_content: str, output_path=None):
    """Save HTML resume to file.
    
    Args:
        html_content (str): HTML content to save
        output_path (pathlib.Path, optional): Custom output path. Defaults to configured path.
        
    Returns:
        pathlib.Path: Path where HTML was saved
    """
    if output_path is None:
        output_path = HTML_OUT
    
    # Ensure assets directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    output_path.write_text(html_content, encoding="utf-8")
    log.info("HTML resume generated → %s", output_path.relative_to(ROOT))
    return output_path

def save_css_file(css_content: str, output_path=None):
    """Save CSS file with config-based styles.
    
    Args:
        css_content (str): CSS content to save
        output_path (pathlib.Path, optional): Custom output path. Defaults to assets/styles.css
        
    Returns:
        pathlib.Path: Path where CSS was saved
    """
    if output_path is None:
        output_path = ROOT / config.ASSETS_DIR / "styles.css"
    
    # Ensure assets directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    output_path.write_text(css_content, encoding="utf-8")
    log.info("CSS file generated → %s", output_path.relative_to(ROOT))
    return output_path



def generate_html_resume_file():
    """Complete HTML generation pipeline.
    
    Returns:
        pathlib.Path: Path to generated HTML file
        
    Raises:
        SystemExit: If generation fails
    """
    # Load resume data
    data = load_resume_data()
    
    log.info("Generating HTML resume and CSS...")
    
    # Generate CSS file with config values
    css_content = generate_css_file()
    save_css_file(css_content)
    
    # Generate HTML content
    html_content = generate_html_resume(data)
    
    # Save HTML
    output_path = save_html_resume(html_content)
    
    return output_path

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    generate_html_resume_file()

if __name__ == "__main__":
    main() 