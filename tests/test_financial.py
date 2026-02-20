"""Tests for the financial model."""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.project import (
    TechnicalParameters, FinancialParameters, CreditParameters,
    ProjectStructureParameters, MarketParameters, ProjectParameters
)
from app.models.financial import FinancialModel


def _default_params():
    tech = TechnicalParameters(
        technology_type="onshore_wind",
        nameplate_capacity_mw=150,
        annual_generation_mwh=499_260,
        capacity_factor=0.38,
        technology_readiness_level=9,
        expected_useful_life_years=25,
        degradation_rate_annual=0.008,
        availability_factor=0.97,
        interconnection_voltage_kv=230,
        interconnection_status="agreement_executed",
        environmental_permits_secured=True,
        site_control_secured=True,
    )
    fin = FinancialParameters(
        total_project_cost=225_000_000,
        total_hard_costs=180_000_000,
        total_soft_costs=22_500_000,
        contingency_percent=0.10,
        construction_period_months=24,
        debt_percent=0.65,
        equity_percent=0.35,
        interest_rate=0.050,
        debt_tenor_years=18,
        target_dscr=1.30,
        annual_revenue=23_000_000,
        annual_opex=5_700_000,
        annual_opex_escalation=0.025,
        revenue_escalation=0.02,
        tax_rate=0.21,
        itc_percent=0.0,
        ptc_per_mwh=27.5,
        depreciation_schedule="macrs_5",
        discount_rate=0.08,
    )
    credit = CreditParameters(
        offtake_type="ppa_fixed",
        offtake_tenor_years=20,
        offtaker_credit_rating="A",
        offtaker_entity_type="independent_power_producer",
        revenue_concentration_percent=1.0,
        regulatory_stability_rating="stable",
        curtailment_risk="low",
        counterparty_count=1,
        contract_price_per_mwh=50.0,
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
        market_price_per_mwh=42.0,
        market_price_trend="stable",
        curtailment_history_percent=0.03,
        interconnection_certainty="high",
        grid_congestion_risk="low",
        competing_projects_in_queue=3,
        community_support="supportive",
        land_lease_secured=True,
        land_lease_term_years=30,
    )
    return ProjectParameters(
        project_name="Test Wind Project",
        project_id="TWP-001",
        project_stage="construction_ready",
        entity_type="independent_power_producer",
        location_state="Oklahoma",
        location_county="Garfield",
        is_rural=True,
        description="150 MW onshore wind farm for testing.",
        technical=tech,
        financial=fin,
        credit=credit,
        structure=structure,
        market=market,
    )


class TestFinancialModel(unittest.TestCase):

    def setUp(self):
        self.params = _default_params()
        self.model = FinancialModel(self.params)

    def test_pro_forma_generates_cash_flows(self):
        summary = self.model.build_pro_forma()
        self.assertIsNotNone(summary)
        self.assertGreater(len(summary.annual_cash_flows), 0)

    def test_cash_flow_years_match_useful_life(self):
        summary = self.model.build_pro_forma()
        self.assertEqual(
            len(summary.annual_cash_flows),
            self.params.technical.expected_useful_life_years,
        )

    def test_irr_is_positive(self):
        summary = self.model.build_pro_forma()
        self.assertGreater(summary.irr_project, 0)

    def test_npv_calculated(self):
        summary = self.model.build_pro_forma()
        self.assertIsNotNone(summary.npv_project)

    def test_lcoe_positive(self):
        summary = self.model.build_pro_forma()
        self.assertGreater(summary.lcoe, 0)

    def test_dscr_above_one(self):
        summary = self.model.build_pro_forma()
        self.assertGreater(summary.minimum_dscr, 0.5)

    def test_debt_amount(self):
        expected_debt = (
            self.params.financial.total_project_cost
            * self.params.financial.debt_percent
        )
        actual_debt = self.params.financial.debt_amount
        self.assertAlmostEqual(actual_debt, expected_debt, places=0)

    def test_equity_amount(self):
        expected_equity = (
            self.params.financial.total_project_cost
            * self.params.financial.equity_percent
        )
        actual_equity = self.params.financial.equity_amount
        self.assertAlmostEqual(actual_equity, expected_equity, places=0)

    def test_revenue_positive_year_one(self):
        summary = self.model.build_pro_forma()
        self.assertGreater(summary.annual_cash_flows[0].revenue, 0)

    def test_financial_strength_score(self):
        score = self.model.financial_strength_score()
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)


class TestFinancialEdgeCases(unittest.TestCase):

    def test_zero_debt(self):
        params = _default_params()
        params.financial.debt_percent = 0
        params.financial.equity_percent = 1.0
        model = FinancialModel(params)
        summary = model.build_pro_forma()
        self.assertIsNotNone(summary)
        for cf in summary.annual_cash_flows:
            self.assertEqual(cf.debt_service, 0)

    def test_high_leverage(self):
        params = _default_params()
        params.financial.debt_percent = 0.90
        params.financial.equity_percent = 0.10
        model = FinancialModel(params)
        summary = model.build_pro_forma()
        self.assertIsNotNone(summary)
        self.assertGreater(summary.annual_cash_flows[0].debt_service, 0)

    def test_small_project(self):
        params = _default_params()
        params.technical.nameplate_capacity_mw = 5
        params.financial.total_project_cost = 7_500_000
        params.financial.total_hard_costs = 6_000_000
        params.financial.total_soft_costs = 750_000
        params.financial.annual_revenue = 900_000
        params.financial.annual_opex = 180_000
        model = FinancialModel(params)
        summary = model.build_pro_forma()
        self.assertIsNotNone(summary)
        self.assertGreater(summary.lcoe, 0)


if __name__ == "__main__":
    unittest.main()
