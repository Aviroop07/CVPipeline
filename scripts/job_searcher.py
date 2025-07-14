#!/usr/bin/env python3
"""
Job search module using LinkedIn API.

This module provides functions to search for jobs related to Machine Learning and Artificial Intelligence
and store the results in a JSON file.
"""

import json
import os
import pathlib
import sys
import logging
from typing import List, Dict, Any
from linkedin_fetcher import authenticate_linkedin
import config
import api_cache

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS_OUTPUT_FILE = ROOT / config.ASSETS_DIR / config.JOB_SEARCH_RESULTS_FILE
JOB_ROLES_FILE = ROOT / config.ASSETS_DIR / config.JOB_ROLES_FILE

def load_job_roles() -> List[str]:
    """Load job roles from the text file.
    
    Returns:
        List[str]: List of job roles to search for
        
    Raises:
        FileNotFoundError: If the roles file doesn't exist
    """
    if not JOB_ROLES_FILE.exists():
        log.error(f"Job roles file not found: {JOB_ROLES_FILE}")
        raise FileNotFoundError(f"Job roles file not found: {JOB_ROLES_FILE}")
    
    roles = []
    with open(JOB_ROLES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines, comments, and section headers
            if line and not line.startswith('#') and not line.startswith('##'):
                roles.append(line)
    
    log.info(f"Loaded {len(roles)} job roles from {JOB_ROLES_FILE.name}")
    return roles

# Load job roles from file
try:
    ML_AI_ROLES = load_job_roles()
except FileNotFoundError:
    # Fallback to hardcoded roles if file doesn't exist
    log.warning("Using fallback hardcoded job roles")
    ML_AI_ROLES = [
        # Core ML/AI roles
        "Machine Learning Engineer",
        "Machine Learning Scientist", 
        "ML Engineer",
        "ML Scientist",
        "Artificial Intelligence Engineer",
        "AI Engineer",
        "AI Scientist",
        "Data Scientist",
        "Applied Scientist",
        "Research Scientist",
        "ML Research Engineer",
        "AI Research Engineer",
        
        # Specialized roles
        "Deep Learning Engineer",
        "Computer Vision Engineer",
        "NLP Engineer",
        "Natural Language Processing Engineer",
        "Computer Vision Scientist",
        "NLP Scientist",
        "Deep Learning Scientist",
        "MLOps Engineer",
        "ML Platform Engineer",
        "AI Platform Engineer",
        
        # Senior/Lead roles
        "Senior Machine Learning Engineer",
        "Senior ML Engineer",
        "Senior AI Engineer",
        "Lead Machine Learning Engineer",
        "Lead ML Engineer",
        "Lead AI Engineer",
        "Principal Machine Learning Engineer",
        "Principal ML Engineer",
        "Principal AI Engineer",
        
        # Alternative titles
        "Machine Learning Developer",
        "AI Developer",
        "ML Developer",
        "Machine Learning Specialist",
        "AI Specialist",
        "ML Specialist",
        "Machine Learning Architect",
        "AI Architect",
        "ML Architect",
        
        # Research focused
        "Machine Learning Researcher",
        "AI Researcher",
        "ML Researcher",
        "Research Engineer",
        "Applied Research Scientist",
        "Machine Learning Research Engineer",
        "AI Research Scientist",
        
        # Industry specific
        "ML Software Engineer",
        "AI Software Engineer",
        "Machine Learning Software Engineer",
        "AI/ML Engineer",
        "ML/AI Engineer",
        "Machine Learning & AI Engineer",
        "AI & Machine Learning Engineer"
    ]

def search_jobs_for_role(api, role: str, location: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Search for jobs with a specific role using LinkedIn API.
    
    Args:
        api: Authenticated LinkedIn API client
        role (str): Job role to search for
        location (str, optional): Location to search in
        limit (int): Maximum number of results to return
        
    Returns:
        List[Dict]: List of job search results
    """
    try:
        log.info(f"🔍 Searching for '{role}' positions (FULL-TIME ONLY)...")
        
        # Prepare request data for caching
        request_data = {
            "keywords": role,
            "job_type": ["F"],  # Full-time only
            "location_name": location,
            "limit": limit,
            "listed_at": config.JOB_SEARCH_SECONDS_BACK
        }
        
        # Use cached API call if enabled
        if config.API_CACHE_ENABLED:
            jobs = api_cache.cached_api_call(
                "job_search",
                request_data,
                api.search_jobs,
                keywords=role,
                job_type=["F"],  # Full-time only - this ensures we only get full-time positions
                location_name=location,
                limit=limit,
                listed_at=config.JOB_SEARCH_SECONDS_BACK  # Jobs posted in last N seconds
            )
        else:
            # Direct API call without caching
            jobs = api.search_jobs(
                keywords=role,
                job_type=["F"],  # Full-time only - this ensures we only get full-time positions
                location_name=location,
                limit=limit,
                listed_at=config.JOB_SEARCH_SECONDS_BACK  # Jobs posted in last N seconds
            )
        
        log.info(f"✅ Found {len(jobs)} jobs for '{role}'")
        
        # Print details of each job found
        if jobs:
            log.info(f"📋 Jobs found for '{role}':")
            for i, job in enumerate(jobs, 1):
                job_id = job.get("entityUrn", "").split(":")[-1] if job.get("entityUrn") else "N/A"
                title = job.get("title", "Unknown Title")
                company = job.get("companyDetails", {}).get("company", {}).get("name", "Unknown Company")
                location = job.get("formattedLocation", "Unknown Location")
                employment_type = job.get("employmentStatus", {}).get("employmentType", "Unknown")
                
                log.info(f"  {i:2d}. {title}")
                log.info(f"      Company: {company}")
                log.info(f"      Location: {location}")
                log.info(f"      Job ID: {job_id}")
                log.info(f"      Employment Type: {employment_type}")
                
                # Log additional details if available
                if job.get("experienceLevel"):
                    log.info(f"      Experience Level: {job['experienceLevel']}")
                if job.get("seniorityLevel"):
                    log.info(f"      Seniority Level: {job['seniorityLevel']}")
                if job.get("workplaceType"):
                    log.info(f"      Workplace Type: {job['workplaceType']}")
                if job.get("listedAt"):
                    log.info(f"      Listed At: {job['listedAt']}")
                
                log.info("")  # Empty line for readability
        else:
            log.info(f"  No jobs found for '{role}'")
        
        return jobs
        
    except Exception as e:
        log.error(f"❌ Error searching for '{role}': {e}")
        return []

def extract_job_details(job_data: Dict[str, Any], api=None) -> Dict[str, Any]:
    """Extract relevant details from LinkedIn job data with detailed job information.
    
    Args:
        job_data (Dict): Raw job data from LinkedIn API
        api: Authenticated LinkedIn API client for detailed job fetching
        
    Returns:
        Dict: Cleaned job details with additional information
    """
    try:
        # Extract basic job information first
        job_id = job_data.get("entityUrn", "").split(":")[-1] if job_data.get("entityUrn") else ""
        
        # Initialize job details with basic info from search results
        job_details = {
            "id": job_id,
            "title": job_data.get("title", ""),
            "company": "",
            "location": job_data.get("formattedLocation", ""),
            "listed_at": job_data.get("listedAt", ""),
            "application_type": "",
            "workplace_type": "",
            "employment_type": job_data.get("employmentStatus", {}).get("employmentType", ""),
            "experience_level": job_data.get("experienceLevel", ""),
            "job_url": f"https://www.linkedin.com/jobs/view/{job_id}" if job_id else "",
            "company_url": "",
            "description": "",
            "skills": [],
            "benefits": [],
            "seniority_level": job_data.get("seniorityLevel", ""),
            "job_functions": job_data.get("jobFunctions", []),
            "industries": job_data.get("industries", [])
        }
        
        # Fetch detailed job information if API is available and job_id exists
        if api and job_id:
            try:
                log.info(f"🔍 Fetching detailed job information for job ID: {job_id}")
                
                # Get detailed job information with caching
                if config.API_CACHE_ENABLED:
                    detailed_job = api_cache.cached_api_call(
                        "job_details",
                        {"job_id": job_id},
                        api.get_job,
                        job_id
                    )
                else:
                    detailed_job = api.get_job(job_id)
                
                if detailed_job:
                    log.info(f"✅ Detailed job data retrieved for job ID: {job_id}")
                    
                    # Extract company name from the correct path
                    try:
                        company_details = detailed_job.get("companyDetails", {})
                        if "com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany" in company_details:
                            company_info = company_details["com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany"]
                            if "companyResolutionResult" in company_info:
                                job_details["company"] = company_info["companyResolutionResult"].get("name", "")
                    except Exception as e:
                        log.warning(f"    ⚠️ Error extracting company name: {e}")
                    
                    # Extract workplace type from the correct path
                    try:
                        workplace_types = detailed_job.get("workplaceTypes", [])
                        workplace_resolution = detailed_job.get("workplaceTypesResolutionResults", {})
                        
                        workplace_names = []
                        for workplace_urn in workplace_types:
                            if workplace_urn in workplace_resolution:
                                workplace_names.append(workplace_resolution[workplace_urn].get("localizedName", ""))
                        
                        job_details["workplace_type"] = ", ".join(workplace_names) if workplace_names else ""
                    except Exception as e:
                        log.warning(f"    ⚠️ Error extracting workplace type: {e}")
                    
                    # Extract apply method URL from the correct path
                    try:
                        apply_method = detailed_job.get("applyMethod", {})
                        apply_url = ""
                        
                        # Check for ComplexOnsiteApply
                        if "com.linkedin.voyager.jobs.ComplexOnsiteApply" in apply_method:
                            apply_url = apply_method["com.linkedin.voyager.jobs.ComplexOnsiteApply"].get("easyApplyUrl", "")
                        
                        # Check for OffsiteApply
                        elif "com.linkedin.voyager.jobs.OffsiteApply" in apply_method:
                            apply_url = apply_method["com.linkedin.voyager.jobs.OffsiteApply"].get("companyApplyUrl", "")
                        
                        job_details["application_type"] = apply_url
                        job_details["apply_url"] = apply_url  # Add this field for consistency
                    except Exception as e:
                        log.warning(f"    ⚠️ Error extracting apply URL: {e}")
                    
                    # Extract job description text from the correct path
                    try:
                        description = detailed_job.get("description", {})
                        job_details["description"] = description.get("text", "")
                    except Exception as e:
                        log.warning(f"    ⚠️ Error extracting description text: {e}")
                    
                    # Extract formatted location
                    job_details["location"] = detailed_job.get("formattedLocation", job_details["location"])
                    
                    # Log extracted information
                    if job_details["company"]:
                        log.info(f"    🏢 Company: {job_details['company']}")
                    if job_details["workplace_type"]:
                        log.info(f"    🏠 Workplace Type: {job_details['workplace_type']}")
                    if job_details["application_type"]:
                        log.info(f"    📝 Apply URL: {job_details['application_type']}")
                    if job_details["description"]:
                        desc_length = len(job_details["description"])
                        log.info(f"    📄 Description: {desc_length} characters")
                    
                else:
                    log.warning(f"    ⚠️ No detailed job data returned for job ID: {job_id}")
                
                # Get job skills information with caching
                log.info(f"🔍 Fetching job skills for job ID: {job_id}")
                try:
                    if config.API_CACHE_ENABLED:
                        job_skills = api_cache.cached_api_call(
                            "job_skills",
                            {"job_id": job_id},
                            api.get_job_skills,
                            job_id
                        )
                    else:
                        job_skills = api.get_job_skills(job_id)
                    
                    if job_skills:
                        log.info(f"✅ Job skills data retrieved for job ID: {job_id}")
                        
                        # Extract skills from the job skills response
                        skill_names = []
                        skill_matches = job_skills.get("skillMatchStatuses", [])
                        
                        for skill_match in skill_matches:
                            if "skill" in skill_match and "name" in skill_match["skill"]:
                                skill_names.append(skill_match["skill"]["name"])
                        
                        if skill_names:
                            job_details["skills"] = skill_names
                            log.info(f"    🎯 Found {len(skill_names)} skills for job ID: {job_id}")
                            
                            # Log the top skills (first 5)
                            top_skills = skill_names[:5]
                            for skill in top_skills:
                                log.info(f"      • {skill}")
                            
                            if len(skill_names) > 5:
                                log.info(f"      ... and {len(skill_names) - 5} more skills")
                        else:
                            log.info(f"    ℹ️ No skills found for job ID: {job_id}")
                    else:
                        log.warning(f"    ⚠️ No job skills data returned for job ID: {job_id}")
                        
                except Exception as e:
                    log.warning(f"    ⚠️ Error fetching job skills for job ID {job_id}: {e}")
                
            except Exception as e:
                log.warning(f"⚠️ Error fetching detailed job information for job ID {job_id}: {e}")
                # Continue with basic job details if detailed fetching fails
        
        return job_details
        
    except Exception as e:
        log.error(f"❌ Error extracting job details: {e}")
        return {}

def search_ml_ai_jobs(location: str = None, jobs_per_role: int = None) -> List[Dict[str, Any]]:
    """Search for Machine Learning and AI jobs using multiple role variations.
    
    Args:
        location (str, optional): Location to search in (e.g., "United States", "New York")
        jobs_per_role (int, optional): Number of jobs to fetch per role
        
    Returns:
        List[Dict]: List of all job search results
    """
    # Use config defaults if not provided
    if location is None:
        location = config.JOB_SEARCH_LOCATION
    if jobs_per_role is None:
        jobs_per_role = config.JOB_SEARCH_LIMIT_PER_ROLE
    try:
        # Authenticate with LinkedIn
        api = authenticate_linkedin()
        
        # Clean dirty (expired) cache entries at the start
        if config.API_CACHE_ENABLED:
            dirty_cleared = api_cache.clean_dirty_cache()
            if dirty_cleared > 0:
                log.info(f"🧹 Cleaned {dirty_cleared} dirty (expired) cache entries at start")
        
        # Phase 1: Collect all jobs from all roles (basic info only)
        all_raw_jobs = []
        seen_job_ids = set()  # To avoid duplicates
        
        log.info(f"🚀 Starting ML/AI job search for {len(ML_AI_ROLES)} role variations...")
        log.info(f"📋 Phase 1: Collecting basic job information...")
        
        for i, role in enumerate(ML_AI_ROLES, 1):
            log.info(f"📋 [{i}/{len(ML_AI_ROLES)}] Searching for: {role}")
            
            # Search for jobs with this role
            jobs = search_jobs_for_role(api, role, location, jobs_per_role)
            
            # Collect basic job info and deduplicate by ID
            for job in jobs:
                job_id = job.get("entityUrn", "").split(":")[-1] if job.get("entityUrn") else ""
                if job_id and job_id not in seen_job_ids:
                    seen_job_ids.add(job_id)
                    # Store basic job info with role tracking
                    basic_job_info = {
                        "raw_data": job,
                        "search_role": role,
                        "job_id": job_id
                    }
                    all_raw_jobs.append(basic_job_info)
                    log.debug(f"    ✅ Added basic job: {job.get('title', 'Unknown')} at {job.get('companyDetails', {}).get('company', {}).get('name', 'Unknown')}")
                elif job_id:
                    log.debug(f"    ⏭️ Skipped duplicate job ID: {job_id}")
            
            # Add a small delay to avoid rate limiting
            import time
            time.sleep(2)
        
        log.info(f"📊 Phase 1 complete: Found {len(all_raw_jobs)} unique jobs")
        
        # Phase 2: Limit to maximum total jobs and fetch detailed information
        max_jobs = config.JOB_SEARCH_MAX_TOTAL_JOBS
        if len(all_raw_jobs) > max_jobs:
            log.info(f"📋 Limiting to {max_jobs} jobs (from {len(all_raw_jobs)} found)")
            all_raw_jobs = all_raw_jobs[:max_jobs]
        
        log.info(f"📋 Phase 2: Fetching detailed information for {len(all_raw_jobs)} jobs...")
        
        # Fetch detailed information for each unique job
        all_jobs = []
        for i, job_info in enumerate(all_raw_jobs, 1):
            log.info(f"🔍 [{i}/{len(all_raw_jobs)}] Fetching details for job ID: {job_info['job_id']}")
            job_details = extract_job_details(job_info["raw_data"], api)
            if job_details and job_details.get("id"):
                job_details["search_role"] = job_info["search_role"]  # Track which role found this job
                all_jobs.append(job_details)
                log.debug(f"    ✅ Detailed job: {job_details.get('title', 'Unknown')} at {job_details.get('company', 'Unknown')}")
            else:
                log.warning(f"    ❌ Failed to extract details for job ID: {job_info['job_id']}")
            
            # Add delay between detailed fetches to avoid rate limiting
            import time
            time.sleep(1)
        
        # Count jobs with detailed information
        jobs_with_details = sum(1 for job in all_jobs if job.get("description") or job.get("company"))
        jobs_with_skills = sum(1 for job in all_jobs if job.get("skills"))
        
        log.info(f"🎉 Job search complete! Found {len(all_jobs)} unique ML/AI positions")
        log.info(f"📊 Detailed information: {jobs_with_details} jobs with detailed info, {jobs_with_skills} jobs with skills data")
        return all_jobs
        
    except Exception as e:
        log.error(f"❌ Job search failed: {e}")
        return []

def save_job_results(jobs: List[Dict[str, Any]], output_path: pathlib.Path = None, location: str = None, jobs_per_role: int = None) -> pathlib.Path:
    """Save job search results to JSON file.
    
    Args:
        jobs (List[Dict]): Job search results to save
        output_path (pathlib.Path, optional): Custom output path
        location (str, optional): Location that was searched
        jobs_per_role (int, optional): Number of jobs per role that was searched
        
    Returns:
        pathlib.Path: Path where results were saved
    """
    if output_path is None:
        output_path = JOBS_OUTPUT_FILE
    
    # Ensure assets directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    # Create results structure
    results = {
        "search_metadata": {
            "total_jobs": len(jobs),
            "search_date": str(pathlib.Path().cwd().stat().st_mtime),
            "roles_searched": ML_AI_ROLES,
            "search_location": location or "Global",
            "jobs_per_role": jobs_per_role or config.JOB_SEARCH_LIMIT_PER_ROLE,
            "max_total_jobs": config.JOB_SEARCH_MAX_TOTAL_JOBS,
            "seconds_back": config.JOB_SEARCH_SECONDS_BACK,
            "days_back": config.JOB_SEARCH_SECONDS_BACK // (24 * 60 * 60),  # Convert seconds to days for reference
            "detailed_job_info": True,  # Indicate that detailed job information was fetched
            "job_skills_info": True     # Indicate that job skills information was fetched
        },
        "jobs": jobs
    }
    
    # Save to JSON file
    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False), 
        encoding="utf-8"
    )
    
    log.info(f"✅ Job search results saved to {output_path.relative_to(ROOT)}")
    return output_path

def search_and_save_jobs(location: str = None, jobs_per_role: int = None) -> pathlib.Path:
    """Complete job search and save pipeline.
    
    Args:
        location (str, optional): Location to search in
        jobs_per_role (int, optional): Number of jobs to fetch per role
        
    Returns:
        pathlib.Path: Path to saved job results file
    """
    log.info("🔍 Starting ML/AI job search pipeline...")
    
    # Search for jobs
    jobs = search_ml_ai_jobs(location, jobs_per_role)
    
    if not jobs:
        log.warning("⚠️ No jobs found - creating empty results file")
        jobs = []
    
    # Save results
    output_path = save_job_results(jobs, location=location, jobs_per_role=jobs_per_role)
    
    # Count jobs with detailed information for final summary
    jobs_with_details = sum(1 for job in jobs if job.get("description") or job.get("company"))
    jobs_with_skills = sum(1 for job in jobs if job.get("skills"))
    
    log.info(f"🎯 Job search pipeline complete! Found {len(jobs)} positions")
    log.info(f"📊 Enhanced data: {jobs_with_details} jobs with detailed descriptions, {jobs_with_skills} jobs with skills analysis")
    
    # Print cache statistics if caching is enabled
    if config.API_CACHE_ENABLED:
        log.info("📊 Final API Cache Statistics:")
        stats = api_cache.get_cache_stats()
        if stats:
            log.info(f"  Total entries: {stats.get('total_entries', 0)}")
            log.info(f"  Valid entries: {stats.get('valid_entries', 0)}")
            log.info(f"  Expired entries: {stats.get('expired_entries', 0)}")
            log.info(f"  Database size: {stats.get('db_size_mb', 0)} MB")
            
            # Show cache freshness information
            freshness = api_cache.get_cache_freshness()
            if freshness.get("status") == "dirty":
                log.warning(f"⚠️ Cache is dirty: {freshness.get('expired_entries', 0)} expired entries")
            elif freshness.get("status") == "mostly_fresh":
                log.info(f"ℹ️ Cache is mostly fresh: {freshness.get('freshness_percentage', 0)}% valid")
            else:
                log.info(f"✅ Cache is fresh: {freshness.get('freshness_percentage', 0)}% valid")
            
            # Show entries by API type
            entries_by_type = stats.get('entries_by_type', {})
            if entries_by_type:
                log.info("  Entries by API type:")
                for api_type, count in entries_by_type.items():
                    log.info(f"    {api_type}: {count}")
        else:
            log.info("ℹ️ No cache statistics available")
    
    return output_path

def add_job_role(new_role: str, category: str = "Additional Roles") -> bool:
    """Add a new job role to the roles file.
    
    Args:
        new_role (str): New job role to add
        category (str): Category to add the role under
        
    Returns:
        bool: True if role was added successfully, False otherwise
    """
    try:
        if not JOB_ROLES_FILE.exists():
            log.error(f"Job roles file not found: {JOB_ROLES_FILE}")
            return False
        
        # Read existing content
        with open(JOB_ROLES_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if role already exists
        if new_role in content:
            log.warning(f"Role '{new_role}' already exists in the file")
            return False
        
        # Add the new role to the appropriate category
        if f"## {category}" in content:
            # Insert after the category header
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == f"## {category}":
                    # Find the next category or end of file
                    insert_pos = i + 1
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith('##') and lines[j].strip() != f"## {category}":
                            insert_pos = j
                            break
                        elif j == len(lines) - 1:
                            insert_pos = j + 1
                            break
                    
                    lines.insert(insert_pos, new_role)
                    break
        else:
            # Add new category at the end
            lines = content.split('\n')
            lines.append(f"\n## {category}")
            lines.append(new_role)
        
        # Write back to file
        with open(JOB_ROLES_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        log.info(f"✅ Added new role '{new_role}' to category '{category}'")
        return True
        
    except Exception as e:
        log.error(f"❌ Error adding job role: {e}")
        return False

def list_job_roles() -> List[str]:
    """List all currently loaded job roles.
    
    Returns:
        List[str]: List of all job roles
    """
    return ML_AI_ROLES.copy()

def clear_job_search_cache(expired_only: bool = True) -> int:
    """Clear job search API cache.
    
    Args:
        expired_only (bool): If True, only clear expired entries. If False, clear all.
        
    Returns:
        int: Number of entries removed
    """
    if not config.API_CACHE_ENABLED:
        log.info("ℹ️ API caching is disabled")
        return 0
    
    return api_cache.clear_cache(expired_only=expired_only)

def get_job_search_cache_stats() -> Dict[str, Any]:
    """Get job search cache statistics.
    
    Returns:
        Dict[str, Any]: Cache statistics
    """
    if not config.API_CACHE_ENABLED:
        return {"cache_enabled": False}
    
    stats = api_cache.get_cache_stats()
    stats["cache_enabled"] = True
    return stats

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    search_and_save_jobs()

if __name__ == "__main__":
    main() 