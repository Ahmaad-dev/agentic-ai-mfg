# Smart Planning Snapshot Auto-Corrector

Intelligent, LLM-powered tool for automatically correcting validation errors in ESAROM Smart Planning snapshots.

## Architecture

This tool uses a **hybrid approach**:
- **LLM intelligence** for context-aware corrections (not hard-coded rules)
- **Structured outputs** via OpenAI's `response_format` to ensure valid responses
- **API integration** with Smart Planning for real validation
- **Context extraction** to reduce token costs by 99.9% (2KB vs 1.6MB)

### Workflow

```
1. Upload snapshot to Smart Planning API
2. Get validation messages (errors + warnings)
3. Extract minimal context for each error (~2KB)
4. Use LLM with structured Pydantic schemas to generate corrections
5. Apply corrections to snapshot
6. Re-upload and validate
7. Repeat until no errors remain
```

## Components

### Core Modules

1. **`correction_models.py`** - Type-safe Pydantic schemas
   - `DensityCorrectionRequest/Response` - Fix invalid density values
   - `DuplicateIDCorrectionRequest/Response` - Resolve duplicate IDs
   - `EmptyIDCorrectionRequest/Response` - Generate valid IDs
   - `MissingReferenceRequest/Response` - Fix broken references
   - `CorrectionLogEntry` - Audit trail with LLM reasoning

2. **`smart_planning_api.py`** - API client
   - `create_snapshot()` - Upload snapshot
   - `get_validation_messages()` - Fetch errors/warnings
   - `update_snapshot()` - Update during iteration
   - Handles pagination, errors, timeouts

3. **`context_extractor.py`** - Context extraction (99.9% token reduction)
   - Extracts only affected objects + context (max 10 similar items)
   - Routes errors to appropriate extraction methods
   - Example: For density error on Article 123, sends only that article + 10 similar ones

4. **`llm_corrector.py`** - LLM with structured outputs
   - Uses OpenAI's `beta.chat.completions.parse()` with `response_format`
   - Guarantees schema-compliant responses (Pydantic validation)
   - Includes LLM reasoning for transparency

5. **`correction_applier.py`** - Apply corrections
   - Applies LLM corrections to snapshot
   - Maintains audit log with timestamps and reasoning
   - Exports log to JSON for review

6. **`main_correction.py`** - Orchestrator
   - CLI entry point
   - Coordinates full auto-correction loop
   - Max iterations to prevent infinite loops

## Installation

```bash
pip install -r requirements.txt
```

### Requirements

- `openai` - LLM API with structured outputs
- `pydantic` - Type-safe models with validation
- `requests` - HTTP client for Smart Planning API
- `python-dotenv` - Environment variable management

## Usage

### Basic Usage

```bash
python main_correction.py snapshot.json \
    --api-url https://your-api.com/api/v1 \
    --api-key YOUR_API_KEY \
    --openai-key YOUR_OPENAI_KEY
```

### Advanced Options

```bash
python main_correction.py snapshot.json \
    --api-url https://smart-planning.example.com/api/v1 \
    --api-key $(cat .env | grep SMART_PLANNING_API_KEY | cut -d'=' -f2) \
    --openai-key $(cat .env | grep OPENAI_API_KEY | cut -d'=' -f2) \
    --model gpt-4o \
    --output corrected_snapshot.json \
    --log correction_log.json \
    --max-iterations 15
```

### Environment Variables

Create a `.env` file:

```env
SMART_PLANNING_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_key_here
```

Then use without `--api-key` and `--openai-key` flags.

## Token Cost Optimization

### Problem
- Full snapshot: 80k-1M lines, ~1.6MB
- Sending to LLM: ~400k tokens = **$4 per correction** (GPT-4)

### Solution: Context Extraction
- Extract only affected object + context
- Example: Article + 10 similar articles = ~2KB
- Result: ~500 tokens = **$0.001 per correction**
- **99.9% cost reduction**

### Example Context

For density error on Article 106270:
```json
{
  "error_message": "[validate_density_values] Article 106270 has invalid rel_density_min: 0.0",
  "affected_article": { "articleId": "106270", "relDensityMin": 0.0, ... },
  "similar_articles": [
    { "articleId": "106271", "relDensityMin": 1.2, "relDensityMax": 1.5, ... },
    { "articleId": "106272", "relDensityMin": 1.1, "relDensityMax": 1.4, ... },
    ...  // max 10 similar articles
  ]
}
```

LLM receives **only this 2KB** instead of entire 1.6MB snapshot.

## Supported Error Types

### Currently Implemented

1. **Density Validation** (`validate_density_values`)
   - Invalid relDensityMin/Max values (e.g., 0.0)
   - LLM calculates median from similar articles

2. **Duplicate IDs** (`validate_unique_ids` - duplicates)
   - Multiple items with same ID
   - LLM decides which to keep, renames others

3. **Empty IDs** (`validate_unique_ids` - empty)
   - Null or empty ID fields
   - LLM generates valid unique IDs

4. **Missing References** (`validate_work_plan_ids`, etc.)
   - References to non-existent objects
   - LLM maps to valid targets

### In Progress

- Equipment availability validation
- Work item configuration completeness
- Start/end operation existence
- Equipment-worker qualification compatibility
- Equipment predecessor references
- Packaging compatibility

## Structured Output Enforcement

Uses **OpenAI's structured output feature** to guarantee valid responses:

```python
from openai import OpenAI
from correction_models import DensityCorrectionResponse

client = OpenAI()
completion = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[...],
    response_format=DensityCorrectionResponse  # Enforces Pydantic schema
)

response = completion.choices[0].message.parsed  # Type-safe!
```

Benefits:
- **No invalid JSON** - guaranteed schema compliance
- **Type safety** - Pydantic validates all fields
- **Field constraints** - e.g., `relDensityMax >= relDensityMin`
- **Enum enforcement** - only allowed values

## Audit Logging

Every correction is logged with:
- Timestamp
- Error type
- Affected ID
- Correction applied
- **LLM reasoning** (transparency)

Example log entry:
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "error_type": "density_validation",
  "affected_id": "106270",
  "correction_applied": {
    "relDensityMin": 1.15,
    "relDensityMax": 1.45,
    "method": "median_calculation"
  },
  "llm_reasoning": "Calculated median from 8 similar articles of same type. Median relDensityMin: 1.15, median relDensityMax: 1.45."
}
```

## Testing

### Manual Testing

1. Prepare snapshot and validation files
2. Run correction:
   ```bash
   python main_correction.py test_snapshot.json \
       --api-url https://test-api.com/api/v1 \
       --api-key test_key \
       --openai-key sk-...
   ```
3. Review correction log
4. Validate corrected snapshot

### With Mock API (for development)

Use a local mock server to test without real API:
```bash
# TODO: Add mock server setup
```

## Architecture Decisions

### Why LLM instead of hard-coded rules?

**Before:**
- Hard-coded: "Set density to 1.0"
- Problem: Not context-aware, loses data quality

**After:**
- LLM: "Calculate median from similar articles"
- Benefit: Intelligent, context-aware corrections

### Why structured outputs?

**Before:**
- LLM returns free-form text
- Problem: Invalid JSON, type errors, schema violations

**After:**
- Enforced Pydantic schemas via `response_format`
- Benefit: Guaranteed valid, type-safe responses

### Why context extraction?

**Before:**
- Send entire 1.6MB snapshot to LLM
- Cost: ~$4 per correction

**After:**
- Send only 2KB relevant context
- Cost: ~$0.001 per correction
- **99.9% cost reduction**

## File Structure

```
demo/smart-planning/
├── correction_models.py      # Pydantic schemas (NEW)
├── smart_planning_api.py     # API client (NEW)
├── context_extractor.py      # Context extraction (NEW)
├── llm_corrector.py          # LLM with structured outputs (NEW)
├── correction_applier.py     # Apply corrections (NEW)
├── main_correction.py        # Orchestrator (REWRITTEN)
├── report_agent.py           # Final report generation (KEEP)
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

### Deprecated (old deterministic approach)
- `snapshot_corrector.py` - Delete after migration
- `auto_fix_loop.py` - Delete after migration
- `README_AutoFix.md` - Delete after migration

## Migration from Old System

If you have the old deterministic tool, migration is simple:

1. Install new dependencies:
   ```bash
   pip install openai pydantic
   ```

2. Update `.env` with API keys:
   ```env
   SMART_PLANNING_API_KEY=...
   OPENAI_API_KEY=...
   ```

3. Use new CLI:
   ```bash
   # Old: python main_correction.py --snapshot X --validation Y
   # New: python main_correction.py X --api-url URL
   ```

4. Delete old files:
   ```bash
   rm snapshot_corrector.py auto_fix_loop.py README_AutoFix.md
   ```

## Troubleshooting

### "Module not found: openai"
```bash
pip install openai
```

### "Model does not support structured outputs"
Use `gpt-4o` or `gpt-4o-mini`:
```bash
python main_correction.py snapshot.json --model gpt-4o-mini
```

### "Could not extract context"
Check error message format in logs. May need to add new extraction pattern.

### "Max iterations reached"
Some errors may need manual review. Check correction log for details.

## Future Enhancements

- [ ] Add remaining error type handlers (equipment, packaging, etc.)
- [ ] Implement retry logic for LLM API failures
- [ ] Add batch processing for multiple snapshots
- [ ] Create web UI for non-technical users
- [ ] Optimize LLM prompts for better accuracy
- [ ] Add unit tests for each component
- [ ] Generate final HTML reports with visualizations

## License

Internal ESAROM tool - proprietary.

## Contact

For questions or issues, contact the AI team.
