# Bootstrap Verdict Data Ingestion

## Overview

The **Bootstrap Verdict DataLoader** is a pure rule-based, LLM-free pipeline for ingesting raw Persian legal verdict text files into the MAHOUN system.

This pipeline:
- Reads raw `.txt` verdict files (UTF-8, Persian)
- Parses them into structured JSON-compatible dictionaries
- Saves each parsed verdict as `<filename>.parsed.json`
- Optionally indexes into VectorStore and/or Graph backend

**No LLM calls are made during parsing.** All extraction is rule-based using regex patterns and Persian text processing.

---

## Architecture

### Components

1. **Minimal Verdict Parser** (`pipelines/ingestion/minimal_verdict_parser.py`)
   - Pure Python library for parsing Persian legal verdicts
   - Rule-based extraction using regex patterns
   - Handles Persian text normalization and digit conversion
   - Returns structured JSON-compatible dictionaries

2. **Bootstrap Verdict DataLoader** (`orchestrator/bootstrap_verdict_dataloader.py`)
   - CLI orchestrator for batch processing verdict files
   - Iterates over `.txt` files in input directory
   - Writes `.parsed.json` files to output directory
   - Optional hooks for VectorStore and Graph ingestion

---

## JSON Schema

Each parsed verdict produces a JSON file with the following structure:

```json
{
  "case_meta": {
    "court_level": "دادگاه تجدیدنظر استان تهران",
    "procedure_stage": "تجدیدنظر",
    "case_type": "اعتراض ثالث / توقیف عملیات اجرایی",
    "is_final": true,
    "finality_basis": "ماده 348 قانون آیین دادرسی مدنی"
  },
  "parties": {
    "third_party_objector": {
      "title": "آقای",
      "name": "محمد احمدی",
      "father_name": "علی"
    },
    "third_party_objector_attorney": {
      "title": "آقای",
      "name": "حسن رضایی",
      "father_name": "رضا"
    },
    "respondents": [...],
    "respondents_attorneys": [...]
  },
  "claims": {
    "main": [
      "اعتراض ثالث به عملیات اجرایی",
      "رفع توقیف"
    ],
    "execution_files": [
      "پرونده 123/456 شعبه 5"
    ]
  },
  "first_instance_summary": {
    "decision": "رد دعوا",
    "reasoning_keywords": ["عدم احراز", "فقدان دلیل"]
  },
  "appeal_court_reasoning": {
    "result": "نقض رأی بدوی",
    "key_points": ["ماده 348", "اصاله الصحه"]
  },
  "legal_references": {
    "substantive_law": [
      "ماده 10 قانون مدنی",
      "ماده 219 قانون مدنی"
    ],
    "procedural_law": [
      "ماده 348 قانون آیین دادرسی مدنی",
      "ماده 358 قانون آیین دادرسی مدنی"
    ],
    "fiqh_principles": [
      "اصاله الصحه",
      "قاعده لاضرر",
      "قاعده ید"
    ]
  },
  "final_decision": {
    "appeal_result": "تأیید رأی بدوی",
    "third_party_objection": "پذیرفته شده",
    "is_final": true
  },
  "system_tags": [
    "اعتراض ثالث اجرایی",
    "رفع توقیف",
    "تأیید رأی بدوی",
    "اصاله الصحه"
  ]
}
```

---

## Usage Examples

### Basic Usage

Process all `.txt` files in a directory:

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts
```

**Output:** Creates `/home/haji/DATA/mahoun_bootstrap/raw_verdicts_parsed/` with `.parsed.json` files.

---

### Specify Output Directory

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --output-dir /home/haji/DATA/mahoun_bootstrap/parsed_verdicts
```

---

### Process Limited Number of Files

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --limit 10
```

**Use case:** Test parsing on first 10 files before processing entire dataset.

---

### Overwrite Existing Parsed Files

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --overwrite
```

**Default behavior:** Skips files that already have `.parsed.json` output.

---

### With VectorStore Integration

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --with-vectorstore
```

**Requires:** VectorStore manager must be configured and available.

**Behavior:** After parsing, each verdict is indexed into the vector database for semantic search.

---

### With Graph Backend Integration

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --with-graph
```

**Requires:** Neo4j graph backend must be configured and available.

**Behavior:** After parsing, each verdict is ingested into the knowledge graph.

---

### Full Integration (VectorStore + Graph)

```bash
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /home/haji/DATA/mahoun_bootstrap/raw_verdicts \
  --with-vectorstore \
  --with-graph
```

**Recommended for production:** Enables full RAG + Graph capabilities.

---

## Supported Case Types

The parser supports 34+ types of Persian legal cases:

### Civil Cases (دعاوی مدنی)
- اعتراض ثالث (Third-party objection)
- توقیف عملیات اجرایی (Execution suspension)
- رفع توقیف (Lifting suspension)
- خلع ید (Eviction)
- تخلیه (Evacuation)
- الزام به تنظیم سند (Obligation to register document)
- ابطال سند (Document annulment)
- فسخ معامله (Contract rescission)

### Financial Claims (دعاوی مالی)
- مطالبه وجه (Claim for payment)
- مطالبه خسارت (Claim for damages)
- مطالبه نفقه (Alimony claim)
- مطالبه مهریه (Dowry claim)
- مطالبه مزد (Wage claim)

### Family Law (دعاوی خانوادگی)
- طلاق (Divorce)
- حضانت (Custody)
- نفقه (Alimony)
- مهریه (Dowry)

### Inheritance (دعاوی ارث)
- ارث و میراث (Inheritance)
- انحصار وراثت (Certificate of inheritance)
- تقسیم ترکه (Estate division)
- وصیت (Will)

### Labor Law (دعاوی کارگری)
- اعتراض به اخراج (Objection to dismissal)
- بازگشت به کار (Reinstatement)
- مطالبه حق سنوات (Severance claim)

### Commercial Law (دعاوی تجاری)
- اوراق تجاری (Commercial papers: check, promissory note)
- انحلال شرکت (Company dissolution)
- ورشکستگی (Bankruptcy)

### Criminal Law (دعاوی جزایی)
- دیه (Blood money)
- قصاص (Retaliation)
- کلاهبرداری (Fraud)
- خیانت در امانت (Breach of trust)

---

## Legal References Extraction

The parser identifies and classifies legal references into three categories:

### 1. Substantive Law (قوانین موضوعی)
- قانون مدنی (Civil Code)
- قانون تجارت (Commercial Code)
- قانون کار (Labor Code)
- قانون مجازات (Penal Code)
- قانون حمایت خانواده (Family Protection Act)
- قانون امور حسبی (Probate Code)
- And 10+ other substantive laws

### 2. Procedural Law (قوانین آیین دادرسی)
- قانون آیین دادرسی مدنی (Civil Procedure Code)
- قانون اجرای احکام مدنی (Civil Execution Code)
- قانون آیین دادرسی کیفری (Criminal Procedure Code)

### 3. Fiqh Principles (اصول فقهی)
- اصاله الصحه (Presumption of validity)
- قاعده لاضرر (No harm principle)
- قاعده ید (Possession principle)
- قاعده تسلیط (Dominion principle)
- And 10+ other principles

---

## Advanced Features

### Dynamic Pattern Extraction

The parser uses dynamic patterns to extract custom claims:

**Pattern: "الزام به + [anything]"**
- الزام به تحویل کالا (Obligation to deliver goods)
- الزام به پرداخت وجه (Obligation to pay)
- الزام به رفع تصرف (Obligation to remove possession)

**Pattern: "مطالبه + [anything]"**
- مطالبه خسارت دادرسی (Claim for litigation costs)
- مطالبه اجرت المثل (Claim for fair rental value)
- مطالبه حق مسلم (Claim for undisputed right)

### System Tags

Automatically generates 50+ semantic tags for categorization:
- Case type tags
- Legal domain tags
- Procedural stage tags
- Decision outcome tags
- Legal principle tags

---

## Error Handling

### Graceful Degradation

The pipeline is designed to continue processing even if optional integrations fail:

- **Missing VectorStore:** Prints warning, continues with JSON output
- **Missing Graph backend:** Prints warning, continues with JSON output
- **Parsing errors:** Logs error, skips file, continues with next file

### Exit Codes

- `0`: All files processed successfully
- `1`: Some files failed to parse (JSON still written for successful ones)

---

## Performance

### Benchmarks (approximate)

- **Parsing speed:** ~50-100 verdicts/second (rule-based, no LLM)
- **Memory usage:** ~10-20 MB per 1000 verdicts
- **Disk I/O:** Main bottleneck for large datasets

### Recommendations

- For 10,000+ files: Use `--limit` for incremental processing
- For production: Enable `--with-vectorstore --with-graph` for full integration
- For testing: Start with `--limit 10` to validate patterns

---

## Troubleshooting

### Common Issues

**Issue:** Parser not recognizing case type
- **Solution:** Check if case type pattern exists in `detect_case_type()`
- **Workaround:** Case type will be marked as "نامشخص" (unknown)

**Issue:** Legal articles not extracted
- **Solution:** Verify article reference format: "ماده [number] قانون [law name]"
- **Example:** "ماده ۱۰ قانون مدنی" ✓  vs  "م 10" ✗

**Issue:** Party names not extracted
- **Solution:** Ensure party names follow format: "(آقای|خانم) [name] فرزند [father]"
- **Example:** "آقای محمد احمدی فرزند علی" ✓

**Issue:** VectorStore indexing fails
- **Solution:** Check VectorStore configuration in `config/settings.py`
- **Workaround:** Run without `--with-vectorstore` flag

---

## Development

### Adding New Case Type Patterns

Edit `pipelines/ingestion/minimal_verdict_parser.py`:

```python
def detect_case_type(text: str) -> str:
    types = []
    
    # Add your pattern here
    if re.search(r'your_pattern_here', text):
        types.append('نوع دعوای جدید')
    
    # ... existing patterns ...
```

### Adding New Legal References

```python
def extract_legal_articles(text: str) -> tuple:
    # ... existing code ...
    
    # Add new law to substantive law list
    if any(keyword in law_name for keyword in [
        'مدنی',
        'تجارت',
        'your_new_law_keyword',  # Add here
    ]):
        substantive_law.append(ref)
```

### Adding New Fiqh Principles

```python
fiqh_patterns = [
    r'(اصاله\s+الصحه)',
    r'(your_new_principle)',  # Add here
]
```

---

## Testing

### Unit Tests

```bash
cd /home/haji/Desktop/MAHOUN_v2_core_only_baseline
python3 -c "from pipelines.ingestion.minimal_verdict_parser import parse_verdict_text; print('OK')"
```

### Integration Test

```bash
# Create test verdict
mkdir -p /tmp/test_verdicts
echo "دادنامه شماره ۱۴۰۲..." > /tmp/test_verdicts/sample.txt

# Run parser
python -m orchestrator.bootstrap_verdict_dataloader \
  --input-dir /tmp/test_verdicts

# Check output
cat /tmp/test_verdicts_parsed/sample.parsed.json
```

---

## Appendix: File Locations

```
MAHOUN_v2_core_only_baseline/
├── pipelines/
│   └── ingestion/
│       ├── __init__.py
│       ├── pipeline.py (existing)
│       └── minimal_verdict_parser.py (NEW)
├── orchestrator/
│   ├── __init__.py
│   ├── orchestrator.py (existing)
│   └── bootstrap_verdict_dataloader.py (NEW)
└── docs/
    └── BOOTSTRAP_VERDICTS.md (this file)
```

---

## License & Credits

Part of the MAHOUN Legal AI System.

Developed for Persian (Farsi) legal document processing.

---

**Last Updated:** 2025-11-27

