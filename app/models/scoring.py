"""
Bankability scoring engine.
Computes a composite bankability readiness score (0-100) from weighted
sub-scores across five assessment dimensions: Technology, Financial,
Credit Risk, Project Structure, and Market/Resource.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from app.models.financial import FinancialModel
from app.models.credit_risk import CreditRiskModel


SCORE_THRESHOLDS = {
    "Investment Grade": {"min": 80, "color": "#1a7a3a", "label": "Strong bankability"},
    "Near Investment Grade": {"min": 65, "color": "#2d8f4e", "label": "Adequate with conditions"},
    "Sub-Investment Grade": {"min": 50, "color": "#b8860b", "label": "Requires significant enhancement"},
    "Speculative": {"min": 35, "color": "#cc6600", "label": "Major structural gaps"},
    "Pre-Bankable": {"min": 0, "color": "#b22222", "label": "Not ready for financing"},
}


@dataclass
class SubScore:
    category: str
    score: float
    weight: float
    weighted_score: float
    components: List[Dict] = field(default_factory=list)
    commentary: str = ""


@dataclass
class BankabilityResult:
    overall_score: float = 0.0
    grade: str = ""
    grade_label: str = ""
    grade_color: str = ""
    sub_scores: List[SubScore] = field(default_factory=list)
    financial_summary: object = None
    credit_assessment: object = None
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    rus_eligibility: Dict = field(default_factory=dict)
    lpo_eligibility: Dict = field(default_factory=dict)

    def to_dict(self):
        result = {
            "overall_score": round(self.overall_score, 1),
            "grade": self.grade,
            "grade_label": self.grade_label,
            "grade_color": self.grade_color,
            "sub_scores": [],
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "recommendations": self.recommendations,
            "rus_eligibility": self.rus_eligibility,
            "lpo_eligibility": self.lpo_eligibility,
        }
        for ss in self.sub_scores:
            result["sub_scores"].append({
                "category": ss.category,
                "score": round(ss.score, 1),
                "weight": ss.weight,
                "weighted_score": round(ss.weighted_score, 1),
                "commentary": ss.commentary,
                "components": ss.components,
            })

        if self.financial_summary:
            fs = self.financial_summary
            result["financial_metrics"] = {
                "npv_project": round(fs.npv_project, 0),
                "npv_equity": round(fs.npv_equity, 0),
                "irr_project": round(fs.irr_project * 100, 2),
                "irr_equity": round(fs.irr_equity * 100, 2),
                "lcoe": round(fs.lcoe, 2),
                "payback_years": round(fs.payback_years, 1),
                "average_dscr": round(fs.average_dscr, 2),
                "minimum_dscr": round(fs.minimum_dscr, 2),
                "debt_yield": round(fs.debt_yield * 100, 2),
                "equity_multiple": round(fs.equity_multiple, 2),
            }
            result["cash_flows"] = []
            for cf in fs.annual_cash_flows:
                result["cash_flows"].append({
                    "year": cf.year,
                    "revenue": round(cf.revenue, 0),
                    "opex": round(cf.opex, 0),
                    "noi": round(cf.net_operating_income, 0),
                    "debt_service": round(cf.debt_service, 0),
                    "dscr": round(cf.dscr, 2) if cf.dscr != float("inf") else 999.99,
                    "free_cash_flow": round(cf.free_cash_flow_equity, 0),
                    "cumulative_cf": round(cf.cumulative_cash_flow, 0),
                })

        if self.credit_assessment:
            ca = self.credit_assessment
            result["credit_metrics"] = {
                "probability_of_default": round(ca.probability_of_default * 10000, 1),
                "loss_given_default": round(ca.loss_given_default * 100, 1),
                "expected_loss": round(ca.expected_loss, 0),
                "expected_loss_rate_bps": round(ca.expected_loss_rate * 10000, 1),
                "equivalent_rating": ca.credit_rating_equivalent,
                "risk_category": ca.risk_category,
                "credit_spread_bps": ca.credit_spread_bps,
                "overall_credit_score": round(ca.overall_credit_score, 1),
                "risk_factors": ca.risk_factors,
                "mitigants": ca.mitigants,
            }

        return result


class BankabilityScorer:
    """
    Orchestrates the bankability assessment by computing sub-scores across
    all five dimensions and producing a weighted composite score with
    detailed narrative output.
    """

    WEIGHTS = {
        "Technology & Performance": 0.20,
        "Financial Strength": 0.25,
        "Credit & Counterparty": 0.20,
        "Project Structure": 0.20,
        "Market & Resource": 0.15,
    }

    def __init__(self, project_params):
        self.params = project_params
        self.financial_model = FinancialModel(project_params)
        self.credit_model = CreditRiskModel(project_params)

    def score(self):
        """Run the complete bankability assessment."""
        result = BankabilityResult()

        financial_summary = self.financial_model.build_pro_forma()
        credit_assessment = self.credit_model.assess()

        result.financial_summary = financial_summary
        result.credit_assessment = credit_assessment

        # Technology score
        tech_raw = self.params.technical.efficiency_score()
        tech_sub = SubScore(
            category="Technology & Performance",
            score=tech_raw,
            weight=self.WEIGHTS["Technology & Performance"],
            weighted_score=tech_raw * self.WEIGHTS["Technology & Performance"],
        )
        tech_sub.components = self._technology_components()
        tech_sub.commentary = self._technology_commentary(tech_raw)
        result.sub_scores.append(tech_sub)

        # Financial score
        fin_raw = self.financial_model.financial_strength_score(financial_summary)
        fin_sub = SubScore(
            category="Financial Strength",
            score=fin_raw,
            weight=self.WEIGHTS["Financial Strength"],
            weighted_score=fin_raw * self.WEIGHTS["Financial Strength"],
        )
        fin_sub.components = self._financial_components(financial_summary)
        fin_sub.commentary = self._financial_commentary(financial_summary, fin_raw)
        result.sub_scores.append(fin_sub)

        # Credit score
        credit_raw = credit_assessment.overall_credit_score
        credit_sub = SubScore(
            category="Credit & Counterparty",
            score=credit_raw,
            weight=self.WEIGHTS["Credit & Counterparty"],
            weighted_score=credit_raw * self.WEIGHTS["Credit & Counterparty"],
        )
        credit_sub.components = self._credit_components(credit_assessment)
        credit_sub.commentary = self._credit_commentary(credit_assessment, credit_raw)
        result.sub_scores.append(credit_sub)

        # Structure score
        struct_raw = self.params.structure.structure_score()
        struct_sub = SubScore(
            category="Project Structure",
            score=struct_raw,
            weight=self.WEIGHTS["Project Structure"],
            weighted_score=struct_raw * self.WEIGHTS["Project Structure"],
        )
        struct_sub.components = self._structure_components()
        struct_sub.commentary = self._structure_commentary(struct_raw)
        result.sub_scores.append(struct_sub)

        # Market score
        market_raw = self.params.market.market_score()
        market_sub = SubScore(
            category="Market & Resource",
            score=market_raw,
            weight=self.WEIGHTS["Market & Resource"],
            weighted_score=market_raw * self.WEIGHTS["Market & Resource"],
        )
        market_sub.components = self._market_components()
        market_sub.commentary = self._market_commentary(market_raw)
        result.sub_scores.append(market_sub)

        result.overall_score = sum(ss.weighted_score for ss in result.sub_scores)

        for grade, info in SCORE_THRESHOLDS.items():
            if result.overall_score >= info["min"]:
                result.grade = grade
                result.grade_label = info["label"]
                result.grade_color = info["color"]
                break

        result.strengths = self._identify_strengths(result)
        result.weaknesses = self._identify_weaknesses(result)
        result.recommendations = self._generate_recommendations(result)
        result.rus_eligibility = self._check_rus_eligibility()
        result.lpo_eligibility = self._check_lpo_eligibility()

        return result

    def _technology_components(self):
        tp = self.params.technical
        return [
            {"name": "Technology Type", "value": tp.technology_type.replace("_", " ").title()},
            {"name": "Capacity", "value": f"{tp.nameplate_capacity_mw:.1f} MW"},
            {"name": "Capacity Factor", "value": f"{tp.capacity_factor:.1%}"},
            {"name": "TRL", "value": f"{tp.technology_readiness_level}/9"},
            {"name": "Availability", "value": f"{tp.availability_factor:.1%}"},
            {"name": "Permits Secured", "value": "Yes" if tp.environmental_permits_secured else "No"},
            {"name": "Site Control", "value": "Yes" if tp.site_control_secured else "No"},
        ]

    def _financial_components(self, fs):
        return [
            {"name": "Project IRR", "value": f"{fs.irr_project:.1%}"},
            {"name": "Equity IRR", "value": f"{fs.irr_equity:.1%}"},
            {"name": "NPV (Project)", "value": f"${fs.npv_project:,.0f}"},
            {"name": "Min DSCR", "value": f"{fs.minimum_dscr:.2f}x"},
            {"name": "Avg DSCR", "value": f"{fs.average_dscr:.2f}x"},
            {"name": "LCOE", "value": f"${fs.lcoe:.2f}/MWh"},
            {"name": "Payback", "value": f"{fs.payback_years:.1f} years"},
            {"name": "Debt Yield", "value": f"{fs.debt_yield:.1%}"},
            {"name": "Equity Multiple", "value": f"{fs.equity_multiple:.2f}x"},
        ]

    def _credit_components(self, ca):
        return [
            {"name": "Equivalent Rating", "value": ca.credit_rating_equivalent},
            {"name": "Risk Category", "value": ca.risk_category},
            {"name": "PD", "value": f"{ca.probability_of_default:.2%}"},
            {"name": "LGD", "value": f"{ca.loss_given_default:.0%}"},
            {"name": "Expected Loss", "value": f"${ca.expected_loss:,.0f}"},
            {"name": "Credit Spread", "value": f"{ca.credit_spread_bps} bps"},
        ]

    def _structure_components(self):
        sp = self.params.structure
        return [
            {"name": "EPC Type", "value": sp.epc_contract_type.replace("_", " ").title()},
            {"name": "Contractor", "value": sp.epc_contractor_experience.title()},
            {"name": "Performance Guarantee", "value": "Yes" if sp.performance_guarantee else "No"},
            {"name": "Completion Guarantee", "value": "Yes" if sp.completion_guarantee else "No"},
            {"name": "Insurance", "value": sp.insurance_coverage.title()},
            {"name": "DSRA Funded", "value": "Yes" if sp.reserve_accounts_funded else "No"},
            {"name": "DSRA Months", "value": str(sp.debt_service_reserve_months)},
        ]

    def _market_components(self):
        mp = self.params.market
        return [
            {"name": "Resource Quality", "value": mp.resource_quality.title()},
            {"name": "Assessment Basis", "value": mp.resource_assessment_confidence.upper()},
            {"name": "Independent Assessment", "value": "Yes" if mp.independent_resource_assessment else "No"},
            {"name": "Interconnection", "value": mp.interconnection_certainty.title()},
            {"name": "Grid Congestion", "value": mp.grid_congestion_risk.title()},
            {"name": "Curtailment History", "value": f"{mp.curtailment_history_percent:.1%}"},
        ]

    def _technology_commentary(self, score):
        if score >= 80:
            return ("Technology profile is well-suited for project finance. Mature technology with "
                    "strong performance track record reduces execution risk.")
        elif score >= 60:
            return ("Technology assessment is adequate for financing consideration. Some areas "
                    "could be strengthened to improve lender confidence.")
        elif score >= 40:
            return ("Technology profile presents moderate risk. Additional performance data, "
                    "permitting progress, or site control would improve the assessment.")
        else:
            return ("Technology readiness is below the threshold for conventional project finance. "
                    "Significant development milestones remain before bankability is achievable.")

    def _financial_commentary(self, fs, score):
        parts = []
        if fs.minimum_dscr >= 1.40:
            parts.append(f"Debt service coverage of {fs.minimum_dscr:.2f}x meets or exceeds "
                         f"typical lender requirements.")
        elif fs.minimum_dscr >= 1.20:
            parts.append(f"Minimum DSCR of {fs.minimum_dscr:.2f}x is within an acceptable range "
                         f"but leaves limited cushion for downside scenarios.")
        else:
            parts.append(f"Minimum DSCR of {fs.minimum_dscr:.2f}x is below the 1.20x floor "
                         f"typically required for infrastructure debt.")

        if fs.irr_project >= 0.10:
            parts.append(f"Project IRR of {fs.irr_project:.1%} supports equity investment "
                         f"at current return expectations.")
        elif fs.irr_project >= 0.06:
            parts.append(f"Project IRR of {fs.irr_project:.1%} may be tight depending "
                         f"on equity investor return thresholds.")
        else:
            parts.append(f"Project IRR of {fs.irr_project:.1%} is below typical minimum "
                         f"equity return requirements.")

        return " ".join(parts)

    def _credit_commentary(self, ca, score):
        parts = [f"Overall credit profile maps to an equivalent {ca.credit_rating_equivalent} rating "
                 f"with a {ca.risk_category.lower()} risk classification."]

        if ca.risk_factors:
            high_risk = [rf for rf in ca.risk_factors if rf["severity"] == "high"]
            if high_risk:
                factors = ", ".join(rf["factor"].lower() for rf in high_risk[:3])
                parts.append(f"Key risk factors include {factors}.")

        if ca.mitigants:
            strong = [m for m in ca.mitigants if m["strength"] == "strong"]
            if strong:
                mitigs = ", ".join(m["mitigant"].lower() for m in strong[:3])
                parts.append(f"These are partially offset by {mitigs}.")

        return " ".join(parts)

    def _structure_commentary(self, score):
        if score >= 75:
            return ("Project structure includes strong contractual protections and risk allocation "
                    "appropriate for project finance.")
        elif score >= 55:
            return ("Structural elements are broadly adequate but would benefit from additional "
                    "protections such as funded reserves or enhanced guarantees.")
        elif score >= 35:
            return ("Project structure has notable gaps that would need to be addressed during "
                    "financing negotiations.")
        else:
            return ("Structural framework requires substantial development before the project "
                    "is ready for lender due diligence.")

    def _market_commentary(self, score):
        if score >= 75:
            return ("Market and resource conditions are favorable, with strong resource assessment, "
                    "clear interconnection path, and manageable congestion risk.")
        elif score >= 55:
            return ("Market environment is adequate for project viability. An independent resource "
                    "assessment and interconnection progress would strengthen the profile.")
        elif score >= 35:
            return ("Market conditions present material risk. Resource quality, interconnection "
                    "certainty, or curtailment exposure may limit financing options.")
        else:
            return ("Market and resource fundamentals are weak. Substantial de-risking is needed "
                    "before lenders will consider the project bankable.")

    def _identify_strengths(self, result):
        strengths = []
        for ss in result.sub_scores:
            if ss.score >= 75:
                strengths.append(f"Strong {ss.category.lower()} profile (score: {ss.score:.0f}/100).")
        fs = result.financial_summary
        if fs and fs.minimum_dscr >= 1.40:
            strengths.append(f"Debt coverage of {fs.minimum_dscr:.2f}x exceeds typical lender minimums.")
        if fs and fs.irr_project >= 0.10:
            strengths.append(f"Project returns ({fs.irr_project:.1%} IRR) support equity investment.")
        if self.params.technical.environmental_permits_secured and self.params.technical.site_control_secured:
            strengths.append("Key development milestones (permits, site control) have been achieved.")
        if self.params.credit.offtake_type in ("ppa_fixed", "regulated_rate"):
            strengths.append("Contracted revenue provides cash flow predictability.")
        return strengths

    def _identify_weaknesses(self, result):
        weaknesses = []
        for ss in result.sub_scores:
            if ss.score < 50:
                weaknesses.append(f"Weak {ss.category.lower()} profile (score: {ss.score:.0f}/100) "
                                  f"requires attention.")
        fs = result.financial_summary
        if fs and fs.minimum_dscr < 1.20:
            weaknesses.append(f"DSCR of {fs.minimum_dscr:.2f}x is below the 1.20x minimum for most lenders.")
        if fs and fs.irr_project < 0.06:
            weaknesses.append(f"Project IRR of {fs.irr_project:.1%} may not attract equity capital.")
        ca = result.credit_assessment
        if ca and ca.risk_category in ("High", "Very High"):
            weaknesses.append(f"Credit risk category of '{ca.risk_category}' limits access to "
                              f"low-cost financing.")
        return weaknesses

    def _generate_recommendations(self, result):
        recs = []
        fs = result.financial_summary
        ca = result.credit_assessment

        if fs and fs.minimum_dscr < 1.40:
            recs.append("Consider restructuring the capital stack to improve DSCR -- options include "
                        "increasing equity contribution, extending debt tenor, or reducing operating costs.")

        if not self.params.structure.reserve_accounts_funded:
            recs.append("Fund a debt service reserve account (minimum 6 months of debt service) to "
                        "provide liquidity cushion and satisfy standard lender requirements.")

        if not self.params.technical.environmental_permits_secured:
            recs.append("Secure all required environmental permits before approaching lenders to "
                        "eliminate permitting risk from the financing discussion.")

        if self.params.market.interconnection_certainty in ("low", "speculative"):
            recs.append("Advance interconnection studies and secure an interconnection agreement "
                        "to de-risk the grid connection timeline.")

        if not self.params.market.independent_resource_assessment:
            recs.append("Commission an independent resource assessment to provide lenders with "
                        "third-party validation of expected energy production.")

        if self.params.credit.offtake_type == "merchant":
            recs.append("Secure a long-term offtake agreement (PPA or tolling) to provide "
                        "contracted revenue certainty required for project finance.")

        if ca and ca.probability_of_default > 0.01:
            recs.append("Explore credit enhancement mechanisms such as letters of credit, "
                        "guarantees, or credit wraps to improve the credit profile.")

        if self.params.structure.epc_contract_type != "fixed_price_turnkey":
            recs.append("Negotiate a fixed-price turnkey EPC contract to transfer construction "
                        "cost and schedule risk to an experienced contractor.")

        if self.params.is_rural and result.rus_eligibility.get("eligible"):
            recs.append("Project appears eligible for USDA RUS financing. Consider preparing "
                        "a Form 201 application to access below-market interest rates.")

        if result.lpo_eligibility.get("potentially_eligible"):
            recs.append("Project may qualify for DOE LPO Title XVII loan guarantee. "
                        "Evaluate whether the technology meets the innovation threshold.")

        return recs

    def _check_rus_eligibility(self):
        """Evaluate preliminary eligibility for USDA Rural Utilities Service financing."""
        eligible = True
        criteria = []

        if self.params.is_rural:
            criteria.append({"criterion": "Rural location", "met": True,
                             "detail": "Project is located in a rural area."})
        else:
            eligible = False
            criteria.append({"criterion": "Rural location", "met": False,
                             "detail": "RUS financing requires the project to serve a rural area. "
                                       "Review USDA rural designation maps for eligibility."})

        eligible_entities = ["cooperative", "municipal_utility", "tribal_utility", "state_authority"]
        if self.params.entity_type in eligible_entities:
            criteria.append({"criterion": "Eligible entity type", "met": True,
                             "detail": f"{self.params.entity_type.replace('_', ' ').title()} is an eligible borrower type."})
        else:
            eligible = False
            criteria.append({"criterion": "Eligible entity type", "met": False,
                             "detail": "RUS typically finances cooperatives, municipal utilities, and tribal utilities."})

        if self.params.financial.total_project_cost > 0:
            criteria.append({"criterion": "Project cost defined", "met": True,
                             "detail": f"Total project cost of ${self.params.financial.total_project_cost:,.0f}."})
        else:
            eligible = False
            criteria.append({"criterion": "Project cost defined", "met": False,
                             "detail": "A defined project cost is required for RUS application."})

        if self.params.financial.dscr >= 1.0:
            criteria.append({"criterion": "Financial feasibility", "met": True,
                             "detail": f"DSCR of {self.params.financial.dscr:.2f}x indicates "
                                       f"sufficient revenue coverage."})
        else:
            eligible = False
            criteria.append({"criterion": "Financial feasibility", "met": False,
                             "detail": "Project must demonstrate ability to repay debt from operations."})

        return {
            "eligible": eligible,
            "criteria": criteria,
            "program": "USDA RUS Electric Program",
            "form": "RUS Form 201 - Loan Application",
            "max_term_years": 35,
            "notes": "Preliminary assessment only. Formal eligibility is determined by RUS upon application review.",
        }

    def _check_lpo_eligibility(self):
        """Evaluate preliminary eligibility for DOE Loan Programs Office Title XVII guarantee."""
        potentially_eligible = True
        criteria = []

        innovative_technologies = [
            "battery_storage", "offshore_wind", "geothermal", "solar_plus_storage",
            "microgrids", "grid_modernization",
        ]
        if self.params.technical.technology_type in innovative_technologies:
            criteria.append({"criterion": "Innovative technology", "met": True,
                             "detail": f"{self.params.technical.technology_type.replace('_', ' ').title()} "
                                       f"may qualify as an innovative energy technology."})
        else:
            criteria.append({"criterion": "Innovative technology", "met": "Uncertain",
                             "detail": "Technology must employ a new or significantly improved technology "
                                       "compared to commercial technologies in service."})

        if self.params.financial.total_project_cost >= 25_000_000:
            criteria.append({"criterion": "Minimum project size", "met": True,
                             "detail": "Project size exceeds typical minimum for LPO consideration."})
        else:
            potentially_eligible = False
            criteria.append({"criterion": "Minimum project size", "met": False,
                             "detail": "LPO generally considers projects with costs of $25M or more."})

        criteria.append({"criterion": "Environmental review", "met": "Required",
                         "detail": "NEPA environmental review will be required as part of the application."})

        if self.params.financial.dscr >= 1.20:
            criteria.append({"criterion": "Credit assessment", "met": True,
                             "detail": f"DSCR of {self.params.financial.dscr:.2f}x supports "
                                       f"reasonable prospect of repayment."})
        else:
            potentially_eligible = False
            criteria.append({"criterion": "Credit assessment", "met": False,
                             "detail": "Applicant must demonstrate reasonable prospect of repayment."})

        return {
            "potentially_eligible": potentially_eligible,
            "criteria": criteria,
            "program": "DOE Loan Programs Office - Title XVII",
            "max_guarantee": "Up to 80% of project costs",
            "credit_subsidy": "Borrower pays credit subsidy cost (typically 1-5% of guarantee amount)",
            "notes": "Preliminary assessment only. Formal eligibility requires Part I and Part II "
                     "application review by LPO.",
        }
