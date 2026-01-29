# -*- coding: utf-8 -*-
"""
ENPOWER - Full test pipeline (baseline + alternative)
Created by CARTIF

Overview
--------
This script generates:
1) A baseline context and baseline KPIs.
2) An alternative scenario output using the baseline context as input.

It is intended as a simple, reproducible example for developers to run local tests
after cloning the repository.

How to run
----------
python test_full_pipeline.py

Inputs
------
- data JSON:        api/services/scripts_enpower/data/data_database.json
- front_data JSON:  api/services/scripts_enpower/data/front_data.json

Output
------
A single JSON file saved under:
api/services/scripts_enpower/data/outputs_pruebas/

Notes
-----
- The code supports slight signature differences in the integration functions
  (some versions include generation_system_information, others do not).
"""

import os
import json
import inspect


from api.services.scripts_enpower.module_integration import (
    generate_baseline_pathway_intermediate,
    get_new_context,
    run_pipeline_from_context_json,
)


# =============================================================================
# Function: read_json
# -----------------------------------------------------------------------------
# Definition:
#   Reads a JSON file and returns its parsed content.
#
# Parameters:
#   path (str): JSON file path.
#
# Returns:
#   Any: Parsed JSON content.
# =============================================================================
def read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Function: write_json
# -----------------------------------------------------------------------------
# Definition:
#   Writes an object to a JSON file (pretty-printed).
#
# Parameters:
#   path (str): Output JSON file path.
#   obj (Any): Object to serialize.
#
# Returns:
#   None
# =============================================================================
def write_json(path: str, obj) -> None:
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# =============================================================================
# Function: call_generate_baseline
# -----------------------------------------------------------------------------
# Definition:
#   Calls generate_baseline_pathway_intermediate with the correct signature.
#   Some versions accept (data, front_data), others accept
#   (data, front_data, generation_system_information).
#
# Parameters:
#   data (Any): Data catalogue JSON content.
#   front_data (Any): Front input JSON content.
#   generation_system_information (dict|None): Optional extra info.
#
# Returns:
#   tuple:
#     baseline_context (Any): Baseline context/object.
#     baseline_kpis (Any): Baseline KPIs.
# =============================================================================
def call_generate_baseline(data, front_data, generation_system_information=None):
    sig = inspect.signature(generate_baseline_pathway_intermediate)
    if len(sig.parameters) >= 3:
        return generate_baseline_pathway_intermediate(
            data,
            front_data,
            generation_system_information or {},
        )
    return generate_baseline_pathway_intermediate(data, front_data)


# =============================================================================
# Function: call_run_pipeline
# -----------------------------------------------------------------------------
# Definition:
#   Calls run_pipeline_from_context_json with the correct signature.
#   Some versions accept (context, goal, selected_combo), others accept
#   (context, goal, selected_combo, generation_system_information).
#
# Parameters:
#   context (dict): Updated baseline context used as input for alternatives.
#   goal (dict): Goal definition.
#   selected_combo (dict|str): Selected technology combo.
#   generation_system_information (dict|None): Optional extra info.
#
# Returns:
#   Any: Alternative scenario output (context and KPIs, depending on implementation).
# =============================================================================
def call_run_pipeline(context, goal, selected_combo, generation_system_information=None):
    sig = inspect.signature(run_pipeline_from_context_json)
    if len(sig.parameters) >= 4:
        return run_pipeline_from_context_json(
            context,
            goal,
            selected_combo,
            generation_system_information or {},
        )
    return run_pipeline_from_context_json(context, goal, selected_combo)


# =============================================================================
# Function: run_test
# -----------------------------------------------------------------------------
# Definition:
#   Executes baseline generation, then runs an alternative scenario using the
#   baseline output as input. Saves one final JSON file.
#
# Parameters:
#   data_path (str): Path to data JSON.
#   front_data_path (str): Path to front_data JSON.
#   goal (dict): Goal definition.
#   selected_combo (dict): Selected technology combination.
#   output_path (str): Output JSON path.
#   generation_system_information_path (str|None): Optional path to extra info JSON.
#
# Returns:
#   None
# =============================================================================
def run_test(
    data_path: str,
    front_data_path: str,
    goal: dict,
    selected_combo: dict,
    output_path: str,
    generation_system_information_path: str = None,
) -> None:
    data = read_json(data_path)
    front_data = read_json(front_data_path)

    generation_system_information = {}
    if generation_system_information_path and os.path.exists(generation_system_information_path):
        generation_system_information = read_json(generation_system_information_path)

    baseline_context, baseline_kpis = call_generate_baseline(
        data,
        front_data,
        generation_system_information,
    )

    updated_context = get_new_context(baseline_context)

    alternative_output = call_run_pipeline(
        updated_context,
        goal,
        selected_combo,
        generation_system_information,
    )

    result = {
        "baseline_context": baseline_context,
        "baseline_kpis": baseline_kpis,
        "alternative_output": alternative_output,
        "goal": goal,
        "selected_combo": selected_combo,
    }

    write_json(output_path, result)
    print(output_path)


if __name__ == "__main__":
    cwd = os.getcwd()
    data_dir = os.path.join(cwd, "api", "services", "scripts_enpower", "data")

    data_path = os.path.join(data_dir, "data_database.json")
    front_data_path = os.path.join(data_dir, "front_data.json")

    goal = {"goals": "1", "country": "ES"}
    selected_combo = {"id": 1, "combination": "PV"}

    out_dir = os.path.join(data_dir, "outputs_pruebas")
    combo = selected_combo.get("combination", "NO_COMBO").replace(" ", "_").replace("+", "_")
    country = goal.get("country", "XX")
    output_path = os.path.join(out_dir, f"full_pipeline_{country}_{combo}.json")

    run_test(
        data_path=data_path,
        front_data_path=front_data_path,
        goal=goal,
        selected_combo=selected_combo,
        output_path=output_path,
        generation_system_information_path=None,
    )
