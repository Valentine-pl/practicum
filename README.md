# RAG Agent - Technical Documentation

Agent system with calculator and document retrieval tools via API Gateway.

Includes full request/response logging and monthly budget tracking.

---

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
```

Edit `.env`:
```dotenv
MODEL_API_URL=https://your-api.execute-api.us-east-1.amazonaws.com/prod/invoke
MODEL_API_KEY=your-key-here

KB_API_URL=https://your-kb-api.execute-api.us-east-1.amazonaws.com/prod/retrieve
KB_API_KEY=your-key-here
```

### 3. Run
```bash
python agent.py
```

---

## Project Structure
```
├── .env                 # API credentials (gitignored)
├── .env.example        # Credentials template
├── config.py           # All configuration parameters
├── agent.py            # Main agent with full logging
├── tools/
│   ├── __init__.py
│   ├── calculator.py   # SymPy calculator tool
│   └── retrieve.py     # KB retrieval tool
├── requirements.txt
└── README.md          # This file
```

---

## Configuration (`config.py`)

### Model Settings
```python
MODEL_ID = "us.anthropic.claude-sonnet-4-20250514-v1:0"
TEMPERATURE = 0.7
MAX_TOKENS = 4096
MAX_ITERATIONS = 5
```

### Retrieval Settings
```python
DEFAULT_K = 10                    # Number of results (1-50)
DEFAULT_SEARCH_TYPE = "HYBRID"    # HYBRID | SEMANTIC | KEYWORD
DEFAULT_COMPANY_FILTER = None     # Optional company filter
```

### Calculator Settings
```python
DEFAULT_PRECISION = 10             # Decimal places
DEFAULT_CALC_MODE = "evaluate"     # evaluate | solve
```

---

## How It Works

### Agent Flow

1. User sends message → Added to conversation history
2. Agent calls model with tools and conversation history
3. Model decides:
   - Use tool → Execute tool → Send result back → Loop
   - Answer directly → Return final response
4. Track costs for each iteration
5. Display budget usage after each request

### Tools Available

#### 1. `calculator`
- **Input**: `expression`, `mode`, `precision`
- **Output**: Calculation result
- **Example**: `"2^10"` → `1024`

#### 2. `retrieve_documents`
- **Input**: `query`, `k`, `search_type`, `company_name`
- **Output**: Ranked document chunks with scores
- **Example**: Query "CEO" → 10 chunks with scores 0.0-1.0

---

## Budget Tracking

### Monthly Limits

Each API key has a monthly budget limit (default: **$100**).

Budget is checked **before** each Bedrock API call.

### Budget Display

After each request, you see:
```
────────────────────────────────────────────────────────────────────────────────
  💰 BUDGET STATUS
────────────────────────────────────────────────────────────────────────────────
  Monthly Usage: $35.42 / $100.00
  [█████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 35.4%
  Remaining: $64.58
```

### Warnings

- **75% used**: Notice displayed
- **90% used**: Warning displayed
- **100% used**: Request blocked with error

### When You Hit the Limit
```
════════════════════════════════════════════════════════════════════════════════
                          ❌ BUDGET LIMIT EXCEEDED
════════════════════════════════════════════════════════════════════════════════

  You have used $100.00 of your $100.00 monthly limit.
  Please contact your instructor to increase your limit.

  Current usage: $100.00
  Monthly limit: $100.00
  Remaining: $0.00

  📧 Contact your instructor to increase your limit.
  ════════════════════════════════════════════════════════════════════════════
```

**You cannot make requests until:**
1. Instructor increases your limit, OR
2. New month starts (resets automatically)

---

## API Structure

### Model API

**Endpoint**: `POST /prod/invoke`

**Request**:
```json
{
  "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "messages": [...],
  "system": [...],
  "inference_config": {
    "maxTokens": 4096,
    "temperature": 0.7
  },
  "tools": [...],
  "tool_choice": {"auto": {}}
}
```

**Response** (Success):
```json
{
  "elapsed_ms": 3120,
  "model_id": "...",
  "stop_reason": "tool_use" | "end_turn",
  "output": {
    "message": {
      "content": [...]
    }
  },
  "usage": {
    "input_tokens": 852,
    "output_tokens": 123,
    "total_cost": 0.004401
  },
  "budget_info": {
    "current_usage": 35.42,
    "monthly_limit": 100.00,
    "remaining": 64.58,
    "percentage_used": 35.4
  }
}
```

**Response** (Budget Exceeded):
```json
{
  "error": "Monthly budget limit exceeded",
  "budget_info": {
    "current_usage": 100.00,
    "monthly_limit": 100.00,
    "remaining": 0.00
  },
  "message": "You have used $100.00 of your $100.00 monthly limit. Please contact your instructor to increase your limit."
}
```

**HTTP Status Codes**:
- `200`: Success
- `400`: Bad request
- `401`: Invalid API key
- `429`: **Budget limit exceeded**
- `500`: Server error

### Knowledge Base API

**Endpoint**: `POST /prod/retrieve`

**Request**:
```json
{
  "query": "CEO",
  "k": 10,
  "search_type": "HYBRID",
  "company_name": null
}
```

**Response**:
```json
{
  "status": "success",
  "query": "CEO",
  "search_type": "HYBRID",
  "k": 10,
  "results_count": 10,
  "results": [
    {
      "rank": 1,
      "text": "...",
      "score": 0.58,
      "metadata": {
        "company_name": "...",
        "x-amz-bedrock-kb-document-page-number": 192
      }
    }
  ]
}
```

---

## Output Format

### Complete Request/Response Logging
```
════════════════════════════════════════════════════════════════════════════════
                                🌐 API REQUEST #1
════════════════════════════════════════════════════════════════════════════════
[12:00:01.234] 🌐 Model: us.anthropic.claude-sonnet-4-20250514-v1:0
[12:00:01.234] 🌐 Messages in conversation: 1

📤 REQUEST PAYLOAD
{
  "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
  "messages": [...],
  "tools": [...]
}

[12:00:01.235] 🌐 Sending to Bedrock...
[12:00:04.567] ✅ Response in 3.33s

════════════════════════════════════════════════════════════════════════════════
                                📥 FULL API RESPONSE
════════════════════════════════════════════════════════════════════════════════
{
  "elapsed_ms": 3330,
  "model_id": "...",
  "stop_reason": "tool_use",
  "output": {...},
  "usage": {...},
  "budget_info": {...}
}

────────────────────────────────────────────────────────────────────────────────
  💰 BUDGET STATUS
────────────────────────────────────────────────────────────────────────────────
  Monthly Usage: $35.42 / $100.00
  [█████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 35.4%
  Remaining: $64.58

📊 USAGE METRICS
  Input Tokens:  852
  Output Tokens: 152
  Cost:          $0.004836
  Stop Reason:   tool_use
```

### Tool Execution Details
```
════════════════════════════════════════════════════════════════════════════════
                      🔧 TOOL EXECUTION: retrieve_documents
════════════════════════════════════════════════════════════════════════════════
[12:00:04.568] 🔧 Tool: retrieve_documents
[12:00:04.568] 🔧 ID: tooluse_ABC123

📥 TOOL INPUT
{
  "query": "CEO",
  "k": 10,
  "search_type": "HYBRID"
}

[12:00:04.569] 🔧 Executing...

════════════════════════════════════════════════════════════════════════════════
                      📤 FULL TOOL RESULT: retrieve_documents
════════════════════════════════════════════════════════════════════════════════
{
  "status": "success",
  "results_count": 10,
  "results": [...]
}

────────────────────────────────────────────────────────────────────────────────
  🔍 RETRIEVAL ANALYSIS
────────────────────────────────────────────────────────────────────────────────
  Total Results: 10
  Query: CEO
  Search Type: HYBRID

  📊 Score Distribution:
  Rank 1: 0.5811 |█████████████████████████████░░░░░░░░░░░░░░░░░░░| Company (p.192)
  Rank 2: 0.4907 |████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░| Company (p.120)
  ...

  📄 FULL DOCUMENT CHUNKS:
  ────────────────────────────────────────────────────────────────────────────

  CHUNK #1 (Score: 0.5811)
  Company: אבגול2023
  Page: 192.0
  Source: s3://reports-hackathon-data-source-1/אבגול2023.pdf

  TEXT:
  ────────────────────────────────────────────────────────────────────────────
  [COMPLETE UNTRUNCATED CHUNK TEXT HERE]
  ────────────────────────────────────────────────────────────────────────────
```

---

## Commands
```bash
# Interactive commands
👤 You: your question      # Ask questions
👤 You: reset              # Clear conversation history
👤 You: save               # Save session to JSON
👤 You: quit               # Exit and save
```

---

## Session Logs

Automatically saved on quit, or manually with `save` command.

**Filename**: `session_YYYYMMDD_HHMMSS.json`

**Contents**:
```json
{
  "session_cost": 0.050379,
  "total_requests": 2,
  "conversation_history": [...],
  "iteration_logs": [
    {
      "tool": "retrieve_documents",
      "input": {...},
      "result": {...},
      "timestamp": "2026-01-04T12:00:15"
    }
  ],
  "timestamp": "2026-01-04T12:05:30"
}
```

---

## Cost Calculation

**Pricing** (per 1M tokens):
- Input: $3.00
- Output: $15.00

**Formula**:
```
cost = (input_tokens / 1,000,000 × $3.00) + (output_tokens / 1,000,000 × $15.00)
```

**Example**:
- Input: 852 tokens → $0.002556
- Output: 123 tokens → $0.001845
- **Total**: $0.004401

---

## Parameters

### `k` (retrieval count)
- Min: 1
- Max: 50
- Default: 10
- **Effect**: More chunks = more context but higher cost

### `search_type`
- `HYBRID`: Semantic + keyword combined
- `SEMANTIC`: Vector similarity only
- `KEYWORD`: Exact text matching
- Default: `HYBRID`

### `temperature`
- Range: 0.0 - 1.0
- 0.0 = deterministic/focused
- 1.0 = creative/random
- Default: 0.7

---

## Troubleshooting

### Budget Errors

**Error**: `429 - Monthly budget limit exceeded`

**Solution**:
1. Check your usage in the agent output
2. Contact instructor with your API key ID
3. Wait for limit increase
4. OR wait until next month (auto-resets)

### API Errors

| Code | Meaning | Solution |
|------|---------|----------|
| 400 | Bad request | Check request format |
| 401 | Invalid API key | Verify `.env` file |
| 429 | Budget exceeded | Contact instructor |
| 500 | Server error | Try again or contact instructor |

### No Results

**Problem**: `results_count: 0`

**Solutions**:
- Try different `search_type`
- Increase `k` value
- Rephrase query
- Remove `company_filter` if too restrictive

---

## Backend Architecture
```
┌─────────────┐
│  Student    │
│  (agent.py) │
└──────┬──────┘
       │
       ├─ POST /invoke ──► Lambda ──► Bedrock API
       │                     │
       │                     ├──► Check Budget (DynamoDB)
       │                     ├──► Call Bedrock
       │                     └──► Log Usage (DynamoDB)
       │
       └─ POST /retrieve ─► Lambda ──► Knowledge Base
```

### DynamoDB Tables

**StudentUsage**:
- Primary Key: `requestid`
- Attributes: `api_key_id`, `date`, `model_id`, `input_tokens`, `output_tokens`, `total_cost`

**StudentBudgets**:
- Primary Key: `api_key_id`
- Attributes: `monthly_limit`, `created_at`

---

## Budget Management (Instructor Only)

### View Student Usage
```bash
# Get all usage for a student (by API key ID)
aws dynamodb scan \
    --table-name StudentUsage \
    --filter-expression "api_key_id = :key AND begins_with(#date, :month)" \
    --expression-attribute-names '{"#date": "date"}' \
    --expression-attribute-values '{":key":{"S":"wvwsn32q88"},":month":{"S":"2026-01"}}'
```

### Check Current Budget
```bash
aws dynamodb get-item \
    --table-name StudentBudgets \
    --key '{"api_key_id":{"S":"wvwsn32q88"}}'
```

### Update Student Limit
```bash
aws dynamodb put-item \
    --table-name StudentBudgets \
    --item '{
        "api_key_id": {"S": "wvwsn32q88"},
        "monthly_limit": {"N": "200.00"}
    }'
```

### View All Budgets
```bash
aws dynamodb scan --table-name StudentBudgets
```

### Calculate Total Usage
```bash
# Get sum of costs for specific API key
aws dynamodb scan \
    --table-name StudentUsage \
    --filter-expression "api_key_id = :key" \
    --expression-attribute-values '{":key":{"S":"wvwsn32q88"}}' \
    --projection-expression "total_cost"
```

---

## Dependencies
```txt
requests>=2.31.0
python-dotenv>=1.0.0
sympy>=1.12
```