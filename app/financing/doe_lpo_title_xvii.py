"""
DOE Loan Programs Office (LPO) Title XVII application data generator.
Produces structured output aligning with the LPO application process
for innovative energy technology loan guarantees.

Reference: Energy Policy Act of 2005, Title XVII (42 U.S.C. 16511-16514)
           10 CFR Part 609 -- Loan Guarantees for Projects That Employ
           Innovative Technologies
"""

from datetime import date


ELIGIBLE_CATEGORIES = {
    "renewable_energy": {
        "label": "Renewable Energy Systems",
        "description": "Systems that generate electricity from renewable sources "
                       "employing new or significantly improved technologies.",
        "examples": ["Advanced solar", "Offshore wind", "Enhanced geothermal"],
    },
    "energy_efficiency": {
        "label": "Energy Efficiency Technologies",
        "description": "Technologies that improve energy efficiency in industrial, "
                       "commercial, or residential applications.",
        "examples": ["Advanced building systems", "Industrial process improvements"],
    },
    "advanced_nuclear": {
        "label": "Advanced Nuclear Energy",
        "description": "Advanced nuclear energy facilities with improved safety, "
                       "efficiency, or waste characteristics.",
        "examples": ["Small modular reactors", "Advanced reactor designs"],
    },
    "fossil_energy": {
        "label": "Advanced Fossil Energy",
        "description": "Projects employing carbon capture, advanced gasification, "
                       "or other innovative fossil energy technologies.",
        "examples": ["Carbon capture and storage", "Advanced turbines"],
    },
    "energy_storage": {
        "label": "Energy Storage",
        "description": "Grid-scale or distributed energy storage systems employing "
                       "innovative technologies.",
        "examples": ["Advanced battery chemistries", "Long-duration storage"],
    },
    "grid_modernization": {
        "label": "Grid Modernization",
        "description": "Technologies that improve grid reliability, resilience, "
                       "or enable integration of distributed resources.",
        "examples": ["Advanced grid controls", "Microgrids", "HVDC transmission"],
    },
}


class LPOTitleXVIIGenerator:
    """
    Generates structured data for a DOE LPO Title XVII loan guarantee
    application, covering both Part I (pre-application) and Part II
    (full application) requirements.
    """

    def __init__(self, project_params, financial_summary=None, credit_assessment=None):
        self.params = project_params
        self.fp = project_params.financial
        self.tp = project_params.technical
        self.financial_summary = financial_summary
        self.credit_assessment = credit_assessment

    def generate(self):
        """Build the full LPO application data structure."""
        return {
            "application_metadata": self._metadata(),
            "part_i_pre_application": self._part_i(),
            "part_ii_full_application": self._part_ii(),
            "credit_assessment_summary": self._credit_summary(),
            "environmental_requirements": self._environmental_requirements(),
            "compliance_requirements": self._compliance_requirements(),
            "application_fees": self._fee_schedule(),
            "eligibility_assessment": self._eligibility_assessment(),
        }

    def _metadata(self):
        return {
            "program": "DOE Loan Programs Office -- Title XVII Innovative Energy Loan Guarantee",
            "statutory_authority": "Energy Policy Act of 2005, Title XVII (42 U.S.C. 16511-16514)",
            "regulatory_reference": "10 CFR Part 609",
            "date_prepared": date.today().isoformat(),
            "project_name": self.params.project_name or "[Project Name]",
            "applicant": self.params.entity_type.replace("_", " ").title(),
            "technology_category": self._identify_category(),
        }

    def _identify_category(self):
        tech = self.tp.technology_type
        category_map = {
            "solar_pv": "renewable_energy",
            "onshore_wind": "renewable_energy",
            "offshore_wind": "renewable_energy",
            "geothermal": "renewable_energy",
            "hydro_small": "renewable_energy",
            "biomass": "renewable_energy",
            "battery_storage": "energy_storage",
            "solar_plus_storage": "energy_storage",
            "microgrids": "grid_modernization",
            "grid_modernization": "grid_modernization",
            "transmission_line": "grid_modernization",
            "distribution_upgrade": "grid_modernization",
            "substation": "grid_modernization",
            "natural_gas_peaker": "fossil_energy",
            "combined_cycle": "fossil_energy",
        }
        cat_key = category_map.get(tech, "renewable_energy")
        return ELIGIBLE_CATEGORIES.get(cat_key, ELIGIBLE_CATEGORIES["renewable_energy"])

    def _part_i(self):
        """Part I: Pre-Application (initial screening by LPO)."""
        guarantee_amount = self.fp.total_project_cost * 0.80

        return {
            "section_title": "Part I: Pre-Application",
            "description": (
                "The Part I pre-application provides LPO with sufficient "
                "information to evaluate whether the project warrants a full "
                "application review. LPO typically responds within 60 days."
            ),
            "sections": {
                "executive_summary": {
                    "project_name": self.params.project_name or "[Project Name]",
                    "project_description": self._project_description(),
                    "applicant_name": "[Legal Entity Name]",
                    "applicant_type": self.params.entity_type.replace("_", " ").title(),
                    "location": f"{self.params.location_county or '[County]'}, "
                                f"{self.params.location_state or '[State]'}",
                    "total_project_cost": f"${self.fp.total_project_cost:,.0f}",
                    "guarantee_amount_requested": f"${guarantee_amount:,.0f}",
                    "guarantee_percent": "80%",
                    "estimated_jobs_construction": "[Number]",
                    "estimated_jobs_permanent": "[Number]",
                },
                "technology_description": {
                    "technology_type": self.tp.technology_type.replace("_", " ").title(),
                    "capacity": f"{self.tp.nameplate_capacity_mw:.1f} MW",
                    "innovation_narrative": self._innovation_narrative(),
                    "technology_readiness_level": self.tp.technology_readiness_level,
                    "prior_commercial_deployment": "[Description of prior deployments]",
                    "performance_basis": f"Capacity factor: {self.tp.capacity_factor:.1%}",
                    "key_technology_risks": "[Identified technology-specific risks]",
                },
                "financial_overview": {
                    "total_project_cost": f"${self.fp.total_project_cost:,.0f}",
                    "debt_amount": f"${self.fp.debt_amount:,.0f}",
                    "equity_amount": f"${self.fp.equity_amount:,.0f}",
                    "leverage_ratio": f"{self.fp.leverage_ratio:.0%}",
                    "projected_dscr": f"{self.fp.dscr:.2f}x",
                    "revenue_source": self.params.credit.offtake_type.replace("_", " ").title(),
                    "offtake_agreement_status": "[Executed/In Negotiation/Planned]",
                    "equity_commitment_status": "[Committed/In Discussion/Uncommitted]",
                },
                "environmental_benefits": {
                    "ghg_reduction_annual_tons": "[Estimated annual CO2 reduction]",
                    "ghg_reduction_lifetime_tons": "[Estimated lifetime CO2 reduction]",
                    "criteria_pollutant_reductions": "[If applicable]",
                    "environmental_justice_benefits": "[Description if applicable]",
                    "community_benefits": "[Description of community impact]",
                },
            },
        }

    def _part_ii(self):
        """Part II: Full Application (detailed due diligence package)."""
        return {
            "section_title": "Part II: Full Application",
            "description": (
                "The Part II application is a comprehensive submission required "
                "after LPO invites the applicant to proceed. It includes detailed "
                "technical, financial, legal, and environmental documentation."
            ),
            "required_elements": {
                "detailed_project_description": {
                    "description": "Complete technical description of the project",
                    "status": "[To be prepared]",
                    "contents": [
                        "Engineering design documents and specifications",
                        "Equipment procurement strategy and supplier information",
                        "Construction plan and timeline",
                        "Site description and site control documentation",
                        "Interconnection studies and agreements",
                        "Technology performance data and warranties",
                    ],
                },
                "financial_model": {
                    "description": "Detailed financial model with assumptions",
                    "status": "[To be prepared]",
                    "contents": [
                        "Base case pro forma financial projections",
                        "Sensitivity analysis on key variables",
                        "Capital structure and sources/uses",
                        "Revenue projections and offtake agreements",
                        "Operating cost projections",
                        "Tax analysis including ITC/PTC/depreciation",
                        "Debt sizing and DSCR calculations",
                    ],
                },
                "credit_analysis": {
                    "description": "Credit assessment for the guarantee",
                    "status": "[To be prepared]",
                    "contents": [
                        "Borrower credit history and financial statements",
                        "Counterparty credit analysis",
                        "Collateral description and valuation",
                        "Insurance program description",
                        "Risk factor analysis and mitigants",
                    ],
                },
                "legal_documentation": {
                    "description": "Legal structure and documentation",
                    "status": "[To be prepared]",
                    "contents": [
                        "Corporate structure and organizational documents",
                        "Material project contracts (EPC, O&M, PPA)",
                        "Site control documents (lease/purchase agreements)",
                        "Permits and regulatory approvals",
                        "Title and survey reports",
                    ],
                },
                "independent_engineer_report": {
                    "description": "Third-party technical assessment",
                    "status": "[To be commissioned]",
                    "contents": [
                        "Technology assessment and risk evaluation",
                        "Construction cost and schedule review",
                        "Performance projections review",
                        "O&M plan assessment",
                        "Equipment supplier evaluation",
                    ],
                },
                "market_study": {
                    "description": "Independent market and resource assessment",
                    "status": "[To be commissioned]",
                    "contents": [
                        "Resource assessment (solar, wind, etc.)",
                        "Market price analysis",
                        "Competitive landscape assessment",
                        "Grid interconnection and curtailment analysis",
                    ],
                },
            },
        }

    def _credit_summary(self):
        """Format credit assessment data for LPO requirements."""
        data = {
            "section_title": "Credit Assessment Summary",
            "credit_subsidy_estimation": {
                "description": (
                    "Under the Federal Credit Reform Act, the borrower must pay "
                    "the credit subsidy cost of the loan guarantee, which represents "
                    "the net present value of estimated cash flows from the government's "
                    "perspective."
                ),
                "typical_range": "1% to 5% of the guarantee amount",
                "estimated_guarantee_amount": f"${self.fp.total_project_cost * 0.80:,.0f}",
                "estimated_subsidy_range": {
                    "low": f"${self.fp.total_project_cost * 0.80 * 0.01:,.0f}",
                    "high": f"${self.fp.total_project_cost * 0.80 * 0.05:,.0f}",
                },
            },
        }

        if self.credit_assessment:
            ca = self.credit_assessment
            data["project_credit_metrics"] = {
                "equivalent_rating": ca.credit_rating_equivalent,
                "risk_category": ca.risk_category,
                "probability_of_default": f"{ca.probability_of_default:.2%}",
                "loss_given_default": f"{ca.loss_given_default:.0%}",
                "expected_loss_rate": f"{ca.expected_loss_rate:.2%}",
                "credit_spread": f"{ca.credit_spread_bps} bps",
            }

        return data

    def _environmental_requirements(self):
        return {
            "section_title": "Environmental Review Requirements",
            "description": (
                "DOE must complete a National Environmental Policy Act (NEPA) "
                "review before issuing a loan guarantee. The applicant is "
                "responsible for providing environmental data and supporting "
                "the review process."
            ),
            "nepa_process": {
                "categorical_exclusion": (
                    "May apply to small modifications to existing facilities "
                    "with minimal environmental impact."
                ),
                "environmental_assessment": (
                    "Required for most projects. Results in a Finding of No "
                    "Significant Impact (FONSI) or requirement for an EIS."
                ),
                "environmental_impact_statement": (
                    "Required for projects with potentially significant "
                    "environmental impacts."
                ),
            },
            "required_environmental_data": [
                "Biological resources survey (threatened/endangered species)",
                "Cultural resources survey (Section 106 compliance)",
                "Wetlands delineation",
                "Phase I Environmental Site Assessment",
                "Air quality impact analysis",
                "Water resources assessment",
                "Noise impact assessment",
                "Visual impact assessment",
                "Environmental justice analysis (Executive Order 12898)",
                "Community engagement documentation",
            ],
        }

    def _compliance_requirements(self):
        return {
            "section_title": "Compliance Requirements",
            "requirements": [
                {
                    "requirement": "Davis-Bacon Act",
                    "description": ("Workers on the project must be paid prevailing wages "
                                    "as determined by the Department of Labor."),
                    "applicability": "All construction activities",
                },
                {
                    "requirement": "Buy America / Build America, Buy America Act",
                    "description": ("Iron, steel, manufactured products, and construction "
                                    "materials must be produced in the United States, subject "
                                    "to waivers."),
                    "applicability": "Procurement of materials and equipment",
                },
                {
                    "requirement": "National Environmental Policy Act (NEPA)",
                    "description": "Environmental review must be completed before financial close.",
                    "applicability": "Project-wide",
                },
                {
                    "requirement": "Section 106 (Historic Preservation)",
                    "description": ("Consultation with State Historic Preservation Officer "
                                    "regarding potential impacts to cultural resources."),
                    "applicability": "Project site and surrounding area",
                },
                {
                    "requirement": "Community Benefits Plan",
                    "description": ("DOE requires a plan addressing workforce development, "
                                    "community engagement, and equity considerations."),
                    "applicability": "Project-wide",
                },
                {
                    "requirement": "Reporting Requirements",
                    "description": ("Quarterly construction progress reports and annual "
                                    "operational reports to DOE during the guarantee term."),
                    "applicability": "Construction and operations phases",
                },
            ],
        }

    def _fee_schedule(self):
        guarantee_amount = self.fp.total_project_cost * 0.80
        return {
            "section_title": "Application and Facility Fees",
            "fees": [
                {
                    "fee": "Application Fee (Part I)",
                    "amount": "$75,000",
                    "timing": "Due with Part I submission",
                    "refundable": False,
                },
                {
                    "fee": "Application Fee (Part II)",
                    "amount": "Up to $350,000",
                    "timing": "Due with Part II submission",
                    "refundable": False,
                },
                {
                    "fee": "Credit Subsidy Cost",
                    "amount": f"Estimated ${guarantee_amount * 0.01:,.0f} to ${guarantee_amount * 0.05:,.0f}",
                    "timing": "Due at financial close",
                    "refundable": False,
                },
                {
                    "fee": "Facility Fee",
                    "amount": "Negotiated (typically 25-100 bps annually on outstanding balance)",
                    "timing": "Ongoing during guarantee term",
                    "refundable": False,
                },
                {
                    "fee": "Maintenance Fee",
                    "amount": "Negotiated",
                    "timing": "Annual during guarantee term",
                    "refundable": False,
                },
            ],
            "note": (
                "Fees are subject to change. Applicants should confirm current "
                "fee schedules with the LPO before submission."
            ),
        }

    def _eligibility_assessment(self):
        assessments = []
        tech = self.tp.technology_type

        innovative_techs = [
            "battery_storage", "offshore_wind", "geothermal",
            "solar_plus_storage", "microgrids", "grid_modernization",
        ]
        if tech in innovative_techs:
            assessments.append({
                "criterion": "Innovative Technology",
                "status": "Likely Eligible",
                "detail": (f"{tech.replace('_', ' ').title()} is generally considered to employ "
                           f"new or significantly improved technology for Title XVII purposes."),
            })
        else:
            assessments.append({
                "criterion": "Innovative Technology",
                "status": "Requires Review",
                "detail": (f"Standard {tech.replace('_', ' ')} technology may need to demonstrate "
                           f"a specific innovation element to qualify under Title XVII. "
                           f"Consider how the project's technology differs from commercial "
                           f"technologies currently in service."),
            })

        if self.fp.total_project_cost >= 25_000_000:
            assessments.append({
                "criterion": "Project Scale",
                "status": "Likely Sufficient",
                "detail": f"Project cost of ${self.fp.total_project_cost:,.0f} exceeds typical minimum scale.",
            })
        else:
            assessments.append({
                "criterion": "Project Scale",
                "status": "Below Typical Minimum",
                "detail": ("LPO typically considers larger-scale projects. Smaller projects "
                           "may face higher relative application costs."),
            })

        if self.fp.dscr >= 1.20:
            assessments.append({
                "criterion": "Reasonable Prospect of Repayment",
                "status": "Supported",
                "detail": f"DSCR of {self.fp.dscr:.2f}x indicates sufficient cash flow coverage.",
            })
        else:
            assessments.append({
                "criterion": "Reasonable Prospect of Repayment",
                "status": "Requires Strengthening",
                "detail": "Cash flow coverage may be insufficient to demonstrate reasonable prospect of repayment.",
            })

        return {
            "section_title": "Preliminary Eligibility Assessment",
            "assessments": assessments,
            "disclaimer": (
                "This is a preliminary assessment based on available project data. "
                "Formal eligibility is determined by DOE LPO upon review of the "
                "Part I pre-application. Applicants should engage with LPO staff "
                "for informal guidance before submitting."
            ),
        }

    def _project_description(self):
        tech = self.tp.technology_type.replace("_", " ")
        capacity = self.tp.nameplate_capacity_mw
        return (
            f"Proposed {capacity:.1f} MW {tech} project located in "
            f"{self.params.location_county or '[County]'}, "
            f"{self.params.location_state or '[State]'}. "
            f"The project will generate approximately {self.tp.annual_generation_mwh:,.0f} MWh "
            f"annually with an expected capacity factor of {self.tp.capacity_factor:.1%}. "
            f"{self.params.description or ''}"
        )

    def _innovation_narrative(self):
        tech = self.tp.technology_type
        narratives = {
            "battery_storage": (
                "The project deploys grid-scale energy storage technology that "
                "provides critical grid balancing services and enables higher "
                "penetration of variable renewable energy resources."
            ),
            "offshore_wind": (
                "The project advances offshore wind energy deployment in U.S. waters, "
                "employing technology and installation methods that have limited "
                "commercial deployment domestically."
            ),
            "solar_plus_storage": (
                "The project integrates solar generation with battery storage to "
                "provide dispatchable renewable energy, addressing intermittency "
                "challenges through innovative system design."
            ),
            "geothermal": (
                "The project employs enhanced or advanced geothermal systems that "
                "extend geothermal energy production beyond conventional "
                "hydrothermal resource areas."
            ),
            "microgrids": (
                "The project deploys an advanced microgrid system with islanding "
                "capability, intelligent load management, and integration of "
                "multiple distributed energy resources."
            ),
            "grid_modernization": (
                "The project implements advanced grid technologies including "
                "digital controls, sensors, and communications systems that "
                "significantly improve grid reliability and resilience."
            ),
        }
        return narratives.get(
            tech,
            "[Describe how the project's technology represents a new or "
            "significantly improved technology that is not yet in widespread "
            "commercial use in the United States.]"
        )
