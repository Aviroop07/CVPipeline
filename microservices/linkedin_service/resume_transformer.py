import logging
from typing import Dict, Any, List, Tuple
from config import MONTHS

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

class ResumeTransformer:
    """Transform LinkedIn profile data to JSON-Resume format"""
    
    def __init__(self):
        """Initialize the resume transformer"""
        pass
    
    def _date(self, ldict: Dict[str, Any]) -> str:
        """
        Convert LinkedIn date dict to YYYY-MM format.
        
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
    
    def transform_linkedin_to_resume(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform LinkedIn profile data to JSON-Resume format.
        
        Args:
            raw_data (dict): Raw LinkedIn profile data
            
        Returns:
            dict: JSON-Resume formatted data
        """
        try:
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
                        "date": self._date(h.get("issueDate")),
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
                        "startDate": self._date(p.get("timePeriod",{}).get("startDate")),
                        "endDate": self._date(p.get("timePeriod",{}).get("endDate")),
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
            
            # Process work experiences
            for w in raw_data.get("experience", []):
                work_entry = {
                    "name": w.get("companyName", ""),
                    "position": w.get("title", ""),
                    "location": w.get("locationName", ""),
                    "startDate": self._date(w.get("timePeriod", {}).get("startDate")),
                    "endDate": self._date(w.get("timePeriod", {}).get("endDate")),
                    "summary": w.get("description", ""),
                    "url": "",  # Will be filled by URL validation service
                    "public_id": ""
                }
                resume_data["work"].append(work_entry)
            
            # Process education entries
            for e in raw_data.get("education", []):
                education_entry = {
                    "institution": e.get("schoolName", ""),
                    "area": e.get("fieldOfStudy", ""),
                    "studyType": e.get("degreeName", ""),
                    "score": e.get("grade", ""),
                    "startDate": self._date(e.get("timePeriod", {}).get("startDate")),
                    "endDate": self._date(e.get("timePeriod", {}).get("endDate")),
                    "url": "",  # Will be filled by URL validation service
                    "public_id": ""
                }
                resume_data["education"].append(education_entry)
            
            log.info("✅ LinkedIn data transformed to JSON-Resume format")
            return resume_data
            
        except Exception as e:
            log.error(f"❌ Error transforming LinkedIn data: {e}")
            raise
    
    def format_date_range(self, start: str, end: str) -> str:
        """
        Format date range from YYYY-MM strings.
        
        Args:
            start (str): Start date in YYYY-MM format
            end (str): End date in YYYY-MM format (None means present)
            
        Returns:
            str: Formatted date range (e.g., "Jan, 2020 – Present")
        """
        if not start:
            return ""
        try:
            ys, ms = start.split("-")
            ms = int(ms)
            ys_int = int(ys)
            sm = MONTHS[ms-1]
        except Exception:
            return start

        if end:
            try:
                ye, me = end.split("-")
                me = int(me)
                ye_int = int(ye)
                em = MONTHS[me-1]
            except Exception:
                return f"{sm}, {ys} – {end}"

            if ys_int == ye_int:
                return f"{sm} – {em}, {ys}"
            return f"{sm}, {ys} – {em}, {ye}"
        else:
            return f"{sm}, {ys} – Present" 