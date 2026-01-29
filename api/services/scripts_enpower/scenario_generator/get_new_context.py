import pandas as pd
import os
import copy
from datetime import datetime
from api.services.scripts_enpower.scenario_generator.context_creation import (
    create_unified_building_assets, 
    # create_unified_community_assets,
    get_centroid,
    call_PVGIS
)
from api.services.scripts_enpower.kpi_module.key_performance_indicators import handle_demand_profile
import api.services.scripts_enpower.helpers.constants as cte
from shapely.geometry import Point

# Constants for keys used across the context dictionary
AVAILABILITY_TS = cte.AVAILABILITY_TS
BUILDING_ASSET_CONTEXT = cte.BUILDING_ASSET_CONTEXT
COMMUNITY_ENERGY_ASSET = cte.COMMUNITY_ENERGY_ASSET
GENERATION_SYSTEM_PROFILE = cte.GENERATION_SYSTEM_PROFILE
GENERATION_SYSTEM_PROFILE_ID = cte.GENERATION_SYSTEM_PROFILE_ID
BUILDING = cte.BUILDING
BUILDING_CONSUMPTION = cte.BUILDING_CONSUMPTION
DEMANDPROFILE = cte.DEMANDPROFILE
HEATING_SYSTEM = cte.HEATING_SYSTEM
COOLING_SYSTEM = cte.COOLING_SYSTEM
DHW_SYSTEM = cte.DHW_SYSTEM
ELECTRICITY_SYSTEM = cte.ELECTRICITY_SYSTEM
ELECTRICITY_DEMAND = cte.ELECTRICITY_DEMAND
HEATING_DEMAND = cte.HEATING_DEMAND
COOLING_DEMAND = cte.COOLING_DEMAND
DHW_DEMAND = cte.DHW_DEMAND
ELECTRICITY_CONSUMPTION = cte.ELECTRICITY_CONSUMPTION
HEAT_CONSUMPTION = cte.HEAT_CONSUMPTION
COOL_CONSUMPTION = cte.COOL_CONSUMPTION
DHW_CONSUMPTION = cte.DHW_CONSUMPTION
ENERGY_CARRIER_INPUT1_ID = cte.ENERGY_CARRIER_INPUT1_ID
ENERGY_CARRIER_INPUT1 = cte.ENERGY_CARRIER_INPUT1
FINAL_ENERGY_ELECTRICITY_GRID = cte.FINAL_ENERGY_ELECTRICITY_GRID
VALUE_INPUT1 = cte.VALUE_INPUT1
PMAX_SCALAR = cte.PMAX_SCALAR
GENERATION_SYSTEM_ID = cte.GENERATION_SYSTEM_ID
FUEL_YIELD_1 = cte.FUEL_YIELD_1
DEMAND_PROFILE = cte.DEMAND_PROFILE
NATIONAL_ENERGY_CARRIER_DATA = cte.NATIONAL_ENERGY_CARRIER_DATA
DHW_SYSTEM_ID = cte.DHW_SYSTEM_ID
HEATING_SYSTEM_ID = cte.HEATING_SYSTEM_ID
COOLING_SYSTEM_ID = cte.COOLING_SYSTEM_ID
ELECTRICITY_SYSTEM_ID = cte.ELECTRICITY_SYSTEM_ID

def assign_ids(context):
    """
    Assigns temporary IDs to each energy asset in the context for easier handling.
    """
    asset_counter = 1
    for building_context in context.get(BUILDING_ASSET_CONTEXT, []):
        for asset in building_context.get("building_energy_asset", []):
            asset["id_temp"] = asset_counter
            if "availability_ts" in asset:
                asset["availability_ts"]["id_temp"] = asset_counter
            asset_counter += 1
            
    # for asset in context.get(COMMUNITY_ENERGY_ASSET, []):
    #     asset["id_temp"] = asset_counter
    #     if "availability_ts" in asset:
    #         asset["availability_ts"]["id_temp"] = asset_counter
    #     asset_counter += 1
    return context

def resbased_generator_context_creation(goal, community_context, recommendations_dic):
    """
    Orchestrates the creation of a new energy context using a unified asset structure.
    
    Parameters:
        goal (str): Description or name of the target scenario or optimization goal.
        community_context (dict): Original energy context with all buildings and assets.
        recommendations_dic (dict): Actions to apply, with IDs and names.

    Returns:
        community_context_updated (dict): The updated context with unified asset structure.
    """
    community_context_updated = copy.deepcopy(community_context)
    action_keys = {int(action["id"]) for action in recommendations_dic.values() if "id" in action}
    
    # --- Phase 1: Prepare common data and profiles ---
    print("   Phase 1: Preparing common energy profiles...")
    group_of_geoms = {
        b["building"]["id"]: {"geom": b["building"]["geom"]}
        for b in community_context.get(BUILDING_ASSET_CONTEXT, [])
    }
    _, community_centroid = get_centroid(group_of_geoms)
    
    # Call PVGIS API to retrieve shared PV and wind profiles for the entire community
    pv_profile, wind_profile, stc_profile = call_PVGIS(community_centroid.x, community_centroid.y, tilt_angle=35, use_realistic_wind=True)
    
    # Assemble common profiles into a dictionary
    common_profiles = {
        "pv_profile": pv_profile,
        "wind_profile": wind_profile,
        "stc_profile": stc_profile,
        "community_centroid_wkt": community_centroid.wkt
    }
    
    # Pre-compute demand profiles per building and add them to common_profiles
    for b_context in community_context.get(BUILDING_ASSET_CONTEXT, []):
        b_id = b_context["building"]["id"]
        common_profiles[f"demand_{b_id}"] = handle_demand_profile(
            b_context, 
            b_context.get("generation_system_profile", {}), 
            b_context.get("building_consumption", {})
        )

    # --- Phase 2: Generate unified asset lists ---
    print("   Phase 2: Generating unified asset lists...")
    
    
    # b) Building assets
    for building_data in community_context_updated.get(BUILDING_ASSET_CONTEXT, []):
        building_data["building_energy_asset"] = create_unified_building_assets(
            building_data,
            action_keys,
            common_profiles
        )
        # # Remove outdated generation system profile
        # if "generation_system_profile" in building_data:
        #     del building_data["generation_system_profile"]

        # Remove legacy profile but KEEP electricity system metadata for KPIs
        gsp = building_data.get("generation_system_profile", {})
        elec_sys = gsp.get("electricity_system")
        elec_id  = gsp.get("electricity_system_id")

        if elec_sys or elec_id:
            # Keep only the electricity system subset; drop the rest
            building_data["generation_system_profile"] = {}
            if elec_sys:
                building_data["generation_system_profile"]["electricity_system"] = elec_sys
            if elec_id:
                building_data["generation_system_profile"]["electricity_system_id"] = elec_id
        else:
            # If there is nothing useful, then remove the profile entirely
            building_data.pop("generation_system_profile", None)


    # --- Phase 3: Final assembly ---
    print("   Phase 3: Assembling final context...")

    # Defensive check: every building must expose electricity grid metadata somewhere
    for b in community_context_updated.get(BUILDING_ASSET_CONTEXT, []):
        has_grid_asset = any(
            ((a.get("generation_system") or {}).get("energy_carrier_input_1") == "electricity_grid") or
            ((a.get("generation_system") or {}).get("energy_carrier_input_1_id") == 24)
            for a in b.get("building_energy_asset", [])
        )
        has_grid_profile = bool(
            b.get("generation_system_profile", {}).get("electricity_system") or
            b.get("generation_system_profile", {}).get("electricity_system_id")
        )
        if not (has_grid_asset or has_grid_profile):
            b_id = b.get('building', {}).get('id', '?')
            b_name = b.get('building', {}).get('name', 'unknown')
            raise ValueError(
                f"Electricity grid metadata missing for building id={b_id}, name='{b_name}'."
            )

    # Assign temporary IDs to all newly created assets
    community_context_updated = assign_ids(community_context_updated)
    
    # Update context metadata (name, timestamp, etc.)
    actions_applied = {int(action["id"]): action["action_name"] for action in recommendations_dic.values() if "id" in action}
    action_str = "_".join(map(str, sorted(actions_applied.keys())))
    name_of_actions_applied = f"scenario_{action_str}"
    
    community_context_updated["context_parent"] = community_context.get("id")
    community_context_updated["name"] = f"{community_context_updated.get('context_parent', 'context')}_{name_of_actions_applied}"
    community_context_updated["description"] = f"{community_context_updated['name']}_with_goal_{goal}"
    community_context_updated["creation_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if "id" in community_context_updated:
        del community_context_updated["id"]  # Remove inherited ID to generate a new one

    print("✅ Unified context generated successfully.")
    return community_context_updated
