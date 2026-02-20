from flask import Blueprint, render_template, redirect, url_for, flash, Response
from app.models.project import ProjectParameters
from app.financing.rus_form_201 import RUSForm201Generator
from app.financing.doe_lpo_title_xvii import LPOTitleXVIIGenerator
from app.models.scoring import BankabilityScorer
from app.utils.export import export_results_json, build_summary_report
from app.session_store import store_get

report_bp = Blueprint("report", __name__)


@report_bp.route("/summary")
def summary_report():
    assessment = store_get("assessment_results")
    if not assessment:
        flash("No assessment results found. Please run an assessment first.", "error")
        return redirect(url_for("project.new_project"))

    report = build_summary_report(assessment)
    return render_template("report.html", report=report, results=assessment)


@report_bp.route("/rus-201")
def rus_201():
    project_data = store_get("project_data")
    assessment = store_get("assessment_results")
    if not project_data:
        flash("No project data found.", "error")
        return redirect(url_for("project.new_project"))

    params = ProjectParameters.from_dict(project_data)
    financial_summary = None
    if assessment:
        scorer = BankabilityScorer(params)
        result = scorer.score()
        financial_summary = result.financial_summary

    generator = RUSForm201Generator(params, financial_summary)
    raw = generator.generate()

    # Transform generator output to flat structure for the template
    sec_a_fields = raw.get("section_a_borrower_info", {}).get("fields", {})
    sec_b_fields = raw.get("section_b_loan_request", {}).get("fields", {})
    sec_c_fields = raw.get("section_c_project_description", {}).get("fields", {})
    sec_d_fields = raw.get("section_d_cost_estimates", {}).get("fields", {})
    sec_e_fields = raw.get("section_e_financial_information", {}).get("fields", {})
    sec_f_fields = raw.get("section_f_economic_feasibility", {}).get("fields", {})
    sec_g_fields = raw.get("section_g_environmental", {}).get("fields", {})
    sec_h = raw.get("section_h_certifications", {})
    supporting = raw.get("supporting_documents", {})

    # Parse the loan amount from the formatted string
    loan_amount_str = sec_b_fields.get("loan_amount_requested", "$0")
    loan_amount = sec_b_fields.get("loan_amount_numeric", 0)

    # Build cost breakdown list from nested dict
    cost_bd = sec_d_fields.get("cost_breakdown", {})
    cost_breakdown = []
    for key, item in cost_bd.items():
        if isinstance(item, dict):
            cost_breakdown.append({
                "category": item.get("label", key),
                "amount": item.get("amount_numeric", 0),
            })

    # Funding sources
    funding = sec_d_fields.get("funding_sources", {})
    loan_source = funding.get("rus_loan", {})
    equity_source = funding.get("borrower_equity", {})

    total_cost_numeric = sec_d_fields.get("total_project_cost_numeric", 0)

    # Financial ratios
    noi = params.financial.net_operating_income
    dscr = params.financial.dscr

    # Economic feasibility
    cost_benefit = sec_f_fields.get("cost_benefit_summary", {})
    detailed_metrics = sec_f_fields.get("detailed_metrics", {})

    form_data = {
        "section_a": {
            "applicant_name": sec_a_fields.get("borrower_name", ""),
            "applicant_type": sec_a_fields.get("borrower_type", ""),
            "state": sec_a_fields.get("state", ""),
            "date_incorporated": "[Date of Incorporation]",
            "physical_address": sec_a_fields.get("principal_office_address", ""),
            "mailing_address": sec_a_fields.get("principal_office_address", ""),
            "contact_name": sec_a_fields.get("contact_name", ""),
            "phone": sec_a_fields.get("contact_phone", ""),
            "email": sec_a_fields.get("contact_email", ""),
            "existing_borrower": "To Be Determined",
            "borrower_designation": "[RUS Designation]",
            "duns_number": "[DUNS Number]",
        },
        "section_b": {
            "loan_type": raw.get("form_metadata", {}).get("loan_type", ""),
            "loan_amount": loan_amount,
            "loan_purpose": sec_b_fields.get("loan_purpose", ""),
            "interest_rate_type": sec_b_fields.get("interest_rate_preference", ""),
            "term_years": sec_b_fields.get("loan_term_requested_years", 0),
            "amortization_years": sec_b_fields.get("loan_term_requested_years", 0),
            "first_advance_date": sec_b_fields.get("estimated_first_advance_date", ""),
            "construction_period": f"{sec_b_fields.get('construction_period_months', 0)} months",
        },
        "section_c": {
            "project_name": sec_c_fields.get("project_name", ""),
            "project_type": sec_c_fields.get("technology_type", ""),
            "technology": sec_c_fields.get("technology_type", ""),
            "capacity_mw": sec_c_fields.get("nameplate_capacity_mw", 0),
            "annual_generation_mwh": sec_c_fields.get("expected_annual_generation_mwh", 0),
            "location": sec_c_fields.get("location_description", ""),
            "rural_area": sec_c_fields.get("rural_area_served", ""),
            "consumers_served": "[Number of consumers]",
            "target_cod": sec_c_fields.get("target_commercial_operation", ""),
            "useful_life": sec_c_fields.get("expected_useful_life_years", 0),
            "narrative": sec_c_fields.get("project_description", ""),
        },
        "section_d": {
            "cost_breakdown": cost_breakdown,
            "total_project_cost": total_cost_numeric,
            "sources": {
                "loan": loan_amount,
                "equity": params.financial.equity_amount,
                "other": 0,
            },
        },
        "section_e": {
            "equity": params.financial.equity_amount,
            "total_assets": params.financial.total_project_cost,
            "total_liabilities": params.financial.debt_amount,
            "annual_revenue": params.financial.annual_revenue,
            "net_income": noi,
            "current_ratio": 1.5,
            "debt_to_equity": f"{params.financial.leverage_ratio:.2f}",
            "tier": f"{noi / max(params.financial.debt_amount * params.financial.interest_rate, 1):.2f}x",
            "dsc": f"{dscr:.2f}x",
        },
        "section_f": {
            "projected_dscr_min": f"{dscr:.2f}" if not financial_summary else f"{financial_summary.minimum_dscr:.2f}",
            "projected_dscr_avg": f"{dscr:.2f}" if not financial_summary else f"{financial_summary.average_dscr:.2f}",
            "project_irr": f"{0:.1f}" if not financial_summary else f"{financial_summary.irr_project * 100:.1f}",
            "lcoe": f"{0:.2f}" if not financial_summary else f"{financial_summary.lcoe:.2f}",
            "payback_years": "N/A" if not financial_summary else f"{financial_summary.payback_years:.1f}",
            "npv": 0 if not financial_summary else financial_summary.npv_project,
            "offtake_type": params.credit.offtake_type.replace("_", " ").title(),
            "offtake_term": params.credit.offtake_tenor_years,
            "contract_price": f"{params.credit.contract_price_per_mwh:.2f}",
        },
        "section_g": sec_g_fields,
        "section_h": sec_h.get("certifications", {}),
        "supporting_documents": supporting.get("checklist", []),
        "eligibility_notes": raw.get("eligibility_notes", []),
    }

    return render_template("rus_201.html", form_data=form_data, project=project_data)


@report_bp.route("/lpo-xvii")
def lpo_xvii():
    project_data = store_get("project_data")
    assessment = store_get("assessment_results")
    if not project_data:
        flash("No project data found.", "error")
        return redirect(url_for("project.new_project"))

    params = ProjectParameters.from_dict(project_data)
    financial_summary = None
    credit_assessment = None
    if assessment:
        scorer = BankabilityScorer(params)
        result = scorer.score()
        financial_summary = result.financial_summary
        credit_assessment = result.credit_assessment

    generator = LPOTitleXVIIGenerator(params, financial_summary, credit_assessment)
    raw = generator.generate()

    # Transform generator output to flatten for template
    part_i_sections = raw.get("part_i_pre_application", {}).get("sections", {})
    exec_summary = part_i_sections.get("executive_summary", {})
    tech_desc = part_i_sections.get("technology_description", {})
    fin_overview = part_i_sections.get("financial_overview", {})

    guarantee_amount = params.financial.total_project_cost * 0.80

    # Build credit subsidy if available
    credit_summary_raw = raw.get("credit_assessment_summary", {})
    subsidy_est = credit_summary_raw.get("credit_subsidy_estimation", {})
    credit_subsidy = None
    if subsidy_est:
        subsidy_range = subsidy_est.get("estimated_subsidy_range", {})
        credit_subsidy = {
            "estimated_cost": params.financial.total_project_cost * 0.80 * 0.03,
            "subsidy_rate": 3.0,
            "guarantee_amount": guarantee_amount,
            "note": "Estimate based on typical range of 1-5% of guarantee amount.",
        }

    # Part II elements
    part_ii_raw = raw.get("part_ii_full_application", {}).get("required_elements", {})
    part_ii_project_details = {}
    for key, element in part_ii_raw.items():
        if isinstance(element, dict):
            part_ii_project_details[key.replace("_", " ").title()] = element.get("description", "")

    # Financial plan from params
    financial_plan = {
        "Total Project Cost": params.financial.total_project_cost,
        "Debt Amount": params.financial.debt_amount,
        "Equity Amount": params.financial.equity_amount,
        "Leverage": f"{params.financial.leverage_ratio:.0%}",
        "Interest Rate": f"{params.financial.interest_rate:.2%}",
        "Debt Tenor": f"{params.financial.debt_tenor_years} years",
        "DSCR": f"{params.financial.dscr:.2f}x",
    }
    if financial_summary:
        financial_plan["Project IRR"] = f"{financial_summary.irr_project * 100:.1f}%"
        financial_plan["Project NPV"] = financial_summary.npv_project
        financial_plan["LCOE"] = f"${financial_summary.lcoe:.2f}/MWh"

    # Environmental
    env_raw = raw.get("environmental_requirements", {})
    environmental = {}
    for item in env_raw.get("required_environmental_data", []):
        environmental[item] = "To Be Completed"

    # Compliance
    compliance_raw = raw.get("compliance_requirements", {}).get("requirements", [])
    compliance = []
    for req in compliance_raw:
        compliance.append({
            "requirement": req.get("requirement", ""),
            "status": "To Be Addressed",
            "detail": req.get("description", ""),
        })

    # Fee schedule
    fee_raw = raw.get("application_fees", {}).get("fees", [])
    fee_schedule = {}
    for fee in fee_raw:
        fee_schedule[fee.get("fee", "")] = fee.get("amount", "")

    # Eligibility assessment
    elig_raw = raw.get("eligibility_assessment", {}).get("assessments", [])
    eligibility_assessment = []
    for e in elig_raw:
        met = True if e.get("status", "").startswith("Likely") or e.get("status") == "Supported" else "Review"
        eligibility_assessment.append({
            "criterion": e.get("criterion", ""),
            "met": met,
            "detail": e.get("detail", ""),
        })

    app_data = {
        "part_i": {
            "project_name": exec_summary.get("project_name", ""),
            "applicant": exec_summary.get("applicant_name", ""),
            "location": exec_summary.get("location", ""),
            "technology_category": tech_desc.get("technology_type", ""),
            "technology_type": tech_desc.get("technology_type", ""),
            "capacity_mw": params.technical.nameplate_capacity_mw,
            "total_project_cost": params.financial.total_project_cost,
            "guarantee_amount_requested": guarantee_amount,
            "target_cod": params.cod_target or "[Date]",
            "jobs_construction": "[Estimate]",
            "jobs_operations": "[Estimate]",
            "eligible_category": raw.get("application_metadata", {}).get("technology_category", {}).get("label", ""),
            "statutory_authority": "Energy Policy Act of 2005, Title XVII (42 U.S.C. 16511-16514)",
            "innovation_narrative": tech_desc.get("innovation_narrative", ""),
            "debt_equity_split": f"{params.financial.debt_percent:.0%} / {params.financial.equity_percent:.0%}",
            "project_irr": f"{0:.1f}" if not financial_summary else f"{financial_summary.irr_project * 100:.1f}",
            "dscr_min": f"{params.financial.dscr:.2f}" if not financial_summary else f"{financial_summary.minimum_dscr:.2f}",
            "lcoe": f"{0:.2f}" if not financial_summary else f"{financial_summary.lcoe:.2f}",
            "offtake_summary": params.credit.offtake_type.replace("_", " ").title(),
            "equity_sponsors": "[To be identified]",
            "credit_subsidy": credit_subsidy,
        },
        "part_ii": {
            "project_details": part_ii_project_details,
            "financial_plan": financial_plan,
            "environmental": environmental if environmental else None,
            "compliance": compliance if compliance else None,
            "fee_schedule": fee_schedule if fee_schedule else None,
        },
        "eligibility_assessment": eligibility_assessment,
    }

    return render_template("lpo_xvii.html", app_data=app_data, project=project_data)


@report_bp.route("/export-json")
def export_json():
    assessment = store_get("assessment_results")
    if not assessment:
        flash("No assessment results to export.", "error")
        return redirect(url_for("project.new_project"))

    json_str = export_results_json(assessment)
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": "attachment;filename=bankability_assessment.json"},
    )
