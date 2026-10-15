# Sprints Talent Analytics
### Data Analytics | Learner Performance | Employer Skill Intelligence

An end-to-end data analytics project that transforms learner cohort data and employer job requirements into actionable insights through data cleaning, exploratory data analysis, feature engineering, interactive visualizations, and a dynamic HTML dashboard.

The project aims to provide a clearer understanding of learner performance, cohort distributions, assessment outcomes, and the skills most frequently requested by employers.

---

## Project Overview

Sprints Talent Analytics combines learner performance data with employer requirements to explore educational outcomes and workforce skill demand.

The project implements a Python-based analytics workflow that preserves the original learner dataset, identifies data quality issues, derives meaningful learner-level features, analyzes employer requirements, and presents findings through interactive visualizations and an HTML dashboard.

### Key Objectives

- Inspect and validate learner cohort data.
- Identify duplicate records, missing values, and invalid engagement scores.
- Clean and prepare data for reliable analysis.
- Perform exploratory data analysis (EDA).
- Engineer meaningful learner-level features.
- Analyze employer requirements across job roles, industries, and company tiers.
- Identify frequently requested technical skills.
- Generate interactive Plotly visualizations.
- Build an interactive HTML dashboard.
- Produce an analytical report and a partner kickoff presentation.

---

## Key Results

| Metric | Result |
|---|---:|
| Original learner records | 26 |
| Learner records after cleaning | 24 |
| Exact duplicate rows removed | 2 |
| Learner dataset columns | 18 |
| Engineered learner features | 5 |
| Total employer role records | 50 |
| Unique employer-required skills | 60 |
| Interactive visualizations generated | 8 |
| Dashboard | Interactive HTML |
| Presentation | 9 slides |

### Highlights

- Preserved the original learner CSV while producing separate cleaned and engineered datasets.
- Corrected a malformed CSV row during the data inspection and repair workflow without discarding a learner record.
- Removed exact duplicate rows from the cleaned dataset.
- Identified and handled engagement scores outside the assumed valid range of 0–100.
- Analyzed assessment performance, engagement, cohort distributions, and graduation data.
- Extracted five additional learner-level features.
- Identified Python as a requirement across all 50 employer roles.
- Generated eight interactive charts and an HTML dashboard with track and cohort filters.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language and analytics workflow |
| Pandas | Data cleaning, manipulation, and analysis |
| NumPy | Numerical computation |
| Plotly | Interactive data visualization |
| HTML | Dashboard and standalone chart presentation |
| JSON | Employer requirements and analytical reports |
| CSV | Learner datasets and processed outputs |
| PowerPoint | Partner kickoff presentation |

The analytical workflow is implemented in Python using the project's core data analysis libraries. Interactive visualizations are delivered as HTML files.

---

## Project Structure

```text
sprints-talent-analytics/
│
├── dashboard/
│   └── index.html
│
├── data/
│   ├── employer_partner_requirements.json
│   ├── sprints_cohort_data_2023.csv
│   ├── sprints_cohort_clean.csv
│   └── sprints_cohort_features.csv
│
├── docs/
│
├── notebooks/
│
├── presentation/
│   └── Sprints_Talent_Analytics_Partner_Kickoff.pptx
│
├── reports/
│   ├── figures/
│   │   ├── 01_track_distribution.html
│   │   ├── 02_cohort_distribution.html
│   │   ├── 03_assessment_scores.html
│   │   ├── 04_average_score_distribution.html
│   │   ├── 05_engagement_vs_capstone.html
│   │   ├── 06_score_vs_module_completeness.html
│   │   ├── 07_company_tier_distribution.html
│   │   └── 08_top_employer_skills.html
│   │
│   ├── analytical_report.html
│   ├── cleaning_report.json
│   ├── eda_summary.json
│   ├── employer_requirements_summary.json
│   ├── feature_engineering_readiness.json
│   └── feature_engineering_report.json
│
├── src/
│   ├── analyze_employer_requirements.py
│   ├── clean_data.py
│   ├── create_dashboard.py
│   ├── data_quality_report.py
│   ├── duplicate_analysis.py
│   ├── eda.py
│   ├── feature_engineering.py
│   ├── inspect_data.py
│   ├── inspect_feature_requirements.py
│   ├── test_csv_repair.py
│   └── visualize_data.py
│
├── tests/
│   ├── test_data_validation.py
│   └── test_reports.py
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Data Sources

The project uses two primary datasets.

### 1. Learner Cohort Dataset

The learner dataset contains information about learners, including:

- Learner identifiers.
- Cohort identifiers.
- Enrollment and graduation dates.
- Demographic groups.
- Learning tracks.
- Engagement scores.
- Module assessment scores.
- Capstone assessment scores.

**Original file:** `data/sprints_cohort_data_2023.csv`

### 2. Employer Requirements Dataset

The employer requirements dataset contains job-related information, including:

- Role identifiers.
- Job titles.
- Industries.
- Company tiers.
- Required skills.
- Minimum assessment thresholds.
- Priority weights.

**Source file:** `data/employer_partner_requirements.json`

---

## Data Processing Pipeline

The project follows a structured workflow from raw data inspection to analytical outputs.

### 1. Data Inspection and Validation

The inspection workflow examines the learner dataset's structure, identifies malformed CSV rows, checks duplicate records, detects missing values, and validates score ranges.

A malformed row containing an extra trailing field was repaired during the CSV loading workflow. The original CSV was preserved.

### 2. Data Cleaning

The cleaning pipeline:

- Removes exact duplicate rows.
- Converts score fields into numeric values.
- Parses enrollment and graduation dates.
- Treats engagement scores outside the assumed 0–100 range as invalid.
- Preserves missing values rather than automatically replacing them with zero.
- Generates a separate cleaned dataset.
- Produces a JSON cleaning report.

**Output:** `data/sprints_cohort_clean.csv`

### 3. Exploratory Data Analysis

The EDA workflow examines:

- Dataset dimensions and data types.
- Cohort distribution.
- Learning track distribution.
- Assessment score statistics.
- Engagement score statistics.
- Engagement and capstone score correlation.
- Module assessment averages.
- Graduation date availability.
- Missing values by column.

**Output:** `reports/eda_summary.json`

### 4. Employer Requirements Analysis

The employer analysis workflow evaluates job roles, required skills, industries, company tiers, assessment thresholds, and priority weights.

It also checks role identifier uniqueness, required field completeness, and skill list validity.

**Output:** `reports/employer_requirements_summary.json`

### 5. Feature Engineering

Five learner-level features are derived from the available data.

| Feature | Description |
|---|---|
| `average_module_score` | Mean of the available module assessment scores |
| `module_score_count` | Number of non-missing module assessment scores |
| `module_score_std` | Standard deviation of the available module assessment scores |
| `enrollment_year` | Year extracted from the enrollment date |
| `days_to_graduation` | Number of days between enrollment and graduation |

Missing assessment scores are not interpreted as zero. Graduation duration is calculated only when both required dates are available.

**Output:** `data/sprints_cohort_features.csv`

### 6. Data Visualization

Eight interactive Plotly charts are generated:

1. Track distribution.
2. Cohort distribution.
3. Assessment scores.
4. Average score distribution.
5. Engagement versus capstone score.
6. Score versus module completeness.
7. Company tier distribution.
8. Top employer-required skills.

**Output directory:** `reports/figures/`

Each chart is saved as a standalone HTML file.

### 7. Interactive Dashboard

The HTML dashboard provides a centralized interface for exploring learner performance and employer requirements.

Its features include:

- Key performance indicators.
- Track and cohort filters.
- Interactive performance charts.
- Employer skill analysis.
- A learner-level data table.

**Dashboard file:** `dashboard/index.html`

Open this file in a web browser to explore the dashboard.

### 8. Reporting and Presentation

The project includes an analytical report and a partner kickoff presentation.

- **Analytical report:** `reports/analytical_report.html`
- **Partner kickoff presentation:** `presentation/Sprints_Talent_Analytics_Partner_Kickoff.pptx`

The report summarizes the analysis, data quality findings, engineered features, employer requirements, and recommendations. The presentation communicates the project's objectives, workflow, findings, and next steps.

---

## Employer Skill Insights

The employer requirements analysis identified 60 unique skills across 50 job roles.

### Most Frequently Requested Skills

| Rank | Skill | Number of Roles |
|---:|---|---:|
| 1 | Python | 50 |
| 2 | Pandas | 20 |
| 3 | SQL | 19 |
| 4 | Data Visualization | 9 |
| 5 | Machine Learning | 9 |
| 6 | NumPy | 8 |
| 7 | Statistics | 6 |
| 8 | Matplotlib | 4 |
| 9 | Plotly | 4 |
| 10 | Tableau | 4 |

Python appears in all 50 employer role records, making it the most frequently requested skill in the analyzed dataset.

These frequencies describe the supplied employer requirements dataset and should not be interpreted as universal labor market statistics.

---

## Learner Performance Insights

The cleaned learner dataset contains 24 records.

### Learning Track Distribution

| Learning Track | Learners |
|---|---:|
| Advanced Data Analysis | 13 |
| AI & Machine Learning | 6 |
| Full Stack Web Development | 5 |
| **Total** | **24** |

### Assessment and Engagement Findings

- The mean capstone score is 86.05.
- The mean engagement score is 73.95, calculated from 19 valid observations.
- There are 21 available capstone scores.
- Graduation dates are available for 22 learners.
- Five engagement values are missing after cleaning, including the originally missing value and four invalid values.

The analysis found a correlation of 0.992 between engagement and capstone scores across 16 valid pairs.

This is a very strong positive correlation in the available sample. However, the dataset is small, and correlation does not establish causation. The result should be interpreted as an initial analytical observation rather than proof that engagement causes higher capstone scores.

---

## Installation and Setup

### Requirements

- Python 3.10 or a compatible Python version.
- pip.
- A terminal such as PowerShell.
- A web browser for opening the HTML dashboard and visualizations.

### 1. Clone the Repository

After publishing the repository on GitHub, clone it:

```powershell
git clone <YOUR_REPOSITORY_URL>
cd sprints-talent-analytics
```

Replace `<YOUR_REPOSITORY_URL>` with the actual URL of your GitHub repository.

### 2. Create a Virtual Environment

```powershell
python -m venv .venv
```

### 3. Activate the Virtual Environment

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

---

## Running the Project

Run commands from the project root directory with the virtual environment activated.

### Inspect the Original Data

```powershell
python .\src\inspect_data.py
```

### Generate a Data Quality Report

```powershell
python .\src\data_quality_report.py
```

### Run the Cleaning Pipeline

```powershell
python .\src\clean_data.py
```

### Perform Exploratory Data Analysis

```powershell
python .\src\eda.py
```

### Analyze Employer Requirements

```powershell
python .\src\analyze_employer_requirements.py
```

### Inspect Feature Engineering Readiness

```powershell
python .\src\inspect_feature_requirements.py
```

### Generate Engineered Features

```powershell
python .\src\feature_engineering.py
```

### Generate Interactive Visualizations

```powershell
python .\src\visualize_data.py
```

### Generate the Dashboard

```powershell
python .\src\create_dashboard.py
```

### Open the Dashboard

Open `dashboard/index.html` in your browser.

The standalone visualization files are available in `reports/figures/`.

**Note:** Run the cleaning pipeline before the downstream analysis scripts when rebuilding outputs from the original learner dataset. The dashboard and reports depend on the corresponding generated data and output files.

---

## Data Quality and Analytical Limitations

The findings should be interpreted in the context of the source data and the project's assumptions.

- The cleaned learner dataset contains 24 records, which is a relatively small sample.
- Some module assessment scores are missing.
- Some graduation dates are unavailable.
- Four engagement values were outside the assumed valid range of 0–100 and were treated as missing.
- The 0–100 engagement range is an analytical assumption and should be confirmed against the original data specification when available.
- The engagement and capstone correlation is based on 16 valid pairs and does not establish causation.
- Module scores are not directly mapped to specific technical skills because the available data does not establish a validated relationship between those scores and individual skills.
- Employer skill frequencies reflect the supplied 50-role dataset, not the entire labor market.
- The dashboard's conclusions depend on the quality and completeness of the underlying datasets.

---

## Project Deliverables

The project produces the following deliverables:

- Original learner dataset.
- Cleaned learner dataset.
- Engineered learner dataset.
- Data inspection and cleaning scripts.
- Exploratory data analysis report.
- Employer requirements analysis report.
- Feature engineering readiness and output reports.
- Eight standalone interactive Plotly visualizations.
- Interactive HTML dashboard.
- Analytical report.
- Nine-slide partner kickoff presentation.
- Dependency specification in `requirements.txt`.

---

## Future Improvements

Potential improvements include:

- Expanding the learner dataset to support more robust analysis.
- Validating score ranges against authoritative dataset documentation.
- Investigating missing data patterns in greater depth.
- Adding automated tests for data cleaning and analytical outputs.
- Establishing a validated mapping between learner assessments and employer-required skills if suitable data becomes available.
- Improving the dashboard with additional validated analytical views.
- Adding a reproducible end-to-end execution workflow.

---

## Author

Developed as a data analytics capstone project focused on learner performance, employer skill demand, and interactive reporting.

---

## Acknowledgments

This project uses Python's data analysis and visualization ecosystem, including Pandas, NumPy, and Plotly.

---

**Sprints Talent Analytics — Turning learner and employer data into actionable insights.**