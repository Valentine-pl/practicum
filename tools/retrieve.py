# tools/retrieve.py
"""
Knowledge Base retrieval tool using API Gateway
"""

import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from config import (
    DEFAULT_K,
    DEFAULT_SEARCH_TYPE,
    DEFAULT_COMPANY_FILTER,
    MIN_K,
    MAX_K
)

# Load environment
load_dotenv()

KB_API_URL = os.getenv("KB_API_URL")
KB_API_KEY = os.getenv("KB_API_KEY")


def get_retrieve_tool_spec() -> Dict[str, Any]:
    """Return tool specification for Bedrock Converse API"""
    return {
        "toolSpec": {
            "name": "retrieve_documents",
            "description": "Retrieve relevant documents from the knowledge base. Use this to find information from uploaded documents.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query - what to find in the documents"
                        },
                        "k": {
                            "type": "integer",
                            "description": f"Number of results to return ({MIN_K}-{MAX_K}, default: {DEFAULT_K})"
                        },
                        "search_type": {
                            "type": "string",
                            "enum": ["HYBRID", "SEMANTIC", "KEYWORD"],
                            "description": f"Search type (default: {DEFAULT_SEARCH_TYPE})"
                        },
                        "company_name": {
                            "type": "string",
                            "description": "Filter by specific company name (optional)"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    }


def retrieve_documents(
    query: str,
    k: int = DEFAULT_K,
    search_type: str = DEFAULT_SEARCH_TYPE,
    company_name: Optional[str] = DEFAULT_COMPANY_FILTER
) -> Dict[str, Any]:
    """
    Retrieve documents from knowledge base
    
    Args:
        query: Search query
        k: Number of results
        search_type: HYBRID, SEMANTIC, or KEYWORD
        company_name: Optional company filter
        
    Returns:
        Dict with status and results
    """
    if not KB_API_URL or not KB_API_KEY:
        return {
            "status": "error",
            "error": "Knowledge Base API not configured. Check .env file."
        }
    
    # Validate and normalize inputs
    k = max(MIN_K, min(k, MAX_K))
    search_type = search_type.upper()
    if search_type not in ["HYBRID", "SEMANTIC", "KEYWORD"]:
        search_type = DEFAULT_SEARCH_TYPE
    
    # Build request
    payload = {
        "query": query,
        "k": k,
        "search_type": search_type
    }
    
    if company_name:
        payload["company_name"] = company_name
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": KB_API_KEY
    }
    
    try:
        response = requests.post(
            KB_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Format results
        results = []
        for idx, result in enumerate(data.get("results", []), 1):
            results.append({
                "rank": idx,
                "text": result.get("text", ""),
                "score": result.get("score"),
                "metadata": result.get("metadata", {})
            })
        
        return {
            "status": "success",
            "query": query,
            "search_type": search_type,
            "k": k,
            "company_filter": company_name,
            "results_count": len(results),
            "results": results
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "Request timeout"
        }
    except requests.exceptions.HTTPError as e:
        return {
            "status": "error",
            "error": f"API error: {e.response.status_code}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }