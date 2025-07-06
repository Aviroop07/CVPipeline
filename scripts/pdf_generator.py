#!/usr/bin/env python3
"""
PDF resume generation module.

This module provides functions to generate PDF resumes using the borb library.
"""

import json, os, pathlib, sys, logging
from typing import List, Dict, Any
import config
import dotenv

# borb imports for version 2.x
from borb.pdf import Document, Page, Paragraph, PDF
from borb.pdf.page_layout.multi_column_layout import MultiColumnLayout
from borb.pdf.page_layout.page_layout import PageLayout
from borb.pdf.layout_element.layout_element import LayoutElement
from borb.pdf.color.hex_color import HexColor
from borb.pdf.layout_element.text.chunk import Chunk as ChunkOfText
from borb.pdf.layout_element.text.heterogeneous_paragraph import HeterogeneousParagraph
from borb.pdf.layout_element.annotation.remote_go_to_annotation import RemoteGoToAnnotation

# Spacer function removed - no longer needed with 0 margins

Alignment = LayoutElement.HorizontalAlignment

def get_paragraph_kwargs(**kwargs):
    """Get paragraph kwargs with proper fixed_leading handling."""
    if config.PDF_PARAGRAPH_LEADING is not None:
        kwargs['fixed_leading'] = Decimal(config.PDF_PARAGRAPH_LEADING)
    return kwargs

def _tight(**kwargs):
    """
    Convenience wrapper: apply a fixed_leading equal to
    1.1 × font_size unless caller overrides.
    """
    font_size = float(kwargs.get("font_size", config.PDF_FONT_SIZE))
    kwargs.setdefault("fixed_leading", int(font_size * config.PDF_TIGHT_LEADING_MULT))
    return kwargs

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESUME_JSON = ROOT / config.RESUME_JSON_FILE
PDF_OUT = ROOT / config.RESUME_PDF_FILE

# Load environment variables from .env file if present
dotenv.load_dotenv()

# Initialise logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# borb 2.x expects plain int/float margins; use a no-op Decimal stub to keep old calls
def Decimal(x):
    return x

def clean_text(text: str) -> str:
    """Remove or replace special Unicode characters that can't be rendered in basic fonts.
    
    Args:
        text (str): Input text to clean
        
    Returns:
        str: Cleaned text with special characters replaced
    """
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

def create_header_section(layout: PageLayout, basics: Dict[str, Any]) -> None:
    """Create the header section with name, contact info, and links.
    
    Args:
        layout (PageLayout): Page layout to add content to
        basics (Dict): Basic information from resume data
    """
    # Name as title
    name = clean_text(basics.get("name", ""))
    layout.append_layout_element(Paragraph(
        name,
        font="Times-Bold",
        font_size=config.PDF_TITLE_FONT_SIZE,
        horizontal_alignment=Alignment.MIDDLE,
        margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
        margin_bottom=Decimal(2)  # Minimal gap to contact info
    ))
    
    # Contact information with LinkedIn hyperlink
    contact_chunks = []
    
    if basics.get("email"):
        contact_chunks.append(ChunkOfText(clean_text(basics["email"]),
                                        font="Times-Roman",
                                        font_size=config.PDF_FONT_SIZE))
    
    if basics.get("phone"):
        if contact_chunks:
            contact_chunks.append(ChunkOfText(" | ",
                                            font="Times-Roman",
                                            font_size=config.PDF_FONT_SIZE))
        contact_chunks.append(ChunkOfText(clean_text(basics["phone"]),
                                        font="Times-Roman",
                                        font_size=config.PDF_FONT_SIZE))
    
    if basics.get("location"):
        if contact_chunks:
            contact_chunks.append(ChunkOfText(" | ",
                                            font="Times-Roman",
                                            font_size=config.PDF_FONT_SIZE))
        contact_chunks.append(ChunkOfText(clean_text(basics["location"]),
                                        font="Times-Roman",
                                        font_size=config.PDF_FONT_SIZE))
    
    # Add LinkedIn link if public_id is available
    linkedin_chunk = None
    if basics.get("public_id"):
        if contact_chunks:
            contact_chunks.append(ChunkOfText(" | ",
                                            font="Times-Roman",
                                            font_size=config.PDF_FONT_SIZE))
        linkedin_chunk = ChunkOfText("LinkedIn",
                                   font="Times-Roman",
                                   font_size=config.PDF_FONT_SIZE,
                                   font_color=HexColor("0066CC"))
        contact_chunks.append(linkedin_chunk)
    
    if contact_chunks:
        contact_para = HeterogeneousParagraph(
            contact_chunks,
            horizontal_alignment=Alignment.MIDDLE,
            margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
            margin_bottom=Decimal(config.PDF_HEADER_MARGIN_BOTTOM)
        )
        layout.append_layout_element(contact_para)
        
        # Add hyperlink annotation to LinkedIn chunk
        # Hyperlink annotations temporarily disabled due to borb API changes
        # linkedin_url = f"https://www.linkedin.com/in/{basics['public_id']}"
        # rect = linkedin_chunk.get_previous_paint_box()
        # layout._page.add_annotation(RemoteGoToAnnotation(rect, linkedin_url))
    
    # Links
    if basics.get("profiles"):
        links = []
        for profile in basics["profiles"]:
            if profile.get("url"):
                links.append(profile["url"])
        if links:
            layout.append_layout_element(Paragraph(
                " | ".join(links),
                font="Times-Roman",
                font_size=config.PDF_FONT_SIZE - 1,
                horizontal_alignment=Alignment.MIDDLE,
                margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                margin_bottom=Decimal(config.PDF_PARAGRAPH_MARGIN_BOTTOM)
            ))

def create_section_heading(layout: PageLayout, title: str, is_first_section: bool = False) -> None:
    """Create a section heading with controlled spacing.
    
    Args:
        layout (PageLayout): Page layout to add content to
        title (str): Section title
        is_first_section (bool): Whether this is the first content section
    """
    # Use different margins for first section vs subsequent sections
    margin_top = Decimal(config.PDF_ELEMENT_MARGIN_TOP if is_first_section else config.PDF_SECTION_MARGIN_TOP)
    
    layout.append_layout_element(Paragraph(
        title.upper(),
        font="Times-Bold",
        font_size=config.PDF_HEADING_FONT_SIZE,
        horizontal_alignment=Alignment.LEFT,
        margin_top=margin_top,
        margin_bottom=Decimal(config.PDF_SECTION_MARGIN_BOTTOM)
    ))

def create_work_experience_section(layout: PageLayout, work: List[Dict[str, Any]], is_first_section: bool = False) -> None:
    """Create the work experience section.
    
    Args:
        layout (PageLayout): Page layout to add content to
        work (List[Dict]): Work experience data
        is_first_section (bool): Whether this is the first content section
    """
    if not work:
        return
    
    create_section_heading(layout, "Professional Experience", is_first_section=is_first_section)
    
    for i, job in enumerate(work):
        # Job header: Company Name (bold, ink blue) | Position (non-bold, black) | Period (italics, non-bold, black)
        company = clean_text(job.get("name", ""))
        position = clean_text(job.get("position", ""))
        period = clean_text(job.get("period", ""))
        company_url = job.get("url", "")
        
        # Build header with hyperlinked company name if URL available
        header_chunks = []
        company_chunk = None
        
        if company:
            if company_url:
                # Make company name clickable (bold, ink blue)
                company_chunk = ChunkOfText(company,
                                          font="Times-Bold",
                                          font_size=config.PDF_FONT_SIZE,
                                          font_color=HexColor("0066CC"))
            else:
                # Regular company name (bold, ink blue)
                company_chunk = ChunkOfText(company,
                                          font="Times-Bold",
                                          font_size=config.PDF_FONT_SIZE,
                                          font_color=HexColor("0066CC"))
            header_chunks.append(company_chunk)
        
        if position:
            if header_chunks:
                header_chunks.append(ChunkOfText(" | ",
                                               font="Times-Roman",
                                               font_size=config.PDF_FONT_SIZE))
            header_chunks.append(ChunkOfText(position,
                                           font="Times-Roman",
                                           font_size=config.PDF_FONT_SIZE))
        
        if period:
            if header_chunks:
                header_chunks.append(ChunkOfText(" | ",
                                               font="Times-Roman",
                                               font_size=config.PDF_FONT_SIZE))
            header_chunks.append(ChunkOfText(period,
                                           font="Times-Italic",
                                           font_size=config.PDF_FONT_SIZE))
        
        # Determine if this is the last job in the list
        is_last_job = (i == len(work) - 1)
        item_margin_bottom = Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM if is_last_job else config.PDF_ITEM_MARGIN_BOTTOM)
        
        if header_chunks:
            header_para = HeterogeneousParagraph(
                header_chunks,
                margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                margin_bottom=Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM)
            )
            layout.append_layout_element(header_para)
            
            # Add hyperlink annotation to company chunk if URL available
            # if company_chunk and company_url:
            #     rect = company_chunk.get_previous_paint_box()
            #     layout._page.add_annotation(RemoteGoToAnnotation(rect, company_url))
        
        # Description/summary as regular paragraph (more compact than bullet points)
        summary = clean_text(job.get("summary", ""))
        if summary:
            layout.append_layout_element(Paragraph(
                summary,
                **_tight(
                    font="Times-Roman",
                    font_size=config.PDF_FONT_SIZE - 1,
                    margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                    margin_bottom=item_margin_bottom
                )
            ))
        
        # If there are processed bullet points, show them as well
        points = job.get("points", [])
        if points and not summary:  # Only show points if no summary
            for j, point in enumerate(points):
                is_last_point = (j == len(points) - 1)
                point_margin_bottom = item_margin_bottom if is_last_point else Decimal(config.PDF_BULLET_MARGIN_BOTTOM)
                
                layout.append_layout_element(Paragraph(
                    f"• {clean_text(point)}",
                    **_tight(
                        font="Times-Roman",
                        font_size=config.PDF_FONT_SIZE - 1,
                        margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                        margin_bottom=point_margin_bottom
                    )
                ))

def create_education_section(layout: PageLayout, education: List[Dict[str, Any]], is_first_section: bool = False) -> None:
    """Create the education section.
    
    Args:
        layout (PageLayout): Page layout to add content to
        education (List[Dict]): Education data
        is_first_section (bool): Whether this is the first content section
    """
    if not education:
        return
    
    create_section_heading(layout, "Education", is_first_section=is_first_section)
    
    for i, edu in enumerate(education):
        # Education header: Institution (bold, ink blue) | Degree (non-bold, black) | Period (italics, non-bold, black)
        degree = clean_text(edu.get("studyType", ""))
        field = clean_text(edu.get("area", ""))
        institution = clean_text(edu.get("institution", ""))
        period = clean_text(edu.get("period", ""))
        school_url = edu.get("url", "")
        
        # Build degree with field
        degree_text = degree
        if field:
            degree_text += f" in {field}"
        
        # Build header with hyperlinked institution name if URL available
        header_chunks = []
        institution_chunk = None
        
        if institution:
            if school_url:
                # Make institution name clickable (bold, ink blue)
                institution_chunk = ChunkOfText(institution,
                                              font="Times-Bold",
                                              font_size=config.PDF_FONT_SIZE,
                                              font_color=HexColor("0066CC"))
            else:
                # Regular institution name (bold, ink blue)
                institution_chunk = ChunkOfText(institution,
                                              font="Times-Bold",
                                              font_size=config.PDF_FONT_SIZE,
                                              font_color=HexColor("0066CC"))
            header_chunks.append(institution_chunk)
        
        if degree_text:
            if header_chunks:
                header_chunks.append(ChunkOfText(" | ",
                                               font="Times-Roman",
                                               font_size=config.PDF_FONT_SIZE))
            header_chunks.append(ChunkOfText(degree_text,
                                           font="Times-Roman",
                                           font_size=config.PDF_FONT_SIZE))
        
        if period:
            if header_chunks:
                header_chunks.append(ChunkOfText(" | ",
                                               font="Times-Roman",
                                               font_size=config.PDF_FONT_SIZE))
            header_chunks.append(ChunkOfText(period,
                                           font="Times-Italic",
                                           font_size=config.PDF_FONT_SIZE))
        
        if header_chunks:
            header_para = HeterogeneousParagraph(
                header_chunks,
                margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                margin_bottom=Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM)
            )
            layout.append_layout_element(header_para)
            
            # Add hyperlink annotation to institution chunk if URL available
            # if institution_chunk and school_url:
            #     rect = institution_chunk.get_previous_paint_box()
            #     layout._page.add_annotation(RemoteGoToAnnotation(rect, school_url))
        
        # Determine if this is the last education item
        is_last_edu = (i == len(education) - 1)
        
        # GPA/Score on a new line if available
        if edu.get("score"):
            item_margin_bottom = Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM if is_last_edu else config.PDF_ITEM_MARGIN_BOTTOM)
            layout.append_layout_element(Paragraph(
                f"GPA: {clean_text(edu['score'])}",
                font="Times-Roman",
                font_size=config.PDF_FONT_SIZE - 1,
                margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                margin_bottom=item_margin_bottom
            ))
        # No additional spacing needed - margins handle this automatically

def create_projects_section(layout: PageLayout, projects: List[Dict[str, Any]], is_first_section: bool = False) -> None:
    """Create the projects section.
    
    Args:
        layout (PageLayout): Page layout to add content to
        projects (List[Dict]): Projects data
        is_first_section (bool): Whether this is the first content section
    """
    if not projects:
        return
    
    create_section_heading(layout, "Projects", is_first_section=is_first_section)
    
    for i, project in enumerate(projects):
        # Project header: Name (bold, ink blue if URL available) | Period (italics, non-bold, black)
        name = clean_text(project.get("name", ""))
        period = clean_text(project.get("period", ""))
        project_url = project.get("url", "")
        
        # Build header with hyperlinked project name if URL available
        header_chunks = []
        name_chunk = None
        
        if name:
            if project_url:
                # Create clickable project name (bold, ink blue)
                name_chunk = ChunkOfText(name,
                                       font="Times-Bold",
                                       font_size=config.PDF_FONT_SIZE,
                                       font_color=HexColor("0066CC"))
            else:
                # Regular project name (bold, black)
                name_chunk = ChunkOfText(name,
                                       font="Times-Bold",
                                       font_size=config.PDF_FONT_SIZE)
            header_chunks.append(name_chunk)
        
        if period:
            if header_chunks:
                header_chunks.append(ChunkOfText(" | ",
                                               font="Times-Roman",
                                               font_size=config.PDF_FONT_SIZE))
            header_chunks.append(ChunkOfText(period,
                                           font="Times-Italic",
                                           font_size=config.PDF_FONT_SIZE))
        
        if header_chunks:
            header_para = HeterogeneousParagraph(
                header_chunks,
                margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                margin_bottom=Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM)
            )
            layout.append_layout_element(header_para)
            
            # Add hyperlink annotation to project name if URL available
            # if name_chunk and project_url:
            #     rect = name_chunk.get_previous_paint_box()
            #     layout._page.add_annotation(RemoteGoToAnnotation(rect, project_url))
        
        # Determine if this is the last project
        is_last_project = (i == len(projects) - 1)
        item_margin_bottom = Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM if is_last_project else config.PDF_ITEM_MARGIN_BOTTOM)
        
        # Description as regular paragraph (more compact than bullet points)
        description = clean_text(project.get("description", ""))
        if description:
            layout.append_layout_element(Paragraph(
                description,
                **_tight(
                    font="Times-Roman",
                    font_size=config.PDF_FONT_SIZE - 1,
                    margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                    margin_bottom=item_margin_bottom
                )
            ))
        
        # If there are processed bullet points, show them as well
        points = project.get("points", [])
        if points and not description:  # Only show points if no description
            for j, point in enumerate(points):
                is_last_point = (j == len(points) - 1)
                point_margin_bottom = item_margin_bottom if is_last_point else Decimal(config.PDF_BULLET_MARGIN_BOTTOM)
                
                layout.append_layout_element(Paragraph(
                    f"• {clean_text(point)}",
                    **_tight(
                        font="Times-Roman",
                        font_size=config.PDF_FONT_SIZE - 1,
                        margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                        margin_bottom=point_margin_bottom
                    )
                ))

def create_skills_section(layout: PageLayout, skills_by_category: Dict[str, List[str]], is_first_section: bool = False) -> None:
    """Create the skills section.
    
    Args:
        layout (PageLayout): Page layout to add content to
        skills_by_category (Dict[str, List[str]]): Skills grouped by category
        is_first_section (bool): Whether this is the first content section
    """
    if not skills_by_category:
        return
    
    create_section_heading(layout, "Skills", is_first_section=is_first_section)
    
    categories = list(skills_by_category.items())
    for i, (category, skills) in enumerate(categories):
        if skills:
            # Create single line: Category (bold): skills list (non-bold)
            skills_text = ", ".join([clean_text(skill) for skill in skills])
            
            skill_chunks = [
                ChunkOfText(f"{category}: ",
                          font="Times-Bold",
                          font_size=config.PDF_FONT_SIZE),
                ChunkOfText(skills_text,
                          font="Times-Roman",
                          font_size=config.PDF_FONT_SIZE)
            ]
            
            # Determine if this is the last skill category
            is_last_category = (i == len(categories) - 1)
            margin_bottom = Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM if is_last_category else config.PDF_PARAGRAPH_MARGIN_BOTTOM)
            
            skill_para = HeterogeneousParagraph(
                skill_chunks,
                margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                margin_bottom=margin_bottom
            )
            layout.append_layout_element(skill_para)

def create_awards_section(layout: PageLayout, awards: List[Dict[str, Any]], is_first_section: bool = False) -> None:
    """Create the awards section.
    
    Args:
        layout (PageLayout): Page layout to add content to
        awards (List[Dict]): Awards data
        is_first_section (bool): Whether this is the first content section
    """
    if not awards:
        return
    
    create_section_heading(layout, "Awards & Achievements", is_first_section=is_first_section)
    
    for i, award in enumerate(awards):
        title = clean_text(award.get("title", ""))
        issuer = clean_text(award.get("issuer", ""))
        date = clean_text(award.get("date", ""))
        
        # Build header with title and date on same line
        header_chunks = []
        
        # Award title (bold, black)
        if title:
            header_text = title
            if issuer:
                header_text += f" • {issuer}"
            header_chunks.append(ChunkOfText(header_text,
                                           font="Times-Bold",
                                           font_size=config.PDF_FONT_SIZE))
        
        # Date (italics, non-bold, black) on same line
        if date:
            if header_chunks:
                header_chunks.append(ChunkOfText(" | ",
                                               font="Times-Roman",
                                               font_size=config.PDF_FONT_SIZE))
            header_chunks.append(ChunkOfText(date,
                                           font="Times-Italic",
                                           font_size=config.PDF_FONT_SIZE))
        
        # Determine if this is the last award
        is_last_award = (i == len(awards) - 1)
        
        if header_chunks:
            header_margin_bottom = Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM)
            if award.get("summary"):
                # If there's a summary, use less margin after header
                header_margin_bottom = Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM)
            elif not is_last_award:
                # No summary but not last award, use item spacing
                header_margin_bottom = Decimal(config.PDF_ITEM_MARGIN_BOTTOM)
            
            header_para = HeterogeneousParagraph(
                header_chunks,
                margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                margin_bottom=header_margin_bottom
            )
            layout.append_layout_element(header_para)
        
        # Description/summary on next line if available
        if award.get("summary"):
            item_margin_bottom = Decimal(config.PDF_ELEMENT_MARGIN_BOTTOM if is_last_award else config.PDF_ITEM_MARGIN_BOTTOM)
            layout.append_layout_element(Paragraph(
                clean_text(award["summary"]),
                font="Times-Roman",
                font_size=config.PDF_FONT_SIZE - 1,
                margin_top=Decimal(config.PDF_ELEMENT_MARGIN_TOP),
                margin_bottom=item_margin_bottom
            ))

def create_pdf_document(data: Dict[str, Any]) -> Document:
    """Generate PDF document from resume data.
    
    Args:
        data (Dict): Resume data in JSON-Resume format
        
    Returns:
        Document: Generated PDF document
    """
    # Create document
    doc = Document()
    page = Page()
    doc.append_page(page)
    
    # Create layout with required margins (single-column)
    layout = MultiColumnLayout(
        page,
        number_of_columns=1,
        margin_top=Decimal(config.PDF_MARGIN_TOP),
        margin_right=Decimal(config.PDF_MARGIN_RIGHT),
        margin_bottom=Decimal(config.PDF_MARGIN_BOTTOM),
        margin_left=Decimal(config.PDF_MARGIN_LEFT)
    )
    
    # Add content sections
    basics = data.get("basics", {})
    create_header_section(layout, basics)
    
    # Track if this is the first content section
    first_section = True
    
    work = data.get("work", [])
    if work:
        create_work_experience_section(layout, work, is_first_section=first_section)
        first_section = False
    
    education = data.get("education", [])
    if education:
        create_education_section(layout, education, is_first_section=first_section)
        first_section = False
    
    projects = data.get("projects", [])
    if projects:
        create_projects_section(layout, projects, is_first_section=first_section)
        first_section = False
    
    skills_by_category = data.get("skills_by_category", {})
    if skills_by_category:
        create_skills_section(layout, skills_by_category, is_first_section=first_section)
        first_section = False
    
    awards = data.get("awards", [])
    if awards:
        create_awards_section(layout, awards, is_first_section=first_section)
        first_section = False
    
    return doc

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

def save_pdf_document(doc: Document, output_path=None):
    """Save PDF document to file.
    
    Args:
        doc (Document): PDF document to save
        output_path (pathlib.Path, optional): Custom output path. Defaults to configured path.
        
    Returns:
        pathlib.Path: Path where PDF was saved
    """
    if output_path is None:
        output_path = PDF_OUT

    # borb 2.x expects a pathlib.Path or str for where_to; passing a raw file handle
    # results in an empty PDF. Provide the path directly so borb can manage the file.
    PDF.write(what=doc, where_to=output_path)

    log.info("PDF generated → %s", output_path.relative_to(ROOT))
    return output_path

def generate_pdf_resume():
    """Complete PDF generation pipeline.
    
    Returns:
        pathlib.Path: Path to generated PDF file
        
    Raises:
        SystemExit: If generation fails
    """
    # Load resume data
    data = load_resume_data()

    log.info("Generating PDF with borb...")
    
    # Generate PDF document
    doc = create_pdf_document(data)
    
    # Save PDF
    output_path = save_pdf_document(doc)
    
    return output_path

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    generate_pdf_resume()

if __name__ == "__main__":
    main() 