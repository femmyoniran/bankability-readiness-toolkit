"""
Credit risk assessment for energy infrastructure projects.
Evaluates counterparty risk, probability of default, loss given default,
and overall credit exposure to determine lending risk.
"""

from dataclasses import dataclass
from typing import Optional


RATING_PD_MAP = {
    "AAA": 0.0001, "AA+": 0.0002, "AA": 0.0003, "AA-": 0.0005,
    "A+": 0.0008, "A": 0.0010, "A-": 0.0015,
    "BBB+": 0.0025, "BBB": 0.0040, "BBB-": 0.0070,
    "BB+": 0.0120, "BB": 0.0200, "BB-": 0.0350,
    "B+": 0.0550, "B": 0.0800, "B-": 0.1200,
    "CCC": 0.2000, "CC": 0.3500, "C": 0.5000, "D": 1.0000,
    "unrated": 0.0500,
}

ENTITY_LGD_MAP = {
    "investor_owned_utility": 0.35,
    "municipal_utility": 0.30,
    "cooperative": 0.35,
    "independent_power_producer": 0.45,
    "community_choice_aggregator": 0.50,
    "tribal_utility": 0.40,
    "state_authority": 0.25,
}


@dataclass
class CreditAssessment:
    probability_of_default: float = 0.0
    loss_given_default: float = 0.0
    exposure_at_default: float = 0.0
    expected_loss: float = 0.0
    expected_loss_rate: float = 0.0
    credit_rating_equivalent: str = ""
    risk_category: str = ""
    credit_spread_bps: int = 0
    counterparty_risk_score: float = 0.0
    structural_risk_score: float = 0.0
    market_risk_score: float = 0.0
    overall_credit_score: float = 0.0
    risk_factors: list = None
    mitigants: list = None

    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.mitigants is None:
            self.mitigants = []


class CreditRiskModel:
    """
    Evaluates the credit risk of an energy infrastructure project from a
    lender's perspective. Produces expected loss estimates, risk scores,
    and identifies key risk factors and mitigants.
    """

    CREDIT_SPREAD_TABLE = {
        "AAA": 20, "AA+": 35, "AA": 50, "AA-": 65,
        "A+": 80, "A": 100, "A-": 120,
        "BBB+": 150, "BBB": 180, "BBB-": 220,
        "BB+": 300, "BB": 400, "BB-": 500,
        "B+": 600, "B": 750, "B-": 900,
        "CCC": 1200, "CC": 1500, "C": 2000,
    }

    def __init__(self, project_params):
        self.params = project_params
        self.cp = project_params.credit
        self.fp = project_params.financial
        self.sp = project_params.structure
        self.mp = project_params.market

    def assess(self):
        """Run the full credit risk assessment."""
        assessment = CreditAssessment()

        assessment.probability_of_default = self._compute_adjusted_pd()
        assessment.loss_given_default = self._compute_lgd()
        assessment.exposure_at_default = self.fp.debt_amount
        assessment.expected_loss = (
            assessment.probability_of_default
            * assessment.loss_given_default
            * assessment.exposure_at_default
        )

        if assessment.exposure_at_default > 0:
            assessment.expected_loss_rate = assessment.expected_loss / assessment.exposure_at_default
        else:
            assessment.expected_loss_rate = 0.0

        assessment.credit_rating_equivalent = self._derive_equivalent_rating(assessment.probability_of_default)
        assessment.risk_category = self._categorize_risk(assessment.probability_of_default)
        assessment.credit_spread_bps = self.CREDIT_SPREAD_TABLE.get(
            assessment.credit_rating_equivalent, 300
        )

        assessment.counterparty_risk_score = self._score_counterparty_risk()
        assessment.structural_risk_score = self._score_structural_risk()
        assessment.market_risk_score = self._score_market_risk()
        assessment.overall_credit_score = (
            assessment.counterparty_risk_score * 0.40
            + assessment.structural_risk_score * 0.30
            + assessment.market_risk_score * 0.30
        )

        assessment.risk_factors = self._identify_risk_factors()
        assessment.mitigants = self._identify_mitigants()

        return assessment

    def _compute_adjusted_pd(self):
        """Calculate adjusted probability of default using base PD and modifiers."""
        base_pd = RATING_PD_MAP.get(self.cp.offtaker_credit_rating, 0.05)

        # Tenor adjustment: longer contracts reduce refinancing/renewal risk
        if self.cp.offtake_tenor_years >= 20:
            tenor_adj = 0.85
        elif self.cp.offtake_tenor_years >= 15:
            tenor_adj = 0.90
        elif self.cp.offtake_tenor_years >= 10:
            tenor_adj = 1.0
        elif self.cp.offtake_tenor_years >= 5:
            tenor_adj = 1.15
        else:
            tenor_adj = 1.40

        # Contract type adjustment
        contract_adj = {
            "ppa_fixed": 0.85, "ppa_indexed": 0.95, "regulated_rate": 0.80,
            "tolling_agreement": 1.0, "capacity_contract": 1.05,
            "bundled_rate": 0.90, "merchant": 1.60,
        }
        ct_adj = contract_adj.get(self.cp.offtake_type, 1.0)

        # DSCR adjustment
        dscr = self.fp.dscr
        if dscr >= 1.60:
            dscr_adj = 0.70
        elif dscr >= 1.40:
            dscr_adj = 0.80
        elif dscr >= 1.25:
            dscr_adj = 0.90
        elif dscr >= 1.10:
            dscr_adj = 1.0
        else:
            dscr_adj = 1.30

        # Entity type adjustment
        entity_adj = {
            "investor_owned_utility": 0.90, "municipal_utility": 0.85,
            "cooperative": 0.95, "independent_power_producer": 1.10,
            "community_choice_aggregator": 1.15, "tribal_utility": 1.05,
            "state_authority": 0.80,
        }
        ent_adj = entity_adj.get(self.cp.offtaker_entity_type, 1.0)

        # Concentration adjustment
        if self.cp.revenue_concentration_percent >= 0.90:
            conc_adj = 1.10
        elif self.cp.revenue_concentration_percent >= 0.70:
            conc_adj = 1.05
        else:
            conc_adj = 0.95

        adjusted_pd = base_pd * tenor_adj * ct_adj * dscr_adj * ent_adj * conc_adj
        return min(max(adjusted_pd, 0.0001), 1.0)

    def _compute_lgd(self):
        """Estimate loss given default based on entity type and structural protections."""
        base_lgd = ENTITY_LGD_MAP.get(self.cp.offtaker_entity_type, 0.45)

        if self.sp.completion_guarantee:
            base_lgd *= 0.90

        if self.sp.reserve_accounts_funded:
            reserve_months = self.sp.debt_service_reserve_months
            reserve_adjustment = max(0, 1.0 - reserve_months * 0.02)
            base_lgd *= reserve_adjustment

        if self.cp.has_credit_support:
            base_lgd *= 0.85

        if self.sp.step_in_rights:
            base_lgd *= 0.92

        if self.sp.insurance_coverage == "comprehensive":
            base_lgd *= 0.90
        elif self.sp.insurance_coverage == "standard":
            base_lgd *= 0.95

        return min(max(base_lgd, 0.05), 0.95)

    def _derive_equivalent_rating(self, pd):
        """Map a probability of default to an equivalent credit rating."""
        rating_thresholds = [
            (0.0002, "AAA"), (0.0004, "AA+"), (0.0006, "AA"), (0.0010, "AA-"),
            (0.0015, "A+"), (0.0025, "A"), (0.0040, "A-"),
            (0.0060, "BBB+"), (0.0080, "BBB"), (0.0120, "BBB-"),
            (0.0200, "BB+"), (0.0350, "BB"), (0.0550, "BB-"),
            (0.0800, "B+"), (0.1200, "B"), (0.2000, "B-"),
            (0.3500, "CCC"), (0.5000, "CC"),
        ]
        for threshold, rating in rating_thresholds:
            if pd <= threshold:
                return rating
        return "C"

    def _categorize_risk(self, pd):
        if pd <= 0.0010:
            return "Minimal"
        elif pd <= 0.0040:
            return "Low"
        elif pd <= 0.0120:
            return "Moderate"
        elif pd <= 0.0350:
            return "Elevated"
        elif pd <= 0.0800:
            return "High"
        else:
            return "Very High"

    def _score_counterparty_risk(self):
        """Score counterparty risk on 0-100 (100 = lowest risk)."""
        return self.cp.credit_quality_score()

    def _score_structural_risk(self):
        """Score structural risk protection on 0-100."""
        return self.sp.structure_score()

    def _score_market_risk(self):
        """Score market/resource risk on 0-100."""
        return self.mp.market_score()

    def _identify_risk_factors(self):
        """Identify and list key risk factors for the project."""
        factors = []

        if self.fp.dscr < 1.20:
            factors.append({
                "category": "Financial",
                "factor": "Below-target debt service coverage",
                "severity": "high",
                "detail": f"DSCR of {self.fp.dscr:.2f} is below the 1.20x minimum threshold "
                          f"typically required by infrastructure lenders.",
            })

        if self.fp.leverage_ratio > 0.80:
            factors.append({
                "category": "Financial",
                "factor": "High leverage ratio",
                "severity": "medium",
                "detail": f"Debt-to-total-capital of {self.fp.leverage_ratio:.0%} exceeds "
                          f"the 80% level that triggers additional lender scrutiny.",
            })

        pd = RATING_PD_MAP.get(self.cp.offtaker_credit_rating, 0.05)
        if pd >= 0.02:
            factors.append({
                "category": "Credit",
                "factor": "Sub-investment-grade offtaker",
                "severity": "high",
                "detail": f"Offtaker rated {self.cp.offtaker_credit_rating}, which is below "
                          f"investment grade and may limit financing options.",
            })

        if self.cp.offtake_type == "merchant":
            factors.append({
                "category": "Revenue",
                "factor": "Merchant exposure",
                "severity": "high",
                "detail": "Project lacks a long-term contracted revenue stream, exposing "
                          "cash flows to market price volatility.",
            })

        if self.cp.offtake_tenor_years < self.fp.debt_tenor_years:
            factors.append({
                "category": "Revenue",
                "factor": "Contract-tenor mismatch",
                "severity": "medium",
                "detail": f"Offtake contract ({self.cp.offtake_tenor_years} years) expires before "
                          f"debt maturity ({self.fp.debt_tenor_years} years), creating recontracting risk.",
            })

        if self.cp.revenue_concentration_percent > 0.80 and self.cp.counterparty_count <= 1:
            factors.append({
                "category": "Credit",
                "factor": "Revenue concentration",
                "severity": "medium",
                "detail": "Revenue stream depends on a single counterparty with no diversification.",
            })

        if self.mp.curtailment_history_percent > 0.05:
            factors.append({
                "category": "Market",
                "factor": "Curtailment risk",
                "severity": "medium",
                "detail": f"Historical curtailment rate of {self.mp.curtailment_history_percent:.1%} "
                          f"could reduce realized generation volumes.",
            })

        if self.mp.interconnection_certainty in ("low", "speculative"):
            factors.append({
                "category": "Market",
                "factor": "Interconnection uncertainty",
                "severity": "high",
                "detail": "Interconnection status poses execution risk to project timeline and commercial operation.",
            })

        if not self.sp.reserve_accounts_funded:
            factors.append({
                "category": "Structure",
                "factor": "Unfunded reserves",
                "severity": "low",
                "detail": "Debt service and maintenance reserve accounts are not yet funded.",
            })

        if not self.params.technical.environmental_permits_secured:
            factors.append({
                "category": "Permitting",
                "factor": "Outstanding environmental permits",
                "severity": "medium",
                "detail": "Environmental permits have not been fully secured, creating regulatory and timeline risk.",
            })

        return factors

    def _identify_mitigants(self):
        """Identify structural and contractual risk mitigants."""
        mitigants = []

        if self.cp.offtake_type in ("ppa_fixed", "regulated_rate"):
            mitigants.append({
                "category": "Revenue",
                "mitigant": "Contracted revenue stream",
                "strength": "strong",
                "detail": f"Long-term {self.cp.offtake_type.replace('_', ' ')} contract provides "
                          f"revenue certainty over {self.cp.offtake_tenor_years} years.",
            })

        if self.sp.epc_contract_type == "fixed_price_turnkey":
            mitigants.append({
                "category": "Construction",
                "mitigant": "Fixed-price turnkey EPC",
                "strength": "strong",
                "detail": "Construction cost risk is transferred to the EPC contractor under a "
                          "lump-sum turnkey arrangement.",
            })

        if self.sp.performance_guarantee:
            mitigants.append({
                "category": "Performance",
                "mitigant": "Performance guarantee",
                "strength": "moderate",
                "detail": f"Equipment/system performance guaranteed at {self.sp.performance_guarantee_level:.0%} "
                          f"of nameplate capacity.",
            })

        if self.sp.completion_guarantee:
            mitigants.append({
                "category": "Construction",
                "mitigant": "Completion guarantee",
                "strength": "strong",
                "detail": "Sponsor or contractor completion guarantee reduces construction completion risk.",
            })

        if self.sp.reserve_accounts_funded:
            mitigants.append({
                "category": "Liquidity",
                "mitigant": "Funded reserve accounts",
                "strength": "moderate",
                "detail": f"{self.sp.debt_service_reserve_months} months of debt service reserve "
                          f"provides liquidity cushion.",
            })

        if self.sp.insurance_coverage == "comprehensive":
            mitigants.append({
                "category": "Risk Transfer",
                "mitigant": "Comprehensive insurance",
                "strength": "moderate",
                "detail": "Full insurance program covering property, liability, business "
                          "interruption, and natural catastrophe.",
            })

        if self.cp.has_credit_support:
            mitigants.append({
                "category": "Credit",
                "mitigant": "Credit support",
                "strength": "strong",
                "detail": f"Additional credit support ({self.cp.credit_support_type or 'letter of credit'}) "
                          f"enhances counterparty credit quality.",
            })

        if self.fp.dscr >= 1.40:
            mitigants.append({
                "category": "Financial",
                "mitigant": "Strong debt service coverage",
                "strength": "strong",
                "detail": f"DSCR of {self.fp.dscr:.2f}x provides substantial cash flow cushion "
                          f"above debt service requirements.",
            })

        return mitigants
