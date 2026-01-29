# =============================================================================
# module_integration.py
# =============================================================================
# Purpose
# ------------------------
# This file acts as the “glue” between the main parts of the Energy Optimization Framework.
# It provides small, clear functions that:
#   1) Recommend valid technology combinations for the front-end (what the user can choose).
#   2) Take an input context + a chosen combination and run the full OEMOF simulation.
#   3) Compute KPIs from the final context produced by the simulation.
#   4) Build a baseline scenario and community indicators from front-end inputs.
#
# The idea is simple: JSON in → JSON out. These helpers are easy to call from a UI or API.
# =============================================================================
import datetime
from typing import Dict, Any, List, Optional
from api.services.scripts_enpower.OEMOF_module.run_oemof_simulation import run_oemof_simulation
# from api.services.scripts_enpower.OEMOF_module.run_oemof_simulation_min_const import run_oemof_simulation
# KPI computation from a finished context
from api.services.scripts_enpower.calculate_kpis_from_context import calculate_energy_kpis_from_context
# Scenario generator (recommends technologies, builds unified context, handles geodata and demand)
from api.services.scripts_enpower.scenario_generator.RESbased_scenario_generator import (
    res_based_generator_list_technologies, # given (goal, country) → returns recommended actions/techs
    generate_geojson,  # builds a GeoJSON from front-end inputs
    fetch_geojson, # retrieves/saves the GeoJSON for processing
    baseline_pathway_intermediate,  # builds a baseline description for the pathway
    demand_thermagrid) # generates demand profiles using the “thermagrid” approach
# Create an OEMOF-ready context from recommendations
from api.services.scripts_enpower.scenario_generator.get_new_context import resbased_generator_context_creation
# Baseline energy computation by technology (consumption side)
from api.services.scripts_enpower.kpi_module.energy_consumption import generation_system_function
# Baseline indicators and aggregation helpers
from api.services.scripts_enpower.kpi_module.key_performance_indicators import get_indicators_from_baseline, aggregate_demand_profiles, community_KPIs, recalculate_indicators
from api.services.scripts_enpower.transform_structure import transform_whole_structure, reverse_whole_structure, pre_save_context_data
from api.services.scripts_enpower.OEMOF_module.tech_combinations_module import (combination_info,
                                                                                get_valid_combinations_for_front,
                                                                                add_generation_system_to_front_combos,
                                                                                parse_selected_combo,
                                                                                required_selected_actions)
from api.services.scripts_enpower.kpi_module.kpis_to_front import front_from_baseline


# =============================================================================
# Baseline pathway builder (optional helper)
# -----------------------------------------------------------------------------
# This helper:
#   - Generates GeoJSON from front-end inputs (location and settings)
#   - Builds hourly demand profiles (thermagrid)
#   - Computes baseline consumption per technology
#   - Creates a baseline object for the pathway
#   - Calculates citizen KPIs and community indicators for the baseline
# The result is useful for early-stage analysis before running full OEMOF.
# =============================================================================
def generate_baseline_pathway_intermediate(data, front_data, generation_system_information):
    geojson_object=generate_geojson(front_data=front_data)
    geojson_file = fetch_geojson(geojson_object=geojson_object)
    demand_profile=demand_thermagrid(front_data=front_data, geojson_file=geojson_file)
    #calculate energy consumption based on the technology
    building_consumption_dict = generation_system_function(data=data, front_data=front_data, demand_profile=demand_profile)
    #create baseline object
    baseline = baseline_pathway_intermediate(data=data, front_data=front_data, geojson_file=geojson_file, demand_profile=demand_profile, building_consumption_dict=building_consumption_dict )
    #calculate kpis per building
    citizen_KPIs,areas_buildings = get_indicators_from_baseline(data=data, front_data=front_data, demand_profile=demand_profile, building_consumption_dict=building_consumption_dict)
    # calculate total aggregated demand
    total_demand = aggregate_demand_profiles(demand_profile=demand_profile)
    # calculate total community indicators
    community_indicators = community_KPIs(citizen_KPIs=citizen_KPIs, total_demand=total_demand, areas_buildings=areas_buildings)
    #devolver más adelante citizen_KPIs_per_building,
    front_community_indicators = front_from_baseline(baseline_community_indicators=community_indicators,demand_profile=demand_profile,citizen_kpis_per_building=citizen_KPIs)
    return baseline, front_community_indicators


# =============================================================================
# Step 1 — Recommend valid combinations for the front-end (JSON in → JSON out)
# -----------------------------------------------------------------------------
# Input:  {"goals": "3", "country": "AT"}   (strings expected by recommender)
# Output: [{"id": 6, "combination": "HP+PV"}, {"id": 2, "combination": "TS"}, ...]
# Explanation:
#   - Ask the recommender which actions are relevant for (goal, country)
#   - Translate those detailed action names to short labels (PV, HP, TS…)
#   - Keep only the combinations that are truly feasible with those techs
# =============================================================================
def get_new_context(community_context):
    community_context_updated = reverse_whole_structure(community_context)
    return community_context_updated

def recommend_to_front_combos(goal):
    recs = res_based_generator_list_technologies(goal)
    tech_translation = combination_info()
    action_names = {v.get("action_name") for v in recs.values() if isinstance(v, dict)}
    translated = [tech_translation.get(a) for a in action_names if tech_translation.get(a)]
    list_of_possible_combination = get_valid_combinations_for_front(translated)
    final_list_of_combos = add_generation_system_to_front_combos(list_of_possible_combination)
    return final_list_of_combos


# =============================================================================
# Step 2 — Build unified context and run OEMOF with the user’s combination
# -----------------------------------------------------------------------------
# Typical call chain:
#   - Start from a base context (what the community/buildings look like today).
#   - Get recommendations for (goal, country).
#   - Filter those to keep only the actions required by the chosen combination (e.g., “HP+PV”).
#   - Create a unified, OEMOF-ready context entirely in memory.
#   - Run the OEMOF simulation and return the final context (with results).
# =============================================================================
def run_pipeline_from_context_json(community_context_updated,goal,selected_combo, generation_system_information):
    base_context = community_context_updated.get("context", community_context_updated)
    tech_translation = combination_info()
    recs = res_based_generator_list_technologies(goal)
    selected_combo_v1 = parse_selected_combo(selected_combo)
    selected_actions = required_selected_actions(selected_combo=selected_combo_v1,tech_translation = tech_translation, recs =recs)
    unified_context = resbased_generator_context_creation(goal=goal,community_context=base_context,recommendations_dic=selected_actions)
    final_context = run_oemof_simulation(context=unified_context)
    new_context_updated = transform_whole_structure(final_context)
    cleaned_context= pre_save_context_data(new_context_updated)
    kpis_totals = calculate_energy_kpis_from_context(final_context, country_id=None)
    return {"context":cleaned_context, "kpis":kpis_totals}


# =============================================================================
# Step 3 — Compute KPIs from the final context (JSON in → JSON out)
# -----------------------------------------------------------------------------
# Input:  final_context (the output of the OEMOF run)
# Output: dictionary with:
#   - "totals": community indicators
#   - "buildings": list of per-building indicators
# =============================================================================
def calculate_indicators(community_context):
    community_context_updated = reverse_whole_structure(community_context)
    citizen_kpis_per_building, demand_profiles_context, areas_buildings = recalculate_indicators(community_context_updated)
    total_demand = aggregate_demand_profiles(demand_profiles_context)
    community_indicators = community_KPIs(citizen_kpis_per_building,total_demand,areas_buildings)
    community_kpis= {
        "community": community_indicators,
        "buildings": citizen_kpis_per_building
        # "demand_profiles": demand_profiles_context,
        # "areas_buildings": areas_buildings,
    }
    return community_kpis

# def calculate_indicators(community_context):
#     #adapt structure
#     community_context_updated=reverse_whole_structure(community_context)
#     #with new structure calculate indicators
#     citizen_KPIs_per_building, demand_profiles_context,areas_buildings=recalculate_indicators(community_context_updated)
#     #calculate total aggregated demand
#     total_demand = aggregate_demand_profiles(demand_profiles_context)
#     #calculate total community indicators
#     community_indicators = community_KPIs(citizen_KPIs_per_building, total_demand,areas_buildings)
#     #devolver más adelante citizen_KPIs_per_building
#     return community_indicators
