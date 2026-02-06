# Qonfido Data Analytics Intern Assignment

**Candidate:** Pranay  
**Date:** February 2026  
**Role:** Data Analytics Intern (Financial Data)

---

## 📋 Overview

This project automates the extraction and consolidation of mutual fund portfolio data from Asset Management Company (AMC) websites. The solution is designed to be **generic and scalable** across different AMCs, though currently configured for Axis Mutual Fund.

---

## 🎯 Assignment Objectives Completed

✅ **Data Collection:** Automated navigation to axismf.com statutory disclosures  
✅ **File Download:** Automatic identification and download of December 2025 consolidated portfolio  
✅ **Data Parsing:** Intelligent extraction from multi-sheet Excel files  
✅ **Consolidation:** Structured output in CSV format  
✅ **Generic Schema:** AMC-agnostic data model for portability  
✅ **Automation:** Full workflow automation with fallback options  

---

## 🏗️ Data Model & Schema

### Consolidated Portfolio Schema

The output follows a **normalized, AMC-agnostic structure**:

| Field | Description | Example |
|-------|-------------|---------|
| `amc_name` | Asset Management Company name | "Axis Mutual Fund" |
| `scheme_name` | Mutual fund scheme name | "Axis NIFTY India Consumption ETF" |
| `instrument_name` | Name of the holding/security | "Bharti Airtel Limited" |
| `instrument_type` | Asset class | "Equity", "Debt", "Money Market", "Other" |
| `isin` | International Securities ID (if available) | "INE397D01024" |
| `industry_rating` | Industry sector or credit rating | "Telecom - Services" |
| `quantity` | Number of units held | 6882 |
| `market_value_lakhs` | Market value in lakhs (₹) | 144.91 |
| `percentage_of_portfolio` | % of net assets | 9.95 |
| `reporting_date` | Portfolio reporting date | "2025-12-31" |

### Design Principles

1. **Generic Structure:** Field names are standardized (not AMC-specific)
2. **Extensibility:** Easy to add new fields (e.g., maturity_date, coupon_rate for debt)
3. **Data Quality:** Handles missing values gracefully
4. **Type Safety:** Numeric fields properly typed for analysis

---

## 🔧 Technical Implementation

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 MutualFundPortfolioScraper                  │
├─────────────────────────────────────────────────────────────┤
│ 1. Web Navigation        → Find portfolio file URL         │
│ 2. File Download         → Download Excel file             │
│ 3. Excel Parsing         → Extract from multiple sheets    │
│ 4. Data Consolidation    → Merge all holdings              │
│ 5. CSV Export            → Generate structured output      │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **Web Scraping Module**
- Uses `requests` + `BeautifulSoup` for HTML parsing
- Intelligent URL pattern matching for file identification
- Handles relative/absolute URLs properly
- User-agent spoofing to avoid bot detection

#### 2. **Excel Parser**
- Identifies scheme sheets (excludes index/summary sheets)
- Dynamically finds header rows (adapts to different formats)
- Detects section headers (Equity/Debt/Money Market)
- Extracts holdings with flexible column mapping

#### 3. **Data Extraction Logic**
- **Adaptive Column Detection:** Matches columns by keywords (e.g., "name", "isin", "quantity")
- **Section Classification:** Automatically categorizes Equity, Debt, Money Market instruments
- **Data Validation:** Filters out total/subtotal rows
- **Date Extraction:** Finds reporting date from sheet metadata

#### 4. **Output Generation**
- Primary consolidated CSV with all holdings
- Optional: Separate CSVs by instrument type (Equity, Debt, etc.)
- Summary statistics for validation

---

## 🚀 Automation Approach

### Workflow

```python
START
  ↓
[Navigate to statutory disclosures page]
  ↓
[Search for "Monthly Scheme Portfolios" section]
  ↓
[Identify December 2025 Consolidated file]
  ↓
[Download Excel file]
  ↓
[Parse all scheme sheets]
  ↓
[Extract holdings → Consolidate]
  ↓
[Export to CSV]
  ↓
END
```

### Automation Features

1. **Automatic File Discovery**
   - Pattern matching for "December 2025 Consolidated"
   - Searches all links on statutory disclosures page
   - Handles both direct links and JavaScript-based downloads

2. **Fallback Mechanism**
   - If auto-download fails, provides manual instructions
   - Can accept manually downloaded files via `manual_file_path` parameter

3. **Intelligent Parsing**
   - No hardcoded sheet names or column positions
   - Adapts to varying Excel formats across AMCs
   - Handles merged cells and complex layouts

4. **Error Handling**
   - Graceful failures with informative messages
   - Continues processing even if some sheets fail
   - Logs warnings for skipped data

---

## 📦 Dependencies

```
python >= 3.8
requests >= 2.25.0
beautifulsoup4 >= 4.9.0
pandas >= 1.3.0
openpyxl >= 3.0.0
```

Install via:
```bash
pip install requests beautifulsoup4 pandas openpyxl
```

---

## 💻 How to Run

### Option 1: Automatic Download (Full Automation)

```bash
python qonfido_mf_automation.py
```

The script will:
1. Navigate to axismf.com
2. Find the December 2025 file
3. Download it automatically
4. Parse and generate CSV

### Option 2: With Manual Download

```bash
# Download file manually from axismf.com
# Save as 'portfolio.xlsx' in the same directory

python qonfido_mf_automation.py
```

### Option 3: Python API

```python
from qonfido_mf_automation import MutualFundPortfolioScraper

# Initialize scraper
scraper = MutualFundPortfolioScraper(amc_name="Axis Mutual Fund")

# Run with manual file
output = scraper.run_full_automation(
    manual_file_path="path/to/downloaded/file.xlsx"
)

# Or let it auto-download
output = scraper.run_full_automation()
```

---

## 📁 Output Files

After execution, you'll find:

```
output/
├── consolidated_portfolio.csv          # All holdings consolidated
├── portfolio_equity.csv                # Equity holdings only
├── portfolio_debt.csv                  # Debt holdings only
└── portfolio_money_market.csv          # Money market instruments
```

---

## 🧪 Testing & Validation

### Data Quality Checks

1. **Scheme Coverage:** Verify all scheme sheets are processed
2. **Row Count:** Compare with original Excel row counts
3. **Sum Validation:** Check if % of portfolio sums to ~100% per scheme
4. **ISIN Validation:** Ensure ISINs follow proper format (12 characters)

### Sample Test

```python
import pandas as pd

# Load output
df = pd.read_csv('output/consolidated_portfolio.csv')

# Validation checks
print(f"Total schemes: {df['scheme_name'].nunique()}")
print(f"Total holdings: {len(df)}")
print(f"Missing ISINs: {df['isin'].isna().sum()}")

# Check portfolio % sum per scheme
portfolio_sums = df.groupby('scheme_name')['percentage_of_portfolio'].sum()
print(f"Portfolio % range: {portfolio_sums.min():.2f}% - {portfolio_sums.max():.2f}%")
```

---

## 🔄 Extending to Other AMCs

To adapt this for other AMCs (HDFC, ICICI, SBI, etc.):

1. **Update base URL:**
```python
scraper = MutualFundPortfolioScraper(amc_name="HDFC Mutual Fund")
scraper.base_url = "https://www.hdfcfund.com"
scraper.statutory_url = f"{scraper.base_url}/investor-resources/statutory-disclosures"
```

2. **Adjust search patterns** if file naming conventions differ:
```python
search_patterns = [
    f"portfolio.*{month}.*{year}",  # Add AMC-specific patterns
]
```

3. **Test parsing logic** - The parser is designed to be flexible, but verify with sample files

---

## 🎯 Key Assumptions

1. **File Format:** Excel (.xlsx or .xls) with multiple sheets
2. **Sheet Structure:** 
   - One sheet per mutual fund scheme
   - Header row contains keywords: "name", "ISIN", "quantity", etc.
   - Section headers separate Equity/Debt/Money Market
3. **Date Format:** Reporting date is December 31, 2025
4. **Currency:** All values in Indian Rupees (₹ lakhs)
5. **Network Access:** Script assumes open internet access to AMC website

---

## 🐛 Known Limitations & Future Enhancements

### Current Limitations

1. **JavaScript-Heavy Sites:** Some AMCs use JavaScript dropdowns that require Selenium
2. **CAPTCHA:** Cannot handle CAPTCHA-protected downloads
3. **Authentication:** Does not support login-based portals
4. **PDF Parsing:** Currently only handles Excel files

### Planned Enhancements

1. ✨ Add Selenium support for JavaScript-heavy pages
2. ✨ Implement OCR for PDF portfolio statements
3. ✨ Add historical data tracking (compare month-over-month changes)
4. ✨ Build database backend (PostgreSQL/SQLite) for persistent storage
5. ✨ Create data quality dashboard with Plotly/Streamlit
6. ✨ Add scheduler for monthly automatic runs (cron/Airflow)

---

## 📊 Sample Output Preview

```csv
amc_name,scheme_name,instrument_name,instrument_type,isin,industry_rating,quantity,market_value_lakhs,percentage_of_portfolio,reporting_date
Axis Mutual Fund,Axis NIFTY India Consumption ETF,Bharti Airtel Limited,Equity,INE397D01024,Telecom - Services,6882,144.91,9.95,2025-12-31
Axis Mutual Fund,Axis NIFTY India Consumption ETF,ITC Limited,Equity,INE154A01025,Diversified FMCG,35851,144.48,9.92,2025-12-31
Axis Mutual Fund,Axis NIFTY India Consumption ETF,Mahindra & Mahindra Limited,Equity,INE101A01026,Automobiles,3719,137.95,9.47,2025-12-31
...
```

---

## 🤝 Contact & Feedback

For any questions or clarifications:

**Email:** nikhil@qonfido.com  
**Subject:** Data Analytics Intern Assignment – Pranay

---

## 📝 License & Usage

This code is submitted as part of the Qonfido Data Analytics Intern assignment and is for evaluation purposes only.

---

**Submission Date:** February 7, 2026  
**Developed by:** Pranay  
**Assignment:** Qonfido Data Analytics Intern Take-Home Challenge
