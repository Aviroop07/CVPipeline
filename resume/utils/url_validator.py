#!/usr/bin/env python3
"""
URL validation module for resume generation.

This module provides functions to validate that URLs are actually accessible
before including them in resume data.
"""

import asyncio
import socket
import logging
from urllib.parse import urlparse
from typing import Dict, List, Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# HTTP status codes considered successful
OK = range(200, 400)  # treat 2xx / 3xx as success

def url_works(url: str, *, timeout: float = 5.0) -> bool:
    """
    Return True iff:
      1. the host resolves + TCP/TLS handshake succeeds, and
      2. the server replies with 2xx or 3xx inside `timeout`.
    
    Args:
        url (str): URL to check
        timeout (float): Timeout in seconds for the check
        
    Returns:
        bool: True if URL is accessible, False otherwise
    """
    if not HTTPX_AVAILABLE:
        log.warning("[URL] httpx not available - skipping URL validation")
        return True  # Assume URL works if we can't check
    
    if not url or not url.strip():
        return False
    
    # Add https:// if no scheme is present
    test_url = url if "://" in url else "https://" + url
    parsed = urlparse(test_url)
    
    if not parsed.hostname:
        return False
    
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    try:
        # 1. DNS and TCP reachability test (cheaper than a full HTTP round-trip)
        log.debug(f"[URL] Testing TCP connection to {host}:{port}")
        socket.create_connection((host, port), timeout=timeout).close()
    except OSError as e:
        log.debug(f"[URL] TCP connection failed for {test_url}: {e}")
        return False

    # 2. HTTP(S) test
    try:
        with httpx.Client(
            follow_redirects=True, 
            timeout=timeout, 
            headers={"User-Agent": "resume-generator/1.0"}
        ) as cli:
            # Try HEAD first (fastest probe)
            log.debug(f"[URL] Testing HEAD request to {test_url}")
            r = cli.head(test_url)
            if r.status_code in OK:
                log.debug(f"[URL] URL {test_url} works (HEAD {r.status_code})")
                return True
            if r.status_code == 405:  # HEAD not allowed
                log.debug(f"[URL] HEAD not allowed for {test_url}, trying GET")
                r = cli.get(test_url, stream=True)
                success = r.status_code in OK
                log.debug(f"[URL] URL {test_url} {'works' if success else 'failed'} (GET {r.status_code})")
                return success
            else:
                log.debug(f"[URL] URL {test_url} failed with status {r.status_code}")
                return False
    except httpx.RequestError as e:
        log.debug(f"[URL] HTTP request failed for {test_url}: {e}")
        return False

async def probe_async(url: str, *, timeout: float = 5.0, client: Optional[httpx.AsyncClient] = None) -> bool:
    """
    Asynchronous URL validation.
    
    Args:
        url (str): URL to check
        timeout (float): Timeout in seconds for the check
        client (httpx.AsyncClient, optional): Shared HTTP client for efficiency
        
    Returns:
        bool: True if URL is accessible, False otherwise
    """
    if not HTTPX_AVAILABLE:
        return True  # Assume URL works if we can't check
    
    if not url or not url.strip():
        return False
    
    # Add https:// if no scheme is present
    test_url = url if "://" in url else "https://" + url
    parsed = urlparse(test_url)
    
    if not parsed.hostname:
        return False
    
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    # DNS + TCP reachability test
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, socket.create_connection, (host, port), timeout)
    except OSError:
        return False

    # HTTP(S) test
    c = client or httpx.AsyncClient(
        follow_redirects=True, 
        timeout=timeout,
        headers={"User-Agent": "resume-generator/1.0"}
    )
    try:
        r = await c.head(test_url)
        if r.status_code in OK:
            return True
        if r.status_code == 405:
            r = await c.get(test_url, stream=True)
            return r.status_code in OK
        return False
    except httpx.RequestError:
        return False
    finally:
        if client is None:
            await c.aclose()

async def bulk_check_async(urls: List[str], concurrency: int = 10) -> Dict[str, bool]:
    """
    Check multiple URLs asynchronously.
    
    Args:
        urls (List[str]): List of URLs to check
        concurrency (int): Maximum concurrent connections
        
    Returns:
        Dict[str, bool]: Mapping of URL to validation result
    """
    if not HTTPX_AVAILABLE:
        log.warning("[URL] httpx not available - assuming all URLs work")
        return {url: True for url in urls}
    
    async with httpx.AsyncClient(
        follow_redirects=True, 
        timeout=5,
        headers={"User-Agent": "resume-generator/1.0"}
    ) as shared:
        sem = asyncio.Semaphore(concurrency)
        
        async def guarded(u):
            async with sem:
                result = await probe_async(u, client=shared)
                log.debug(f"[URL] URL validation: {u} -> {'OK' if result else 'FAIL'}")
                return u, result
        
        results = await asyncio.gather(*(guarded(u) for u in urls))
        return dict(results)

def bulk_check(urls: List[str], concurrency: int = 10) -> Dict[str, bool]:
    """
    Check multiple URLs (synchronous wrapper for async function).
    
    Args:
        urls (List[str]): List of URLs to check
        concurrency (int): Maximum concurrent connections
        
    Returns:
        Dict[str, bool]: Mapping of URL to validation result
    """
    return asyncio.run(bulk_check_async(urls, concurrency))

def validate_url_with_fallback(url: str, fallback_url: str = "", timeout: float = 5.0) -> str:
    """
    Validate a URL and return it if it works, otherwise try fallback.
    
    Args:
        url (str): Primary URL to check
        fallback_url (str): Fallback URL to try if primary fails
        timeout (float): Timeout for validation
        
    Returns:
        str: Working URL or empty string if none work
    """
    if url and url_works(url, timeout=timeout):
        log.info(f"[URL] Primary URL works: {url}")
        return url
    elif url:
        log.warning(f"[URL] Primary URL failed: {url}")
    
    if fallback_url and url_works(fallback_url, timeout=timeout):
        log.info(f"[URL] Fallback URL works: {fallback_url}")
        return fallback_url
    elif fallback_url:
        log.warning(f"[URL] Fallback URL failed: {fallback_url}")
    
    log.warning("[URL] No working URLs found")
    return ""

def validate_resume_urls(resume_data: dict) -> dict:
    """
    Validate all URLs in resume data and remove broken ones.
    
    Args:
        resume_data (dict): Resume data with URLs to validate
        
    Returns:
        dict: Resume data with validated URLs
    """
    if not HTTPX_AVAILABLE:
        log.warning("[URL] httpx not available - skipping URL validation")
        return resume_data
    
    # Collect all URLs from resume data
    urls_to_check = []
    
    # Work experience URLs
    for work in resume_data.get("work", []):
        if work.get("url"):
            urls_to_check.append(work["url"])
    
    # Education URLs
    for edu in resume_data.get("education", []):
        if edu.get("url"):
            urls_to_check.append(edu["url"])
    
    # Project URLs
    for project in resume_data.get("projects", []):
        if project.get("url"):
            urls_to_check.append(project["url"])
    
    # Award URLs
    for award in resume_data.get("awards", []):
        if award.get("url"):
            urls_to_check.append(award["url"])
    
    if not urls_to_check:
        log.info("[URL] No URLs found to validate")
        return resume_data
    
    log.info(f"[URL] Validating {len(urls_to_check)} URLs...")
    
    # Check all URLs
    url_results = bulk_check(urls_to_check)
    
    # Update resume data based on validation results
    for work in resume_data.get("work", []):
        if work.get("url") and not url_results.get(work["url"], True):
            log.warning(f"[URL] Removing broken work URL: {work['url']}")
            work["url"] = ""
    
    for edu in resume_data.get("education", []):
        if edu.get("url") and not url_results.get(edu["url"], True):
            log.warning(f"[URL] Removing broken education URL: {edu['url']}")
            edu["url"] = ""
    
    for project in resume_data.get("projects", []):
        if project.get("url") and not url_results.get(project["url"], True):
            log.warning(f"[URL] Removing broken project URL: {project['url']}")
            project["url"] = ""
    
    for award in resume_data.get("awards", []):
        if award.get("url") and not url_results.get(award["url"], True):
            log.warning(f"[URL] Removing broken award URL: {award['url']}")
            award["url"] = ""
    
    # Report results
    working_count = sum(1 for result in url_results.values() if result)
    total_count = len(url_results)
    log.info(f"[URL] URL validation complete: {working_count}/{total_count} URLs working")
    
    return resume_data

def main():
    """Test the URL validation functions."""
    test_urls = [
        "https://www.python.org",
        "https://www.google.com", 
        "https://does-not-exist-xyz.tld",
        "https://www.github.com",
        "invalid-url"
    ]
    
    log.info("[URL] Testing individual URL validation:")
    for url in test_urls:
        result = url_works(url)
        log.info(f"[URL]   {url}: {'OK' if result else 'FAIL'}")
    
    log.info("[URL] Testing bulk URL validation:")
    results = bulk_check(test_urls)
    for url, result in results.items():
        log.info(f"[URL]   {url}: {'OK' if result else 'FAIL'}")

if __name__ == "__main__":
    main() 
