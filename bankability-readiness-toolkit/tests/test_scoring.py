"""Tests for the bankability scoring engine."""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.project import (
    TechnicalParameters, FinancialParameters, CreditParameters,
    ProjectStructureParameters, MarketParameters, ProjectParameters
)
from app.models.scoring import BankabilityScorer


def _default_params():
    """Build a baseline ProjectParameters for testing."""
    tech = TechnicalParameters(
        technology_type="solar_pv",
        nameplate_capacity_mw=100,
        annual_generation_mwh=236520,
        capacity_factor=0.27,
        technology_readiness_level=9,
        expected_useful_life_years=30,
        degradation_rate_annual=0.005,
        availability_factor=0.98,
        interconnection_voltage_kv=138,
        interconnection_status="agreement_executed",
        environmental_permits_secured=True,
        site_control_secured=True,
    )
    fin = FinancialParameters(
        total_project_cost=105_000_000,
        total_hard_costs=84_000_000,
        total_soft_costs=10_500_000,
        contingency_percent=0.10,
        construction_period_months=18,
        debt_percent=0.70,
        equity_percent=0.30,
        interest_rate=0.055,
        debt_tenor_years=20,
        target_dscr=1.35,
        annual_revenue=13_000_000,
        annual_opex=2_100_000,
        annual_opex_escalation=0.025,
        revenue_escalation=0.02,
        tax_rate=0.21,
        itc_percent=0.30,
        ptc_per_mwh=0.0,
        depreciation_schedule="macrs_5",
        discount_rate=0.08,
    )
    credit = CreditParameters(
        offtake_type="ppa_fixed",
        offtake_tenor_years=20,
        offtaker_credit_rating="BBB",
        offtaker_entity_type="cooperative",
        revenue_concentration_percent=1.0,
        regulatory_stability_rating="stable",
        curtailment_risk="low",
        counterparty_count=1,
        contract_price_per_mwh=55.0,
        has_credit_support=True,
        credit_support_type="letter_of_credit",
    )
    structure = ProjectStructureParameters(
        epc_contract_type="fixed_price_turnkey",
        epc_contractor_experience="established",
        epc_warranty_years=2,
        om_contract_type="full_service",
        om_contract_tenor_years=10,
        insurance_coverage="comprehensive",
        performance_guarantee=True,
        performance_guarantee_level=0.95,
        completion_guarantee=True,
        reserve_accounts_funded=True,
        debt_service_reserve_months=6,
        major_maintenance_reserve=True,
        step_in_rights=True,
        assignment_provisions=True,
        change_of_control_provisions=True,
    )
    market = MarketParameters(
        resource_quality="good",
        resource_assessment_confidence="p50",
        independent_resource_assessment=True,
        market_price_per_mwh=45.0,
        market_price_trend="stable",
        curtailment_history_percent=0.02,
        interconnection_certainty="high",
        grid_congestion_risk="low",
        competing_projects_in_queue=5,
        community_support="supportive",
        land_lease_secured=True,
        land_lease_term_years=30,
    )
    return ProjectParameters(
        project_name="Test Solar Project",
        project_id="TSP-001",
        project_stage="advanced_development",
        entity_type="cooperative",
        location_state="Kansas",
        location_county="Butler",
        is_rural=True,
        description="100 MW utility-scale solar project for testing.",
        technical=tech,
        financial=fin,
        credit=credit,
        structure=structure,
        market=market,
    )


class TestBankabilityScorer(unittest.TestCase):

    def setUp(self):
        self.params = _default_params()
        self.scorer = BankabilityScorer(self.params)

    def test_score_returns_result(self):
        result = self.scorer.score()
        self.assertIsNotNone(result)
        self.assertIsInstance(result.overall_score, float)

    def test_overall_score_range(self):
        result = self.scorer.score()
        self.assertGreaterEqual(result.overall_score, 0)
        self.assertLessEqual(result.overall_score, 100)

    def test_subscore_count(self):
        result = self.scorer.score()
        self.assertEqual(len(result.sub_scores), 5)

    def test_grade_assigned(self):
        result = self.scorer.score()
        self.assertIn(result.grade, [
            "Investment Grade", "Near Investment Grade",
            "Sub-Investment Grade", "Speculative", "Pre-Bankable"
        ])

    def test_weights_sum_to_one(self):
        result = self.scorer.score()
        total_weight = sum(ss.weight for ss in result.sub_scores)
        self.assertAlmostEqual(total_weight, 1.0, places=5)

    def test_to_dict_keys(self):
        result = self.scorer.score()
        d = result.to_dict()
        expected_keys = {
            "overall_score", "grade", "grade_label", "grade_color",
            "sub_scores", "strengths", "weaknesses", "recommendations",
            "rus_eligibility", "lpo_eligibility"
        }
        self.assertTrue(expected_keys.issubset(set(d.keys())))

    def test_high_quality_project_scores_well(self):
        """A well-structured project should score above 55."""
        result = self.scorer.score()
        self.assertGreater(result.overall_score, 55)

    def test_poor_project_scores_low(self):
        """A risky project should score lower than a well-structured one."""
        good_scorer = BankabilityScorer(self.params)
        good_result = good_scorer.score()

        self.params.financial.debt_percent = 0.95
        self.params.financial.equity_percent = 0.05
        self.params.financial.interest_rate = 0.12
        self.params.credit.offtake_type = "merchant"
        self.params.credit.offtaker_credit_rating = "B"
        self.params.market.resource_quality = "poor"
        self.params.market.interconnection_certainty = "speculative"
        self.params.structure.epc_contract_type = "cost_plus"
        self.params.structure.completion_guarantee = False
        self.params.structure.reserve_accounts_funded = False
        poor_scorer = BankabilityScorer(self.params)
        poor_result = poor_scorer.score()
        self.assertLess(poor_result.overall_score, good_result.overall_score)

    def test_rus_eligibility_cooperative(self):
        """Cooperative entity should show RUS eligibility."""
        result = self.scorer.score()
        d = result.to_dict()
        self.assertIn("program", d["rus_eligibility"])

    def test_lpo_eligibility(self):
        """Clean energy project should show LPO eligibility data."""
        result = self.scorer.score()
        d = result.to_dict()
        self.assertIn("program", d["lpo_eligibility"])


class TestProjectParameters(unittest.TestCase):

    def test_serialization_roundtrip(self):
        params = _default_params()
        d = params.to_dict()
        restored = ProjectParameters.from_dict(d)
        self.assertEqual(restored.project_name, params.project_name)
        self.assertEqual(
            restored.technical.nameplate_capacity_mw,
            params.technical.nameplate_capacity_mw,
        )
        self.assertEqual(
            restored.financial.total_project_cost,
            params.financial.total_project_cost,
        )

    def test_tech_score_range(self):
        params = _default_params()
        score = params.technical.efficiency_score()
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_credit_quality_score_range(self):
        params = _default_params()
        score = params.credit.credit_quality_score()
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


if __name__ == "__main__":
    unittest.main()
