# =============================================================================
# custom_constraints.py
# =============================================================================
# Purpose (plain language)
# ------------------------
# This module adds special mathematical constraints and helpers
# that control how technologies (like PV or solar thermal) share
# the available rooftop area within each building.
#
# It also provides functions to:
#   • Log how much of that joint area was actually used after optimization.
#   • Compute minimum allowed investment sizes for different technologies.
#
# In simple words: it helps the model decide how much capacity each building
# can install, avoiding unrealistic oversizing and keeping all solutions
# consistent with the available roof area.
# =============================================================================
import math
import pyomo.environ as po
from oemof.solph import Investment

# =============================================================================
# Function: add_joint_capacity_constraint
# -----------------------------------------------------------------------------
# Adds a single "joint rooftop limit" constraint for every building.
#
# Why:
# ----
# Some technologies compete for the same rooftop area (for example,
# PV panels and solar thermal collectors). This function ensures that
# the total installed capacity (PV + STC) stays below a realistic limit
# proportional to the building’s conditioned area.
# =============================================================================

def add_joint_capacity_constraint(model, raw_context, divisor=6):
    import pyomo.environ as po
    from oemof.solph import Investment

    print("\n[Custom Constraint] Applying joint investment limit PER building...")

    building_limits = {}
    flow_map = {}

    # Step 1: Calculate the maximum allowed capacity for each building.
    # The limit is based on its conditioned area divided by 'divisor'.
    # Example: if the area is 600 m² and divisor=6 → limit = 100 kW.
    for b_context in raw_context.get("building_asset_context", []):
        bid = str(b_context["building"]["id"])
        area = b_context["building"].get("area_conditioned")
        if not area or area <= 0:
            continue
        building_limits[bid] = area / divisor
        flow_map[bid] = []

    # Step 2: Identify which energy flows belong to PV or STC in each building.
    for (i, o), flow in model.flows.items():
        if not isinstance(flow.investment, Investment):
            continue
        label = str(i.label)
        for bid in building_limits:
            if label in [f"PV_{bid}", f"STC_DHW_{bid}_0", f"STC_Heating_{bid}_0"]:
                flow_map[bid].append((i, o))

    # Step 3: Create a Pyomo set with building IDs
    model.BLDG_CAP_LIMIT = po.Set(initialize=list(building_limits.keys()))

    # Step 4: Define and apply the rooftop limit constraint per building
    def joint_limit(m, bid):
        flows = flow_map[bid]
        vars_list = []
        for (i, o) in flows:
            # Depending on the oemof.solph version, the investment variable
            # might use [i, o] or [i, o, 0] as its key.
            try:
                var = m.InvestmentFlowBlock.invest[i, o, 0]
            except KeyError:
                try:
                    var = m.InvestmentFlowBlock.invest[i, o]
                except KeyError:
                    continue
            vars_list.append(var)

        # Skip if no related variables exist
        if not vars_list:
            return po.Constraint.Skip
        
        # The sum of investments cannot exceed the building limit
        return sum(vars_list) <= building_limits[bid]

    # Add the constraint to the model
    model.joint_building_limit = po.Constraint(model.BLDG_CAP_LIMIT, rule=joint_limit)

# =============================================================================
# Function: add_joint_slack_logger
# -----------------------------------------------------------------------------
# Prints how much rooftop area each building actually used after the model
# has been solved. Helps to check whether buildings are close to their limits.
# =============================================================================
def add_joint_slack_logger(model, raw_context, divisor=6):
    print("\n Post-solve usage of joint rooftop capacity:")

    building_limits = {}
    flow_map = {}

    # Step 1: Calculate the same rooftop limit per building (as before)
    for b_context in raw_context.get("building_asset_context", []):
        bid = str(b_context["building"]["id"])
        area = b_context["building"].get("area_conditioned", 0)
        if area > 0:
            building_limits[bid] = area / divisor
            flow_map[bid] = []

    # Step 2: Identify the investment flows for rooftop technologies
    for (i, o), flow_obj in model.flows.items():
        if not hasattr(flow_obj, "investment") or flow_obj.investment is None:
            continue
        label = str(i.label)
        for bid in building_limits:
            if label in [f"PV_{bid}", f"STC_DHW_{bid}_0", f"STC_Heating_{bid}_0"]:
                flow_map[bid].append((i, o))

    # Step 3: For each building, sum the optimized investment values and compare with limit
    for bid, flows in flow_map.items():
        total = 0.0
        for (i, o) in flows:
            try:
                var = model.InvestmentFlowBlock.invest[i, o, 0]
            except KeyError:
                try:
                    var = model.InvestmentFlowBlock.invest[i, o]
                except KeyError as e:
                    print(f"    Could not access invest variable for flow: {e}")
                    continue
            total += var.value if var.value is not None else 0.0

        # Compute how much capacity remains unused (slack)
        slack = building_limits[bid] - total
        print(f"  → Building {bid}: used = {total:.2f} kW / max = {building_limits[bid]:.2f} kW → slack = {slack:.2f} kW")

# =============================================================================
# Helper: round_up
# -----------------------------------------------------------------------------
# Simple math helper that rounds a value up to the nearest “step” (e.g. 0.5 or 1 kW).
# Example: round_up(3.2, 0.5) → 3.5
# =============================================================================
def round_up(value, step):
    return math.ceil(value / step) * step

# =============================================================================
# Function: get_minimum_cap
# -----------------------------------------------------------------------------
# Calculates the minimum capacity allowed for each technology (PV, STC, HP, Wind).
#
# Why:
# ----
# Ensures that the model does not propose unrealistic tiny investments.
# For example, a PV system should not be 0.1 kW. It enforces practical lower bounds
# that depend on the technology and the building’s maximum capacity (pmax).
#
# The minimum capacity is always lower than the maximum capacity (pmax).
# =============================================================================
def get_minimum_cap(tech, pmax, subtype=None, percent=0.1):
    """
    Parameters
    ----------
    tech : str
        Technology identifier. Expected values: "PV", "STC", "HP", "Wind".
    pmax : float
        Maximum allowed capacity for the technology (same unit as the investment variable).
        Must be > 0 to guarantee a strictly positive minimum.
    subtype : str | None
        Optional subtype for technologies that split by service (e.g., "heating", "dhw").
    percent : float
        Relative minimum as a fraction of pmax (e.g., 0.1 means 10%).

    Returns
    -------
    float
        Minimum capacity to enforce installation, guaranteed to be > 0 and <= pmax
        when pmax > 0.
    """
    # Define base values depending on the technology (same units as pmax)
    if tech == "PV":
        min_floor = 3.0
        step = 0.5
    elif tech == "Wind":
        min_floor = 800.0
        step = 100.0
    elif tech == "HP":
        if subtype == "heating":
            min_floor = 3.0
        elif subtype == "dhw":
            min_floor = 0.5  # changed from 0 to enforce non-zero installation
        else:
            min_floor = 2.0
        step = 1.0
    elif tech == "DHN":
        if subtype == "heating":
            min_floor = 3.0
        elif subtype == "dhw":
            min_floor = 0.5  # changed from 0 to enforce non-zero installation
        else:
            min_floor = 2.0
        step = 1.0
    elif tech == "STC":
        if subtype == "heating":
            min_floor = 2.0
        elif subtype == "dhw":
            min_floor = 0.5  # changed from 0 to enforce non-zero installation
        else:
            min_floor = 1.5
        step = 0.5
    else:
        # If technology not recognized, we cannot safely enforce >0 here.
        print("ha entrado en el else************************")
        return 0.5

    # Raw minimum: at least a floor and at least a fraction of pmax
    raw_min = max(min_floor, percent * pmax)

    # Enforce strictly positive minimum even if floors are small
    raw_min = max(raw_min, min(step, pmax))

    # Round up to practical step, then clamp again to never exceed pmax
    min_cap = round_up(raw_min, step)
    min_cap = min(min_cap, pmax)

    # If clamping made it 0 (only possible if pmax is 0, already blocked), ensure >0
    if min_cap <= 0:
        min_cap = min(step, pmax)

    print(
        f"[MIN-CAP DEBUG] Tech={tech} | Subtype={subtype} | pmax={pmax:.2f} | "
        f"raw_min={raw_min:.2f} | final_min={min_cap:.2f}"
    )

    return min_cap

