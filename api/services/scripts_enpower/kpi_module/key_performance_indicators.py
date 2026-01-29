# key_performance_indicators.py
import os
import json
from api.services.scripts_enpower.OEMOF_module.classes_database import FinalEnergy, BuildingKPIs, CommunityEnergyAsset
import pandas as pd
from api.services.scripts_enpower.kpi_module.KPI_module import (
    kpi_ctz_factors, tv_h, streaming_h, pizza_h, battery_charges, el_car_charges, trees_number,
    streaming_emission_hours, icv_km, wine_bottles
)
import geopandas as gpd
from shapely import wkt
from shapely.geometry import shape

# Constants for recurring string literals
AREA = "area_conditioned"
AVAILABILITY_TS = "availability_ts"
BUILDING = "building"
BUILDING_ASSET_CONTEXT = "building_asset_context"
BUILDING_CONSUMPTION = "building_consumption"
BUILDING_USE_ID = "building_use_id"
CONSTRUCTION_YEAR = "construction_year"
COOL_CONSUMPTION = "cool_consumption"
COOLING_DEMAND = "cooling_demand"
COOLING_SYSTEM = "cooling_system"
COOLING_SYSTEM_ID = "cooling_system_id"
COUNTRY_ID = "country_id"
DEMAND_PROFILE = "demand_profile"
DEMANDPROFILE = "demandprofile"
DHW_CONSUMPTION = "dhw_consumption"
DHW_DEMAND = "dhw_demand"
DHW_SYSTEM = "dhw_system"
DHW_SYSTEM_ID = "dhw_system_id"
ELECTRICITY_CONSUMPTION = "elec_consumption"
ELECTRICITY_DEMAND = "electricity_demand"
ELECTRICITY_SYSTEM_ID = "electricity_system_id"
ELECTRICITY_SYSTEM = "electricity_system"
ENERGY_CARRIER_INPUT1_ID = "energy_carrier_input_1_id"
ENERGY_CARRIER_INPUT1 = "energy_carrier_input_1"
FINAL_ENERGY_ELECTRICITY_GRID = "final_energy_electricity_grid"
FUEL_YIELD_1 = "fuel_yield1"
GENERATION_SYSTEM_ID = "generation_system_id"
GENERATION_SYSTEM_PROFILE_ID = "generation_system_profile_id"
GENERATION_SYSTEM_PROFILE = "generation_system_profile"
HEAT_CONSUMPTION = "heat_consumption"
HEATING_DEMAND = "heating_demand"
HEATING_SYSTEM = "heating_system"
HEATING_SYSTEM_ID = "heating_system_id"
ID = "id"
NATIONAL_ENERGY_CARRIER_DATA = "national_energy_carrier_production"
PMAX_SCALAR = "pmax_scalar"

# IMPORTANT: availability_ts keys
VALUE_INPUT1 = "value_input1"
VALUE_INPUT2 = "value_input2"
VALUE_OUTPUT1 = "value_output1"
VALUE_OUTPUT2 = "value_output2"

# units
KWH = "kWh"
HOURS = "h"
PIZZA = "pizza"
CHARGES = "charges"
BOTTLES = "bottles"
TREES = "trees"
KM = "km"
AU = "a.u."
EURO = "€"
GRAMS_CO2EQ = "g CO2eq"
KWH_PER_M2 = "kWh/m2"
GRAMS_PER_M2 = "g/m2"
EURO_PER_M2 = "€/m2"
PERCENT = "%"


def handle_demand_profile(building_asset_context, generation_system_profile, consumption_profile):
    consumption_profile_length = len(consumption_profile[ELECTRICITY_CONSUMPTION])
    building_id = building_asset_context.get(ID)
    demand_profile = building_asset_context.get(BUILDING, {}).get(DEMANDPROFILE)

    if demand_profile is None and generation_system_profile is not None:
        if generation_system_profile.get(HEATING_SYSTEM, {}) is not None:
            fuel_yield1_heating = generation_system_profile.get(HEATING_SYSTEM, {}).get(FUEL_YIELD_1, 1)
        else:
            fuel_yield1_heating = 0
            consumption_profile[HEAT_CONSUMPTION] = [0] * consumption_profile_length

        if generation_system_profile.get(COOLING_SYSTEM, {}) is not None:
            fuel_yield1_cooling = generation_system_profile.get(COOLING_SYSTEM, {}).get(FUEL_YIELD_1, 1)
        else:
            fuel_yield1_cooling = 0
            consumption_profile[COOL_CONSUMPTION] = [0] * consumption_profile_length

        if generation_system_profile.get(DHW_SYSTEM, {}) is not None:
            fuel_yield1_dhw = generation_system_profile.get(DHW_SYSTEM, {}).get(FUEL_YIELD_1, 1)
        else:
            fuel_yield1_dhw = 0
            consumption_profile[DHW_CONSUMPTION] = [0] * consumption_profile_length

        demand_profile = {
            ELECTRICITY_DEMAND: consumption_profile[ELECTRICITY_CONSUMPTION],
            HEATING_DEMAND: [x * fuel_yield1_heating for x in consumption_profile.get(HEAT_CONSUMPTION, [])],
            COOLING_DEMAND: [x * fuel_yield1_cooling for x in consumption_profile.get(COOL_CONSUMPTION, [])],
            DHW_DEMAND: [x * fuel_yield1_dhw for x in consumption_profile.get(DHW_CONSUMPTION, [])]
        }
        return demand_profile

    elif demand_profile is None:
        return ValueError(
            f"Demand profile could not be calculated because generation system profile is missing for building ID: {building_id}"
        )


def calculate_self_consumption(total_electricity_use, total_local_generation):
    return [min(total_electricity_use[i], total_local_generation[i]) for i in range(len(total_electricity_use))]


def calculate_rate_of_self_consumption(self_consumption, total_local_generation):
    return [(self_consumption[i] / total_local_generation[i]) * 100 if total_local_generation[i] > 0 else 0
            for i in range(len(self_consumption))]


def calculate_grid_consumption(total_electricity_use, self_consumption):
    return [total_electricity_use[i] - self_consumption[i] for i in range(len(total_electricity_use))]


def calculate_self_sufficiency(self_consumption, total_electricity_use):
    return [(self_consumption[i] / total_electricity_use[i]) * 100 if total_electricity_use[i] > 0 else 0
            for i in range(len(self_consumption))]


def add_electricity_consumption(total_electricity_use, consumption):
    for i in range(len(total_electricity_use)):
        if consumption[i] is None:
            consumption[i] = 0
        total_electricity_use[i] += consumption[i]
    return total_electricity_use


def check_system_type_to_get_consumption(system_name, consumption_profile):
    system_type = None
    if system_name == DHW_SYSTEM_ID:
        consumption = consumption_profile[DHW_CONSUMPTION].copy()
        system_type = DHW_SYSTEM
    elif system_name == HEATING_SYSTEM_ID:
        consumption = consumption_profile[HEAT_CONSUMPTION].copy()
        system_type = HEATING_SYSTEM
    elif system_name == COOLING_SYSTEM_ID:
        consumption = consumption_profile[COOL_CONSUMPTION].copy()
        system_type = COOLING_SYSTEM
    else:
        consumption = [0] * 8760
        system_type = ELECTRICITY_SYSTEM
    return consumption, system_type


def instantiate_final_energy_with_json():
    parent_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(parent_directory, "catalogues", "energy_carrier.json")
    with open(json_file_path, "r") as file:
        json_data = json.load(file)

    total_final_energy = {}
    for entry in json_data:
        if entry.get("final"):
            eid = entry[ID]
            total_final_energy[eid] = FinalEnergy(eid)
            total_final_energy[eid].name = entry["name"]
            total_final_energy[eid].final = entry["final"]

    return total_final_energy


def load_energy_system_catalogue():
    parent_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_files_path = os.path.join(parent_directory, "scenario_generator", "catalogues",
                                    "generation_systems_catalogue.json")
    with open(input_files_path, "r") as file:
        energy_systems_catalogue = json.load(file)
    return energy_systems_catalogue


def load_energy_carrier_catalogue():
    parent_directory = os.path.dirname(os.path.abspath(__file__))
    input_files_path = os.path.join(parent_directory, "catalogues", "energy_carrier.json")
    with open(input_files_path, "r") as f:
        energy_carrier_catalogue = json.load(f)
    return energy_carrier_catalogue


def filter_energy_systems_catalogue(energy_systems_catalogue, new_generation_system_id):
    for system in energy_systems_catalogue:
        if system[ID] == new_generation_system_id:
            return system
    return None


def get_national_energy_carrier_production(energy_carrier_catalogue, country_id, energy_carrier_id):
    fallback_data = None
    for carrier in energy_carrier_catalogue:
        if carrier["id"] == energy_carrier_id:
            for production in carrier.get("national_energy_carrier_production", []):
                if production["country_id"] == country_id:
                    return production
                elif production["country_id"] == 31:
                    fallback_data = production
    return fallback_data if fallback_data is not None else None


# -------------------------------------------------------------------------
# NEW HELPERS: safe series + scale only if it looks like a profile (0..1)
# -------------------------------------------------------------------------
def _safe_ts(values, timestep_count):
    """
    Make series exactly timestep_count length, pad with 0, coerce to float.
    """
    base = values or []
    out = list(base[:timestep_count])
    if len(out) < timestep_count:
        out.extend([0.0] * (timestep_count - len(out)))
    # convert None/NaN-ish to 0
    cleaned = []
    for x in out:
        try:
            cleaned.append(float(0.0 if x is None else x))
        except Exception:
            cleaned.append(0.0)
    return cleaned


def _scale_if_profile(values, scalar, timestep_count):
    """
    Scale values by scalar ONLY if values look like a normalized profile.
    If values already look like absolute kWh (max > ~1.5), return them as-is.

    This avoids double-scaling OEMOF time series that are already kWh.
    """
    ts = _safe_ts(values, timestep_count)
    try:
        s = float(scalar) if scalar is not None else None
    except Exception:
        s = None

    if not ts:
        return ts

    vmax = max(abs(v) for v in ts) if ts else 0.0

    # Heuristic: normalized profile typically within [0..1] (allow small margin)
    looks_like_profile = (vmax <= 1.5)

    if looks_like_profile and s is not None:
        return [v * s for v in ts]
    return ts


# Backward compatible alias (so you DON'T need to update all call sites)
def _scale_ts(values, scalar, timestep_count):
    return _scale_if_profile(values, scalar, timestep_count)

def calculate_building_indicators(
    consumption_profile,
    generation_system_profile,
    building_energy_asset,
    timestep_count,
    building_use_id
):
    """
    Definition
    ----------
    Computes building-level energy indicators for both baseline and OEMOF scenarios.

    Key rules
    ---------
    - Total electricity use = end-use electricity consumption + HP electricity consumption (if applicable).
    - Local electricity generation = sum of electric generation assets (PV + wind).
    - Self-consumption is computed using TOTAL local electricity generation (PV + wind).
    - Total_PV is kept as PV-only (legacy compatibility).

    Parameters
    ----------
    consumption_profile : dict
        Hourly consumption arrays. Expected keys include:
          - ELECTRICITY_CONSUMPTION
          - HEAT_CONSUMPTION
          - COOL_CONSUMPTION
          - DHW_CONSUMPTION
    generation_system_profile : dict | None
        Generation system profile for the building (baseline systems).
    building_energy_asset : list | None
        List of assets with availability_ts and pmax_scalar. In OEMOF scenarios, assets include
        HPs (electricity input) and generators (electricity output).
    timestep_count : int
        Number of timesteps (e.g., 8760).
    building_use_id : int | None
        Building use type identifier (used for cost logic).

    Returns
    -------
    tuple
        (
            total_PV,                 # list[float] PV-only generation (kWh)
            rate_of_self_consumption, # list[float] hourly %
            self_sufficiency,         # list[float] hourly %
            total_electricity_use,    # list[float] hourly electricity load (kWh)
            self_consumption,         # list[float] hourly kWh
            total_final_energy,       # dict[int, FinalEnergy]
            KPIs,                     # dict[int, BuildingKPIs]
            costs                     # dict | None
        )
    """

    # ------------------------------------------------------------
    # Static lists (catalog-dependent)
    # ------------------------------------------------------------
    list_of_hps = [1, 2, 3, 4, 5, 6, 7, 8, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 41,
                   61, 62, 63, 64, 65, 66, 67, 68, 73]
    cooling_hps_list = [1, 2, 3, 4, 5, 6, 7, 8]
    heating_hps_list = [61, 62, 63, 64, 65, 66, 67, 68, 73]
    dhw_hps_list = [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 41]

    pv_asset_ids = [80, 81, 82, 83, 84, 85, 86, 87]
    wind_asset_ids = [132, 134]
    electric_asset_list = pv_asset_ids + wind_asset_ids

    # ------------------------------------------------------------
    # Initialize outputs
    # ------------------------------------------------------------
    rate_of_self_consumption = []
    grid_consumption = []
    self_sufficiency = []
    self_consumption = []
    total_electricity_use = _safe_ts(consumption_profile.get(ELECTRICITY_CONSUMPTION, []), timestep_count)

    total_PV = [0.0] * timestep_count
    total_local_electric_generation = [0.0] * timestep_count
    electricity_asset = False

    cooling_asset = False
    heating_asset = False
    dhw_asset = False

    total_final_energy = instantiate_final_energy_with_json()
    energy_carrier_catalogue = load_energy_carrier_catalogue()
    costs = None

    # ------------------------------------------------------------
    # 1) If assets exist (OEMOF scenario or baseline with assets)
    # ------------------------------------------------------------
    if building_energy_asset is not None:
        # 1a) Add HP electricity consumption from assets (OEMOF)
        for asset in building_energy_asset:
            gs_id = asset.get(GENERATION_SYSTEM_ID)
            availability_ts = asset.get(AVAILABILITY_TS, {}) or {}

            if gs_id in list_of_hps:
                # OEMOF convention: HP electricity input is VALUE_INPUT2
                hp_elec = _safe_ts(availability_ts.get(VALUE_INPUT2, []), timestep_count)
                total_electricity_use = [
                    total_electricity_use[i] + hp_elec[i] for i in range(timestep_count)
                ]

                if gs_id in cooling_hps_list:
                    cooling_asset = True
                if gs_id in heating_hps_list:
                    heating_asset = True
                if gs_id in dhw_hps_list:
                    dhw_asset = True

            else:
                # Final fuels consumption for non-HP assets
                energy_carrier_1 = asset.get("generation_system", {}).get(ENERGY_CARRIER_INPUT1, {})
                if energy_carrier_1.get("final") is True:
                    fuels_id = energy_carrier_1.get(ID, 0)
                    if fuels_id in total_final_energy:
                        pmax = asset.get(PMAX_SCALAR, 0)
                        # keep legacy fuel input in VALUE_INPUT1
                        fuel_ts = asset.get(AVAILABILITY_TS, {}).get(VALUE_INPUT1, [])
                        fuel_ts_scaled = _scale_ts(fuel_ts, pmax, timestep_count)
                        total_final_energy[fuels_id].add_new_consumption(fuel_ts_scaled)

        # 1b) If baseline systems exist and HPs are not present as assets, add them
        for system_name, system_id in (generation_system_profile or {}).items():
            if not isinstance(system_id, int):
                continue

            consumption, system_type = check_system_type_to_get_consumption(system_name, consumption_profile)
            consumption = _safe_ts(consumption, timestep_count)

            if system_name == DHW_SYSTEM_ID and system_id in dhw_hps_list and not dhw_asset:
                total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
            elif system_name == HEATING_SYSTEM_ID and system_id in heating_hps_list and not heating_asset:
                total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
            elif system_name == COOLING_SYSTEM_ID and system_id in cooling_hps_list and not cooling_asset:
                total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
            elif system_name == ELECTRICITY_SYSTEM_ID and system_id == 79:
                # grid handled after self-consumption calculation
                pass
            else:
                if generation_system_profile.get(system_type) is not None:
                    fuels_id = generation_system_profile[system_type][ENERGY_CARRIER_INPUT1_ID]
                    if fuels_id in total_final_energy:
                        total_final_energy[fuels_id].add_new_consumption(consumption)

        # 1c) Local electricity generation from assets (PV + wind)
        for asset in building_energy_asset:
            gs_id = asset.get(GENERATION_SYSTEM_ID)
            if gs_id in electric_asset_list:
                availability_ts = asset.get(AVAILABILITY_TS, {}) or {}

                # OEMOF convention: generation output is VALUE_OUTPUT1
                gen_profile = availability_ts.get(VALUE_OUTPUT1, [])
                pmax = asset.get(PMAX_SCALAR, 0.0)

                gen_ts = _scale_ts(gen_profile, pmax, timestep_count)

                total_local_electric_generation = [
                    total_local_electric_generation[i] + gen_ts[i] for i in range(timestep_count)
                ]

                # PV-only accumulation for legacy KPI Total_PV
                if gs_id in pv_asset_ids:
                    total_PV = [total_PV[i] + gen_ts[i] for i in range(timestep_count)]

                electricity_asset = True

    # ------------------------------------------------------------
    # 2) Self-consumption KPIs (always computed consistently)
    # ------------------------------------------------------------
    if electricity_asset:
        self_consumption = calculate_self_consumption(total_electricity_use, total_local_electric_generation)
        rate_of_self_consumption = calculate_rate_of_self_consumption(self_consumption, total_local_electric_generation)
        grid_consumption = calculate_grid_consumption(total_electricity_use, self_consumption)
        self_sufficiency = calculate_self_sufficiency(self_consumption, total_electricity_use)
    else:
        grid_consumption = total_electricity_use
        self_consumption = [0.0] * timestep_count
        rate_of_self_consumption = [0.0] * timestep_count
        self_sufficiency = [0.0] * timestep_count
        total_PV = [0.0] * timestep_count

    # ------------------------------------------------------------
    # 3) Add grid electricity as final energy (carrier id 12)
    # ------------------------------------------------------------
    if 12 in total_final_energy:
        total_final_energy[12].add_new_consumption(_safe_ts(grid_consumption, timestep_count))

    # ------------------------------------------------------------
    # 4) Build KPIs from final energy
    # ------------------------------------------------------------
    KPIs = {}
    for energy_carrier_id, final_energy_obj in total_final_energy.items():
        if final_energy_obj.final:
            kpi_data = get_national_energy_carrier_production(
                energy_carrier_catalogue=energy_carrier_catalogue,
                country_id=27,
                energy_carrier_id=energy_carrier_id
            )

            if kpi_data is None:
                kpi_data = {
                    "final": True,
                    "energy_carrier_id": energy_carrier_id,
                    "pef_tot": 0,
                    "pef_nren": 0,
                    "pef_ren": 0,
                    "f_co2_eq_g_kwh": 0,
                    "house_costs_eur_kwh": 0,
                    "non_h_costs_eur_kwh": 0,
                    "country_id": 27,
                    "id": energy_carrier_id,
                    "reference": "0",
                }

            KPIs[energy_carrier_id] = BuildingKPIs(final_energy_obj, kpi_data)

    return (
        total_PV,
        rate_of_self_consumption,
        self_sufficiency,
        total_electricity_use,
        self_consumption,
        total_final_energy,
        KPIs,
        costs
    )

# def calculate_building_indicators(consumption_profile,
#                                   generation_system_profile,
#                                   building_energy_asset,
#                                   timestep_count,
#                                   building_use_id):
#     """
#     Computes building-level indicators (self-consumption, grid, final energy, etc.)
#     Works for both baseline and OEMOF scenarios.

#     Key updates:
#     - HP electricity consumption comes from availability_ts.value_input2
#     - PV/electric generation comes from availability_ts.value_output1
#     - Scaling uses _scale_if_profile to avoid double scaling kWh series
#     """

#     rate_of_self_consumption = []
#     grid_consumption = []
#     self_sufficiency = []
#     total_electricity_use = []

#     # NOTE: generation_system_id lists from legacy code (catalog-dependent)
#     list_of_hps = [1, 2, 3, 4, 5, 6, 7, 8, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 41, 61, 62, 63, 64, 65, 66,
#                    67, 68, 73]
#     cooling_hps_list = [1, 2, 3, 4, 5, 6, 7, 8]
#     heating_hps_list = [61, 62, 63, 64, 65, 66, 67, 68, 73]
#     dhw_hps_list = [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 41]

#     # Electric generators list (PV/wind/etc in legacy catalogue)
#     electric_asset_list = [80, 81, 82, 83, 84, 85, 86, 87]
#     # solar_thermal = [37, 38, 39, 40, 69, 70, 71, 72]  # not used here for self-consumption

#     total_fuels_use = {}
#     cooling_asset = False
#     heating_asset = False
#     dhw_asset = False
#     electricity_asset = False

#     total_final_energy = instantiate_final_energy_with_json()
#     energy_systems_catalogue = load_energy_system_catalogue()

#     costs = {}

#     total_PV = [0.0] * timestep_count
#     total_local_electric_generation = [0.0] * timestep_count

#     if building_energy_asset is not None:
#         # base electricity consumption profile (end-use electricity)
#         total_electricity_use = _safe_ts(consumption_profile.get(ELECTRICITY_CONSUMPTION, []), timestep_count)

#         # ------------------------------------------------------------
#         # Add extra electricity consumption from HP assets (OEMOF case)
#         # ------------------------------------------------------------
#         for asset in building_energy_asset:
#             if asset.get(GENERATION_SYSTEM_ID) in list_of_hps:
#                 availability_ts = asset.get(AVAILABILITY_TS, {}) or {}

#                 # UPDATED: HP electricity input stored in value_input2
#                 hp_elec = _safe_ts(availability_ts.get(VALUE_INPUT2, []), timestep_count)

#                 total_electricity_use = [
#                     total_electricity_use[i] + hp_elec[i]
#                     for i in range(timestep_count)
#                 ]

#                 if asset.get(GENERATION_SYSTEM_ID) in cooling_hps_list:
#                     cooling_asset = True
#                 if asset.get(GENERATION_SYSTEM_ID) in dhw_hps_list:
#                     dhw_asset = True
#                 if asset.get(GENERATION_SYSTEM_ID) in heating_hps_list:
#                     heating_asset = True

#             else:
#                 # fuels for non-HP assets: use energy_carrier_input_1.final
#                 if asset:
#                     energy_carrier_1 = asset.get("generation_system", {}).get(ENERGY_CARRIER_INPUT1, {})
#                     if energy_carrier_1.get("final") is True:
#                         fuels_id = energy_carrier_1.get(ID, 0)
#                         if fuels_id and fuels_id in total_final_energy:
#                             pmax = asset.get(PMAX_SCALAR, 0)
#                             # For fuel consumption time series we keep VALUE_INPUT1 (legacy)
#                             consumption = asset.get(AVAILABILITY_TS, {}).get(VALUE_INPUT1, [])
#                             consumption_for_the_asset = _scale_if_profile(consumption, pmax, timestep_count)
#                             total_final_energy[fuels_id].add_new_consumption(consumption_for_the_asset)

#         # ------------------------------------------------------------
#         # If there are baseline systems without explicit assets, add their consumption
#         # ------------------------------------------------------------
#         for system_name, system_id in (generation_system_profile or {}).items():
#             if not isinstance(system_id, int):
#                 continue

#             consumption, system_type = check_system_type_to_get_consumption(system_name, consumption_profile)

#             if system_name == DHW_SYSTEM_ID and system_id in dhw_hps_list and dhw_asset is False:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, _safe_ts(consumption, timestep_count))
#             elif system_name == HEATING_SYSTEM_ID and system_id in heating_hps_list and heating_asset is False:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, _safe_ts(consumption, timestep_count))
#             elif system_name == COOLING_SYSTEM_ID and system_id in cooling_hps_list and cooling_asset is False:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, _safe_ts(consumption, timestep_count))
#             elif system_name in (DHW_SYSTEM_ID, HEATING_SYSTEM_ID, COOLING_SYSTEM_ID) and generation_system_profile.get(system_type) is not None:
#                 fuels_id = generation_system_profile[system_type][ENERGY_CARRIER_INPUT1_ID]
#                 total_final_energy[fuels_id].add_new_consumption(_safe_ts(consumption, timestep_count))

#         # ------------------------------------------------------------
#         # Local electricity generation (PV + wind + other electric assets)
#         # OEMOF stores generation in availability_ts.value_output1
#         # ------------------------------------------------------------
#         for asset in building_energy_asset:
#             if asset.get(GENERATION_SYSTEM_ID) in electric_asset_list:
#                 availability_ts = asset.get(AVAILABILITY_TS, {}) or {}

#                 # UPDATED: use value_output1 for generation
#                 profile_gen = availability_ts.get(VALUE_OUTPUT1, [])
#                 pmax_scalar = asset.get(PMAX_SCALAR, 0.0)

#                 gen_ts = _scale_if_profile(profile_gen, pmax_scalar, timestep_count)

#                 total_local_electric_generation = [
#                     total_local_electric_generation[i] + gen_ts[i]
#                     for i in range(timestep_count)
#                 ]

#                 # PV separate (legacy: PV id==83)
#                 if asset.get(GENERATION_SYSTEM_ID) == 83:
#                     total_PV = [
#                         total_PV[i] + gen_ts[i]
#                         for i in range(timestep_count)
#                     ]

#                 electricity_asset = True

#         # ------------------------------------------------------------
#         # Self-consumption KPIs (building level)
#         # ------------------------------------------------------------
#         if electricity_asset:
#             self_consumption = calculate_self_consumption(total_electricity_use, total_local_electric_generation)
#             rate_of_self_consumption = calculate_rate_of_self_consumption(self_consumption, total_local_electric_generation)
#             grid_consumption = calculate_grid_consumption(total_electricity_use, self_consumption)
#             self_sufficiency = calculate_self_sufficiency(self_consumption, total_electricity_use)
#         else:
#             grid_consumption = total_electricity_use
#             self_consumption = [0.0] * timestep_count
#             rate_of_self_consumption = [0.0] * timestep_count
#             self_sufficiency = [0.0] * timestep_count
#             total_PV = [0.0] * timestep_count

#     else:
#         # no assets: pure baseline
#         total_electricity_use = _safe_ts(consumption_profile.get(ELECTRICITY_CONSUMPTION, []), timestep_count)

#         for system_name, system_id in (generation_system_profile or {}).items():
#             if not isinstance(system_id, int):
#                 continue

#             consumption, system_type = check_system_type_to_get_consumption(system_name, consumption_profile)

#             if system_name == DHW_SYSTEM_ID and system_id in dhw_hps_list:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, _safe_ts(consumption, timestep_count))
#             elif system_name == HEATING_SYSTEM_ID and system_id in heating_hps_list:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, _safe_ts(consumption, timestep_count))
#             elif system_name == COOLING_SYSTEM_ID and system_id in cooling_hps_list:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, _safe_ts(consumption, timestep_count))
#             elif system_name == ELECTRICITY_SYSTEM_ID and system_id == 79:
#                 grid_consumption = total_electricity_use
#                 self_consumption = [0.0] * timestep_count
#                 rate_of_self_consumption = [0.0] * timestep_count
#                 self_sufficiency = [0.0] * timestep_count
#                 total_PV = [0.0] * timestep_count
#             else:
#                 if generation_system_profile.get(system_type) is not None:
#                     fuels_id = generation_system_profile[system_type][ENERGY_CARRIER_INPUT1_ID]
#                     total_final_energy[fuels_id].add_new_consumption(_safe_ts(consumption, timestep_count))

#         # if no electricity asset, grid is all
#         if "grid_consumption" not in locals():
#             grid_consumption = total_electricity_use
#             self_consumption = [0.0] * timestep_count
#             rate_of_self_consumption = [0.0] * timestep_count
#             self_sufficiency = [0.0] * timestep_count
#             total_PV = [0.0] * timestep_count

#     # Add grid electricity final energy (id=12 in many catalogues)
#     if 12 in total_final_energy:
#         total_final_energy[12].add_new_consumption(_safe_ts(grid_consumption, timestep_count))

#     KPIs = {}
#     energy_carrier_catalogue = load_energy_carrier_catalogue()

#     for energy_carrier_id, final_energy_obj in total_final_energy.items():
#         if final_energy_obj.final:
#             kpi_data = get_national_energy_carrier_production(
#                 energy_carrier_catalogue=energy_carrier_catalogue,
#                 country_id=27,
#                 energy_carrier_id=energy_carrier_id
#             )

#             if kpi_data is None:
#                 print(f"THERE IS AN ERROR: No matching/fallback found for country_id=27/31 "
#                       f"for energy_carrier_id={energy_carrier_id}. Assigning 0s.")
#                 kpi_data = {
#                     "final": True,
#                     "energy_carrier_id": energy_carrier_id,
#                     "pef_tot": 0,
#                     "pef_nren": 0,
#                     "f_co2_eq_g_kwh": 0,
#                     "non_h_costs_eur_kwh": 0,
#                     "country_id": 27,
#                     "id": energy_carrier_id,
#                     "pef_ren": 0,
#                     "house_costs_eur_kwh": 0,
#                     "reference": "0"
#                 }

#             KPIs[energy_carrier_id] = BuildingKPIs(final_energy_obj, kpi_data)

#             if energy_carrier_id == 12:
#                 cost_of_electricity_household = kpi_data.get("house_costs_eur_kwh", 0) or 0
#                 cost_of_electricity_non_household = kpi_data.get("non_h_costs_eur_kwh", 0) or 0

#     # Costs calculation (legacy: only PV 83)
#     if building_energy_asset:
#         for asset in building_energy_asset:
#             if asset.get(GENERATION_SYSTEM_ID, 0) == 83:
#                 if building_use_id in [1, 2, 3]:
#                     total_energy_costs_now = KPIs[12].household_costs_yearly
#                     total_energy_costs_baseline = (sum(self_consumption) + sum(grid_consumption)) * cost_of_electricity_household
#                     costs = calculate_costs(
#                         capacity=asset.get(PMAX_SCALAR),
#                         generation_system_id=83,
#                         generation_time_series=total_PV,
#                         total_energy_costs_now=total_energy_costs_now,
#                         total_energy_costs_baseline=total_energy_costs_baseline
#                     )
#                 else:
#                     total_energy_costs_now = KPIs[12].non_h_costs_yearly
#                     total_energy_costs_baseline = (sum(self_consumption) + sum(grid_consumption)) * cost_of_electricity_non_household
#                     costs = calculate_costs(
#                         capacity=asset.get(PMAX_SCALAR),
#                         generation_system_id=83,
#                         generation_time_series=total_PV,
#                         total_energy_costs_now=total_energy_costs_now,
#                         total_energy_costs_baseline=total_energy_costs_baseline
#                     )
#                 break

#     return (
#         total_PV,
#         rate_of_self_consumption,
#         self_sufficiency,
#         total_electricity_use,
#         self_consumption,
#         total_final_energy,
#         KPIs,
#         costs
#     )


def aggregate_demand_profiles(demand_profile):
    total_demand = {}

    if isinstance(demand_profile, list):
        for building in demand_profile:
            profile = building.get(DEMAND_PROFILE, {})
            for demand_type, demand_values in profile.items():
                if isinstance(demand_values, (int, float)):
                    demand_values = [float(demand_values)]
                elif not isinstance(demand_values, list):
                    continue
                demand_values = [0.0 if v is None else float(v) for v in demand_values]

                if demand_type in total_demand:
                    min_len = min(len(total_demand[demand_type]), len(demand_values))
                    total_demand[demand_type] = [
                        total_demand[demand_type][i] + demand_values[i]
                        for i in range(min_len)
                    ]
                else:
                    total_demand[demand_type] = demand_values

    elif isinstance(demand_profile, dict):
        for demand_type, demand_values in demand_profile.get(DEMAND_PROFILE, {}).items():
            if isinstance(demand_values, (int, float)):
                demand_values = [float(demand_values)]
            elif not isinstance(demand_values, list):
                continue
            demand_values = [0.0 if v is None else float(v) for v in demand_values]

            if demand_type in total_demand:
                min_len = min(len(total_demand[demand_type]), len(demand_values))
                total_demand[demand_type] = [
                    total_demand[demand_type][i] + demand_values[i]
                    for i in range(min_len)
                ]
            else:
                total_demand[demand_type] = demand_values

    else:
        raise TypeError("demand_profile must be either a list or a dictionary.")

    return total_demand


# -------------------------------------------------------------------------
# Below here you can keep your original code unchanged.
# (I’m leaving it as-is in your project; only calculate_building_indicators + scaling helpers needed updates.)
# -------------------------------------------------------------------------

# Function to calculate Net Present Value (NPV) of cash flows
def calculate_npv(cash_flows, discount_rate):
    return sum(cf / ((1 + discount_rate) ** year) for year, cf in enumerate(cash_flows, start=1))


def calculate_total_capex(capacity, capex_per_kw):
    return capacity * capex_per_kw


def calculate_annual_opex(annual_generation, opex_per_kwh):
    return annual_generation * opex_per_kwh


def calculate_total_lifetime_costs(capex, npv_opex):
    return capex + npv_opex


def calculate_lcoe(total_lifetime_costs, npv_generation):
    if npv_generation == 0:
        raise ValueError("NPV of generation cannot be zero.")
    return total_lifetime_costs / npv_generation


def calculate_payback_period(total_capex, annual_savings, lifetime):
    if annual_savings <= 0:
        return None
    years = total_capex / annual_savings
    return years if years <= lifetime else None


def calculate_costs(capacity, generation_system_id, generation_time_series,
                    total_energy_costs_baseline=None, total_energy_costs_now=None):
    if generation_time_series is None:
        generation_time_series = [0] * 8760
    if total_energy_costs_baseline is None:
        total_energy_costs_baseline = [0] * len(generation_time_series)
    if total_energy_costs_now is None:
        total_energy_costs_now = [0] * len(generation_time_series)

    energy_systems_catalogue = load_energy_system_catalogue()
    system_profile = filter_energy_systems_catalogue(
        energy_systems_catalogue=energy_systems_catalogue,
        new_generation_system_id=generation_system_id
    )

    if system_profile is None:
        CAPEX = 1000
        OPEX = 25
        lifetime = 20
    else:
        CAPEX = system_profile.get("capex_eur_kw", 1000)
        OPEX = system_profile.get("opex_eur_kwh_year", 25)
        lifetime = system_profile.get("lifetime_years", 20)

    if capacity is None:
        capacity = 0

    discount_rate = 0.05
    total_capex = calculate_total_capex(capacity, CAPEX)
    annual_generation = sum(generation_time_series)
    annual_maintenance_cost = calculate_annual_opex(annual_generation=annual_generation, opex_per_kwh=OPEX)

    annual_baseline_cost = sum(total_energy_costs_baseline) if isinstance(total_energy_costs_baseline, list) else total_energy_costs_baseline
    annual_current_cost = sum(total_energy_costs_now) if isinstance(total_energy_costs_now, list) else total_energy_costs_now

    if lifetime is None or lifetime < 0:
        raise ValueError("Lifetime must be a positive integer.")
    lifetime = int(lifetime)

    baseline_cash_flows = [annual_baseline_cost] * lifetime
    current_cash_flows = [annual_current_cost + annual_maintenance_cost] * lifetime

    npv_opex_before = calculate_npv(baseline_cash_flows, discount_rate)
    npv_opex_after = calculate_npv(current_cash_flows, discount_rate)

    total_lifetime_costs = total_capex + npv_opex_after
    total_savings = npv_opex_before - npv_opex_after

    npv_generation = calculate_npv([annual_generation] * lifetime, discount_rate)
    lcoe = None if npv_generation == 0 else calculate_lcoe(total_lifetime_costs, npv_generation)

    annual_savings = total_savings / lifetime
    payback_period = None if annual_savings <= 0 else calculate_payback_period(total_capex, annual_savings, lifetime)

    return {
        "total_capex": total_capex,
        "npv_opex_before": npv_opex_before,
        "npv_opex_after": npv_opex_after,
        "total_lifetime_costs": total_lifetime_costs,
        "lcoe": lcoe,
        "total_savings": total_savings,
        "payback_period_years": payback_period
    }


# import os
# import json
# from api.services.scripts_enpower.OEMOF_module.classes_database import FinalEnergy, BuildingKPIs, CommunityEnergyAsset
# import pandas as pd
# from api.services.scripts_enpower.kpi_module.KPI_module import (kpi_ctz_factors,tv_h, streaming_h, pizza_h, battery_charges, el_car_charges,trees_number,
#                         streaming_emission_hours,icv_km,wine_bottles)
# import geopandas as gpd
# from shapely import wkt
# from shapely.geometry import shape

# # Constants for recurring string literals
# AREA="area_conditioned"
# AVAILABILITY_TS = "availability_ts"
# BUILDING = "building"
# BUILDING_ASSET_CONTEXT="building_asset_context"
# BUILDING_CONSUMPTION="building_consumption"
# BUILDING_USE_ID="building_use_id"
# CONSTRUCTION_YEAR="construction_year"
# COOL_CONSUMPTION = "cool_consumption"
# COOLING_DEMAND = "cooling_demand"
# COOLING_SYSTEM = "cooling_system"
# COOLING_SYSTEM_ID="cooling_system_id"
# COUNTRY_ID="country_id"
# DEMAND_PROFILE="demand_profile"
# DEMANDPROFILE = "demandprofile"
# DHW_CONSUMPTION = "dhw_consumption"
# DHW_DEMAND = "dhw_demand"
# DHW_SYSTEM = "dhw_system"
# DHW_SYSTEM_ID="dhw_system_id"
# ELECTRICITY_CONSUMPTION = "elec_consumption"
# ELECTRICITY_DEMAND = "electricity_demand"
# ELECTRICITY_SYSTEM_ID="electricity_system_id"
# ELECTRICITY_SYSTEM="electricity_system"
# ENERGY_CARRIER_INPUT1_ID = "energy_carrier_input_1_id"
# ENERGY_CARRIER_INPUT1="energy_carrier_input_1"
# FINAL_ENERGY_ELECTRICITY_GRID = "final_energy_electricity_grid"
# FUEL_YIELD_1="fuel_yield1"
# GENERATION_SYSTEM_ID="generation_system_id"
# GENERATION_SYSTEM_PROFILE_ID="generation_system_profile_id"
# GENERATION_SYSTEM_PROFILE="generation_system_profile"
# HEAT_CONSUMPTION = "heat_consumption"
# HEATING_DEMAND = "heating_demand"
# HEATING_SYSTEM = "heating_system"
# HEATING_SYSTEM_ID="heating_system_id"
# ID = "id"
# NATIONAL_ENERGY_CARRIER_DATA="national_energy_carrier_production"
# PMAX_SCALAR = "pmax_scalar"
# VALUE_INPUT1 = "value_input1"
# # String Literals for KPIs
# KPI_PEAK_HEAT_DEMAND_NAME = "KPI_peak_heat_demand_[kWh]"
# KPI_PEAK_HEAT_DEMAND_VALUE = "KPI_peak_heat_demand"

# KPI_PEAK_ELEC_DEMAND_NAME = "KPI_peak_elec_demand_[kWh]"
# KPI_PEAK_ELEC_DEMAND_VALUE = "KPI_peak_elec_demand"

# TOTAL_PRIMARY_ENERGY_NAME = "total_primary_energy_[kWh]"
# TOTAL_PRIMARY_ENERGY_VALUE = "total_primary_energy_kWh"

# NUM_MEMBERS_NAME = "num_members"
# NUM_MEMBERS_VALUE = 1 # one building one member

# EQUIVALENT_TV_HOURS_NAME = "EquivalentTVHours_[h]"
# EQUIVALENT_TV_HOURS_VALUE = "TV_h"

# EQUIVALENT_STREAMING_HOURS_NAME = "EquivalentstreamingHours_[h]"
# EQUIVALENT_STREAMING_HOURS_VALUE = "streaming_hours"

# PIZZA_CONSUMPTION_COMPARISON_NAME = "PizzaConsumptionComparison_[pizza]"
# PIZZA_CONSUMPTION_COMPARISON_VALUE = "Pizza_h"

# BATTERY_USAGE_ESTIMATION_NAME = "BatteryUsageEstimation_[charges]"
# BATTERY_USAGE_ESTIMATION_VALUE = "Battery_charges"

# ELECTRIC_CAR_CHARGING_ESTIMATION_NAME = "ElectricCarChargingEstimation_[charges]"
# ELECTRIC_CAR_CHARGING_ESTIMATION_VALUE = "ElCar_charges"

# WINE_BOTTLES_PRODUCTION_NAME = "WineBottlesProduction_[bottles]"
# WINE_BOTTLES_PRODUCTION_VALUE = "Wine_bottles"

# TREES_REQUIRED_FOR_CARBON_OFFSET_NAME = "TreesRequiredForCarbonOffset_[trees]"
# TREES_REQUIRED_FOR_CARBON_OFFSET_VALUE = "Trees_number"

# STREAMING_EMISSIONS_IMPACT_NAME = "streamingEmissionsImpact_[hours]"
# STREAMING_EMISSIONS_IMPACT_VALUE = "streaming_emissionhours"

# CARBON_EMISSIONS_PER_KILOMETER_NAME = "CarbonEmissionsPerKilometer_[km]"
# CARBON_EMISSIONS_PER_KILOMETER_VALUE = "ICV_km"

# TOTAL_PV_NAME = "Total_PV_[kWh]"
# TOTAL_PV_VALUE = "total_PV"

# TOTAL_SELF_CONSUMPTION_NAME = "Total_self_consumption"
# TOTAL_SELF_CONSUMPTION_VALUE = "self_consumption"

# TOTAL_SELF_SUFFICIENCY_NAME = "Total_self_sufficiency"
# TOTAL_SELF_SUFFICIENCY_VALUE = "self_sufficiency"

# RATE_OF_SELF_CONSUMPTION_NAME = "rate_of_self_consumption"
# RATE_OF_SELF_CONSUMPTION_VALUE = "rate_of_self_consumption"

# RENEWABLE_PRIMARY_ENERGY_NAME = "renewable_primary_energy_[kWh]"
# RENEWABLE_PRIMARY_ENERGY_VALUE = "total_primary_energy_renewable"

# NON_RENEWABLE_PRIMARY_ENERGY_NAME = "non_renewable_primary_energy_[kWh]"
# NON_RENEWABLE_PRIMARY_ENERGY_VALUE = "total_primary_energy_non_renewable"

# NON_HOUSEHOLDS_COSTS_NAME = "non_households_costs_[€]"
# NON_HOUSEHOLDS_COSTS_VALUE = "total_non_h_costs"

# HOUSEHOLDS_COSTS_NAME = "households_costs_[€]"
# HOUSEHOLDS_COSTS_VALUE = "total_h_costs"

# TOTAL_CO2_NAME = "Total_co2"
# TOTAL_CO2_VALUE = "total_co2"

# TOTAL_PRIMARY_ENERGY_INTENSITY_NAME = "total_primary_energy_intensity"
# TOTAL_PRIMARY_ENERGY_INTENSITY_VALUE = "total_primary_energy_intensity_kWh"

# NATIONAL_AVERAGE_TOTAL_PRIMARY_ENERGY_INTENSITY_NAME = "national_average_total_primary_energy_intensity"
# NATIONAL_AVERAGE_TOTAL_PRIMARY_ENERGY_INTENSITY_VALUE = "national_average_total_primary_energy_intensity"

# TOTAL_CO2_INTENSITY_NAME = "total_CO2_intensity"
# TOTAL_CO2_INTENSITY_VALUE = "total_co2_intensity"

# NATIONAL_AVERAGE_TOTAL_CO2_INTENSITY_NAME = "national_average_total_CO2_intensity"
# NATIONAL_AVERAGE_TOTAL_CO2_INTENSITY_VALUE = "national_average_total_CO2"

# TOTAL_ENERGY_COST_INTENSITY_NAME = "total_energy_cost_intensity"
# TOTAL_ENERGY_COST_INTENSITY_VALUE = "total_energy_cost_intensity"

# NATIONAL_AVERAGE_TOTAL_ENERGY_COST_INTENSITY_NAME = "national_average_total_energy_cost_intensity"
# NATIONAL_AVERAGE_TOTAL_ENERGY_COST_INTENSITY_VALUE = "national_average_total_energy_cost"

# #units
# KWH = "kWh"
# HOURS = "h"
# PIZZA = "pizza"
# CHARGES = "charges"
# BOTTLES = "bottles"
# TREES = "trees"
# KM = "km"
# AU = "a.u."
# EURO = "€"
# GRAMS_CO2EQ = "g CO2eq"
# KWH_PER_M2 = "kWh/m2"
# GRAMS_PER_M2 = "g/m2"
# EURO_PER_M2 = "€/m2"
# PERCENT = "%"


# def handle_demand_profile(building_asset_context,generation_system_profile,consumption_profile):
#     consumption_profile_length=len(consumption_profile[ELECTRICITY_CONSUMPTION])
#     # Handle demand_profile: If it doesn"t exist, calculate using generation system profiles
#     building_id=building_asset_context.get(ID)
#     demand_profile = building_asset_context.get(BUILDING, {}).get(DEMANDPROFILE)
#     if demand_profile is None and generation_system_profile is not None:
#         # Retrieve fuel yield values from the generation system profiles
#         if generation_system_profile.get(HEATING_SYSTEM, {}) is not None:
#             fuel_yield1_heating = generation_system_profile.get(HEATING_SYSTEM, {}).get(FUEL_YIELD_1, 1)
#         else:
#             fuel_yield1_heating = 0
#             consumption_profile[HEAT_CONSUMPTION]=[0]*consumption_profile_length
#         if generation_system_profile.get(COOLING_SYSTEM, {}) is not None:
#             fuel_yield1_cooling = generation_system_profile.get(COOLING_SYSTEM, {}).get(FUEL_YIELD_1, 1)
#         else:
#             fuel_yield1_cooling = 0
#             consumption_profile[COOL_CONSUMPTION]=[0]*consumption_profile_length
#         if generation_system_profile.get(DHW_SYSTEM, {}) is not None:
#             fuel_yield1_dhw = generation_system_profile.get(DHW_SYSTEM, {}).get(FUEL_YIELD_1, 1)
#         else:
#             fuel_yield1_dhw = 0
#             consumption_profile[DHW_CONSUMPTION]=[0]*consumption_profile_length

#         # Calculate demand profile using the consumption profile and fuel yields
#         demand_profile = {
#             ELECTRICITY_DEMAND: consumption_profile[ELECTRICITY_CONSUMPTION],
#             HEATING_DEMAND: [x * fuel_yield1_heating for x in
#                                consumption_profile.get(HEAT_CONSUMPTION, [])],
#             COOLING_DEMAND: [x * fuel_yield1_cooling for x in
#                                consumption_profile.get(COOL_CONSUMPTION, [])],
#             DHW_DEMAND: [x * fuel_yield1_dhw for x in consumption_profile.get(DHW_CONSUMPTION, [])]
#         }
#         return demand_profile

#     elif demand_profile is None:
#         return ValueError(
#             f"Demand profile could not be calculated because generation system profile is missing for building ID: {building_id}")

# def calculate_self_consumption(total_electricity_use, total_PV):
#     return [
#         min(total_electricity_use[i], total_PV[i])
#         for i in range(len(total_electricity_use))
#     ]

# def calculate_rate_of_self_consumption(self_consumption, total_PV):
#     return [
#         (self_consumption[i] / total_PV[i]) * 100 if total_PV[i] > 0 else 0
#         for i in range(len(self_consumption))
#     ]

# def calculate_grid_consumption(total_electricity_use, self_consumption):
#     return [
#         total_electricity_use[i] - self_consumption[i]
#         for i in range(len(total_electricity_use))
#     ]

# def calculate_self_sufficiency(self_consumption, total_electricity_use):
#     return [
#         (self_consumption[i] / total_electricity_use[i]) * 100 if total_electricity_use[i] > 0 else 0
#         for i in range(len(self_consumption))
#     ]

# def add_electricity_consumption(total_electricity_use, consumption):
#     for i in range(len(total_electricity_use)):
#         if consumption[i] is None:
#             consumption[i] = 0  # Handle None values in consumption
#         total_electricity_use[i] += consumption[i]
#     return total_electricity_use

# def check_system_type_to_get_consumption(system_name,consumption_profile):
#     # print(type(consumption_profile))
#     # print(consumption_profile.keys())
#     system_type=None
#     if system_name == DHW_SYSTEM_ID:
#         consumption = consumption_profile[DHW_CONSUMPTION].copy()
#         system_type=DHW_SYSTEM
#     elif system_name == HEATING_SYSTEM_ID:
#         consumption = consumption_profile[HEAT_CONSUMPTION].copy()
#         system_type=HEATING_SYSTEM
#     elif system_name == COOLING_SYSTEM_ID:
#         consumption = consumption_profile[COOL_CONSUMPTION].copy()
#         system_type=COOLING_SYSTEM
#     else:
#         consumption=[0]*8760
#         system_type=ELECTRICITY_SYSTEM
#     return consumption, system_type

# def instantiate_final_energy_with_json():
#     parent_directory = os.path.dirname(os.path.abspath(__file__))
#     json_file_path = os.path.join(parent_directory,
#                                   "catalogues", "energy_carrier.json")
#     with open(json_file_path, "r") as file:
#         json_data = json.load(file)

#     total_final_energy = {} #diccionario de instancias de la clase Final Energy para cada energy carrier
#     for entry in json_data:
#         if entry.get("final"):
#             id = entry[ID]
#             total_final_energy[id] = FinalEnergy(id)
#             total_final_energy[id].name = entry["name"]
#             total_final_energy[id].final = entry["final"]

#     return total_final_energy

# def load_energy_system_catalogue():
#     parent_directory =  os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     input_files_path = os.path.join(parent_directory,"scenario_generator","catalogues",
#                                     "generation_systems_catalogue.json")
#     with open(input_files_path, "r") as file:
#         energy_systems_catalogue = json.load(file)
#     return energy_systems_catalogue

# def load_energy_carrier_catalogue():
#     """
#     Loads the energy_carrier.json catalogue from the specified file path.

#     Args:
#         file_path (str): Path to the energy_carrier.json file.

#     Returns:
#         list: List of energy carriers from the JSON file.
#     """
#     parent_directory = os.path.dirname(os.path.abspath(__file__))
#     input_files_path = os.path.join(parent_directory,"catalogues",
#                                     "energy_carrier.json")
#     with open(input_files_path, "r") as f:
#         energy_carrier_catalogue = json.load(f)
#     return energy_carrier_catalogue

# def filter_energy_systems_catalogue(energy_systems_catalogue, new_generation_system_id):
#     # Loop through each system in the "systems" list
#     for system in energy_systems_catalogue:
#         # Check if the ID in the system matches the new_generation_system_id
#         if system[ID] == new_generation_system_id:
#             return system  # Return the matching system dictionary

#     return None  # Return None if no matching system is found
# def get_national_energy_carrier_production(energy_carrier_catalogue, country_id, energy_carrier_id):
#     """
#     Retrieves the national_energy_carrier_production for a given country_id and energy_carrier_id.

#     Args:
#         energy_carrier_catalogue (list): List of energy carriers from energy_carrier.json.
#         country_id (int): The country ID to search for.
#         energy_carrier_id (int): The energy carrier ID to search for.

#     Returns:
#         dict: The matching national_energy_carrier_production entry, or None if not found.
#     """
#     fallback_data=None
#     for carrier in energy_carrier_catalogue:
#         if carrier["id"] == energy_carrier_id:
#             for production in carrier.get("national_energy_carrier_production", []):
#                 if production["country_id"] == country_id:
#                     return production
#                 elif production["country_id"] == 31:
#                     fallback_data = production  # Store fallback match

#     return fallback_data  if fallback_data is not None else None # Return fallback match if no exact match is found
# def _safe_ts(values, timestep_count):
#     """
#     Definition
#     ----------
#     Normalizes a time series to a fixed length (timestep_count), padding with zeros or truncating.

#     Parameters
#     ----------
#     values : list | None
#         Input time series.
#     timestep_count : int
#         Desired length.

#     Returns
#     -------
#     list[float]
#         Time series with length = timestep_count.
#     """
#     base = values or []
#     out = list(base[:timestep_count])
#     if len(out) < timestep_count:
#         out.extend([0.0] * (timestep_count - len(out)))
#     return [float(x or 0.0) for x in out]


# def _scale_ts(values, scalar, timestep_count):
#     """
#     Definition
#     ----------
#     Scales a time series by a scalar and returns a safe-length series.

#     Parameters
#     ----------
#     values : list
#         Input time series.
#     scalar : float
#         Scaling factor.
#     timestep_count : int
#         Desired length.

#     Returns
#     -------
#     list
#         Scaled time series with length = timestep_count.
#     """
#     ts = _safe_ts(values, timestep_count)
#     try:
#         s = float(scalar or 0.0)
#     except Exception:
#         s = 0.0
#     return [x * s for x in ts]

# def calculate_building_indicators(consumption_profile,
#                                   generation_system_profile,
#                                   building_energy_asset,
#                                   timestep_count,
#                                   building_use_id):
#     """

#     Parameters
#     ----------
#     consumption_profile is the dictionary of consumption, typically:
#         BUILDING_CONSUMPTION:{
#             ID: int,
#             HEAT_CONSUMPTION:[],
#             DHW_CONSUMPTION:[],
#             ELECTRICITY_CONSUMPTION:[],
#             COOL_CONSUMPTION:[]
#             }
#     generation_system_profile is the dictionary of the energy systems
#     building_energy_asset is a list of several assets

#     Returns
#     -------

#     """
#     #initilize:
#     rate_of_self_consumption = []
#     grid_consumption = []
#     self_sufficiency = []
#     total_electricity_use = []
#     list_of_hps = [1, 2, 3, 4, 5, 6, 7, 8, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 41, 61, 62, 63, 64, 65, 66,
#                    67, 68, 73]
#     #dhn 145, 147, 153, 155 is out of the list as el. is consumed somewhere else
#     cooling_hps_list = [1, 2, 3, 4, 5, 6, 7, 8]
#     heating_hps_list = [61, 62, 63, 64, 65, 66, 67, 68, 73]
#     dhw_hps_list = [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 41]
#     chp_list = [88, 89, 90, 91]
#     electric_asset_list = [80, 81, 82, 83, 84, 85, 86, 87]
#     solar_thermal = [37, 38, 39, 40, 69, 70, 71, 72]
#     #any other id is a boiler?????
#     total_fuels_use={}
#     cooling_asset = False
#     heating_asset = False
#     dhw_asset = False
#     electricity_asset = False
#     total_final_energy=instantiate_final_energy_with_json()
#     energy_systems_catalogue=load_energy_system_catalogue()
#     consumption=[]
#     costs={}
#     total_PV = [0.0] * timestep_count
#     total_local_electric_generation = [0.0] * timestep_count
#     if building_energy_asset is not None:
#         # Initialize total_electricity_use with the base consumption profile
#         total_electricity_use = consumption_profile.get(ELECTRICITY_CONSUMPTION, [])
#         for asset in building_energy_asset:
#             if asset[GENERATION_SYSTEM_ID] in list_of_hps:
#                 # Perform element-wise summation for time_series_input1
#                 availability_ts = asset.get(AVAILABILITY_TS, {})
#                 time_series_input1_values =availability_ts.get(VALUE_INPUT1, [0] * timestep_count)
#                 total_electricity_use = [
#                             total_electricity_use[i] + time_series_input1_values[i]
#                             for i in range(len(total_electricity_use))
#                         ]
#                 if asset[GENERATION_SYSTEM_ID] in cooling_hps_list:
#                     cooling_asset = True
#                 if asset[GENERATION_SYSTEM_ID] in dhw_hps_list:
#                     dhw_asset = True
#                 if asset[GENERATION_SYSTEM_ID] in heating_hps_list:
#                     heating_asset = True
#             else:
#                 if asset:
#                      energy_carrier_1= asset.get("generation_system",{}).get(ENERGY_CARRIER_INPUT1,{})
#                      if energy_carrier_1.get("final") is True:
#                          fuels_id = energy_carrier_1.get(ID, 0)
#                          if fuels_id and fuels_id in total_final_energy:
#                              # Use time_series_input1 or any other relevant consumption data
#                              pmax=asset.get(PMAX_SCALAR,0)
#                              consumption = asset.get(AVAILABILITY_TS, {}).get(VALUE_INPUT1, [])
#                              if consumption is not None and pmax is not None:
#                                 consumption_for_the_asset=[x * pmax for x in consumption]
#                              else:
#                                 consumption_for_the_asset = [0] *8760
#                              total_final_energy[fuels_id].add_new_consumption(consumption_for_the_asset)
#         for system_name, system_id in generation_system_profile.items():
#             # Check if the value is an integer (system ID)
#             if not isinstance(system_id, int):
#                 continue  # Skip if the value is not an integer
#             #System_id is an integer, you can safely check it
#             #Get consumption
#             consumption, system_type=check_system_type_to_get_consumption(system_name, consumption_profile)
#             if system_name == DHW_SYSTEM_ID and system_id in dhw_hps_list and dhw_asset == False:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
#             elif system_name ==HEATING_SYSTEM_ID and system_id in heating_hps_list and heating_asset == False:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
#             elif system_name ==COOLING_SYSTEM_ID and system_id in cooling_hps_list and cooling_asset == False:
#                 #If cooling_system_id is in list_of_new_hps and is not already found in asset["generation_system_id],
#                 # the program will proceed to sum the corresponding cool_consumption values with total_electricity_use for each hour.
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
#             elif system_name == DHW_SYSTEM_ID and dhw_asset == False and generation_system_profile[system_type] is not None:
#                 fuels_id=generation_system_profile[system_type][ENERGY_CARRIER_INPUT1_ID ]
#                 total_final_energy[fuels_id].add_new_consumption(consumption)
#             elif system_name == HEATING_SYSTEM_ID and heating_asset == False and generation_system_profile[system_type] is not None:
#                 fuels_id=generation_system_profile[system_type][ENERGY_CARRIER_INPUT1_ID ]
#                 total_final_energy[fuels_id].add_new_consumption(consumption)
#             elif system_name == COOLING_SYSTEM_ID and cooling_asset == False and generation_system_profile[system_type] is not None:
#                 fuels_id=generation_system_profile[system_type][ENERGY_CARRIER_INPUT1_ID ]
#                 total_final_energy[fuels_id].add_new_consumption(consumption)

#         # ------------------------------------------------------------
#         # Local electricity generation (PV + wind + other electric assets)
#         # ------------------------------------------------------------
#         for asset in building_energy_asset:
#             if asset.get(GENERATION_SYSTEM_ID) in electric_asset_list:
#                 availability_ts = asset.get(AVAILABILITY_TS, {}) or {}
#                 profile = availability_ts.get(VALUE_INPUT1, [])
#                 pmax_scalar = asset.get(PMAX_SCALAR, 0.0)  # can be None
#                 gen_ts = _scale_ts(profile, pmax_scalar, timestep_count)

#                 # Sum ALL local electricity generation (PV + wind + etc.)
#                 total_local_electric_generation = [
#                     total_local_electric_generation[i] + gen_ts[i]
#                     for i in range(timestep_count)
#                 ]

#                 # Keep PV series separately for legacy outputs / costs
#                 # NOTE: in your code, PV seems to be generation_system_id == 83
#                 if asset.get(GENERATION_SYSTEM_ID) == 83:
#                     total_PV = [
#                         total_PV[i] + gen_ts[i]
#                         for i in range(timestep_count)
#                     ]

#                 electricity_asset = True

#         # ------------------------------------------------------------
#         # Compute self-consumption and related KPIs ONCE (not per asset)
#         # Using total local electricity generation (not only PV)
#         # ------------------------------------------------------------
#         if electricity_asset:
#             # Self-consumption: min(load, local_generation)
#             self_consumption = calculate_self_consumption(total_electricity_use, total_local_electric_generation)

#             # Rate of self-consumption: self_consumption / local_generation
#             rate_of_self_consumption = calculate_rate_of_self_consumption(self_consumption, total_local_electric_generation)

#             # Grid consumption: load - self_consumption
#             grid_consumption = calculate_grid_consumption(total_electricity_use, self_consumption)

#             # Self-sufficiency: self_consumption / load
#             self_sufficiency = calculate_self_sufficiency(self_consumption, total_electricity_use)
#         else:
#             grid_consumption = total_electricity_use
#             self_consumption = [0.0] * timestep_count
#             rate_of_self_consumption = [0.0] * timestep_count
#             self_sufficiency = [0.0] * timestep_count
#             total_PV = [0.0] * timestep_count        # ------------------------------------------------------------
#         # Local electricity generation (PV + wind + other electric assets)
#         # ------------------------------------------------------------
#         for asset in building_energy_asset:
#             if asset.get(GENERATION_SYSTEM_ID) in electric_asset_list:
#                 availability_ts = asset.get(AVAILABILITY_TS, {}) or {}
#                 profile = availability_ts.get(VALUE_INPUT1, [])
#                 pmax_scalar = asset.get(PMAX_SCALAR, 0.0)  # can be None
#                 gen_ts = _scale_ts(profile, pmax_scalar, timestep_count)

#                 # Sum ALL local electricity generation (PV + wind + etc.)
#                 total_local_electric_generation = [
#                     total_local_electric_generation[i] + gen_ts[i]
#                     for i in range(timestep_count)
#                 ]

#                 # Keep PV series separately for legacy outputs / costs
#                 # NOTE: in your code, PV seems to be generation_system_id == 83
#                 if asset.get(GENERATION_SYSTEM_ID) == 83:
#                     total_PV = [
#                         total_PV[i] + gen_ts[i]
#                         for i in range(timestep_count)
#                     ]

#                 electricity_asset = True

#         # ------------------------------------------------------------
#         # Compute self-consumption and related KPIs ONCE (not per asset)
#         # Using total local electricity generation (not only PV)
#         # ------------------------------------------------------------
#         if electricity_asset:
#             # Self-consumption: min(load, local_generation)
#             self_consumption = calculate_self_consumption(total_electricity_use, total_local_electric_generation)

#             # Rate of self-consumption: self_consumption / local_generation
#             rate_of_self_consumption = calculate_rate_of_self_consumption(self_consumption, total_local_electric_generation)

#             # Grid consumption: load - self_consumption
#             grid_consumption = calculate_grid_consumption(total_electricity_use, self_consumption)

#             # Self-sufficiency: self_consumption / load
#             self_sufficiency = calculate_self_sufficiency(self_consumption, total_electricity_use)
#         else:
#             grid_consumption = total_electricity_use
#             self_consumption = [0.0] * timestep_count
#             rate_of_self_consumption = [0.0] * timestep_count
#             self_sufficiency = [0.0] * timestep_count
#             total_PV = [0.0] * timestep_count        # ------------------------------------------------------------
#         # Local electricity generation (PV + wind + other electric assets)
#         # ------------------------------------------------------------
#         for asset in building_energy_asset:
#             if asset.get(GENERATION_SYSTEM_ID) in electric_asset_list:
#                 availability_ts = asset.get(AVAILABILITY_TS, {}) or {}
#                 profile = availability_ts.get(VALUE_INPUT1, [])
#                 pmax_scalar = asset.get(PMAX_SCALAR, 0.0)  # can be None
#                 gen_ts = _scale_ts(profile, pmax_scalar, timestep_count)

#                 # Sum ALL local electricity generation (PV + wind + etc.)
#                 total_local_electric_generation = [
#                     total_local_electric_generation[i] + gen_ts[i]
#                     for i in range(timestep_count)
#                 ]

#                 # Keep PV series separately for legacy outputs / costs
#                 # NOTE: in your code, PV seems to be generation_system_id == 83
#                 if asset.get(GENERATION_SYSTEM_ID) == 83:
#                     total_PV = [
#                         total_PV[i] + gen_ts[i]
#                         for i in range(timestep_count)
#                     ]

#                 electricity_asset = True

#         # ------------------------------------------------------------
#         # Compute self-consumption and related KPIs ONCE (not per asset)
#         # Using total local electricity generation (not only PV)
#         # ------------------------------------------------------------
#         if electricity_asset:
#             # Self-consumption: min(load, local_generation)
#             self_consumption = calculate_self_consumption(total_electricity_use, total_local_electric_generation)

#             # Rate of self-consumption: self_consumption / local_generation
#             rate_of_self_consumption = calculate_rate_of_self_consumption(self_consumption, total_local_electric_generation)

#             # Grid consumption: load - self_consumption
#             grid_consumption = calculate_grid_consumption(total_electricity_use, self_consumption)

#             # Self-sufficiency: self_consumption / load
#             self_sufficiency = calculate_self_sufficiency(self_consumption, total_electricity_use)
#         else:
#             grid_consumption = total_electricity_use
#             self_consumption = [0.0] * timestep_count
#             rate_of_self_consumption = [0.0] * timestep_count
#             self_sufficiency = [0.0] * timestep_count
#             total_PV = [0.0] * timestep_count        # ------------------------------------------------------------
#         # Local electricity generation (PV + wind + other electric assets)
#         # ------------------------------------------------------------
#         for asset in building_energy_asset:
#             if asset.get(GENERATION_SYSTEM_ID) in electric_asset_list:
#                 availability_ts = asset.get(AVAILABILITY_TS, {}) or {}
#                 profile = availability_ts.get(VALUE_INPUT1, [])
#                 pmax_scalar = asset.get(PMAX_SCALAR, 0.0)  # can be None
#                 gen_ts = _scale_ts(profile, pmax_scalar, timestep_count)

#                 # Sum ALL local electricity generation (PV + wind + etc.)
#                 total_local_electric_generation = [
#                     total_local_electric_generation[i] + gen_ts[i]
#                     for i in range(timestep_count)
#                 ]

#                 # Keep PV series separately for legacy outputs / costs
#                 # NOTE: in your code, PV seems to be generation_system_id == 83
#                 if asset.get(GENERATION_SYSTEM_ID) == 83:
#                     total_PV = [
#                         total_PV[i] + gen_ts[i]
#                         for i in range(timestep_count)
#                     ]

#                 electricity_asset = True

#         # ------------------------------------------------------------
#         # Compute self-consumption and related KPIs ONCE (not per asset)
#         # Using total local electricity generation (not only PV)
#         # ------------------------------------------------------------
#         if electricity_asset:
#             # Self-consumption: min(load, local_generation)
#             self_consumption = calculate_self_consumption(total_electricity_use, total_local_electric_generation)

#             # Rate of self-consumption: self_consumption / local_generation
#             rate_of_self_consumption = calculate_rate_of_self_consumption(self_consumption, total_local_electric_generation)

#             # Grid consumption: load - self_consumption
#             grid_consumption = calculate_grid_consumption(total_electricity_use, self_consumption)

#             # Self-sufficiency: self_consumption / load
#             self_sufficiency = calculate_self_sufficiency(self_consumption, total_electricity_use)
#         else:
#             grid_consumption = total_electricity_use
#             self_consumption = [0.0] * timestep_count
#             rate_of_self_consumption = [0.0] * timestep_count
#             self_sufficiency = [0.0] * timestep_count
#             total_PV = [0.0] * timestep_count
#     else:
#         #there is no asset in this building
#         # Initialize total_electricity_use with the base consumption profile
#         total_electricity_use = consumption_profile[ELECTRICITY_CONSUMPTION].copy()
#         for system_name, system_id in generation_system_profile.items():
#             # Check if the value is an integer (system ID)
#             if not isinstance(system_id, int):
#                 continue  # Skip if the value is not an integer
#             # Get consumption
#             consumption, system_type = check_system_type_to_get_consumption(system_name, consumption_profile)
#                 # Now, system_id is an integer, and you can safely check it
#             if system_name == DHW_SYSTEM_ID and system_id in dhw_hps_list:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
#             elif system_name == HEATING_SYSTEM_ID and system_id in heating_hps_list:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
#             elif system_name == COOLING_SYSTEM_ID and system_id in cooling_hps_list:
#                 total_electricity_use = add_electricity_consumption(total_electricity_use, consumption)
#             elif system_name == ELECTRICITY_SYSTEM_ID and system_id == 79:
#                 # This is the grid
#                 # grid_consumption equal to total_electricity_use
#                 grid_consumption = total_electricity_use
#                 # Set rate_of_self_consumption and self_sufficiency to lists of 8760 zeros
#                 self_consumption = [0] * timestep_count
#                 rate_of_self_consumption = [0] * timestep_count
#                 self_sufficiency = [0] * timestep_count
#                 total_PV =[0] * timestep_count
#             #consumption_profile
#             else:
#                 #this means is not a heat pump nor electricity grid but other type of system, therefore:
#                 if generation_system_profile[system_type] is not None:
#                     fuels_id=generation_system_profile[system_type][ENERGY_CARRIER_INPUT1_ID ]
#                     total_final_energy[fuels_id].add_new_consumption(consumption)

#     total_final_energy[12].add_new_consumption(grid_consumption)
#     KPIs = {}  # Dictionary to store the BuildingKPIs objects

#     # Iterate through total_final_energy items
#     energy_carrier_catalogue=load_energy_carrier_catalogue()
#     for energy_carrier_id, final_energy_obj in total_final_energy.items():
#         if final_energy_obj.final:  # Check if the energy is final
#             # Retrieve kpi_data using the previously defined function
#             kpi_data = get_national_energy_carrier_production(energy_carrier_catalogue=energy_carrier_catalogue, country_id=27,
#                                                               energy_carrier_id=energy_carrier_id)

#             # Check if `kpi_data` is None
#             if kpi_data is None:
#                 print(f"THERE IS AN ERROR:No matching or fallback country_id=27 or country_id=31 found for energy_carrier_id={energy_carrier_id}. 0 values are assigned")
#                 kpi_data={
#                   "final": True,
#                   "energy_carrier_id": energy_carrier_id,
#                   "pef_tot": 0,
#                   "pef_nren": 0,
#                   "f_co2_eq_g_kwh": 0,
#                   "non_h_costs_eur_kwh": 0,
#                   "country_id": 27,
#                   "id": energy_carrier_id,
#                   "pef_ren": 0,
#                   "house_costs_eur_kwh": 0,
#                   "reference": "0"
#                 }
#             if kpi_data is not None:
#                 # Calculate and store KPIs
#                 KPIs[energy_carrier_id] = BuildingKPIs(final_energy_obj, kpi_data)

#                 # Handle specific case for electricity cost (energy_carrier_id = 12)
#                 if energy_carrier_id == 12:
#                     cost_of_electricity_household = kpi_data.get("house_costs_eur_kwh", 0) if kpi_data.get(
#                             "house_costs_eur_kwh") is not None else 0
#                     cost_of_electricity_non_household = kpi_data.get("non_h_costs_eur_kwh", 0) if kpi_data.get(
#                             "non_h_costs_eur_kwh") is not None else 0

#     for asset in building_energy_asset:
#         if asset.get(GENERATION_SYSTEM_ID,0)==83:
#             if building_use_id in [1, 2, 3]:
#                 # print('to be modified in the future')
#                 total_energy_costs_now=KPIs[12].household_costs_yearly
#                 total_energy_costs_baseline=(sum(self_consumption)+sum(grid_consumption))*cost_of_electricity_household
#                 costs = calculate_costs(capacity=asset[PMAX_SCALAR],
#                                                               generation_system_id=83,
#                                                               generation_time_series=total_PV,
#                                                               total_energy_costs_now=total_energy_costs_now,
#                                                               total_energy_costs_baseline=total_energy_costs_baseline
#                                                               )
#             else:
#                 total_energy_costs_now = KPIs[12].non_h_costs_yearly
#                 total_energy_costs_baseline = (sum(self_consumption) + sum(
#                     grid_consumption)) * cost_of_electricity_non_household
#                 costs = calculate_costs(capacity=asset[PMAX_SCALAR],
#                                                               generation_system_id=83,
#                                                               generation_time_series=total_PV,
#                                                               total_energy_costs_now=total_energy_costs_now,
#                                                               total_energy_costs_baseline=total_energy_costs_baseline
#                                                               )
#             #     total_energy_cost = sum(total_non_h_costs)
#             # area_building = building_asset_context.get(BUILDING, {}).get(AREA)

#      # print('to be modified in the future') add here other technologies..

#     return (total_PV,rate_of_self_consumption, self_sufficiency, total_electricity_use, self_consumption,
#             total_final_energy, KPIs, costs)

# def aggregate_demand_profiles(demand_profile):
#     """
#     Aggregate multiple demand profiles into a single total profile.

#     Parameters
#     ----------
#     demand_profile : list or dict
#         Demand profile(s) per building.

#     Returns
#     -------
#     dict
#         Aggregated total demand for all buildings.
#     """
#     total_demand = {}

#     if isinstance(demand_profile, list):
#         for building in demand_profile:
#             profile = building.get(DEMAND_PROFILE, {})

#             for demand_type, demand_values in profile.items():
#                 # ✅ FIX 1: Ensure demand_values is a list
#                 if isinstance(demand_values, (int, float)):
#                     demand_values = [float(demand_values)]
#                 elif not isinstance(demand_values, list):
#                     continue  # skip unexpected types
#                 demand_values = [0.0 if v is None else float(v) for v in demand_values]

#                 if demand_type in total_demand:
#                     # ✅ FIX 2: Use min length to avoid IndexError
#                     min_len = min(len(total_demand[demand_type]), len(demand_values))
#                     total_demand[demand_type] = [
#                         total_demand[demand_type][i] + demand_values[i]
#                         for i in range(min_len)
#                     ]
#                 else:
#                     total_demand[demand_type] = demand_values

#     elif isinstance(demand_profile, dict):
#         for demand_type, demand_values in demand_profile.get(DEMAND_PROFILE, {}).items():
#             if isinstance(demand_values, (int, float)):
#                 demand_values = [float(demand_values)]
#             elif not isinstance(demand_values, list):
#                 continue
#             demand_values = [0.0 if v is None else float(v) for v in demand_values]

#             if demand_type in total_demand:
#                 min_len = min(len(total_demand[demand_type]), len(demand_values))
#                 total_demand[demand_type] = [
#                     total_demand[demand_type][i] + demand_values[i]
#                     for i in range(min_len)
#                 ]
#             else:
#                 total_demand[demand_type] = demand_values

#     else:
#         raise TypeError("demand_profile must be either a list or a dictionary.")

#     return total_demand

def community_KPIs(citizen_KPIs,total_demand,areas_buildings):
    # Initialize an empty dictionary to hold the sum of each KPI
    aggregate_KPIs = {}
    # Define the KPIs requiring area-weighted aggregation
    area_weighted_kpis = [
        "total_primary_energy_intensity",
        "national_average_total_primary_energy_intensity",
        "total_CO2_intensity",
        "national_average_total_CO2_intensity",
        "total_energy_cost_intensity",
        "national_average_total_energy_cost_intensity"
    ]
    # Initialize storage for area-weighted KPI sums
    area_weighted_sums = {kpi: 0 for kpi in area_weighted_kpis}
    total_area = 0
    # Loop through each building"s KPI data in citizen_KPIs
    for building_id, kpis in citizen_KPIs.items():
        building_area = areas_buildings[building_id][AREA]
        total_area += building_area
        for kpi in kpis:
            kpi_name = kpi["name"]
            kpi_value = kpi["value"]
            # Area-weighted aggregation
            if kpi_name in area_weighted_kpis:
                area_weighted_sums[kpi_name] += kpi_value * building_area
                # Standard aggregation for numeric values
            elif isinstance(kpi_value, (int, float)):
                if kpi_name in aggregate_KPIs:
                    aggregate_KPIs[kpi_name]["value"] += kpi_value
                else:
                    aggregate_KPIs[kpi_name] = {"value": kpi_value, "unit": kpi["unit"]}

            # Time-series aggregation
            elif isinstance(kpi_value, list):
                timestep_count = len(kpi_value)
                if kpi_name in aggregate_KPIs:
                    aggregate_KPIs[kpi_name]["value"] = [
                        aggregate_KPIs[kpi_name]["value"][i] + kpi_value[i]
                        for i in range(timestep_count)
                    ]
                else:
                    aggregate_KPIs[kpi_name] = {"value": kpi_value, "unit": kpi["unit"]}
    # Finalize area-weighted KPIs
    for kpi_name in area_weighted_kpis:
        # Find the first occurrence of the KPI in citizen_KPIs to extract its unit
        unit = next(
            (kpi["unit"] for building_kpis in citizen_KPIs.values()
             for kpi in building_kpis if kpi["name"] == kpi_name),
            None
        )
        aggregate_KPIs[kpi_name] = {
            "value": area_weighted_sums[kpi_name] / total_area,
            "unit": unit if unit else "N/A"
        }

    aggregate_KPIs["KPI_peak_heat_demand_[kWh]"]={"value": max(total_demand[HEATING_DEMAND]),"unit": "kWh"}
    aggregate_KPIs["KPI_peak_dhw_demand_[kWh]"]={"value":max(total_demand[DHW_DEMAND]),"unit": "kWh"}
    aggregate_KPIs["KPI_peak_cooling_demand_[kWh]"]={"value": max(total_demand[COOLING_DEMAND]),"unit": "kWh"}
    aggregate_KPIs["KPI_peak_elec_demand_[kWh]"]={"value": max(total_demand[ELECTRICITY_DEMAND]),"unit": "kWh"}
    aggregate_KPIs["KPI_peak_electricity_consumption_[kWh]"]={"value": max(aggregate_KPIs[FINAL_ENERGY_ELECTRICITY_GRID]["value"]),"unit": "kWh"}
    # `aggregate_KPIs` now contains the summed values for each KPI across all buildings
    return aggregate_KPIs

def get_totals_per_building (KPIs,timestep_count,final_energy):
    """

    Parameters
    ----------
    KPIs
    timestep_count
    final_energy

    Returns
    -------

    """
    # Initialize totals for the current building
    total_primary_energy= [0] * timestep_count
    total_primary_energy_renewable = [0] * timestep_count
    total_primary_energy_non_renewable = [0] * timestep_count
    total_non_h_costs = [0] * timestep_count
    total_h_costs = [0] * timestep_count
    total_co2= [0] * timestep_count
    for id_carrier, energy_instance in KPIs.items():
        if energy_instance is not None:
            # Use dot notation to access the energy instance attributes
            total_primary_energy = [
                total_primary_energy[i] + energy_instance.PEF_total[i]
                for i in range(timestep_count)
            ]

            total_primary_energy_renewable = [
                total_primary_energy_renewable[i] + energy_instance.PEF_ren[i]
                for i in range(timestep_count)
            ]

            total_primary_energy_non_renewable = [
                total_primary_energy_non_renewable[i] + energy_instance.PEF_nren[i]
                for i in range(timestep_count)
            ]

            total_non_h_costs = [
                total_non_h_costs[i] + energy_instance.non_h_costs[i]
                for i in range(timestep_count)
            ]

            total_h_costs= [
                total_h_costs[i] + energy_instance.household_costs[i]
                for i in range(timestep_count)
            ]

            total_co2 = [
                total_co2[i] + energy_instance.co2[i]
                for i in range(timestep_count)
            ]
    total_primary_energy_kWh = total_primary_energy  # it is already in kWh unless we decide otherwise
    total_co2_kg = [x / 1000 for x in total_co2]
    # Extract dictionary of citizen_kpis_factors
    citizen_kpis_factors = kpi_ctz_factors()
    # KPI Equivalent TV hours
    TV_h = tv_h(citizen_kpis_factors=citizen_kpis_factors,
                total_primary_energy=total_primary_energy_kWh)
    # KPI Equivalent streaming hours
    streaming_hours = streaming_h(citizen_kpis_factors=citizen_kpis_factors,
                                  total_primary_energy=total_primary_energy_kWh)
    # KPI equivalent pizza items
    Pizza_h = pizza_h(citizen_kpis_factors=citizen_kpis_factors,
                      total_primary_energy=total_primary_energy_kWh)
    # Equivalent battery usage estimation
    Battery_charges = battery_charges(citizen_kpis_factors=citizen_kpis_factors,
                                      total_primary_energy=total_primary_energy_kWh)
    # Equivalent electric car charging times
    ElCar_charges = el_car_charges(citizen_kpis_factors=citizen_kpis_factors,
                                   total_primary_energy=total_primary_energy_kWh)
    # Equivalent trees - - CO2
    Trees_number = trees_number(citizen_kpis_factors=citizen_kpis_factors, total_co2=total_co2_kg)

    # Equivalent Streaming impact in emissions - - CO2
    streaming_emissionhours = streaming_emission_hours(citizen_kpis_factors=citizen_kpis_factors,
                                                       total_co2=total_co2_kg)
    # - - CO2
    ICV_km = icv_km(citizen_kpis_factors=citizen_kpis_factors, total_co2=total_co2_kg)
    # Equivalent wine bottles produced - - CO2
    Wine_bottles = wine_bottles(citizen_kpis_factors=citizen_kpis_factors,
                                total_primary_energy=total_primary_energy_kWh)
    FinalEnergy_dic = {}

    for key, energy_instance in final_energy.items():
        # Check if there"s any non-zero value in hourly_data
        if any(value > 0 for value in energy_instance.hourly_data):
            # Add to the dictionary with the appropriate name as key
            FinalEnergy_dic[f"final_energy_{energy_instance.name}"] = energy_instance.hourly_data

    return (total_primary_energy_kWh, total_co2,total_primary_energy_non_renewable, total_primary_energy_renewable,
            total_h_costs, total_non_h_costs, TV_h, streaming_hours, Pizza_h, Battery_charges, ElCar_charges, Trees_number,
            streaming_emissionhours, ICV_km, Wine_bottles,FinalEnergy_dic)

def filter_function(df, variable, building_use_id, construction_year, country_id):
    try:
        # Step 1: Full match
        df_filtered = df[
            (df[BUILDING_USE_ID] == int(building_use_id)) &
            (df[CONSTRUCTION_YEAR] == int(construction_year)) &
            (df[COUNTRY_ID] == float(country_id))
        ][variable].values
        # Step 2: Match without construction_year
        if len(df_filtered) == 0:
            df_filtered = df[
                (df["building_use_id"] == building_use_id) &
                (df["country_id"] == country_id)
                ][variable].values

        # Step 3: Match with country_id set to 31
        if len(df_filtered) == 0:
            df_filtered = df[
                (df["building_use_id"] == building_use_id) &
                (df["country_id"] == 31)
                ][variable].values

        # Step 4: Return default if still empty
        if len(df_filtered) == 0:
            if variable == "total_primary_energy_intensity":
                return 234.87
            elif variable == "total_energy_cost_intensity":
                return 22
            elif variable == "total_CO2_intensity":
                return 43149.28568

        return df_filtered[0]
    except Exception as e:
        # print(f"Error during filtering in {variable}: {e}")
        if variable == "total_primary_energy_intensity":
            return 234.87
        elif variable == "total_energy_cost_intensity":
            return 22
        elif variable == "total_CO2_intensity":
            return 43149.28568

def filter_values(filename, building_use_id, construction_year, country_id):
    """

    Parameters
    ----------
    filename: total_primary_energy_GHG_costs_intensity.csv
    building_use_id
    construction_year
    country_id

    Returns
    -------
    National averages: total_primary_energy_intensity_filtered, total_energy_cost_filtered, total_CO2_filtered

    """
    # Cast input values to int if not None
    building_use_id = int(building_use_id) if building_use_id is not None else None
    construction_year = int(construction_year) if construction_year is not None else None
    country_id = int(country_id) if country_id is not None else None

    parent_directory =   os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(parent_directory, "scenario_generator", filename)

    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        # print(f"Error: The file {filename} does not exist in the specified directory. , average values provided: 	234.87, 22, 43149.28568")
        return 234.87, 22, 43149.28568
    except Exception as e:
        # print(f"Error loading file {filename}: {e}")
        return 234.87, 22, 43149.28568



    # Ensure required columns are present
    required_columns = {"country_id","building_use_id", "construction_year", "total_primary_energy_intensity", "total_energy_cost_intensity", "total_CO2_intensity"}
    if not required_columns.issubset(df.columns):
        # print(f"Error: The file {filename} must contain the following columns: {required_columns}, average values provided: 	234.87, 22, 43149.28568")
        return 234.87, 22, 43149.28568
    # Cast relevant DataFrame columns to int
    df[BUILDING_USE_ID] = df[BUILDING_USE_ID].astype("Int64")
    df[CONSTRUCTION_YEAR] = df[CONSTRUCTION_YEAR].astype("Int64")
    df[COUNTRY_ID] = df[COUNTRY_ID].astype("Int64")

    try:
        # Perform filtering for each variable
        total_primary_energy_intensity_filtered = filter_function(
            df=df,
            variable="total_primary_energy_intensity",
            building_use_id=building_use_id,
            construction_year=construction_year,
            country_id=country_id,
        )
        total_energy_cost_filtered = filter_function(
            df=df,
            variable="total_energy_cost_intensity",
            building_use_id=building_use_id,
            construction_year=construction_year,
            country_id=country_id,
        )
        total_CO2_filtered = filter_function(
            df=df,
            variable="total_CO2_intensity",
            building_use_id=building_use_id,
            construction_year=construction_year,
            country_id=country_id,
        )
        if total_primary_energy_intensity_filtered is None:
            total_primary_energy_intensity_filtered= 234.87
        if total_energy_cost_filtered is None:
            total_energy_cost_filtered =22
        if total_CO2_filtered is None:
            total_CO2_filtered= 43149.28568

        return total_primary_energy_intensity_filtered, total_energy_cost_filtered, total_CO2_filtered
    except Exception as e:
        # print(f"Error during filtering: {e}, average values provided: 	234.87, 22, 43149.28568")
        return 234.87, 22, 43149.28568

def get_indicators_from_baseline(front_data, data, building_consumption_dict, demand_profile):
    """

    Parameters
    ----------
    front_data = {
    data
    building_consumption_dict

    Returns
    -------

    """
    rate_of_self_consumption = {}
    self_sufficiency = {}
    total_electricity_use = {}
    self_consumption = {}
    total_final_energy = {}
    total_PV = {}
    # groups
    KPIs = {}
    citizen_KPIs = {}
    costs={}
    # Define the number of hours for each month (non-leap year)
    hours_per_month = {
        "January": 744, "February": 672, "March": 744, "April": 720,
        "May": 744, "June": 720, "July": 744, "August": 744,
        "September": 720, "October": 744, "November": 720, "December": 744
    }

    # Total hours in a day
    hours_per_day = 24
    areas_buildings={}

    for i, item in enumerate(front_data):
        # Case 1: building_statistics_profile_id is in front_data and there is a loop for each item in front_data (per building)
        if "building_statistics_profile_id" in item:
            building_statistics_profile_id = item["building_statistics_profile_id"]
            building_profile = next(
                (profile for profile in data if profile.get(ID) == building_statistics_profile_id), None)

            if building_profile is None:
                raise ValueError(
                    f"No se encontró el perfil de estadísticas del edificio con id {building_statistics_profile_id}")

            generation_system_profile = building_profile.get(GENERATION_SYSTEM_PROFILE, {})
            building_use_id = item.get(BUILDING_USE_ID)
            construction_year= item.get(CONSTRUCTION_YEAR)
            # Check the type of item["geom"] and process accordingly
            if isinstance(item["geom"], str):
                # If it's a string, assume it's WKT and convert it to a Shapely geometry object
                wkt_geom = item["geom"]
                geom = wkt.loads(wkt_geom)
            else:
                # Otherwise, assume it's a GeoJSON-like dictionary and use shape()
                geom = shape(item["geom"])
            area_building = geom.area
            # Check if area_building is 0 and assign 100 if true
            if area_building < 10:
                area_building = 100
        else:
            # Else case: No "building_statistics_profile_id" found, we use the "building_statistics_profile"
            building_statistics_profiles = data.get("building_statistics_profile", [])
            generation_system_profile = building_statistics_profiles.get(GENERATION_SYSTEM_PROFILE, {})
            building_use_id = front_data.get(BUILDING_USE_ID)
            construction_year = front_data.get(CONSTRUCTION_YEAR)
            if isinstance(front_data["location"], str):
                # If it's a string, assume it's WKT and convert it to a Shapely geometry object
                wkt_geom = front_data["location"]
                geom = wkt.loads(wkt_geom)
            else:
                # Otherwise, assume it's a GeoJSON-like dictionary and use shape()
                geom = shape(front_data["location"])
            area_building = geom.area
            # Check if area_building is 0 and assign 100 if true
            if area_building < 10:
                area_building = 100 * front_data["num_building"]

            if isinstance(building_statistics_profiles, dict):
                building_statistics_profiles = [building_statistics_profiles]

        building_id=i+1
        areas_buildings[building_id] = {}
        areas_buildings[building_id][AREA] = area_building
        # Get the consumption data for each type of generation system (8760 hourly values)
        # Fetch the building consumption
        building_consumption = building_consumption_dict.get(f"building_id_{i + 1}", {})
        # Check if the retrieved value is empty; if so, get the value for "building_id_1"
        if not building_consumption:
            building_consumption = building_consumption_dict.get("building_id_1", {})

        heating_consumption = building_consumption.get(HEAT_CONSUMPTION, [0] * 8760)
        electricity_consumption = building_consumption.get(ELECTRICITY_CONSUMPTION, [0] * 8760)
        cooling_consumption = building_consumption.get(COOL_CONSUMPTION, [0] * 8760)
        dhw_consumption = building_consumption.get(DHW_CONSUMPTION, [0] * 8760)

        # Check if demand_profile contains multiple buildings or a single building
        if isinstance(demand_profile, list):
            # Multiple buildings: loop through each building
            demand_profile_building = demand_profile[i]
            demand_profile_building = demand_profile_building[DEMAND_PROFILE]
        else:
            # Single building case
            demand_profile_building = demand_profile[DEMAND_PROFILE]
            # Process the single building profile here

        # Define the systems to process (linking them to the profiles)
        systems = {
            HEATING_SYSTEM: heating_consumption,
            "electricity_system": electricity_consumption,
            COOLING_SYSTEM: cooling_consumption,
            DHW_SYSTEM: dhw_consumption
        }

        building_energy_asset=[]
        (
            total_PV[building_id],
            rate_of_self_consumption[building_id],
            self_sufficiency[building_id],
            total_electricity_use[building_id],
            self_consumption[building_id],
            total_final_energy[building_id],
            KPIs[building_id],
            costs[building_id]
        ) = calculate_building_indicators(consumption_profile=building_consumption,
                                          generation_system_profile=generation_system_profile,
                                          building_energy_asset=building_energy_asset,
                                          timestep_count=len(dhw_consumption),
                                          building_use_id=building_use_id)

        (total_primary_energy_kWh, total_co2, total_primary_energy_non_renewable, total_primary_energy_renewable,
         total_h_costs, total_non_h_costs, TV_h, streaming_hours, Pizza_h, Battery_charges, ElCar_charges, Trees_number,
         streaming_emissionhours, ICV_km, Wine_bottles, FinalEnergy_dic) = get_totals_per_building(KPIs[building_id],
                                                                                                   timestep_count=len(
                                                                                                       dhw_consumption),
                                                                                                   final_energy=
                                                                                                   total_final_energy[
                                                                                                           building_id])
        KPI_peak_heat_demand = max(demand_profile_building[HEATING_DEMAND])
        # calculate peak cooling demand
        KPI_peak_elec_demand = max(total_electricity_use[building_id])

        # Extract country_id from generation_system_profile
        try:
            country_id = generation_system_profile[ELECTRICITY_SYSTEM][ENERGY_CARRIER_INPUT1][
                NATIONAL_ENERGY_CARRIER_DATA][0][COUNTRY_ID]
        except (KeyError, IndexError, TypeError):
            print(f"Error: Unable to extract {COUNTRY_ID} from {GENERATION_SYSTEM_PROFILE}.")
            country_id = None

        national_average_total_primary_energy_intensity, national_average_total_CO2, national_average_total_energy_cost = filter_values(
            filename="total_primary_energy_GHG_costs_intensity.csv",
            building_use_id=building_use_id,
            construction_year=construction_year,
            country_id=country_id)

        if building_use_id in [1, 2, 3]:
            total_energy_cost = sum(total_h_costs)
        else:
            total_energy_cost = sum(total_non_h_costs)

        if area_building > 0:
            total_primary_energy_intensity_kWh = sum(total_primary_energy_kWh) / area_building
            total_co2_intensity = sum(total_co2) / area_building
            total_energy_cost_intensity = total_energy_cost / area_building
        else:
            area_building = 1
            total_primary_energy_intensity_kWh = sum(total_primary_energy_kWh) / area_building
            total_co2_intensity = sum(total_co2) / area_building
            total_energy_cost_intensity = total_energy_cost / area_building


        # Store citizen KPIs for the building
        citizen_KPIs[building_id] = [
            {ID: 1, "name": "KPI_peak_heat_demand_[kWh]", "value": KPI_peak_heat_demand, "unit": "kWh"},
            {ID: 2, "name": "KPI_peak_elec_demand_[kWh]", "value": KPI_peak_elec_demand, "unit": "kWh"},
            {ID: 3, "name": "total_primary_energy_[kWh]", "value": total_primary_energy_kWh,
             "unit": "kWh"},
            {ID: 4, "name": "num_members", "value": 0, "unit": "a.u."},
            {ID: 5, "name": "EquivalentTVHours_[h]", "value": TV_h, "unit": "h"},
            {ID: 6, "name": "EquivalentstreamingHours_[h]", "value": streaming_hours, "unit": "h"},
            {ID: 7, "name": "PizzaConsumptionComparison_[pizza]", "value": Pizza_h, "unit": "pizza"},
            {ID: 8, "name": "BatteryUsageEstimation_[charges]", "value": Battery_charges,
             "unit": "charges"},
            {ID: 9, "name": "ElectricCarChargingEstimation_[charges]", "value": ElCar_charges,
             "unit": "charges"},
            {ID: 10, "name": "WineBottlesProduction_[bottles]", "value": Wine_bottles, "unit": "bottles"},
            {ID: 11, "name": "TreesRequiredForCarbonOffset_[trees]", "value": Trees_number,
             "unit": "trees"},
            {ID: 12, "name": "streamingEmissionsImpact_[hours]", "value": streaming_emissionhours,
             "unit": "hours"},
            {ID: 13, "name": "CarbonEmissionsPerKilometer_[km]", "value": ICV_km, "unit": "km"},
            {ID: 14, "name": "Total_PV_[kWh]", "value": total_PV[building_id], "unit": "kWh"},
            {ID: 15, "name": "Total_self_consumption", "value": self_consumption[building_id], "unit": "a.u."},
            {ID: 16, "name": "Total_self_sufficiency", "value": self_sufficiency[building_id], "unit": "a.u."},
            {ID: 17, "name": "rate_of_self_consumption", "value": rate_of_self_consumption[building_id],
             "unit": "%"},
            {ID: 18, "name": "renewable_primary_energy_[kWh]",
             "value": total_primary_energy_renewable[building_id], "unit": "kWh"},
            {ID: 19, "name": "non_renewable_primary_energy_[kWh]",
             "value": total_primary_energy_non_renewable[building_id], "unit": "kWh"},
            {ID: 20, "name": "non_households_costs_[€]", "value": total_non_h_costs[building_id], "unit": "€"},
            {ID: 21, "name": "households_costs_[€]", "value": total_h_costs[building_id], "unit": "€"},
            {ID: 22, "name": "Total_co2", "value": total_co2, "unit": "g CO2eq"},
            {ID: 23, "name": "total_primary_energy_intensity", "value": total_primary_energy_intensity_kWh,
             "unit": "kWh/m2"},
            {ID: 24, "name": "national_average_total_primary_energy_intensity",
             "value": national_average_total_primary_energy_intensity, "unit": "kWh/m2"},
            {ID: 25, "name": "total_CO2_intensity", "value": total_co2_intensity, "unit": "g/m2"},
            {ID: 26, "name": "national_average_total_CO2_intensity", "value": national_average_total_CO2,
             "unit": "g/m2"},
            {ID: 27, "name": "total_energy_cost_intensity", "value": total_energy_cost_intensity, "unit": "€/m2"},
            {ID: 28, "name": "national_average_total_energy_cost_intensity",
             "value": national_average_total_energy_cost, "unit": "€/m2"}
        ]
        id_for_citizen_kpi = 29
        for key, energy_instance in FinalEnergy_dic.items():
            citizen_KPIs[building_id].append(
                {ID: id_for_citizen_kpi, "name": key, "value": energy_instance, "unit": "kWh"})
            id_for_citizen_kpi += 1


    return citizen_KPIs, areas_buildings


# # Function to calculate Net Present Value (NPV) of cash flows
# def calculate_npv(cash_flows, discount_rate):
#     """
#     Calculate the Net Present Value (NPV) of a series of cash flows.

#     Parameters:
#     - cash_flows: List of cash flows (e.g., annual OPEX or generation).
#     - discount_rate: The discount rate for NPV calculation.

#     Returns:
#     - NPV of the cash flows.
#     """
#     return sum(cf / ((1 + discount_rate) ** year) for year, cf in enumerate(cash_flows, start=1))

# # Function to calculate total CAPEX
# def calculate_total_capex(capacity, capex_per_kw):
#     """
#     Calculate total capital expenditure (CAPEX).

#     Parameters:
#     - capacity: Installed power capacity in kW.
#     - capex_per_kw: Capital cost per kW in EUR.

#     Returns:
#     - Total CAPEX in EUR.
#     """
#     return capacity * capex_per_kw


# # Function to calculate annual OPEX
# def calculate_annual_opex(annual_generation, opex_per_kwh):
#     """
#     Calculate annual operating expenses (OPEX).

#     Parameters:
#     - annual_generation: Total electricity generation per year in kWh.
#     - opex_per_kwh: Operating cost per kWh in EUR.

#     Returns:
#     - Annual OPEX in EUR.
#     """
#     return annual_generation * opex_per_kwh


# # Function to calculate total lifetime costs
# def calculate_total_lifetime_costs(capex, npv_opex):
#     """
#     Calculate total lifetime costs by summing CAPEX and discounted OPEX.

#     Parameters:
#     - capex: Total initial capital expenditure in EUR.
#     - npv_opex: Net Present Value of total OPEX in EUR.

#     Returns:
#     - Total lifetime costs in EUR.
#     """
#     return capex + npv_opex


# # Function to calculate Levelized Cost of Electricity (LCOE)
# def calculate_lcoe(total_lifetime_costs, npv_generation):
#     """
#     Calculate the Levelized Cost of Electricity (LCOE).

#     Parameters:
#     - total_lifetime_costs: Sum of CAPEX and discounted OPEX in EUR.
#     - npv_generation: NPV of electricity generation in kWh.

#     Returns:
#     - LCOE in EUR per kWh.
#     """
#     if npv_generation == 0:
#         raise ValueError("NPV of generation cannot be zero.")
#     return total_lifetime_costs / npv_generation


# # Function to calculate Payback Period
# def calculate_payback_period(total_capex, annual_savings, lifetime):
#     """
#     Calculate the payback period in years.

#     Parameters:
#     - total_capex: Total capital expenditure in EUR.
#     - annual_savings: Annual savings in EUR (baseline minus current).
#     - lifetime: System lifetime in years.

#     Returns:
#     - Payback period in years, or None if not achievable within the lifetime.
#     """
#     if annual_savings <= 0:
#         return None  # No payback achievable
#     years = total_capex / annual_savings
#     return years if years <= lifetime else None


# # Main calculation function
# def calculate_costs(capacity, generation_system_id, generation_time_series,
#         total_energy_costs_baseline=None, total_energy_costs_now=None):
#     """
#     Calculate system costs, savings, and LCOE for a specific generation system.

#     Parameters:
#     - capacity: Installed power capacity in kW.
#     - generation_system_id: ID of the selected energy generation system.
#     - generation_time_series: List of annual energy production values in kWh/year.
#     - total_energy_costs_baseline: Time-series baseline energy costs before system installation in EUR.
#     - total_energy_costs_now: Time-series current energy costs after system installation in EUR.

#     Returns:
#     - A dictionary containing:
#         - total_capex: Total CAPEX in EUR.
#         - npv_opex_before: NPV of costs before system installation.
#         - npv_opex_after: NPV of costs after system installation.
#         - total_lifetime_costs: Total lifetime costs after installation.
#         - lcoe: Levelized Cost of Electricity (LCOE) in EUR/kWh.
#         - total_savings: Total savings compared to baseline in EUR.
#         - payback_period_years: Payback period in years, or None if not achievable.
#     """
#     # Ensure generation_time_series is a valid list
#     if generation_time_series is None:
#         generation_time_series = [0]*8760
#     # Handle missing time-series costs
#     if total_energy_costs_baseline is None:
#         total_energy_costs_baseline = [0] * len(generation_time_series)
#     if total_energy_costs_now is None:
#         total_energy_costs_now = [0] * len(generation_time_series)
#     # Load system profile
#     energy_systems_catalogue = load_energy_system_catalogue()
#     system_profile = filter_energy_systems_catalogue(
#         energy_systems_catalogue=energy_systems_catalogue,
#         new_generation_system_id=generation_system_id)
#     # Ensure system_profile is not None
#     if system_profile is None:
#         CAPEX = 1000  # Default: 1000 EUR/kW
#         OPEX = 25  # Default: 25 EUR/kWh per year
#         lifetime = 20  # Default: 20 years
#     else:
#         # Extract parameters with default fallback
#         CAPEX = system_profile.get("capex_eur_kw", 1000)
#         OPEX = system_profile.get("opex_eur_kwh_year", 25)
#         lifetime = system_profile.get("lifetime_years", 20)
#     if capacity is None:
#         capacity=0
#     discount_rate = 0.05
#     # Calculate CAPEX
#     total_capex = calculate_total_capex(capacity, CAPEX)
#     # Total annual generation
#     annual_generation = sum(generation_time_series)
#     # Maintenance and operating costs
#     annual_maintenance_cost = calculate_annual_opex(annual_generation=annual_generation, opex_per_kwh=OPEX)
#     # Total energy costs per year
#     annual_baseline_cost = sum(total_energy_costs_baseline) if isinstance(total_energy_costs_baseline,
#                                                                           list) else total_energy_costs_baseline
#     annual_current_cost = sum(total_energy_costs_now) if isinstance(total_energy_costs_now,
#                                                                     list) else total_energy_costs_now
#     # Ensure lifetime is a positive integer
#     if lifetime is None or lifetime < 0:
#         raise ValueError("Lifetime must be a positive integer.")
#     lifetime = int(lifetime)

#     # Cash flows for lifetime
#     baseline_cash_flows = [annual_baseline_cost] * lifetime
#     current_cash_flows = [annual_current_cost + annual_maintenance_cost] * lifetime

#     # Calculate NPVs (result as floats)
#     npv_opex_before = calculate_npv(baseline_cash_flows, discount_rate)
#     npv_opex_after = calculate_npv(current_cash_flows, discount_rate)

#     # Calculate total lifetime costs
#     total_lifetime_costs = total_capex + npv_opex_after

#     # Calculate total savings
#     total_savings = npv_opex_before - npv_opex_after

#     # Calculate LCOE
#     npv_generation = calculate_npv([annual_generation] * lifetime, discount_rate)
#     if npv_generation == 0:
#         lcoe = None
#     else:
#         lcoe = calculate_lcoe(total_lifetime_costs, npv_generation)
#     # Calculate payback period
#     annual_savings = total_savings / lifetime

#     # Calculate payback period
#     if annual_savings <= 0:
#         payback_period = None  # If no savings, no payback period
#     else:
#         payback_period = calculate_payback_period(total_capex, annual_savings, lifetime)

#     # Return results
#     return {
#         "total_capex": total_capex,
#         "npv_opex_before": npv_opex_before,
#         "npv_opex_after": npv_opex_after,
#         "total_lifetime_costs": total_lifetime_costs,
#         "lcoe": lcoe,
#         "total_savings": total_savings,
#         "payback_period_years": payback_period
#     }


def recalculate_indicators (community_context):
    #dictionary handlers for every KPI and every building
    rate_of_self_consumption={}
    self_sufficiency={}
    total_electricity_use={}
    self_consumption={}
    total_final_energy={}
    total_PV={}
    #groups of KPIs
    KPIs={}
    citizen_KPIs={}
    costs={}
    areas_buildings = {}
    # Totals
    hourly_KPIs = {}
    demand_profiles_context=[]
    if BUILDING_ASSET_CONTEXT in community_context and isinstance(community_context[BUILDING_ASSET_CONTEXT], list):
        for building_asset_context in community_context[BUILDING_ASSET_CONTEXT]:
            building_id_increment=0
            # Check if GENERATION_SYSTEM_PROFILE_ID is in the building_dic
            if GENERATION_SYSTEM_PROFILE_ID in building_asset_context:
                # Handle building_id: If it doesn"t exist, assign an incremented id
                building_id = building_asset_context.get(ID, f"building_{building_id_increment + 1}")  # Incremental ID if missing
                # Handle consumption_profile: Raise an error if it doesn"t exist
                if BUILDING_CONSUMPTION not in building_asset_context or building_asset_context[
                    BUILDING_CONSUMPTION] is None:
                    raise ValueError(f"Consumption profile does not exist for building ID: {building_id}")
                consumption_profile = building_asset_context[BUILDING_CONSUMPTION]
                # Handle timestep_count: If null, use the length of any of the consumption profile arrays
                timestep_count = community_context.get("timestep_count")
                if timestep_count is None:
                    if len(consumption_profile) > 0:
                        timestep_count = len(
                            next(iter(consumption_profile.values())))  # Length of first consumption array
                    else:
                        raise ValueError(f"Timestep count could not be determined for building ID: {building_id}")
                # Handle building_energy_asset: Assign None if it doesn"t exist
                building_energy_asset = building_asset_context.get("building_energy_asset", None)


                # Handle generation_system_profile: Assign None if it doesn"t exist
                generation_system_profile = building_asset_context.get(GENERATION_SYSTEM_PROFILE, None)
                demand_profile=handle_demand_profile(building_asset_context,generation_system_profile,consumption_profile)
                demand_profiles_context.append({DEMAND_PROFILE: demand_profile})
                building_use_id = building_asset_context.get(BUILDING, {}).get(BUILDING_USE_ID)
                # Further processing such as adding to KPIs, calculating other values, etc.
                #timestep_count=community_context["timestep_count"]
                #building_id = building_asset_context[ID]
                #building_energy_asset = building_asset_context["building_energy_asset"]
                #generation_system_profile = building_asset_context[GENERATION_SYSTEM_PROFILE]
                #consumption_profile = building_asset_context[BUILDING_CONSUMPTION]
                #demand_profile=building_asset_context[BUILDING][DEMANDPROFILE]
                hourly_KPIs[building_id] = {}
                # Calculate building indicators
                (
                    total_PV[building_id],
                    rate_of_self_consumption[building_id],
                    self_sufficiency[building_id],
                    total_electricity_use[building_id],
                    self_consumption[building_id],
                    total_final_energy[building_id],
                    KPIs[building_id],
                    costs[building_id]
                ) = calculate_building_indicators(consumption_profile, generation_system_profile, building_energy_asset,
                                                  timestep_count,building_use_id)

                # Add consumption_profile and demand_profile
                for key, value in consumption_profile.items():
                    hourly_KPIs[building_id].update({
                        f"consumption_profile_{key}": value})

                for key, value in demand_profile.items():
                    hourly_KPIs[building_id].update({
                        f"demand_profile_{key}" : value})
                building_id_increment+=1
            (total_primary_energy_kWh, total_co2, total_primary_energy_non_renewable, total_primary_energy_renewable,
             total_h_costs, total_non_h_costs, TV_h, streaming_hours, Pizza_h, Battery_charges, ElCar_charges,
             Trees_number,
             streaming_emissionhours, ICV_km, Wine_bottles, FinalEnergy_dic) = get_totals_per_building(KPIs[building_id],
                                                                                                       timestep_count=timestep_count,
                                                                                                       final_energy=total_final_energy[building_id])
            # calculate peak heat demand
            KPI_peak_heat_demand = max(demand_profile[HEATING_DEMAND])
            # calculate peak cooling demand
            KPI_peak_elec_demand = max(total_electricity_use[building_id])
            try:
                # Extract country_id from generation_system_profile
                data = generation_system_profile[ELECTRICITY_SYSTEM][ENERGY_CARRIER_INPUT1][
                    NATIONAL_ENERGY_CARRIER_DATA]
                if isinstance(data, list):
                    # Look for a match in the list
                    country_id=data[0][COUNTRY_ID]
                else:
                    country_id=data[COUNTRY_ID]
            except (KeyError, IndexError, TypeError):
                # print(f"Error: Unable to extract {COUNTRY_ID} from {GENERATION_SYSTEM_PROFILE}.")
                #assign European country id (31)
                country_id = 31
            try:
                #get national averages for KPIs comparison
                national_average_total_primary_energy_intensity,national_average_total_CO2,national_average_total_energy_cost =filter_values(filename="total_primary_energy_GHG_costs_intensity.csv",
                                                                          building_use_id=building_use_id,
                                                                          construction_year=building_asset_context.get(BUILDING, {}).get(CONSTRUCTION_YEAR),
                                                                          country_id=country_id)
            except (KeyError, IndexError, TypeError):
                print(f"Error: national_average_total_primary_energy_intensity, "
                      f"national_average_total_CO2 or national_average_total_energy_cost "
                      f"is None  ")
            areas_buildings[building_id]={}
            # building_use_mapping = {
            #     1: "residential",  # residential
            #     2: "residential",  # residential
            #     3: "residential",  # residential
            #     4: "office",  # office
            #     5: "commerce",  # commerce
            #     6: "education",  # education
            # }
            if building_use_id in [1,2,3]:
                total_energy_cost=sum(total_h_costs)
            else:
                total_energy_cost=sum(total_non_h_costs)
            area_building = building_asset_context.get(BUILDING, {}).get(AREA)
            if area_building>1:
                total_primary_energy_intensity_kWh = sum(total_primary_energy_kWh) / area_building
                total_co2_intensity=sum(total_co2)/ area_building
                total_energy_cost_intensity=total_energy_cost/area_building
            else:
                # print(f"Error: building area cannot be close to 0, e.g. 1*10-6, 100m2 is assumed")
                area_building=100 #m2 assumption
                total_primary_energy_intensity_kWh = sum(total_primary_energy_kWh) / area_building
                total_co2_intensity=sum(total_co2)/ area_building
                total_energy_cost_intensity=total_energy_cost/area_building
            areas_buildings[building_id][AREA]=area_building
            #get cost data
            if costs[building_id] is not None:
                total_capex = costs[building_id].get("total_capex", 0) if building_energy_asset else 0
                total_lifetime_costs = costs[building_id].get("total_lifetime_costs", 0) if building_energy_asset else 0
                total_savings = costs[building_id].get("total_savings", 0) if building_energy_asset else 0
                payback_period = costs[building_id].get("payback_period_years", 0) if building_energy_asset else 0
            else:
                total_capex = 0
                total_lifetime_costs = 0
                total_savings = 0
                payback_period = 0
            # Store citizen KPIs for the building
            citizen_KPIs[building_id] = [
                {ID: 1, "name": "KPI_peak_heat_demand_[kWh]", "value": KPI_peak_heat_demand, "unit": "kWh"},
                {ID: 2, "name": "KPI_peak_elec_demand_[kWh]", "value": KPI_peak_elec_demand, "unit": "kWh"},
                {ID: 3, "name": "total_primary_energy_[kWh]", "value": total_primary_energy_kWh, "unit": "kWh"},
                {ID: 4, "name": "num_members", "value": 0, "unit": "a.u."},
                {ID: 5, "name": "EquivalentTVHours_[h]", "value": TV_h, "unit": "h"},
                {ID: 6, "name": "EquivalentstreamingHours_[h]", "value": streaming_hours, "unit": "h"},
                {ID: 7, "name": "PizzaConsumptionComparison_[pizza]", "value": Pizza_h, "unit": "pizza"},
                {ID: 8, "name": "BatteryUsageEstimation_[charges]", "value": Battery_charges,
                 "unit": "charges"},
                {ID: 9, "name": "ElectricCarChargingEstimation_[charges]", "value": ElCar_charges,
                 "unit": "charges"},
                {ID: 10, "name": "WineBottlesProduction_[bottles]", "value": Wine_bottles, "unit": "bottles"},
                {ID: 11, "name": "TreesRequiredForCarbonOffset_[trees]", "value": Trees_number,
                 "unit": "trees"},
                {ID: 12, "name": "streamingEmissionsImpact_[hours]", "value": streaming_emissionhours,
                 "unit": "hours"},
                {ID: 13, "name": "CarbonEmissionsPerKilometer_[km]", "value": ICV_km, "unit": "km"},
                {ID: 14, "name": "Total_PV_[kWh]", "value": total_PV[building_id], "unit": "kWh"},
                {ID: 15, "name": "Total_self_consumption", "value": self_consumption[building_id], "unit": "a.u."},
                {ID: 16, "name": "Total_self_sufficiency", "value": self_sufficiency[building_id], "unit": "a.u."},
                {ID: 17, "name": "rate_of_self_consumption", "value": rate_of_self_consumption[building_id], "unit": "%"},
                {ID: 18, "name": "renewable_primary_energy_[kWh]", "value": total_primary_energy_renewable, "unit": "kWh"},
                {ID: 19, "name": "non_renewable_primary_energy_[kWh]", "value": total_primary_energy_non_renewable, "unit": "kWh"},
                {ID: 20, "name": "non_households_costs_[€]", "value": total_non_h_costs, "unit": "€"},
                {ID: 21, "name": "households_costs_[€]", "value": total_h_costs, "unit": "€"},
                {ID: 22, "name": "Total_co2", "value": total_co2, "unit": "g"},
                {ID: 23, "name": "total_primary_energy_intensity","value": total_primary_energy_intensity_kWh, "unit": "kWh/m2"},
                {ID: 24, "name": "national_average_total_primary_energy_intensity","value": national_average_total_primary_energy_intensity, "unit": "kWh/m2"},
                {ID: 25, "name": "total_CO2_intensity","value": total_co2_intensity, "unit": "g/m2"},
                {ID: 26, "name": "national_average_total_CO2_intensity","value": national_average_total_CO2, "unit": "g/m2"},
                {ID: 27, "name": "total_energy_cost_intensity","value": total_energy_cost_intensity, "unit": "€/m2"},
                {ID: 28, "name": "national_average_total_energy_cost_intensity","value": national_average_total_energy_cost, "unit": "€/m2"},
                {ID: 29, "name": "total_capex", "value": total_capex, "unit": "€"},
                {ID: 30, "name": "total_lifetime_costs", "value": total_lifetime_costs, "unit": "€"},
                {ID: 31, "name": "total_savings", "value": total_savings, "unit": "€"},
                {ID: 32, "name": "payback_period_years", "value": payback_period, "unit": "years"}
            ]
            id_for_citizen_kpi = 33
            for key, energy_instance in FinalEnergy_dic.items():
                citizen_KPIs[building_id].append({ID: id_for_citizen_kpi, "name": key, "value": energy_instance, "unit": "kWh"})
                id_for_citizen_kpi += 1
    else:
        print("community context structure is not correct, should be a list")
    return citizen_KPIs, demand_profiles_context,areas_buildings

