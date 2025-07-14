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
        
        # Search for full-time jobs with the specific role
        # LinkedIn job type codes: F=Full-time, C=Contract, P=Part-time, T=Temporary, I=Internship, V=Volunteer, O=Other
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
        # Extract basic job information
        job_id = job_data.get("entityUrn", "").split(":")[-1] if job_data.get("entityUrn") else ""
        
        job_details = {
            "id": job_id,
            "title": job_data.get("title", ""),
            "company": job_data.get("companyDetails", {}).get("company", {}).get("name", ""),
            "location": job_data.get("formattedLocation", ""),
            "listed_at": job_data.get("listedAt", ""),
            "application_type": job_data.get("applicationMethod", {}).get("type", ""),
            "workplace_type": job_data.get("workplaceType", ""),
            "employment_type": job_data.get("employmentStatus", {}).get("employmentType", ""),
            "experience_level": job_data.get("experienceLevel", ""),
            "job_url": f"https://www.linkedin.com/jobs/view/{job_id}" if job_id else "",
            "company_url": job_data.get("companyDetails", {}).get("company", {}).get("linkedInUrl", ""),
            "description": job_data.get("description", ""),
            "skills": job_data.get("skills", []),
            "benefits": job_data.get("benefits", []),
            "seniority_level": job_data.get("seniorityLevel", ""),
            "job_functions": job_data.get("jobFunctions", []),
            "industries": job_data.get("industries", [])
        }
        
        # Additional validation: Double-check that this is a full-time position
        # LinkedIn API should filter this, but we add extra validation
        employment_status = job_data.get("employmentStatus", {})
        employment_type = employment_status.get("employmentType", "")
        
        # Log if we find non-full-time jobs (shouldn't happen with our filter)
        if employment_type and employment_type != "FULL_TIME":
            log.warning(f"Found non-full-time job: {job_details.get('title', 'Unknown')} at {job_details.get('company', 'Unknown')} - Type: {employment_type}")
        
        # Fetch detailed job information if API is available and job_id exists
        if api and job_id:
            try:
                log.info(f"🔍 Fetching detailed job information for job ID: {job_id}")
                
                # Get detailed job information
                detailed_job = api.get_job(job_id)
                if detailed_job:
                    log.info(f"✅ Detailed job data retrieved for job ID: {job_id}")
                    
                    # Extract additional details from the detailed job response
                    if "included" in detailed_job:
                        for item in detailed_job["included"]:
                            if item.get("$type") == "com.linkedin.voyager.jobs.JobPosting":
                                # Extract more detailed information
                                job_details.update({
                                    "detailed_description": item.get("description", ""),
                                    "requirements": item.get("requirements", ""),
                                    "responsibilities": item.get("responsibilities", ""),
                                    "qualifications": item.get("qualifications", ""),
                                    "application_instructions": item.get("applicationInstructions", ""),
                                    "job_posting_id": item.get("jobPostingId", ""),
                                    "formatted_description": item.get("formattedDescription", ""),
                                    "workplace_type_detailed": item.get("workplaceType", ""),
                                    "employment_status_detailed": item.get("employmentStatus", ""),
                                    "experience_level_detailed": item.get("experienceLevel", ""),
                                    "seniority_level_detailed": item.get("seniorityLevel", ""),
                                    "job_functions_detailed": item.get("jobFunctions", []),
                                    "industries_detailed": item.get("industries", []),
                                    "skills_detailed": item.get("skills", []),
                                    "benefits_detailed": item.get("benefits", []),
                                    "application_method": item.get("applicationMethod", {}),
                                    "listed_at_detailed": item.get("listedAt", ""),
                                    "expires_at": item.get("expiresAt", ""),
                                    "application_deadline": item.get("applicationDeadline", ""),
                                    "remote_allowed": item.get("remoteAllowed", False),
                                    "relocation_assistance": item.get("relocationAssistance", False),
                                    "visa_sponsorship": item.get("visaSponsorship", False)
                                })
                                
                                # Log key detailed information
                                if item.get("description"):
                                    desc_length = len(item["description"])
                                    log.info(f"    📄 Detailed description: {desc_length} characters")
                                if item.get("requirements"):
                                    req_length = len(item["requirements"])
                                    log.info(f"    📋 Requirements: {req_length} characters")
                                if item.get("responsibilities"):
                                    resp_length = len(item["responsibilities"])
                                    log.info(f"    📝 Responsibilities: {resp_length} characters")
                                if item.get("remoteAllowed") is not None:
                                    log.info(f"    🏠 Remote allowed: {item['remoteAllowed']}")
                                if item.get("relocationAssistance") is not None:
                                    log.info(f"    🚚 Relocation assistance: {item['relocationAssistance']}")
                                if item.get("visaSponsorship") is not None:
                                    log.info(f"    🛂 Visa sponsorship: {item['visaSponsorship']}")
                                break
                    else:
                        log.warning(f"    ⚠️ No 'included' data found in detailed job response for job ID: {job_id}")
                else:
                    log.warning(f"    ⚠️ No detailed job data returned for job ID: {job_id}")
                
                # Get job skills information
                log.info(f"🔍 Fetching job skills for job ID: {job_id}")
                job_skills = api.get_job_skills(job_id)
                if job_skills:
                    log.info(f"✅ Job skills data retrieved for job ID: {job_id}")
                    
                    # Extract skills from the job skills response
                    if "included" in job_skills:
                        skills_list = []
                        for item in job_skills["included"]:
                            if item.get("$type") == "com.linkedin.voyager.jobs.JobSkill":
                                skill_name = item.get("name", "")
                                if skill_name:
                                    skills_list.append({
                                        "name": skill_name,
                                        "skill_id": item.get("entityUrn", "").split(":")[-1] if item.get("entityUrn") else "",
                                        "match_score": item.get("matchScore", 0),
                                        "required": item.get("required", False),
                                        "skill_type": item.get("skillType", "")
                                    })
                        
                        if skills_list:
                            job_details["detailed_skills"] = skills_list
                            log.info(f"    🎯 Found {len(skills_list)} skills for job ID: {job_id}")
                            
                            # Log the top skills (first 5)
                            top_skills = skills_list[:5]
                            for skill in top_skills:
                                required_flag = " (Required)" if skill.get("required") else ""
                                match_score = skill.get("match_score", 0)
                                log.info(f"      • {skill['name']}{required_flag} (Match: {match_score})")
                            
                            if len(skills_list) > 5:
                                log.info(f"      ... and {len(skills_list) - 5} more skills")
                        else:
                            log.info(f"    ℹ️ No skills found for job ID: {job_id}")
                    else:
                        log.warning(f"    ⚠️ No 'included' data found in job skills response for job ID: {job_id}")
                else:
                    log.warning(f"    ⚠️ No job skills data returned for job ID: {job_id}")
                
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
        jobs_with_details = sum(1 for job in all_jobs if job.get("detailed_description") or job.get("detailed_skills"))
        jobs_with_skills = sum(1 for job in all_jobs if job.get("detailed_skills"))
        
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
    jobs_with_details = sum(1 for job in jobs if job.get("detailed_description") or job.get("detailed_skills"))
    jobs_with_skills = sum(1 for job in jobs if job.get("detailed_skills"))
    
    log.info(f"🎯 Job search pipeline complete! Found {len(jobs)} positions")
    log.info(f"📊 Enhanced data: {jobs_with_details} jobs with detailed descriptions, {jobs_with_skills} jobs with skills analysis")
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

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    search_and_save_jobs()

if __name__ == "__main__":
    main() 