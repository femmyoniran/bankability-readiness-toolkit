"""
Top-level convenience function to run a full bankability assessment.
"""

from app.models.project import ProjectParameters
from app.models.scoring import BankabilityScorer
from app.analysis.techno_economic import TechnoEconomicAnalysis
from app.analysis.sensitivity import SensitivityAnalysis


def run_bankability_assessment(project_data):
    """
    Run a complete bankability assessment from a project data dictionary.

    Returns a dictionary containing the bankability score, financial model
    results, credit assessment, techno-economic analysis, and sensitivity
    analysis.
    """
    if isinstance(project_data, dict):
        params = ProjectParameters.from_dict(project_data)
    elif isinstance(project_data, ProjectParameters):
        params = project_data
    else:
        raise ValueError("project_data must be a dict or ProjectParameters instance")

    scorer = BankabilityScorer(params)
    bankability_result = scorer.score()

    techno_econ = TechnoEconomicAnalysis(params)
    te_results = techno_econ.analyze()

    sensitivity = SensitivityAnalysis(params)
    sensitivity_results = sensitivity.run_standard_cases()

    output = bankability_result.to_dict()
    output["techno_economic"] = te_results
    output["sensitivity"] = sensitivity_results
    output["project_info"] = {
        "name": params.project_name,
        "id": params.project_id,
        "stage": params.project_stage,
        "entity_type": params.entity_type,
        "location": f"{params.location_county}, {params.location_state}" if params.location_county else params.location_state,
        "technology": params.technical.technology_type.replace("_", " ").title(),
        "capacity_mw": params.technical.nameplate_capacity_mw,
        "total_cost": params.financial.total_project_cost,
        "description": params.description,
    }

    return output
