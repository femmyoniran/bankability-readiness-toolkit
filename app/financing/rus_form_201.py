"""
USDA RUS Form 201 loan application data generator.
Produces structured output compatible with the Rural Utilities Service
electric loan program application requirements.

Reference: 7 CFR Part 1710, USDA RUS Bulletin 1710-1
Form: RUS Form 201 -- Loan Application
"""

from datetime import date


class RUSForm201Generator:
    """
    Generates a structured data set compatible with the USDA RUS Form 201
    loan application for rural electric infrastructure projects.
    """

    def __init__(self, project_params, financial_summary=None):
        self.params = project_params
        self.fp = project_params.financial
        self.tp = project_params.technical
        self.financial_summary = financial_summary

    def generate(self):
        """Build the full Form 201 data structure."""
        return {
            "form_metadata": self._form_metadata(),
            "section_a_borrower_info": self._section_a(),
            "section_b_loan_request": self._section_b(),
            "section_c_project_description": self._section_c(),
            "section_d_cost_estimates": self._section_d(),
            "section_e_financial_information": self._section_e(),
            "section_f_economic_feasibility": self._section_f(),
            "section_g_environmental": self._section_g(),
            "section_h_certifications": self._section_h(),
            "supporting_documents": self._supporting_documents(),
            "eligibility_notes": self._eligibility_notes(),
        }

    def _form_metadata(self):
        return {
            "form_number": "RUS Form 201",
            "form_title": "Loan Application",
            "program": "USDA Rural Utilities Service -- Electric Program",
            "regulation_reference": "7 CFR Part 1710",
            "date_prepared": date.today().isoformat(),
            "application_type": "New Loan",
            "loan_type": self._determine_loan_type(),
        }

    def _determine_loan_type(self):
        entity = self.params.entity_type
        if entity == "cooperative":
            return "Federal Financing Bank (FFB) Loan"
        elif entity in ("municipal_utility", "tribal_utility"):
            return "Direct Treasury Rate Loan"
        else:
            return "Hardship Rate Loan" if self.params.is_rural else "Standard Rate Loan"

    def _section_a(self):
        return {
            "section_title": "Section A: Borrower Information",
            "fields": {
                "borrower_name": self.params.project_name or "[Borrower Legal Name]",
                "borrower_type": self.params.entity_type.replace("_", " ").title(),
                "state_of_incorporation": self.params.location_state or "[State]",
                "principal_office_address": "[Street Address]",
                "city": "[City]",
                "state": self.params.location_state or "[State]",
                "county": self.params.location_county or "[County]",
                "zip_code": "[ZIP]",
                "contact_name": "[Contact Name]",
                "contact_title": "[Title]",
                "contact_phone": "[Phone]",
                "contact_email": "[Email]",
                "fiscal_year_end": "December 31",
                "number_of_consumers_served": "[Number]",
                "miles_of_line": "[Miles]",
                "kwh_sold_annually": "[kWh]",
                "peak_demand_kw": "[kW]",
            },
            "instructions": (
                "Complete all fields with current borrower information. "
                "Attach copies of articles of incorporation, bylaws, and "
                "most recent audited financial statements."
            ),
        }

    def _section_b(self):
        loan_amount = self.fp.debt_amount
        return {
            "section_title": "Section B: Loan Request",
            "fields": {
                "loan_amount_requested": f"${loan_amount:,.0f}",
                "loan_amount_numeric": loan_amount,
                "loan_purpose": self._describe_loan_purpose(),
                "loan_term_requested_years": min(self.fp.debt_tenor_years, 35),
                "construction_period_months": self.fp.construction_period_months,
                "estimated_first_advance_date": "[Date]",
                "estimated_completion_date": self.params.cod_target or "[Date]",
                "interest_rate_preference": self._determine_loan_type(),
            },
            "instructions": (
                "Specify the total loan amount requested and detailed purpose. "
                "Loan term may not exceed the useful life of the facilities "
                "being financed, up to a maximum of 35 years."
            ),
        }

    def _describe_loan_purpose(self):
        tech = self.tp.technology_type.replace("_", " ")
        capacity = self.tp.nameplate_capacity_mw
        parts = [
            f"Construction of a {capacity:.1f} MW {tech} facility",
            f"located in {self.params.location_county or '[County]'}, "
            f"{self.params.location_state or '[State]'}.",
        ]
        if self.params.description:
            parts.append(self.params.description)
        return " ".join(parts)

    def _section_c(self):
        return {
            "section_title": "Section C: Description of Proposed Facilities",
            "fields": {
                "project_name": self.params.project_name or "[Project Name]",
                "project_description": self._describe_loan_purpose(),
                "technology_type": self.tp.technology_type.replace("_", " ").title(),
                "nameplate_capacity_mw": self.tp.nameplate_capacity_mw,
                "expected_annual_generation_mwh": self.tp.annual_generation_mwh,
                "capacity_factor": f"{self.tp.capacity_factor:.1%}",
                "interconnection_voltage_kv": self.tp.interconnection_voltage_kv,
                "interconnection_point": "[Substation/Point of Interconnection]",
                "expected_useful_life_years": self.tp.expected_useful_life_years,
                "construction_timeline": f"{self.fp.construction_period_months} months",
                "target_commercial_operation": self.params.cod_target or "[Date]",
                "location_description": (
                    f"{self.params.location_county or '[County]'} County, "
                    f"{self.params.location_state or '[State]'}"
                ),
                "rural_area_served": "Yes" if self.params.is_rural else "To Be Determined",
                "environmental_permits_status": (
                    "Secured" if self.tp.environmental_permits_secured else "In Progress"
                ),
                "site_control_status": (
                    "Secured" if self.tp.site_control_secured else "In Progress"
                ),
            },
            "instructions": (
                "Provide a complete technical description of the proposed "
                "facilities including capacity, location, and timeline. "
                "Attach engineering studies and site plans."
            ),
        }

    def _section_d(self):
        return {
            "section_title": "Section D: Cost Estimates",
            "fields": {
                "total_project_cost": f"${self.fp.total_project_cost:,.0f}",
                "total_project_cost_numeric": self.fp.total_project_cost,
                "cost_breakdown": {
                    "hard_costs": {
                        "label": "Hard Costs (Equipment, Materials, Installation)",
                        "amount": f"${self.fp.total_hard_costs:,.0f}",
                        "amount_numeric": self.fp.total_hard_costs,
                    },
                    "soft_costs": {
                        "label": "Soft Costs (Engineering, Permitting, Legal)",
                        "amount": f"${self.fp.total_soft_costs:,.0f}",
                        "amount_numeric": self.fp.total_soft_costs,
                    },
                    "contingency": {
                        "label": f"Contingency ({self.fp.contingency_percent:.0%})",
                        "amount": f"${self.fp.total_project_cost * self.fp.contingency_percent:,.0f}",
                        "amount_numeric": self.fp.total_project_cost * self.fp.contingency_percent,
                    },
                },
                "funding_sources": {
                    "rus_loan": {
                        "label": "RUS Loan Proceeds",
                        "amount": f"${self.fp.debt_amount:,.0f}",
                        "percent": f"{self.fp.debt_percent:.0%}",
                    },
                    "borrower_equity": {
                        "label": "Borrower Equity Contribution",
                        "amount": f"${self.fp.equity_amount:,.0f}",
                        "percent": f"{self.fp.equity_percent:.0%}",
                    },
                },
                "cost_per_kw": f"${self.fp.total_project_cost / max(self.tp.nameplate_capacity_mw * 1000, 1):,.0f}",
            },
            "instructions": (
                "Provide itemized cost estimates supported by engineering "
                "studies, vendor quotes, or comparable project data. "
                "Include a contingency allowance appropriate for the project stage."
            ),
        }

    def _section_e(self):
        return {
            "section_title": "Section E: Financial Information",
            "fields": {
                "annual_revenue_projection": f"${self.fp.annual_revenue:,.0f}",
                "annual_operating_expenses": f"${self.fp.annual_opex:,.0f}",
                "net_operating_income": f"${self.fp.net_operating_income:,.0f}",
                "annual_debt_service": f"${self.fp.annual_debt_service:,.0f}",
                "debt_service_coverage_ratio": f"{self.fp.dscr:.2f}x",
                "interest_rate_assumed": f"{self.fp.interest_rate:.2%}",
                "loan_term_years": self.fp.debt_tenor_years,
                "revenue_source": self.params.credit.offtake_type.replace("_", " ").title(),
                "offtake_contract_term": f"{self.params.credit.offtake_tenor_years} years",
                "rate_schedule_basis": "[Attach current rate schedules]",
                "current_equity_ratio": f"{1 - self.fp.leverage_ratio:.1%}",
                "times_interest_earned_ratio": (
                    f"{self.fp.net_operating_income / max(self.fp.debt_amount * self.fp.interest_rate, 1):.2f}x"
                ),
            },
            "required_attachments": [
                "Audited financial statements for the past 3 fiscal years",
                "Current year interim financial statements",
                "5-year financial forecast",
                "Current rate schedules and rate study",
                "Power cost study (if applicable)",
                "Load forecast for the service territory",
            ],
            "instructions": (
                "Provide detailed financial data demonstrating the borrower's "
                "ability to repay the requested loan. Include historical "
                "financial performance and forward-looking projections."
            ),
        }

    def _section_f(self):
        data = {
            "section_title": "Section F: Economic Feasibility Study",
            "fields": {
                "cost_benefit_summary": {
                    "total_project_cost": f"${self.fp.total_project_cost:,.0f}",
                    "annual_revenue": f"${self.fp.annual_revenue:,.0f}",
                    "annual_expenses": f"${self.fp.annual_opex:,.0f}",
                    "annual_net_benefit": f"${self.fp.net_operating_income:,.0f}",
                    "simple_payback_years": f"{self.fp.total_project_cost / max(self.fp.net_operating_income, 1):.1f}",
                },
                "rate_impact_analysis": "[To be completed -- projected impact on consumer rates]",
                "alternatives_considered": "[Description of alternatives evaluated]",
                "economic_justification": (
                    f"The proposed {self.tp.technology_type.replace('_', ' ')} project "
                    f"provides {self.tp.annual_generation_mwh:,.0f} MWh of annual generation "
                    f"at a projected cost that supports continued affordable service to "
                    f"the borrower's membership/customer base."
                ),
            },
            "instructions": (
                "Demonstrate that the proposed project is the most "
                "cost-effective means of meeting the identified need. "
                "Include comparison with alternatives and rate impact analysis."
            ),
        }

        if self.financial_summary:
            fs = self.financial_summary
            data["fields"]["detailed_metrics"] = {
                "npv": f"${fs.npv_project:,.0f}",
                "irr": f"{fs.irr_project:.1%}",
                "lcoe": f"${fs.lcoe:.2f}/MWh",
                "lifetime_generation": f"{sum(cf.revenue for cf in fs.annual_cash_flows):,.0f} (total revenue)",
            }

        return data

    def _section_g(self):
        return {
            "section_title": "Section G: Environmental Review",
            "fields": {
                "environmental_review_status": (
                    "Complete" if self.tp.environmental_permits_secured else "Pending"
                ),
                "nepa_classification": "[To be determined by RUS]",
                "environmental_assessment_required": True,
                "protected_species_review": "[Complete/Pending]",
                "cultural_resources_review": "[Complete/Pending]",
                "wetlands_assessment": "[Complete/Pending]",
                "floodplain_assessment": "[Complete/Pending]",
            },
            "regulatory_reference": "7 CFR Part 1970 -- Environmental Policies and Procedures",
            "instructions": (
                "Environmental review must comply with 7 CFR Part 1970. "
                "RUS will determine the appropriate level of environmental "
                "review (categorical exclusion, environmental assessment, or EIS) "
                "upon receipt of the application."
            ),
        }

    def _section_h(self):
        return {
            "section_title": "Section H: Certifications and Signatures",
            "certifications": [
                "The borrower certifies all information is true and complete.",
                "The borrower is not delinquent on any federal debt.",
                "The borrower is in compliance with all existing RUS loan covenants.",
                "The borrower has not been debarred or suspended from federal programs.",
                "The project serves consumers in an eligible rural area.",
                "Equal opportunity and civil rights compliance is maintained.",
            ],
            "required_signatures": [
                {"role": "General Manager / CEO", "name": "[Name]", "date": "[Date]"},
                {"role": "Board President / Chair", "name": "[Name]", "date": "[Date]"},
                {"role": "Board Secretary", "name": "[Name]", "date": "[Date]"},
            ],
            "board_resolution": (
                "Board resolution authorizing the loan application must be "
                "attached, including specific authorization for the amount "
                "requested and designation of authorized signatories."
            ),
        }

    def _supporting_documents(self):
        return {
            "section_title": "Required Supporting Documents",
            "checklist": [
                {"document": "Board resolution authorizing loan application", "status": "[Pending]"},
                {"document": "Articles of incorporation and bylaws", "status": "[Pending]"},
                {"document": "Audited financial statements (3 years)", "status": "[Pending]"},
                {"document": "Current year interim financial statements", "status": "[Pending]"},
                {"document": "5-year financial forecast (CFC/NRECA format)", "status": "[Pending]"},
                {"document": "Load forecast and power requirements study", "status": "[Pending]"},
                {"document": "Engineering feasibility study", "status": "[Pending]"},
                {"document": "Cost estimates with supporting documentation", "status": "[Pending]"},
                {"document": "Environmental report (ER)", "status": "[Pending]"},
                {"document": "Maps showing project location and service area", "status": "[Pending]"},
                {"document": "Interconnection study/agreement", "status": "[Pending]"},
                {"document": "Power purchase agreement or rate schedules", "status": "[Pending]"},
                {"document": "Insurance certificates", "status": "[Pending]"},
                {"document": "Existing mortgage/loan agreements", "status": "[Pending]"},
                {"document": "Title search for real property", "status": "[Pending]"},
            ],
        }

    def _eligibility_notes(self):
        notes = []
        if not self.params.is_rural:
            notes.append(
                "IMPORTANT: RUS eligibility requires the project to serve consumers "
                "in an eligible rural area as defined by USDA. Verify eligibility "
                "using the USDA Rural Development eligibility maps before proceeding."
            )
        if self.params.entity_type not in ("cooperative", "municipal_utility", "tribal_utility", "state_authority"):
            notes.append(
                "IMPORTANT: The borrower entity type may not be eligible for RUS "
                "electric program loans. Eligible borrowers typically include "
                "electric cooperatives, public utility districts, and tribal utilities."
            )
        if self.fp.dscr < 1.0:
            notes.append(
                "WARNING: Current financial projections show a DSCR below 1.0x, "
                "indicating insufficient cash flow to cover debt service. This "
                "would not meet RUS lending standards."
            )
        notes.append(
            "This output is generated as a data template to assist in preparing "
            "a RUS Form 201 application. It does not constitute a completed "
            "application and should be reviewed by legal counsel and the borrower's "
            "RUS General Field Representative before submission."
        )
        return notes
