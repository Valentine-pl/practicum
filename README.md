# Knowledge Base Retrieval API - Client Guide

Simple Python client to search documents in AWS Bedrock Knowledge Base.

---

## Quick Setup

### 1. Install Dependencies
```bash
pip install requests python-dotenv
```

### 2. Configure API Credentials

Create a `.env` file:
```env
KB_API_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/prod/retrieve
KB_API_KEY=your-api-key-here
```

**Get your credentials from AWS Console:**
- `KB_API_URL`: API Gateway → Your API → Stages → Invoke URL
- `KB_API_KEY`: API Gateway → API Keys → Your Key

---

## How to Use

### Step 1: Open `retrieve_api.py`

### Step 2: Configure Search Parameters

Find this section at the top of the file:
```python
# ============================================================================
# SEARCH PARAMETERS - Configure your search here
# ============================================================================
QUERY = "השקעות בהון החברה ועסקאות במניותיה"  # Your search question
K = 10  # Number of results (1-50)
SEARCH_TYPE = "SEMANTIC"  # Options: "HYBRID" or "SEMANTIC" only
COMPANY_NAMES = ["אבגול2023"]  # List of companies, or None for all
```

### Step 3: Run
```bash
python retrieve_api.py
```

---

## Configuration Options

### `QUERY` (Required)
Your search question in Hebrew or English.

**Examples:**
```python
QUERY = "What is RAG architecture?"
QUERY = "Q3 sales report"
QUERY = "השקעות בהון החברה ועסקאות במניותיה"
QUERY = "מה תפקיד ה-Vector DB בארכיטקטורת RAG?"
```

### `K` (Default: 10)
Number of results to return (1-50).

**Examples:**
```python
K = 5   # Get top 5 results
K = 20  # Get top 20 results
K = 50  # Maximum allowed
```

### `SEARCH_TYPE` (Default: "SEMANTIC")
Search algorithm to use:

| Type | Best For | Description |
|------|----------|-------------|
| `"HYBRID"` | Most queries | Combines semantic + keyword search (recommended) |
| `"SEMANTIC"` | Natural questions | Finds similar meanings using embeddings |

**⚠️ Important:** AWS Bedrock only supports `"HYBRID"` and `"SEMANTIC"`. `"KEYWORD"` is NOT supported.

**Examples:**
```python
SEARCH_TYPE = "HYBRID"     # Recommended for most queries
SEARCH_TYPE = "SEMANTIC"   # Good for conceptual questions
```

### `COMPANY_NAMES` (Default: None)
Filter by company name(s).

**Examples:**
```python
# Search all companies
COMPANY_NAMES = None

# Search one company
COMPANY_NAMES = ["אבגול2023"]

# Search multiple companies
COMPANY_NAMES = ["אבגול2023", "TechCorp", "RetailCo"]
```

**Important:** Company names must match exactly with the `company_name` field in document metadata.

---

## Usage Examples

### Example 1: Search All Documents
```python
QUERY = "What is machine learning?"
K = 10
SEARCH_TYPE = "HYBRID"
COMPANY_NAMES = None  # Search all companies
```

Run: `python retrieve_api.py`

**Output:**
```
🔍 Searching all companies...
✓ Found 10 results in 234ms
✓ KB ID: XXXXXXXXXX

--- Result 1 ---
Score: 0.8542
Company: TechCorp
Source: ml_guide.pdf
Text: Machine learning is a subset of artificial intelligence...
```

### Example 2: Search Specific Company (Hebrew)
```python
QUERY = "השקעות בהון החברה ועסקאות במניותיה"
K = 10
SEARCH_TYPE = "SEMANTIC"
COMPANY_NAMES = ["אבגול2023"]
```

**Output:**
```
🔍 Searching: אבגול2023...
✓ Found 9 results in 358ms

======================================================================
TOTAL RESULTS: 9
======================================================================

--- Result 1 ---
Score: 0.4734
Company searched: אבגול2023
Company in metadata: אבגול2023
Text: מאחר שמפעל בשנים 10%פיתוח א', שיעורי המס...
```

### Example 3: Compare Multiple Companies
```python
QUERY = "employee benefits policy"
K = 10
SEARCH_TYPE = "HYBRID"
COMPANY_NAMES = ["Acme Corp", "TechCorp", "RetailCo"]
```

**Output:**
```
🔍 Searching: Acme Corp...
✓ Found 8 results in 201ms

🔍 Searching: TechCorp...
✓ Found 6 results in 189ms

🔍 Searching: RetailCo...
✓ Found 4 results in 176ms

======================================================================
TOTAL RESULTS: 18
======================================================================

--- Result 1 ---
Score: 0.9234
Company searched: Acme Corp
...
```

### Example 4: Semantic Search
```python
QUERY = "מה ההבדל בין supervised ל-unsupervised learning?"
K = 8
SEARCH_TYPE = "SEMANTIC"
COMPANY_NAMES = None
```

### Example 5: Hybrid Search (Best Results)
```python
QUERY = "quarterly financial report 2024"
K = 15
SEARCH_TYPE = "HYBRID"
COMPANY_NAMES = ["אבגול2023"]
```

---

## Understanding Results

Each result contains:
```python
{
    "text": "Document content...",
    "score": 0.4734,  # Relevance score (0-1, higher is better)
    "metadata": {
        "company_name": "אבגול2023",
        "source": "document.pdf",
        # ... other metadata fields
    }
}
```

**Score Interpretation:**
- `> 0.7` = Highly relevant
- `0.5 - 0.7` = Moderately relevant  
- `0.3 - 0.5` = Lower relevance
- `< 0.3` = Weak relevance

**Note:** Scores in the 0.4-0.5 range (like your results) are common and can still be useful, especially for semantic searches in Hebrew.

---

## Troubleshooting

### Error: Invalid search type
```
ERROR: Invalid SEARCH_TYPE: 'KEYWORD'
Only 'HYBRID' and 'SEMANTIC' are supported by AWS Bedrock.
```
**Solution:** Change `SEARCH_TYPE` to either `"HYBRID"` or `"SEMANTIC"`.

### Error: Missing API credentials
```
ERROR: Missing API credentials!
Set KB_API_URL and KB_API_KEY in .env file
```
**Solution:** Create `.env` file with your credentials.

### Error: Authentication failed
```
Authentication failed. Check your API key.
```
**Solution:** 
1. Verify `KB_API_KEY` in `.env` is correct
2. Check key is active in AWS Console → API Gateway → API Keys

### No Results Found
```
✓ Found 0 results
```
**Solutions:**
- Try broader search terms
- Change `SEARCH_TYPE` from `"SEMANTIC"` to `"HYBRID"`
- Set `COMPANY_NAMES = None` to search all companies
- Verify company name spelling matches metadata exactly

### Low Relevance Scores
If scores are below 0.5:
- Try `"HYBRID"` instead of `"SEMANTIC"`
- Rephrase your query
- Use more specific terms
- Increase `K` to get more results

---

## Advanced Usage

### Use as Python Module
```python
from retrieve_api import retrieve_api

# Custom search
results = retrieve_api(
    query="your question",
    k=15,
    search_type="SEMANTIC",
    company_name="אבגול2023"
)

# Process results
for result in results['results']:
    if result['score'] > 0.5:  # Filter by score
        print(f"Score: {result['score']}")
        print(f"Text: {result['text'][:100]}")
```

### Batch Processing

Create `batch_search.py`:
```python
from retrieve_api import retrieve_api

queries = [
    "מה תפקיד ה-Vector DB?",
    "השקעות בהון החברה",
    "דוח רבעוני"
]

for query in queries:
    print(f"\nQuery: {query}")
    results = retrieve_api(
        query=query, 
        k=5, 
        search_type="HYBRID",
        company_name="אבגול2023"
    )
    print(f"Results: {len(results['results'])}")
    if results['results']:
        print(f"Top score: {results['results'][0]['score']:.4f}")
```

---

## Supported Search Types

### ✅ Supported by AWS Bedrock:
- `"HYBRID"` - Combines semantic and keyword matching (recommended)
- `"SEMANTIC"` - Embedding-based similarity search

### ❌ NOT Supported:
- `"KEYWORD"` - This will cause a validation error

---

## Support

**Check:**
1. `.env` file exists with correct credentials
2. API key is active in AWS Console
3. Company names match metadata exactly
4. Using only `"HYBRID"` or `"SEMANTIC"` for SEARCH_TYPE
5. Lambda logs in CloudWatch for errors

**AWS Console Links:**
- API Gateway: https://console.aws.amazon.com/apigateway
- CloudWatch Logs: https://console.aws.amazon.com/cloudwatch

---

## License

MIT