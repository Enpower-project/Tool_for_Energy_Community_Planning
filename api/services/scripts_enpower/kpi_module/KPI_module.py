# KPI_module.py
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 18 11:56:09 2024

@author: iciber
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional


# =============================================================================
# CITIZEN KPI FACTORS
# =============================================================================

def kpi_ctz_factors():
    """
    Defines the factors for calculating citizen KPIs.

    Returns
    -------
    dict
        A dictionary containing the factors for various KPI calculations.
    """
    citizen_kpis_factors = {
        # ENERGY SAVINGS
        "f_tv": 0.250,          # [kW]
        "f_streaming": 0.077,   # [kWh]
        "f_pizza": 0.667,       # [kWh/pizza]
        "f_battery": 68.7,      # [kWh/charge]
        "f_km": 354,            # [km/charge]
        "f_elcar": 0.196,       # [kWh/km]
        "f_wine": 540,          # [kWh/bottle of wine]
        # CO2 SAVINGS
        "f_trees": 25,          # [kg_CO2/year]
        "f_em_net": 0.036,      # [kg_CO2/hour]
        "f_ICV": 0.1163,        # [kg_CO2/km]
    }
    return citizen_kpis_factors


def kpi_scenario_objective(front_data):
    """
    Calculates the scenario objective based on the front data.

    Parameters
    ----------
    front_data : dict or list
        Either a dict with "num_building" or a list of buildings.

    Returns
    -------
    int
        Number of members/buildings in the scenario.
    """
    if isinstance(front_data, dict) and "num_building" in front_data:
        return front_data["num_building"]
    return len(front_data)


# =============================================================================
# CITIZEN KPI CONVERSIONS
# =============================================================================

def tv_h(citizen_kpis_factors, total_primary_energy):
    """
    Equivalent TV hours.

    Parameters
    ----------
    citizen_kpis_factors : dict
    total_primary_energy : list | float | int

    Returns
    -------
    list | float
    """
    f_tv = citizen_kpis_factors["f_tv"]
    if isinstance(total_primary_energy, list):
        return [(total_primary_energy[i] / f_tv) for i in range(len(total_primary_energy))]
    if isinstance(total_primary_energy, (int, float)):
        return total_primary_energy / f_tv
    raise ValueError("total_primary_energy must be a float, int, or list.")


def streaming_h(citizen_kpis_factors, total_primary_energy):
    """
    Equivalent streaming hours.

    Returns
    -------
    list | float
    """
    f_streaming = citizen_kpis_factors["f_streaming"]
    if isinstance(total_primary_energy, list):
        return [(total_primary_energy[i] / f_streaming) for i in range(len(total_primary_energy))]
    if isinstance(total_primary_energy, (int, float)):
        return total_primary_energy / f_streaming
    raise ValueError("total_primary_energy must be a float, int, or list.")


def pizza_h(citizen_kpis_factors, total_primary_energy):
    """
    Pizza consumption comparison.

    Returns
    -------
    list | float
    """
    f_pizza = citizen_kpis_factors["f_pizza"]
    if isinstance(total_primary_energy, list):
        return [(total_primary_energy[i] / f_pizza) for i in range(len(total_primary_energy))]
    if isinstance(total_primary_energy, (int, float)):
        return total_primary_energy / f_pizza
    raise ValueError("total_primary_energy must be a float, int, or list.")


def battery_charges(citizen_kpis_factors, total_primary_energy):
    """
    Battery usage estimation.

    Returns
    -------
    list | float
    """
    f_battery = citizen_kpis_factors["f_battery"]
    if isinstance(total_primary_energy, list):
        return [(total_primary_energy[i] / f_battery) for i in range(len(total_primary_energy))]
    if isinstance(total_primary_energy, (int, float)):
        return total_primary_energy / f_battery
    raise ValueError("total_primary_energy must be a float, int, or list.")


def el_car_charges(citizen_kpis_factors, total_primary_energy):
    """
    Electric car charging estimation.

    Returns
    -------
    list | float
    """
    f_km = citizen_kpis_factors["f_km"]
    f_elcar = citizen_kpis_factors["f_elcar"]
    if isinstance(total_primary_energy, list):
        return [(total_primary_energy[i] / (f_km * f_elcar)) for i in range(len(total_primary_energy))]
    if isinstance(total_primary_energy, (int, float)):
        return total_primary_energy / (f_km * f_elcar)
    raise ValueError("total_primary_energy must be a float, int, or list.")


def trees_number(citizen_kpis_factors, total_co2):
    """
    Trees required for carbon offset.

    Returns
    -------
    list | float
    """
    f_trees = citizen_kpis_factors["f_trees"]
    if isinstance(total_co2, list):
        return [(total_co2[i] / f_trees) for i in range(len(total_co2))]
    if isinstance(total_co2, (int, float)):
        return total_co2 / f_trees
    raise ValueError("total_co2 must be a float, int, or list.")


def streaming_emission_hours(citizen_kpis_factors, total_co2):
    """
    Streaming emissions impact.

    Returns
    -------
    list | float
    """
    f_em_net = citizen_kpis_factors["f_em_net"]
    if isinstance(total_co2, list):
        return [(total_co2[i] / f_em_net) for i in range(len(total_co2))]
    if isinstance(total_co2, (int, float)):
        return total_co2 / f_em_net
    raise ValueError("total_co2 must be a float, int, or list.")


def icv_km(citizen_kpis_factors, total_co2):
    """
    Carbon emissions per kilometer.

    Returns
    -------
    list | float
    """
    f_ICV = citizen_kpis_factors["f_ICV"]
    if isinstance(total_co2, list):
        return [(total_co2[i] / f_ICV) for i in range(len(total_co2))]
    if isinstance(total_co2, (int, float)):
        return total_co2 / f_ICV
    raise ValueError("total_co2 must be a float, int, or list.")


def wine_bottles(citizen_kpis_factors, total_primary_energy):
    """
    Wine bottles production equivalent.

    Returns
    -------
    list | float
    """
    f_wine = citizen_kpis_factors["f_wine"]
    if isinstance(total_primary_energy, list):
        return [(total_primary_energy[i] / f_wine) for i in range(len(total_primary_energy))]
    if isinstance(total_primary_energy, (int, float)):
        return total_primary_energy / f_wine
    raise ValueError("total_primary_energy must be a float, int, or list.")


def save_to_csv(building_consumption_dict, demand_profile, total_primary_energy_MWh, KPI_peak_heat_demand, KPI_peak_elec_demand, num_members,
                TV_h, streaming_h, Pizza_h, Battery_charges, ElCar_charges, Trees_number, streaming_emissionhours, ICV_km, Wine_bottles):
    """
    Builds the citizen KPI list (kept as-is).

    Returns
    -------
    list[dict]
    """
    Energy_use_MWh = 0

    if isinstance(demand_profile, list):
        for demand in demand_profile:
            profile = demand["demand_profile"]
            community_energy_use_MWh = (sum(profile["electricity_demand"])
                                        + sum(profile["heating_demand"])
                                        + sum(profile["cooling_demand"])
                                        + sum(profile["dhw_demand"])) / 1000
            Energy_use_MWh += community_energy_use_MWh

    elif isinstance(demand_profile, dict):
        profile = demand_profile["demand_profile"]
        community_energy_use_MWh = (sum(profile["electricity_demand"])
                                    + sum(profile["heating_demand"])
                                    + sum(profile["cooling_demand"])
                                    + sum(profile["dhw_demand"])) / 1000
        Energy_use_MWh += community_energy_use_MWh
    else:
        raise ValueError("demand_profile must be a list of dictionaries or a single dictionary.")

    kpis_community = [
        {"id": 0, "name": "Energy_use_[MWh]", "value": Energy_use_MWh, "unit": "MWh"},
        {"id": 1, "name": "KPI_peak_heat_demand_[kWh]", "value": KPI_peak_heat_demand, "unit": "kWh"},
        {"id": 2, "name": "KPI_peak_elec_demand_[kWh]", "value": KPI_peak_elec_demand, "unit": "kWh"},
        {"id": 3, "name": "total_primary_energy_[MWh]", "value": total_primary_energy_MWh, "unit": "MWh"},
        {"id": 4, "name": "num_members", "value": num_members, "unit": "a.u."},
        {"id": 5, "name": "EquivalentTVHours_[hours]", "value": TV_h, "unit": "kW"},
        {"id": 6, "name": "EquivalentstreamingHours_[hours]", "value": streaming_h, "unit": "kW"},
        {"id": 7, "name": "PizzaConsumptionComparison_[pizzas]", "value": Pizza_h, "unit": "kW"},
        {"id": 8, "name": "BatteryUsageEstimation_[charges]", "value": Battery_charges, "unit": "charge"},
        {"id": 9, "name": "ElectricCarChargingEstimation_[charges]", "value": ElCar_charges, "unit": "charge"},
        {"id": 10, "name": "WineBottlesProduction_[bottles]", "value": Wine_bottles, "unit": "bottles"},
        {"id": 11, "name": "TreesRequiredForCarbonOffset_[Tree]", "value": Trees_number, "unit": "tree"},
        {"id": 12, "name": "streamingEmissionsImpact_[hours]", "value": streaming_emissionhours, "unit": "hours"},
        {"id": 13, "name": "CarbonEmissionsPerKilometer_[km]", "value": ICV_km, "unit": "km"},
    ]
    return kpis_community


# =============================================================================
# SELF-CONSUMPTION KPI HELPERS
# =============================================================================

def KPI_self_consumption(pv_profile, load_profile):
    """
    Parameters
    ----------
    pv_profile : np.ndarray
    load_profile : np.ndarray

    Returns
    -------
    float
    """
    return float(np.minimum(pv_profile, load_profile).sum())


def KPI_self_sufficiency(pv_profile, load_profile):
    """
    Parameters
    ----------
    pv_profile : np.ndarray
    load_profile : np.ndarray

    Returns
    -------
    float
    """
    total_load = load_profile.sum()
    if total_load == 0:
        return 0.0
    return float(np.minimum(pv_profile, load_profile).sum())


def debug_building_energy_flows(building_idx, building_id, pv_profile, load_profile, stc_profile,
                               grid_import, self_consumption, stc_generation):
    print(f"\nDEBUG Building {building_idx + 1} (ID: {building_id})")
    print(f"  PV gen total       : {pv_profile.sum():.2f} kWh")
    print(f"  Elec. demand total : {load_profile.sum():.2f} kWh")
    print(f"  Self-consumed PV   : {self_consumption:.2f} kWh")
    print(f"  Grid import        : {grid_import:.2f} kWh")
    print(f"  STC gen total      : {stc_generation:.2f} kWh")
    print(f"  Load match         : {np.minimum(pv_profile, load_profile).sum():.2f} kWh")
    print(f"  PV/Load ratio      : {(pv_profile.sum()/load_profile.sum()*100):.2f}%"
          if load_profile.sum() > 0 else "  No load detected")


# =============================================================================
# FACTOR LOOKUPS
# =============================================================================

def pick_carrier_ids(pef_lookup: Dict[int, float],
                     co2_lookup: Dict[int, float],
                     name_lookup: Dict[int, str]) -> Tuple[Optional[int], Optional[int]]:
    elec_names = {"electricity", "electric power", "electricidad", "grid electricity"}
    gas_names = {"gas", "natural gas", "gas natural"}
    elec_id = None
    gas_id = None

    for cid, name in name_lookup.items():
        n = (name or "").lower()
        if any(tag in n for tag in elec_names):
            elec_id = cid if elec_id is None else elec_id
        if any(tag in n for tag in gas_names):
            gas_id = cid if gas_id is None else gas_id

    if elec_id is None:
        for cid, pef in pef_lookup.items():
            if 1.5 <= float(pef) <= 3.0:
                elec_id = cid
                break

    if gas_id is None:
        for cid, pef in pef_lookup.items():
            co2 = co2_lookup.get(cid)
            if co2 is None:
                continue
            if 1.05 <= float(pef) <= 1.3 and 0.15 <= float(co2) <= 0.25:
                gas_id = cid
                break

    return elec_id, gas_id


def _choose_best_nat_record(records, country_pref: Optional[int]):
    if not records:
        return None
    if country_pref is not None:
        for r in records:
            if r.get("country_id") == country_pref:
                return r
    for cand in (31, 0, None):
        for r in records:
            if r.get("country_id") == cand and (r.get("pef") is not None or r.get("co2_kg_kwh") is not None or
                                                r.get("pef_tot") is not None or r.get("f_co2_eq_g_kwh") is not None):
                return r
    return records[0]


def build_factor_lookups(context: Dict[str, Any], country_pref: Optional[int] = None):
    pef_lookup: Dict[int, float] = {}
    co2_lookup: Dict[int, float] = {}
    name_lookup: Dict[int, str] = {}

    for bac in context.get("building_asset_context", []) or []:
        for asset in bac.get("building_energy_asset", []) or []:
            gs = asset.get("generation_system", {}) or {}
            for side in ("energy_carrier_input_1", "energy_carrier_input_2",
                         "energy_carrier_output_1", "energy_carrier_output_2"):
                carrier = gs.get(side) or {}
                cid = carrier.get("id")
                if not cid:
                    continue

                cname = (carrier.get("name") or "").strip()
                if cname and cid not in name_lookup:
                    name_lookup[cid] = cname

                recs = carrier.get("national_energy_carrier_production") or []
                sel = _choose_best_nat_record(recs, country_pref)
                if not sel:
                    continue

                pef = sel.get("pef")
                if pef is None:
                    pef = sel.get("pef_tot")

                co2 = sel.get("co2_kg_kwh")
                if co2 is None and sel.get("f_co2_eq_g_kwh") is not None:
                    co2 = float(sel["f_co2_eq_g_kwh"]) / 1000.0

                if pef is not None and cid not in pef_lookup:
                    pef_lookup[cid] = float(pef)
                if co2 is not None and cid not in co2_lookup:
                    co2_lookup[cid] = float(co2)

    return pef_lookup, co2_lookup, name_lookup


# =============================================================================
# TIME SERIES HELPERS
# =============================================================================

def _fit_length(a: Optional[np.ndarray], n_ref: Optional[int]) -> Optional[np.ndarray]:
    if a is None or n_ref is None:
        return a
    if a.size == n_ref:
        return a
    if a.size > n_ref:
        return a[:n_ref]
    return np.pad(a, (0, n_ref - a.size), mode="constant")


def _as_np(arr):
    if arr is None:
        return None
    return np.asarray(arr, dtype=float)


def _get_generation_system_id(asset: Dict[str, Any]) -> Optional[int]:
    gsid = asset.get("generation_system_id")
    if gsid is not None:
        return int(gsid)
    gs = asset.get("generation_system", {}) or {}
    if gs.get("id") is not None:
        return int(gs["id"])
    return None


def _is_hp(asset: Dict[str, Any]) -> bool:
    """
    Heat pump / AC technologies by generation_system id.
    """
    return _get_generation_system_id(asset) in (63, 31, 2)


def get_scaled_ts(asset: Dict[str, Any], which: str) -> Optional[np.ndarray]:
    """
    Parameters
    ----------
    asset : dict
    which : str
        "input1", "input2", "output1", "output2"

    Returns
    -------
    np.ndarray | None
    """
    ts = asset.get("availability_ts", {}) or {}
    arr = _as_np(ts.get(f"value_{which}"))
    if arr is None:
        return None

    pmax = asset.get("pmax_scalar")
    if pmax is not None and arr.size > 0 and np.nanmax(arr) <= 1.5:
        return arr * float(pmax)

    return arr


def get_grid_imports(building_ctx: Dict[str, Any], n_ref: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    gi = building_ctx.get("grid_imports", {}) or {}
    e = _as_np(gi.get("grid_import_kwh"))
    g = _as_np(gi.get("gas_import_kwh"))

    if e is None:
        e = np.zeros_like(g) if g is not None else np.zeros(0)
    if g is None:
        g = np.zeros_like(e)

    e = _fit_length(e, n_ref)
    g = _fit_length(g, n_ref)
    return e, g


def sum_assets_power(building_ctx: Dict[str, Any],
                     system_type_ids=(),
                     gen_system_ids=(),
                     n_ref: Optional[int] = None):
    """
    Parameters
    ----------
    building_ctx : dict
    system_type_ids : iterable
        Optional filter by generation_system.system_type_id (1..5). Use only when you want
        "heating_system / dhw_system / cooling_system / elec_supply_system / storage".
    gen_system_ids : iterable
        Filter by generation_system_id (technology id, e.g. PV=83, HP heat=63, STC=71, etc.)
    n_ref : int | None
        Reference length for timeseries

    Returns
    -------
    tuple(np.ndarray, np.ndarray)
        (sum_input, sum_output)
    """
    arr_in = None
    arr_out = None

    for asset in building_ctx.get("building_energy_asset", []) or []:
        gs = asset.get("generation_system", {}) or {}

        # Filter by demand category (1..5) only if requested
        if system_type_ids and gs.get("system_type_id") not in system_type_ids:
            continue

        # Filter by technology id if requested
        if gen_system_ids:
            gsid = _get_generation_system_id(asset)
            if gsid is None or gsid not in gen_system_ids:
                continue

        # KEY RULE:
        # - HP electricity is stored in value_input2
        # - Other technologies use value_input1
        input_key = "input2" if _is_hp(asset) else "input1"

        a_in = _fit_length(get_scaled_ts(asset, input_key), n_ref)
        a_out = _fit_length(get_scaled_ts(asset, "output1"), n_ref)

        if a_in is not None:
            arr_in = a_in if arr_in is None else (arr_in + a_in)
        if a_out is not None:
            arr_out = a_out if arr_out is None else (arr_out + a_out)

    if arr_in is None and arr_out is None:
        e, _ = get_grid_imports(building_ctx, n_ref=n_ref)
        n = e.size if e is not None else (n_ref or 0)
        z = np.zeros(n)
        return z, z

    if arr_in is None:
        arr_in = np.zeros_like(arr_out)
    if arr_out is None:
        arr_out = np.zeros_like(arr_in)

    return arr_in, arr_out


# =============================================================================
# TECHNOLOGY IDs (generation_system_id)
# =============================================================================

GEN_PV = {83}
GEN_HP_HEAT = {63}
GEN_HP_DHW = {31}
GEN_HP_COOL = {2}
GEN_STC_HEAT = {71}
GEN_STC_DHW = {39}


def compute_all_kpis_for_building(building: dict, pef_lookup: dict, emission_lookup: dict,
                                  country_id: int, building_idx: int,
                                  n_ref: Optional[int] = None,
                                  elec_id: Optional[int] = None,
                                  gas_id: Optional[int] = None,
                                  elec_fallback_pef: Optional[float] = None,
                                  elec_fallback_co2: Optional[float] = None) -> dict:
    """
    Computes KPIs for one building.

    IMPORTANT:
    - HP is filtered by generation_system_id (63/31/2), NOT system_type_id.
    - HP electricity input is read from value_input2 by sum_assets_power().
    """

    grid_e, grid_g = get_grid_imports(building, n_ref=n_ref)

    pv_in, pv_out = sum_assets_power(building, gen_system_ids=GEN_PV, n_ref=n_ref)
    hpH_in, hpH_out = sum_assets_power(building, gen_system_ids=GEN_HP_HEAT, n_ref=n_ref)
    hpD_in, hpD_out = sum_assets_power(building, gen_system_ids=GEN_HP_DHW, n_ref=n_ref)
    hpC_in, hpC_out = sum_assets_power(building, gen_system_ids=GEN_HP_COOL, n_ref=n_ref)
    stcH_in, stcH_out = sum_assets_power(building, gen_system_ids=GEN_STC_HEAT, n_ref=n_ref)
    stcD_in, stcD_out = sum_assets_power(building, gen_system_ids=GEN_STC_DHW, n_ref=n_ref)

    elec_load_for_sc = grid_e + hpH_in + hpD_in + hpC_in
    pv_profile = pv_out

    pv_generation = float(pv_out.sum())
    stc_generation = float(stcH_out.sum() + stcD_out.sum())
    electricity_demand = float(grid_e.sum())
    grid_import = float(grid_e.sum())

    def kpi_self_consumption(pv, load):
        return float(np.minimum(pv, load).sum())

    def kpi_self_sufficiency(pv, load):
        sc = np.minimum(pv, load).sum()
        return float(100.0 * sc / load.sum()) if load.sum() > 0 else 0.0

    self_consumption = kpi_self_consumption(pv_profile, elec_load_for_sc)
    rate_sc = float(100.0 * self_consumption / pv_generation) if pv_generation > 0 else 0.0
    rate_ss = kpi_self_sufficiency(pv_profile, elec_load_for_sc)

    if elec_id is None:
        elec_id = 12 if 12 in pef_lookup or 12 in emission_lookup else None
    if gas_id is None:
        gas_id = 1 if 1 in pef_lookup or 1 in emission_lookup else None

    if elec_id is not None:
        pef_e = float(pef_lookup.get(elec_id, elec_fallback_pef if elec_fallback_pef is not None else 1.0))
        co2_e = float(emission_lookup.get(elec_id, elec_fallback_co2 if elec_fallback_co2 is not None else 0.0))
    else:
        pef_e = float(elec_fallback_pef if elec_fallback_pef is not None else 1.0)
        co2_e = float(elec_fallback_co2 if elec_fallback_co2 is not None else 0.0)

    pef_g = float(pef_lookup.get(gas_id, 1.1))
    co2_g = float(emission_lookup.get(gas_id, 0.2))

    elec_final = grid_e
    gas_final = grid_g

    primary_energy = float((elec_final * pef_e).sum() + (gas_final * pef_g).sum())
    co2_total = float((elec_final * co2_e).sum() + (gas_final * co2_g).sum())

    return {
        "Building_ID": building.get("building_id"),
        "PV_Generation_[kWh]": round(pv_generation, 2),
        "STC_Generation_[kWh]": round(stc_generation, 2),
        "Electricity_Demand_[kWh]": round(electricity_demand, 2),
        "Grid_Import_[kWh]": round(grid_import, 2),
        "Self_Consumption_[kWh]": round(self_consumption, 2),
        "Rate_Self_Consumption_[%]": round(rate_sc, 2),
        "Rate_Self_Sufficiency_[%]": round(rate_ss, 2),
        "Gas_Consumption_[kWh]": round(float(grid_g.sum()), 2),
        "Primary_Energy_[kWh]": round(primary_energy, 2),
        "CO2_Emissions_[kg]": round(co2_total, 2),
        "Electricity_Load_for_SC_[kWh]": round(float(elec_load_for_sc.sum()), 2),
        # Optional debug fields (keep if useful)
        "HP_Electricity_Heat_[kWh]": round(float(hpH_in.sum()), 2),
        "HP_Electricity_DHW_[kWh]": round(float(hpD_in.sum()), 2),
        "HP_Electricity_Cool_[kWh]": round(float(hpC_in.sum()), 2),
    }


# # KPI_module.py
# # -*- coding: utf-8 -*-
# """
# Created on Mon Mar 18 11:56:09 2024

# @author: iciber
# """
# '''
# -------------------------------------------------------------------------------
# numpy                         1.26.4
# jsonschema                    4.19.2
# jsonschema-specifications     2023.7.1
# pandas                        2.2.1
# Python                        3.9
# spyder                        5.5.1
# -------------------------------------------------------------------------------

# License: GNU GPLv3
# The GNU General Public License is a free, copyleft license for software and other kinds of works.
# https://www.gnu.org/licenses/gpl-3.0.html
# You may copy, distribute and modify the software as long as you track changes/dates in source files.
#  Any modifications to or software including (via compiler) GPL-licensed code must also be made 
#  available under the GPL along with build & install instructions. 
#  This means, you must:
#      - Include original
#      - State Changes
#      - Disclose source
#      - Include the same license -- to make sure it remains free software for all its users.
#      - Include copyright
#      - Include install instructions 
     
# You cannot: sublicense or hold liable.

# Copyright @CARTIF 2024

# '''
# # %% IMPORTS
# import numpy as np
# from typing import Dict, Any, Tuple, Optional

# def kpi_ctz_factors():
#     """
#     This function defines the factors for calculating citizen KPIs.

#     Returns
#     -------
#     citizen : dict
#         A dictionary containing the factors for various KPI calculations.
#     """
#     citizen_kpis_factors = {
#         # ENERGY SAVINGS
#         "f_tv": 0.250,    #[kW]
#         "f_streaming": 0.077,    #[kWh]
#         "f_pizza": 0.667,          # [kWh/pizza] DOMESTIC OVEN WATTAGE 2Kw*20MINUTES OF BAKING A PIZZA
#         "f_battery": 68.7,     # [kWh/charge] #REVISAR# 68.7 si es batería de eV, 0.01 si es smartphone  Battery_charges
#         "f_km": 354,           # [km/charge]
#         "f_elcar": 0.196,      # [kWh/km]
#         "f_wine": 540,         # [kWh/bottle of wine]
#         # CO2 SAVINGS
#         "f_trees": 25,         # [kg_CO2/year]
#         "f_em_net": 0.036,     # [kg_CO2/hour] for streaming_emissionhours
#         "f_ICV": 0.1163,       # [kg_CO2/km] wine making in Italy
        
#     }

#     return citizen_kpis_factors  

# def kpi_scenario_objective(front_data):
#     """
#     This function calculates the scenario objective based on the front data and building data.

#     Parameters
#     ----------
#     front_data : dict or list
#         A dictionary containing information about the front data or a list of dictionaries.

#     Returns
#     -------
#     num_members : int
#         The number of members in the scenario.
#     """
#     if isinstance(front_data, dict) and "num_building" in front_data:
#         num_members = front_data["num_building"]
#     else:
#         num_members = len(front_data)
        
#     return num_members


# def tv_h(citizen_kpis_factors,total_primary_energy):
#     '''
#     Equivalent TV hours
#     Description: Calculates the number of hours equivalent to the energy consumption, 
#     representing the time spent watching TV.

#     Parameters
#     ----------
#     citizen_kpis_factors : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_primary_energy : a list or a float containing information about total_primary_energy

#     Returns
#     -------
#     TV_h : float
#         Equivalent TV hours.
#     '''
#     f_tv = citizen_kpis_factors["f_tv"]  # Factor for TV hours

#     if isinstance(total_primary_energy, list):  # Check if it's a list
#         TV_h = [(total_primary_energy[i] / f_tv) for i in
#                 range(len(total_primary_energy))]  # Element-wise division for list
#     elif isinstance(total_primary_energy, (int, float)):  # Check if it's a float or integer
#         TV_h = total_primary_energy / f_tv  # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")

#     return TV_h


# def streaming_h(citizen_kpis_factors,total_primary_energy):
#     '''
#     Equivalent streaming hours
#     Description: Estimates the hours equivalent to the energy consumed, 
#     reflecting the duration of streaming.

#     Parameters
#     ----------
#     citizen : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_primary_energy : a list or a float containing information about total_primary_energy

#     Returns
#     -------
#     streaming_h : float
#         Equivalent streaming hours
#     '''
    
#     f_streaming= citizen_kpis_factors["f_streaming"]  # [h]

#     if isinstance(total_primary_energy, list):  # Check if it's a list
#         streaming_h = [(total_primary_energy[i] / f_streaming) for i in
#                 range(len(total_primary_energy))]  # Element-wise division for list
#     elif isinstance(total_primary_energy, (int, float)):  # Check if it's a float or integer
#         streaming_h = total_primary_energy / f_streaming  # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")

#     return streaming_h


# def pizza_h(citizen_kpis_factors,total_primary_energy):
#     '''
#     Pizza consumption comparison
#     Description: Converts the energy consumption into hours of pizza consumption, 
#     providing a relatable comparison.

#     Parameters
#     ----------
#     citizen : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_primary_energy : a list or a float containing information about total_primary_energy

#     Returns
#     -------
#     Pizza_h : float
#         Equivalent pizza consumption hours.
#     '''
    
#     f_pizza =citizen_kpis_factors["f_pizza"]  # [h]

#     if isinstance(total_primary_energy, list):  # Check if it's a list
#         Pizza_h = [(total_primary_energy[i] / f_pizza) for i in
#                        range(len(total_primary_energy))]  # Element-wise division for list
#     elif isinstance(total_primary_energy, (int, float)):  # Check if it's a float or integer
#         Pizza_h = total_primary_energy / f_pizza  # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")
#     return Pizza_h


# def battery_charges(citizen_kpis_factors,total_primary_energy):
#     '''
#     Battery usage estimation
#     Description: Determines the number of times a battery could be charged 
#     with the energy consumed.

#     Parameters
#     ----------
#     citizen : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_primary_energy : a list or a float containing information about total_primary_energy

#     Returns
#     -------
#     Battery_charges : float
#         Number of battery charges.
#     '''
#     f_battery= citizen_kpis_factors["f_battery"]  # [charges]
#     if isinstance(total_primary_energy, list):  # Check if it's a list
#         Battery_charges = [(total_primary_energy[i] / f_battery) for i in
#                        range(len(total_primary_energy))]  # Element-wise division for list
#     elif isinstance(total_primary_energy, (int, float)):  # Check if it's a float or integer
#         Battery_charges = total_primary_energy / f_battery  # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")
#     return Battery_charges


# def el_car_charges(citizen_kpis_factors,total_primary_energy):
#     '''
#     Electric car charging estimation
#     Description: Computes the number of times an electric car could be charged 
#     with the energy consumed.

#     Parameters
#     ----------
#     citizen : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_primary_energy : a list or a float containing information about total_primary_energy

#     Returns
#     -------
#     ElCar_charges : float
#         Number of electric car charges.
#     '''

#     f_km = citizen_kpis_factors["f_km"]  # [km/charges]
#     f_elcar = citizen_kpis_factors["f_elcar"]  # [kWh/km]

#     if isinstance(total_primary_energy, list):  # Check if it's a list
#         ElCar_charges = [(total_primary_energy[i] / (f_km*f_elcar)) for i in
#                        range(len(total_primary_energy))]  # Element-wise division for list
#     elif isinstance(total_primary_energy, (int, float)):  # Check if it's a float or integer
#         ElCar_charges = total_primary_energy /(f_km*f_elcar) # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")
#     return ElCar_charges


# def trees_number(citizen_kpis_factors,total_co2):
#     '''
#     Trees required for carbon offset
#     Description: Calculates the number of trees needed to offset the carbon emissions 
#     resulting from the energy consumption.
#     Equivalent trees = GHGsav /ghg_tree		trees
# 		kg CO2eq
# 	25	kg CO2eq/tree

#     Parameters
#     ----------
#     citizen : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_co2 : a list or a float containing information about total_co2 in kgCO2eq
#     Returns
#     -------
#     Trees_number : float
#         Number of trees required for carbon offset.
#     '''

#     f_trees= citizen_kpis_factors["f_trees"]  # [trees/year]

#     if isinstance(total_co2, list):  # Check if it's a list
#         Trees_number = [(total_co2[i] / f_trees) for i in
#                        range(len(total_co2))]  # Element-wise division for list
#     elif isinstance(total_co2, (int, float)):  # Check if it's a float or integer
#         Trees_number = total_co2 / f_trees  # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")

#     return Trees_number


# def streaming_emission_hours(citizen_kpis_factors,total_co2):
#     '''
#     Streaming emissions impact
#     Description: Assesses the environmental impact in terms of streaming usage 
#     associated with the energy consumption.

#     Parameters
#     ----------
#     citizen : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_co2 : a list or a float containing information about total_co2 in kgCO2eq

#     Returns
#     -------
#     Streaming_emissionhours : float
#         Streaming emissions impact in hours.
#     '''

#     f_em_net = citizen_kpis_factors["f_em_net"]  # [h]
#     if isinstance(total_co2, list):  # Check if it's a list
#         streaming_emissionhours = [(total_co2[i] / f_em_net) for i in
#                        range(len(total_co2))]  # Element-wise division for list
#     elif isinstance(total_co2, (int, float)):  # Check if it's a float or integer
#         streaming_emissionhours = total_co2 / f_em_net  # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")

#     return streaming_emissionhours


# def icv_km(citizen_kpis_factors,total_co2):
#     '''
#     Carbon emissions per kilometer
#     Description: Calculates the carbon emissions per kilometer traveled 
#     as a result of the energy consumption.

#     Parameters
#     ----------
#     citizen : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_co2 : a list or a float containing information about total_co2 in kgCO2eq
#     Returns
#     -------
#     ICV_km : float
#         Carbon emissions per kilometer.
#     '''

#     f_ICV= citizen_kpis_factors["f_ICV"]  # [km]

#     if isinstance(total_co2, list):  # Check if it's a list
#         ICV_km = [(total_co2[i] / f_ICV) for i in
#                        range(len(total_co2))]  # Element-wise division for list
#     elif isinstance(total_co2, (int, float)):  # Check if it's a float or integer
#         ICV_km = total_co2 / f_ICV  # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")
#     return ICV_km

# def wine_bottles(citizen_kpis_factors,total_primary_energy):
#     '''
#     Consume related to Wine bottles production
#     Description: Calculates the number of wine bottles producted based on energy consumption.

#     Parameters
#     ----------
#     citizen : dict
#         A dictionary containing information about citizen factors.
#     data : dict
#         A dictionary containing information about building statistics profiles, including generation system profiles.
#     total_primary_energy :  a list or a float containing information about total_primary_energy

#     Returns
#     -------
#     Wine_bottles : float
#         Number of wine bottles generated.
#     '''

#     f_wine= citizen_kpis_factors["f_wine"]  # [bottles]

#     if isinstance(total_primary_energy, list):  # Check if it's a list
#         Wine_bottles = [(total_primary_energy[i] / f_wine) for i in
#                        range(len(total_primary_energy))]  # Element-wise division for list
#     elif isinstance(total_primary_energy, (int, float)):  # Check if it's a float or integer
#         Wine_bottles = total_primary_energy / f_wine  # Single value division for float or int
#     else:
#         raise ValueError("total_primary_energy must be a float, int, or list.")

#     return Wine_bottles

# def save_to_csv(building_consumption_dict, demand_profile, total_primary_energy_MWh, KPI_peak_heat_demand, KPI_peak_elec_demand, num_members,
#                 TV_h, streaming_h, Pizza_h, Battery_charges, ElCar_charges, Trees_number, streaming_emissionhours, ICV_km, Wine_bottles):
#     """
#     This function saves building consumption and KPI calculation data to a CSV file.

#     Parameters
#     ----------
#     building_consumption_dict : dict
#         A dictionary containing building consumption data.
#     demand_profile : dict
#         A dictionary containing information about demand profiles for heating, cooling, electricity, and DHW.
#     total_primary_energy_MWh : float
#         Total primary energy consumption in MWh.
#     KPI_peak_heat_demand : float
#         Peak heat demand in kWh.
#     KPI_peak_elec_demand : float
#         Peak electricity demand in kWh.
#     num_members : int
#         Number of members in the household.
#     TV_h : float
#         Equivalent TV hours.
#     streaming_h : float
#         Equivalent streaming hours.
#     Pizza_h : float
#         Pizza consumption comparison.
#     Battery_charges : float
#         Battery usage estimation.
#     ElCar_charges : float
#         Electric car charging estimation.
#     Trees_number : float
#         Number of trees required for carbon offset.
#     streaming_emission_hours : float
#         Streaming emissions impact.
#     ICV_km : float
#         Carbon emissions per kilometer.
#     Wine_bottles : float
#         Number of wine bottles produced.

#     Returns
#     -------
#     kpis_community : pandas.DataFrame
#         DataFrame containing citizen KPIs results.
#     """

#     # Initialize the variable to store the total energy use
#     Energy_use_MWh = 0
#     # Case 1: demand_profile is a list of dictionaries
#     if isinstance(demand_profile, list):
#         for demand in demand_profile:
#             profile = demand["demand_profile"]
#             # Sum the values for electricity, heating, cooling, and DHW demand for the current profile
#             community_energy_use_MWh = (sum(profile["electricity_demand"])
#                                         + sum(profile["heating_demand"])
#                                         + sum(profile["cooling_demand"])
#                                         + sum(profile["dhw_demand"])) / 1000
#             # Add the community energy use to the total energy use
#             Energy_use_MWh += community_energy_use_MWh

#     # Case 2: demand_profile is a single dictionary
#     elif isinstance(demand_profile, dict):
#         profile = demand_profile["demand_profile"]
#         # Sum the values for electricity, heating, cooling, and DHW demand for the current profile
#         community_energy_use_MWh = (sum(profile["electricity_demand"])
#                                     + sum(profile["heating_demand"])
#                                     + sum(profile["cooling_demand"])
#                                     + sum(profile["dhw_demand"])) / 1000
#         # Add the community energy use to the total energy use
#         Energy_use_MWh += community_energy_use_MWh

#     else:
#         raise ValueError("demand_profile must be a list of dictionaries or a single dictionary.")


#     # Create DataFrame for citizen KPIs
#     kpis_community = [
#                 {"id": 0, "name": "Energy_use_[MWh]", "value": Energy_use_MWh, "unit": "MWh"},
#                 {"id": 1, "name": "KPI_peak_heat_demand_[kWh]", "value": KPI_peak_heat_demand, "unit": "kWh"},
#                 {"id": 2, "name": "KPI_peak_elec_demand_[kWh]", "value": KPI_peak_elec_demand, "unit": "kWh"},
#                 {"id": 3, "name": "total_primary_energy_[MWh]", "value": total_primary_energy_MWh, "unit": "MWh"},
#                 {"id": 4, "name": "num_members", "value": num_members, "unit": "a.u."},
#                 {"id": 5, "name": "EquivalentTVHours_[hours]", "value": TV_h, "unit": "kW"},
#                 {"id": 6, "name": "EquivalentstreamingHours_[hours]", "value": streaming_h, "unit": "kW"},
#                 {"id": 7, "name": "PizzaConsumptionComparison_[pizzas]", "value": Pizza_h, "unit": "kW"},
#                 {"id": 8, "name": "BatteryUsageEstimation_[charges]", "value": Battery_charges, "unit": "charge"},
#                 {"id": 9, "name": "ElectricCarChargingEstimation_[charges]", "value": ElCar_charges, "unit": "charge"},
#                 {"id": 10, "name": "WineBottlesProduction_[bottles]", "value": Wine_bottles, "unit": "bottles"},
#                 {"id": 11, "name": "TreesRequiredForCarbonOffset_[Tree]", "value": Trees_number, "unit": "tree"},
#                 {"id": 12, "name": "streamingEmissionsImpact_[hours]", "value": streaming_emissionhours, "unit": "hours"},
#                 {"id": 13, "name": "CarbonEmissionsPerKilometer_[km]", "value": ICV_km, "unit": "km"},
#             ]
    
#     return kpis_community


# def KPI_self_consumption(pv_profile, load_profile):
#     """
#     Calculates the amount of PV energy consumed directly by the building (self-consumed).

#     Parameters:
#         pv_profile (array): Hourly PV generation.
#         load_profile (array): Hourly electricity demand.

#     Returns:
#         float: Self-consumed PV energy [kWh]
#     """
#     return float(np.minimum(pv_profile, load_profile).sum())

# def KPI_self_sufficiency(pv_profile, load_profile):
#     """
#     Calculates how much of the load is covered by the PV generation.

#     Parameters:
#         pv_profile (array): Hourly PV generation.
#         load_profile (array): Hourly electricity demand.

#     Returns:
#         float: Energy covered by PV / total demand [kWh]
#     """
#     total_load = load_profile.sum()
#     if total_load == 0:
#         return 0.0
#     return float(np.minimum(pv_profile, load_profile).sum())


# def debug_building_energy_flows(building_idx, building_id, pv_profile, load_profile, stc_profile, grid_import, self_consumption, stc_generation):
#     print(f"\nDEBUG Building {building_idx + 1} (ID: {building_id})")
#     print(f"  PV gen total       : {pv_profile.sum():.2f} kWh")
#     print(f"  Elec. demand total : {load_profile.sum():.2f} kWh")
#     print(f"  Self-consumed PV   : {self_consumption:.2f} kWh")
#     print(f"  Grid import        : {grid_import:.2f} kWh")
#     print(f"  STC gen total     : {stc_generation:.2f} kWh")
#     print(f"  Load match        : {np.minimum(pv_profile, load_profile).sum():.2f} kWh")
#     print(f"  PV/Load ratio      : {(pv_profile.sum()/load_profile.sum()*100):.2f}%" if load_profile.sum() > 0 else "  ❗ No load detected")

# def pick_carrier_ids(pef_lookup: Dict[int, float],
#                      co2_lookup: Dict[int, float],
#                      name_lookup: Dict[int, str]) -> Tuple[Optional[int], Optional[int]]:
#     # 1) por nombre
#     elec_names = {"electricity", "electric power", "electricidad", "grid electricity"}
#     gas_names  = {"gas", "natural gas", "gas natural"}
#     elec_id = None
#     gas_id  = None

#     for cid, name in name_lookup.items():
#         n = (name or "").lower()
#         if any(tag in n for tag in elec_names):
#             elec_id = cid if elec_id is None else elec_id
#         if any(tag in n for tag in gas_names):
#             gas_id = cid if gas_id is None else gas_id

#     # 2) heurística si el nombre no apareció
#     if elec_id is None:
#         # electricidad típica: PEF 1.5–3.0 (depende del país/año)
#         for cid, pef in pef_lookup.items():
#             if 1.5 <= float(pef) <= 3.0:
#                 elec_id = cid
#                 break
#     if gas_id is None:
#         # gas típico: PEF 1.05–1.3 y CO2 0.15–0.25 kg/kWh
#         for cid, pef in pef_lookup.items():
#             co2 = co2_lookup.get(cid)
#             if co2 is None:
#                 continue
#             if 1.05 <= float(pef) <= 1.3 and 0.15 <= float(co2) <= 0.25:
#                 gas_id = cid
#                 break

#     return elec_id, gas_id


# # Ajusta estos IDs a tu catálogo real:
# SYSTEM_PV       = {83}
# SYSTEM_HP_HEAT  = {63}
# SYSTEM_HP_DHW   = {31}
# SYSTEM_HP_COOL  = {2}
# SYSTEM_STC_HEAT = {71}
# SYSTEM_STC_DHW  = {39}
# # IDs por generation_system (no por system_type)
# GEN_PV        = {83}
# GEN_STC_HEAT  = {71}
# GEN_STC_DHW   = {39}

# def compute_all_kpis_for_building(building: dict, pef_lookup: dict, emission_lookup: dict,
#                                   country_id: int, building_idx: int,
#                                   n_ref: Optional[int] = None,
#                                   elec_id: Optional[int] = None,
#                                   gas_id: Optional[int] = None,
#                                   elec_fallback_pef: Optional[float] = None,
#                                   elec_fallback_co2: Optional[float] = None) -> dict:

#     grid_e, grid_g = get_grid_imports(building, n_ref=n_ref)

#     pv_in,  pv_out  = sum_assets_power(building, gen_system_ids=GEN_PV,          n_ref=n_ref)
#     hpH_in, hpH_out = sum_assets_power(building, system_type_ids=SYSTEM_HP_HEAT, n_ref=n_ref)   # si tus HP ya usan system_type
#     hpD_in, hpD_out = sum_assets_power(building, system_type_ids=SYSTEM_HP_DHW,  n_ref=n_ref)
#     hpC_in, hpC_out = sum_assets_power(building, system_type_ids=SYSTEM_HP_COOL, n_ref=n_ref)
#     stcH_in, stcH_out = sum_assets_power(building, gen_system_ids=GEN_STC_HEAT,  n_ref=n_ref)
#     stcD_in, stcD_out = sum_assets_power(building, gen_system_ids=GEN_STC_DHW,   n_ref=n_ref)

#     # Demandas y perfiles base
#     # Para PEF/CO2: solo compras a red (grid_e)
#     # Para autoconsumo: toda la carga en bus AC = grid_e + consumos eléctricos internos
#     elec_load_for_sc = grid_e + hpH_in + hpD_in + hpC_in
#     pv_profile   = pv_out

#     pv_generation = float(pv_out.sum())
#     stc_generation = float(stcH_out.sum() + stcD_out.sum())
#     electricity_demand = float(grid_e.sum())   # demanda eléctrica final = compras de red (por ahora)
#     grid_import = float(grid_e.sum())

#     # Autoconsumo (kWh) + ratios
#     def kpi_self_consumption(pv, load):
#         return float(np.minimum(pv, load).sum())
#     def kpi_self_sufficiency(pv, load):
#         sc = np.minimum(pv, load).sum()
#         return float(100.0 * sc / load.sum()) if load.sum() > 0 else 0.0

#     self_consumption = kpi_self_consumption(pv_profile, elec_load_for_sc)
#     rate_sc = float(100.0 * self_consumption / pv_generation) if pv_generation > 0 else 0.0
#     rate_ss = kpi_self_sufficiency(pv_profile, elec_load_for_sc)

#     # Si elec_id/gas_id vienen dados desde fuera, úsalos; si no, intenta deducirlos
#     if elec_id is None:
#         elec_id = 12 if 12 in pef_lookup or 12 in emission_lookup else None
#     if gas_id is None:
#         gas_id  = 1  if 1  in pef_lookup or 1  in emission_lookup else None

#     # PEF/CO₂ electricidad
#     if elec_id is not None:
#         pef_e = float(pef_lookup.get(elec_id, elec_fallback_pef if elec_fallback_pef is not None else 1.0))
#         co2_e = float(emission_lookup.get(elec_id, elec_fallback_co2 if elec_fallback_co2 is not None else 0.0))
#     else:
#         pef_e = float(elec_fallback_pef if elec_fallback_pef is not None else 1.0)
#         co2_e = float(elec_fallback_co2 if elec_fallback_co2 is not None else 0.0)

#     # PEF/CO₂ gas
#     pef_g = float(pef_lookup.get(gas_id, 1.1))
#     co2_g = float(emission_lookup.get(gas_id, 0.2))

#     elec_final = grid_e   # kWh finales electricidad (compras de red; PV autoconsumido se añadirá cuando registremos export)
#     gas_final  = grid_g   # kWh finales gas

#     primary_energy = float((elec_final * pef_e).sum() + (gas_final * pef_g).sum())
#     co2_total = float((elec_final * co2_e).sum() + (gas_final * co2_g).sum())

#     return {
#         "Building_ID": building.get("building_id"),
#         "PV_Generation_[kWh]": round(pv_generation, 2),
#         "STC_Generation_[kWh]": round(stc_generation, 2),
#         "Electricity_Demand_[kWh]": round(electricity_demand, 2),
#         "Grid_Import_[kWh]": round(grid_import, 2),
#         "Self_Consumption_[kWh]": round(self_consumption, 2),
#         "Rate_Self_Consumption_[%]": round(rate_sc, 2),
#         "Rate_Self_Sufficiency_[%]": round(rate_ss, 2),
#         "Gas_Consumption_[kWh]": round(float(grid_g.sum()), 2),
#         "Primary_Energy_[kWh]": round(primary_energy, 2),
#         "CO2_Emissions_[kg]": round(co2_total, 2),
#         "Electricity_Load_for_SC_[kWh]": round(float(elec_load_for_sc.sum()), 2),
#     }

# def _fit_length(a: Optional[np.ndarray], n_ref: Optional[int]) -> Optional[np.ndarray]:
#     """Recorta o rellena con 0s para que el array tenga longitud n_ref."""
#     if a is None or n_ref is None:
#         return a
#     if a.size == n_ref:
#         return a
#     if a.size > n_ref:
#         return a[:n_ref]
#     # a.size < n_ref
#     pad = n_ref - a.size
#     return np.pad(a, (0, pad), mode="constant")

# def _as_np(arr):
#     if arr is None:
#         return None
#     return np.asarray(arr, dtype=float)

# def get_scaled_ts(asset, which):
#     ts = asset.get("availability_ts", {}) or {}
#     arr = _as_np(ts.get(f"value_{which}"))
#     if arr is None: return None
#     pmax = asset.get("pmax_scalar")
#     # Si parece perfil normalizado (<=1.5), escala; si ya son kWh absolutos, no escales
#     if pmax is not None and np.nanmax(arr) <= 1.5:
#         return arr * float(pmax)
#     return arr

# def get_grid_imports(building_ctx: Dict[str, Any], n_ref: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
#     gi = building_ctx.get("grid_imports", {}) or {}

#     e = _as_np(gi.get("grid_import_kwh"))
#     g = _as_np(gi.get("gas_import_kwh"))

#     # Fallbacks explícitos
#     if e is None:
#         if g is not None and g.size > 0:
#             e = np.zeros_like(g)
#         else:
#             e = np.zeros(0)

#     if g is None:
#         if e is not None and e.size > 0:
#             g = np.zeros_like(e)
#         else:
#             g = np.zeros(0)

#     # Forzar longitud
#     e = _fit_length(e, n_ref)
#     g = _fit_length(g, n_ref)
#     return e, g


# def _choose_best_nat_record(records, country_pref: Optional[int]):
#     if not records:
#         return None
#     if country_pref is not None:
#         for r in records:
#             if r.get("country_id") == country_pref:
#                 return r
#     for cand in (31, 0, None):
#         for r in records:
#             if r.get("country_id") == cand and (r.get("pef") is not None or r.get("co2_kg_kwh") is not None or
#                                                 r.get("pef_tot") is not None or r.get("f_co2_eq_g_kwh") is not None):
#                 return r
#     return records[0]

# def build_factor_lookups(context: Dict[str, Any], country_pref: Optional[int] = None):
#     """Construye lookups PEF/CO₂ recorriendo carriers dentro de cada generation_system."""
#     pef_lookup: Dict[int, float] = {}
#     co2_lookup: Dict[int, float] = {}
#     name_lookup: Dict[int, str] = {}
#     for bac in context.get("building_asset_context", []) or []:
#         for asset in bac.get("building_energy_asset", []) or []:
#             gs = asset.get("generation_system", {}) or {}
#             for side in ("energy_carrier_input_1", "energy_carrier_input_2",
#                          "energy_carrier_output_1", "energy_carrier_output_2"):
#                 carrier = gs.get(side) or {}
#                 cid = carrier.get("id")
#                 if not cid:
#                     continue
#                 cname = (carrier.get("name") or "").strip()
#                 if cname and cid not in name_lookup:
#                     name_lookup[cid] = cname
#                 recs = carrier.get("national_energy_carrier_production") or []
#                 sel = _choose_best_nat_record(recs, country_pref)
#                 if not sel:
#                     continue
#                 # Admite nombres alternativos del JSON (pef o pef_tot; co2_kg_kwh o f_co2_eq_g_kwh/1000)
#                 pef = sel.get("pef")
#                 if pef is None:
#                     pef = sel.get("pef_tot")
#                 co2 = sel.get("co2_kg_kwh")
#                 if co2 is None and sel.get("f_co2_eq_g_kwh") is not None:
#                     co2 = float(sel["f_co2_eq_g_kwh"]) / 1000.0
#                 if pef is not None and cid not in pef_lookup:
#                     pef_lookup[cid] = float(pef)
#                 if co2 is not None and cid not in co2_lookup:
#                     co2_lookup[cid] = float(co2)
#     return pef_lookup, co2_lookup, name_lookup

# def sum_assets_power(building_ctx: Dict[str, Any], system_type_ids=(), gen_system_ids=(), n_ref: Optional[int] = None):
#     arr_in = None; arr_out = None
#     for asset in building_ctx.get("building_energy_asset", []) or []:
#         gs = asset.get("generation_system", {}) or {}
#         # Permitir filtrar por system_type_id O por generation_system_id
#         if system_type_ids and gs.get("system_type_id") not in system_type_ids:
#             continue
#         if gen_system_ids and (gs.get("id") not in gen_system_ids and asset.get("generation_system_id") not in gen_system_ids):
#             continue

#         a_in  = _fit_length(get_scaled_ts(asset, "input1"),  n_ref)
#         a_out = _fit_length(get_scaled_ts(asset, "output1"), n_ref)
#         if a_in is not None:
#             arr_in = a_in if arr_in is None else (arr_in + a_in)
#         if a_out is not None:
#             arr_out = a_out if arr_out is None else (arr_out + a_out)

#     # Si no hubo nada, crea ceros compatibles
#     if arr_in is None and arr_out is None:
#         e, _ = get_grid_imports(building_ctx, n_ref=n_ref)
#         n = e.size if e is not None else (n_ref or 0)
#         z = np.zeros(n)
#         return z, z
#     if arr_in is None:  arr_in = np.zeros_like(arr_out)
#     if arr_out is None: arr_out = np.zeros_like(arr_in)
#     return arr_in, arr_out


