from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from app.analysis.bankability_score import run_bankability_assessment
from app.financing.structures import FinancingStructureBuilder
from app.models.project import ProjectParameters
from app.session_store import store_get, store_set

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/results")
def results():
    project_data = store_get("project_data")
    if not project_data:
        flash("No project data found. Please enter project details first.", "error")
        return redirect(url_for("project.new_project"))

    try:
        assessment = run_bankability_assessment(project_data)
    except Exception as e:
        flash(f"Error running assessment: {str(e)}", "error")
        return redirect(url_for("project.new_project"))

    store_set("assessment_results", assessment)
    return render_template("results.html", results=assessment)


@analysis_bp.route("/financing")
def financing():
    project_data = store_get("project_data")
    if not project_data:
        flash("No project data found. Please enter project details first.", "error")
        return redirect(url_for("project.new_project"))

    params = ProjectParameters.from_dict(project_data)
    builder = FinancingStructureBuilder(params)
    raw_structures = builder.recommend_structures()

    assessment = store_get("assessment_results", {})

    # Transform structures for the template
    structures = []
    term_sheets = []
    rus_eligible = False
    lpo_eligible = False
    for s in raw_structures:
        tmpl = s["template"]
        structures.append({
            "name": tmpl["name"],
            "description": tmpl["description"],
            "fit_score": s["fit_score"],
            "type": s["structure_key"].replace("_", " ").title(),
            "typical_leverage": f"{tmpl['typical_leverage']:.0%}",
            "tenor_range": f"Up to {tmpl['typical_tenor']} years",
            "rate_basis": f"Reference + {tmpl['typical_spread_bps']} bps",
            "min_project_size": f"${tmpl['min_project_size']:,.0f}" if tmpl["min_project_size"] > 0 else "None",
            "eligibility_notes": s["eligibility"].get("notes", []),
            "advantages": [],
            "considerations": [],
        })
        ts = s["term_sheet"]
        term_sheets.append({
            "title": ts["structure"],
            "date_generated": __import__("datetime").date.today().isoformat(),
            "key_terms": {
                "Borrower": ts["borrower"],
                "Project": ts["project"],
                "Facility": ts["facility_type"],
                "Amount": ts["amount"],
                "Tenor": ts["tenor"],
                "Amortization": ts["amortization"],
                "Pricing": ts["pricing"],
                "DSCR Covenant": ts["dscr_covenant"],
            },
            "security": [ts["security"]] if isinstance(ts["security"], str) else ts["security"],
            "conditions_precedent": ts["conditions_precedent"],
            "covenants": {c: "" for c in ts["covenants"]} if isinstance(ts["covenants"], list) else ts["covenants"],
            "reserves": {r: "" for r in ts["reserve_requirements"]} if isinstance(ts["reserve_requirements"], list) else ts["reserve_requirements"],
        })
        if s["structure_key"] in ("rus_direct", "rus_guaranteed"):
            rus_eligible = True
        if s["structure_key"] == "doe_lpo":
            lpo_eligible = True

    return render_template(
        "financing.html",
        project_name=params.project_name,
        capacity_mw=params.technical.nameplate_capacity_mw,
        technology=params.technical.technology_type.replace("_", " ").title(),
        structures=structures,
        term_sheets=term_sheets,
        rus_eligible=rus_eligible,
        lpo_eligible=lpo_eligible,
        results=assessment,
    )


@analysis_bp.route("/api/assess", methods=["POST"])
def api_assess():
    """JSON API endpoint for programmatic access."""
    project_data = request.get_json()
    if not project_data:
        return jsonify({"error": "No project data provided"}), 400

    try:
        assessment = run_bankability_assessment(project_data)
        return jsonify(assessment)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
