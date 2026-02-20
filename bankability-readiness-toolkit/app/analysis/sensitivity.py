"""
Sensitivity analysis for bankability assessments.
Evaluates how key financial metrics respond to changes in critical assumptions.
"""

import copy
from app.models.financial import FinancialModel


class SensitivityAnalysis:
    """
    Runs one-factor-at-a-time sensitivity analysis on a project,
    varying key parameters to show their impact on DSCR, IRR, and NPV.
    """

    DEFAULT_VARIATION_RANGE = [-0.20, -0.10, -0.05, 0.0, 0.05, 0.10, 0.20]

    SENSITIVITY_PARAMETERS = [
        {
            "name": "revenue",
            "label": "Annual Revenue",
            "attribute_path": ("financial", "annual_revenue"),
            "unit": "percent_change",
        },
        {
            "name": "opex",
            "label": "Operating Costs",
            "attribute_path": ("financial", "annual_opex"),
            "unit": "percent_change",
        },
        {
            "name": "capex",
            "label": "Total Project Cost",
            "attribute_path": ("financial", "total_project_cost"),
            "unit": "percent_change",
        },
        {
            "name": "interest_rate",
            "label": "Interest Rate",
            "attribute_path": ("financial", "interest_rate"),
            "unit": "absolute_change",
            "variations": [-0.02, -0.01, -0.005, 0.0, 0.005, 0.01, 0.02],
        },
        {
            "name": "capacity_factor",
            "label": "Capacity Factor / Generation",
            "attribute_path": ("technical", "annual_generation_mwh"),
            "unit": "percent_change",
        },
    ]

    def __init__(self, project_params):
        self.base_params = project_params

    def run_standard_cases(self):
        """Run sensitivity analysis for all standard parameters."""
        results = {}
        for param_config in self.SENSITIVITY_PARAMETERS:
            results[param_config["name"]] = self._run_single_parameter(param_config)
        return results

    def _run_single_parameter(self, param_config):
        """Run sensitivity for one parameter across its variation range."""
        variations = param_config.get("variations", self.DEFAULT_VARIATION_RANGE)
        section_name, attr_name = param_config["attribute_path"]
        unit = param_config["unit"]

        section = getattr(self.base_params, section_name)
        base_value = getattr(section, attr_name)

        cases = []
        for var in variations:
            params_copy = copy.deepcopy(self.base_params)
            section_copy = getattr(params_copy, section_name)

            if unit == "percent_change":
                new_value = base_value * (1 + var)
                label = f"{var:+.0%}"
            else:
                new_value = base_value + var
                if "rate" in attr_name:
                    label = f"{var * 100:+.1f}%"
                else:
                    label = f"{var:+.2f}"

            setattr(section_copy, attr_name, new_value)

            # Recalculate debt-related fields if capex changed
            if attr_name == "total_project_cost":
                section_copy.total_hard_costs = params_copy.financial.total_hard_costs * (1 + var)

            model = FinancialModel(params_copy)
            summary = model.build_pro_forma()

            cases.append({
                "variation": var,
                "label": label,
                "base_value": round(base_value, 2),
                "adjusted_value": round(new_value, 2),
                "min_dscr": round(summary.minimum_dscr, 3),
                "avg_dscr": round(summary.average_dscr, 3),
                "irr_project": round(summary.irr_project * 100, 2),
                "npv_project": round(summary.npv_project, 0),
                "lcoe": round(summary.lcoe, 2),
                "payback_years": round(summary.payback_years, 1),
            })

        return {
            "parameter": param_config["name"],
            "label": param_config["label"],
            "base_value": base_value,
            "cases": cases,
        }

    def run_custom_scenario(self, overrides):
        """
        Run a custom scenario with multiple parameter overrides.

        overrides: dict of {section.attribute: new_value}
        Example: {"financial.annual_revenue": 5000000, "financial.interest_rate": 0.06}
        """
        params_copy = copy.deepcopy(self.base_params)

        for key, value in overrides.items():
            parts = key.split(".")
            if len(parts) == 2:
                section_name, attr_name = parts
                section = getattr(params_copy, section_name, None)
                if section and hasattr(section, attr_name):
                    setattr(section, attr_name, value)

        model = FinancialModel(params_copy)
        summary = model.build_pro_forma()

        return {
            "overrides": overrides,
            "min_dscr": round(summary.minimum_dscr, 3),
            "avg_dscr": round(summary.average_dscr, 3),
            "irr_project": round(summary.irr_project * 100, 2),
            "irr_equity": round(summary.irr_equity * 100, 2),
            "npv_project": round(summary.npv_project, 0),
            "npv_equity": round(summary.npv_equity, 0),
            "lcoe": round(summary.lcoe, 2),
            "payback_years": round(summary.payback_years, 1),
        }
