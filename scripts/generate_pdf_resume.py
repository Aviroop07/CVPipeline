#!/usr/bin/env python3
"""
Generate PDF version of the résumé directly using borb.

Steps:
1. Load resume.json (JSON-Resume 1.0 structure).
2. Refine list-based sections via the OpenAI API (if OPENAI_API_KEY is set).
3. Generate PDF directly using borb library.

Usage:
    python scripts/generate_pdf_resume.py

Outputs:
    Aviroop_Mitra_Resume.pdf
"""

from __future__ import annotations

import json, os, pathlib, sys, datetime as _dt, re, logging
from typing import List, Dict, Any
from string import Template as StrTemplate
import config
import dotenv

# borb imports
from borb.pdf import Document, Page, Paragraph
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.page_layout.page_layout import PageLayout
from borb.pdf.canvas.layout.text.paragraph import Paragraph
from borb.pdf.canvas.layout.list.unordered_list import UnorderedList
from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.font.font import Font
from borb.pdf import PDF

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESUME_JSON = ROOT / config.RESUME_JSON_FILE
PDF_OUT = ROOT / config.RESUME_PDF_FILE

PROMPTS_DIR = ROOT / config.PROMPTS_DIR

# Load environment variables from .env file if present
dotenv.load_dotenv()

# Initialise logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Utility to load a prompt template and fill placeholders
def _load_prompt(name: str, **kwargs) -> str:
    tpl_path = PROMPTS_DIR / name
    if not tpl_path.exists():
        raise FileNotFoundError(f"Prompt template {tpl_path} not found")
    template_text = tpl_path.read_text(encoding="utf-8")
    return StrTemplate(template_text).substitute(**kwargs)

# ───────────────────────────────────────────────────────── Helpers

def _chronological(items: List[Dict[str, Any]], date_key: str) -> List[Dict[str, Any]]:
    """Return *items* sorted descending by *date_key* (YYYY-MM or YYYY)."""
    def _key(it):
        date = it.get(date_key)
        return date or ""
    return sorted(items, key=_key, reverse=True)

def _openai_chat(prompt: str) -> str:
    """Send *prompt* to OpenAI chat if API key available, else return empty string."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.debug("OPENAI_API_KEY not set – skipping call")
        return ""
    try:
        from openai import OpenAI  # requires openai >= 1.x
        log.debug("Calling OpenAI with %d chars prompt", len(prompt))
        log.debug("OpenAI prompt (%d chars): %s", len(prompt), prompt[:500])

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "developer", "content": prompt}],
            temperature=config.OPENAI_TEMPERATURE,
            reasoning_effort=config.OPENAI_REASONING_EFFORT
        )

        result = response.choices[0].message.content.strip()
        log.debug("OpenAI response received (%d chars)", len(result))
        log.debug("OpenAI response: %s", result)
        return result
    except Exception as exc:
        log.warning("OpenAI call failed: %s", exc)
        return ""

def _rank_list_openai(items: List[str], section: str) -> List[str]:
    """
    Ask GPT-4 to rank & cull items for the given section.
    Returns the reordered list; falls back to original on error.
    """
    if not items:
        return items

    prompt = _load_prompt(
        config.RANK_ITEMS_PROMPT,
        section_name=section,
        items_list=", ".join(items)
    )
    ranked_json = _openai_chat(prompt)
    if not ranked_json:
        return items

    try:
        ranked = json.loads(ranked_json)
        # Preserve all original items: ranked order first, then any missing ones
        ordered = [it for it in ranked if it in items]
        for it in items:
            if it not in ordered:
                ordered.append(it)
        return ordered
    except Exception as exc:
        print(f"⚠️  Failed to parse ranked {section}: {exc}", file=sys.stderr)
        return items

def _reorder_objects(obj_list: List[Dict[str, Any]], key: str, section: str) -> List[Dict[str, Any]]:
    """Reorder objects based on OpenAI-ranked keys."""
    order = _rank_list_openai([o[key] for o in obj_list], section)
    ordered = [next(o for o in obj_list if o[key] == name) for name in order]
    return ordered

def _categorize_skills_openai(skills: List[str]) -> Dict[str, List[str]]:
    if not skills:
        return {}
    prompt = _load_prompt(config.CATEGORIZE_SKILLS_PROMPT, skills_list=", ".join(skills))
    log.info("Categorizing %d skills via OpenAI", len(skills))
    response = _openai_chat(prompt)
    log.debug("Skill categorization raw response: %s", response)
    if not response:
        return {}
    # Ensure we only take JSON object from response
    try:
        json_text = re.search(r"\{.*\}", response, re.S).group(0)
        categories = json.loads(json_text)
        log.info("Received %d skill categories", len(categories))
        log.debug("Categories: %s", categories)
        return categories
    except Exception as exc:
        log.warning("Failed to parse skill categorization JSON: %s", exc)
        return {}

def _filter_skills_openai(skills: List[str]) -> List[str]:
    """Return a subset of *skills* deemed résumé-worthy via OpenAI prompt."""
    if not skills:
        return skills

    prompt = _load_prompt(config.FILTER_SKILLS_PROMPT, skills_list=", ".join(skills))
    log.info("Filtering %d skills via OpenAI", len(skills))
    response = _openai_chat(prompt)
    log.debug("Skill filtering raw response: %s", response)
    if not response:
        return skills

    try:
        json_text = re.search(r"\[.*\]", response, re.S).group(0)
        kept = json.loads(json_text)
        # Ensure only skills present in the original list are kept (order preserved as in original)
        filtered = [s for s in skills if s in kept]
        log.info("Kept %d/%d skills after filtering", len(filtered), len(skills))
        return filtered if filtered else skills
    except Exception as exc:
        log.warning("Failed to parse filtered skills JSON: %s", exc)
        return skills

def _extract_points(text: str) -> List[str]:
    """Return list of bullet-point strings extracted from *text* (may call OpenAI)."""
    if not text:
        return []

    # If already contains newline/bullets, split heuristically
    if "\n" in text or "•" in text:
        raw_parts = re.split(r"[\n•]\s*", text)
        parts = [p.strip(" •-\t") for p in raw_parts if p.strip()]
        return parts

    # If sentence longer than POINT_WORD_THRESHOLD words, ask OpenAI to break down
    word_count = len(text.split())
    if word_count < config.POINT_WORD_THRESHOLD:
        return [text.strip()]

    prompt = _load_prompt(config.EXTRACT_POINTS_PROMPT, raw_text=text)
    log.info("Requesting point extraction (%d words) via OpenAI", word_count)
    resp = _openai_chat(prompt)
    log.debug("Point extraction raw response: %s", resp)
    try:
        points = json.loads(resp)
        return points if isinstance(points, list) else [text]
    except Exception as exc:
        log.warning("Failed to parse points JSON: %s", exc)
        return [text]

def _fmt_range(start: str|None, end: str|None) -> str:
    """Convert 'YYYY-MM' strings to nice range."""
    if not start:
        return ""
    try:
        ys, ms = start.split("-")
        ms = int(ms)
        ys_int = int(ys)
        sm = config.MONTHS[ms-1]
    except Exception:
        return start

    if end:
        try:
            ye, me = end.split("-")
            me = int(me)
            ye_int = int(ye)
            em = config.MONTHS[me-1]
        except Exception:
            return f"{sm}, {ys} – {end}"

        if ys_int == ye_int:
            return f"{sm} – {em}, {ys}"
        return f"{sm}, {ys} – {em}, {ye}"
    else:
        return f"{sm}, {ys} – Present"

def _fmt_single(date: str|None) -> str:
    """Convert 'YYYY-MM' (or 'YYYY') to 'Mon, YYYY'. Returns empty string on failure."""
    if not date:
        return ""
    try:
        if "-" in date:
            y, m = date.split("-")
            m_int = int(m)
            month = config.MONTHS[m_int-1]
            return f"{month}, {y}"
        # only year provided
        return date
    except Exception:
        return date

def preprocess(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply transformations & OpenAI enhancements keeping structure."""
    # Chronological ordering (latest first)
    data["work"] = _chronological(data.get("work", []), "startDate")
    data["education"] = _chronological(data.get("education", []), "startDate")
    data["projects"] = _chronological(data.get("projects", []), "startDate")
    data["awards"] = _chronological(data.get("awards", []), "date")
    data["certificates"] = _chronological(data.get("certificates", []), "date")

    # Ensure summary is empty (ignored)
    data["basics"]["summary"] = ""

    # Convert work summaries/descriptions to point lists
    for w in data.get("work", []):
        w["points"] = _extract_points(w.get("summary", ""))
        w["period"] = _fmt_range(w.get("startDate"), w.get("endDate"))

    for p in data.get("projects", []):
        p["points"] = _extract_points(p.get("description", ""))
        p["period"] = _fmt_range(p.get("startDate"), p.get("endDate"))

    for e in data.get("education", []):
        e["period"] = _fmt_range(e.get("startDate"), e.get("endDate"))

    # Format single-date fields (awards, certificates)
    for a in data.get("awards", []):
        a["date"] = _fmt_single(a.get("date"))

    for c in data.get("certificates", []):
        c["date"] = _fmt_single(c.get("date"))

    # Categorise skills into buckets based on keywords
    skill_names = [s["name"] for s in data.get("skills", [])]

    # Step 1: filter skills for relevance via OpenAI
    filtered_skills = _filter_skills_openai(skill_names)

    # Step 2: categorise the filtered skills
    categorized = _categorize_skills_openai(filtered_skills)
    if not categorized:
        # Fallback: put all skills under "General"
        categorized = {"General": filtered_skills}

    data["skills_by_category"] = categorized

    # Replace original skills list with filtered list so downstream templates (if any) stay in sync
    data["skills"] = [{"name": s} for s in filtered_skills]

    # Reorder sections based on relevance
    data["projects"] = _reorder_objects(data["projects"], "name", "Projects")
    data["awards"] = _reorder_objects(data["awards"], "title", "Achievements")
    data["work"] = _reorder_objects(data["work"], "position", "Work Experience")

    log.debug("Data after preprocessing keys: %s", list(data.keys()))

    return data

# ───────────────────────────────────────────────────────── PDF Generation

def create_header(layout: PageLayout, basics: Dict[str, Any]) -> None:
    """Create the header section with name, contact info, and links."""
    # Name as title
    name = basics.get("name", "")
    layout.add(Paragraph(
        name,
        font=Font.helvetica_bold(),
        font_size=config.PDF_TITLE_FONT_SIZE,
        text_alignment="CENTER"
    ))
    
    # Contact information
    contact_info = []
    if basics.get("email"):
        contact_info.append(basics["email"])
    if basics.get("phone"):
        contact_info.append(basics["phone"])
    if basics.get("location", {}).get("city"):
        location = basics["location"]
        location_str = f"{location.get('city', '')}, {location.get('region', '')}"
        contact_info.append(location_str)
    
    if contact_info:
        layout.add(Paragraph(
            " | ".join(contact_info),
            font=Font.helvetica(),
            font_size=config.PDF_FONT_SIZE,
            text_alignment="CENTER"
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
                font=Font.helvetica(),
                font_size=config.PDF_FONT_SIZE - 1,
                text_alignment="CENTER"
            ))
    
    layout.add(Paragraph(" "))  # Spacing

def create_section_heading(layout: PageLayout, title: str) -> None:
    """Create a section heading."""
    layout.add(Paragraph(
        title.upper(),
        font=Font.helvetica_bold(),
        font_size=config.PDF_HEADING_FONT_SIZE,
        text_alignment="LEFT"
    ))
    layout.add(Paragraph(" "))  # Spacing

def create_work_experience(layout: PageLayout, work: List[Dict[str, Any]]) -> None:
    """Create the work experience section."""
    if not work:
        return
    
    create_section_heading(layout, "Professional Experience")
    
    for job in work:
        # Job header: Position at Company
        position = job.get("position", "")
        company = job.get("name", "")
        period = job.get("period", "")
        
        header_text = f"{position}"
        if company:
            header_text += f" at {company}"
        if period:
            header_text += f" • {period}"
        
        layout.add(Paragraph(
            header_text,
            font=Font.helvetica_bold(),
            font_size=config.PDF_FONT_SIZE
        ))
        
        # Company URL if available
        if job.get("url"):
            layout.add(Paragraph(
                job["url"],
                font=Font.helvetica(),
                font_size=config.PDF_FONT_SIZE - 1,
                text_color=HexColor("0066CC")
            ))
        
        # Bullet points
        points = job.get("points", [])
        if points:
            bullet_list = []
            for point in points:
                bullet_list.append(Paragraph(
                    point,
                    font=Font.helvetica(),
                    font_size=config.PDF_FONT_SIZE - 1
                ))
            layout.add(UnorderedList(*bullet_list))
        
        layout.add(Paragraph(" "))  # Spacing between jobs

def create_education(layout: PageLayout, education: List[Dict[str, Any]]) -> None:
    """Create the education section."""
    if not education:
        return
    
    create_section_heading(layout, "Education")
    
    for edu in education:
        # Education header: Degree at Institution
        degree = edu.get("studyType", "")
        field = edu.get("area", "")
        institution = edu.get("institution", "")
        period = edu.get("period", "")
        
        header_text = f"{degree}"
        if field:
            header_text += f" in {field}"
        if institution:
            header_text += f" • {institution}"
        if period:
            header_text += f" • {period}"
        
        layout.add(Paragraph(
            header_text,
            font=Font.helvetica_bold(),
            font_size=config.PDF_FONT_SIZE
        ))
        
        # GPA if available
        if edu.get("score"):
            layout.add(Paragraph(
                f"GPA: {edu['score']}",
                font=Font.helvetica(),
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
        name = project.get("name", "")
        period = project.get("period", "")
        
        header_text = name
        if period:
            header_text += f" • {period}"
        
        layout.add(Paragraph(
            header_text,
            font=Font.helvetica_bold(),
            font_size=config.PDF_FONT_SIZE
        ))
        
        # Project URL if available
        if project.get("url"):
            layout.add(Paragraph(
                project["url"],
                font=Font.helvetica(),
                font_size=config.PDF_FONT_SIZE - 1,
                text_color=HexColor("0066CC")
            ))
        
        # Description
        description = project.get("description", "")
        if description:
            layout.add(Paragraph(
                description,
                font=Font.helvetica(),
                font_size=config.PDF_FONT_SIZE - 1
            ))
        
        # Bullet points
        points = project.get("points", [])
        if points:
            bullet_list = []
            for point in points:
                bullet_list.append(Paragraph(
                    point,
                    font=Font.helvetica(),
                    font_size=config.PDF_FONT_SIZE - 1
                ))
            layout.add(UnorderedList(*bullet_list))
        
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
                font=Font.helvetica_bold(),
                font_size=config.PDF_FONT_SIZE
            ))
            
            skills_text = ", ".join(skills)
            layout.add(Paragraph(
                skills_text,
                font=Font.helvetica(),
                font_size=config.PDF_FONT_SIZE - 1
            ))
            layout.add(Paragraph(" "))  # Spacing

def create_awards(layout: PageLayout, awards: List[Dict[str, Any]]) -> None:
    """Create the awards section."""
    if not awards:
        return
    
    create_section_heading(layout, "Awards & Achievements")
    
    for award in awards:
        title = award.get("title", "")
        issuer = award.get("issuer", "")
        date = award.get("date", "")
        
        header_text = title
        if issuer:
            header_text += f" • {issuer}"
        if date:
            header_text += f" • {date}"
        
        layout.add(Paragraph(
            header_text,
            font=Font.helvetica_bold(),
            font_size=config.PDF_FONT_SIZE
        ))
        
        # Description if available
        if award.get("summary"):
            layout.add(Paragraph(
                award["summary"],
                font=Font.helvetica(),
                font_size=config.PDF_FONT_SIZE - 1
            ))
        
        layout.add(Paragraph(" "))  # Spacing

def create_certificates(layout: PageLayout, certificates: List[Dict[str, Any]]) -> None:
    """Create the certificates section."""
    if not certificates:
        return
    
    create_section_heading(layout, "Certifications")
    
    for cert in certificates:
        name = cert.get("name", "")
        issuer = cert.get("issuer", "")
        date = cert.get("date", "")
        
        header_text = name
        if issuer:
            header_text += f" • {issuer}"
        if date:
            header_text += f" • {date}"
        
        layout.add(Paragraph(
            header_text,
            font=Font.helvetica_bold(),
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
    data = preprocess(data)

    log.info("Generating PDF with borb...")
    doc = generate_pdf(data)
    
    # Save PDF
    with open(PDF_OUT, "wb") as pdf_file_handle:
        PDF.dumps(pdf_file_handle, doc)
    
    log.info("PDF generated → %s", PDF_OUT.relative_to(ROOT))

if __name__ == "__main__":
    main() 