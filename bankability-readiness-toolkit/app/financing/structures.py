"""
Financing structure templates for energy infrastructure projects.
Generates capital stack recommendations and term sheet templates
based on project characteristics and target financing programs.
"""


class FinancingStructureBuilder:
    """
    Builds recommended financing structures based on project type,
    size, entity type, and financial metrics.
    """

    STRUCTURE_TEMPLATES = {
        "project_finance": {
            "name": "Non-Recourse Project Finance",
            "description": (
                "Standard project finance structure with ring-fenced project company, "
                "non-recourse senior debt secured by project assets and cash flows, "
                "and sponsor equity."
            ),
            "typical_leverage": 0.70,
            "typical_tenor": 18,
            "typical_dscr_min": 1.30,
            "typical_spread_bps": 200,
            "suitable_for": ["independent_power_producer", "community_choice_aggregator"],
            "min_project_size": 25_000_000,
        },
        "utility_corporate": {
            "name": "Utility Corporate Finance",
            "description": (
                "On-balance-sheet financing by the utility borrower, secured by "
                "the utility's general credit and revenue stream rather than "
                "ring-fenced project assets."
            ),
            "typical_leverage": 0.55,
            "typical_tenor": 20,
            "typical_dscr_min": 1.20,
            "typical_spread_bps": 150,
            "suitable_for": ["investor_owned_utility", "municipal_utility", "cooperative"],
            "min_project_size": 0,
        },
        "rus_direct": {
            "name": "USDA RUS Direct Loan",
            "description": (
                "Direct federal loan from the Rural Utilities Service at Treasury rate "
                "plus a small spread. Available to eligible rural electric cooperatives, "
                "municipal utilities, and tribal entities."
            ),
            "typical_leverage": 0.80,
            "typical_tenor": 35,
            "typical_dscr_min": 1.00,
            "typical_spread_bps": 25,
            "suitable_for": ["cooperative", "municipal_utility", "tribal_utility"],
            "min_project_size": 0,
            "requires_rural": True,
        },
        "rus_guaranteed": {
            "name": "USDA RUS Loan Guarantee",
            "description": (
                "Federal guarantee on private-sector loans arranged through the "
                "Federal Financing Bank or commercial lenders. Reduces borrowing "
                "costs through the government guarantee."
            ),
            "typical_leverage": 0.80,
            "typical_tenor": 35,
            "typical_dscr_min": 1.00,
            "typical_spread_bps": 50,
            "suitable_for": ["cooperative", "municipal_utility", "tribal_utility"],
            "min_project_size": 0,
            "requires_rural": True,
        },
        "doe_lpo": {
            "name": "DOE LPO Title XVII Loan Guarantee",
            "description": (
                "Federal loan guarantee for innovative energy projects under "
                "Title XVII of the Energy Policy Act. Covers up to 80% of project "
                "costs with long tenors and competitive rates."
            ),
            "typical_leverage": 0.80,
            "typical_tenor": 30,
            "typical_dscr_min": 1.20,
            "typical_spread_bps": 75,
            "suitable_for": ["independent_power_producer", "investor_owned_utility", "cooperative"],
            "min_project_size": 25_000_000,
            "requires_innovation": True,
        },
        "tax_equity": {
            "name": "Tax Equity Partnership Flip",
            "description": (
                "Partnership structure where a tax equity investor receives the "
                "majority of tax benefits (ITC/PTC, MACRS depreciation) in exchange "
                "for upfront capital, with allocation ratios flipping after a target "
                "return is achieved."
            ),
            "typical_leverage": 0.40,
            "typical_tenor": 10,
            "typical_dscr_min": 1.0,
            "typical_spread_bps": 0,
            "suitable_for": ["independent_power_producer"],
            "min_project_size": 10_000_000,
            "requires_tax_credits": True,
        },
        "municipal_bond": {
            "name": "Tax-Exempt Municipal Revenue Bonds",
            "description": (
                "Tax-exempt bonds issued by a municipal entity or authority, "
                "secured by project revenues. Lower cost of capital due to "
                "tax-exempt interest for bondholders."
            ),
            "typical_leverage": 0.75,
            "typical_tenor": 30,
            "typical_dscr_min": 1.25,
            "typical_spread_bps": 100,
            "suitable_for": ["municipal_utility", "state_authority"],
            "min_project_size": 10_000_000,
        },
    }

    def __init__(self, project_params):
        self.params = project_params

    def recommend_structures(self):
        """Identify and rank applicable financing structures."""
        applicable = []

        for key, template in self.STRUCTURE_TEMPLATES.items():
            eligibility = self._check_eligibility(key, template)
            if eligibility["eligible"]:
                fit_score = self._compute_fit_score(key, template)
                applicable.append({
                    "structure_key": key,
                    "template": template,
                    "fit_score": fit_score,
                    "eligibility": eligibility,
                    "term_sheet": self._generate_term_sheet(key, template),
                })

        applicable.sort(key=lambda x: x["fit_score"], reverse=True)
        return applicable

    def _check_eligibility(self, key, template):
        eligible = True
        notes = []

        if self.params.entity_type not in template["suitable_for"]:
            eligible = False
            notes.append(f"Entity type '{self.params.entity_type}' is not typically eligible.")

        if self.params.financial.total_project_cost < template["min_project_size"]:
            eligible = False
            notes.append(f"Project size below minimum of ${template['min_project_size']:,.0f}.")

        if template.get("requires_rural") and not self.params.is_rural:
            eligible = False
            notes.append("Project must be located in a designated rural area.")

        if template.get("requires_tax_credits"):
            has_credits = self.params.financial.itc_percent > 0 or self.params.financial.ptc_per_mwh > 0
            if not has_credits:
                eligible = False
                notes.append("Structure requires ITC or PTC eligibility.")

        return {"eligible": eligible, "notes": notes}

    def _compute_fit_score(self, key, template):
        score = 50.0

        dscr = self.params.financial.dscr
        if dscr >= template["typical_dscr_min"]:
            score += 15
        elif dscr >= template["typical_dscr_min"] * 0.9:
            score += 5

        leverage = self.params.financial.leverage_ratio
        if abs(leverage - template["typical_leverage"]) <= 0.10:
            score += 10

        if key in ("rus_direct", "rus_guaranteed") and self.params.is_rural:
            score += 20

        if key == "doe_lpo":
            innovative = [
                "battery_storage", "offshore_wind", "geothermal",
                "solar_plus_storage", "microgrids", "grid_modernization",
            ]
            if self.params.technical.technology_type in innovative:
                score += 15

        if key == "tax_equity":
            if self.params.financial.itc_percent >= 0.30:
                score += 15
            elif self.params.financial.ptc_per_mwh > 0:
                score += 10

        if key == "municipal_bond":
            if self.params.entity_type in ("municipal_utility", "state_authority"):
                score += 15

        return min(score, 100)

    def _generate_term_sheet(self, key, template):
        fp = self.params.financial
        debt_amount = fp.total_project_cost * template["typical_leverage"]

        term_sheet = {
            "structure": template["name"],
            "borrower": self.params.entity_type.replace("_", " ").title(),
            "project": self.params.project_name or "TBD",
            "facility_type": "Senior Secured Term Loan" if key != "municipal_bond" else "Tax-Exempt Revenue Bonds",
            "amount": f"${debt_amount:,.0f}",
            "amount_numeric": debt_amount,
            "tenor": f"{template['typical_tenor']} years",
            "amortization": "Fully amortizing" if key != "tax_equity" else "Sculpted",
            "pricing": f"Reference rate + {template['typical_spread_bps']} bps",
            "dscr_covenant": f"Minimum {template['typical_dscr_min']:.2f}x",
            "security": self._describe_security(key),
            "conditions_precedent": self._list_conditions_precedent(key),
            "covenants": self._list_covenants(key, template),
            "reserve_requirements": self._list_reserves(key),
        }

        return term_sheet

    def _describe_security(self, key):
        if key in ("rus_direct", "rus_guaranteed"):
            return ("First priority lien on all assets of the borrower system, "
                    "including real property, equipment, revenues, and accounts. "
                    "Assignment of all material project contracts.")
        elif key == "doe_lpo":
            return ("First priority lien on project assets and assignment of "
                    "project contracts. Government guarantee secured by project cash flows.")
        elif key == "project_finance":
            return ("First priority security interest in all project assets, "
                    "assignment of project contracts (EPC, O&M, PPA), pledge of equity "
                    "interests in project company, and assignment of insurance proceeds.")
        elif key == "municipal_bond":
            return "Revenue pledge from project operations and system revenues."
        else:
            return "Security package to be determined based on lender requirements."

    def _list_conditions_precedent(self, key):
        cps = [
            "Execution of all material project contracts",
            "Receipt of all required permits and approvals",
            "Satisfactory independent engineer report",
            "Satisfactory legal opinions",
            "Evidence of required insurance coverage",
            "Funding of required reserve accounts",
        ]
        if key in ("rus_direct", "rus_guaranteed"):
            cps.extend([
                "Approved RUS Form 201 loan application",
                "Environmental review compliance (7 CFR 1970)",
                "USDA Rural Development area eligibility confirmation",
            ])
        elif key == "doe_lpo":
            cps.extend([
                "Completed LPO Part I and Part II application",
                "NEPA environmental review completion",
                "Credit subsidy cost payment",
                "Davis-Bacon Act compliance certification",
            ])
        return cps

    def _list_covenants(self, key, template):
        covenants = [
            f"Minimum DSCR: {template['typical_dscr_min']:.2f}x (tested quarterly)",
            "Distribution lock-up DSCR: 1.10x",
            "Annual audited financial statements within 120 days of fiscal year end",
            "Quarterly unaudited financial statements within 45 days of quarter end",
            "Maintenance of all material permits and approvals",
            "Maintenance of required insurance coverage",
            "No additional indebtedness without lender consent",
        ]
        if key in ("rus_direct", "rus_guaranteed"):
            covenants.extend([
                "Compliance with RUS mortgage requirements",
                "Annual RUS Operating Report (Form 7)",
                "Maintain minimum TIER (Times Interest Earned Ratio) of 1.50x",
            ])
        return covenants

    def _list_reserves(self, key):
        reserves = [
            "Debt service reserve: 6 months of debt service",
            "Major maintenance reserve: As determined by independent engineer",
        ]
        if key in ("rus_direct", "rus_guaranteed"):
            reserves.append(
                "Cushion of credit reserve: Optional pre-payment account per RUS regulations"
            )
        return reserves
