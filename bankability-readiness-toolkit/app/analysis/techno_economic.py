"""
Techno-economic analysis for energy infrastructure projects.
Computes capital cost benchmarks, capacity cost ratios, and technology-specific
performance metrics used in bankability evaluation.
"""


# Installed cost benchmarks ($/kW) -- representative 2024-2025 market ranges
COST_BENCHMARKS = {
    "solar_pv": {"low": 800, "mid": 1050, "high": 1400},
    "onshore_wind": {"low": 1100, "mid": 1400, "high": 1800},
    "offshore_wind": {"low": 2800, "mid": 3500, "high": 4500},
    "battery_storage": {"low": 800, "mid": 1200, "high": 1800},
    "solar_plus_storage": {"low": 1400, "mid": 1900, "high": 2600},
    "transmission_line": {"low": 1500, "mid": 2500, "high": 4000},
    "distribution_upgrade": {"low": 500, "mid": 1000, "high": 2000},
    "substation": {"low": 80, "mid": 150, "high": 300},  # $/kVA
    "hydro_small": {"low": 2000, "mid": 3500, "high": 6000},
    "geothermal": {"low": 2500, "mid": 4000, "high": 6500},
    "biomass": {"low": 2000, "mid": 3500, "high": 5000},
    "natural_gas_peaker": {"low": 600, "mid": 900, "high": 1300},
    "combined_cycle": {"low": 800, "mid": 1100, "high": 1500},
    "microgrids": {"low": 2000, "mid": 3500, "high": 6000},
    "grid_modernization": {"low": 500, "mid": 1500, "high": 3000},
}

# Fixed O&M benchmarks ($/kW-year)
OM_BENCHMARKS = {
    "solar_pv": {"low": 8, "mid": 14, "high": 22},
    "onshore_wind": {"low": 25, "mid": 38, "high": 55},
    "offshore_wind": {"low": 60, "mid": 90, "high": 130},
    "battery_storage": {"low": 6, "mid": 12, "high": 20},
    "solar_plus_storage": {"low": 14, "mid": 22, "high": 35},
    "hydro_small": {"low": 20, "mid": 40, "high": 65},
    "geothermal": {"low": 30, "mid": 50, "high": 80},
    "biomass": {"low": 50, "mid": 80, "high": 120},
    "natural_gas_peaker": {"low": 10, "mid": 18, "high": 30},
    "combined_cycle": {"low": 12, "mid": 20, "high": 35},
}


class TechnoEconomicAnalysis:
    """
    Performs techno-economic benchmarking and analysis for an energy
    infrastructure project, comparing inputs against industry norms.
    """

    def __init__(self, project_params):
        self.params = project_params
        self.tp = project_params.technical
        self.fp = project_params.financial

    def analyze(self):
        """Run the full techno-economic analysis."""
        results = {
            "capital_cost_analysis": self._analyze_capital_costs(),
            "operating_cost_analysis": self._analyze_operating_costs(),
            "performance_analysis": self._analyze_performance(),
            "cost_competitiveness": self._analyze_cost_competitiveness(),
        }
        return results

    def _analyze_capital_costs(self):
        """Compare project capital costs against industry benchmarks."""
        tech = self.tp.technology_type
        benchmarks = COST_BENCHMARKS.get(tech, {"low": 1000, "mid": 2000, "high": 3000})

        if self.tp.nameplate_capacity_mw > 0:
            cost_per_kw = self.fp.total_project_cost / (self.tp.nameplate_capacity_mw * 1000)
        else:
            cost_per_kw = 0

        if cost_per_kw <= benchmarks["low"]:
            position = "Below market low"
            assessment = "favorable"
        elif cost_per_kw <= benchmarks["mid"]:
            position = "Below market midpoint"
            assessment = "competitive"
        elif cost_per_kw <= benchmarks["high"]:
            position = "Above market midpoint"
            assessment = "acceptable"
        else:
            position = "Above market high"
            assessment = "elevated"

        return {
            "cost_per_kw": round(cost_per_kw, 0),
            "benchmark_low": benchmarks["low"],
            "benchmark_mid": benchmarks["mid"],
            "benchmark_high": benchmarks["high"],
            "position": position,
            "assessment": assessment,
            "hard_cost_ratio": round(
                self.fp.total_hard_costs / self.fp.total_project_cost * 100, 1
            ) if self.fp.total_project_cost > 0 else 0,
            "contingency_amount": round(
                self.fp.total_project_cost * self.fp.contingency_percent, 0
            ),
        }

    def _analyze_operating_costs(self):
        """Analyze operating costs against benchmarks."""
        tech = self.tp.technology_type
        benchmarks = OM_BENCHMARKS.get(tech, {"low": 10, "mid": 25, "high": 50})

        if self.tp.nameplate_capacity_mw > 0:
            om_per_kw = self.fp.annual_opex / (self.tp.nameplate_capacity_mw * 1000)
        else:
            om_per_kw = 0

        if om_per_kw <= benchmarks["low"]:
            assessment = "below_benchmark"
        elif om_per_kw <= benchmarks["mid"]:
            assessment = "competitive"
        elif om_per_kw <= benchmarks["high"]:
            assessment = "above_average"
        else:
            assessment = "high"

        opex_ratio = 0
        if self.fp.annual_revenue > 0:
            opex_ratio = self.fp.annual_opex / self.fp.annual_revenue * 100

        return {
            "om_per_kw_year": round(om_per_kw, 2),
            "benchmark_low": benchmarks["low"],
            "benchmark_mid": benchmarks["mid"],
            "benchmark_high": benchmarks["high"],
            "assessment": assessment,
            "opex_to_revenue_ratio": round(opex_ratio, 1),
            "annual_escalation": f"{self.fp.annual_opex_escalation:.1%}",
        }

    def _analyze_performance(self):
        """Analyze technical performance metrics."""
        tp = self.tp

        annual_hours = 8760
        if tp.nameplate_capacity_mw > 0 and tp.annual_generation_mwh > 0:
            implied_cf = tp.annual_generation_mwh / (tp.nameplate_capacity_mw * annual_hours)
        else:
            implied_cf = tp.capacity_factor

        cf_benchmarks = {
            "solar_pv": {"p10": 0.15, "p50": 0.22, "p90": 0.30},
            "onshore_wind": {"p10": 0.25, "p50": 0.33, "p90": 0.45},
            "offshore_wind": {"p10": 0.35, "p50": 0.42, "p90": 0.52},
            "battery_storage": {"p10": 0.10, "p50": 0.15, "p90": 0.25},
            "hydro_small": {"p10": 0.30, "p50": 0.42, "p90": 0.55},
            "geothermal": {"p10": 0.80, "p50": 0.88, "p90": 0.93},
            "combined_cycle": {"p10": 0.40, "p50": 0.55, "p90": 0.70},
        }

        tech_cf = cf_benchmarks.get(tp.technology_type, {"p10": 0.15, "p50": 0.30, "p90": 0.50})

        lifetime_generation = sum(
            tp.annual_generation_mwh * (1 - tp.degradation_rate_annual) ** y
            for y in range(tp.expected_useful_life_years)
        )
        total_degradation = (1 - tp.degradation_rate_annual) ** tp.expected_useful_life_years

        return {
            "implied_capacity_factor": round(implied_cf, 3),
            "stated_capacity_factor": round(tp.capacity_factor, 3),
            "cf_benchmark_p10": tech_cf["p10"],
            "cf_benchmark_p50": tech_cf["p50"],
            "cf_benchmark_p90": tech_cf["p90"],
            "availability_factor": round(tp.availability_factor, 3),
            "annual_generation_mwh": round(tp.annual_generation_mwh, 0),
            "lifetime_generation_mwh": round(lifetime_generation, 0),
            "end_of_life_output_ratio": round(total_degradation, 3),
            "degradation_rate": f"{tp.degradation_rate_annual:.2%}",
            "technology_readiness_level": tp.technology_readiness_level,
        }

    def _analyze_cost_competitiveness(self):
        """Assess overall cost competitiveness of the project."""
        # Revenue per MWh
        if self.tp.annual_generation_mwh > 0:
            revenue_per_mwh = self.fp.annual_revenue / self.tp.annual_generation_mwh
            cost_per_mwh = self.fp.annual_opex / self.tp.annual_generation_mwh
            margin_per_mwh = revenue_per_mwh - cost_per_mwh
        else:
            revenue_per_mwh = 0
            cost_per_mwh = 0
            margin_per_mwh = 0

        # Capital intensity
        if self.tp.annual_generation_mwh > 0:
            capital_per_mwh_annual = self.fp.total_project_cost / self.tp.annual_generation_mwh
        else:
            capital_per_mwh_annual = 0

        # Operating margin
        if self.fp.annual_revenue > 0:
            operating_margin = (self.fp.annual_revenue - self.fp.annual_opex) / self.fp.annual_revenue
        else:
            operating_margin = 0

        return {
            "revenue_per_mwh": round(revenue_per_mwh, 2),
            "cost_per_mwh": round(cost_per_mwh, 2),
            "margin_per_mwh": round(margin_per_mwh, 2),
            "capital_intensity": round(capital_per_mwh_annual, 0),
            "operating_margin": round(operating_margin * 100, 1),
        }
