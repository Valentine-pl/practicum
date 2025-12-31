# retrieve_api.py

"""
Bedrock Knowledge Base Retrieval API Client

Configure your search parameters below and run: python retrieve_api.py
"""

import os
import json
import requests
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# API CONFIGURATION - Get these from AWS Console
# ============================================================================
API_URL = os.getenv("KB_API_URL")  # Your API Gateway URL
API_KEY = os.getenv("KB_API_KEY")  # Your API Key

# ============================================================================
# SEARCH PARAMETERS - Configure your search here
# ============================================================================
QUERY = "דוח מאזן"  # Your search question
K = 10  # Number of results (1-50)
SEARCH_TYPE = "HYBRID"  # Options: "HYBRID" or "SEMANTIC" only
COMPANY_NAMES = ["שופרסל2022"]  # List of companies to search, or None for all

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================
SAVE_RESULTS = True  # Set to False to disable saving
RESULTS_FOLDER = "results"  # Folder to save results


def retrieve_api(
    query: str,
    k: int,
    search_type: str,
    company_name: Optional[str] = None
):
    """
    Call the Knowledge Base API.
    
    Args:
        query: Search question
        k: Number of results
        search_type: Search algorithm type ("HYBRID" or "SEMANTIC")
        company_name: Company filter (optional)
    
    Returns:
        API response dictionary
    """
    if not API_URL or not API_KEY:
        raise RuntimeError(
            "ERROR: Missing API credentials!\n"
            "Set KB_API_URL and KB_API_KEY in .env file"
        )
    
    # Validate search type
    search_type_upper = search_type.upper()
    if search_type_upper not in ["HYBRID", "SEMANTIC"]:
        raise ValueError(
            f"Invalid SEARCH_TYPE: '{search_type}'\n"
            "Only 'HYBRID' and 'SEMANTIC' are supported by AWS Bedrock."
        )
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    
    payload = {
        "query": query,
        "k": k,
        "search_type": search_type_upper
    }
    
    if company_name:
        payload["company_name"] = company_name
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code in [401, 403]:
            raise RuntimeError(f"Authentication failed. Check your API key.")
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    except Exception as e:
        raise RuntimeError(f"Request failed: {str(e)}")


def save_results_to_file(query, search_type, company_names, all_results, elapsed_ms):
    """
    Save search results to a text file in the results folder.
    
    Args:
        query: Search query
        search_type: Search type used
        company_names: List of companies searched
        all_results: List of all results
        elapsed_ms: Total elapsed time
    """
    # Create results folder if it doesn't exist
    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_{timestamp}.txt"
    filepath = os.path.join(RESULTS_FOLDER, filename)
    
    # Write results to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("BEDROCK KNOWLEDGE BASE RETRIEVAL RESULTS\n")
        f.write("=" * 70 + "\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Query: {query}\n")
        f.write(f"Search Type: {search_type}\n")
        f.write(f"Companies: {company_names if company_names else 'All companies'}\n")
        f.write(f"Total Results: {len(all_results)}\n")
        f.write(f"Search Time: {elapsed_ms}ms\n")
        f.write("=" * 70 + "\n\n")
        
        for i, result in enumerate(all_results, 1):
            f.write(f"{'=' * 70}\n")
            f.write(f"RESULT {i}\n")
            f.write(f"{'=' * 70}\n")
            f.write(f"Score: {result['score']:.4f}\n")
            
            # Write company info
            if '_company_searched' in result:
                f.write(f"Company Searched: {result['_company_searched']}\n")
            
            # Write all metadata
            f.write("\nMetadata:\n")
            metadata = result.get('metadata', {})
            if metadata:
                for key, value in metadata.items():
                    f.write(f"  {key}: {value}\n")
            else:
                f.write("  No metadata available\n")
            
            # Write full text
            f.write(f"\nText:\n")
            f.write(f"{result['text']}\n")
            f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("END OF RESULTS\n")
        f.write("=" * 70 + "\n")
    
    return filepath


def save_results_to_json(query, search_type, company_names, all_results, elapsed_ms):
    """
    Save search results to a JSON file in the results folder.
    
    Args:
        query: Search query
        search_type: Search type used
        company_names: List of companies searched
        all_results: List of all results
        elapsed_ms: Total elapsed time
    """
    # Create results folder if it doesn't exist
    os.makedirs(RESULTS_FOLDER, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_{timestamp}.json"
    filepath = os.path.join(RESULTS_FOLDER, filename)
    
    # Prepare data
    data = {
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "search_type": search_type,
        "companies": company_names if company_names else "all",
        "total_results": len(all_results),
        "elapsed_ms": elapsed_ms,
        "results": all_results
    }
    
    # Write to JSON file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath


if __name__ == "__main__":
    print("=" * 70)
    print("BEDROCK KNOWLEDGE BASE RETRIEVAL")
    print("=" * 70)
    print(f"Query: {QUERY}")
    print(f"Results per search: {K}")
    print(f"Search type: {SEARCH_TYPE}")
    print(f"Companies: {COMPANY_NAMES if COMPANY_NAMES else 'All companies'}")
    print("=" * 70)
    
    try:
        all_results = []
        total_elapsed_ms = 0
        
        # If no company filter, search all
        if not COMPANY_NAMES:
            print("\n🔍 Searching all companies...")
            results = retrieve_api(QUERY, K, SEARCH_TYPE, company_name=None)
            
            print(f"✓ Found {len(results['results'])} results in {results['elapsed_ms']}ms")
            print(f"✓ KB ID: {results['kb_id']}\n")
            
            all_results = results['results']
            total_elapsed_ms = results['elapsed_ms']
            
            for i, result in enumerate(results['results'], 1):
                print(f"--- Result {i} ---")
                print(f"Score: {result['score']:.4f}")
                
                # Print ALL metadata fields
                metadata = result.get('metadata', {})
                if metadata:
                    print("Metadata:")
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
                else:
                    print("Metadata: None")
                
                print(f"Text: {result['text'][:200]}...")
                print()
        
        # If company list provided, search each company
        else:
            for company in COMPANY_NAMES:
                print(f"\n🔍 Searching: {company}...")
                results = retrieve_api(QUERY, K, SEARCH_TYPE, company_name=company)
                
                print(f"✓ Found {len(results['results'])} results in {results['elapsed_ms']}ms")
                
                total_elapsed_ms += results['elapsed_ms']
                
                for result in results['results']:
                    result['_company_searched'] = company
                    all_results.append(result)
            
            # Sort all results by score
            all_results.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"\n{'=' * 70}")
            print(f"TOTAL RESULTS: {len(all_results)}")
            print(f"{'=' * 70}\n")
            
            for i, result in enumerate(all_results[:K], 1):  # Show top K overall
                print(f"--- Result {i} ---")
                print(f"Score: {result['score']:.4f}")
                print(f"Company searched: {result['_company_searched']}")
                
                # Print ALL metadata fields
                metadata = result.get('metadata', {})
                if metadata:
                    print("Metadata:")
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
                else:
                    print("Metadata: None")
                
                print(f"Text: {result['text'][:200]}...")
                print()
        
        # Save results to files
        if SAVE_RESULTS and all_results:
            print(f"\n{'=' * 70}")
            print("SAVING RESULTS")
            print(f"{'=' * 70}")
            
            # Save as TXT
            txt_file = save_results_to_file(
                QUERY, SEARCH_TYPE, COMPANY_NAMES, all_results, total_elapsed_ms
            )
            print(f"✓ Saved to TXT: {txt_file}")
            
            # Save as JSON
            json_file = save_results_to_json(
                QUERY, SEARCH_TYPE, COMPANY_NAMES, all_results, total_elapsed_ms
            )
            print(f"✓ Saved to JSON: {json_file}")
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has KB_API_URL and KB_API_KEY")
        print("2. Verify API key is active in AWS Console")
        print("3. Check company names match exactly with metadata")
        print("4. Use only 'HYBRID' or 'SEMANTIC' for SEARCH_TYPE")