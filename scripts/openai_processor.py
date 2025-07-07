#!/usr/bin/env python3
"""
OpenAI resume processing module.

This module provides functions to enhance resume data using OpenAI API.
"""

import json, os, pathlib, sys, re, logging
from typing import List, Dict, Any
from string import Template as StrTemplate
import config
import dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESUME_JSON = ROOT / config.DATA_DIR / config.RESUME_JSON_FILE
PROMPTS_DIR = ROOT / config.PROMPTS_DIR

# Load environment variables from .env file if present
dotenv.load_dotenv()

# Initialise logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def load_prompt_template(name: str, **kwargs) -> str:
    """Load a prompt template and fill placeholders.
    
    Args:
        name (str): Prompt template filename
        **kwargs: Template variables to substitute
        
    Returns:
        str: Filled prompt template
        
    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    tpl_path = PROMPTS_DIR / name
    if not tpl_path.exists():
        raise FileNotFoundError(f"Prompt template {tpl_path} not found")
    template_text = tpl_path.read_text(encoding="utf-8")
    return StrTemplate(template_text).substitute(**kwargs)

def call_openai_api(prompt: str = None, messages: list = None) -> str:
    """Send prompt or messages to OpenAI chat API.
    
    Args:
        prompt (str, optional): Simple prompt to send (will be converted to messages format)
        messages (list, optional): List of message dictionaries for chat API
        
    Returns:
        str: OpenAI response or empty string if API key not available or call fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.debug("OPENAI_API_KEY not set – skipping call")
        return ""
    
    # Convert prompt to messages format if needed
    if prompt and not messages:
        messages = [{"role": "user", "content": prompt}]
    elif not messages:
        log.warning("No prompt or messages provided to OpenAI API")
        return ""
    
    try:
        from openai import OpenAI  # requires openai >= 1.x
        
        # Print messages before making the call
        print("🤖 OpenAI API Call - Messages:")
        print(json.dumps(messages, indent=2, ensure_ascii=False))
        print("=" * 60)
        
        log.debug("Calling OpenAI with %d messages", len(messages))

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=config.OPENAI_TEMPERATURE,
            reasoning_effort=config.OPENAI_REASONING_EFFORT
        )

        result = response.choices[0].message.content.strip()
        
        # Print the response from OpenAI
        print("🤖 OpenAI API Response:")
        print(result)
        print("=" * 60)
        
        log.debug("OpenAI response received (%d chars)", len(result))
        log.debug("OpenAI response: %s", result)
        return result
    except Exception as exc:
        log.warning("OpenAI call failed: %s", exc)
        return ""

def sort_chronologically(items: List[Dict[str, Any]], date_key: str) -> List[Dict[str, Any]]:
    """Sort items chronologically by date key (descending - latest first).
    
    Args:
        items (List[Dict]): Items to sort
        date_key (str): Key containing date in YYYY-MM format
        
    Returns:
        List[Dict]: Sorted items
    """
    def _key(it):
        date = it.get(date_key)
        return date or ""
    return sorted(items, key=_key, reverse=True)

def rank_items_with_openai(items: List[str], section: str) -> List[str]:
    """Rank and potentially cull items using OpenAI.
    
    Args:
        items (List[str]): Items to rank
        section (str): Section name for context
        
    Returns:
        List[str]: Reordered items (falls back to original on error)
    """
    if not items:
        return items

    prompt = load_prompt_template(
        config.RANK_ITEMS_PROMPT,
        section_name=section,
        items_list=", ".join(items)
    )
    ranked_json = call_openai_api(prompt)
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

def reorder_objects_by_key(obj_list: List[Dict[str, Any]], key: str, section: str) -> List[Dict[str, Any]]:
    """Reorder objects based on OpenAI-ranked keys.
    
    Args:
        obj_list (List[Dict]): Objects to reorder
        key (str): Key to extract for ranking
        section (str): Section name for context
        
    Returns:
        List[Dict]: Reordered objects
    """
    order = rank_items_with_openai([o[key] for o in obj_list], section)
    ordered = [next(o for o in obj_list if o[key] == name) for name in order]
    return ordered

def categorize_skills_with_openai(skills: List[str]) -> Dict[str, List[str]]:
    """Categorize skills into groups using OpenAI.
    
    Args:
        skills (List[str]): List of skill names
        
    Returns:
        Dict[str, List[str]]: Skills grouped by category
    """
    if not skills:
        return {}
    prompt = load_prompt_template(config.CATEGORIZE_SKILLS_PROMPT, skills_list=", ".join(skills))
    log.info("Categorizing %d skills via OpenAI", len(skills))
    response = call_openai_api(prompt)
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

def filter_skills_with_openai(skills: List[str]) -> List[str]:
    """Filter skills for resume relevance using OpenAI.
    
    Args:
        skills (List[str]): List of skill names
        
    Returns:
        List[str]: Filtered list of relevant skills
    """
    if not skills:
        return skills

    prompt = load_prompt_template(config.FILTER_SKILLS_PROMPT, skills_list=", ".join(skills))
    log.info("Filtering %d skills via OpenAI", len(skills))
    response = call_openai_api(prompt)
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

def extract_bullet_points(text: str) -> List[str]:
    """Extract bullet points from text using heuristics or OpenAI.
    
    Args:
        text (str): Text to extract points from
        
    Returns:
        List[str]: List of bullet points
    """
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

    prompt = load_prompt_template(config.EXTRACT_POINTS_PROMPT, raw_text=text)
    log.info("Requesting point extraction (%d words) via OpenAI", word_count)
    resp = call_openai_api(prompt)
    log.debug("Point extraction raw response: %s", resp)
    try:
        points = json.loads(resp)
        return points if isinstance(points, list) else [text]
    except Exception as exc:
        log.warning("Failed to parse points JSON: %s", exc)
        return [text]

def format_date_range(start: str|None, end: str|None) -> str:
    """Format date range from YYYY-MM strings.
    
    Args:
        start (str|None): Start date in YYYY-MM format
        end (str|None): End date in YYYY-MM format (None means present)
        
    Returns:
        str: Formatted date range (e.g., "Jan, 2020 – Present")
    """
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

def format_single_date(date: str|None) -> str:
    """Format single date from YYYY-MM string.
    
    Args:
        date (str|None): Date in YYYY-MM or YYYY format
        
    Returns:
        str: Formatted date (e.g., "Jan, 2020") or empty string on failure
    """
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

def process_resume_with_openai(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply OpenAI enhancements to resume data.
    
    Args:
        data (Dict): Resume data in JSON-Resume format
        
    Returns:
        Dict: Enhanced resume data
    """
    log.info("Processing resume data with OpenAI API...")
    
    # Chronological ordering (latest first)
    data["work"] = sort_chronologically(data.get("work", []), "startDate")
    data["education"] = sort_chronologically(data.get("education", []), "startDate")
    data["projects"] = sort_chronologically(data.get("projects", []), "startDate")
    data["awards"] = sort_chronologically(data.get("awards", []), "date")

    # Convert work summaries/descriptions to point lists and extract projects
    for w in data.get("work", []):
        # Extract projects from the work experience description/summary
        experience_text = w.get("summary", "")
        extracted_projects = extract_experience_projects(experience_text)
        
        # Store extracted projects in the work entry
        w["extracted_projects"] = extracted_projects
        
        # Still create bullet points from the original summary for backward compatibility
        w["points"] = extract_bullet_points(experience_text)
        w["period"] = format_date_range(w.get("startDate"), w.get("endDate"))

    for p in data.get("projects", []):
        p["points"] = extract_bullet_points(p.get("description", ""))
        p["period"] = format_date_range(p.get("startDate"), p.get("endDate"))

    for e in data.get("education", []):
        e["period"] = format_date_range(e.get("startDate"), e.get("endDate"))

    # Format single-date fields (awards)
    for a in data.get("awards", []):
        a["date"] = format_single_date(a.get("date"))

    # Categorise skills into buckets based on keywords
    skill_names = [s["name"] for s in data.get("skills", [])]

    # Step 1: filter skills for relevance via OpenAI
    filtered_skills = filter_skills_with_openai(skill_names)

    # Step 2: categorise the filtered skills
    categorized = categorize_skills_with_openai(filtered_skills)
    if not categorized:
        # Fallback: put all skills under "General"
        categorized = {"General": filtered_skills}

    data["skills_by_category"] = categorized

    # Replace original skills list with filtered list so downstream templates (if any) stay in sync
    data["skills"] = [{"name": s} for s in filtered_skills]

    # Reorder sections based on relevance
    data["projects"] = reorder_objects_by_key(data["projects"], "name", "Projects")
    data["awards"] = reorder_objects_by_key(data["awards"], "title", "Achievements")
    data["work"] = reorder_objects_by_key(data["work"], "position", "Work Experience")

    log.debug("Data after OpenAI processing keys: %s", list(data.keys()))
    log.info("OpenAI processing completed successfully")

    return data

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

def save_enhanced_resume_data(data: Dict[str, Any], output_path=None):
    """Save enhanced resume data to JSON file.
    
    Args:
        data (Dict): Enhanced resume data
        output_path (pathlib.Path, optional): Custom output path. Defaults to configured path.
        
    Returns:
        pathlib.Path: Path where data was saved
    """
    if output_path is None:
        output_path = RESUME_JSON
        
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Enhanced {config.RESUME_JSON_FILE} saved successfully")
    return output_path

def enhance_resume_with_openai():
    """Complete OpenAI resume enhancement pipeline.
    
    Returns:
        dict: Enhanced resume data
        
    Raises:
        SystemExit: If processing fails
    """
    # Load resume data
    data = load_resume_data()
    
    # Process with OpenAI
    enhanced_data = process_resume_with_openai(data)
    
    # Save enhanced data back to resume.json
    save_enhanced_resume_data(enhanced_data)
    return enhanced_data

def extract_experience_projects(experience_text: str) -> List[Dict[str, Any]]:
    """Extract project data from experience text using OpenAI with examples.
    
    Args:
        experience_text (str): Raw experience text to extract projects from
        
    Returns:
        List[Dict]: List of extracted project dictionaries
    """
    if not experience_text.strip():
        return []

    try:
        # Load the experience extraction prompt
        system_prompt = load_prompt_template(config.EXPERIENCE_EXTRACTION_PROMPT)
        
        # Load the examples
        examples_path = PROMPTS_DIR / "experience_examples.json"
        if not examples_path.exists():
            log.warning("Experience examples file not found, using fallback extraction")
            return []
        
        examples_data = json.loads(examples_path.read_text(encoding="utf-8"))
        
        # Construct messages for OpenAI API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(examples_data, ensure_ascii=False, indent=2)},
            {"role": "user", "content": f"Extract data from this experience section - \n\n{experience_text}"}
        ]
        
        log.info("Extracting experience projects via OpenAI (%d chars)", len(experience_text))
        response = call_openai_api(messages=messages)
        
        if not response:
            return []
        
        # Parse the JSON response
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\[.*\]', response, re.S)
            if json_match:
                json_text = json_match.group(0)
            else:
                json_text = response
            
            projects = json.loads(json_text)
            log.info("Extracted %d projects from experience", len(projects))
            return projects if isinstance(projects, list) else []
            
        except json.JSONDecodeError as e:
            log.warning("Failed to parse experience extraction JSON: %s", e)
            log.debug("Raw response: %s", response)
            return []
            
    except Exception as e:
        log.warning("Experience extraction failed: %s", e)
        return []

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    enhance_resume_with_openai()

if __name__ == "__main__":
    main() 