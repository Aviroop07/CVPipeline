#!/usr/bin/env python3
"""
Generate PDF version of the résumé directly using borb.

Steps:
1. Load resume.json (JSON-Resume 1.0 structure, already processed with OpenAI).
2. Generate PDF directly using borb library.

Usage:
    python scripts/generate_pdf_resume.py

Inputs:
    resume.json (from process_with_openai.py)

Outputs:
    Aviroop_Mitra_Resume.pdf
"""

from __future__ import annotations

import json, os, pathlib, sys, logging
from typing import List, Dict, Any
import config
import dotenv

# borb imports for version 2.x
from borb.pdf import Document, Page, Paragraph
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.page_layout.page_layout import PageLayout
from borb.pdf.canvas.layout.text.paragraph import Paragraph

from borb.pdf.canvas.layout.layout_element import Alignment
from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.font.simple_font.font_type_1 import StandardType1Font
from borb.pdf import PDF

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESUME_JSON = ROOT / config.RESUME_JSON_FILE
PDF_OUT = ROOT / config.RESUME_PDF_FILE

# Load environment variables from .env file if present
dotenv.load_dotenv()

# Initialise logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────── Helpers

def clean_text(text: str) -> str:
    """Remove or replace special Unicode characters that can't be rendered in basic fonts."""
    if not text:
        return text
    
    # Replace common special characters
    replacements = {
        '↔': '<->',  # left-right arrow
        '↑': '^',    # up arrow
        '→': '->',   # right arrow
        '←': '<-',   # left arrow
        '↓': 'v',    # down arrow
        '•': '*',    # bullet point (though we add our own)
        '–': '-',    # en dash
        '—': '-',    # em dash
        ''': "'",    # smart quote
        ''': "'",    # smart quote
        '"': '"',    # smart quote
        '"': '"',    # smart quote
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    return result

# ───────────────────────────────────────────────────────── PDF Generation

def create_header(layout: PageLayout, basics: Dict[str, Any]) -> None:
    """Create the header section with name, contact info, and links."""
    # Name as title
    name = clean_text(basics.get("name", ""))
    layout.add(Paragraph(
        name,
        font=StandardType1Font("Helvetica-Bold"),
        font_size=config.PDF_TITLE_FONT_SIZE,
        horizontal_alignment=Alignment.CENTERED
    ))
    
    # Contact information
    contact_info = []
    if basics.get("email"):
        contact_info.append(clean_text(basics["email"]))
    if basics.get("phone"):
        contact_info.append(clean_text(basics["phone"]))
    if basics.get("location", {}).get("city"):
        location = basics["location"]
        location_str = f"{location.get('city', '')}, {location.get('region', '')}"
        contact_info.append(clean_text(location_str))
    
    if contact_info:
        layout.add(Paragraph(
            " | ".join(contact_info),
            font=StandardType1Font("Helvetica"),
            font_size=config.PDF_FONT_SIZE,
            horizontal_alignment=Alignment.CENTERED
        ))
    
    # Links
    if basics.get("profiles"):
        links = []
        for profile in basics["profiles"]:
            if profile.get("url"):
                links.append(profile["url"])
        if links:
            layout.add(Paragraph(
                " | ".join(links),
                font=StandardType1Font("Helvetica"),
                font_size=config.PDF_FONT_SIZE - 1,
                horizontal_alignment=Alignment.CENTERED
            ))
    
    layout.add(Paragraph(" "))  # Spacing

def create_section_heading(layout: PageLayout, title: str) -> None:
    """Create a section heading."""
    layout.add(Paragraph(
        title.upper(),
        font=StandardType1Font("Helvetica-Bold"),
        font_size=config.PDF_HEADING_FONT_SIZE,
        horizontal_alignment=Alignment.LEFT
    ))
    layout.add(Paragraph(" "))  # Spacing

def create_work_experience(layout: PageLayout, work: List[Dict[str, Any]]) -> None:
    """Create the work experience section."""
    if not work:
        return
    
    create_section_heading(layout, "Professional Experience")
    
    for job in work:
        # Job header: Position at Company
        position = clean_text(job.get("position", ""))
        company = clean_text(job.get("name", ""))
        period = clean_text(job.get("period", ""))
        
        header_text = f"{position}"
        if company:
            header_text += f" at {company}"
        if period:
            header_text += f" • {period}"
        
        layout.add(Paragraph(
            header_text,
            font=StandardType1Font("Helvetica-Bold"),
            font_size=config.PDF_FONT_SIZE
        ))
        
        # Company URL if available
        if job.get("url"):
            layout.add(Paragraph(
                clean_text(job["url"]),
                font=StandardType1Font("Helvetica"),
                font_size=config.PDF_FONT_SIZE - 1,
                font_color=HexColor("0066CC")
            ))
        
        # Bullet points
        points = job.get("points", [])
        if points:
            for point in points:
                layout.add(Paragraph(
                    f"• {clean_text(point)}",
                    font=StandardType1Font("Helvetica"),
                    font_size=config.PDF_FONT_SIZE - 1
                ))
        
        layout.add(Paragraph(" "))  # Spacing between jobs

def create_education(layout: PageLayout, education: List[Dict[str, Any]]) -> None:
    """Create the education section."""
    if not education:
        return
    
    create_section_heading(layout, "Education")
    
    for edu in education:
        # Education header: Degree at Institution
        degree = clean_text(edu.get("studyType", ""))
        field = clean_text(edu.get("area", ""))
        institution = clean_text(edu.get("institution", ""))
        period = clean_text(edu.get("period", ""))
        
        header_text = f"{degree}"
        if field:
            header_text += f" in {field}"
        if institution:
            header_text += f" • {institution}"
        if period:
            header_text += f" • {period}"
        
        layout.add(Paragraph(
            header_text,
            font=StandardType1Font("Helvetica-Bold"),
            font_size=config.PDF_FONT_SIZE
        ))
        
        # GPA if available
        if edu.get("score"):
            layout.add(Paragraph(
                f"GPA: {clean_text(edu['score'])}",
                font=StandardType1Font("Helvetica"),
                font_size=config.PDF_FONT_SIZE - 1
            ))
        
        layout.add(Paragraph(" "))  # Spacing

def create_projects(layout: PageLayout, projects: List[Dict[str, Any]]) -> None:
    """Create the projects section."""
    if not projects:
        return
    
    create_section_heading(layout, "Projects")
    
    for project in projects:
        # Project header: Name
        name = clean_text(project.get("name", ""))
        period = clean_text(project.get("period", ""))
        
        header_text = name
        if period:
            header_text += f" • {period}"
        
        layout.add(Paragraph(
            header_text,
            font=StandardType1Font("Helvetica-Bold"),
            font_size=config.PDF_FONT_SIZE
        ))
        
        # Project URL if available
        if project.get("url"):
            layout.add(Paragraph(
                clean_text(project["url"]),
                font=StandardType1Font("Helvetica"),
                font_size=config.PDF_FONT_SIZE - 1,
                font_color=HexColor("0066CC")
            ))
        
        # Description
        description = clean_text(project.get("description", ""))
        if description:
            layout.add(Paragraph(
                description,
                font=StandardType1Font("Helvetica"),
                font_size=config.PDF_FONT_SIZE - 1
            ))
        
        # Bullet points
        points = project.get("points", [])
        if points:
            for point in points:
                layout.add(Paragraph(
                    f"• {clean_text(point)}",
                    font=StandardType1Font("Helvetica"),
                    font_size=config.PDF_FONT_SIZE - 1
                ))
        
        layout.add(Paragraph(" "))  # Spacing

def create_skills(layout: PageLayout, skills_by_category: Dict[str, List[str]]) -> None:
    """Create the skills section."""
    if not skills_by_category:
        return
    
    create_section_heading(layout, "Skills")
    
    for category, skills in skills_by_category.items():
        if skills:
            layout.add(Paragraph(
                f"{category}:",
                font=StandardType1Font("Helvetica-Bold"),
                font_size=config.PDF_FONT_SIZE
            ))
            
            skills_text = ", ".join([clean_text(skill) for skill in skills])
            layout.add(Paragraph(
                skills_text,
                font=StandardType1Font("Helvetica"),
                font_size=config.PDF_FONT_SIZE - 1
            ))
            layout.add(Paragraph(" "))  # Spacing

def create_awards(layout: PageLayout, awards: List[Dict[str, Any]]) -> None:
    """Create the awards section."""
    if not awards:
        return
    
    create_section_heading(layout, "Awards & Achievements")
    
    for award in awards:
        title = clean_text(award.get("title", ""))
        issuer = clean_text(award.get("issuer", ""))
        date = clean_text(award.get("date", ""))
        
        header_text = title
        if issuer:
            header_text += f" • {issuer}"
        if date:
            header_text += f" • {date}"
        
        layout.add(Paragraph(
            header_text,
            font=StandardType1Font("Helvetica-Bold"),
            font_size=config.PDF_FONT_SIZE
        ))
        
        # Description if available
        if award.get("summary"):
            layout.add(Paragraph(
                clean_text(award["summary"]),
                font=StandardType1Font("Helvetica"),
                font_size=config.PDF_FONT_SIZE - 1
            ))
        
        layout.add(Paragraph(" "))  # Spacing

def create_certificates(layout: PageLayout, certificates: List[Dict[str, Any]]) -> None:
    """Create the certificates section."""
    if not certificates:
        return
    
    create_section_heading(layout, "Certifications")
    
    for cert in certificates:
        name = clean_text(cert.get("name", ""))
        issuer = clean_text(cert.get("issuer", ""))
        date = clean_text(cert.get("date", ""))
        
        header_text = name
        if issuer:
            header_text += f" • {issuer}"
        if date:
            header_text += f" • {date}"
        
        layout.add(Paragraph(
            header_text,
            font=StandardType1Font("Helvetica-Bold"),
            font_size=config.PDF_FONT_SIZE
        ))
        
        layout.add(Paragraph(" "))  # Spacing

def generate_pdf(data: Dict[str, Any]) -> Document:
    """Generate PDF document from resume data."""
    # Create document
    doc = Document()
    page = Page()
    doc.add_page(page)
    
    # Create layout
    layout = SingleColumnLayout(page)
    layout._margin_top = config.PDF_MARGIN
    layout._margin_bottom = config.PDF_MARGIN
    layout._margin_left = config.PDF_MARGIN
    layout._margin_right = config.PDF_MARGIN
    
    # Add content sections
    basics = data.get("basics", {})
    create_header(layout, basics)
    
    work = data.get("work", [])
    create_work_experience(layout, work)
    
    education = data.get("education", [])
    create_education(layout, education)
    
    projects = data.get("projects", [])
    create_projects(layout, projects)
    
    skills_by_category = data.get("skills_by_category", {})
    create_skills(layout, skills_by_category)
    
    awards = data.get("awards", [])
    create_awards(layout, awards)
    
    certificates = data.get("certificates", [])
    create_certificates(layout, certificates)
    
    return doc

# ───────────────────────────────────────────────────────── Main

def main() -> None:
    if not RESUME_JSON.exists():
        log.error(f"{config.RESUME_JSON_FILE} not found – aborting")
        sys.exit(1)

    log.info(f"Loading {config.RESUME_JSON_FILE}")
    data = json.loads(RESUME_JSON.read_text(encoding="utf-8"))

    log.info("Generating PDF with borb...")
    doc = generate_pdf(data)
    
    # Save PDF
    with open(PDF_OUT, "wb") as pdf_file_handle:
        PDF.dumps(pdf_file_handle, doc)
    
    log.info("PDF generated → %s", PDF_OUT.relative_to(ROOT))

if __name__ == "__main__":
    main() 