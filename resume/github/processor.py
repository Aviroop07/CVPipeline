#!/usr/bin/env python3
"""
GitHub repository processing module.

This module provides functions to fetch GitHub repositories and process their README content
to extract project information for the resume.
"""

import json
import os
import logging
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv
from github import Github, Auth
from string import Template as StrTemplate
from resume.utils import config
from resume.utils.api_cache import cached_api_call, get_cache
from resume.openai.processor import highlight_tech_skills_async, highlight_tech_skills_batch_async

# Load environment variables
load_dotenv()

PROMPTS_DIR = config.PROJECT_ROOT / config.PROMPTS_DIR

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

cache = get_cache()

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
    """Send prompt or messages to OpenAI chat API (synchronous version).
    
    Args:
        prompt (str, optional): Simple prompt to send (will be converted to messages format)
        messages (list, optional): List of message dictionaries for chat API
        
    Returns:
        str: OpenAI response or empty string if API key not available or call fails
    """
    # Run the async version in a new event loop for backward compatibility
    return asyncio.run(call_openai_api_async(prompt, messages))

async def call_openai_api_async(prompt: str = None, messages: list = None) -> str:
    """Send prompt or messages to OpenAI chat API (async version).
    
    Args:
        prompt (str, optional): Simple prompt to send (will be converted to messages format)
        messages (list, optional): List of message dictionaries for chat API
        
    Returns:
        str: OpenAI response or empty string if API key not available or call fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log.debug("[OpenAI] OPENAI_API_KEY not set – skipping call")
        return ""
    
    # Convert prompt to messages format if needed
    if prompt and not messages:
        messages = [{"role": "user", "content": prompt}]
    elif not messages:
        log.warning("[OpenAI] No prompt or messages provided to OpenAI API")
        return ""
    
    try:
        from openai import AsyncOpenAI  # requires openai >= 1.x
        
        # Log messages before making the call
        log.debug("[OpenAI] API Call - Messages:")
        log.debug(json.dumps(messages, indent=2, ensure_ascii=False))
        log.debug("=" * 60)
        log.debug(f"[OpenAI] Calling OpenAI with {len(messages)} messages")

        # Use context manager to ensure proper cleanup
        async with AsyncOpenAI(api_key=api_key) as client:
            response = await client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                temperature=config.OPENAI_TEMPERATURE,
                reasoning_effort=config.OPENAI_REASONING_EFFORT
            )

            result = response.choices[0].message.content.strip()
            
            # Log the response from OpenAI
            log.debug("[OpenAI] API Response:")
            log.debug(result)
            log.debug("=" * 60)
            log.debug(f"[OpenAI] Response received ({len(result)} chars)")
            log.debug(f"[OpenAI] Response: {result}")
            return result
    except Exception as exc:
        log.warning(f"[OpenAI] Call failed: {exc}")
        return ""

def github_details(username: str, token: str):
    """Fetch GitHub repository details including README content with caching.
    
    Args:
        username (str): GitHub username
        token (str): GitHub personal access token
        
    Returns:
        dict: Repository information with README content
    """
    log.info(f"[GitHub] Request for user: {username}")
    
    def fetch_github_details():
        gh = Github(auth=Auth.Token(token))
        user = gh.get_user(login=username)
        
        result = {"username": username, "repos": []}

        for repo in user.get_repos():
            # Only include repos where the owner matches the specified username
            if repo.owner.login != username:
                continue
                
            # commit metadata ??? only 2 API calls instead of walking every page
            commits = repo.get_commits()
            last = commits[0].commit.author.date
            first = commits.reversed[0].commit.author.date  # uses the last page
            commit_count = commits.totalCount               # set by PyGithub

            # Get README content using PyGithub's built-in method
            try:
                readme_content = repo.get_contents(config.README_FILE)
                readme_text = readme_content.decoded_content.decode('utf-8')
                readme_error = None
            except Exception as e:
                # Repository doesn't have a README.md file or other error
                readme_text = None
                readme_error = str(e)

            result["repos"].append(
                {
                    "repo_name": repo.name,
                    "first_commit": first.strftime("%Y-%m-%d"),
                    "last_commit": last.strftime("%Y-%m-%d"),
                    "commit_count": commit_count,
                    "readme_content": readme_text,
                    "readme_error": readme_error,
                }
            )

        log.info(f"[GitHub] Response for user {username}: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result

    # Use cached API call
    return cached_api_call("github_details", {"username": username}, fetch_github_details)

async def extract_project_points_async(readme_content: str) -> List[str]:
    """Extract bullet points from README content using OpenAI (async version).
    
    Args:
        readme_content (str): README content to extract points from
        
    Returns:
        List[str]: List of bullet points
    """
    if not readme_content or not readme_content.strip():
        return []

    try:
        # Load the extract points prompt
        system_prompt = load_prompt_template(config.EXTRACT_POINTS_PROMPT)
        
        # Ensure consistent structure for messages
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": [{"type": "text", "text": "Raw Text : "}, {"type": "text", "text": readme_content}]}]

        log.info("Extracting project points from README via OpenAI (async) (%d chars)", len(readme_content))
        response = await call_openai_api_async(messages=messages)
        
        # Cache the response
        cache.set("openai_chat", {"messages": messages}, response)
        
        if not response:
            log.warning("Empty response from OpenAI for README extraction")
            return []
        
        # Debug: Log the raw response
        log.debug("Raw OpenAI response: %s", response)
        
        # Parse the JSON response
        try:
            # Extract JSON array from response (in case there's extra text)
            import re
            json_match = re.search(r'\[.*\]', response, re.S)
            if json_match:
                json_text = json_match.group(0)
                log.debug("Extracted JSON text: %s", json_text)
            else:
                json_text = response
                log.debug("Using full response as JSON: %s", json_text)
            
            points = json.loads(json_text)
            log.info("Extracted %d points from README", len(points))
            return points if isinstance(points, list) else []
            
        except json.JSONDecodeError as e:
            log.warning("Failed to parse project points JSON: %s", e)
            log.warning("Raw response: %s", response)
            return []
            
    except Exception as e:
        log.warning("Project points extraction failed: %s", e)
        return []

def extract_project_points(readme_content: str) -> List[str]:
    """Extract bullet points from README content using OpenAI (synchronous wrapper).
    
    Args:
        readme_content (str): README content to extract points from
        
    Returns:
        List[str]: List of bullet points
    """
    return asyncio.run(extract_project_points_async(readme_content))

def format_date_range(start_date: str, end_date: str) -> str:
    """Format date range from YYYY-MM-DD strings.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        
    Returns:
        str: Formatted date range (e.g., "Jan, 2020 – Present")
    """
    if not start_date:
        return ""
    
    try:
        # Parse start date
        start_year, start_month, _ = start_date.split("-")
        start_month_name = config.MONTHS[int(start_month) - 1]
        
        # Parse end date
        if end_date:
            end_year, end_month, _ = end_date.split("-")
            end_month_name = config.MONTHS[int(end_month) - 1]
            
            if start_year == end_year:
                if start_month == end_month:
                    return f"{start_month_name}, {start_year}"
                else:
                    return f"{start_month_name} – {end_month_name}, {start_year}"
            else:
                return f"{start_month_name}, {start_year} – {end_month_name}, {end_year}"
        else:
            return f"{start_month_name}, {start_year} – Present"
            
    except Exception:
        return f"{start_date} – {end_date if end_date else 'Present'}"

async def process_github_repos_async(username: str) -> List[Dict[str, Any]]:
    """Process GitHub repositories and extract project information (async version).
    
    Args:
        username (str): GitHub username
        
    Returns:
        List[Dict]: List of processed project dictionaries
    """
    github_token = os.getenv("PAT_GITHUB")
    if not github_token:
        log.warning("PAT_GITHUB not set - skipping GitHub processing")
        return []
    
    log.info(f"🔍 [GitHub] Fetching GitHub repositories for user: {username}")
    
    try:
        # Fetch repository details
        repo_data = github_details(username, github_token)
        
        if not repo_data.get("repos"):
            log.info("No repositories found for user: %s", username)
            return []
        
        log.info(f"📁 [GitHub] Found {len(repo_data['repos'])} repositories, processing README content...")
        
        # Process each repository
        projects = []
        for repo in repo_data["repos"]:
            repo_name = repo["repo_name"]
            readme_content = repo.get("readme_content")
            
            if not readme_content:
                log.debug("Skipping %s - no README content", repo_name)
                continue
            
            # Extract bullet points from README
            points = await extract_project_points_async(readme_content)
            
            if points:
                # Batch tech highlighting for all points in this project
                highlights_list = await highlight_tech_skills_batch_async(points)
                highlighted_points = []
                for point, highlights in zip(points, highlights_list):
                    highlighted_points.append({
                        "text": point,
                        "highlights": highlights
                    })
                # Create project entry
                project = {
                    "name": repo_name,
                    "description": readme_content[:200] + "..." if len(readme_content) > 200 else readme_content,
                    "startDate": repo["first_commit"][:7],  # YYYY-MM format
                    "endDate": repo["last_commit"][:7],     # YYYY-MM format
                    "url": f"https://github.com/{username}/{repo_name}",
                    "points": highlighted_points,
                    "period": format_date_range(repo["first_commit"], repo["last_commit"]),
                    "commit_count": repo["commit_count"]
                }
                projects.append(project)
                log.info(f"✅ [GitHub] Processed project: {repo_name} ({len(points)} points)")
            else:
                log.debug("No points extracted from %s", repo_name)
        
        log.info(f"🎉 [GitHub] Processing complete: {len(projects)} projects extracted")
        return projects
        
    except Exception as e:
        log.error("❌ [GitHub] Processing failed: %s", e)
        return []
    finally:
        # Ensure any remaining async resources are cleaned up
        import gc
        gc.collect()

def process_github_repos(username: str) -> List[Dict[str, Any]]:
    """Process GitHub repositories and extract project information (synchronous wrapper).
    
    Args:
        username (str): GitHub username
        
    Returns:
        List[Dict]: List of processed project dictionaries
    """
    return asyncio.run(process_github_repos_async(username))

async def enhance_resume_with_github_projects_async(resume_data: Dict[str, Any], username: str) -> Dict[str, Any]:
    """Enhance resume data with GitHub projects (async version).
    
    Args:
        resume_data (Dict): Resume data in JSON-Resume format
        username (str): GitHub username
        
    Returns:
        Dict: Enhanced resume data with GitHub projects
    """
    log.info("🚀 [GitHub] Enhancing resume with GitHub projects...")
    
    # Process GitHub repositories
    github_projects = await process_github_repos_async(username)
    
    if github_projects:
        # Sort projects chronologically by end date (most recent first)
        github_projects.sort(key=lambda x: x.get("endDate", ""), reverse=True)
        
        # Replace existing projects with GitHub projects
        resume_data["projects"] = github_projects
        log.info(f"✅ [GitHub] Replaced {len(resume_data.get('projects', []))} LinkedIn projects with {len(github_projects)} GitHub projects (sorted chronologically)")
    else:
        log.info("ℹ️  No GitHub projects found, keeping existing projects")
    
    return resume_data

def enhance_resume_with_github_projects(resume_data: Dict[str, Any], username: str) -> Dict[str, Any]:
    """Enhance resume data with GitHub projects (synchronous wrapper).
    
    Args:
        resume_data (Dict): Resume data in JSON-Resume format
        username (str): GitHub username
        
    Returns:
        Dict: Enhanced resume data with GitHub projects
    """
    return asyncio.run(enhance_resume_with_github_projects_async(resume_data, username))

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    # Use GitHub username from config
    test_username = config.GITHUB_USERNAME
    projects = process_github_repos(test_username)
    
    log.info(f"[GitHub] Test results:")
    for project in projects:
        log.info(f"  - {project['name']}: {len(project['points'])} points")

if __name__ == "__main__":
    main() 
