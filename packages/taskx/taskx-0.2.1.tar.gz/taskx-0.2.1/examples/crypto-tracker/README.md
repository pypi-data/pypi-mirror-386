# 📊 Cryptocurrency Price Tracker

**Real-world example demonstrating taskx task automation**

This project shows how to use **taskx** to automate a real-world data processing pipeline:
- 🌐 Fetch live cryptocurrency prices from public APIs
- ✅ Validate data quality
- 📈 Analyze and compute statistics
- 📄 Generate beautiful HTML reports

---

## 🚀 Quick Start

### 1. Install taskx

```bash
pip install taskx
```

### 2. Run the Complete Pipeline

```bash
# Run the full pipeline: fetch → validate → analyze → report
taskx pipeline
```

This will:
1. Fetch live prices for BTC, ETH, SOL, ADA, DOT
2. Validate data integrity
3. Compute statistics (avg, min, max)
4. Generate an HTML report

### 3. View the Report

```bash
# Generate and open the report in your browser
taskx view
```

---

## 📋 Available Tasks

List all available tasks:

```bash
taskx list
```

Output:
```
Available tasks:
  fetch      Fetch live cryptocurrency prices from API
  validate   Validate data quality and integrity
  analyze    Analyze prices and compute statistics
  report     Generate HTML report with visualizations
  pipeline   Run complete data pipeline
  check      Run all quality checks in parallel
  dev        Development mode: auto-run on file changes
  clean      Clean all generated data and reports
  quick      Quick fetch and analyze (no validation)
  view       Generate and view report in browser
```

---

## 🎯 Task Examples

### Individual Tasks

```bash
# Fetch prices only
taskx fetch

# Validate data
taskx validate

# Analyze data
taskx analyze

# Generate report
taskx report
```

### Task Dependencies

taskx automatically runs dependencies in the correct order:

```bash
# Running 'analyze' automatically runs 'fetch' and 'validate' first
taskx analyze
```

Output:
```
→ Running: fetch
✓ Completed: fetch (2.1s)
→ Running: validate
✓ Completed: validate (0.3s)
→ Running: analyze
✓ Completed: analyze (0.5s)
```

### Parallel Execution

Run quality checks in parallel for faster execution:

```bash
taskx check
```

### Watch Mode

Auto-run tasks when scripts change (perfect for development):

```bash
taskx watch dev
```

---

## 🏗️ Project Structure

```
crypto-tracker/
├── pyproject.toml          # taskx configuration
├── scripts/
│   ├── fetch_prices.py     # Fetch data from API
│   ├── validate_data.py    # Validate data quality
│   ├── analyze_data.py     # Compute statistics
│   └── generate_report.py  # Create HTML report
├── data/                   # Generated data files
│   ├── raw_prices.json
│   └── analysis.json
└── reports/                # Generated reports
    └── crypto_report.html
```

---

## 🔧 How It Works

### Task Dependencies

The pipeline is defined in `pyproject.toml`:

```toml
[tool.taskx.tasks]

# Simple task
fetch = {
    cmd = "python3 scripts/fetch_prices.py",
    description = "Fetch live prices"
}

# Task with dependency
validate = {
    depends = ["fetch"],
    cmd = "python3 scripts/validate_data.py"
}

# Complete pipeline with multiple dependencies
pipeline = {
    depends = ["fetch", "validate", "analyze", "report"],
    cmd = "echo 'Pipeline complete!'"
}
```

### Environment Variables

Use environment variables for flexibility:

```toml
[tool.taskx.env]
PYTHON = "python3"
SCRIPTS_DIR = "scripts"

[tool.taskx.tasks]
fetch = { cmd = "${PYTHON} ${SCRIPTS_DIR}/fetch_prices.py" }
```

### Parallel Execution

Run independent tasks simultaneously:

```toml
check = {
    parallel = [
        "python3 scripts/validate_data.py",
        "echo 'Checking permissions...'",
        "echo 'Checking structure...'"
    ]
}
```

---

## 📊 Sample Output

### Running the Pipeline

```bash
$ taskx pipeline

→ Running: fetch
Fetching prices for 5 cryptocurrencies...
  → Fetching BTC...
    ✓ BTC: $43,250.00
  → Fetching ETH...
    ✓ ETH: $2,315.50
  → Fetching SOL...
    ✓ SOL: $98.75
  → Fetching ADA...
    ✓ ADA: $0.52
  → Fetching DOT...
    ✓ DOT: $7.23

✓ Saved 5 prices to data/raw_prices.json
✓ Completed: fetch (2.1s)

→ Running: validate
Validating cryptocurrency data...
✓ Validation passed!
  → 5 entries validated
  → All required fields present
  → All prices are positive values
✓ Completed: validate (0.3s)

→ Running: analyze
Analyzing cryptocurrency data...
  → Loaded 5 cryptocurrency prices

  Analysis Results:
  ─────────────────────────────────────────
  Total cryptocurrencies: 5
  Total market value: $45,671.00
  Average price: $9,134.20
  Highest: BTC ($43,250.00)
  Lowest: ADA ($0.52)

✓ Analysis saved to data/analysis.json
✓ Completed: analyze (0.5s)

→ Running: report
Generating cryptocurrency report...
✓ Report generated: /path/to/reports/crypto_report.html
✓ Completed: report (0.2s)

✓ Complete pipeline executed successfully!
✓ Completed: pipeline (3.1s)
```

---

## 💡 Real-World Use Cases

This pattern works for many scenarios:

### Data Processing
- ETL pipelines
- Data validation and cleaning
- Report generation
- Scheduled data collection

### Web Development
- Build and deployment
- Asset compilation
- Database migrations
- Testing pipelines

### Machine Learning
- Data preparation
- Model training
- Evaluation and validation
- Deployment automation

### DevOps
- Multi-stage deployments
- Health checks
- Backup automation
- Log aggregation

---

## 🎓 Learn More

- **taskx Documentation**: [GitHub](https://github.com/0xV8/taskx)
- **Install taskx**: `pip install taskx`

---

## 📝 License

This example is provided as-is for educational purposes.

Powered by **taskx** - Modern Python Task Runner
