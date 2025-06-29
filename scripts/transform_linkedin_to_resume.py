#!/usr/bin/env python3
"""
Transform data/linkedin_raw.json → resume.json  (JSON-Resume 1.0 schema)
Exits with code 1 when the résumé did not change – so the GitHub Action
can skip committing an empty diff.
"""
import json, pathlib, sys, datetime as _dt, os, re, requests
from functools import lru_cache
from linkedin_api import Linkedin
from requests.cookies import RequestsCookieJar

ROOT     = pathlib.Path(__file__).resolve().parent.parent
RAW_FILE = ROOT / "data"   / "linkedin_raw.json"
CV_FILE  = ROOT / "resume.json"

# ────────────────────────────────────────────────────────────────────────────
def _date(ldict):
    """{'year':2024,'month':7} ➜ '2024-07'   |   {} or None ➜ None"""
    if not ldict: return None
    y = ldict.get("year")
    m = ldict.get("month", 1)
    return f"{y:04d}-{m:02d}" if y else None

# ─── Initialise a lightweight Linkedin client for org look-ups ────────────────

@lru_cache()
def _api():
    """Return a cached authenticated Linkedin client (cookies preferred)."""
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
    print(f'🔍 Searching for company: {name}')
    if not name:
        return ""
    
    # Try multiple approaches to find the company URL
    
    # Approach 1: Try get_company with the name
    try:
        company_data = _api().get_company(name)
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
        search_results = _api().search_companies(keywords=[name], limit=1)
        print(f'🔍 Search results for {name}: {search_results}')
        
        if search_results:
            # Try to get the company using the first result's name
            first_result = search_results[0]
            if first_result.get("name"):
                try:
                    company_data = _api().get_company(first_result["name"])
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
            company_data = _api().get_company(common_variations[name])
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
    print(f'🎓 Searching for school: {name}')
    if not name:
        return ""
    
    # Try multiple approaches to find the school URL
    
    # Approach 1: Try get_school with the name
    try:
        school_data = _api().get_school(name)
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
        search_results = _api().search_companies(keywords=[name], limit=1)
        print(f'🔍 Search results for school {name}: {search_results}')
        
        if search_results:
            # Try to get the school using the first result's name
            first_result = search_results[0]
            if first_result.get("name"):
                try:
                    school_data = _api().get_school(first_result["name"])
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
            school_data = _api().get_school(common_variations[name])
            if school_data and school_data.get("universalName"):
                universal_name = school_data["universalName"]
                url = f"https://www.linkedin.com/school/{universal_name}/"
                print(f'✅ Found LinkedIn URL for {name} via common variation: {url}')
                return url
        except Exception as e:
            print(f'❌ Error with common variation for school {name}: {e}')
    
    print(f'❌ No LinkedIn URL found for school: {name}')
    return ""

def transform(raw):
    j = {
        "basics": {
            "name"     : f"{raw.get('firstName','')} {raw.get('lastName','')}".strip(),
            "label"    : raw.get("headline",""),
            "email"    : raw.get("contact_info",{}).get("email_address",""),
            "phone"    : next((p["number"] for p in raw.get("contact_info",{}).get("phone_numbers",[]) if p.get("type")=="MOBILE"),""),
            "location" : {
                "city"        : raw.get("geoLocationName",""),
                "countryCode" : raw.get("location",{}).get("basicLocation",{}).get("countryCode","")
            },
            "summary"  : raw.get("summary",""),
            "public_id": raw.get("public_id", "")
        },

        "work": [
            {
                "name"      : w.get("companyName",""),
                "position"  : w.get("title",""),
                "location"  : w.get("locationName",""),
                "startDate" : _date(w.get("timePeriod",{}).get("startDate")),
                "endDate"   : _date(w.get("timePeriod",{}).get("endDate")),
                "summary"   : w.get("description",""),
                "url"       : _company_url(w.get("companyName", ""))
            }
            for w in raw.get("experience",[])
        ],

        "education": [
            {
                "institution": e.get("schoolName",""),
                "area"       : e.get("fieldOfStudy",""),
                "studyType"  : e.get("degreeName",""),
                "score"      : e.get("grade",""),
                "startDate"  : _date(e.get("timePeriod",{}).get("startDate")),
                "endDate"    : _date(e.get("timePeriod",{}).get("endDate")),
                "url"        : _school_url(e.get("schoolName", ""))
            }
            for e in raw.get("education",[])
        ],

        "certificates": [
            {
                "name"   : c.get("name",""),
                "issuer" : c.get("authority",""),
                "date"   : _date(c.get("timePeriod",{}).get("startDate")),
                "url"    : c.get("url","")
            }
            for c in raw.get("certifications",[])
        ],

        "awards": [
            {
                "title"    : h.get("title",""),
                "date"     : _date(h.get("issueDate")),
                "awarder"  : h.get("issuer",""),
                "summary"  : h.get("description",""),
                "url"      : h.get("url","")
            }
            for h in raw.get("honors",[])
        ],

        "projects": [
            {
                "name"       : p.get("title",""),
                "description": p.get("description",""),
                "startDate"  : _date(p.get("timePeriod",{}).get("startDate")),
                "endDate"    : _date(p.get("timePeriod",{}).get("endDate")),
                "url"        : p.get("url","")
            }
            for p in raw.get("projects",[])
        ],

        "skills":  [ { "name": s["name"] } for s in raw.get("skills",[]) ],

        "languages": [
            {
                "language": l.get("name",""),
                "fluency" : l.get("proficiency","")
            }
            for l in raw.get("languages",[])
        ]
    }

    return j
# ────────────────────────────────────────────────────────────────────────────
def main():
    if not RAW_FILE.exists():
        sys.exit("✖  Run the LinkedIn scraper first – data/linkedin_raw.json missing.")

    raw_data   = json.loads(RAW_FILE.read_text(encoding="utf-8"))
    new_resume = transform(raw_data)

    old_resume = {}
    if CV_FILE.exists():
        file_content = CV_FILE.read_text(encoding="utf-8").strip()
        if file_content:  # Only try to parse if file has content
            old_resume = json.loads(file_content)

    if new_resume == old_resume:
        print("ℹ  No changes – résumé already up-to-date.")
        sys.exit(1)                        # signals "skip commit" to the Action

    CV_FILE.write_text(json.dumps(new_resume, indent=2, ensure_ascii=False), encoding="utf-8")
    print("✅  resume.json refreshed.")

if __name__ == "__main__":
    main()
