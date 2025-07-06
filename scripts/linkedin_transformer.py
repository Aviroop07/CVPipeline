#!/usr/bin/env python3
"""
LinkedIn to JSON-Resume transformation module.

This module provides functions to transform LinkedIn profile data into JSON-Resume format.
"""

import json, pathlib, sys, os, re, requests
from functools import lru_cache
from linkedin_api import Linkedin
from requests.cookies import RequestsCookieJar
import config

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / config.DATA_DIR / config.LINKEDIN_RAW_FILE
CV_FILE = ROOT / config.RESUME_JSON_FILE

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

def _company_url(name: str, company_urn: str = None) -> str:
    """Get LinkedIn company URL from company name.
    
    Args:
        name (str): Company name
        company_urn (str, optional): Company URN (unused currently)
        
    Returns:
        str: LinkedIn company URL or empty string if not found
    """
    print(f'🔍 Searching for company: {name}')
    if not name:
        return ""
    
    # Try multiple approaches to find the company URL
    
    # Approach 1: Try get_company with the name
    try:
        company_data = _get_linkedin_api().get_company(name)
        print(f'📊 Company data for {name}: {company_data}')
        
        if company_data and company_data.get("universalName"):
            universal_name = company_data["universalName"]
            url = f"https://www.linkedin.com/company/{universal_name}/"
            print(f'✅ Found LinkedIn URL for {name}: {url}')
            return url
    except Exception as e:
        print(f'❌ Error with get_company for {name}: {e}')
    
    # Approach 2: Try search_companies
    try:
        search_results = _get_linkedin_api().search_companies(keywords=[name], limit=1)
        print(f'🔍 Search results for {name}: {search_results}')
        
        if search_results:
            # Try to get the company using the first result's name
            first_result = search_results[0]
            if first_result.get("name"):
                try:
                    company_data = _get_linkedin_api().get_company(first_result["name"])
                    if company_data and company_data.get("universalName"):
                        universal_name = company_data["universalName"]
                        url = f"https://www.linkedin.com/company/{universal_name}/"
                        print(f'✅ Found LinkedIn URL for {name} via search: {url}')
                        return url
                except Exception as e:
                    print(f'❌ Error getting company data for search result {first_result["name"]}: {e}')
    except Exception as e:
        print(f'❌ Error with search_companies for {name}: {e}')
    
    # Approach 3: Try common variations for known companies
    common_variations = {
        "PwC India": "pwc",
        "Neurologic-ai": "neurologic-ai"
    }
    
    if name in common_variations:
        try:
            company_data = _get_linkedin_api().get_company(common_variations[name])
            if company_data and company_data.get("universalName"):
                universal_name = company_data["universalName"]
                url = f"https://www.linkedin.com/company/{universal_name}/"
                print(f'✅ Found LinkedIn URL for {name} via common variation: {url}')
                return url
        except Exception as e:
            print(f'❌ Error with common variation for {name}: {e}')
    
    print(f'❌ No LinkedIn URL found for company: {name}')
    return ""

def _school_url(name: str, school_urn: str = None) -> str:
    """Get LinkedIn school URL from school name.
    
    Args:
        name (str): School name
        school_urn (str, optional): School URN (unused currently)
        
    Returns:
        str: LinkedIn school URL or empty string if not found
    """
    print(f'🎓 Searching for school: {name}')
    if not name:
        return ""
    
    # Try multiple approaches to find the school URL
    
    # Approach 1: Try get_school with the name
    try:
        school_data = _get_linkedin_api().get_school(name)
        print(f'📊 School data for {name}: {school_data}')
        
        if school_data and school_data.get("universalName"):
            universal_name = school_data["universalName"]
            url = f"https://www.linkedin.com/school/{universal_name}/"
            print(f'✅ Found LinkedIn URL for {name}: {url}')
            return url
    except Exception as e:
        print(f'❌ Error with get_school for {name}: {e}')
    
    # Approach 2: Try search_companies (schools often appear in company search)
    try:
        search_results = _get_linkedin_api().search_companies(keywords=[name], limit=1)
        print(f'🔍 Search results for school {name}: {search_results}')
        
        if search_results:
            # Try to get the school using the first result's name
            first_result = search_results[0]
            if first_result.get("name"):
                try:
                    school_data = _get_linkedin_api().get_school(first_result["name"])
                    if school_data and school_data.get("universalName"):
                        universal_name = school_data["universalName"]
                        url = f"https://www.linkedin.com/school/{universal_name}/"
                        print(f'✅ Found LinkedIn URL for {name} via search: {url}')
                        return url
                except Exception as e:
                    print(f'❌ Error getting school data for search result {first_result["name"]}: {e}')
    except Exception as e:
        print(f'❌ Error with search_companies for school {name}: {e}')
    
    # Approach 3: Try common variations for known schools
    common_variations = {
        "Jadavpur University": "jadavpur-university",
        "Burdwan Municipal High School": "burdwan-municipal-high-school"
    }
    
    if name in common_variations:
        try:
            school_data = _get_linkedin_api().get_school(common_variations[name])
            if school_data and school_data.get("universalName"):
                universal_name = school_data["universalName"]
                url = f"https://www.linkedin.com/school/{universal_name}/"
                print(f'✅ Found LinkedIn URL for {name} via common variation: {url}')
                return url
        except Exception as e:
            print(f'❌ Error with common variation for school {name}: {e}')
    
    print(f'❌ No LinkedIn URL found for school: {name}')
    return ""

def transform_linkedin_to_resume(raw_data):
    """Transform LinkedIn profile data to JSON-Resume format.
    
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

        "work": [
            {
                "name": w.get("companyName",""),
                "position": w.get("title",""),
                "location": w.get("locationName",""),
                "startDate": _date(w.get("timePeriod",{}).get("startDate")),
                "endDate": _date(w.get("timePeriod",{}).get("endDate")),
                "summary": w.get("description",""),
                "url": _company_url(w.get("companyName", ""))
            }
            for w in raw_data.get("experience",[])
        ],

        "education": [
            {
                "institution": e.get("schoolName",""),
                "area": e.get("fieldOfStudy",""),
                "studyType": e.get("degreeName",""),
                "score": e.get("grade",""),
                "startDate": _date(e.get("timePeriod",{}).get("startDate")),
                "endDate": _date(e.get("timePeriod",{}).get("endDate")),
                "url": _school_url(e.get("schoolName", ""))
            }
            for e in raw_data.get("education",[])
        ],

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

    return resume_data

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
        input_path = RAW_FILE
        
    if not input_path.exists():
        sys.exit(f"✖  Run the LinkedIn scraper first – {config.DATA_DIR}/{config.LINKEDIN_RAW_FILE} missing.")
    
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
        output_path = CV_FILE
        
    output_path.write_text(json.dumps(resume_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅  {config.RESUME_JSON_FILE} refreshed.")
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
    if CV_FILE.exists():
        file_content = CV_FILE.read_text(encoding="utf-8").strip()
        if file_content:  # Only try to parse if file has content
            old_resume = json.loads(file_content)

    if new_resume == old_resume:
        print("ℹ  No changes – résumé already up-to-date.")
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