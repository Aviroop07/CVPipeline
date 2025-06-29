#!/usr/bin/env python3
"""
Generate markdown and PDF versions of the résumé.

Steps:
1. Load resume.json (JSON-Resume 1.0 structure).
2. Refine list-based sections via the OpenAI API (if OPENAI_API_KEY is set).
3. Render a Markdown file using a static Jinja2 template.
4. Convert the Markdown to PDF using pandoc (must be available on PATH).

Usage:
    python scripts/generate_markdown_resume.py

Outputs:
    resume.md
    Aviroop_Mitra_Resume.pdf
"""

from __future__ import annotations

import json, os, pathlib, subprocess, sys, datetime as _dt, re, logging
from typing import List, Dict, Any
from jinja2 import Template
from string import Template as StrTemplate
import config
import dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESUME_JSON = ROOT / "resume.json"
MD_OUT = ROOT / "resume.md"
PDF_OUT = ROOT / "Aviroop_Mitra_Resume.pdf"

PROMPTS_DIR = ROOT / "prompts"

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

# Load Jinja2 markdown template from external file
TEMPLATE = Template((ROOT / "templates" / "resume.md.j2").read_text(encoding="utf-8"))

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
        "rank_items.txt",
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
    prompt = _load_prompt("categorize_skills.txt", skills_list=", ".join(skills))
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

# New: filter skills before categorization
def _filter_skills_openai(skills: List[str]) -> List[str]:
    """Return a subset of *skills* deemed résumé-worthy via OpenAI prompt."""
    if not skills:
        return skills

    prompt = _load_prompt("filter_skills.txt", skills_list=", ".join(skills))
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

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

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

    prompt = _load_prompt("extract_points.txt", raw_text=text)
    log.info("Requesting point extraction (%d words) via OpenAI", word_count)
    resp = _openai_chat(prompt)
    log.debug("Point extraction raw response: %s", resp)
    try:
        points = json.loads(resp)
        return points if isinstance(points, list) else [text]
    except Exception as exc:
        log.warning("Failed to parse points JSON: %s", exc)
        return [text]

# -------- date range helper ---------

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

# -------- single date helper ---------

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

# ───────────────────────────────────────────────────────── Main

def main() -> None:
    if not RESUME_JSON.exists():
        log.error("resume.json not found – aborting")
        sys.exit(1)

    log.info("Loading resume.json")
    data = json.loads(RESUME_JSON.read_text(encoding="utf-8"))
    data = preprocess(data)

    md_content = TEMPLATE.render(**data)
    log.debug("Markdown length: %d chars", len(md_content))
    MD_OUT.write_text(md_content, encoding="utf-8")
    log.info("Markdown written to %s", MD_OUT.relative_to(ROOT))

    # Try generating PDF via pandoc (if installed)
    try:
        log.info("Generating PDF via pandoc…")
        subprocess.run(["pandoc", str(MD_OUT), "-o", str(PDF_OUT)], check=True)
        log.info("PDF generated → %s", PDF_OUT.relative_to(ROOT))
    except FileNotFoundError:
        log.warning("pandoc not installed – skipping PDF generation.")
    except subprocess.CalledProcessError as e:
        log.warning("pandoc failed: %s", e)

if __name__ == "__main__":
    main()