"""
Export utilities for bankability assessment results.
"""

import json
from datetime import date, datetime


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def export_results_json(results, indent=2):
    """Export assessment results as a formatted JSON string."""
    return json.dumps(results, indent=indent, cls=DateEncoder, default=str)


def results_to_csv_rows(results):
    """Convert cash flow results to a list of CSV-compatible rows."""
    rows = []

    header = [
        "Year", "Revenue", "OpEx", "NOI", "Debt Service",
        "DSCR", "Free Cash Flow", "Cumulative CF"
    ]
    rows.append(header)

    for cf in results.get("cash_flows", []):
        rows.append([
            cf["year"],
            cf["revenue"],
            cf["opex"],
            cf["noi"],
            cf["debt_service"],
            cf["dscr"],
            cf["free_cash_flow"],
            cf["cumulative_cf"],
        ])

    return rows


def build_summary_report(results):
    """Build a structured summary suitable for display or export."""
    project_info = results.get("project_info", {})
    summary = {
        "report_title": "Bankability Readiness Assessment Report",
        "date_generated": date.today().isoformat(),
        "project_name": project_info.get("name", ""),
        "technology": project_info.get("technology", ""),
        "capacity_mw": project_info.get("capacity_mw", 0),
        "total_investment": project_info.get("total_cost", 0),
        "location": project_info.get("location", ""),
        "entity_type": project_info.get("entity_type", "").replace("_", " ").title(),
        "stage": project_info.get("stage", "").replace("_", " ").title(),
        "overall_score": results.get("overall_score"),
        "grade": results.get("grade"),
        "grade_label": results.get("grade_label"),
        "grade_color": results.get("grade_color"),
        "sub_scores": results.get("sub_scores", []),
        "financial_metrics": results.get("financial_metrics", {}),
        "credit_metrics": results.get("credit_metrics", {}),
        "strengths": results.get("strengths", []),
        "weaknesses": results.get("weaknesses", []),
        "recommendations": results.get("recommendations", []),
        "rus_eligibility": results.get("rus_eligibility", {}),
        "lpo_eligibility": results.get("lpo_eligibility", {}),
    }
    return summary
