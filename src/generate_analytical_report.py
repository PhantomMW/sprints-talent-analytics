"""
Sprints Talent Analytics
Professional Analytical Report Generator

Creates a polished HTML report designed for browser viewing and A4 PDF printing.
Inputs are the project's existing processed datasets and saved JSON reports.
The script does not modify source datasets.
"""

from pathlib import Path
from datetime import datetime
import html
import json
import sys

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

CLEAN_DATA_PATH = DATA_DIR / "sprints_cohort_clean.csv"
FEATURES_DATA_PATH = DATA_DIR / "sprints_cohort_features.csv"
EMPLOYER_DATA_PATH = DATA_DIR / "employer_partner_requirements.json"
OUTPUT_PATH = REPORTS_DIR / "analytical_report.html"
REPORT_BUILD_ID = "FINAL-FEATURE-TABLE-FIX-20261015"

REPORT_PATHS = {
    "cleaning": REPORTS_DIR / "cleaning_report.json",
    "eda": REPORTS_DIR / "eda_summary.json",
    "employer": REPORTS_DIR / "employer_requirements_summary.json",
    "readiness": REPORTS_DIR / "feature_engineering_readiness.json",
    "features": REPORTS_DIR / "feature_engineering_report.json",
}

NAVY = "#102A43"
BLUE = "#176B87"
TEAL = "#239B91"
TEXT = "#243B53"
MUTED = "#627D98"
BORDER = "#D9E2EC"


def esc(value):
    """Escape text before inserting it into HTML."""
    if value is None:
        return "N/A"
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return "N/A"
    return html.escape(str(value))


def fmt(value, decimals=2):
    """Format numeric values consistently."""
    try:
        number = float(value)
        if not np.isfinite(number):
            return "N/A"
        if number.is_integer():
            return f"{int(number):,}"
        return f"{number:,.{decimals}f}"
    except (TypeError, ValueError):
        return esc(value)


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path.name}")
    return value


def flatten_dict(data, prefix=""):
    """Flatten nested JSON dictionaries without losing their meaning."""
    result = []
    if not isinstance(data, dict):
        return result
    for key, value in data.items():
        label = f"{prefix} / {key}" if prefix else str(key)
        if isinstance(value, dict):
            result.extend(flatten_dict(value, label))
        elif isinstance(value, list):
            result.append((label, ", ".join(map(str, value))))
        else:
            result.append((label, value))
    return result


def html_table(headers, rows, empty_message="No data available."):
    if not rows:
        return f'<div class="empty">{esc(empty_message)}</div>'
    head = "".join(f"<th>{esc(item)}</th>" for item in headers)
    body = []
    for row in rows:
        cells = "".join(f"<td>{esc(value)}</td>" for value in row)
        body.append(f"<tr>{cells}</tr>")
    return (
        '<div class="table-wrap"><table><thead><tr>'
        + head
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def metric_card(label, value, detail, color="blue"):
    return f"""
    <article class="metric {color}">
      <div class="metric-label">{esc(label)}</div>
      <div class="metric-value">{esc(value)}</div>
      <div class="metric-detail">{esc(detail)}</div>
    </article>
    """


def section(title, subtitle, content, section_id):
    return f"""
    <section class="report-section" id="{esc(section_id)}">
      <div class="section-title">
        <span class="section-accent"></span>
        <div>
          <h2>{esc(title)}</h2>
          <p>{esc(subtitle)}</p>
        </div>
      </div>
      {content}
    </section>
    """


def callout(title, message, kind="info"):
    return f"""
    <aside class="callout {esc(kind)}">
      <strong>{esc(title)}</strong>
      <p>{esc(message)}</p>
    </aside>
    """


def load_project():
    print("\n[1/5] Loading saved analysis reports...")
    reports = {}
    for name, path in REPORT_PATHS.items():
        print(f"      Loading: {path.name}")
        reports[name] = load_json(path)

    print("\n[2/5] Loading processed datasets...")
    for path in (CLEAN_DATA_PATH, FEATURES_DATA_PATH, EMPLOYER_DATA_PATH):
        if not path.exists():
            raise FileNotFoundError(f"Required dataset not found: {path}")

    learners = pd.read_csv(CLEAN_DATA_PATH)
    features = pd.read_csv(FEATURES_DATA_PATH)
    with EMPLOYER_DATA_PATH.open("r", encoding="utf-8") as file:
        employer_json = json.load(file)

    roles = employer_json.get("employer_requirements", [])
    employers = pd.DataFrame(roles)

    if learners.empty or features.empty or employers.empty:
        raise ValueError("One or more required datasets are empty.")

    for column in ("learner_id", "track_name", "cohort_id"):
        if column not in learners.columns:
            raise ValueError(f"Required learner column is missing: {column}")

    print(f"      Learner records: {len(learners)}")
    print(f"      Feature records: {len(features)}")
    print(f"      Employer roles: {len(employers)}")
    return reports, learners, features, employers


def build_executive(learners, features, employers):
    skills = set()
    if "required_skills" in employers.columns:
        for item in employers["required_skills"]:
            if isinstance(item, list):
                skills.update(str(skill).strip() for skill in item if str(skill).strip())

    cards = [
        metric_card("Learner Records", fmt(len(learners)), "Cleaned learner rows", "blue"),
        metric_card("Training Tracks", fmt(learners["track_name"].nunique()), "Distinct tracks", "teal"),
        metric_card("Cohorts", fmt(learners["cohort_id"].nunique()), "Distinct cohorts", "navy"),
        metric_card("Employer Roles", fmt(len(employers)), "Role records analyzed", "blue"),
        metric_card("Distinct Skills", fmt(len(skills)), "Skills listed across roles", "teal"),
        metric_card("Feature Columns", fmt(len(features.columns)), "Engineered dataset columns", "navy"),
    ]
    return """
      <div class="executive-note">
        <span class="eyebrow">PROJECT OVERVIEW</span>
        <p>This report summarizes learner performance, data quality, engineered
        features, and employer skill requirements. The analysis is descriptive
        and exploratory; results should be interpreted within the documented
        sample size, missing values, and skill-mapping limitations.</p>
      </div>
      <div class="metrics-grid">""" + "".join(cards) + "</div>"


def build_dataset_overview(learners, features, employers):
    inventory = [
        ("Clean learner dataset", CLEAN_DATA_PATH.name),
        ("Learner records", len(learners)),
        ("Learner columns", len(learners.columns)),
        ("Feature dataset", FEATURES_DATA_PATH.name),
        ("Feature records", len(features)),
        ("Feature columns", len(features.columns)),
        ("Employer roles", len(employers)),
        ("Unique learner IDs", learners["learner_id"].nunique()),
    ]
    tracks = learners["track_name"].value_counts(dropna=False)
    cohorts = learners["cohort_id"].value_counts(dropna=False).sort_index()
    return f"""
      <div class="two-col">
        <div><h3>Dataset Inventory</h3>
          {html_table(["Property", "Value"], inventory)}
        </div>
        <div><h3>Learners by Training Track</h3>
          {html_table(["Training Track", "Learners"], list(tracks.items()))}
        </div>
      </div>
      <h3 class="subheading">Learners by Cohort</h3>
      {html_table(["Cohort", "Learners"], list(cohorts.items()))}
      <p class="small-note">Learner records and employer role records are analyzed
      independently. The report does not assume that each learner corresponds
      to a particular employer role.</p>
    """


def build_cleaning(report, learners):
    rows = [(key, value) for key, value in flatten_dict(report)]
    summary = html_table(["Cleaning Report Field", "Recorded Value"], rows)

    missing_rows = []
    for column in learners.columns:
        count = int(learners[column].isna().sum())
        if count:
            missing_rows.append((column, count, fmt(count / len(learners) * 100)))
    missing = html_table(
        ["Column", "Missing Values", "Missing (%)"],
        missing_rows,
        "No missing values found in the cleaned dataset."
    )
    total_missing = int(learners.isna().sum().sum())
    note = callout(
        "Score range assumption",
        "The engagement score range of 0–100 is provisional and should be "
        "confirmed against the data dictionary or source documentation.",
        "warning"
    )
    missing_note = callout(
        "Missing values are not zero",
        f"The cleaned dataset contains {total_missing} missing cell values. "
        "Missing scores and dates are preserved where imputation has not "
        "been justified.",
        "info"
    )
    return f"""
      <h3>Cleaning Summary</h3>{summary}
      {note}
      <h3 class="subheading">Missing Values by Column</h3>{missing}
      {missing_note}
      <h3 class="subheading">Cleaning Interpretation</h3>
      <p>Exact duplicate rows are removed while retaining one occurrence.
      Numeric conversion, engagement-range checks, date parsing, and structural
      CSV repairs are documented by the cleaning pipeline. The original source
      CSV is not overwritten.</p>
    """


def build_eda(report, learners):
    score_columns = [
        col for col in learners.columns
        if col.endswith("_score") and pd.api.types.is_numeric_dtype(learners[col])
    ]
    rows = []
    for column in score_columns:
        values = pd.to_numeric(learners[column], errors="coerce").dropna()
        rows.append((
            column.replace("_", " ").title(),
            fmt(values.mean()) if len(values) else "N/A",
            fmt(values.median()) if len(values) else "N/A",
            len(values),
        ))
    score_table = html_table(
        ["Assessment", "Mean", "Median", "Available Scores"], rows
    )

    paired_note = ""
    if {"engagement_score", "capstone_score"}.issubset(learners.columns):
        paired = learners[["engagement_score", "capstone_score"]].apply(
            pd.to_numeric, errors="coerce"
        ).dropna()
        if len(paired) >= 2:
            corr = paired["engagement_score"].corr(paired["capstone_score"])
            corr_text = fmt(corr, 3) if pd.notna(corr) else "N/A"
            paired_note = callout(
                "Engagement and Capstone relationship",
                f"The Pearson correlation is {corr_text}, calculated from "
                f"{len(paired)} complete records. Correlation does not establish "
                "causation, and the limited sample restricts generalization.",
                "info"
            )

    return f"""
      <p>Assessment means and medians use available numeric values. The valid
      count is shown for each score so that differences in data coverage remain
      visible.</p>
      <h3>Assessment Score Summary</h3>{score_table}
      {paired_note}
      <h3 class="subheading">Interpretation</h3>
      <p>Differences between module averages are descriptive comparisons.
      Without information about assessment difficulty, grading criteria,
      learner progression, and comparable cohorts, they should not be treated
      as definitive evidence of improvement or decline.</p>
    """


def build_features(feature_report, readiness_report, features):
    derived = feature_report.get("derived_features", {})
    rows = []
    if isinstance(derived, dict):
        for name, details in derived.items():
            if not isinstance(details, dict):
                details = {"description": str(details)}
            rows.append((
                name,
                details.get("description", "N/A"),
                fmt(details["minimum"]) if details.get("minimum") is not None else "—",
                fmt(details["maximum"]) if details.get("maximum") is not None else "—",
                details.get("missing_count", "N/A"),
            ))

    derived_table = html_table(
        ["Feature", "Description", "Minimum", "Maximum", "Missing"],
        rows
    )

    summary_rows = [
        ("Input records", feature_report.get("input_records", "N/A")),
        ("Output records", feature_report.get("output_records", "N/A")),
        ("Input columns", feature_report.get("input_columns", "N/A")),
        ("Output columns", feature_report.get("output_columns", len(features.columns))),
        ("Duplicate rows in output", feature_report.get("duplicate_rows_in_output", "N/A")),
    ]
    summary = html_table(["Validation Check", "Result"], summary_rows)

    missing_map = feature_report.get("missing_values_after_feature_engineering", {})
    missing_rows = []
    if isinstance(missing_map, dict):
        missing_rows = [
            (column, count) for column, count in missing_map.items()
            if isinstance(count, (int, float)) and count > 0
        ]
    missing_table = html_table(
        ["Feature Column", "Missing Values"],
        missing_rows,
        "No missing values were recorded."
    )

    skill_mapping = feature_report.get(
        "skill_mapping_status",
        "Not established: module scores do not directly identify individual skills."
    )
    note = callout(
        "Skill mapping limitation",
        str(skill_mapping) + " Do not infer individual skill proficiency from "
        "general module scores without a validated assessment-to-skill mapping.",
        "warning"
    )

    # Keep readiness information concise instead of dumping nested dictionaries.
    readiness_data = readiness_report.get("learner_data", {})
    potential = readiness_data.get("potential_features", []) if isinstance(readiness_data, dict) else []
    potential_rows = []
    for item in potential:
        if isinstance(item, dict):
            potential_rows.append((
                item.get("feature", "N/A"),
                item.get("description", "N/A"),
                item.get("requires_validation", "N/A"),
            ))
    readiness_table = html_table(
        ["Potential Feature", "Purpose", "Validation Required"],
        potential_rows
    )

    return f"""
      <p>Feature engineering derives additional variables from the cleaned
      learner dataset to support performance analysis and completeness checks.</p>
      <h3>Derived Features</h3>{derived_table}
      <h3 class="subheading">Feature Engineering Summary</h3>{summary}
      <h3 class="subheading">Missing Values in Feature Dataset</h3>{missing_table}
      {note}
      <h3 class="subheading">Feature Readiness Notes</h3>{readiness_table}
    """


def build_employer(employer_report, employers):
    tier_html = ""
    if "company_tier" in employers.columns:
        tier_counts = employers["company_tier"].value_counts(dropna=False).sort_index()
        tier_html = html_table(
            ["Company Tier", "Number of Roles"],
            list(tier_counts.items())
        )

    skill_counts = {}
    if "required_skills" in employers.columns:
        for item in employers["required_skills"]:
            if isinstance(item, list):
                for skill in set(str(s).strip() for s in item if str(s).strip()):
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
    sorted_skills = sorted(skill_counts.items(), key=lambda item: (-item[1], item[0].lower()))
    skill_rows = [(index, skill, count) for index, (skill, count) in enumerate(sorted_skills[:15], 1)]
    skills_table = html_table(["Rank", "Skill", "Number of Roles"], skill_rows)

    threshold_html = ""
    if "minimum_assessment_threshold" in employers.columns:
        thresholds = pd.to_numeric(
            employers["minimum_assessment_threshold"], errors="coerce"
        ).dropna()
        if not thresholds.empty:
            threshold_rows = [
                ("Valid threshold values", len(thresholds)),
                ("Minimum threshold", fmt(thresholds.min())),
                ("Median threshold", fmt(thresholds.median())),
                ("Mean threshold", fmt(thresholds.mean())),
                ("Maximum threshold", fmt(thresholds.max())),
            ]
            threshold_html = html_table(["Threshold Metric", "Value"], threshold_rows)

    report_rows = flatten_dict(employer_report)
    saved_summary = html_table(
        ["Saved Analysis Metric", "Value"],
        [(key, value) for key, value in report_rows]
    )
    return f"""
      <p>Employer requirements are analyzed separately from learner assessment
      results. Skill frequency counts the number of role records listing each skill.</p>
      <div class="two-col">
        <div><h3>Company Tier Distribution</h3>{tier_html}</div>
        <div><h3>Assessment Thresholds</h3>{threshold_html}</div>
      </div>
      <h3 class="subheading">Top 15 Most Requested Skills</h3>{skills_table}
      <p class="small-note">Skill frequency represents the number of role records
      listing a skill. It is not a direct measure of market-wide demand, hiring
      probability, salary impact, or learner proficiency.</p>
      <details class="details">
        <summary>View saved employer analysis details</summary>
        {saved_summary}
      </details>
    """


def build_findings(learners, features, employers):
    findings = [
        (
            "Learner distribution",
            f"The cleaned dataset contains {len(learners)} learner records across "
            f"{learners['track_name'].nunique()} training tracks and "
            f"{learners['cohort_id'].nunique()} cohorts. This describes the "
            "available dataset, not all learners."
        )
    ]

    if "average_module_score" in features.columns:
        values = pd.to_numeric(features["average_module_score"], errors="coerce").dropna()
        if not values.empty:
            findings.append((
                "Assessment performance",
                f"The average module score ranges from {fmt(values.min())} to "
                f"{fmt(values.max())}. These values describe this sample and "
                "are not universal performance benchmarks."
            ))

    skills = {}
    if "required_skills" in employers.columns:
        for item in employers["required_skills"]:
            if isinstance(item, list):
                for skill in set(str(s).strip() for s in item if str(s).strip()):
                    skills[skill] = skills.get(skill, 0) + 1
    if skills:
        top_skill, top_count = sorted(skills.items(), key=lambda x: (-x[1], x[0].lower()))[0]
        findings.append((
            "Most requested skill",
            f"{top_skill} appears in {top_count} employer role records out of "
            f"{len(employers)}. This reflects the provided requirements file."
        ))

    findings.extend([
        (
            "Data completeness",
            "Some assessment scores and graduation dates remain missing. "
            "Comparisons should account for valid observations for each metric."
        ),
        (
            "Skill mapping",
            "Learner module scores are not directly mapped to individual "
            "employer-required skills, so skill-level proficiency cannot be inferred."
        ),
    ])

    cards = []
    for index, (title, text) in enumerate(findings, 1):
        cards.append(f"""
          <article class="info-card">
            <div class="number">{index:02d}</div>
            <div><h3>{esc(title)}</h3><p>{esc(text)}</p></div>
          </article>
        """)
    return "".join(cards)


def build_recommendations():
    items = [
        ("Prioritize data quality",
         "Keep an audit trail for duplicate rows, invalid values, missing assessments, and structural CSV issues."),
        ("Validate score definitions",
         "Confirm the engagement score range and assessment scoring rules with the dataset owner."),
        ("Investigate missing values",
         "Ask why assessment scores and graduation dates are missing. Do not replace missing scores with zero without an approved rule."),
        ("Use employer requirements for curriculum review",
         "Use frequently requested skills to guide curriculum discussions while considering role-specific needs and priority weights."),
        ("Establish a validated skill mapping",
         "Document which assessments measure each skill and the evidence needed to assign proficiency."),
        ("Expand the evidence base",
         "Repeat the analysis on larger cohorts and multiple time periods before making broad claims."),
    ]
    cards = []
    for index, (title, text) in enumerate(items, 1):
        cards.append(f"""
          <article class="info-card recommendation">
            <div class="number teal-number">{index}</div>
            <div><h3>{esc(title)}</h3><p>{esc(text)}</p></div>
          </article>
        """)
    return "".join(cards)


def build_limitations():
    rows = [
        ("Sample size", "The learner sample is limited; subgroup comparisons are exploratory."),
        ("Missing values", "Incomplete assessment records can change the number of observations used in each statistic."),
        ("Score range assumption", "The expected engagement score range should be confirmed with the data owner."),
        ("Skill mapping", "Module scores are not a validated substitute for skill-level assessments."),
        ("Employer coverage", "The employer file represents the roles included in this dataset, not necessarily the entire job market."),
        ("Further validation", "Repeat the analysis with additional cohorts, documented scoring rules, and validated skill mappings."),
    ]
    artifacts = [
        ("Cleaned learner data", "data/sprints_cohort_clean.csv"),
        ("Engineered features", "data/sprints_cohort_features.csv"),
        ("Employer requirements", "data/employer_partner_requirements.json"),
        ("Cleaning report", "reports/cleaning_report.json"),
        ("EDA summary", "reports/eda_summary.json"),
        ("Employer analysis", "reports/employer_requirements_summary.json"),
        ("Feature readiness", "reports/feature_engineering_readiness.json"),
        ("Feature engineering report", "reports/feature_engineering_report.json"),
    ]
    return f"""
      <h3>Limitations and Future Improvements</h3>
      {html_table(["Limitation", "Interpretation"], rows)}
      <h3 class="subheading">Reproducibility: Input Artifacts</h3>
      {html_table(["Artifact", "Project Path"], artifacts)}
      {callout("Reproducibility note",
        "The report is generated from saved JSON analysis reports and processed datasets. "
        "Rerun upstream analysis scripts before regenerating the HTML report.", "info")}
    """


def build_report(reports, learners, features, employers):
    generated = datetime.now().strftime("%d %B %Y, %H:%M")
    sections = [
        section("Executive Summary",
                "A concise overview of the project and its analytical scope.",
                build_executive(learners, features, employers), "executive"),
        section("Dataset Overview",
                "Structure and coverage of the available datasets.",
                build_dataset_overview(learners, features, employers), "overview"),
        section("Data Quality & Cleaning",
                "Cleaning decisions and remaining data-quality considerations.",
                build_cleaning(reports["cleaning"], learners), "cleaning"),
        section("Exploratory Data Analysis",
                "Descriptive statistics and patterns in the learner data.",
                build_eda(reports["eda"], learners), "eda"),
        section("Feature Engineering",
                "Derived features, validation checks, and skill-mapping limitations.",
                build_features(reports["features"], reports["readiness"], features), "features"),
        section("Employer Requirements Analysis",
                "Employer role distribution, thresholds, and requested skills.",
                build_employer(reports["employer"], employers), "employers"),
        section("Key Findings",
                "Evidence-based findings from the current analysis.",
                '<div class="cards-grid">' + build_findings(learners, features, employers) + "</div>",
                "findings"),
        section("Recommendations",
                "Practical next steps to improve data quality and analytical value.",
                '<div class="cards-grid">' + build_recommendations() + "</div>",
                "recommendations"),
        section("Limitations & Reproducibility",
                "Interpretation boundaries and the artifacts used to build this report.",
                build_limitations(), "limitations"),
    ]

    toc = [
        ("Executive Summary", "executive"),
        ("Dataset Overview", "overview"),
        ("Data Quality & Cleaning", "cleaning"),
        ("Exploratory Data Analysis", "eda"),
        ("Feature Engineering", "features"),
        ("Employer Requirements", "employers"),
        ("Key Findings", "findings"),
        ("Recommendations", "recommendations"),
        ("Limitations & Reproducibility", "limitations"),
    ]
    toc_html = "".join(
        f'<a href="#{anchor}"><span>{index:02d}</span>{esc(title)}</a>'
        for index, (title, anchor) in enumerate(toc, 1)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Sprints Talent Analytics analytical report">
<title>Sprints Talent Analytics | Analytical Report</title>
<style>
:root {{
 --navy:{NAVY}; --blue:{BLUE}; --teal:{TEAL}; --text:{TEXT};
 --muted:{MUTED}; --border:{BORDER}; --bg:#F3F6FA; --surface:#FFFFFF;
}}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; scroll-padding-top:20px; }}
body {{ margin:0; background:var(--bg); color:var(--text);
 font:14px/1.7 "Segoe UI",Arial,Helvetica,sans-serif; }}
a {{ color:var(--blue); text-decoration:none; }}
.cover {{ color:#fff; padding:66px 7% 58px; background:
 radial-gradient(circle at 90% 15%,rgba(35,155,145,.45),transparent 32%),
 linear-gradient(125deg,#102A43 0%,#183B56 58%,#176B87 100%); }}
.cover-inner {{ max-width:1180px; margin:auto; }}
.brand {{ display:flex; align-items:center; gap:12px; margin-bottom:42px;
 color:#D7F5F0; font-size:12px; font-weight:800; letter-spacing:2px; }}
.brand-mark {{ display:grid; place-items:center; width:36px; height:36px;
 border:1px solid #7192A6; border-radius:11px; background:#24485E; }}
.eyebrow {{ color:#7FE0D2; font-size:11px; font-weight:900; letter-spacing:2px; }}
.cover h1 {{ margin:10px 0 0; font-size:clamp(36px,5vw,58px);
 letter-spacing:-1.6px; line-height:1.1; }}
.cover-subtitle {{ max-width:740px; color:#D8E7F0; font-size:16px; margin:20px 0 0; }}
.page-container {{ width:min(1180px,calc(100% - 40px)); margin:28px auto 54px; }}
.contents {{ display:grid; grid-template-columns:1fr 2fr; gap:24px; padding:25px;
 background:#fff; border:1px solid var(--border); border-radius:16px; margin-bottom:26px; }}
.contents h2 {{ margin:0 0 6px; color:var(--navy); font-size:19px; }}
.contents p {{ margin:0; color:var(--muted); font-size:12px; }}
.contents-links {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; }}
.contents-links a {{ display:flex; gap:8px; align-items:center; padding:8px;
 background:#F6F9FC; border-radius:8px; color:var(--text); font-size:11px;
 font-weight:700; line-height:1.4; }}
.contents-links span {{ color:var(--teal); font-weight:900; flex-shrink:0; }}
.report-section {{ background:#fff; border:1px solid var(--border); border-radius:16px;
 padding:30px; margin-bottom:25px; scroll-margin-top:18px; }}
.section-title {{ display:flex; gap:14px; align-items:flex-start; margin-bottom:23px; }}
.section-accent {{ flex:0 0 5px; height:43px; border-radius:8px;
 background:linear-gradient(180deg,var(--teal),var(--blue)); }}
.section-title h2 {{ margin:0; color:var(--navy); font-size:24px; line-height:1.3; letter-spacing:-.5px; }}
.section-title p {{ margin:7px 0 0; color:var(--muted); font-size:12px; }}
.executive-note {{ padding:20px 23px; border:1px solid #D5EAE8; border-radius:12px;
 background:linear-gradient(120deg,#F0FAF8,#F5FAFD); margin-bottom:20px; }}
.executive-note p {{ margin:8px 0 0; color:#334E68; }}
.metrics-grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:13px; }}
.metric {{ position:relative; overflow:hidden; min-height:130px; padding:19px;
 border:1px solid var(--border); border-radius:12px; background:#fff; break-inside:avoid; }}
.metric:before {{ content:""; position:absolute; top:0; left:0; height:4px; width:100%; background:var(--blue); }}
.metric.teal:before {{ background:var(--teal); }} .metric.navy:before {{ background:var(--navy); }}
.metric-label {{ color:var(--muted); font-size:10px; font-weight:800; letter-spacing:.6px; text-transform:uppercase; }}
.metric-value {{ margin-top:10px; color:var(--navy); font-size:30px; font-weight:900; line-height:1.2; }}
.metric-detail {{ margin-top:7px; color:var(--muted); font-size:11px; }}
.two-col {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px; align-items:start; }}
h3 {{ color:var(--navy); font-size:15px; line-height:1.45; margin:0 0 12px; }}
.subheading {{ margin-top:25px; }}
.table-wrap {{ width:100%; overflow-x:auto; border:1px solid var(--border); border-radius:10px; }}
table {{ width:100%; border-collapse:collapse; font-size:11px; line-height:1.55; }}
thead {{ display:table-header-group; }}
th {{ padding:11px 12px; background:#EDF4F8; color:var(--navy); text-align:left;
 font-size:10px; font-weight:900; text-transform:uppercase; letter-spacing:.3px; }}
td {{ padding:10px 12px; border-top:1px solid #E9EFF5; color:#334E68;
 vertical-align:top; overflow-wrap:anywhere; }}
tbody tr:nth-child(even) {{ background:#F8FAFC; }}
.callout {{ margin-top:18px; padding:16px 19px; border-left:4px solid var(--blue);
 border-radius:8px; background:#EAF3F8; break-inside:avoid; }}
.callout.warning {{ border-left-color:#B7791F; background:#FFFAF0; }}
.callout.info {{ border-left-color:var(--teal); background:#EFFAF8; }}
.callout strong {{ display:block; color:var(--navy); font-size:12px; }}
.callout p {{ margin:5px 0 0; color:#486581; font-size:11px; }}
.cards-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:13px; }}
.info-card {{ display:flex; gap:13px; padding:17px; border:1px solid var(--border);
 border-radius:11px; break-inside:avoid; page-break-inside:avoid; }}
.info-card h3 {{ margin:0 0 5px; font-size:13px; }}
.info-card p {{ margin:0; color:var(--muted); font-size:11px; line-height:1.75; }}
.number {{ display:grid; place-items:center; flex:0 0 34px; height:34px;
 border-radius:10px; color:var(--blue); background:#EAF3F8; font-weight:900; font-size:11px; }}
.teal-number {{ color:#16805D; background:#E5F5F2; border-radius:50%; }}
.small-note {{ color:var(--muted); font-size:11px; margin:12px 0 0; }}
.details {{ margin-top:20px; border:1px solid var(--border); border-radius:10px; padding:14px; }}
.details summary {{ cursor:pointer; color:var(--navy); font-weight:800; }}
.empty {{ padding:18px; border:1px dashed var(--border); border-radius:9px; color:var(--muted); }}
.footer {{ padding:22px 10px 0; border-top:1px solid var(--border); color:var(--muted);
 text-align:center; font-size:11px; }}
.footer strong {{ color:var(--navy); }}
.top {{ position:fixed; right:18px; bottom:18px; display:grid; place-items:center;
 width:40px; height:40px; background:#fff; border:1px solid var(--border);
 border-radius:11px; color:var(--blue); box-shadow:0 4px 15px #102A431A; font-size:20px; }}
@media(max-width:900px) {{
 .contents {{ grid-template-columns:1fr; }} .contents-links {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
 .two-col {{ grid-template-columns:1fr; }} .metrics-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
 .cards-grid {{ grid-template-columns:1fr; }} .report-section {{ padding:23px; }}
}}
@media(max-width:560px) {{
 .cover {{ padding:42px 22px; }} .page-container {{ width:calc(100% - 22px); }}
 .contents {{ padding:18px; }} .contents-links {{ grid-template-columns:1fr; }}
 .report-section {{ padding:18px; }} .section-title h2 {{ font-size:21px; }}
 .metrics-grid {{ gap:9px; }} .metric {{ padding:13px; min-height:118px; }}
 .metric-value {{ font-size:24px; }} th,td {{ padding:8px; }}
}}
.print-btn {{ position:fixed; right:18px; bottom:68px; display:flex; align-items:center;
 gap:6px; padding:10px 18px; background:var(--teal); color:#fff; border:none; border-radius:11px;
 font-size:13px; font-weight:700; cursor:pointer; box-shadow:0 4px 15px #102A431A;
 transition:background .2s; z-index:10; }}
.print-btn:hover {{ background:var(--blue); }}
@media print {{
 @page {{ size:A4; margin:13mm 12mm 15mm; }}
 body {{ background:#fff; font-size:9pt; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
 .cover {{ padding:31mm 15mm 25mm; break-after:page; page-break-after:always; }}
 .cover h1 {{ font-size:34pt; }} .cover-subtitle {{ font-size:11pt; }}
 .page-container {{ width:100%; margin:0; }}
 .contents {{ display:block; border-radius:0; padding:7mm; margin-bottom:8mm;
   break-after:page; page-break-after:always; }}
 .contents-links {{ grid-template-columns:repeat(2,minmax(0,1fr)); margin-top:5mm; }}
 .report-section {{ border-radius:0; box-shadow:none; padding:7mm; margin-bottom:7mm; }}
 .section-title {{ margin-bottom:5mm; break-after:avoid; page-break-after:avoid; }}
 .section-title h2 {{ font-size:17pt; }}
 h3 {{ break-after:avoid; page-break-after:avoid; }}
 .metrics-grid {{ grid-template-columns:repeat(3,minmax(0,1fr)); gap:3mm; }}
 .metric {{ min-height:28mm; padding:3.5mm; }}
 .metric-value {{ font-size:19pt; }}
 .two-col {{ grid-template-columns:repeat(2,minmax(0,1fr)); gap:5mm; }}
 .cards-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)); gap:3mm; }}
 .info-card,.metric,.callout {{ break-inside:avoid; page-break-inside:avoid; }}
 .table-wrap {{ overflow:visible; }}
 table {{ font-size:7.5pt; }}
 th,td {{ padding:2mm; }}
 tr {{ break-inside:avoid; page-break-inside:avoid; }}
 .top {{ display:none; }}
  .print-btn {{ display:none; }}
 .footer {{ margin-top:6mm; }}
}}
</style>
</head>
<body id="top">
<header class="cover">
 <div class="cover-inner">
  <div class="brand"><span class="brand-mark">ST</span><span>SPRINTS TALENT ANALYTICS</span></div>
  <div class="eyebrow">ADVANCED DATA ANALYSIS CAPSTONE</div>
  <h1>Analytical<br>Report</h1>
  <p class="cover-subtitle">Learner Performance, Data Quality, Feature Engineering, and Employer Skills Intelligence</p>
 </div>
</header>
<main class="page-container">
 <nav class="contents">
  <div><h2>Report Contents</h2><p>Navigate through the analysis, findings, recommendations, and limitations.</p></div>
  <div class="contents-links">{toc_html}</div>
 </nav>
 {''.join(sections)}
 <footer class="footer"><strong>Sprints Talent Analytics</strong><br>
 Advanced Data Analysis Capstone<br>
 Generated from saved analysis outputs and processed datasets.<br>
 Interpret findings within the documented data and sample limitations.</footer>
</main>
<button class="print-btn" onclick="window.print()" aria-label="Save as PDF">&#128438; Save as PDF</button>
<a class="top" href="#top" aria-label="Back to top">↑</a>
</body>
</html>"""


def main():
    print("=" * 70)
    print("SPRINTS TALENT ANALYTICS")
    print("PROFESSIONAL ANALYTICAL REPORT GENERATOR")
    print("=" * 70)
    try:
        reports, learners, features, employers = load_project()
        print("\n[3/5] Validating project data...")
        print(f"      Learner records: {len(learners)}")
        print(f"      Training tracks: {learners['track_name'].nunique()}")
        print(f"      Cohorts: {learners['cohort_id'].nunique()}")
        print(f"      Employer roles: {len(employers)}")
        print(f"      Feature columns: {len(features.columns)}")

        print("\n[4/5] Building report...")
        content = build_report(reports, learners, features, employers)

        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        print("\n[5/5] Saving HTML report...")
        OUTPUT_PATH.write_text(content, encoding="utf-8")

        # Verify the specific fix before reporting success.
        generated_html = OUTPUT_PATH.read_text(encoding="utf-8")
        required_markers = [
            "Minimum",
            "Maximum",
            "Missing",
            "Derived Features",
        ]
        missing_markers = [marker for marker in required_markers if marker not in generated_html]
        if missing_markers:
            raise RuntimeError(
                "Generated report failed verification. Missing markers: "
                + ", ".join(missing_markers)
            )
        if "{'description':" in generated_html or '{"description":' in generated_html:
            raise RuntimeError(
                "Generated report still contains a raw feature dictionary. "
                "The report was not accepted as verified."
            )

        print("\n" + "=" * 70)
        print("ANALYTICAL REPORT GENERATED AND VERIFIED SUCCESSFULLY")
        print(f"Build ID: {REPORT_BUILD_ID}")
        print("=" * 70)
        print(f"\nOutput file: {OUTPUT_PATH}")
        print(f"File size: {OUTPUT_PATH.stat().st_size:,} bytes")
        print("\nReport sections:")
        for i, title in enumerate([
            "Executive Summary", "Dataset Overview", "Data Quality & Cleaning",
            "Exploratory Data Analysis", "Feature Engineering",
            "Employer Requirements Analysis", "Key Findings", "Recommendations",
            "Limitations & Reproducibility"
        ], 1):
            print(f"  {i}. {title}")
        print("\nNext step:")
        print("  Start-Process .\\reports\\analytical_report.html")
        print("  For PDF: open the report, press Ctrl+P, choose Save as PDF, Paper size A4.")
        return 0
    except Exception as error:
        print("\nREPORT GENERATION FAILED")
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
