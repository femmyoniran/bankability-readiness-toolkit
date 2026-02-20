"""Tests for the credit risk model."""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.project import (
    TechnicalParameters, FinancialParameters, CreditParameters,
    ProjectStructureParameters, MarketParameters, ProjectParameters
)
from app.models.credit_risk import CreditRiskModel


def _default_params():
    tech = TechnicalParameters(
        technology_type="battery_storage",
        nameplate_capacity_mw=50,
        annual_generation_mwh=73_000,
        capacity_factor=0.17,
        technology_readiness_level=8,
        expected_useful_life_years=20,
        degradation_rate_annual=0.02,
        availability_factor=0.97,
        interconnection_voltage_kv=69,
        interconnection_status="agreement_executed",
        environmental_permits_secured=True,
        site_control_secured=True,
    )
    fin = FinancialParameters(
        total_project_cost=65_000_000,
        total_hard_costs=52_000_000,
        total_soft_costs=6_500_000,
        contingency_percent=0.10,
        construction_period_months=12,
        debt_percent=0.60,
        equity_percent=0.40,
        interest_rate=0.060,
        debt_tenor_years=15,
        target_dscr=1.40,
        annual_revenue=8_500_000,
        annual_opex=1_300_000,
        annual_opex_escalation=0.025,
        revenue_escalation=0.02,
        tax_rate=0.0,
        itc_percent=0.30,
        ptc_per_mwh=0.0,
        depreciation_schedule="macrs_7",
        discount_rate=0.10,
    )
    credit = CreditParameters(
        offtake_type="capacity_contract",
        offtake_tenor_years=15,
        offtaker_credit_rating="A-",
        offtaker_entity_type="municipal_utility",
        revenue_concentration_percent=1.0,
        regulatory_stability_rating="stable",
        curtailment_risk="low",
        counterparty_count=1,
        contract_price_per_mwh=0.0,
        has_credit_support=False,
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
        independent_resource_assessment=False,
        market_price_per_mwh=55.0,
        market_price_trend="increasing",
        curtailment_history_percent=0.0,
        interconnection_certainty="secured",
        grid_congestion_risk="moderate",
        competing_projects_in_queue=2,
        community_support="supportive",
        land_lease_secured=True,
        land_lease_term_years=25,
    )
    return ProjectParameters(
        project_name="Test Storage Project",
        project_id="TST-003",
        project_stage="advanced_development",
        entity_type="municipal_utility",
        location_state="Arizona",
        location_county="Maricopa",
        is_rural=False,
        description="50 MW / 200 MWh battery energy storage system.",
        technical=tech,
        financial=fin,
        credit=credit,
        structure=structure,
        market=market,
    )


class TestCreditRiskModel(unittest.TestCase):

    def setUp(self):
        self.params = _default_params()
        self.model = CreditRiskModel(self.params)

    def test_pd_positive(self):
        result = self.model.assess()
        self.assertGreater(result.probability_of_default, 0)

    def test_lgd_range(self):
        result = self.model.assess()
        self.assertGreaterEqual(result.loss_given_default, 0)
        self.assertLessEqual(result.loss_given_default, 1.0)

    def test_expected_loss_positive(self):
        result = self.model.assess()
        self.assertGreater(result.expected_loss, 0)

    def test_equivalent_rating_valid(self):
        result = self.model.assess()
        valid_ratings = [
            "AAA", "AA+", "AA", "AA-", "A+", "A", "A-",
            "BBB+", "BBB", "BBB-", "BB+", "BB", "BB-",
            "B+", "B", "B-", "CCC"
        ]
        self.assertIn(result.credit_rating_equivalent, valid_ratings)

    def test_risk_factors_list(self):
        result = self.model.assess()
        self.assertIsInstance(result.risk_factors, list)

    def test_mitigants_list(self):
        result = self.model.assess()
        self.assertIsInstance(result.mitigants, list)

    def test_high_risk_increases_pd(self):
        # Baseline
        result_base = self.model.assess()
        # High risk
        self.params.credit.offtake_type = "merchant"
        self.params.credit.offtaker_credit_rating = "B"
        self.params.financial.debt_percent = 0.90
        self.params.financial.equity_percent = 0.10
        model_risky = CreditRiskModel(self.params)
        result_risky = model_risky.assess()
        self.assertGreater(
            result_risky.probability_of_default,
            result_base.probability_of_default,
        )

    def test_risk_category_assigned(self):
        result = self.model.assess()
        self.assertIsInstance(result.risk_category, str)
        self.assertGreater(len(result.risk_category), 0)

    def test_credit_spread_positive(self):
        result = self.model.assess()
        self.assertGreater(result.credit_spread_bps, 0)


if __name__ == "__main__":
    unittest.main()
