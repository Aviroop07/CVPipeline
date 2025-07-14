import json
from typing import Dict, List, Optional, Union

def extract_job_details(job_data: Dict) -> Dict:
    """
    Extract specific details from a LinkedIn job posting response.
    
    Args:
        job_data: The JSON response from LinkedIn's get_job function
        
    Returns:
        Dictionary containing extracted job details
    """
    extracted_data = {}
    
    # Extract company name
    try:
        company_details = job_data.get("companyDetails", {})
        if "com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany" in company_details:
            company_info = company_details["com.linkedin.voyager.deco.jobs.web.shared.WebCompactJobPostingCompany"]
            if "companyResolutionResult" in company_info:
                extracted_data["company_name"] = company_info["companyResolutionResult"].get("name", "")
    except Exception as e:
        extracted_data["company_name"] = ""
        print(f"Error extracting company name: {e}")
    
    # Extract job title
    extracted_data["title"] = job_data.get("title", "")
    
    # Extract workplace type
    try:
        workplace_types = job_data.get("workplaceTypes", [])
        workplace_resolution = job_data.get("workplaceTypesResolutionResults", {})
        
        workplace_names = []
        for workplace_urn in workplace_types:
            if workplace_urn in workplace_resolution:
                workplace_names.append(workplace_resolution[workplace_urn].get("localizedName", ""))
        
        extracted_data["workplace_type"] = ", ".join(workplace_names) if workplace_names else ""
    except Exception as e:
        extracted_data["workplace_type"] = ""
        print(f"Error extracting workplace type: {e}")
    
    # Extract apply method URL
    try:
        apply_method = job_data.get("applyMethod", {})
        apply_url = ""
        
        # Check for ComplexOnsiteApply
        if "com.linkedin.voyager.jobs.ComplexOnsiteApply" in apply_method:
            apply_url = apply_method["com.linkedin.voyager.jobs.ComplexOnsiteApply"].get("easyApplyUrl", "")
        
        # Check for OffsiteApply
        elif "com.linkedin.voyager.jobs.OffsiteApply" in apply_method:
            apply_url = apply_method["com.linkedin.voyager.jobs.OffsiteApply"].get("companyApplyUrl", "")
        
        extracted_data["apply_url"] = apply_url
    except Exception as e:
        extracted_data["apply_url"] = ""
        print(f"Error extracting apply URL: {e}")
    
    # Extract job description text
    try:
        description = job_data.get("description", {})
        extracted_data["description_text"] = description.get("text", "")
    except Exception as e:
        extracted_data["description_text"] = ""
        print(f"Error extracting description text: {e}")
    
    # Extract formatted location
    extracted_data["formatted_location"] = job_data.get("formattedLocation", "")
    
    return extracted_data

def extract_skills_from_skills_data(skills_data: Dict) -> List[str]:
    """
    Extract skill names from the skills data structure.
    
    Args:
        skills_data: The JSON response containing skills information
        
    Returns:
        List of skill names
    """
    skill_names = []
    
    try:
        skill_matches = skills_data.get("skillMatchStatuses", [])
        
        for skill_match in skill_matches:
            if "skill" in skill_match and "name" in skill_match["skill"]:
                skill_names.append(skill_match["skill"]["name"])
    
    except Exception as e:
        print(f"Error extracting skills: {e}")
    
    return skill_names

def main():
    """Example usage of the extraction functions."""
    
    # Load example job data
    try:
        with open("example_jd.json", "r", encoding="utf-8") as f:
            job_data = json.load(f)
        
        # Extract job details
        job_details = extract_job_details(job_data)
        
        print("=== EXTRACTED JOB DETAILS ===")
        print(f"Company Name: {job_details['company_name']}")
        print(f"Job Title: {job_details['title']}")
        print(f"Workplace Type: {job_details['workplace_type']}")
        print(f"Apply URL: {job_details['apply_url']}")
        print(f"Location: {job_details['formatted_location']}")
        print(f"Description Length: {len(job_details['description_text'])} characters")
        print(f"Description Preview: {job_details['description_text'][:200]}...")
        
    except FileNotFoundError:
        print("example_jd.json not found")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    
    # Load example skills data
    try:
        with open("example_skills.json", "r", encoding="utf-8") as f:
            skills_data = json.load(f)
        
        # Extract skills
        skills = extract_skills_from_skills_data(skills_data)
        
        print("\n=== EXTRACTED SKILLS ===")
        for i, skill in enumerate(skills, 1):
            print(f"{i}. {skill}")
        
    except FileNotFoundError:
        print("example_skills.json not found")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")

if __name__ == "__main__":
    main() 