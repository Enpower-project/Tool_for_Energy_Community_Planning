from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import re


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _to_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _sum_ts(x: Any) -> float:
    """
    Suma segura de series horarias (list/np.array) o números.
    """
    if x is None:
        return 0.0
    if isinstance(x, (int, float)):
        return float(x)
    try:
        arr = np.asarray(x, dtype=float)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        return float(arr.sum())
    except Exception:
        return 0.0


def _safe_get_value(indicators: Dict[str, Any], key: str) -> Any:
    """
    legacy baseline/community_KPIs típico: { "kpi_name": {"value": ..., "unit": ...}, ... }
    """
    item = indicators.get(key)
    if isinstance(item, dict) and "value" in item:
        return item["value"]
    return item


def _sum_demand_profile(demand_profile: Any) -> Tuple[float, float]:
    """
    demand_profile puede ser:
      - list: [{"demand_profile": {...}}, ...]
      - dict: {"demand_profile": {...}}
      - ya directamente {...}
    Devuelve: (electricity_demand_kWh, thermal_demand_kWh)
    thermal = heating + dhw + cooling
    """
    elec = 0.0
    thermal = 0.0

    def _extract(dp_obj: Any) -> Dict[str, Any]:
        if isinstance(dp_obj, dict) and "demand_profile" in dp_obj:
            return dp_obj.get("demand_profile") or {}
        if isinstance(dp_obj, dict):
            return dp_obj
        return {}

    if isinstance(demand_profile, list):
        for b in demand_profile:
            dp = _extract(b)
            elec += _sum_ts(dp.get("electricity_demand"))
            thermal += _sum_ts(dp.get("heating_demand"))
            thermal += _sum_ts(dp.get("dhw_demand"))
            thermal += _sum_ts(dp.get("cooling_demand"))
    elif isinstance(demand_profile, dict):
        dp = _extract(demand_profile)
        elec += _sum_ts(dp.get("electricity_demand"))
        thermal += _sum_ts(dp.get("heating_demand"))
        thermal += _sum_ts(dp.get("dhw_demand"))
        thermal += _sum_ts(dp.get("cooling_demand"))

    return float(elec), float(thermal)


# -------------------------------------------------------------------
# Citizen KPIs (solo desde SAVINGS)
# -------------------------------------------------------------------
def citizen_kpis_from_savings(saved_primary_kwh: float, avoided_co2_kg: float) -> Dict[str, float]:
    """
    Citizen KPIs calculados SOLO a partir de ahorros (energía primaria y CO2 evitado).
    """
    factors = {
        "f_tv": 0.250,
        "f_streaming": 0.077,
        "f_pizza": 0.667,
        "f_battery": 68.7,
        "f_km": 354,
        "f_elcar": 0.196,
        "f_wine": 540,
        "f_trees": 25,
        "f_em_net": 0.036,
        "f_ICV": 0.1163,
    }

    pe = max(0.0, float(saved_primary_kwh or 0.0))
    co2 = max(0.0, float(avoided_co2_kg or 0.0))

    return {
        "EquivalentTVHours_[h]": round(pe / factors["f_tv"], 3) if factors["f_tv"] else 0.0,
        "EquivalentstreamingHours_[h]": round(pe / factors["f_streaming"], 3) if factors["f_streaming"] else 0.0,
        "PizzaConsumptionComparison_[pizza]": round(pe / factors["f_pizza"], 3) if factors["f_pizza"] else 0.0,
        "BatteryUsageEstimation_[charges]": round(pe / factors["f_battery"], 3) if factors["f_battery"] else 0.0,
        "ElectricCarChargingEstimation_[charges]": round(pe / (factors["f_km"] * factors["f_elcar"]), 3)
        if (factors["f_km"] * factors["f_elcar"]) else 0.0,
        "WineBottlesProduction_[bottles]": round(pe / factors["f_wine"], 3) if factors["f_wine"] else 0.0,
        "TreesRequiredForCarbonOffset_[trees]": round(co2 / factors["f_trees"], 3) if factors["f_trees"] else 0.0,
        "streamingEmissionsImpact_[hours]": round(co2 / factors["f_em_net"], 3) if factors["f_em_net"] else 0.0,
        "CarbonEmissionsPerKilometer_[km]": round(co2 / factors["f_ICV"], 3) if factors["f_ICV"] else 0.0,
    }


# -------------------------------------------------------------------
# CORE KPIs (mismo formato baseline y scenario)
# -------------------------------------------------------------------
CORE_TOTAL_KEYS = (
    "Renewable_Generation_[kWh]",
    "PV_Generation_[kWh]",
    "STC_Generation_[kWh]",
    "Electricity_Demand_[kWh]",
    "Thermal_Demand_[kWh]",
    "Energy_Demand_Total_[kWh]",
    "Self_Consumption_[kWh]",
    "Rate_Self_Consumption_[%]",
    "Rate_Self_Sufficiency_[%]",
    "Grid_Import_[kWh]",
    "Gas_Consumption_[kWh]",
    "Primary_Energy_[kWh]",
    "CO2_Emissions_[kg]",
    "Energy_Costs_[€]",
)

CORE_BUILDING_KEYS = (
    "Building_ID",
    "Renewable_Generation_[kWh]",
    "PV_Generation_[kWh]",
    "STC_Generation_[kWh]",
    "Electricity_Demand_[kWh]",
    "Thermal_Demand_[kWh]",
    "Energy_Demand_Total_[kWh]",
    "Self_Consumption_[kWh]",
    "Rate_Self_Consumption_[%]",
    "Rate_Self_Sufficiency_[%]",
    "Grid_Import_[kWh]",
    "Gas_Consumption_[kWh]",
    "Primary_Energy_[kWh]",
    "CO2_Emissions_[kg]",
    "Energy_Costs_[€]",
)


# -------------------------------------------------------------------
# BASELINE -> FRONT (CORE)
# -------------------------------------------------------------------
def front_from_baseline(
    baseline_community_indicators: Dict[str, Any],
    demand_profile: Optional[Any] = None,
    citizen_kpis_per_building: Optional[Dict[Any, List[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    """
    Definition
    ----------
    Transforms baseline results (legacy community_KPIs output + thermagrid demand profiles + per-building KPI lists)
    into a stable "CORE KPIs" payload for the front-end.

    Key rule (baseline, consistent with scenario):
    - Electricity_Demand_[kWh] is the electricity bus load used for self-consumption/self-sufficiency:
        Electricity_Demand_[kWh] = Grid_Import_[kWh] + Self_Consumption_[kWh]
      (If no PV/self-consumption exists, it falls back to demand_profile electricity demand.)

    Parameters
    ----------
    baseline_community_indicators : Dict[str, Any]
        Output of community_KPIs(...) for baseline (legacy aggregated structure).
    demand_profile : Optional[Any]
        Thermagrid demand profiles (list per building or single dict). Used to compute thermal demand totals
        and as a fallback for electricity demand if self-consumption cannot be inferred.
    citizen_kpis_per_building : Optional[Dict[Any, List[Dict[str, Any]]]]
        Output of get_indicators_from_baseline(...) keyed by building identifier.
        Each value is a list of KPI dicts with at least {"name": ..., "value": ...}.

    Returns
    -------
    Dict[str, Any]
        A dictionary with:
          - "totals": community CORE KPIs (baseline)
          - "buildings": list of per-building CORE KPIs
          - "dwellings": alias of "buildings" (building == dwelling)
    """

    def _kpi_list_to_map(kpi_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k in (kpi_list or []):
            if not isinstance(k, dict):
                continue
            name = k.get("name")
            if not name:
                continue
            out[name] = k.get("value")
        return out

    def _sort_building_ids(ids: List[Any]) -> List[Any]:
        def _key(x: Any):
            s = str(x)
            m = re.search(r"(\d+)$", s)
            return int(m.group(1)) if m else 10**9
        return sorted(ids, key=_key)

    # Demand totals (baseline definition: thermal = heating + dhw + cooling)
    elec_demand_from_dp, thermal_demand = _sum_demand_profile(demand_profile) if demand_profile is not None else (0.0, 0.0)

    # Community imports (legacy: can be series or scalar)
    grid_import_comm = _sum_ts(_safe_get_value(baseline_community_indicators, "final_energy_electricity_grid"))
    gas_comm = _sum_ts(_safe_get_value(baseline_community_indicators, "final_energy_gas"))

    # Community primary / CO2 (legacy: Total_co2 usually in grams)
    primary_comm = _sum_ts(_safe_get_value(baseline_community_indicators, "total_primary_energy_[kWh]"))
    co2_g = _safe_get_value(baseline_community_indicators, "Total_co2")
    co2_comm_kg = (_sum_ts(co2_g) / 1000.0) if co2_g is not None else 0.0

    # Community costs (legacy: households + non-households)
    costs_comm = (
        _sum_ts(_safe_get_value(baseline_community_indicators, "households_costs_[€]")) +
        _sum_ts(_safe_get_value(baseline_community_indicators, "non_households_costs_[€]"))
    )

    # Per-building outputs (CORE)
    buildings_out: List[Dict[str, Any]] = []

    # Aggregate PV + self-consumption from per-building lists (baseline may have PV)
    pv_comm = 0.0
    stc_comm = 0.0  # baseline STC is not provided by legacy indicators; kept for schema stability
    self_consumption_comm = 0.0

    if isinstance(citizen_kpis_per_building, dict) and citizen_kpis_per_building:
        building_ids = _sort_building_ids(list(citizen_kpis_per_building.keys()))

        # Demand profile per building (if list)
        dp_list = demand_profile if isinstance(demand_profile, list) else None

        for idx, b_id in enumerate(building_ids):
            m = _kpi_list_to_map(citizen_kpis_per_building.get(b_id) or [])

            pv_b = _sum_ts(m.get("Total_PV_[kWh]"))
            sc_b = _sum_ts(m.get("Total_self_consumption"))

            # Optional keys if available in the per-building KPI list
            grid_b = _sum_ts(m.get("final_energy_electricity_grid"))
            gas_b = _sum_ts(m.get("final_energy_gas"))
            primary_b = _sum_ts(m.get("total_primary_energy_[kWh]"))

            co2_b_g = m.get("Total_co2")
            co2_b_kg = (_sum_ts(co2_b_g) / 1000.0) if co2_b_g is not None else 0.0

            costs_b = _sum_ts(m.get("households_costs_[€]")) + _sum_ts(m.get("non_households_costs_[€]"))

            # Thermal demand per building (from thermagrid, if available)
            thermal_b = 0.0
            if dp_list is not None and idx < len(dp_list):
                dp_b = (dp_list[idx] or {}).get("demand_profile") or {}
                thermal_b = (
                    _sum_ts(dp_b.get("heating_demand")) +
                    _sum_ts(dp_b.get("dhw_demand")) +
                    _sum_ts(dp_b.get("cooling_demand"))
                )

            # Electricity bus load (baseline definition consistent with scenario)
            # If grid import by building is available, use it; else keep minimum coherent definition.
            if grid_b > 0 or sc_b > 0:
                elec_b = grid_b + sc_b
            else:
                # fallback to thermagrid electricity demand if available
                if dp_list is not None and idx < len(dp_list):
                    dp_b = (dp_list[idx] or {}).get("demand_profile") or {}
                    elec_b = _sum_ts(dp_b.get("electricity_demand"))
                else:
                    elec_b = 0.0

            # Renewables (baseline: PV known, STC unknown here -> 0)
            stc_b = 0.0
            ren_b = pv_b + stc_b

            # Rates (same equations as scenario)
            rate_sc_b = (100.0 * sc_b / pv_b) if pv_b > 0 else 0.0
            rate_ss_b = (100.0 * sc_b / elec_b) if elec_b > 0 else 0.0

            buildings_out.append({
                "Building_ID": b_id,
                "Renewable_Generation_[kWh]": round(ren_b, 2),
                "PV_Generation_[kWh]": round(pv_b, 2),
                "STC_Generation_[kWh]": round(stc_b, 2),

                "Electricity_Demand_[kWh]": round(elec_b, 2),
                "Thermal_Demand_[kWh]": round(thermal_b, 2),
                "Energy_Demand_Total_[kWh]": round(elec_b + thermal_b, 2),

                "Self_Consumption_[kWh]": round(sc_b, 2),
                "Rate_Self_Consumption_[%]": round(min(100.0, max(0.0, rate_sc_b)), 2),
                "Rate_Self_Sufficiency_[%]": round(min(100.0, max(0.0, rate_ss_b)), 2),

                # These fields are kept for schema stability (even if not shown in the UI cards)
                "Grid_Import_[kWh]": round(grid_b, 2),
                "Gas_Consumption_[kWh]": round(gas_b, 2),
                "Primary_Energy_[kWh]": round(primary_b, 2),
                "CO2_Emissions_[kg]": round(co2_b_kg, 2),
                "Energy_Costs_[€]": round(costs_b, 2),
            })

            pv_comm += pv_b
            self_consumption_comm += sc_b

    # Community renewables
    ren_comm = pv_comm + stc_comm

    # Community electricity demand (bus load)
    elec_load_for_sc_comm = grid_import_comm + self_consumption_comm
    elec_demand_comm = elec_load_for_sc_comm if elec_load_for_sc_comm > 0 else float(elec_demand_from_dp)

    # Rates (same equations as scenario)
    rate_sc_comm = (100.0 * self_consumption_comm / pv_comm) if pv_comm > 0 else 0.0
    rate_ss_comm = (100.0 * self_consumption_comm / elec_demand_comm) if elec_demand_comm > 0 else 0.0

    totals = {
        "Renewable_Generation_[kWh]": round(ren_comm, 2),
        "PV_Generation_[kWh]": round(pv_comm, 2),
        "STC_Generation_[kWh]": round(stc_comm, 2),

        "Electricity_Demand_[kWh]": round(elec_demand_comm, 2),
        "Thermal_Demand_[kWh]": round(thermal_demand, 2),
        "Energy_Demand_Total_[kWh]": round(elec_demand_comm + thermal_demand, 2),

        "Self_Consumption_[kWh]": round(self_consumption_comm, 2),
        "Rate_Self_Consumption_[%]": round(min(100.0, max(0.0, rate_sc_comm)), 2),
        "Rate_Self_Sufficiency_[%]": round(min(100.0, max(0.0, rate_ss_comm)), 2),

        # Kept for stability (may be useful to compute scenario savings and debug)
        "Grid_Import_[kWh]": round(grid_import_comm, 2),
        "Gas_Consumption_[kWh]": round(gas_comm, 2),
        "Primary_Energy_[kWh]": round(primary_comm, 2),
        "CO2_Emissions_[kg]": round(co2_comm_kg, 2),
        "Energy_Costs_[€]": round(costs_comm, 2),
    }

    return {
        "totals": totals,
        "buildings": buildings_out,
        "dwellings": buildings_out,
    }


# -------------------------------------------------------------------
# SCENARIO -> FRONT (CORE)
# -------------------------------------------------------------------
def front_from_scenario(
    scenario_totals: Dict[str, Any],
    baseline_totals: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    NOTE: dejo tu implementación tal cual (no la toco aquí).
    """
    # ... (tu código existente)
    return {
        "totals": scenario_totals,
        "savings": {},
        "citizen_kpis": {},
    }


# from typing import Any, Dict, List, Optional, Tuple
# import numpy as np


# # -------------------------------------------------------------------
# # Helpers
# # -------------------------------------------------------------------
# def _to_float(x: Any) -> float:
#     try:
#         return float(x)
#     except Exception:
#         return 0.0


# def _sum_ts(x: Any) -> float:
#     """
#     Suma segura de series horarias (list/np.array) o números.
#     """
#     if x is None:
#         return 0.0
#     if isinstance(x, (int, float)):
#         return float(x)
#     try:
#         arr = np.asarray(x, dtype=float)
#         arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
#         return float(arr.sum())
#     except Exception:
#         return 0.0


# def _safe_get_value(indicators: Dict[str, Any], key: str) -> Any:
#     """
#     legacy baseline/community_KPIs típico: { "kpi_name": {"value": ..., "unit": ...}, ... }
#     """
#     item = indicators.get(key)
#     if isinstance(item, dict) and "value" in item:
#         return item["value"]
#     return item


# def _sum_demand_profile(demand_profile: Any) -> Tuple[float, float]:
#     """
#     demand_profile puede ser:
#       - list: [{"demand_profile": {...}}, ...]
#       - dict: {"demand_profile": {...}}
#       - ya directamente {...}
#     Devuelve: (electricity_demand_kWh, thermal_demand_kWh)
#     thermal = heating + dhw + cooling
#     """
#     elec = 0.0
#     thermal = 0.0

#     def _extract(dp_obj: Any) -> Dict[str, Any]:
#         if isinstance(dp_obj, dict) and "demand_profile" in dp_obj:
#             return dp_obj.get("demand_profile") or {}
#         if isinstance(dp_obj, dict):
#             return dp_obj
#         return {}

#     if isinstance(demand_profile, list):
#         for b in demand_profile:
#             dp = _extract(b)
#             elec += _sum_ts(dp.get("electricity_demand"))
#             thermal += _sum_ts(dp.get("heating_demand"))
#             thermal += _sum_ts(dp.get("dhw_demand"))
#             thermal += _sum_ts(dp.get("cooling_demand"))
#     elif isinstance(demand_profile, dict):
#         dp = _extract(demand_profile)
#         elec += _sum_ts(dp.get("electricity_demand"))
#         thermal += _sum_ts(dp.get("heating_demand"))
#         thermal += _sum_ts(dp.get("dhw_demand"))
#         thermal += _sum_ts(dp.get("cooling_demand"))

#     return float(elec), float(thermal)


# # -------------------------------------------------------------------
# # Citizen KPIs (solo desde SAVINGS)
# # -------------------------------------------------------------------
# def citizen_kpis_from_savings(saved_primary_kwh: float, avoided_co2_kg: float) -> Dict[str, float]:
#     """
#     Citizen KPIs calculados SOLO a partir de ahorros (energía primaria y CO2 evitado).
#     """
#     factors = {
#         "f_tv": 0.250,
#         "f_streaming": 0.077,
#         "f_pizza": 0.667,
#         "f_battery": 68.7,
#         "f_km": 354,
#         "f_elcar": 0.196,
#         "f_wine": 540,
#         "f_trees": 25,
#         "f_em_net": 0.036,
#         "f_ICV": 0.1163,
#     }

#     pe = max(0.0, float(saved_primary_kwh or 0.0))
#     co2 = max(0.0, float(avoided_co2_kg or 0.0))

#     return {
#         "EquivalentTVHours_[h]": round(pe / factors["f_tv"], 3) if factors["f_tv"] else 0.0,
#         "EquivalentstreamingHours_[h]": round(pe / factors["f_streaming"], 3) if factors["f_streaming"] else 0.0,
#         "PizzaConsumptionComparison_[pizza]": round(pe / factors["f_pizza"], 3) if factors["f_pizza"] else 0.0,
#         "BatteryUsageEstimation_[charges]": round(pe / factors["f_battery"], 3) if factors["f_battery"] else 0.0,
#         "ElectricCarChargingEstimation_[charges]": round(pe / (factors["f_km"] * factors["f_elcar"]), 3)
#         if (factors["f_km"] * factors["f_elcar"]) else 0.0,
#         "WineBottlesProduction_[bottles]": round(pe / factors["f_wine"], 3) if factors["f_wine"] else 0.0,
#         "TreesRequiredForCarbonOffset_[trees]": round(co2 / factors["f_trees"], 3) if factors["f_trees"] else 0.0,
#         "streamingEmissionsImpact_[hours]": round(co2 / factors["f_em_net"], 3) if factors["f_em_net"] else 0.0,
#         "CarbonEmissionsPerKilometer_[km]": round(co2 / factors["f_ICV"], 3) if factors["f_ICV"] else 0.0,
#     }


# # -------------------------------------------------------------------
# # CORE KPIs (mismo formato baseline y scenario)
# # -------------------------------------------------------------------
# CORE_TOTAL_KEYS = (
#     "Renewable_Generation_[kWh]",
#     "PV_Generation_[kWh]",
#     "STC_Generation_[kWh]",
#     "Electricity_Demand_[kWh]",
#     "Thermal_Demand_[kWh]",
#     "Energy_Demand_Total_[kWh]",
#     "Self_Consumption_[kWh]",
#     "Rate_Self_Consumption_[%]",
#     "Rate_Self_Sufficiency_[%]",
#     "Grid_Import_[kWh]",
#     "Gas_Consumption_[kWh]",
#     "Primary_Energy_[kWh]",
#     "CO2_Emissions_[kg]",
#     "Energy_Costs_[€]",
# )

# CORE_BUILDING_KEYS = (
#     "Building_ID",
#     "Renewable_Generation_[kWh]",
#     "PV_Generation_[kWh]",
#     "STC_Generation_[kWh]",
#     "Electricity_Demand_[kWh]",
#     "Thermal_Demand_[kWh]",
#     "Energy_Demand_Total_[kWh]",
#     "Self_Consumption_[kWh]",
#     "Rate_Self_Consumption_[%]",
#     "Rate_Self_Sufficiency_[%]",
#     "Grid_Import_[kWh]",
#     "Gas_Consumption_[kWh]",
#     "Primary_Energy_[kWh]",
#     "CO2_Emissions_[kg]",
#     "Energy_Costs_[€]",
# )


# # -------------------------------------------------------------------
# # BASELINE -> FRONT (CORE)
# # -------------------------------------------------------------------
# def front_from_baseline(
#     baseline_community_indicators: Dict[str, Any],
#     demand_profile: Optional[Any] = None,
#     citizen_kpis_per_building: Optional[Dict[Any, List[Dict[str, Any]]]] = None,
# ) -> Dict[str, Any]:
#     """
#     Baseline -> CORE KPIs (sin citizen, sin savings).

#     Inputs:
#       - baseline_community_indicators: salida de community_KPIs(...) (legacy agregado)
#       - demand_profile: el mismo demand_profile que ya calculas en baseline (thermagrid)
#       - citizen_kpis_per_building: salida de get_indicators_from_baseline(...) (por building)
#         (aunque el nombre diga citizen, aquí dentro también viene PV y self_consumption por hora)

#     Nota importante:
#       Puede haber PV en baseline. Si existe:
#         - PV_Generation = suma total_PV
#         - Self_Consumption = suma total_self_consumption
#         - Grid_Import = final_energy_electricity_grid (ya representa la parte comprada a red)
#         - Electric demand "del bus" = Self_Consumption + Grid_Import
#     """

#     # Demandas (misma definición para baseline y scenario)
#     elec_demand_from_dp, thermal_demand = _sum_demand_profile(demand_profile) if demand_profile is not None else (0.0, 0.0)

#     # Grid & gas (series horarias en legacy)
#     grid_import = _sum_ts(_safe_get_value(baseline_community_indicators, "final_energy_electricity_grid"))
#     gas = _sum_ts(_safe_get_value(baseline_community_indicators, "final_energy_gas"))

#     # Primary energy / CO2 (legacy: Total_co2 suele venir en g)
#     primary = _sum_ts(_safe_get_value(baseline_community_indicators, "total_primary_energy_[kWh]"))
#     co2_g = _safe_get_value(baseline_community_indicators, "Total_co2")
#     co2_kg = _sum_ts(co2_g) / 1000.0 if co2_g is not None else 0.0

#     # Costs legacy: households + non-households
#     costs = (
#         _sum_ts(_safe_get_value(baseline_community_indicators, "households_costs_[€]")) +
#         _sum_ts(_safe_get_value(baseline_community_indicators, "non_households_costs_[€]"))
#     )

#     # PV / self-consumption baseline (si hay citizen_kpis_per_building)
#     pv = 0.0
#     self_consumption = 0.0
#     buildings_out: List[Dict[str, Any]] = []

#     if isinstance(citizen_kpis_per_building, dict) and citizen_kpis_per_building:
#         for b_id, kpi_list in citizen_kpis_per_building.items():
#             # kpi_list: [{id,..,"name": "...", "value": ...}, ...]
#             m = {k.get("name"): k.get("value") for k in (kpi_list or []) if isinstance(k, dict)}

#             pv_b = _sum_ts(m.get("Total_PV_[kWh]"))
#             sc_b = _sum_ts(m.get("Total_self_consumption"))

#             # si no hay PV, sc_b debería ser 0 igualmente
#             pv += pv_b
#             self_consumption += sc_b

#             # baseline no tiene STC aquí (si algún día lo metes, se puede añadir igual)
#             stc_b = 0.0
#             ren_b = pv_b + stc_b

#             # electricidad "del bus" = autoconsumida + comprada a red.
#             # PERO por building no tenemos grid import desagregado fiable aquí.
#             # (podríamos hacerlo si citizen KPIs incluye final_energy_electricity_grid por building;
#             #  ahora mismo no lo veo garantizado, así que lo dejamos en 0 en building).
#             elec_b = sc_b  # mínimo coherente; si más adelante añades grid por building, aquí se suma.
#             thermal_b = 0.0

#             rate_sc_b = (100.0 * sc_b / pv_b) if pv_b > 0 else 0.0
#             rate_ss_b = (100.0 * sc_b / elec_b) if elec_b > 0 else 0.0

#             buildings_out.append({
#                 "Building_ID": b_id,
#                 "Renewable_Generation_[kWh]": round(ren_b, 2),
#                 "PV_Generation_[kWh]": round(pv_b, 2),
#                 "STC_Generation_[kWh]": 0.0,
#                 "Electricity_Demand_[kWh]": round(elec_b, 2),
#                 "Thermal_Demand_[kWh]": round(thermal_b, 2),
#                 "Energy_Demand_Total_[kWh]": round(elec_b + thermal_b, 2),
#                 "Self_Consumption_[kWh]": round(sc_b, 2),
#                 "Rate_Self_Consumption_[%]": round(rate_sc_b, 2),
#                 "Rate_Self_Sufficiency_[%]": round(rate_ss_b, 2),
#                 "Grid_Import_[kWh]": 0.0,
#                 "Gas_Consumption_[kWh]": 0.0,
#                 "Primary_Energy_[kWh]": 0.0,
#                 "CO2_Emissions_[kg]": 0.0,
#                 "Energy_Costs_[€]": 0.0,
#             })

#     # Renewables baseline
#     stc = 0.0
#     ren = pv + stc

#     # Electricidad demand coherente (bus eléctrico):
#     # si hay PV: load = grid_import + self_consumption
#     # si no hay PV: load = grid_import (y self_consumption = 0)
#     elec_load_for_sc = grid_import + self_consumption
#     elec_demand = elec_load_for_sc if elec_load_for_sc > 0 else float(elec_demand_from_dp)

#     # Rates (mismas ecuaciones que scenario)
#     rate_sc = (100.0 * self_consumption / pv) if pv > 0 else 0.0
#     rate_ss = (100.0 * self_consumption / elec_demand) if elec_demand > 0 else 0.0

#     totals = {
#         "Renewable_Generation_[kWh]": round(ren, 2),
#         "PV_Generation_[kWh]": round(pv, 2),
#         "STC_Generation_[kWh]": round(stc, 2),

#         "Electricity_Demand_[kWh]": round(elec_demand, 2),
#         "Thermal_Demand_[kWh]": round(thermal_demand, 2),
#         "Energy_Demand_Total_[kWh]": round(elec_demand + thermal_demand, 2),

#         "Self_Consumption_[kWh]": round(self_consumption, 2),
#         "Rate_Self_Consumption_[%]": round(rate_sc, 2),
#         "Rate_Self_Sufficiency_[%]": round(rate_ss, 2),

#         "Grid_Import_[kWh]": round(grid_import, 2),
#         "Gas_Consumption_[kWh]": round(gas, 2),

#         "Primary_Energy_[kWh]": round(primary, 2),
#         "CO2_Emissions_[kg]": round(co2_kg, 3),
#         "Energy_Costs_[€]": round(costs, 2),
#     }

#     return {"totals": totals, "buildings": buildings_out}


# # -------------------------------------------------------------------
# # SCENARIO -> FRONT (CORE)
# # -------------------------------------------------------------------
# def front_from_scenario(
#     scenario_kpis: Dict[str, Any],
#     scenario_context: Optional[Dict[str, Any]] = None,
# ) -> Dict[str, Any]:
#     """
#     Scenario -> CORE KPIs (sin citizen, sin savings).
#     scenario_kpis: salida de calculate_energy_kpis_from_context => {"totals":..., "buildings":[...]}

#     Nota:
#       - Self_Consumption se basa en "PV - exports" (lo que no se exporta).
#       - Rate_SS se define como: self_consumption / electricity_demand (electric load del bus eléctrico, incl. HP)
#     """

#     tin = scenario_kpis.get("totals") or {}
#     bin_list = scenario_kpis.get("buildings") or []

#     pv = _to_float(tin.get("PV_Generation_[kWh]"))
#     stc = _to_float(tin.get("STC_Generation_[kWh]"))
#     ren = pv + stc

#     # Electricidad demand: preferimos la que incluye consumos eléctricos internos (HP)
#     elec_demand = _to_float(tin.get("Electricity_Load_for_SC_[kWh]")) or _to_float(tin.get("Electricity_Demand_[kWh]"))

#     # Thermal demand: si hay building_consumption en el contexto, lo sumas aquí.
#     # Si no lo pasas, queda 0 (mantenemos coherencia con tu pipeline actual).
#     thermal_demand = 0.0
#     if scenario_context:
#         # si algún día quieres, aquí puedes sumar heat/dhw/cool desde building_consumption
#         pass

#     grid_import = _to_float(tin.get("Grid_Import_[kWh]"))
#     gas = _to_float(tin.get("Gas_Consumption_[kWh]"))
#     primary = _to_float(tin.get("Primary_Energy_[kWh]"))
#     co2 = _to_float(tin.get("CO2_Emissions_[kg]"))
#     costs = _to_float(tin.get("Energy_Costs_[€]"))

#     # Autoconsumo coherente: PV no exportada
#     self_consumption = _to_float(tin.get("Self_Consumption_[kWh]"))
#     if self_consumption <= 0:
#         exports = _to_float(tin.get("Electricity_Exports_[kWh]"))
#         self_consumption = max(0.0, pv - exports)

#     rate_sc = (100.0 * self_consumption / pv) if pv > 0 else 0.0
#     rate_ss = (100.0 * self_consumption / elec_demand) if elec_demand > 0 else 0.0

#     totals = {
#         "Renewable_Generation_[kWh]": round(ren, 2),
#         "PV_Generation_[kWh]": round(pv, 2),
#         "STC_Generation_[kWh]": round(stc, 2),

#         "Electricity_Demand_[kWh]": round(elec_demand, 2),
#         "Thermal_Demand_[kWh]": round(thermal_demand, 2),
#         "Energy_Demand_Total_[kWh]": round(elec_demand + thermal_demand, 2),

#         "Self_Consumption_[kWh]": round(self_consumption, 2),
#         "Rate_Self_Consumption_[%]": round(rate_sc, 2),
#         "Rate_Self_Sufficiency_[%]": round(rate_ss, 2),

#         "Grid_Import_[kWh]": round(grid_import, 2),
#         "Gas_Consumption_[kWh]": round(gas, 2),

#         "Primary_Energy_[kWh]": round(primary, 2),
#         "CO2_Emissions_[kg]": round(co2, 3),
#         "Energy_Costs_[€]": round(costs, 2),
#     }

#     # Buildings (solo reducción)
#     out_buildings: List[Dict[str, Any]] = []
#     for b in bin_list:
#         pv_b = _to_float(b.get("PV_Generation_[kWh]"))
#         stc_b = _to_float(b.get("STC_Generation_[kWh]"))
#         ren_b = pv_b + stc_b

#         elec_b = _to_float(b.get("Electricity_Load_for_SC_[kWh]")) or _to_float(b.get("Electricity_Demand_[kWh]"))
#         self_b = _to_float(b.get("Self_Consumption_[kWh]"))

#         rate_sc_b = (100.0 * self_b / pv_b) if pv_b > 0 else 0.0
#         rate_ss_b = (100.0 * self_b / elec_b) if elec_b > 0 else 0.0

#         out_buildings.append({
#             "Building_ID": b.get("Building_ID"),
#             "Renewable_Generation_[kWh]": round(ren_b, 2),
#             "PV_Generation_[kWh]": round(pv_b, 2),
#             "STC_Generation_[kWh]": round(stc_b, 2),

#             "Electricity_Demand_[kWh]": round(elec_b, 2),
#             "Thermal_Demand_[kWh]": 0.0,
#             "Energy_Demand_Total_[kWh]": round(elec_b, 2),

#             "Self_Consumption_[kWh]": round(self_b, 2),
#             "Rate_Self_Consumption_[%]": round(rate_sc_b, 2),
#             "Rate_Self_Sufficiency_[%]": round(rate_ss_b, 2),

#             "Grid_Import_[kWh]": round(_to_float(b.get("Grid_Import_[kWh]")), 2),
#             "Gas_Consumption_[kWh]": round(_to_float(b.get("Gas_Consumption_[kWh]")), 2),

#             "Primary_Energy_[kWh]": round(_to_float(b.get("Primary_Energy_[kWh]")), 2),
#             "CO2_Emissions_[kg]": round(_to_float(b.get("CO2_Emissions_[kg]")), 3),
#             "Energy_Costs_[€]": round(_to_float(b.get("Energy_Costs_[€]")), 2),
#         })

#     return {"totals": totals, "buildings": out_buildings}


# # -------------------------------------------------------------------
# # Savings + Citizen (solo escenarios)
# # -------------------------------------------------------------------
# def add_savings_and_citizen_to_scenario(
#     scenario_core: Dict[str, Any],
#     baseline_core: Dict[str, Any],
# ) -> Dict[str, Any]:
#     """
#     Devuelve:
#     {
#       "totals": {...core...},
#       "buildings": [...core...],
#       "savings": {
#          "totals": {... + citizen_kpis},
#          "buildings": [...]
#       }
#     }

#     Citizen KPIs SOLO dentro de savings.totals.
#     """

#     s_tot = scenario_core.get("totals") or {}
#     b_tot = baseline_core.get("totals") or {}

#     def get(k: str) -> Tuple[float, float]:
#         return (_to_float(s_tot.get(k)), _to_float(b_tot.get(k)))

#     s_primary, b_primary = get("Primary_Energy_[kWh]")
#     s_co2, b_co2 = get("CO2_Emissions_[kg]")
#     s_cost, b_cost = get("Energy_Costs_[€]")

#     saved_primary = max(0.0, b_primary - s_primary)
#     avoided_co2 = max(0.0, b_co2 - s_co2)
#     money_saved = max(0.0, b_cost - s_cost)

#     s_ren, b_ren = get("Renewable_Generation_[kWh]")
#     extra_renewable = max(0.0, s_ren - b_ren)

#     savings_totals = {
#         "Primary_Energy_Saved_[kWh]": round(saved_primary, 2),
#         "CO2_Avoided_[kg]": round(avoided_co2, 3),
#         "Money_Saved_[€]": round(money_saved, 2),
#         "Extra_Renewable_Generation_[kWh]": round(extra_renewable, 2),
#     }

#     # Citizen KPIs SOLO en savings.totals
#     savings_totals.update(citizen_kpis_from_savings(saved_primary_kwh=saved_primary, avoided_co2_kg=avoided_co2))

#     # Savings por building (si baseline buildings existe; si no, vacío)
#     bld_s = scenario_core.get("buildings") or []
#     bld_b = baseline_core.get("buildings") or []
#     b_map = {x.get("Building_ID"): x for x in bld_b if isinstance(x, dict)}

#     savings_buildings: List[Dict[str, Any]] = []
#     for sb in bld_s:
#         bid = sb.get("Building_ID")
#         bb = b_map.get(bid, {})

#         s_pe = _to_float(sb.get("Primary_Energy_[kWh]"))
#         b_pe = _to_float(bb.get("Primary_Energy_[kWh]"))
#         s_c = _to_float(sb.get("CO2_Emissions_[kg]"))
#         b_c = _to_float(bb.get("CO2_Emissions_[kg]"))
#         s_cost_b = _to_float(sb.get("Energy_Costs_[€]"))
#         b_cost_b = _to_float(bb.get("Energy_Costs_[€]"))

#         savings_buildings.append({
#             "Building_ID": bid,
#             "Primary_Energy_Saved_[kWh]": round(max(0.0, b_pe - s_pe), 2),
#             "CO2_Avoided_[kg]": round(max(0.0, b_c - s_c), 3),
#             "Money_Saved_[€]": round(max(0.0, b_cost_b - s_cost_b), 2),
#         })

#     out = dict(scenario_core)
#     out["savings"] = {"totals": savings_totals, "buildings": savings_buildings}
#     return out
