"""
Cash flow analysis and waterfall construction for energy infrastructure projects.
"""

from app.models.financial import FinancialModel


class CashFlowAnalysis:
    """
    Provides detailed cash flow analysis with waterfall breakdowns,
    cumulative tracking, and period-over-period comparisons.
    """

    def __init__(self, project_params):
        self.params = project_params
        self.model = FinancialModel(project_params)

    def generate_waterfall(self):
        """Build a cash flow waterfall showing each step from revenue to free cash flow."""
        summary = self.model.build_pro_forma()
        waterfall_years = []

        for cf in summary.annual_cash_flows:
            waterfall_years.append({
                "year": cf.year,
                "steps": [
                    {"label": "Revenue", "amount": round(cf.revenue, 0), "type": "positive"},
                    {"label": "Operating Expenses", "amount": round(-cf.opex, 0), "type": "negative"},
                    {"label": "Net Operating Income", "amount": round(cf.net_operating_income, 0), "type": "subtotal"},
                    {"label": "Interest", "amount": round(-cf.interest_payment, 0), "type": "negative"},
                    {"label": "Principal", "amount": round(-cf.principal_payment, 0), "type": "negative"},
                    {"label": "Cash After Debt Service", "amount": round(cf.cash_flow_after_debt, 0), "type": "subtotal"},
                    {"label": "Tax Credit", "amount": round(cf.tax_credit, 0), "type": "positive"},
                    {"label": "Taxes", "amount": round(-max(cf.tax_expense, 0), 0), "type": "negative"},
                    {"label": "Free Cash Flow to Equity", "amount": round(cf.free_cash_flow_equity, 0), "type": "total"},
                ],
            })

        return {
            "waterfall": waterfall_years,
            "summary": {
                "total_revenue": round(summary.total_revenue, 0),
                "total_opex": round(summary.total_opex, 0),
                "total_debt_service": round(summary.total_debt_service, 0),
                "total_net_income": round(summary.total_net_income, 0),
                "npv_project": round(summary.npv_project, 0),
                "irr_project": round(summary.irr_project * 100, 2),
            },
        }

    def debt_schedule(self):
        """Generate the full debt amortization schedule."""
        summary = self.model.build_pro_forma()
        schedule = []
        for cf in summary.annual_cash_flows:
            if cf.year <= self.params.financial.debt_tenor_years:
                schedule.append({
                    "year": cf.year,
                    "beginning_balance": round(
                        cf.outstanding_debt + cf.principal_payment, 0
                    ),
                    "interest": round(cf.interest_payment, 0),
                    "principal": round(cf.principal_payment, 0),
                    "total_payment": round(cf.debt_service, 0),
                    "ending_balance": round(cf.outstanding_debt, 0),
                    "dscr": round(cf.dscr, 2) if cf.dscr != float("inf") else 999.99,
                })

        return schedule

    def annual_summary_table(self):
        """Generate a comprehensive annual summary table."""
        summary = self.model.build_pro_forma()
        table = []
        for cf in summary.annual_cash_flows:
            table.append({
                "year": cf.year,
                "revenue": round(cf.revenue, 0),
                "opex": round(cf.opex, 0),
                "noi": round(cf.net_operating_income, 0),
                "debt_service": round(cf.debt_service, 0),
                "dscr": round(cf.dscr, 2) if cf.dscr != float("inf") else 999.99,
                "depreciation": round(cf.depreciation, 0),
                "tax_credit": round(cf.tax_credit, 0),
                "tax_expense": round(cf.tax_expense, 0),
                "net_income": round(cf.net_income, 0),
                "fcfe": round(cf.free_cash_flow_equity, 0),
                "cumulative_cf": round(cf.cumulative_cash_flow, 0),
            })
        return table
