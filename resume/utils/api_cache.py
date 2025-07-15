#!/usr/bin/env python3
"""
API response caching module using SQLite.

This module provides functions to cache API responses to avoid redundant calls
when running the workflow multiple times.
"""

import sqlite3
import json
import hashlib
import logging
import pathlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from resume.utils import config
import os

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

class APICache:
    """Simple SQLite-based cache for API responses."""
    
    def __init__(self, db_path: pathlib.Path = None, cache_ttl_hours: int = None):
        """Initialize the API cache.
        
        Args:
            db_path (pathlib.Path, optional): Path to SQLite database file
            cache_ttl_hours (int, optional): Cache TTL in hours (defaults to config value)
        """
        self.db_path = db_path or (config.PROJECT_ROOT / config.DATA_DIR / config.API_CACHE_DB_FILE)
        # Convert seconds to hours for timedelta (which expects hours)
        cache_ttl_seconds = cache_ttl_hours or config.CACHE_TTL_SECONDS
        self.cache_ttl_hours = cache_ttl_seconds // 3600  # Convert seconds to hours
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Create cache table with additional searchable fields
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS api_cache (
                        cache_key TEXT PRIMARY KEY,
                        api_type TEXT NOT NULL,
                        request_data TEXT,
                        response_data TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        request_summary TEXT,
                        response_size INTEGER DEFAULT 0
                    )
                """)
                
                # Create indexes for faster lookups and searching
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_api_cache_expires 
                    ON api_cache(expires_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_api_cache_type 
                    ON api_cache(api_type)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_api_cache_created 
                    ON api_cache(created_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_api_cache_request_summary 
                    ON api_cache(request_summary)
                """)
                
                conn.commit()
                log.debug(f"✅ API cache database initialized at {self.db_path}")
                
        except Exception as e:
            log.error(f"❌ Failed to initialize API cache database: {e}")
            raise
    
    def _generate_cache_key(self, api_type: str, request_data: Dict[str, Any]) -> str:
        """Generate a unique cache key for the API request.
        
        Args:
            api_type (str): Type of API call (e.g., 'job_search', 'job_details', 'job_skills')
            request_data (Dict): Request parameters
            
        Returns:
            str: Unique cache key
        """
        # Create a deterministic string representation of the request
        request_str = json.dumps(request_data, sort_keys=True, ensure_ascii=False)
        
        # Generate hash of the request
        request_hash = hashlib.md5(request_str.encode('utf-8')).hexdigest()
        
        return f"{api_type}:{request_hash}"
    
    def _generate_request_summary(self, api_type: str, request_data: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the request for searching.
        
        Args:
            api_type (str): Type of API call
            request_data (Dict): Request parameters
            
        Returns:
            str: Human-readable request summary
        """
        summary_parts = [api_type]
        
        # Add key request parameters based on API type
        if api_type == "job_search":
            keywords = request_data.get("keywords", "")
            location = request_data.get("location_name", "")
            limit = request_data.get("limit", "")
            summary_parts.extend([f"keywords:{keywords}", f"location:{location}", f"limit:{limit}"])
        
        elif api_type == "job_details":
            job_id = request_data.get("job_id", "")
            summary_parts.append(f"job_id:{job_id}")
        
        elif api_type == "job_skills":
            job_id = request_data.get("job_id", "")
            summary_parts.append(f"job_id:{job_id}")
        
        elif api_type == "linkedin_profile":
            public_id = request_data.get("public_id", "")
            summary_parts.append(f"public_id:{public_id}")
        
        elif api_type == "linkedin_contact_info":
            public_id = request_data.get("public_id", "")
            summary_parts.append(f"public_id:{public_id}")
        
        elif api_type == "linkedin_skills":
            public_id = request_data.get("public_id", "")
            summary_parts.append(f"public_id:{public_id}")
        
        elif api_type == "linkedin_experiences":
            urn_id = request_data.get("urn_id", "")
            summary_parts.append(f"urn_id:{urn_id}")
        
        elif api_type == "linkedin_get_company":
            company_name = request_data.get("company_name", "")
            company_id = request_data.get("company_id", "")
            if company_name:
                summary_parts.append(f"company:{company_name}")
            elif company_id:
                summary_parts.append(f"company_id:{company_id}")
        
        elif api_type == "linkedin_search_companies":
            keywords = request_data.get("keywords", [])
            limit = request_data.get("limit", "")
            summary_parts.extend([f"keywords:{','.join(keywords)}", f"limit:{limit}"])
        
        elif api_type == "linkedin_get_school":
            school_name = request_data.get("school_name", "")
            school_id = request_data.get("school_id", "")
            if school_name:
                summary_parts.append(f"school:{school_name}")
            elif school_id:
                summary_parts.append(f"school_id:{school_id}")
        
        elif api_type == "linkedin_get_profile":
            urn_id = request_data.get("urn_id", "")
            summary_parts.append(f"urn_id:{urn_id}")
        
        elif api_type == "google_kg_search":
            query = request_data.get("query", "")
            entity_type = request_data.get("entity_type", "")
            summary_parts.extend([f"query:{query}", f"type:{entity_type}"])
        
        else:
            # For unknown API types, include all request data keys
            for key, value in request_data.items():
                if isinstance(value, (str, int, float)):
                    summary_parts.append(f"{key}:{value}")
                elif isinstance(value, list):
                    summary_parts.append(f"{key}:{','.join(map(str, value))}")
        
        return " | ".join(summary_parts)
    
    def get(self, api_type: str, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached response for an API request.
        
        Args:
            api_type (str): Type of API call
            request_data (Dict): Request parameters
            
        Returns:
            Dict[str, Any] or None: Cached response if found and not expired, None otherwise
        """
        try:
            cache_key = self._generate_cache_key(api_type, request_data)
            
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Get cached response
                cursor.execute("""
                    SELECT response_data, expires_at 
                    FROM api_cache 
                    WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP
                """, (cache_key,))
                
                result = cursor.fetchone()
                
                if result:
                    response_data, expires_at = result
                    log.debug(f"✅ Cache hit for {api_type}: {cache_key}")
                    return json.loads(response_data)
                else:
                    # Check if there's an expired entry
                    cursor.execute("""
                        SELECT expires_at FROM api_cache 
                        WHERE cache_key = ?
                    """, (cache_key,))
                    expired_result = cursor.fetchone()
                    
                    if expired_result:
                        expired_at = expired_result[0]
                        log.debug(f"🕐 Cache expired for {api_type}: {cache_key} (expired at {expired_at})")
                    else:
                        log.debug(f"❌ Cache miss for {api_type}: {cache_key}")
                    return None
                    
        except Exception as e:
            log.warning(f"⚠️ Error reading from cache: {e}")
            return None
    
    def set(self, api_type: str, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> bool:
        """Cache an API response.
        
        Args:
            api_type (str): Type of API call
            request_data (Dict): Request parameters
            response_data (Dict): Response data to cache
            
        Returns:
            bool: True if successfully cached, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(api_type, request_data)
            expires_at = datetime.now() + timedelta(hours=self.cache_ttl_hours)
            request_summary = self._generate_request_summary(api_type, request_data)
            response_size = len(json.dumps(response_data, ensure_ascii=False))
            
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Insert or replace cached response with additional metadata
                cursor.execute("""
                    INSERT OR REPLACE INTO api_cache 
                    (cache_key, api_type, request_data, response_data, expires_at, request_summary, response_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_key,
                    api_type,
                    json.dumps(request_data, ensure_ascii=False),
                    json.dumps(response_data, ensure_ascii=False),
                    expires_at.isoformat(),
                    request_summary,
                    response_size
                ))
                
                conn.commit()
                log.debug(f"✅ Cached response for {api_type}: {cache_key} (summary: {request_summary})")
                return True
                
        except Exception as e:
            log.warning(f"⚠️ Error writing to cache: {e}")
            return False
    
    def clear_expired(self) -> int:
        """Clear expired cache entries.
        
        Returns:
            int: Number of expired entries removed
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Count expired entries
                cursor.execute("""
                    SELECT COUNT(*) FROM api_cache 
                    WHERE expires_at <= CURRENT_TIMESTAMP
                """)
                expired_count = cursor.fetchone()[0]
                
                # Delete expired entries
                cursor.execute("""
                    DELETE FROM api_cache 
                    WHERE expires_at <= CURRENT_TIMESTAMP
                """)
                
                conn.commit()
                
                if expired_count > 0:
                    log.info(f"🧹 Cleared {expired_count} expired cache entries")
                
                return expired_count
                
        except Exception as e:
            log.warning(f"⚠️ Error clearing expired cache: {e}")
            return 0
    
    def clear_all(self) -> int:
        """Clear all cache entries.
        
        Returns:
            int: Number of entries removed
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Count all entries
                cursor.execute("SELECT COUNT(*) FROM api_cache")
                total_count = cursor.fetchone()[0]
                
                # Delete all entries
                cursor.execute("DELETE FROM api_cache")
                conn.commit()
                
                log.info(f"🧹 Cleared all {total_count} cache entries")
                return total_count
                
        except Exception as e:
            log.warning(f"⚠️ Error clearing all cache: {e}")
            return 0
    
    def search_cache(self, search_term: str = None, api_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Search cache entries by various criteria.
        
        Args:
            search_term (str, optional): Search term to match in request summary
            api_type (str, optional): Filter by specific API type
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of matching cache entries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Build query based on search criteria
                query = """
                    SELECT cache_key, api_type, request_summary, response_size, 
                           created_at, expires_at, 
                           CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 'valid' ELSE 'expired' END as status
                    FROM api_cache
                    WHERE 1=1
                """
                params = []
                
                if search_term:
                    query += " AND request_summary LIKE ?"
                    params.append(f"%{search_term}%")
                
                if api_type:
                    query += " AND api_type = ?"
                    params.append(api_type)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                entries = []
                for row in results:
                    entries.append({
                        "cache_key": row[0],
                        "api_type": row[1],
                        "request_summary": row[2],
                        "response_size": row[3],
                        "created_at": row[4],
                        "expires_at": row[5],
                        "status": row[6]
                    })
                
                return entries
                
        except Exception as e:
            log.warning(f"⚠️ Error searching cache: {e}")
            return []
    
    def list_cache_entries(self, api_type: str = None, status: str = "valid", limit: int = 20) -> List[Dict[str, Any]]:
        """List cache entries with optional filtering.
        
        Args:
            api_type (str, optional): Filter by API type
            status (str): Filter by status ('valid', 'expired', or 'all')
            limit (int): Maximum number of results to return
            
        Returns:
            List[Dict]: List of cache entries
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Build query
                query = """
                    SELECT cache_key, api_type, request_summary, response_size, 
                           created_at, expires_at,
                           CASE WHEN expires_at > CURRENT_TIMESTAMP THEN 'valid' ELSE 'expired' END as status
                    FROM api_cache
                    WHERE 1=1
                """
                params = []
                
                if api_type:
                    query += " AND api_type = ?"
                    params.append(api_type)
                
                if status == "valid":
                    query += " AND expires_at > CURRENT_TIMESTAMP"
                elif status == "expired":
                    query += " AND expires_at <= CURRENT_TIMESTAMP"
                # 'all' doesn't add any filter
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                entries = []
                for row in results:
                    entries.append({
                        "cache_key": row[0],
                        "api_type": row[1],
                        "request_summary": row[2],
                        "response_size": row[3],
                        "created_at": row[4],
                        "expires_at": row[5],
                        "status": row[6]
                    })
                
                return entries
                
        except Exception as e:
            log.warning(f"⚠️ Error listing cache entries: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        try:
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                cursor = conn.cursor()
                
                # Total entries
                cursor.execute("SELECT COUNT(*) FROM api_cache")
                total_entries = cursor.fetchone()[0]
                
                # Expired entries
                cursor.execute("""
                    SELECT COUNT(*) FROM api_cache 
                    WHERE expires_at <= CURRENT_TIMESTAMP
                """)
                expired_entries = cursor.fetchone()[0]
                
                # Valid entries
                valid_entries = total_entries - expired_entries
                
                # Entries by API type
                cursor.execute("""
                    SELECT api_type, COUNT(*) 
                    FROM api_cache 
                    GROUP BY api_type
                """)
                entries_by_type = dict(cursor.fetchall())
                
                # Database size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "total_entries": total_entries,
                    "valid_entries": valid_entries,
                    "expired_entries": expired_entries,
                    "entries_by_type": entries_by_type,
                    "db_size_bytes": db_size,
                    "db_size_mb": round(db_size / (1024 * 1024), 2),
                    "cache_ttl_hours": self.cache_ttl_hours
                }
                
        except Exception as e:
            log.warning(f"⚠️ Error getting cache stats: {e}")
            return {}
                
        except Exception as e:
            log.warning(f"⚠️ Error getting cache stats: {e}")
            return {}

# Global cache instance
_cache_instance = None

def get_cache() -> APICache:
    """Get the global cache instance.
    
    Returns:
        APICache: Global cache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = APICache()
    return _cache_instance

def get_cache_path():
    """Return the absolute path to the cache database file."""
    return config.PROJECT_ROOT / config.DATA_DIR / pathlib.Path(config.API_CACHE_DB_FILE)

def clear_cache(expired_only: bool = True) -> int:
    """Clear cache entries.
    
    Args:
        expired_only (bool): If True, only clear expired entries. If False, clear all.
        
    Returns:
        int: Number of entries removed
    """
    cache = get_cache()
    if expired_only:
        return cache.clear_expired()
    else:
        return cache.clear_all()

def cached_api_call(api_type: str, request_data: Dict[str, Any], api_function, *args, **kwargs):
    """Execute an API call with caching.
    
    Args:
        api_type (str): Type of API call for caching
        request_data (Dict): Request parameters for cache key generation
        api_function: Function to call if not cached
        *args: Arguments to pass to api_function
        **kwargs: Keyword arguments to pass to api_function
        
    Returns:
        Any: API response (from cache or fresh call)
    """
    cache = get_cache()
    
    # Try to get from cache first
    cached_response = cache.get(api_type, request_data)
    if cached_response is not None:
        log.info(f"🚀 Using cached response for {api_type}")
        return cached_response
    
    # If not in cache, make the API call
    log.info(f"🚀 Making fresh API call for {api_type}")
    response = api_function(*args, **kwargs)
    
    # Cache the response
    if response is not None:
        cache.set(api_type, request_data, response)
    
    return response

async def cached_api_call_async(api_type, request_data, coro, *args, **kwargs):
    cache = get_cache()
    hit = cache.get(api_type, request_data)
    if hit is not None:
        return hit
    result = await coro(*args, **kwargs)
    cache.set(api_type, request_data, result)
    return result

def clean_dirty_cache() -> int:
    """Clean dirty (expired) cache entries.
    
    Returns:
        int: Number of dirty entries removed
    """
    cache = get_cache()
    return cache.clear_expired()

def get_cache_freshness() -> Dict[str, Any]:
    """Get cache freshness information.
    
    Returns:
        Dict[str, Any]: Cache freshness statistics
    """
    stats = get_cache_stats()
    if not stats:
        return {"error": "Could not retrieve cache statistics"}
    
    total = stats.get('total_entries', 0)
    valid = stats.get('valid_entries', 0)
    expired = stats.get('expired_entries', 0)
    
    if total == 0:
        return {
            "total_entries": 0,
            "valid_entries": 0,
            "expired_entries": 0,
            "freshness_percentage": 100.0,
            "status": "empty"
        }
    
    freshness_percentage = (valid / total) * 100
    
    if expired == 0:
        status = "fresh"
    elif expired < total * 0.5:
        status = "mostly_fresh"
    else:
        status = "dirty"
    
    return {
        "total_entries": total,
        "valid_entries": valid,
        "expired_entries": expired,
        "freshness_percentage": round(freshness_percentage, 1),
        "status": status,
        "cache_ttl_hours": stats.get('cache_ttl_hours', 24)
    }

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics.
    
    Returns:
        Dict[str, Any]: Cache statistics
    """
    cache = get_cache()
    return cache.get_stats()

def search_cache_entries(search_term: str = None, api_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Search cache entries by various criteria.
    
    Args:
        search_term (str, optional): Search term to match in request summary
        api_type (str, optional): Filter by specific API type
        limit (int): Maximum number of results to return
        
    Returns:
        List[Dict]: List of matching cache entries
    """
    cache = get_cache()
    return cache.search_cache(search_term, api_type, limit)

def list_cache_entries(api_type: str = None, status: str = "valid", limit: int = 20) -> List[Dict[str, Any]]:
    """List cache entries with optional filtering.
    
    Args:
        api_type (str, optional): Filter by API type
        status (str): Filter by status ('valid', 'expired', or 'all')
        limit (int): Maximum number of results to return
        
    Returns:
        List[Dict]: List of cache entries
    """
    cache = get_cache()
    return cache.list_cache_entries(api_type, status, limit)

def print_cache_stats():
    """Print cache statistics to console."""
    stats = get_cache_stats()
    if stats:
        log.info("📊 API Cache Statistics:")
        log.info(f"  Total entries: {stats.get('total_entries', 0)}")
        log.info(f"  Valid entries: {stats.get('valid_entries', 0)}")
        log.info(f"  Expired entries: {stats.get('expired_entries', 0)}")
        log.info(f"  Database size: {stats.get('db_size_mb', 0)} MB")
        log.info(f"  Cache TTL: {stats.get('cache_ttl_hours', 0)} hours (1 day)")
        
        # Add cache freshness information
        if stats.get('total_entries', 0) > 0:
            valid_percentage = (stats.get('valid_entries', 0) / stats.get('total_entries', 1)) * 100
            log.info(f"  Cache freshness: {valid_percentage:.1f}% valid")
            
            if stats.get('expired_entries', 0) > 0:
                log.info(f"  ⚠️ {stats.get('expired_entries', 0)} entries are dirty (expired)")
        
        entries_by_type = stats.get('entries_by_type', {})
        if entries_by_type:
            log.info("  Entries by API type:")
            for api_type, count in entries_by_type.items():
                log.info(f"    {api_type}: {count}")
    else:
        log.warning("⚠️ Could not retrieve cache statistics")

if __name__ == "__main__":
    # Test the cache functionality
    print_cache_stats()
    
    # Clear expired entries
    cleared = clear_cache()
    if cleared > 0:
        log.info(f"Cleared {cleared} expired entries")
    
    print_cache_stats() 
