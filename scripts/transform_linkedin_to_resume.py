#!/usr/bin/env python3
"""
Transform data/linkedin_raw.json → resume.json  (JSON-Resume 1.0 schema)
Exits with code 1 when the résumé did not change – so the GitHub Action
can skip committing an empty diff.
"""
import json, pathlib, sys, datetime as _dt

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
            "summary"  : raw.get("summary","")
        },

        "work": [
            {
                "name"      : w.get("companyName",""),
                "position"  : w.get("title",""),
                "location"  : w.get("locationName",""),
                "startDate" : _date(w.get("timePeriod",{}).get("startDate")),
                "endDate"   : _date(w.get("timePeriod",{}).get("endDate")),
                "summary"   : w.get("description","")
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
                "endDate"    : _date(e.get("timePeriod",{}).get("endDate"))
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
                "summary"  : h.get("description","")
            }
            for h in raw.get("honors",[])
        ],

        "projects": [
            {
                "name"       : p.get("title",""),
                "description": p.get("description",""),
                "startDate"  : _date(p.get("timePeriod",{}).get("startDate")),
                "endDate"    : _date(p.get("timePeriod",{}).get("endDate"))
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
