#!/usr/bin/env python3
"""
LinkedIn to JSON-Resume transformation module.

This module provides functions to transform LinkedIn profile data into JSON-Resume format.
"""

import json, pathlib, sys, os, asyncio, logging
from functools import lru_cache
from typing import Tuple, List, Dict, Any
from linkedin_api import Linkedin
from requests.cookies import RequestsCookieJar
from resume.utils import config
from resume.utils import entity_search
from resume.utils import url_validator
from resume.utils import api_cache

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Remove ROOT, RAW_FILE, CV_FILE assignments

def _date(ldict):
    """Convert LinkedIn date dict to YYYY-MM format.
    
    Args:
        ldict (dict): LinkedIn date dict with 'year' and 'month' keys
        
    Returns:
        str: Date in YYYY-MM format, or None if invalid
    """
    if not ldict: 
        return None
    y = ldict.get("year")
    m = ldict.get("month", 1)
    return f"{y:04d}-{m:02d}" if y else None

@lru_cache()
def _get_linkedin_api():
    """Return a cached authenticated LinkedIn client (cookies preferred)."""
    li_at = os.getenv("LI_AT", "").strip()
    jsessionid = os.getenv("LI_JSESSIONID", "").strip()
    if li_at and jsessionid:
        jar = RequestsCookieJar()
        jar.set("li_at", li_at, domain=".linkedin.com", path="/")
        jar.set("JSESSIONID", jsessionid, domain=".linkedin.com", path="/")
        return Linkedin("", "", cookies=jar)
    # fallback uses credentials (may require 2FA)
    return Linkedin(os.getenv("LI_USER", ""), os.getenv("LI_PASS", ""))

def _extract_urn_id_from_entity_urn(entity_urn: str) -> str:
    """Extract URN ID from LinkedIn entity URN.
    
    Args:
        entity_urn (str): Entity URN like "urn:li:fs_position:(ACoAADhwtxQBsXApQoktnF30iLk5zpuxpsuLAvA,2418598327)"
        
    Returns:
        str: URN ID like "ACoAADhwtxQBsXApQoktnF30iLk5zpuxpsuLAvA" or empty string if not found
    """
    try:
        # Extract content between parentheses
        start = entity_urn.find('(')
        end = entity_urn.find(')')
        if start != -1 and end != -1:
            content = entity_urn[start+1:end]
            # Split by comma and take the first part (URN ID)
            parts = content.split(',')
            if parts:
                return parts[0].strip()
    except Exception as e:
        log.error(f'❌ Error extracting URN ID from {entity_urn}: {e}')
    return ""

def _linkedin_company_search_fallback(name: str, entity_urn: str = None) -> Tuple[str, str]:
    """Fallback LinkedIn company search when Google KG fails.
    
    Args:
        name (str): Company name
        entity_urn (str, optional): Entity URN from experience data for profile fallback
        
    Returns:
        Tuple[str, str]: (LinkedIn company URL, public_id) or ("", "") if not found
    """
    log.info(f'🔍 LinkedIn fallback search for company: {name}')
    if not name:
        return "", ""
    
    try:
        # Try get_company with the name (with caching)
        if config.API_CACHE_ENABLED:
            company_data = api_cache.cached_api_call(
                "linkedin_get_company",
                {"company_name": name},
                _get_linkedin_api().get_company,
                name
            )
        else:
            company_data = _get_linkedin_api().get_company(name)
        
        if company_data and company_data.get("universalName"):
            # Validate that the LinkedIn result name matches our query
            linkedin_name = company_data.get("name", "")
            if linkedin_name and entity_search.names_match(name, linkedin_name):
                universal_name = company_data["universalName"]
                url = f"https://www.linkedin.com/company/{universal_name}/"
                log.info(f'Found matching LinkedIn URL for {name}: {url} (result: {linkedin_name})')
                return url, universal_name
            else:
                log.warning(f'⚠️ LinkedIn name mismatch for {name}: got "{linkedin_name}", skipping')
    except Exception as e:
        log.error(f'❌ Error with get_company for {name}: {e}')
    
    try:
        # Try search_companies with higher limit to check multiple results (with caching)
        if config.API_CACHE_ENABLED:
            search_results = api_cache.cached_api_call(
                "linkedin_search_companies",
                {"keywords": [name], "limit": 10},
                _get_linkedin_api().search_companies,
                keywords=[name], limit=10
            )
        else:
            search_results = _get_linkedin_api().search_companies(keywords=[name], limit=10)
        
        log.info(f'Found {len(search_results)} company search results for {name}')
        if search_results:
            for i, result in enumerate(search_results):
                result_name = result.get("name", "")
                if not result_name:
                    continue
                    
                log.debug(f'Checking result {i+1}: "{result_name}"')
                try:
                    if config.API_CACHE_ENABLED:
                        company_data = api_cache.cached_api_call(
                            "linkedin_get_company",
                            {"company_name": result_name},
                            _get_linkedin_api().get_company,
                            result_name
                        )
                    else:
                        company_data = _get_linkedin_api().get_company(result_name)
                    
                    if company_data and company_data.get("universalName"):
                        # Validate that the LinkedIn result name matches our query
                        linkedin_name = company_data.get("name", "")
                        if linkedin_name and entity_search.names_match(name, linkedin_name):
                            universal_name = company_data["universalName"]
                            url = f"https://www.linkedin.com/company/{universal_name}/"
                            log.info(f'Found matching LinkedIn URL for {name} via search result {i+1}: {url} (result: {linkedin_name})')
                            return url, universal_name
                        else:
                            log.debug(f'LinkedIn search name mismatch for {name}: got "{linkedin_name}", checking next result')
                except Exception as e:
                    log.warning(f'Error getting company data for search result {i+1}: {e}')
    except Exception as e:
        log.error(f'❌ Error with search_companies for {name}: {e}')
    
    # Try profile fallback using entity URN if available
    if entity_urn:
        urn_id = _extract_urn_id_from_entity_urn(entity_urn)
        if urn_id:
            log.info(f'Trying profile fallback for {name} using URN ID: {urn_id}')
            try:
                if config.API_CACHE_ENABLED:
                    profile_data = api_cache.cached_api_call(
                        "linkedin_get_profile",
                        {"urn_id": urn_id},
                        _get_linkedin_api().get_profile,
                        urn_id=urn_id
                    )
                else:
                    profile_data = _get_linkedin_api().get_profile(urn_id=urn_id)
                
                if profile_data:
                    # Look for work experience matching the company name
                    experiences = profile_data.get("experience", [])
                    log.debug(f'Found {len(experiences)} experiences in profile for {name}')
                    for i, exp in enumerate(experiences):
                        exp_company = exp.get("companyName", "")
                        if exp_company and entity_search.names_match(name, exp_company):
                            log.info(f'Profile experience "{exp_company}" matches "{name}"')
                            # Try to get company data from the experience
                            company_urn = exp.get("companyUrn", "")
                            if company_urn:
                                try:
                                    # Extract company ID from URN
                                    company_id = company_urn.split(":")[-1] if ":" in company_urn else company_urn
                                    if config.API_CACHE_ENABLED:
                                        company_data = api_cache.cached_api_call(
                                            "linkedin_get_company",
                                            {"company_id": company_id},
                                            _get_linkedin_api().get_company,
                                            company_id
                                        )
                                    else:
                                        company_data = _get_linkedin_api().get_company(company_id)
                                    
                                    if company_data and company_data.get("universalName"):
                                        universal_name = company_data["universalName"]
                                        url = f"https://www.linkedin.com/company/{universal_name}/"
                                        log.info(f'Found LinkedIn URL for {name} via profile fallback: {url}')
                                        return url, universal_name
                                except Exception as e:
                                    log.warning(f'Error getting company from profile fallback: {e}')
            except Exception as e:
                log.error(f'❌ Error with profile fallback for {name}: {e}')
    
    log.warning(f"❌ No LinkedIn URL found for company: {name}")
    return "", ""

def _linkedin_school_search_fallback(name: str, entity_urn: str = None) -> Tuple[str, str]:
    """Fallback LinkedIn school search when Google KG fails.
    
    Args:
        name (str): School name
        entity_urn (str, optional): Entity URN from education data for profile fallback
        
    Returns:
        Tuple[str, str]: (LinkedIn school URL, public_id) or ("", "") if not found
    """
    log.info(f'🎓 LinkedIn fallback search for school: {name}')
    if not name:
        return "", ""
    
    try:
        # Try get_school with the name (with caching)
        if config.API_CACHE_ENABLED:
            school_data = api_cache.cached_api_call(
                "linkedin_get_school",
                {"school_name": name},
                _get_linkedin_api().get_school,
                name
            )
        else:
            school_data = _get_linkedin_api().get_school(name)
        
        if school_data and school_data.get("universalName"):
            # Validate that the LinkedIn result name matches our query
            linkedin_name = school_data.get("name", "")
            if linkedin_name and entity_search.names_match(name, linkedin_name):
                universal_name = school_data["universalName"]
                url = f"https://www.linkedin.com/school/{universal_name}/"
                log.info(f'Found matching LinkedIn URL for {name}: {url} (result: {linkedin_name})')
                return url, universal_name
            else:
                log.warning(f'⚠️ LinkedIn school name mismatch for {name}: got "{linkedin_name}", skipping')
    except Exception as e:
        log.error(f'❌ Error with get_school for {name}: {e}')
    
    try:
        # Try search_companies (schools often appear in company search) with higher limit (with caching)
        if config.API_CACHE_ENABLED:
            search_results = api_cache.cached_api_call(
                "linkedin_search_companies",
                {"keywords": [name], "limit": 10},
                _get_linkedin_api().search_companies,
                keywords=[name], limit=10
            )
        else:
            search_results = _get_linkedin_api().search_companies(keywords=[name], limit=10)
        
        log.info(f'Found {len(search_results)} company search results for school {name}')
        if search_results:
            for i, result in enumerate(search_results):
                result_name = result.get("name", "")
                if not result_name:
                    continue
                    
                log.debug(f'Checking school result {i+1}: "{result_name}"')
                try:
                    if config.API_CACHE_ENABLED:
                        school_data = api_cache.cached_api_call(
                            "linkedin_get_school",
                            {"school_name": result_name},
                            _get_linkedin_api().get_school,
                            result_name
                        )
                    else:
                        school_data = _get_linkedin_api().get_school(result_name)
                    
                    if school_data and school_data.get("universalName"):
                        # Validate that the LinkedIn result name matches our query
                        linkedin_name = school_data.get("name", "")
                        if linkedin_name and entity_search.names_match(name, linkedin_name):
                            universal_name = school_data["universalName"]
                            url = f"https://www.linkedin.com/school/{universal_name}/"
                            log.info(f'Found matching LinkedIn URL for {name} via search result {i+1}: {url} (result: {linkedin_name})')
                            return url, universal_name
                        else:
                            log.debug(f'LinkedIn school search name mismatch for {name}: got "{linkedin_name}", checking next result')
                except Exception as e:
                    log.warning(f'Error getting school data for search result {i+1}: {e}')
    except Exception as e:
        log.error(f'❌ Error with search_companies for school {name}: {e}')
    
    # Try profile fallback using entity URN if available
    if entity_urn:
        urn_id = _extract_urn_id_from_entity_urn(entity_urn)
        if urn_id:
            log.info(f'Trying profile fallback for school {name} using URN ID: {urn_id}')
            try:
                if config.API_CACHE_ENABLED:
                    profile_data = api_cache.cached_api_call(
                        "linkedin_get_profile",
                        {"urn_id": urn_id},
                        _get_linkedin_api().get_profile,
                        urn_id=urn_id
                    )
                else:
                    profile_data = _get_linkedin_api().get_profile(urn_id=urn_id)
                
                if profile_data:
                    # Look for education experience matching the school name
                    education_entries = profile_data.get("education", [])
                    log.debug(f'Found {len(education_entries)} education entries in profile for {name}')
                    for i, edu in enumerate(education_entries):
                        edu_school = edu.get("schoolName", "")
                        if edu_school and entity_search.names_match(name, edu_school):
                            log.info(f'Profile education "{edu_school}" matches "{name}"')
                            # Try to get school data from the education entry
                            school_urn = edu.get("schoolUrn", "")
                            if school_urn:
                                try:
                                    # Extract school ID from URN
                                    school_id = school_urn.split(":")[-1] if ":" in school_urn else school_urn
                                    if config.API_CACHE_ENABLED:
                                        school_data = api_cache.cached_api_call(
                                            "linkedin_get_school",
                                            {"school_id": school_id},
                                            _get_linkedin_api().get_school,
                                            school_id
                                        )
                                    else:
                                        school_data = _get_linkedin_api().get_school(school_id)
                                    
                                    if school_data and school_data.get("universalName"):
                                        universal_name = school_data["universalName"]
                                        url = f"https://www.linkedin.com/school/{universal_name}/"
                                        log.info(f'Found LinkedIn URL for {name} via profile fallback: {url}')
                                        return url, universal_name
                                except Exception as e:
                                    log.warning(f'Error getting school from profile fallback: {e}')
            except Exception as e:
                log.error(f'❌ Error with profile fallback for school {name}: {e}')
    
    log.warning(f"❌ No LinkedIn URL found for school: {name}")
    return "", ""

def _company_url_and_id(name: str, company_urn: str = None, entity_urn: str = None) -> Tuple[str, str]:
    """Get company URL and ID using Google Knowledge Graph with LinkedIn fallback.
    
    Args:
        name (str): Company name
        company_urn (str, optional): Company URN (unused, for compatibility)
        entity_urn (str, optional): Entity URN from experience data for profile fallback
        
    Returns:
        Tuple[str, str]: (Company URL, entity_id/public_id) or ("", "") if not found
    """
    # Try Google Knowledge Graph first
    url, entity_id = entity_search.company_url_and_id(name, company_urn)
    if url and entity_id:
        # Validate the URL works
        if url_validator.url_works(url, timeout=10.0):
            log.info(f"Google KG URL validated for {name}: {url}")
            return url, entity_id
        else:
            log.warning(f"Google KG URL failed validation for {name}: {url}")
    
    # Fallback to LinkedIn search
    log.info(f"Google KG failed for {name}, trying LinkedIn fallback...")
    linkedin_url, linkedin_id = _linkedin_company_search_fallback(name, entity_urn)
    if linkedin_url and linkedin_id:
        # Validate LinkedIn URL
        if url_validator.url_works(linkedin_url, timeout=10.0):
            log.info(f"LinkedIn URL validated for {name}: {linkedin_url}")
            return linkedin_url, linkedin_id
        else:
            log.warning(f"LinkedIn URL failed validation for {name}: {linkedin_url}")
    
    # Both methods failed or URLs don't work
    log.warning(f"❌ No working URLs found for company: {name}")
    return "", ""

def _company_url(name: str, company_urn: str = None, entity_urn: str = None) -> str:
    """Get company URL from company name (Google KG or LinkedIn fallback).
    
    Args:
        name (str): Company name
        company_urn (str, optional): Company URN (unused, for compatibility)
        entity_urn (str, optional): Entity URN from experience data for profile fallback
        
    Returns:
        str: Company URL (official website or LinkedIn) or empty string if not found
    """
    url, _ = _company_url_and_id(name, company_urn, entity_urn)
    return url

def _school_url_and_id(name: str, school_urn: str = None, entity_urn: str = None) -> Tuple[str, str]:
    """Get school URL and ID using Google Knowledge Graph with LinkedIn fallback.
    
    Args:
        name (str): School name
        school_urn (str, optional): School URN (unused, for compatibility)
        entity_urn (str, optional): Entity URN from education data for profile fallback
        
    Returns:
        Tuple[str, str]: (School URL, entity_id/public_id) or ("", "") if not found
    """
    # Try Google Knowledge Graph first
    url, entity_id = entity_search.school_url_and_id(name, school_urn)
    if url and entity_id:
        # Validate the URL works
        if url_validator.url_works(url, timeout=10.0):
            log.info(f"Google KG URL validated for {name}: {url}")
            return url, entity_id
        else:
            log.warning(f"Google KG URL failed validation for {name}: {url}")
    
    # Fallback to LinkedIn search
    log.info(f"Google KG failed for {name}, trying LinkedIn fallback...")
    linkedin_url, linkedin_id = _linkedin_school_search_fallback(name, entity_urn)
    if linkedin_url and linkedin_id:
        # Validate LinkedIn URL
        if url_validator.url_works(linkedin_url, timeout=10.0):
            log.info(f"LinkedIn URL validated for {name}: {linkedin_url}")
            return linkedin_url, linkedin_id
        else:
            log.warning(f"LinkedIn URL failed validation for {name}: {linkedin_url}")
    
    # Both methods failed or URLs don't work
    log.warning(f"❌ No working URLs found for school: {name}")
    return "", ""

def _school_url(name: str, school_urn: str = None, entity_urn: str = None) -> str:
    """Get school URL from school name (Google KG or LinkedIn fallback).
    
    Args:
        name (str): School name
        school_urn (str, optional): School URN (unused, for compatibility)
        entity_urn (str, optional): Entity URN from education data for profile fallback
        
    Returns:
        str: School URL (official website or LinkedIn) or empty string if not found
    """
    url, _ = _school_url_and_id(name, school_urn, entity_urn)
    return url

async def _company_url_and_id_async(name: str, company_urn: str = None, entity_urn: str = None) -> Tuple[str, str]:
    """Async wrapper for company URL and ID extraction.
    
    Args:
        name (str): Company name
        company_urn (str, optional): Company URN (unused, for compatibility)
        entity_urn (str, optional): Entity URN from experience data for profile fallback
        
    Returns:
        Tuple[str, str]: (Company URL, entity_id/public_id) or ("", "") if not found
    """
    # Run the synchronous function in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _company_url_and_id, name, company_urn, entity_urn)

async def _school_url_and_id_async(name: str, school_urn: str = None, entity_urn: str = None) -> Tuple[str, str]:
    """Async wrapper for school URL and ID extraction.
    
    Args:
        name (str): School name
        school_urn (str, optional): School URN (unused, for compatibility)
        entity_urn (str, optional): Entity URN from education data for profile fallback
        
    Returns:
        Tuple[str, str]: (School URL, entity_id/public_id) or ("", "") if not found
    """
    # Run the synchronous function in a thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _school_url_and_id, name, school_urn, entity_urn)

async def _process_work_experience_async(w: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single work experience entry asynchronously.
    
    Args:
        w (Dict): Work experience data from LinkedIn
        
    Returns:
        Dict: Processed work entry
    """
    company_name = w.get("companyName", "")
    entity_urn = w.get("entityUrn", "")
    company_url, company_public_id = await _company_url_and_id_async(company_name, entity_urn=entity_urn)
    
    return {
        "name": company_name,
        "position": w.get("title", ""),
        "location": w.get("locationName", ""),
        "startDate": _date(w.get("timePeriod", {}).get("startDate")),
        "endDate": _date(w.get("timePeriod", {}).get("endDate")),
        "summary": w.get("description", ""),
        "url": company_url,
        "public_id": company_public_id
    }

async def _process_education_entry_async(e: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single education entry asynchronously.
    
    Args:
        e (Dict): Education data from LinkedIn
        
    Returns:
        Dict: Processed education entry
    """
    school_name = e.get("schoolName", "")
    entity_urn = e.get("entityUrn", "")
    school_url, school_public_id = await _school_url_and_id_async(school_name, entity_urn=entity_urn)
    
    return {
        "institution": school_name,
        "area": e.get("fieldOfStudy", ""),
        "studyType": e.get("degreeName", ""),
        "score": e.get("grade", ""),
        "startDate": _date(e.get("timePeriod", {}).get("startDate")),
        "endDate": _date(e.get("timePeriod", {}).get("endDate")),
        "url": school_url,
        "public_id": school_public_id
    }

async def transform_linkedin_to_resume_async(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform LinkedIn profile data to JSON-Resume format asynchronously.
    
    Args:
        raw_data (dict): Raw LinkedIn profile data
        
    Returns:
        dict: JSON-Resume formatted data
    """
    resume_data = {
        "basics": {
            "name": f"{raw_data.get('firstName','')} {raw_data.get('lastName','')}".strip(),
            "label": raw_data.get("headline",""),
            "email": raw_data.get("contact_info",{}).get("email_address",""),
            "phone": next((p["number"] for p in raw_data.get("contact_info",{}).get("phone_numbers",[]) if p.get("type")=="MOBILE"),""),
            "location": raw_data.get("geoCountryName",""),
            "public_id": raw_data.get("public_id", "")
        },

        "work": [],
        "education": [],

        "awards": [
            {
                "title": h.get("title",""),
                "date": _date(h.get("issueDate")),
                "awarder": h.get("issuer",""),
                "summary": h.get("description",""),
                "url": h.get("url","")
            }
            for h in raw_data.get("honors",[])
        ],

        "projects": [
            {
                "name": p.get("title",""),
                "description": p.get("description",""),
                "startDate": _date(p.get("timePeriod",{}).get("startDate")),
                "endDate": _date(p.get("timePeriod",{}).get("endDate")),
                "url": p.get("url","")
            }
            for p in raw_data.get("projects",[])
        ],

        "skills": [{"name": s["name"]} for s in raw_data.get("skills",[])],

        "languages": [
            {
                "language": l.get("name",""),
                "fluency": l.get("proficiency","")
            }
            for l in raw_data.get("languages",[])
        ]
    }

    # Process work experiences and education concurrently
    work_tasks = [_process_work_experience_async(w) for w in raw_data.get("experience", [])]
    education_tasks = [_process_education_entry_async(e) for e in raw_data.get("education", [])]
    
    # Wait for all URL extractions to complete
    if work_tasks or education_tasks:
        log.info(f"🚀 Processing {len(work_tasks)} work experiences and {len(education_tasks)} education entries concurrently...")
        
        # Use asyncio.gather to run all tasks concurrently
        all_tasks = work_tasks + education_tasks
        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Separate work and education results
        work_results = results[:len(work_tasks)]
        education_results = results[len(work_tasks):]
        
        # Handle results and exceptions
        for i, result in enumerate(work_results):
            if isinstance(result, Exception):
                log.error(f"❌ Error processing work experience {i}: {result}")
                # Create a fallback entry
                w = raw_data["experience"][i]
                resume_data["work"].append({
                    "name": w.get("companyName", ""),
                    "position": w.get("title", ""),
                    "location": w.get("locationName", ""),
                    "startDate": _date(w.get("timePeriod", {}).get("startDate")),
                    "endDate": _date(w.get("timePeriod", {}).get("endDate")),
                    "summary": w.get("description", ""),
                    "url": "",
                    "public_id": ""
                })
            else:
                resume_data["work"].append(result)
        
        for i, result in enumerate(education_results):
            if isinstance(result, Exception):
                log.error(f"❌ Error processing education entry {i}: {result}")
                # Create a fallback entry
                e = raw_data["education"][i]
                resume_data["education"].append({
                    "institution": e.get("schoolName", ""),
                    "area": e.get("fieldOfStudy", ""),
                    "studyType": e.get("degreeName", ""),
                    "score": e.get("grade", ""),
                    "startDate": _date(e.get("timePeriod", {}).get("startDate")),
                    "endDate": _date(e.get("timePeriod", {}).get("endDate")),
                    "url": "",
                    "public_id": ""
                })
            else:
                resume_data["education"].append(result)

    return resume_data

def transform_linkedin_to_resume(raw_data):
    """Transform LinkedIn profile data to JSON-Resume format (sync wrapper).
    
    Args:
        raw_data (dict): Raw LinkedIn profile data
        
    Returns:
        dict: JSON-Resume formatted data
    """
    # Run the async version in an event loop
    return asyncio.run(transform_linkedin_to_resume_async(raw_data))

def load_linkedin_data(input_path=None):
    """Load LinkedIn raw data from file.
    
    Args:
        input_path (pathlib.Path, optional): Custom input path. Defaults to configured path.
        
    Returns:
        dict: Raw LinkedIn data
        
    Raises:
        SystemExit: If file doesn't exist
    """
    if input_path is None:
        input_path = config.PROJECT_ROOT / config.DATA_DIR / config.LINKEDIN_RAW_FILE
    if not (input_path.exists()):
        sys.exit(f"Run the LinkedIn scraper first  {config.DATA_DIR}/{config.LINKEDIN_RAW_FILE} missing.")
    
    return json.loads(input_path.read_text(encoding="utf-8"))

def save_resume_data(resume_data, output_path=None):
    """Save resume data to JSON file.
    
    Args:
        resume_data (dict): Resume data to save
        output_path (pathlib.Path, optional): Custom output path. Defaults to configured path.
        
    Returns:
        pathlib.Path: Path where data was saved
    """
    if output_path is None:
        output_path = config.PROJECT_ROOT / config.DATA_DIR / config.RESUME_JSON_FILE
        
    output_path.write_text(json.dumps(resume_data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"✅  {config.DATA_DIR}/{config.RESUME_JSON_FILE} refreshed.")
    return output_path

def transform_linkedin_data():
    """Complete LinkedIn to JSON-Resume transformation pipeline.
    
    Returns:
        dict: Transformed resume data
        
    Raises:
        SystemExit: If no changes detected (exit code 1) or if transformation fails
    """
    # Load raw LinkedIn data
    raw_data = load_linkedin_data()
    
    # Transform to JSON-Resume format
    new_resume = transform_linkedin_to_resume(raw_data)

    # Check if resume has changed
    old_resume = {}
    if (config.PROJECT_ROOT / config.DATA_DIR / config.RESUME_JSON_FILE).exists():
        file_content = (config.PROJECT_ROOT / config.DATA_DIR / config.RESUME_JSON_FILE).read_text(encoding="utf-8").strip()
        if file_content:  # Only try to parse if file has content
            old_resume = json.loads(file_content)

    if new_resume == old_resume:
        log.info("ℹ  No changes – résumé already up-to-date.")
        sys.exit(1)  # signals "skip commit" to the Action

    # Save transformed data
    save_resume_data(new_resume)
    return new_resume

# Legacy main function for backward compatibility
def main():
    """Main function for standalone script execution."""
    transform_linkedin_data()

if __name__ == "__main__":
    main() 