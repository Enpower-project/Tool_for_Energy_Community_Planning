# =============================================================================
# calculate_kpis_from_context.py
# =============================================================================
import json
from pathlib import Path
import numpy as np

from api.services.scripts_enpower.kpi_module.KPI_module import (
    build_factor_lookups,
    compute_all_kpis_for_building,
    pick_carrier_ids,
)
from api.services.scripts_enpower.kpi_module import KPI_module as KM


# -----------------------------
# helpers
# -----------------------------
def _sum_ts(x) -> float:
    """Safe sum for list/np arrays/scalars."""
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


def _get_len_ts_from_building(b) -> int:
    """Try to infer timestep count from any available series."""
    try:
        gi = ((b.get("grid_imports") or {}).get("grid_import_kwh")) or []
        if isinstance(gi, list) and len(gi) > 0:
            return len(gi)
    except Exception:
        pass
    return 8760


def _sum_wind_generation_from_building_assets(b) -> float:
    """
    Wind gen: sum availability_ts.value_output1 for assets with generation_system_id == 132
    """
    total = 0.0
    for a in (b.get("building_energy_asset") or []):
        try:
            if a.get("generation_system_id") == 132:
                ts = (a.get("availability_ts") or {}).get("value_output1")
                total += _sum_ts(ts)
        except Exception:
            continue
    return total


def _make_demand_profile_from_ctx(building_ctx, n_ref=None):
    bc = (building_ctx.get("building_consumption") or {})

    def to_np(key):
        arr = np.asarray(bc.get(key) or [], dtype=float)
        if n_ref is not None and arr.size != n_ref:
            if arr.size > n_ref:
                arr = arr[:n_ref]
            else:
                arr = np.pad(arr, (0, n_ref - arr.size), mode="constant")
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        return arr

    return {
        "demand_profile": {
            "electricity_demand": to_np("elec_consumption"),
            "heating_demand": to_np("heat_consumption"),
            "cooling_demand": to_np("cool_consumption"),
            "dhw_demand": to_np("dhw_consumption"),
        }
    }


def calculate_energy_kpis_from_context(context, country_id: int = None):
    # -------------------------------------------------------------------------
    # Step 1: Lookups
    # -------------------------------------------------------------------------
    pef_lookup, emission_lookup, name_lookup = build_factor_lookups(context, country_pref=country_id)
    elec_id, gas_id = pick_carrier_ids(pef_lookup, emission_lookup, name_lookup)
    print(f"[Carrier IDs] elec={elec_id}, gas={gas_id}")

    # -------------------------------------------------------------------------
    # Step 2: fallback elec factors
    # -------------------------------------------------------------------------
    elec_fallback_pef = None
    elec_fallback_co2 = None
    if elec_id is None:
        elec_fallback_pef = 2.0
        elec_fallback_co2 = 0.20
        print(f"[Electricity factors fallback] PEF={elec_fallback_pef}, CO2={elec_fallback_co2}")

    # -------------------------------------------------------------------------
    # Step 3: timesteps
    # -------------------------------------------------------------------------
    n_ref = context.get("timestep_count")
    if not isinstance(n_ref, int):
        try:
            first_b = (context.get("building_asset_context") or [])[0]
            n_ref = _get_len_ts_from_building(first_b)
        except Exception:
            n_ref = 8760

    # -------------------------------------------------------------------------
    # Step 4: totals init
    # -------------------------------------------------------------------------
    totals = {
        "Primary_Energy_[kWh]": 0.0,
        "CO2_Emissions_[kg]": 0.0,

        "PV_Generation_[kWh]": 0.0,
        "STC_Generation_[kWh]": 0.0,
        "Wind_Generation_[kWh]": 0.0,
        "Renewable_Electricity_Generation_[kWh]": 0.0,

        "Electricity_Demand_[kWh]": 0.0,
        "Electricity_Load_for_SC_[kWh]": 0.0,
        "Electricity_Load_Pure_[kWh]": 0.0,

        "Grid_Import_[kWh]": 0.0,

        "Self_Consumption_[kWh]": 0.0,
        "Rate_Self_Consumption_[%]": 0.0,
        "Rate_Self_Sufficiency_[%]": 0.0,

        "Excess_Electricity_[kWh]": 0.0,
        "Excess_Heating_[kWh]": 0.0,
        "Excess_DHW_[kWh]": 0.0,
        "Excess_Total_[kWh]": 0.0,

        "Electricity_Exports_[kWh]": 0.0,
    }

    per_building = []

    # citizen factors (si luego los quieres usar en totals, ok)
    ctz_factors = None
    if hasattr(KM, "kpi_ctz_factors"):
        try:
            ctz_factors = KM.kpi_ctz_factors()
        except Exception:
            ctz_factors = None

    # -------------------------------------------------------------------------
    # Step 5: per building
    # -------------------------------------------------------------------------
    for i, b in enumerate(context.get("building_asset_context", []) or []):
        # base KPIs from module
        k = compute_all_kpis_for_building(
            b, pef_lookup, emission_lookup, country_id, i,
            n_ref=n_ref, elec_id=elec_id, gas_id=gas_id,
            elec_fallback_pef=elec_fallback_pef,
            elec_fallback_co2=elec_fallback_co2,
        )

        # optional peak KPIs
        peak_heat_fn = getattr(KM, "kpi_peak_heat_demand", None)
        peak_elec_fn = getattr(KM, "kpi_peak_electricity_demand", None)
        if callable(peak_heat_fn) or callable(peak_elec_fn):
            dp_payload = _make_demand_profile_from_ctx(b, n_ref=n_ref)
            if callable(peak_heat_fn):
                try:
                    k["KPI_peak_heat_demand_[kWh]"] = round(float(peak_heat_fn(dp_payload)), 2)
                except Exception:
                    print(f"[WARN] kpi_peak_heat_demand failed for building {k.get('Building_ID')}")
            if callable(peak_elec_fn):
                try:
                    k["KPI_peak_elec_demand_[kWh]"] = round(float(peak_elec_fn(dp_payload)), 2)
                except Exception:
                    print(f"[WARN] kpi_peak_electricity_demand failed for building {k.get('Building_ID')}")

        # overwrite grid import with actual series if available
        try:
            gi_series = ((b.get("grid_imports") or {}).get("grid_import_kwh")) or []
            if gi_series:
                k["Grid_Import_[kWh]"] = round(_sum_ts(gi_series), 2)
        except Exception:
            pass

        # pure load mirror
        k["Electricity_Load_Pure_[kWh]"] = float(k.get("Electricity_Demand_[kWh]", 0.0) or 0.0)

        # building excess (electric + thermal)
        ex_b = (b.get("excess") or {})
        k["Excess_Electricity_[kWh]"] = round(_sum_ts(ex_b.get("elec_excess_kwh")), 2)
        k["Excess_Heating_[kWh]"] = round(_sum_ts(ex_b.get("heating_excess_kwh")), 2)
        k["Excess_DHW_[kWh]"] = round(_sum_ts(ex_b.get("dhw_excess_kwh")), 2)
        k["Excess_Total_[kWh]"] = round(
            float(k["Excess_Electricity_[kWh]"]) +
            float(k["Excess_Heating_[kWh]"]) +
            float(k["Excess_DHW_[kWh]"]), 2
        )

        # Wind generation per building (from assets availability_ts.value_output1)
        wind_gen = _sum_wind_generation_from_building_assets(b)
        k["Wind_Generation_[kWh]"] = round(wind_gen, 2)

        # ---------------------------------------------------------------------
        # ✅ Self-consumption PER BUILDING (PV + Wind, consistent with “exports/excess”)
        # We assume building "Excess_Electricity_[kWh]" represents exported/spilled electricity.
        # ---------------------------------------------------------------------
        pv_b = float(k.get("PV_Generation_[kWh]", 0.0) or 0.0)
        wind_b = float(k.get("Wind_Generation_[kWh]", 0.0) or 0.0)
        ren_gen_b = max(0.0, pv_b + wind_b)

        exports_b = float(k.get("Excess_Electricity_[kWh]", 0.0) or 0.0)
        load_b = float(k.get("Electricity_Load_for_SC_[kWh]", 0.0) or k.get("Electricity_Demand_[kWh]", 0.0) or 0.0)

        # renewable used locally (cannot exceed load)
        sc_b_raw = max(0.0, ren_gen_b - exports_b)
        sc_b = min(sc_b_raw, load_b) if load_b > 0 else 0.0

        k["Self_Consumption_[kWh]"] = round(sc_b, 2)
        k["Rate_Self_Consumption_[%]"] = round(100.0 * sc_b / ren_gen_b, 2) if ren_gen_b > 0 else 0.0
        k["Rate_Self_Sufficiency_[%]"] = round(100.0 * sc_b / load_b, 2) if load_b > 0 else 0.0

        # hard cap ratios
        k["Rate_Self_Consumption_[%]"] = min(100.0, max(0.0, k["Rate_Self_Consumption_[%]"]))
        k["Rate_Self_Sufficiency_[%]"] = min(100.0, max(0.0, k["Rate_Self_Sufficiency_[%]"]))

        # legacy naming alignment (optional)
        k["Total_PV_[kWh]"] = k.get("PV_Generation_[kWh]", 0.0)
        k["Total_self_consumption"] = k.get("Self_Consumption_[kWh]", 0.0)
        k["Total_self_sufficiency_[%]"] = k.get("Rate_Self_Sufficiency_[%]", 0.0)
        k["rate_of_self_consumption_[%]"] = k.get("Rate_Self_Consumption_[%]", 0.0)

        # push + sum totals
        per_building.append(k)
        for key in totals.keys():
            # only sum numeric KPIs; ratios will be recomputed at community level below
            if key in ("Rate_Self_Consumption_[%]", "Rate_Self_Sufficiency_[%]"):
                continue
            totals[key] += float(k.get(key, 0.0) or 0.0)

    # -------------------------------------------------------------------------
    # Step 6: Community exports (robust)
    #   - prefer community_excess.elec_excess_kwh if exists
    #   - else sum building Exccess_Electricity
    # -------------------------------------------------------------------------
    exports_comm = 0.0

    comm_excess = context.get("community_excess") or {}
    elec_ex = comm_excess.get("elec_excess_kwh")
    if elec_ex is not None:
        exports_comm = _sum_ts(elec_ex)
    else:
        # fallback: sum per-building excess electricity
        exports_comm = sum(float(bk.get("Excess_Electricity_[kWh]", 0.0) or 0.0) for bk in per_building)

    totals["Electricity_Exports_[kWh]"] = round(float(exports_comm), 2)
    totals["Excess_Electricity_[kWh]"] = totals["Electricity_Exports_[kWh]"]

    # thermal community excess (fallback: sum buildings, since community_excess may not exist)
    if (context.get("community_excess") or {}).get("heating_excess_kwh") is not None:
        totals["Excess_Heating_[kWh]"] = round(_sum_ts((context.get("community_excess") or {}).get("heating_excess_kwh")), 2)
    else:
        totals["Excess_Heating_[kWh]"] = round(sum(float(bk.get("Excess_Heating_[kWh]", 0.0) or 0.0) for bk in per_building), 2)

    if (context.get("community_excess") or {}).get("dhw_excess_kwh") is not None:
        totals["Excess_DHW_[kWh]"] = round(_sum_ts((context.get("community_excess") or {}).get("dhw_excess_kwh")), 2)
    else:
        totals["Excess_DHW_[kWh]"] = round(sum(float(bk.get("Excess_DHW_[kWh]", 0.0) or 0.0) for bk in per_building), 2)

    totals["Excess_Total_[kWh]"] = round(
        float(totals.get("Electricity_Exports_[kWh]", 0.0) or 0.0) +
        float(totals.get("Excess_Heating_[kWh]", 0.0) or 0.0) +
        float(totals.get("Excess_DHW_[kWh]", 0.0) or 0.0),
        2
    )

    # -------------------------------------------------------------------------
    # Step 7: Community self-consumption PV+Wind (ONLY ONCE, here)
    # -------------------------------------------------------------------------
    pv = float(totals.get("PV_Generation_[kWh]", 0.0) or 0.0)
    wind = float(totals.get("Wind_Generation_[kWh]", 0.0) or 0.0)
    ren_elec = max(0.0, pv + wind)
    totals["Renewable_Electricity_Generation_[kWh]"] = round(ren_elec, 2)

    exp = float(totals.get("Electricity_Exports_[kWh]", 0.0) or 0.0)
    load_sc = float(totals.get("Electricity_Load_for_SC_[kWh]", 0.0) or totals.get("Electricity_Demand_[kWh]", 0.0) or 0.0)

    sc_comm_raw = max(0.0, ren_elec - exp)
    sc_comm = min(sc_comm_raw, load_sc) if load_sc > 0 else 0.0

    totals["Self_Consumption_[kWh]"] = round(sc_comm, 2)
    totals["Rate_Self_Consumption_[%]"] = round(100.0 * sc_comm / ren_elec, 2) if ren_elec > 0 else 0.0
    totals["Rate_Self_Sufficiency_[%]"] = round(100.0 * sc_comm / load_sc, 2) if load_sc > 0 else 0.0

    totals["Rate_Self_Consumption_[%]"] = min(100.0, max(0.0, totals["Rate_Self_Consumption_[%]"]))
    totals["Rate_Self_Sufficiency_[%]"] = min(100.0, max(0.0, totals["Rate_Self_Sufficiency_[%]"]))

    # (optional) for backwards compatibility
    if pv > 0:
        totals["Rate_Self_Consumption_from_Exports_[%]"] = round(100.0 * (1.0 - exp / pv), 2)
    else:
        totals["Rate_Self_Consumption_from_Exports_[%]"] = 0.0

    # thermal spill rate
    stc = float(totals.get("STC_Generation_[kWh]", 0.0) or 0.0)
    if stc > 0:
        totals["Thermal_Spill_Rate_[%]"] = round(100.0 * (totals["Excess_Heating_[kWh]"] + totals["Excess_DHW_[kWh]"]) / stc, 2)
        totals["Thermal_Spill_Rate_[%]"] = min(100.0, max(0.0, totals["Thermal_Spill_Rate_[%]"]))
    else:
        totals["Thermal_Spill_Rate_[%]"] = 0.0

    # -------------------------------------------------------------------------
    # Step X: Citizen KPIs (si los quieres en totals)
    # -------------------------------------------------------------------------
    if ctz_factors:
        ctz_map_energy = {
            "EquivalentTVHours_[h]": "tv_h",
            "EquivalentstreamingHours_[h]": "streaming_h",
            "PizzaConsumptionComparison_[pizza]": "pizza_h",
            "BatteryUsageEstimation_[charges]": "battery_charges",
            "ElectricCarChargingEstimation_[charges]": "el_car_charges",
            "WineBottlesProduction_[bottles]": "wine_bottles",
        }
        ctz_map_co2 = {
            "TreesRequiredForCarbonOffset_[trees]": "trees_number",
            "streamingEmissionsImpact_[hours]": "streaming_emission_hours",
            "CarbonEmissionsPerKilometer_[km]": "icv_km",
        }

        pe_comm = float(totals.get("Primary_Energy_[kWh]", 0.0) or 0.0)
        co2_comm = float(totals.get("CO2_Emissions_[kg]", 0.0) or 0.0)

        for out_key, fn_name in ctz_map_energy.items():
            fn = getattr(KM, fn_name, None)
            if callable(fn):
                try:
                    totals[out_key] = round(float(fn(ctz_factors, pe_comm)), 3)
                except Exception:
                    print(f"[WARN] totals citizen KPI failed: {fn_name}() -> {out_key}")

        for out_key, fn_name in ctz_map_co2.items():
            fn = getattr(KM, fn_name, None)
            if callable(fn):
                try:
                    totals[out_key] = round(float(fn(ctz_factors, co2_comm)), 3)
                except Exception:
                    print(f"[WARN] totals citizen KPI failed: {fn_name}() -> {out_key}")

    return {"totals": totals, "buildings": per_building}


# =============================================================================
# Optional: standalone execution for quick testing
# =============================================================================
if __name__ == "__main__":
    with open("data/final_context.json", "r", encoding="utf-8") as f:
        context = json.load(f)

    kpis = calculate_energy_kpis_from_context(context)
    print("\n--- Final KPIs ---")
    print(kpis["totals"])

    output_path = Path("data/final_kpis.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(kpis, f, ensure_ascii=False, indent=2)

    print(f"[INFO] KPIs exportados a {output_path.resolve()}")

# # =============================================================================
# # calculate_kpis_from_context.py
# # =============================================================================
# # Purpose
# # -------
# # This script reads the full energy simulation results (stored in a “context”)
# # and calculates all Key Performance Indicators (KPIs) for each building and
# # for the community as a whole.
# #
# # It connects the results from the OEMOF optimization with the KPI module,
# # applies emission and energy factors, and generates aggregated values such as:
# #   • total primary energy
# #   • CO2 emissions
# #   • PV and thermal generation
# #   • grid imports
# #   • self-consumption and self-sufficiency ratios
# #   • energy or CO2 intensities per m²
# #
# # Optional “citizen KPIs” are also computed (like equivalent TV hours or trees
# # needed to offset carbon), when available in the KPI module.
# # =============================================================================
# import json
# from pathlib import Path
# import numpy as np
# from api.services.scripts_enpower.kpi_module.KPI_module import (
#         build_factor_lookups,
#         compute_all_kpis_for_building,
#         pick_carrier_ids,
#     )
# from api.services.scripts_enpower.kpi_module import KPI_module as KM

# def calculate_energy_kpis_from_context(context, country_id: int = None):
#     """
#     Main function that calculates all energy KPIs from the simulation context.

#     What it does in simple terms:
#     -----------------------------
#     1. Reads emission and primary energy factors for the selected country.
#     2. Goes through every building in the context.
#     3. For each one, computes all KPIs (energy, CO2, PV, grid, etc.).
#     4. Calculates optional additional indicators (peaks, citizen KPIs, intensities).
#     5. Aggregates all buildings to form community-level totals.

#     Parameters
#     ----------
#     context : dict
#         The full simulation data (usually generated after OEMOF optimization).
#     country_id : int, optional
#         Country identifier used to select national emission and PEF factors.

#     Returns
#     -------
#     dict
#         Dictionary containing:
#         • "totals": overall community KPIs
#         • "buildings": list of per-building KPIs
#     """
#     # -------------------------------------------------------------------------
#     # Step 1: Build lookup tables for emission and primary energy factors.
#     # -------------------------------------------------------------------------
#     pef_lookup, emission_lookup, name_lookup = build_factor_lookups(context, country_pref=country_id)
#     elec_id, gas_id = pick_carrier_ids(pef_lookup, emission_lookup, name_lookup)
#     print(f"[Carrier IDs] elec={elec_id}, gas={gas_id}")

#     # Show a quick sample of the factors for verification
#     peek_pef = list(pef_lookup.items())[:3]
#     peek_co2 = list(emission_lookup.items())[:3]
#     print(f"[PEF sample] {peek_pef}")
#     print(f"[CO2 sample] {peek_co2}")

#     # -------------------------------------------------------------------------
#     # Step 2: Define fallback values in case electricity factors are missing.
#     # -------------------------------------------------------------------------
#     elec_fallback_pef = None
#     elec_fallback_co2 = None
#     if elec_id is None:
#         # Replace these with national reference values if available
#         elec_fallback_pef = 2.0      # Example: 2.0 kWh primary / kWh electricity
#         elec_fallback_co2 = 0.20     # Example: 0.2 kg CO2 per kWh electricity
#         print(f"[Electricity factors fallback] PEF={elec_fallback_pef}, CO2={elec_fallback_co2}")

#     # -------------------------------------------------------------------------
#     # Step 3: Check how many time steps are in the simulation.
#     # If not explicitly given, we infer it from one building’s grid import series.
#     # -------------------------------------------------------------------------
#     n_ref = context.get("timestep_count")
#     if not isinstance(n_ref, int):
#         # fallback: intenta derivarlo del primer building
#         try:
#             first_b = (context.get("building_asset_context") or [])[0]
#             e = (first_b.get("grid_imports") or {}).get("grid_import_kwh") or []
#             n_ref = len(e) if isinstance(e, list) else None
#         except Exception:
#             n_ref = None

#     # -------------------------------------------------------------------------
#     # Step 4: Initialize total KPIs (community-level sums).
#     # -------------------------------------------------------------------------
#     totals = {
#         "Primary_Energy_[kWh]": 0.0,
#         "CO2_Emissions_[kg]": 0.0,
#         "PV_Generation_[kWh]": 0.0,
#         "STC_Generation_[kWh]": 0.0,
#         "Electricity_Demand_[kWh]": 0.0,
#         "Grid_Import_[kWh]": 0.0,
#         "Self_Consumption_[kWh]": 0.0,
#         "Electricity_Load_for_SC_[kWh]": 0.0,
#         "Electricity_Load_Pure_[kWh]": 0.0,
#         "Excess_Electricity_[kWh]": 0.0,
#         "Excess_Heating_[kWh]": 0.0,
#         "Excess_DHW_[kWh]": 0.0,
#         "Excess_Total_[kWh]": 0.0,
#         "Wind_Generation_[kWh]": 0.0,
#         "Renewable_Electricity_Generation_[kWh]": 0.0,

#     }
#     per_building = [] # will store each building's KPI results

#     # -------------------------------------------------------------------------
#     # Helper: Create a small dictionary with demand profiles from the context
#     # This helps when computing “peak demand” KPIs.
#     # -------------------------------------------------------------------------
#     def make_demand_profile_from_ctx(building_ctx, n_ref=None):
#         bc = (building_ctx.get("building_consumption") or {})
#         def to_np(key):
#             arr = np.asarray(bc.get(key) or [], dtype=float)
#             if n_ref is not None and arr.size != n_ref:
#                 if arr.size > n_ref:
#                     arr = arr[:n_ref]
#                 else:
#                     arr = np.pad(arr, (0, n_ref - arr.size), mode="constant")
#             return arr
#         return {
#             "demand_profile": {
#                 "electricity_demand": to_np("elec_consumption"),
#                 "heating_demand":     to_np("heat_consumption"),
#                 "cooling_demand":     to_np("cool_consumption"),
#                 "dhw_demand":         to_np("dhw_consumption"),
#             }
#         }

#     # Load optional “citizen equivalence” factors if available in KPI module
#     ctz_factors = None
#     if hasattr(KM, "kpi_ctz_factors"):
#         try:
#             ctz_factors = KM.kpi_ctz_factors()
#         except Exception:
#             ctz_factors = None    

#     # -------------------------------------------------------------------------
#     # Step 5: Process each building in the context
#     # -------------------------------------------------------------------------
#     for i, b in enumerate(context.get("building_asset_context", []) or []):
#         k = compute_all_kpis_for_building(
#             b, pef_lookup, emission_lookup, country_id, i,
#             n_ref=n_ref, elec_id=elec_id, gas_id=gas_id,
#             elec_fallback_pef=elec_fallback_pef,
#             elec_fallback_co2=elec_fallback_co2,
#         )

#         # --- Wind generation per building ---
#         wind_gen = 0.0
#         try:
#             for a in (b.get("building_energy_asset") or []):
#                 if a.get("generation_system_id") == 132:
#                     ts = (a.get("availability_ts") or {}).get("value_output1") or []
#                     if ts:
#                         arr_w = np.asarray(ts, dtype=float)
#                         arr_w = np.nan_to_num(arr_w, nan=0.0, posinf=0.0, neginf=0.0)
#                         wind_gen += float(arr_w.sum())
#         except Exception:
#             wind_gen = 0.0
#         k["Wind_Generation_[kWh]"] = round(wind_gen, 2)

#         # --- Grid imports overwrite (as you had) ---
#         try:
#             gi_series = ((b.get("grid_imports") or {}).get("grid_import_kwh")) or []
#             if gi_series:
#                 arr_gi = np.asarray(gi_series, dtype=float)
#                 arr_gi = np.nan_to_num(arr_gi, nan=0.0, posinf=0.0, neginf=0.0)
#                 k["Grid_Import_[kWh]"] = round(float(arr_gi.sum()), 2)
#         except Exception:
#             pass

#         k["Electricity_Load_Pure_[kWh]"] = k.get("Electricity_Demand_[kWh]", 0.0)

#         # --- Excess per building (as you had) ---
#         ex_b = (b.get("excess") or {})
#         elec_ex_b = ex_b.get("elec_excess_kwh")
#         if elec_ex_b:
#             try:
#                 arr_b = np.asarray(elec_ex_b, dtype=float)
#                 arr_b = np.nan_to_num(arr_b, nan=0.0, posinf=0.0, neginf=0.0)
#                 k["Excess_Electricity_[kWh]"] = round(float(arr_b.sum()), 2)
#             except Exception:
#                 k["Excess_Electricity_[kWh]"] = 0.0
#         else:
#             k["Excess_Electricity_[kWh]"] = 0.0

#         h_series = ex_b.get("heating_excess_kwh") or []
#         try:
#             arr_h = np.asarray(h_series, dtype=float)
#             arr_h = np.nan_to_num(arr_h, nan=0.0, posinf=0.0, neginf=0.0)
#             k["Excess_Heating_[kWh]"] = round(float(arr_h.sum()), 2)
#         except Exception:
#             k["Excess_Heating_[kWh]"] = 0.0

#         d_series = ex_b.get("dhw_excess_kwh") or []
#         try:
#             arr_d = np.asarray(d_series, dtype=float)
#             arr_d = np.nan_to_num(arr_d, nan=0.0, posinf=0.0, neginf=0.0)
#             k["Excess_DHW_[kWh]"] = round(float(arr_d.sum()), 2)
#         except Exception:
#             k["Excess_DHW_[kWh]"] = 0.0

#         k["Excess_Total_[kWh]"] = round(
#             k.get("Excess_Electricity_[kWh]", 0.0) +
#             k.get("Excess_Heating_[kWh]", 0.0) +
#             k.get("Excess_DHW_[kWh]", 0.0), 2
#         )

#         # --- ✅ Self-consumption per building (PV + Wind) ---
#         pv_b = float(k.get("PV_Generation_[kWh]", 0.0) or 0.0)
#         wind_b = float(k.get("Wind_Generation_[kWh]", 0.0) or 0.0)
#         gen_b = max(0.0, pv_b + wind_b)

#         ex_elec_b = float(k.get("Excess_Electricity_[kWh]", 0.0) or 0.0)
#         sc_b = max(0.0, gen_b - ex_elec_b)

#         k["Self_Consumption_[kWh]"] = round(sc_b, 2)
#         k["Rate_Self_Consumption_[%]"] = round(100.0 * sc_b / gen_b, 2) if gen_b > 0 else 0.0

#         load_b = float(k.get("Electricity_Load_for_SC_[kWh]", 0.0) or k.get("Electricity_Demand_[kWh]", 0.0) or 0.0)
#         k["Rate_Self_Sufficiency_[%]"] = round(100.0 * sc_b / load_b, 2) if load_b > 0 else 0.0

#         # --- append + sum totals AFTER updating k ---
#         per_building.append(k)
#         for key in totals:
#             totals[key] += k.get(key, 0.0)

#     # -------------------------------------------------------------------------
#     # Step 6: Add community-level exports (same as you had)
#     # -------------------------------------------------------------------------
#     comm_excess = context.get("community_excess") or {}
#     elec_ex = comm_excess.get("elec_excess_kwh") or []
#     try:
#         arr = np.asarray(elec_ex, dtype=float)
#         arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
#         totals["Electricity_Exports_[kWh]"] = round(float(arr.sum()), 2)
#     except Exception:
#         totals["Electricity_Exports_[kWh]"] = 0.0

#     totals["Excess_Electricity_[kWh]"] = totals.get("Electricity_Exports_[kWh]", 0.0)

#     # -------------------------------------------------------------------------
#     # Step 7: Community self-consumption PV+Wind (ONLY ONCE, here)
#     # -------------------------------------------------------------------------
#     pv = float(totals.get("PV_Generation_[kWh]", 0.0) or 0.0)
#     wind = float(totals.get("Wind_Generation_[kWh]", 0.0) or 0.0)
#     exp = float(totals.get("Electricity_Exports_[kWh]", 0.0) or 0.0)

#     ren_elec = max(0.0, pv + wind)
#     totals["Renewable_Electricity_Generation_[kWh]"] = round(ren_elec, 2)

#     sc_comm = max(0.0, ren_elec - exp)
#     totals["Self_Consumption_[kWh]"] = round(sc_comm, 2)
#     totals["Rate_Self_Consumption_[%]"] = round(100.0 * sc_comm / ren_elec, 2) if ren_elec > 0 else 0.0

#     load_sc = float(totals.get("Electricity_Load_for_SC_[kWh]", 0.0) or 0.0)
#     totals["Rate_Self_Sufficiency_[%]"] = round(100.0 * sc_comm / load_sc, 2) if load_sc > 0 else 0.0
#     # -------------------------------------------------------------------------
#     # Step 6: Add community-level excess and rates
#     # -------------------------------------------------------------------------
#     comm_excess = context.get("community_excess") or {}
#     elec_ex = comm_excess.get("elec_excess_kwh") or []
#     # Community electricity exports
#     try:
#         arr = np.asarray(elec_ex, dtype=float)
#         arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)  # <- evita NaN
#         totals["Electricity_Exports_[kWh]"] = round(float(arr.sum()), 2)
#     except Exception:
#         totals["Electricity_Exports_[kWh]"] = 0.0

#     # Mirror the naming for compatibility
#     totals["Excess_Electricity_[kWh]"] = totals.get("Electricity_Exports_[kWh]", 0.0)

#     # Self-consumption ratio from exports
#     if totals["PV_Generation_[kWh]"]:
#         totals["Rate_Self_Consumption_from_Exports_[%]"] = round(
#             100.0 * (1.0 - totals["Electricity_Exports_[kWh]"] / totals["PV_Generation_[kWh]"]), 2
#         )
#     else:
#         totals["Rate_Self_Consumption_from_Exports_[%]"] = 0.0

#     # Community thermal excess (heating + DHW)
#     h_comm = (context.get("community_excess") or {}).get("heating_excess_kwh") or []
#     d_comm = (context.get("community_excess") or {}).get("dhw_excess_kwh") or []
#     try:
#         arr_hc = np.asarray(h_comm, dtype=float)
#         arr_hc = np.nan_to_num(arr_hc, nan=0.0, posinf=0.0, neginf=0.0)
#         totals["Excess_Heating_[kWh]"] += round(float(arr_hc.sum()), 2)
#     except Exception:
#         pass

#     try:
#         arr_dc = np.asarray(d_comm, dtype=float)
#         arr_dc = np.nan_to_num(arr_dc, nan=0.0, posinf=0.0, neginf=0.0)
#         totals["Excess_DHW_[kWh]"] += round(float(arr_dc.sum()), 2)
#     except Exception:
#         pass

#     # Final total excess (electric + thermal)
#     totals["Excess_Total_[kWh]"] = round(
#         totals.get("Electricity_Exports_[kWh]", 0.0) +
#         totals.get("Excess_Heating_[kWh]", 0.0) +
#         totals.get("Excess_DHW_[kWh]", 0.0), 2
#     )

#     # Thermal spill rate (share of unused solar thermal)
#     if totals["STC_Generation_[kWh]"]:
#         totals["Thermal_Spill_Rate_[%]"] = round(
#             100.0 * (totals["Excess_Heating_[kWh]"] + totals["Excess_DHW_[kWh]"]) /
#             totals["STC_Generation_[kWh]"], 2
#         )
#     else:
#         totals["Thermal_Spill_Rate_[%]"] = 0.0




#     # pv   = totals.get("PV_Generation_[kWh]", 0.0)
#     # exp  = totals.get("Electricity_Exports_[kWh]", 0.0)
#     # load = totals.get("Electricity_Load_Pure_[kWh]", 0.0)
#     # sc_pure = max(0.0, pv - exp)

#     # if load > 0:
#     #     totals["Rate_Self_Sufficiency_Pure_[%]"] = round(100.0 * min(1.0, sc_pure / load), 2)
#     # else:
#     #     totals["Rate_Self_Sufficiency_Pure_[%]"] = 0.0

#     # totals["Rate_Self_Consumption_[%]"] = round(
#     #     100.0 * totals["Self_Consumption_[kWh]"] / totals["PV_Generation_[kWh]"], 2
#     # ) if totals["PV_Generation_[kWh]"] else 0.0

#     # totals["Rate_Self_Sufficiency_[%]"] = round(
#     #     100.0 * totals["Self_Consumption_[kWh]"] / totals["Electricity_Load_for_SC_[kWh]"], 2
#     # ) if totals["Electricity_Load_for_SC_[kWh]"] else 0.0

#     # totals["Rate_Self_Consumption_Pure_[%]"] = round(
#     #     100.0 * min(1.0, sc_pure / pv), 2
#     # ) if pv > 0 else 0.0
#         # -------------------------------------------------------------------------
#     # Step X: Citizen KPIs ONLY at community level (totals)
#     # -------------------------------------------------------------------------
#     if ctz_factors:
#         # Mappings (same as before)
#         ctz_map_energy = {
#             "EquivalentTVHours_[h]":                  "tv_h",
#             "EquivalentstreamingHours_[h]":           "streaming_h",
#             "PizzaConsumptionComparison_[pizza]":     "pizza_h",
#             "BatteryUsageEstimation_[charges]":       "battery_charges",
#             "ElectricCarChargingEstimation_[charges]":"el_car_charges",
#             "WineBottlesProduction_[bottles]":        "wine_bottles",
#         }
#         ctz_map_co2 = {
#             "TreesRequiredForCarbonOffset_[trees]":   "trees_number",
#             "streamingEmissionsImpact_[hours]":       "streaming_emission_hours",
#             "CarbonEmissionsPerKilometer_[km]":       "icv_km",
#         }

#         pe_comm = float(totals.get("Primary_Energy_[kWh]", 0.0) or 0.0)
#         co2_comm = float(totals.get("CO2_Emissions_[kg]", 0.0) or 0.0)

#         # Energy-based citizen KPIs
#         for out_key, fn_name in ctz_map_energy.items():
#             fn = getattr(KM, fn_name, None)
#             if callable(fn):
#                 try:
#                     totals[out_key] = round(float(fn(ctz_factors, pe_comm)), 3)
#                 except Exception:
#                     print(f"[WARN] totals citizen KPI failed: {fn_name}() -> {out_key}")

#         # CO2-based citizen KPIs
#         for out_key, fn_name in ctz_map_co2.items():
#             fn = getattr(KM, fn_name, None)
#             if callable(fn):
#                 try:
#                     totals[out_key] = round(float(fn(ctz_factors, co2_comm)), 3)
#                 except Exception:
#                     print(f"[WARN] totals citizen KPI failed: {fn_name}() -> {out_key}")

#     kpis = {"totals": totals, "buildings": per_building}
#     # -------------------------------------------------------------------------
#     # Step 8: Return everything
#     # -------------------------------------------------------------------------
#     return kpis

# # =============================================================================
# # Optional: standalone execution for quick testing
# # =============================================================================
# if __name__ == "__main__":
#     with open("data/final_context.json", "r") as f:
#         context = json.load(f)

#     kpis = calculate_energy_kpis_from_context(context)
#     print("\n--- Final KPIs ---")
#     for k, v in kpis.items():
#         print(f"{k}: {v}")

#     # Export KPIs to JSON for inspection
#     output_path = Path("data/final_kpis.json")
#     output_path.parent.mkdir(parents=True, exist_ok=True)
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump(kpis, f, ensure_ascii=False, indent=2)
#     print(f"[INFO] KPIs exportados a {output_path.resolve()}")
