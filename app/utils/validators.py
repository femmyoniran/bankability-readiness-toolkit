"""
Input validation for project parameters.
"""


def validate_project_input(data):
    """
    Validate project input data and return a list of validation errors.
    Returns an empty list if all inputs are valid.
    """
    errors = []

    if not data.get("project_name"):
        errors.append("Project name is required.")

    tech = data.get("technical", {})
    if not tech.get("technology_type"):
        errors.append("Technology type is required.")

    capacity = tech.get("nameplate_capacity_mw", 0)
    try:
        capacity = float(capacity)
        if capacity <= 0:
            errors.append("Nameplate capacity must be greater than zero.")
    except (TypeError, ValueError):
        errors.append("Nameplate capacity must be a valid number.")

    fin = data.get("financial", {})
    total_cost = fin.get("total_project_cost", 0)
    try:
        total_cost = float(total_cost)
        if total_cost <= 0:
            errors.append("Total project cost must be greater than zero.")
    except (TypeError, ValueError):
        errors.append("Total project cost must be a valid number.")

    debt_pct = fin.get("debt_percent", 0.70)
    equity_pct = fin.get("equity_percent", 0.30)
    try:
        debt_pct = float(debt_pct)
        equity_pct = float(equity_pct)
        total_pct = debt_pct + equity_pct
        if abs(total_pct - 1.0) > 0.01:
            errors.append(f"Debt and equity percentages must sum to 100% (currently {total_pct:.0%}).")
    except (TypeError, ValueError):
        errors.append("Debt and equity percentages must be valid numbers.")

    interest_rate = fin.get("interest_rate", 0.055)
    try:
        interest_rate = float(interest_rate)
        if interest_rate < 0 or interest_rate > 0.30:
            errors.append("Interest rate should be between 0% and 30%.")
    except (TypeError, ValueError):
        errors.append("Interest rate must be a valid number.")

    revenue = fin.get("annual_revenue", 0)
    try:
        revenue = float(revenue)
        if revenue < 0:
            errors.append("Annual revenue cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Annual revenue must be a valid number.")

    opex = fin.get("annual_opex", 0)
    try:
        opex = float(opex)
        if opex < 0:
            errors.append("Annual operating expenses cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Annual operating expenses must be a valid number.")

    cf = tech.get("capacity_factor", 0)
    try:
        cf = float(cf)
        if cf < 0 or cf > 1.0:
            errors.append("Capacity factor must be between 0 and 1.0.")
    except (TypeError, ValueError):
        errors.append("Capacity factor must be a valid number.")

    return errors


def coerce_numeric_fields(data):
    """
    Convert string values to appropriate numeric types in the input data.
    Handles form submissions where all values arrive as strings.
    """
    float_fields_financial = [
        "total_project_cost", "total_hard_costs", "total_soft_costs",
        "contingency_percent", "debt_percent", "equity_percent",
        "interest_rate", "target_dscr", "annual_revenue", "annual_opex",
        "annual_opex_escalation", "revenue_escalation", "tax_rate",
        "itc_percent", "ptc_per_mwh", "discount_rate",
    ]
    int_fields_financial = ["construction_period_months", "debt_tenor_years"]

    float_fields_technical = [
        "nameplate_capacity_mw", "annual_generation_mwh", "capacity_factor",
        "degradation_rate_annual", "availability_factor", "interconnection_voltage_kv",
    ]
    int_fields_technical = ["technology_readiness_level", "expected_useful_life_years"]

    float_fields_credit = [
        "revenue_concentration_percent", "contract_price_per_mwh",
    ]
    int_fields_credit = ["offtake_tenor_years", "counterparty_count"]

    float_fields_structure = ["performance_guarantee_level"]
    int_fields_structure = ["epc_warranty_years", "om_contract_tenor_years", "debt_service_reserve_months"]

    float_fields_market = ["curtailment_history_percent", "market_price_per_mwh"]
    int_fields_market = ["competing_projects_in_queue", "land_lease_term_years"]

    bool_fields_technical = ["environmental_permits_secured", "site_control_secured"]
    bool_fields_credit = ["has_credit_support"]
    bool_fields_structure = [
        "performance_guarantee", "completion_guarantee",
        "reserve_accounts_funded", "major_maintenance_reserve",
        "step_in_rights", "assignment_provisions", "change_of_control_provisions",
    ]
    bool_fields_market = ["independent_resource_assessment", "land_lease_secured"]

    sections = {
        "financial": (float_fields_financial, int_fields_financial, []),
        "technical": (float_fields_technical, int_fields_technical, bool_fields_technical),
        "credit": (float_fields_credit, int_fields_credit, bool_fields_credit),
        "structure": (float_fields_structure, int_fields_structure, bool_fields_structure),
        "market": (float_fields_market, int_fields_market, bool_fields_market),
    }

    for section_name, (floats, ints, bools) in sections.items():
        section = data.get(section_name, {})
        for field in floats:
            if field in section:
                try:
                    section[field] = float(section[field])
                except (TypeError, ValueError):
                    pass
        for field in ints:
            if field in section:
                try:
                    section[field] = int(float(section[field]))
                except (TypeError, ValueError):
                    pass
        for field in bools:
            if field in section:
                val = section[field]
                if isinstance(val, str):
                    section[field] = val.lower() in ("true", "1", "yes", "on")

    if "is_rural" in data:
        val = data["is_rural"]
        if isinstance(val, str):
            data["is_rural"] = val.lower() in ("true", "1", "yes", "on")

    return data
