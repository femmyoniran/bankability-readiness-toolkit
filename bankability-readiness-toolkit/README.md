# Bankability Assessment Toolkit

A financial analysis tool for evaluating the bankability readiness of energy infrastructure projects. The toolkit generates composite bankability scores integrating techno-economic parameters, credit risk indicators, and financing structure templates compatible with USDA RUS Form 201 and DOE LPO Title XVII requirements.

## Overview

The Bankability Assessment Toolkit provides energy project developers, utilities, cooperatives, and financial advisors with a structured framework for evaluating whether a proposed energy infrastructure project meets the commercialization and credit thresholds required by institutional lenders and federal lending programs.

### Capabilities

- **Composite Bankability Scoring** - Weighted assessment across five dimensions: Technology (20%), Financial (25%), Credit (20%), Structure (20%), Market (15%)
- **Pro Forma Financial Modeling** - Multi-year cash flow projections with NPV, IRR, LCOE, DSCR, debt yield, and equity multiple calculations
- **Credit Risk Analysis** - Probability of default estimation, loss given default, expected loss, equivalent credit rating derivation
- **Sensitivity Analysis** - One-factor-at-a-time analysis across revenue, operating costs, capital costs, interest rate, and capacity factor
- **Financing Structure Recommendations** - Six financing templates (project finance, utility corporate, RUS direct/guaranteed, DOE LPO, tax equity, municipal bond) with fit scoring and indicative term sheets
- **USDA RUS Form 201 Generator** - Pre-populated draft application data for the Electric Loan and Loan Guarantee Program
- **DOE LPO Title XVII Generator** - Pre-populated Part I (pre-application) and Part II (full application) data for Innovative Clean Energy loan guarantees

### Supported Technologies

Solar PV (utility and distributed), Concentrated Solar Power, Onshore Wind, Offshore Wind, Battery Storage, Natural Gas (combined cycle and combustion turbine), Nuclear (conventional and SMR), Hydroelectric, Geothermal, Biomass, Coal IGCC, and Transmission.

## Project Structure

```
bankability-readiness-toolkit/
    run.py                      # Application entry point
    config.py                   # Configuration (scoring weights, financial defaults)
    requirements.txt            # Python dependencies
    app/
        __init__.py             # Flask application factory
        models/
            project.py          # Data models (dataclasses)
            financial.py        # Financial model (pro forma, IRR, NPV, LCOE)
            credit_risk.py      # Credit risk model (PD, LGD, EL, rating)
            scoring.py          # Bankability scoring engine
        analysis/
            techno_economic.py  # Technology benchmarking
            bankability_score.py # Assessment convenience function
            sensitivity.py      # Sensitivity analysis
            cash_flow.py        # Cash flow waterfall and amortization
        financing/
            structures.py       # Financing structure templates and term sheets
            rus_form_201.py     # USDA RUS Form 201 data generator
            doe_lpo_title_xvii.py # DOE LPO Title XVII application generator
        routes/
            main_routes.py      # Landing page and about
            project_routes.py   # Project input and sample projects
            analysis_routes.py  # Assessment results and financing
            report_routes.py    # Reports, RUS/LPO views, JSON export
        utils/
            calculations.py     # Financial utility functions
            validators.py       # Input validation
            export.py           # JSON/CSV export
        templates/              # Jinja2 HTML templates
        static/
            css/style.css       # Application stylesheet
            js/main.js          # General JavaScript
            js/charts.js        # Chart.js chart rendering
            js/forms.js         # Form helpers
    data/
        templates/              # Form templates (RUS 201, DOE LPO)
        reference/              # Industry benchmarks and defaults
    tests/
        test_scoring.py         # Scoring engine tests
        test_financial.py       # Financial model tests
        test_credit_risk.py     # Credit risk model tests
```

## Installation

### Prerequisites

- Python 3.9 or higher

### Setup

1. Clone or extract the project:
   ```
   cd bankability-readiness-toolkit
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the application:
   ```
   python run.py
   ```

6. Open a browser to `http://127.0.0.1:5000`

## Usage

### Quick Start with Sample Projects

The toolkit includes three pre-built sample projects for immediate demonstration:

1. **100 MW Solar PV** - Kansas cooperative, $105M total investment, RUS-eligible
2. **150 MW Onshore Wind** - Oklahoma IPP, $225M total investment, PTC-eligible
3. **50 MW Battery Storage** - Arizona municipal utility, $65M total investment, ITC-eligible

Click "Load & Assess" on any sample project from the homepage to run the full analysis pipeline.

### Custom Project Assessment

1. Navigate to "New Assessment" from the top navigation
2. Complete the multi-section input form covering:
   - Project Information (name, location, technology)
   - Technical Parameters (capacity, capacity factor, degradation, availability)
   - Financial Parameters (total cost, leverage, interest rate, tenor, tax credits, pricing)
   - Credit and Offtake (contract type, counterparty rating, entity type, construction risk)
   - Project Structure (development stage, permitting, interconnection, EPC contract)
   - Market and Resource (wholesale prices, resource quality, regulatory environment)
3. Submit the form to receive the full bankability assessment

### Understanding Results

**Overall Bankability Score** (0-100):
| Score Range | Grade | Interpretation |
|-------------|-------|---------------|
| 80-100 | Investment Grade | Project likely financeable on favorable terms |
| 65-79 | Near Investment Grade | Addressable gaps; competitive financing achievable |
| 50-64 | Sub-Investment Grade | Material weaknesses requiring remediation |
| 35-49 | Speculative | Significant barriers to conventional financing |
| 0-34 | Pre-Bankable | Fundamental restructuring needed |

### Federal Program Eligibility

The toolkit includes preliminary eligibility screening for two federal lending programs:

- **USDA RUS Electric Program** - Primarily for cooperatives, municipal utilities, and public utility districts serving rural areas. The toolkit generates draft Form 201 data aligned with 7 CFR Part 1710 requirements.

- **DOE Loan Programs Office (Title XVII)** - For projects employing innovative or commercially proven clean energy technologies. The toolkit generates draft Part I and Part II application data aligned with current LPO solicitation requirements.

These outputs are for preliminary assessment only and do not constitute submission-ready applications.

## Running Tests

```
python -m pytest tests/ -v
```

Or with unittest:
```
python -m unittest discover -s tests -v
```

## Configuration

Key configuration parameters are in `config.py`:

- `SCORING_WEIGHTS` - Dimension weights for the composite score
- `FINANCIAL_DEFAULTS` - Default financial assumptions
- `DSCR_THRESHOLDS` - Debt service coverage thresholds by tier
- `RUS_CONFIG` and `LPO_CONFIG` - Federal program configuration

## Technical Notes

- The application uses Flask sessions for state management. No database is required.
- Financial calculations use NumPy for array operations. IRR is computed using Newton-Raphson iteration.
- MACRS depreciation schedules (5-year and 7-year) are built in for tax credit modeling.
- All monetary values are in USD. The tool does not perform currency conversion.
- Chart rendering uses Chart.js 4.4.1 loaded from CDN.


