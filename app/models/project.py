"""
Project parameter definitions for energy infrastructure bankability assessment.
Captures all inputs needed to evaluate a grid project across technical,
financial, and structural dimensions.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import date


TECHNOLOGY_TYPES = [
    "solar_pv",
    "onshore_wind",
    "offshore_wind",
    "battery_storage",
    "solar_plus_storage",
    "transmission_line",
    "distribution_upgrade",
    "substation",
    "hydro_small",
    "geothermal",
    "biomass",
    "natural_gas_peaker",
    "combined_cycle",
    "microgrids",
    "grid_modernization",
]

PROJECT_STAGES = [
    "pre_development",
    "early_development",
    "advanced_development",
    "construction_ready",
    "under_construction",
    "operational",
]

OFFTAKE_TYPES = [
    "ppa_fixed",
    "ppa_indexed",
    "merchant",
    "regulated_rate",
    "tolling_agreement",
    "capacity_contract",
    "bundled_rate",
]

ENTITY_TYPES = [
    "investor_owned_utility",
    "municipal_utility",
    "cooperative",
    "independent_power_producer",
    "community_choice_aggregator",
    "tribal_utility",
    "state_authority",
]


@dataclass
class TechnicalParameters:
    technology_type: str = "solar_pv"
    nameplate_capacity_mw: float = 0.0
    annual_generation_mwh: float = 0.0
    capacity_factor: float = 0.0
    technology_readiness_level: int = 9
    expected_useful_life_years: int = 30
    degradation_rate_annual: float = 0.005
    availability_factor: float = 0.98
    interconnection_voltage_kv: float = 0.0
    interconnection_status: str = "planned"
    environmental_permits_secured: bool = False
    site_control_secured: bool = False

    def efficiency_score(self):
        """Rate technical efficiency on a 0-100 scale."""
        score = 0.0
        if self.capacity_factor > 0:
            cf_benchmarks = {
                "solar_pv": 0.25, "onshore_wind": 0.35, "offshore_wind": 0.45,
                "battery_storage": 0.85, "hydro_small": 0.45, "geothermal": 0.90,
                "biomass": 0.80, "natural_gas_peaker": 0.15,
                "combined_cycle": 0.55, "transmission_line": 0.95,
                "distribution_upgrade": 0.95, "substation": 0.95,
            }
            benchmark = cf_benchmarks.get(self.technology_type, 0.30)
            cf_ratio = min(self.capacity_factor / benchmark, 1.5)
            score += cf_ratio * 30

        trl_score = min(self.technology_readiness_level / 9.0, 1.0) * 25
        score += trl_score

        score += self.availability_factor * 20

        if self.environmental_permits_secured:
            score += 12.5
        if self.site_control_secured:
            score += 12.5

        return min(score, 100.0)


@dataclass
class FinancialParameters:
    total_project_cost: float = 0.0
    total_hard_costs: float = 0.0
    total_soft_costs: float = 0.0
    contingency_percent: float = 0.10
    construction_period_months: int = 24
    debt_percent: float = 0.70
    equity_percent: float = 0.30
    interest_rate: float = 0.055
    debt_tenor_years: int = 20
    target_dscr: float = 1.40
    annual_revenue: float = 0.0
    annual_opex: float = 0.0
    annual_opex_escalation: float = 0.025
    revenue_escalation: float = 0.02
    tax_rate: float = 0.21
    itc_percent: float = 0.0
    ptc_per_mwh: float = 0.0
    depreciation_schedule: str = "macrs_5"
    discount_rate: float = 0.08

    @property
    def debt_amount(self):
        return self.total_project_cost * self.debt_percent

    @property
    def equity_amount(self):
        return self.total_project_cost * self.equity_percent

    @property
    def annual_debt_service(self):
        if self.debt_amount <= 0 or self.debt_tenor_years <= 0:
            return 0.0
        r = self.interest_rate
        n = self.debt_tenor_years
        if r == 0:
            return self.debt_amount / n
        payment = self.debt_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
        return payment

    @property
    def net_operating_income(self):
        return self.annual_revenue - self.annual_opex

    @property
    def dscr(self):
        ads = self.annual_debt_service
        if ads <= 0:
            return float("inf")
        return self.net_operating_income / ads

    @property
    def leverage_ratio(self):
        if self.total_project_cost <= 0:
            return 0.0
        return self.debt_amount / self.total_project_cost


@dataclass
class CreditParameters:
    offtake_type: str = "ppa_fixed"
    offtake_tenor_years: int = 20
    offtaker_credit_rating: str = "BBB"
    offtaker_entity_type: str = "investor_owned_utility"
    revenue_concentration_percent: float = 1.0
    regulatory_jurisdiction: str = ""
    regulatory_stability_rating: str = "stable"
    curtailment_risk: str = "low"
    counterparty_count: int = 1
    contract_price_per_mwh: float = 0.0
    has_credit_support: bool = False
    credit_support_type: str = ""
    sovereign_risk_rating: str = "AAA"

    def credit_quality_score(self):
        """Rate overall credit quality on 0-100 scale."""
        rating_scores = {
            "AAA": 100, "AA+": 95, "AA": 90, "AA-": 85,
            "A+": 80, "A": 75, "A-": 70,
            "BBB+": 65, "BBB": 60, "BBB-": 55,
            "BB+": 45, "BB": 40, "BB-": 35,
            "B+": 30, "B": 25, "B-": 20,
            "CCC": 10, "CC": 5, "C": 2, "D": 0,
            "unrated": 30,
        }
        score = rating_scores.get(self.offtaker_credit_rating, 30) * 0.35

        tenor_score = min(self.offtake_tenor_years / 25.0, 1.0) * 100
        score += tenor_score * 0.20

        offtake_scores = {
            "ppa_fixed": 90, "ppa_indexed": 75, "regulated_rate": 85,
            "tolling_agreement": 70, "capacity_contract": 65,
            "bundled_rate": 80, "merchant": 20,
        }
        score += offtake_scores.get(self.offtake_type, 40) * 0.20

        concentration_score = max(0, 100 - (self.revenue_concentration_percent * 80))
        if self.counterparty_count > 1:
            concentration_score = min(100, concentration_score + self.counterparty_count * 5)
        score += concentration_score * 0.10

        stability_scores = {"stable": 100, "positive": 90, "uncertain": 50, "negative": 20}
        score += stability_scores.get(self.regulatory_stability_rating, 50) * 0.10

        if self.has_credit_support:
            score += 5.0

        return min(score, 100.0)


@dataclass
class ProjectStructureParameters:
    epc_contract_type: str = "fixed_price_turnkey"
    epc_contractor_experience: str = "established"
    epc_warranty_years: int = 2
    om_contract_type: str = "full_service"
    om_contract_tenor_years: int = 10
    insurance_coverage: str = "comprehensive"
    performance_guarantee: bool = True
    performance_guarantee_level: float = 0.95
    completion_guarantee: bool = True
    reserve_accounts_funded: bool = False
    debt_service_reserve_months: int = 6
    major_maintenance_reserve: bool = False
    step_in_rights: bool = True
    assignment_provisions: bool = True
    change_of_control_provisions: bool = True
    dispute_resolution: str = "arbitration"
    governing_law: str = "US"

    def structure_score(self):
        """Rate project structure on 0-100 scale."""
        score = 0.0

        epc_scores = {
            "fixed_price_turnkey": 30,
            "fixed_price_epc": 25,
            "cost_plus_gmp": 15,
            "cost_plus": 5,
            "self_build": 10,
        }
        score += epc_scores.get(self.epc_contract_type, 10)

        exp_scores = {"established": 15, "experienced": 12, "moderate": 8, "limited": 3}
        score += exp_scores.get(self.epc_contractor_experience, 5)

        if self.performance_guarantee:
            score += min(self.performance_guarantee_level * 10, 10)
        if self.completion_guarantee:
            score += 8

        if self.reserve_accounts_funded:
            score += 5
            reserve_score = min(self.debt_service_reserve_months / 6.0, 1.0) * 7
            score += reserve_score

        if self.major_maintenance_reserve:
            score += 5

        insurance_scores = {"comprehensive": 10, "standard": 7, "basic": 3, "none": 0}
        score += insurance_scores.get(self.insurance_coverage, 3)

        if self.step_in_rights:
            score += 3
        if self.assignment_provisions:
            score += 3
        if self.change_of_control_provisions:
            score += 2

        return min(score, 100.0)


@dataclass
class MarketParameters:
    resource_quality: str = "good"
    resource_assessment_confidence: str = "p50"
    independent_resource_assessment: bool = False
    market_price_per_mwh: float = 0.0
    market_price_trend: str = "stable"
    curtailment_history_percent: float = 0.0
    interconnection_certainty: str = "high"
    grid_congestion_risk: str = "low"
    competing_projects_in_queue: int = 0
    community_support: str = "supportive"
    land_lease_secured: bool = False
    land_lease_term_years: int = 30

    def market_score(self):
        """Rate market conditions on 0-100 scale."""
        score = 0.0

        quality_scores = {"excellent": 25, "good": 20, "average": 12, "below_average": 5, "poor": 0}
        score += quality_scores.get(self.resource_quality, 10)

        confidence_scores = {"p90": 20, "p75": 15, "p50": 10, "p99": 25}
        score += confidence_scores.get(self.resource_assessment_confidence, 10)
        if self.independent_resource_assessment:
            score += 5

        curtailment_penalty = min(self.curtailment_history_percent * 200, 15)
        score += max(0, 15 - curtailment_penalty)

        interconnection_scores = {"secured": 20, "high": 15, "moderate": 8, "low": 3, "speculative": 0}
        score += interconnection_scores.get(self.interconnection_certainty, 5)

        congestion_scores = {"none": 10, "low": 8, "moderate": 5, "high": 2, "severe": 0}
        score += congestion_scores.get(self.grid_congestion_risk, 3)

        if self.land_lease_secured:
            score += 5

        return min(score, 100.0)


@dataclass
class ProjectParameters:
    """Top-level container for all project parameters."""
    project_name: str = ""
    project_id: str = ""
    project_stage: str = "pre_development"
    entity_type: str = "investor_owned_utility"
    location_state: str = ""
    location_county: str = ""
    is_rural: bool = False
    cod_target: Optional[str] = None
    description: str = ""

    technical: TechnicalParameters = field(default_factory=TechnicalParameters)
    financial: FinancialParameters = field(default_factory=FinancialParameters)
    credit: CreditParameters = field(default_factory=CreditParameters)
    structure: ProjectStructureParameters = field(default_factory=ProjectStructureParameters)
    market: MarketParameters = field(default_factory=MarketParameters)

    def to_dict(self):
        """Serialize all parameters to a dictionary."""
        result = {
            "project_name": self.project_name,
            "project_id": self.project_id,
            "project_stage": self.project_stage,
            "entity_type": self.entity_type,
            "location_state": self.location_state,
            "location_county": self.location_county,
            "is_rural": self.is_rural,
            "cod_target": self.cod_target,
            "description": self.description,
        }

        for section_name in ["technical", "financial", "credit", "structure", "market"]:
            section = getattr(self, section_name)
            section_dict = {}
            for attr_name in vars(section):
                if not attr_name.startswith("_"):
                    section_dict[attr_name] = getattr(section, attr_name)
            result[section_name] = section_dict

        return result

    @classmethod
    def from_dict(cls, data):
        """Build ProjectParameters from a dictionary."""
        params = cls()
        simple_fields = [
            "project_name", "project_id", "project_stage", "entity_type",
            "location_state", "location_county", "is_rural", "cod_target", "description",
        ]
        for f in simple_fields:
            if f in data:
                setattr(params, f, data[f])

        section_map = {
            "technical": TechnicalParameters,
            "financial": FinancialParameters,
            "credit": CreditParameters,
            "structure": ProjectStructureParameters,
            "market": MarketParameters,
        }

        for section_name, section_cls in section_map.items():
            if section_name in data and isinstance(data[section_name], dict):
                section = section_cls()
                for k, v in data[section_name].items():
                    if hasattr(section, k):
                        expected_type = type(getattr(section, k))
                        try:
                            setattr(section, k, expected_type(v))
                        except (ValueError, TypeError):
                            setattr(section, k, v)
                setattr(params, section_name, section)

        return params
