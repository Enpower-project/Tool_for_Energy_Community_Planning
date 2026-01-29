# =============================================================================
# tech_combinations_module.py
# =============================================================================
# Purpose
# -------
# This file helps decide which *technology combinations* are possible and
# which part of the platform should handle them.
#
# Example:
#   - If the recommended technologies are ["HP", "PV"], then "HP+PV" is a valid
#     combination and will be handled by the OEMOF part of the framework.
#   - If the recommended technologies are ["PV", "Battery"], then "PV+Battery"
#     is valid but handled by the SITEC part of the framework.
#
# You can think of it as a small "router":
#   recommended techs  →  valid combos  →  which module should run (OEMOF or SITEC)
# =============================================================================

from api.services.scripts_enpower.scenario_generator.RESbased_scenario_generator import res_based_generator_list_technologies

# -----------------------------------------------------------------------------
# List of all combinations the front-end might show to the user.
# Each item has an id (just an internal number) and a readable "combination".
# -----------------------------------------------------------------------------
'''
PARA PRUEBAS

COMBINATIONS_FOR_FRONT = [
    {"id": 1, "combination": "HP", "generation_system": [2, 31, 63]},
    {"id": 2, "combination": "TS", "generation_system": [39, 71]},
    {"id": 3, "combination": "Wind", "generation_system": [132]},
    {"id": 4, "combination": "HP+TS", "generation_system": [2, 31, 39, 63, 71]},
    {"id": 5, "combination": "HP+Wind", "generation_system": [2, 31, 63, 132]},
    {"id": 6, "combination": "HP+PV", "generation_system": [2, 31, 63, 83]},
    {"id": 7, "combination": "TS+Wind", "generation_system": [39, 71, 132]},
    {"id": 8, "combination": "TS+PV", "generation_system": [39, 71, 83]},
    {"id": 9, "combination": "Wind+PV", "generation_system": [83, 132]},
    {"id": 10, "combination": "HP+TS+Wind", "generation_system": [2, 31, 39, 63, 71, 132]},
    {"id": 11, "combination": "HP+TS+PV", "generation_system": [2, 31, 39, 63, 71, 83]},
    {"id": 12, "combination": "HP+Wind+PV", "generation_system": [2, 31, 63, 83, 132]},
    {"id": 13, "combination": "TS+Wind+PV", "generation_system": [39, 71, 83, 132]},
    {"id": 14, "combination": "HP+TS+Wind+PV", "generation_system": [2, 31, 39, 63, 71, 83, 132]},
    {"id": 15, "combination": "DHN", "generation_system": [143, 151]},
    {"id": 16, "combination": "PV", "generation_system": [83]},
    {"id": 17, "combination": "Battery", "generation_system": [94]},
    {"id": 18, "combination": "CS", "generation_system": [94]},
    {"id": 19, "combination": "PV+Battery", "generation_system": [83, 94]},
    {"id": 20, "combination": "PV+CS", "generation_system": [83, 94]},
    {"id": 21, "combination": "Battery+CS", "generation_system": [94]},
    {"id": 22, "combination": "PV+Battery+CS", "generation_system": [83, 94]}
]

'''
COMBINATIONS_FOR_FRONT = [
    {"id": 1, "combination": "HP"},
    {"id": 2, "combination": "TS"},
    {"id": 3, "combination": "Wind"},
    {"id": 4, "combination": "HP+TS"},
    {"id": 5, "combination": "HP+Wind"},
    {"id": 6, "combination": "HP+PV"},
    {"id": 7, "combination": "TS+Wind"},
    {"id": 8, "combination": "TS+PV"},
    {"id": 9, "combination": "Wind+PV"},
    {"id": 10, "combination": "HP+TS+Wind"},
    {"id": 11, "combination": "HP+TS+PV"},
    {"id": 12, "combination": "HP+Wind+PV"},
    {"id": 13, "combination": "TS+Wind+PV"},
    {"id": 14, "combination": "HP+TS+Wind+PV"},
    {"id": 15, "combination": "DHN"}, #añadida nueva
    {"id": 16, "combination": "PV"},
    {"id": 17, "combination": "Battery"},
    {"id": 18, "combination": "CS"},
    {"id": 19, "combination": "PV+Battery"},
    {"id": 20, "combination": "PV+CS"},
    {"id": 21, "combination": "Battery+CS"},
    {"id": 22, "combination": "PV+Battery+CS"}

]

# -----------------------------------------------------------------------------
# This dictionary explains what technologies form each "combination" string.
# For example, "HP+PV" means the set ["HP", "PV"] must be available.
# -----------------------------------------------------------------------------
COMBINATION_TO_TECHS = {
    "HP": ["HP"], "TS": ["TS"], "Wind": ["Wind"], "HP+TS": ["HP", "TS"],
    "HP+Wind": ["HP", "Wind"], "HP+PV": ["HP", "PV"], "TS+Wind": ["TS", "Wind"],
    "TS+PV": ["TS", "PV"], "Wind+PV": ["Wind", "PV"], "HP+TS+Wind": ["HP", "TS", "Wind"],
    "HP+TS+PV": ["HP", "TS", "PV"], "HP+Wind+PV": ["HP", "Wind", "PV"],
    "TS+Wind+PV": ["TS", "Wind", "PV"], "HP+TS+Wind+PV": ["HP", "TS", "Wind", "PV"],
    "PV": ["PV"], "Battery": ["Battery"], "CS": ["CS"],
    "PV+Battery": ["PV", "Battery"], "PV+CS": ["PV", "CS"],
    "Battery+CS": ["Battery", "CS"], "PV+Battery+CS": ["PV", "Battery", "CS"],
    "DHN": ["DHN"] #añadida nueva
}

# -----------------------------------------------------------------------------
# We split combinations into two families:
#   • OEMOF_COMBINATIONS (handled by the OEMOF module) → ids 1..14
#   • SITEC_COMBINATIONS (handled by the SITEC module) → ids 15..21
# This tells the pipeline which engine should process a given combination.
# -----------------------------------------------------------------------------
OEMOF_COMBINATIONS = set(c["combination"] for c in COMBINATIONS_FOR_FRONT if c["id"] <= 15)
SITEC_COMBINATIONS = set(c["combination"] for c in COMBINATIONS_FOR_FRONT if c["id"] >= 16)

# -----------------------------------------------------------------------------
# Some parts of the system use detailed names (e.g., "solar_fleet").
# We translate those names to the short codes used in combinations: "PV", "TS", etc.
# -----------------------------------------------------------------------------
def combination_info():
    tech_translation = {
        "solar_fleet": "PV",
        "solar_thermal": "TS",
        "wind_fleet": "Wind",
        "heat_pump": "HP",
        "creation_of_dhn": "DHN", #añadida nueva
        "battery_storage": "Battery",
        "charging_station": "CS"
    }
    return tech_translation
# ============================== Public Functions =============================
# Each function below is meant to be easy to read:
#  - You give it the set/list of technologies you have.
#  - It returns the combinations that are truly possible with those techs.
#  - Or it tells you which module (OEMOF/SITEC) should be used.

def parse_selected_combo(selected_combo):
    """
    Accepts:
      - "HP+PV"
      - {"id": 6, "combination": "HP+PV", ...}
    Returns:
      - "HP+PV" (string)
    """
    if isinstance(selected_combo, dict):
        return selected_combo.get("combination", "")
    
    return selected_combo

def required_selected_actions(selected_combo,tech_translation, recs):
    if isinstance(selected_combo, dict):
        selected_combo_str = selected_combo.get("combination", "")
    else:
        selected_combo_str = selected_combo
    combo_techs = [t.strip() for t in selected_combo_str.split("+") if t.strip()]
    reverse_map = {v: k for k, v in tech_translation.items()}  # PV->"solar_fleet", etc.
    required_action_names = {reverse_map[t] for t in combo_techs if t in reverse_map}
    selected_actions = {
        str(v["id"]): v
        for v in recs.values()
        if isinstance(v, dict) and v.get("action_name") in required_action_names
    }
    return selected_actions

def get_valid_combinations_for_front(recommended_techs):
    """
    Input: a list like ["HP", "PV"] or ["PV", "Battery"].
    Output: all combinations from COMBINATIONS_FOR_FRONT that are feasible
            with those technologies (used for showing options to the user).
    """
    return [c for c in COMBINATIONS_FOR_FRONT
            if all(t in recommended_techs for t in COMBINATION_TO_TECHS[c["combination"]])]

def get_all_oemof_combinations(user_techs):
    """
    Input: a list like ["HP", "PV"].
    Output: the subset of combinations that (a) are OEMOF-handled and
            (b) can be built using only the technologies you have.
    """
    return [c for c in COMBINATIONS_FOR_FRONT
            if c["combination"] in OEMOF_COMBINATIONS and
            all(t in user_techs for t in COMBINATION_TO_TECHS[c["combination"]])]

def get_all_sitec_combinations(user_techs):
    """
    Same idea as the previous function, but for SITEC-handled combinations.
    """
    return [c for c in COMBINATIONS_FOR_FRONT
            if c["combination"] in SITEC_COMBINATIONS and
            all(t in user_techs for t in COMBINATION_TO_TECHS[c["combination"]])]

def get_module_from_combination(combo_name):
    """
    Quick helper:
      - If the combination belongs to the OEMOF family → return "OEMOF"
      - If it belongs to the SITEC family → return "SITEC"
      - Otherwise → return None (unknown combination)
    """
    if combo_name in OEMOF_COMBINATIONS:
        return "OEMOF"
    elif combo_name in SITEC_COMBINATIONS:
        return "SITEC"
    else:
        return None
def add_generation_system_to_front_combos(list_of_possible_combination):
    """
    Adds generation_system_id to each combination in list_of_possible_combination.
    
    Input:
        [{'id': 1, 'combination': 'HP'}, {'id': 4, 'combination': 'HP+TS'}]
    
    Output:
        [{'id': 1, 'combination': 'HP', 'generation_system_id': [63, 31, 2]}, ...]
    """

    TECH_TO_GENERATION_SYSTEM = {
        "PV": [83],
        "HP": [63, 31, 2],
        "TS": [71, 39],  # en tus combos es TS, no ST
        "DHN": [143, 151],
        "Caldera Biomasa": [22, 58],
        "Wind": [132],

        # tecnologías nuevas sin mapping todavía (para que no falle)
        "Battery": [94],
        "CS": [157]
    }

    updated_combos = []

    for combo_dict in list_of_possible_combination:
        combo_str = combo_dict.get("combination", "")
        techs = [t.strip() for t in combo_str.split("+") if t.strip()]

        generation_ids = []
        for tech in techs:
            generation_ids.extend(TECH_TO_GENERATION_SYSTEM.get(tech, []))

        # quitar duplicados manteniendo orden
        generation_ids = list(dict.fromkeys(generation_ids))

        # construir nuevo dict (evita modificar el original si no quieres side effects)
        new_combo_dict = combo_dict.copy()
        new_combo_dict["generation_system"] = generation_ids

        updated_combos.append(new_combo_dict)

    return updated_combos

# def demo_technology_combination_analysis(user_inputs):
#     """
#     Small demonstration utility for testing.
#     It does three things:
#       1) Gets recommended technologies from the RES-based generator.
#       2) Translates detailed names to the short codes used here (PV, TS, etc.).
#       3) Prints which combinations are valid for the front-end, OEMOF, and SITEC.

#     You can run this to understand how the routing works in practice.
#     """
#     print("=== Running Technology Combination Demo ===")
#     print("User inputs:", user_inputs)
#     tech_translation = combination_info()
#     # Ask the RES-based recommender which actions/technologies are suggested.
#     recommendations = res_based_generator_list_technologies(user_inputs)

#     # Extract the recommended actions and translate them to short codes like "PV", "HP", etc.
#     raw_techs = sorted({v["action_name"] for v in recommendations.values()})
#     user_techs = [tech_translation.get(t, t) for t in raw_techs]

#     print("\nTranslated recommended technologies:", user_techs)

#     # Show combinations that the front-end could present to the user.
#     valid_front = get_valid_combinations_for_front(user_techs)
#     print("\nValid combinations for front-end:")
#     for combo in valid_front:
#         print(f"  - {combo}")

#     # Show which OEMOF combinations are feasible with the available techs.
#     valid_oemof = get_all_oemof_combinations(user_techs)
#     print("\nCompatible OEMOF combinations:")
#     for combo in valid_oemof:
#         print(f"  - {combo}")

#     # Show which SITEC combinations are feasible with the available techs.
#     valid_sitec = get_all_sitec_combinations(user_techs)
#     print("\nCompatible SITEC combinations:")
#     for combo in valid_sitec:
#         print(f"  - {combo}")

#     # As an illustration, check a few example strings and say which module should run.
#     print("\nModule classification test:")
#     for combo in ["HP+PV", "PV+Battery", "TS", "PV+CS", "XYZ"]:
#         print(f"  - '{combo}' → {get_module_from_combination(combo)}")
