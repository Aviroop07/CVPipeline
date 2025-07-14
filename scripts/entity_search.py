#!/usr/bin/env python3
"""
Entity search module using Google Knowledge Graph API.

This module provides functions to search for companies and schools using Google's Knowledge Graph
and extract their LinkedIn URLs and public IDs.
"""

import json
import os
import re
import logging
from typing import Tuple, Optional
from requests import Session
import dotenv
import config

# Load environment variables
dotenv.load_dotenv()

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Global session for reuse
_session = None

def normalize_name(name: str) -> str:
    """Normalize a name for comparison by removing common variations.
    
    Args:
        name (str): Name to normalize
        
    Returns:
        str: Normalized name for comparison
    """
    if not name:
        return ""
    
    # Convert to lowercase for comparison
    normalized = name.lower().strip()
    
    # Remove common company/organization suffixes for better matching
    suffixes_to_remove = [
        ' inc', ' inc.', ' corporation', ' corp', ' corp.', ' company', ' co', ' co.',
        ' ltd', ' ltd.', ' limited', ' llc', ' university', ' college', ' institute',
        ' school', ' high school', ' municipal high school'
    ]
    
    for suffix in suffixes_to_remove:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    # Remove extra whitespace and special characters
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized

def names_match(query_name: str, result_name: str, threshold: float = 0.8) -> bool:
    """Check if two names match with some tolerance for variations.
    
    Args:
        query_name (str): Original query name
        result_name (str): Name from API result
        threshold (float): Similarity threshold (0.0 to 1.0)
        
    Returns:
        bool: True if names match sufficiently
    """
    if not query_name or not result_name:
        return False
    
    normalized_query = normalize_name(query_name)
    normalized_result = normalize_name(result_name)
    
    # Exact match after normalization
    if normalized_query == normalized_result:
        return True
    
    # Check if one contains the other (for cases like "PwC" vs "PwC India")
    if normalized_query in normalized_result or normalized_result in normalized_query:
        return True
    
    # Calculate simple word overlap ratio
    query_words = set(normalized_query.split())
    result_words = set(normalized_result.split())
    
    if not query_words or not result_words:
        return False
    
    overlap = len(query_words.intersection(result_words))
    total_unique = len(query_words.union(result_words))
    
    similarity = overlap / total_unique if total_unique > 0 else 0
    
    log.debug(f"Name similarity: '{query_name}' vs '{result_name}' = {similarity:.2f}")
    return similarity >= threshold

def get_session() -> Session:
    """Get or create a requests session for API calls.
    
    Returns:
        Session: Configured requests session
    """
    global _session
    if _session is None:
        _session = Session()
    return _session

def prepare_kg_search_url(query: str, entity_type: str = "", limit: int = 5, languages: str = "en") -> str:
    """Prepare Google Knowledge Graph search URL.
    
    Args:
        query (str): Search query (company or school name)
        entity_type (str, optional): Specific entity type to search for
        limit (int): Maximum number of results to return
        languages (str): Language preference for results
        
    Returns:
        str: Complete Knowledge Graph API URL
    """
    api_key = os.getenv("GOOGLE_KG_API")
    if not api_key:
        log.warning("GOOGLE_KG_API not set - entity search will fail")
        return ""
    
    # Clean and encode the query
    clean_query = query.strip().replace(' ', '+')
    
    url = f"{config.KG_URL}?key={api_key}&query={clean_query}&limit={limit}&indent=true&languages={languages}"
    
    if entity_type:
        url += f"&types={entity_type}"
    
    return url

def extract_entity_info(kg_result: dict) -> Tuple[str, str]:
    """Extract official website URL and entity ID from Knowledge Graph result.
    
    Args:
        kg_result (dict): Single result from Knowledge Graph API
        
    Returns:
        Tuple[str, str]: (Official website URL, entity_id) or ("", "") if not found
    """
    # Extract the official website URL from the main 'url' field
    official_url = kg_result.get("url", "")
    
    # Extract entity ID from the '@id' field (e.g., "kg:/m/046vm" -> "m/046vm")
    entity_id = kg_result.get("@id", "")
    if entity_id.startswith("kg:/"):
        entity_id = entity_id[4:]  # Remove "kg:/" prefix
    
    # Clean up the URL - ensure it has proper protocol
    if official_url and not official_url.startswith(("http://", "https://")):
        official_url = "https://" + official_url
    
    log.debug(f"Found official URL: {official_url}, Entity ID: {entity_id}")
    return official_url, entity_id

def search_entity_kg(query: str, entity_type: str = "") -> Tuple[str, str]:
    """Search for an entity using Google Knowledge Graph API.
    
    Args:
        query (str): Entity name to search for
        entity_type (str, optional): Type of entity (Corporation, EducationalOrganization, etc.)
        
    Returns:
        Tuple[str, str]: (Official website URL, entity_id) or ("", "") if not found
    """
    if not query.strip():
        return "", ""
    
    log.info(f"🔍 Searching Knowledge Graph for: {query}")
    
    try:
        search_url = prepare_kg_search_url(query, entity_type)
        if not search_url:
            log.warning("Cannot prepare KG search URL - API key missing")
            return "", ""
        
        session = get_session()
        response = session.get(search_url, timeout=10)
        response.raise_for_status()
        
        kg_data = response.json()
        log.debug(f"KG API response: {json.dumps(kg_data, indent=2)}")
        
        # Check if we have results
        items = kg_data.get("itemListElement", [])
        if not items:
            log.info(f"No Knowledge Graph results found for: {query}")
            return "", ""
        
        # Try each result to find entity information and validate name match
        for item in items:
            result = item.get("result", {})
            result_name = result.get("name", "")
            official_url, entity_id = extract_entity_info(result)
            
            if official_url and result_name:
                # Validate that the result name matches our query
                if names_match(query, result_name):
                    log.info(f"✅ Found matching official URL for {query}: {official_url} (result: {result_name})")
                    return official_url, entity_id
                else:
                    log.debug(f"⚠️ Name mismatch for {query}: got '{result_name}', skipping")
        
        log.info(f"❌ No matching official URL found in Knowledge Graph results for: {query}")
        return "", ""
        
    except Exception as e:
        log.warning(f"Knowledge Graph search failed for {query}: {e}")
        return "", ""

def search_company_kg(name: str) -> Tuple[str, str]:
    """Search for a company using Google Knowledge Graph API.
    
    Args:
        name (str): Company name
        
    Returns:
        Tuple[str, str]: (Official company website URL, entity_id) or ("", "") if not found
    """
    log.info(f"🏢 Searching for company: {name}")
    
    # Try with Corporation type first
    url, entity_id = search_entity_kg(name, "Corporation")
    if url:
        return url, entity_id
    
    # Fallback to general search
    url, entity_id = search_entity_kg(name)
    if url:
        return url, entity_id
    
    # Try with additional common company terms
    for suffix in [" Inc", " Corporation", " Ltd", " Limited", " Company"]:
        if not name.endswith(suffix):
            extended_name = name + suffix
            url, entity_id = search_entity_kg(extended_name, "Corporation")
            if url:
                return url, entity_id
    
    log.info(f"❌ No company official URL found for: {name}")
    return "", ""

def search_school_kg(name: str) -> Tuple[str, str]:
    """Search for a school/university using Google Knowledge Graph API.
    
    Args:
        name (str): School/university name
        
    Returns:
        Tuple[str, str]: (Official school website URL, entity_id) or ("", "") if not found
    """
    log.info(f"🎓 Searching for school: {name}")
    
    # Try with EducationalOrganization type first
    url, entity_id = search_entity_kg(name, "EducationalOrganization")
    if url:
        return url, entity_id
    
    # Try with University type
    url, entity_id = search_entity_kg(name, "University")
    if url:
        return url, entity_id
    
    # Fallback to general search
    url, entity_id = search_entity_kg(name)
    if url:
        return url, entity_id
    
    # Try with additional common school terms
    for suffix in [" University", " College", " Institute", " School"]:
        if not name.endswith(suffix):
            extended_name = name + suffix
            url, entity_id = search_entity_kg(extended_name, "EducationalOrganization")
            if url:
                return url, entity_id
    
    log.info(f"❌ No school official URL found for: {name}")
    return "", ""

# Legacy functions for backward compatibility with linkedin_transformer.py
def company_url_and_id(name: str, company_urn: str = None) -> Tuple[str, str]:
    """Get official company website URL and entity ID from company name (legacy wrapper).
    
    Args:
        name (str): Company name
        company_urn (str, optional): Company URN (unused, for compatibility)
        
    Returns:
        Tuple[str, str]: (Official company website URL, entity_id) or ("", "") if not found
    """
    return search_company_kg(name)

def school_url_and_id(name: str, school_urn: str = None) -> Tuple[str, str]:
    """Get official school website URL and entity ID from school name (legacy wrapper).
    
    Args:
        name (str): School name
        school_urn (str, optional): School URN (unused, for compatibility)
        
    Returns:
        Tuple[str, str]: (Official school website URL, entity_id) or ("", "") if not found
    """
    return search_school_kg(name)

def company_url(name: str, company_urn: str = None) -> str:
    """Get official company website URL from company name (legacy wrapper).
    
    Args:
        name (str): Company name
        company_urn (str, optional): Company URN (unused, for compatibility)
        
    Returns:
        str: Official company website URL or empty string if not found
    """
    url, _ = search_company_kg(name)
    return url

def school_url(name: str, school_urn: str = None) -> str:
    """Get official school website URL from school name (legacy wrapper).
    
    Args:
        name (str): School name
        school_urn (str, optional): School URN (unused, for compatibility)
        
    Returns:
        str: Official school website URL or empty string if not found
    """
    url, _ = search_school_kg(name)
    return url

if __name__ == "__main__":
    # Test the functionality
    test_companies = ["PwC India", "Neurologic-ai", "Google", "Microsoft"]
    test_schools = ["Jadavpur University", "Stanford University", "MIT"]
    
    log.info("Testing company searches:")
    for company in test_companies:
        url, public_id = search_company_kg(company)
        log.info(f"  {company}: {url} (ID: {public_id})")
    
    log.info("\nTesting school searches:")
    for school in test_schools:
        url, public_id = search_school_kg(school)
        log.info(f"  {school}: {url} (ID: {public_id})") 