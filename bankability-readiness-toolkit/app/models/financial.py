"""
Financial modeling for energy infrastructure projects.
Generates pro forma cash flows, computes key metrics (NPV, IRR, LCOE, payback),
and provides the financial foundation for bankability scoring.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AnnualCashFlow:
    year: int
    revenue: float = 0.0
    opex: float = 0.0
    net_operating_income: float = 0.0
    debt_service: float = 0.0
    interest_payment: float = 0.0
    principal_payment: float = 0.0
    outstanding_debt: float = 0.0
    cash_flow_after_debt: float = 0.0
    dscr: float = 0.0
    cumulative_cash_flow: float = 0.0
    depreciation: float = 0.0
    taxable_income: float = 0.0
    tax_expense: float = 0.0
    net_income: float = 0.0
    tax_credit: float = 0.0
    free_cash_flow_equity: float = 0.0


@dataclass
class FinancialSummary:
    npv_project: float = 0.0
    npv_equity: float = 0.0
    irr_project: float = 0.0
    irr_equity: float = 0.0
    lcoe: float = 0.0
    payback_years: float = 0.0
    average_dscr: float = 0.0
    minimum_dscr: float = 0.0
    total_revenue: float = 0.0
    total_opex: float = 0.0
    total_debt_service: float = 0.0
    total_net_income: float = 0.0
    debt_yield: float = 0.0
    equity_multiple: float = 0.0
    annual_cash_flows: List[AnnualCashFlow] = field(default_factory=list)


class FinancialModel:
    """
    Builds a full pro forma financial model for an energy infrastructure project.
    Supports standard amortizing debt, tax credits (ITC/PTC), MACRS depreciation,
    and revenue/cost escalation over the project life.
    """

    MACRS_5_SCHEDULE = [0.20, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    MACRS_7_SCHEDULE = [0.1429, 0.2449, 0.1749, 0.1249, 0.0893, 0.0892, 0.0893, 0.0446]

    def __init__(self, project_params):
        self.params = project_params
        self.fp = project_params.financial
        self.tp = project_params.technical

    def build_pro_forma(self):
        """Generate the full pro forma cash flow projection."""
        project_life = self.tp.expected_useful_life_years
        annual_flows = []

        debt_balance = self.fp.debt_amount
        annual_debt_service = self.fp.annual_debt_service
        cumulative_cf = -self.fp.equity_amount

        depreciation_schedule = self._get_depreciation_schedule()

        itc_value = self.fp.total_project_cost * self.fp.itc_percent if self.fp.itc_percent > 0 else 0.0

        for year in range(1, project_life + 1):
            cf = AnnualCashFlow(year=year)

            degradation_factor = (1 - self.tp.degradation_rate_annual) ** (year - 1)
            revenue_escalation = (1 + self.fp.revenue_escalation) ** (year - 1)
            cf.revenue = self.fp.annual_revenue * revenue_escalation * degradation_factor

            opex_escalation = (1 + self.fp.annual_opex_escalation) ** (year - 1)
            cf.opex = self.fp.annual_opex * opex_escalation

            cf.net_operating_income = cf.revenue - cf.opex

            if year <= self.fp.debt_tenor_years and debt_balance > 0:
                cf.interest_payment = debt_balance * self.fp.interest_rate
                cf.principal_payment = annual_debt_service - cf.interest_payment
                if cf.principal_payment > debt_balance:
                    cf.principal_payment = debt_balance
                cf.debt_service = cf.interest_payment + cf.principal_payment
                debt_balance -= cf.principal_payment
                cf.outstanding_debt = max(debt_balance, 0)
            else:
                cf.interest_payment = 0.0
                cf.principal_payment = 0.0
                cf.debt_service = 0.0
                cf.outstanding_debt = 0.0

            cf.cash_flow_after_debt = cf.net_operating_income - cf.debt_service

            if year - 1 < len(depreciation_schedule):
                cf.depreciation = self.fp.total_hard_costs * depreciation_schedule[year - 1]
            else:
                cf.depreciation = 0.0

            cf.taxable_income = cf.net_operating_income - cf.interest_payment - cf.depreciation

            if year == 1 and itc_value > 0:
                cf.tax_credit = itc_value

            generation_mwh = self.tp.annual_generation_mwh * degradation_factor
            if self.fp.ptc_per_mwh > 0 and year <= 10:
                cf.tax_credit += generation_mwh * self.fp.ptc_per_mwh

            cf.tax_expense = max(0, cf.taxable_income * self.fp.tax_rate) - cf.tax_credit
            cf.net_income = cf.taxable_income - cf.tax_expense
            cf.free_cash_flow_equity = cf.cash_flow_after_debt - max(cf.tax_expense, 0) + cf.tax_credit

            if cf.debt_service > 0:
                cf.dscr = cf.net_operating_income / cf.debt_service
            else:
                cf.dscr = float("inf") if cf.net_operating_income > 0 else 0.0

            cumulative_cf += cf.free_cash_flow_equity
            cf.cumulative_cash_flow = cumulative_cf

            annual_flows.append(cf)

        return self._compute_summary(annual_flows)

    def _get_depreciation_schedule(self):
        if self.fp.depreciation_schedule == "macrs_5":
            return self.MACRS_5_SCHEDULE
        elif self.fp.depreciation_schedule == "macrs_7":
            return self.MACRS_7_SCHEDULE
        elif self.fp.depreciation_schedule == "straight_line":
            life = self.tp.expected_useful_life_years
            return [1.0 / life] * life
        else:
            return self.MACRS_5_SCHEDULE

    def _compute_summary(self, annual_flows):
        summary = FinancialSummary()
        summary.annual_cash_flows = annual_flows

        project_cfs = [-self.fp.total_project_cost]
        equity_cfs = [-self.fp.equity_amount]

        dscr_values = []
        cumulative_unlevered = 0.0
        payback_found = False

        for cf in annual_flows:
            project_cfs.append(cf.net_operating_income)
            equity_cfs.append(cf.free_cash_flow_equity)

            summary.total_revenue += cf.revenue
            summary.total_opex += cf.opex
            summary.total_debt_service += cf.debt_service
            summary.total_net_income += cf.net_income

            if cf.dscr != float("inf") and cf.dscr > 0:
                dscr_values.append(cf.dscr)

            cumulative_unlevered += cf.net_operating_income
            if not payback_found and cumulative_unlevered >= self.fp.total_project_cost:
                fraction = 1.0
                if cf.net_operating_income > 0:
                    overshoot = cumulative_unlevered - self.fp.total_project_cost
                    fraction = 1.0 - (overshoot / cf.net_operating_income)
                summary.payback_years = cf.year - 1 + fraction
                payback_found = True

        if not payback_found:
            summary.payback_years = self.tp.expected_useful_life_years

        summary.npv_project = self._compute_npv(project_cfs, self.fp.discount_rate)
        summary.npv_equity = self._compute_npv(equity_cfs, self.fp.discount_rate)
        summary.irr_project = self._compute_irr(project_cfs)
        summary.irr_equity = self._compute_irr(equity_cfs)

        if dscr_values:
            summary.average_dscr = sum(dscr_values) / len(dscr_values)
            summary.minimum_dscr = min(dscr_values)
        else:
            summary.average_dscr = 0.0
            summary.minimum_dscr = 0.0

        total_generation = sum(
            self.tp.annual_generation_mwh * (1 - self.tp.degradation_rate_annual) ** (y - 1)
            for y in range(1, self.tp.expected_useful_life_years + 1)
        )
        if total_generation > 0:
            total_costs = self.fp.total_project_cost + summary.total_opex
            discount_factors = [1 / (1 + self.fp.discount_rate) ** y
                                for y in range(1, self.tp.expected_useful_life_years + 1)]
            discounted_gen = sum(
                self.tp.annual_generation_mwh * (1 - self.tp.degradation_rate_annual) ** (y - 1) * df
                for y, df in zip(range(1, self.tp.expected_useful_life_years + 1), discount_factors)
            )
            discounted_costs = self.fp.total_project_cost + sum(
                cf.opex / (1 + self.fp.discount_rate) ** cf.year for cf in annual_flows
            )
            summary.lcoe = discounted_costs / discounted_gen if discounted_gen > 0 else 0.0
        else:
            summary.lcoe = 0.0

        if self.fp.debt_amount > 0:
            year1_noi = annual_flows[0].net_operating_income if annual_flows else 0
            summary.debt_yield = year1_noi / self.fp.debt_amount
        else:
            summary.debt_yield = 0.0

        if self.fp.equity_amount > 0:
            total_equity_cf = sum(cf.free_cash_flow_equity for cf in annual_flows)
            summary.equity_multiple = total_equity_cf / self.fp.equity_amount
        else:
            summary.equity_multiple = 0.0

        return summary

    @staticmethod
    def _compute_npv(cash_flows, rate):
        if not cash_flows or rate < 0:
            return 0.0
        npv = 0.0
        for i, cf in enumerate(cash_flows):
            npv += cf / (1 + rate) ** i
        return npv

    @staticmethod
    def _compute_irr(cash_flows, max_iterations=200, tolerance=1e-7):
        """Newton-Raphson IRR calculation."""
        if not cash_flows or len(cash_flows) < 2:
            return 0.0

        total = sum(cash_flows)
        if total <= 0:
            return 0.0

        guess = 0.10
        for _ in range(max_iterations):
            npv = 0.0
            d_npv = 0.0
            for i, cf in enumerate(cash_flows):
                factor = (1 + guess) ** i
                if factor != 0:
                    npv += cf / factor
                    if i > 0:
                        d_npv -= i * cf / ((1 + guess) ** (i + 1))

            if abs(d_npv) < 1e-15:
                break

            new_guess = guess - npv / d_npv

            if new_guess < -0.99:
                new_guess = -0.5
            if new_guess > 10.0:
                new_guess = 5.0

            if abs(new_guess - guess) < tolerance:
                return new_guess

            guess = new_guess

        return guess

    def financial_strength_score(self, summary=None):
        """Rate financial strength on a 0-100 scale for bankability scoring."""
        if summary is None:
            summary = self.build_pro_forma()

        score = 0.0

        # DSCR scoring (30 points max)
        if summary.minimum_dscr >= 1.60:
            score += 30
        elif summary.minimum_dscr >= 1.40:
            score += 25
        elif summary.minimum_dscr >= 1.25:
            score += 18
        elif summary.minimum_dscr >= 1.10:
            score += 10
        elif summary.minimum_dscr >= 1.0:
            score += 5

        # IRR scoring (20 points max)
        if summary.irr_project >= 0.15:
            score += 20
        elif summary.irr_project >= 0.10:
            score += 15
        elif summary.irr_project >= 0.08:
            score += 10
        elif summary.irr_project >= 0.05:
            score += 5

        # NPV scoring (15 points max)
        if summary.npv_project > 0:
            score += 15
        elif summary.npv_project > -self.fp.total_project_cost * 0.05:
            score += 5

        # Payback scoring (15 points max)
        life = self.tp.expected_useful_life_years
        if summary.payback_years <= life * 0.3:
            score += 15
        elif summary.payback_years <= life * 0.5:
            score += 10
        elif summary.payback_years <= life * 0.7:
            score += 5

        # Leverage scoring (10 points max)
        leverage = self.fp.leverage_ratio
        if 0.50 <= leverage <= 0.75:
            score += 10
        elif 0.40 <= leverage <= 0.80:
            score += 7
        elif leverage < 0.40:
            score += 8
        elif leverage <= 0.90:
            score += 3

        # Debt yield scoring (10 points max)
        if summary.debt_yield >= 0.12:
            score += 10
        elif summary.debt_yield >= 0.10:
            score += 8
        elif summary.debt_yield >= 0.08:
            score += 5
        elif summary.debt_yield >= 0.06:
            score += 3

        return min(score, 100.0)
