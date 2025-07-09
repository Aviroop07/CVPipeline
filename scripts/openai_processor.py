#!/usr/bin/env python3
"""
OpenAI resume processing module.

This module provides functions to enhance resume data using OpenAI API with async support for improved performance.
"""

import json, os, pathlib, sys, re, logging, asyncio
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



async def call_openai_api_async(prompt: str = None, messages: list = None) -> str:
    """Send prompt or messages to OpenAI chat API (asynchronous version).
    
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
        from openai import AsyncOpenAI  # requires openai >= 1.x
        
        # Log messages before making the call
        log.debug("🤖 OpenAI API Call - Messages:")
        log.debug(json.dumps(messages, indent=2, ensure_ascii=False))
        log.debug("=" * 60)
        
        log.debug("Calling OpenAI with %d messages", len(messages))

        client = AsyncOpenAI(api_key=api_key)

        response = await client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=config.OPENAI_TEMPERATURE,
            reasoning_effort=config.OPENAI_REASONING_EFFORT
        )

        result = response.choices[0].message.content.strip()
        
        # Log the response from OpenAI
        log.debug("🤖 OpenAI API Response:")
        log.debug(result)
        log.debug("=" * 60)
        
        log.debug("OpenAI response received (%d chars)", len(result))
        log.debug("OpenAI response: %s", result)
        return result
    except Exception as exc:
        log.warning("OpenAI call failed: %s", exc)
        return ""

def sort_chronologically(items: List[Dict[str, Any]], date_key: str = None, end_date_key: str = None) -> List[Dict[str, Any]]:
    """Sort items chronologically (descending - latest first), prioritizing end dates.
    
    Args:
        items (List[Dict]): Items to sort
        date_key (str, optional): Key containing start date in YYYY-MM format
        end_date_key (str, optional): Key containing end date in YYYY-MM format
        
    Returns:
        List[Dict]: Sorted items
    """
    def _key(it):
        # Prioritize end date if available, otherwise use start date
        if end_date_key:
            end_date = it.get(end_date_key)
            if end_date:
                return end_date
        
        if date_key:
            start_date = it.get(date_key)
            if start_date:
                return start_date
        
        # Fallback for awards or other single-date items
        if it.get("date"):
            return it.get("date")
            
        return ""
    
    return sorted(items, key=_key, reverse=True)

def sort_extracted_projects(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort extracted projects chronologically by duration end date, then start date.
    
    Args:
        projects (List[Dict]): List of extracted project dictionaries
        
    Returns:
        List[Dict]: Sorted projects
    """
    def _project_key(project):
        duration = project.get("duration", {})
        
        # Prioritize end date
        end_info = duration.get("end", {})
        if end_info.get("year"):
            end_year = end_info["year"]
            end_month = end_info.get("month", 1)
            return f"{end_year:04d}-{end_month:02d}"
        
        # Fallback to start date
        start_info = duration.get("start", {})
        if start_info.get("year"):
            start_year = start_info["year"]
            start_month = start_info.get("month", 1)
            return f"{start_year:04d}-{start_month:02d}"
        
        return ""
    
    return sorted(projects, key=_project_key, reverse=True)

async def filter_and_categorize_skills_with_openai_async(skills: List[str]) -> Dict[str, List[str]]:
    """Filter and categorize skills using OpenAI (async version).
    
    Args:
        skills (List[str]): List of skill names
        
    Returns:
        Dict[str, List[str]]: Skills grouped by category
    """
    if not skills:
        return {}

    # Load the system prompt
    system_prompt = load_prompt_template(config.FILTER_SKILLS_PROMPT)
    
    # Create messages with system prompt and user skills list
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": [
            {"type": "text", "text": "Input Skills as a list of strings: "},
            {"type": "text", "text" : f'{skills}'}
        ]}
    ]
    
    log.info("Filtering %d skills via OpenAI (async)", len(skills))
    response = await call_openai_api_async(messages=messages)
    log.debug("Skill filtering raw response: %s", response)
    if not response:
        return {"General": skills}

    try:
        # Look for JSON object in response (not array)
        json_match = re.search(r"\{.*\}", response, re.S)
        if json_match:
            json_text = json_match.group(0)
            result = json.loads(json_text)
            
            # Count total filtered skills
            total_filtered = sum(len(skill_list) if isinstance(skill_list, list) else 0 
                               for skill_list in result.values())
            
            log.info("Filtered and categorized: kept %d/%d skills in %d categories", 
                    total_filtered, len(skills), len(result))
            return result if total_filtered > 0 else {"General": skills}
        else:
            log.warning("No JSON object found in response")
            return {"General": skills}
    except Exception as exc:
        log.warning("Failed to parse filtered skills JSON: %s", exc)
        return {"General": skills}



async def extract_bullet_points_async(text: str) -> List[str]:
    """Extract bullet points from text using heuristics or OpenAI (async version).
    
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
    log.info("Requesting point extraction (%d words) via OpenAI (async)", word_count)
    resp = await call_openai_api_async(prompt)
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

async def process_resume_with_openai_async(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply OpenAI enhancements to resume data with async processing for improved performance.
    
    Args:
        data (Dict): Resume data in JSON-Resume format
        
    Returns:
        Dict: Enhanced resume data
    """
    log.info("Processing resume data with OpenAI API (async)...")
    
    # Chronological ordering (latest first) - prioritize end dates
    data["work"] = sort_chronologically(data.get("work", []), "startDate", "endDate")
    data["education"] = sort_chronologically(data.get("education", []), "startDate", "endDate")
    data["projects"] = sort_chronologically(data.get("projects", []), "startDate", "endDate")
    data["awards"] = sort_chronologically(data.get("awards", []))

    # Phase 1: Start independent async operations
    log.info("Phase 1: Starting independent OpenAI operations...")
    
    # Skills filtering - completely independent
    skill_names = [s["name"] for s in data.get("skills", [])]
    skills_task = asyncio.create_task(
        filter_and_categorize_skills_with_openai_async(skill_names)
    )
    
    # Experience extraction - independent per work experience
    work_experiences = data.get("work", [])
    experience_tasks = []
    for i, w in enumerate(work_experiences):
        experience_text = w.get("summary", "")
        if experience_text:
            task = asyncio.create_task(
                extract_experience_projects_async(experience_text)
            )
            experience_tasks.append((i, task))
    
    # Project bullet point extraction - independent per project
    projects = data.get("projects", [])
    project_tasks = []
    for i, p in enumerate(projects):
        description = p.get("description", "")
        if description:
            task = asyncio.create_task(
                extract_bullet_points_async(description)
            )
            project_tasks.append((i, task))
    
    # Phase 2: Wait for experience extraction to complete
    log.info("Phase 2: Processing experience extraction results...")
    
    # Wait for all experience extractions to complete
    for i, task in experience_tasks:
        extracted_projects = await task
        work_experiences[i]["extracted_projects"] = sort_extracted_projects(extracted_projects)
        work_experiences[i]["points"] = await extract_bullet_points_async(work_experiences[i].get("summary", ""))
        work_experiences[i]["period"] = format_date_range(work_experiences[i].get("startDate"), work_experiences[i].get("endDate"))
    
    # Phase 3: Now run tech highlighting for all extracted projects in parallel
    log.info("Phase 3: Running tech highlighting for extracted projects...")
    
    tech_highlight_tasks = []
    for w in work_experiences:
        for project in w.get("extracted_projects", []):
            if project.get("description"):
                task = asyncio.create_task(
                    highlight_tech_skills_async(project["description"])
                )
                tech_highlight_tasks.append((project, task))
    
    # Wait for all tech highlighting to complete
    for project, task in tech_highlight_tasks:
        highlights = await task
        project["tech_highlights"] = highlights
    
    # Phase 4: Wait for remaining independent tasks
    log.info("Phase 4: Finalizing remaining tasks...")
    
    # Wait for skills filtering to complete
    categorized = await skills_task
    if not categorized:
        categorized = {"General": skill_names}
    data["skills_by_category"] = categorized
    
    # Extract all filtered skills from categories for backward compatibility
    filtered_skills = []
    for category, skill_list in categorized.items():
        if isinstance(skill_list, list):
            filtered_skills.extend(skill_list)
    data["skills"] = [{"name": s} for s in filtered_skills]
    
    # Wait for all project bullet point extractions to complete
    for i, task in project_tasks:
        points = await task
        projects[i]["points"] = points
        projects[i]["period"] = format_date_range(projects[i].get("startDate"), projects[i].get("endDate"))
    
    # Format dates for education and awards
    for e in data.get("education", []):
        e["period"] = format_date_range(e.get("startDate"), e.get("endDate"))

    for a in data.get("awards", []):
        a["date"] = format_single_date(a.get("date"))

    log.debug("Data after OpenAI processing keys: %s", list(data.keys()))
    log.info("OpenAI processing completed successfully (async)")

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
    """Complete OpenAI resume enhancement pipeline (synchronous wrapper).
    
    Returns:
        dict: Enhanced resume data
        
    Raises:
        SystemExit: If processing fails
    """
    # Load resume data
    data = load_resume_data()
    
    # Process with OpenAI (async)
    enhanced_data = asyncio.run(process_resume_with_openai_async(data))
    
    # Save enhanced data back to resume.json
    save_enhanced_resume_data(enhanced_data)
    return enhanced_data

async def extract_experience_projects_async(experience_text: str) -> List[Dict[str, Any]]:
    """Extract project data from experience text using OpenAI with examples (async version).
    
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
            {"role": "user", "content": [
                {"type": "text", "text": "Input Text: "},
                {"type": "text", "text": experience_text}
            ]}
        ]
        
        log.info("Extracting experience projects via OpenAI (async) (%d chars)", len(experience_text))
        response = await call_openai_api_async(messages=messages)
        
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



async def highlight_tech_skills_async(description: str) -> List[str]:
    """Extract technical skills and quantitative impacts from project description (async version).
    
    Args:
        description (str): Project description text
        
    Returns:
        List[str]: List of highlighted technical terms and metrics
    """
    if not description.strip():
        return []

    try:
        # Load the tech highlighting prompt
        system_prompt = load_prompt_template(config.HIGHLIGHT_TECH_PROMPT)
        
        # Load the examples
        examples_path = PROMPTS_DIR / "highlight_examples.json"
        if not examples_path.exists():
            log.warning("Tech highlighting examples file not found")
            return []
        
        examples_data = json.loads(examples_path.read_text(encoding="utf-8"))
        
        # Construct messages for OpenAI API with the specific format requested
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add examples in the specified format
        for i, example in enumerate(examples_data, 1):
            example_message = {
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"Example {i}"},
                    {"type": "text", "text": example["content"]},
                    {"type": "text", "text": str(example["highlights"])}
                ]
            }
            messages.append(example_message)
        
        # Add the actual project description to highlight
        messages.append({
            "role": "user", 
            "content": [
                {"type": "text", "text": "Input Text: "},
                {"type": "text", "text": description}
            ]
        })
        
        log.info("Highlighting tech skills via OpenAI (async) (%d chars)", len(description))
        response = await call_openai_api_async(messages=messages)
        
        if not response:
            return []
        
        # Parse the response (can be JSON or Python list format)
        try:
            # Extract list from response (in case there's extra text)
            list_match = re.search(r'\[.*\]', response, re.S)
            if list_match:
                list_text = list_match.group(0)
            else:
                list_text = response
            
            # Try JSON parsing first
            try:
                highlights = json.loads(list_text)
            except json.JSONDecodeError:
                # Fallback: try parsing as Python literal (handles single quotes)
                import ast
                highlights = ast.literal_eval(list_text)
            
            log.info("Extracted %d tech highlights", len(highlights))
            return highlights if isinstance(highlights, list) else []
            
        except (json.JSONDecodeError, ValueError, SyntaxError) as e:
            log.warning("Failed to parse tech highlights: %s", e)
            log.debug("Raw response: %s", response)
            return []
            
    except Exception as e:
        log.warning("Tech highlighting failed: %s", e)
        return []



# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    enhance_resume_with_openai()

if __name__ == "__main__":
    main() 