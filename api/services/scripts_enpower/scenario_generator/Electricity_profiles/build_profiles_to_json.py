"""
build_profiles_to_json.py

Generate one electric profile per dwelling from a JSON input (order preserved)
and write the result as a JSON *list of objects*, one object per dwelling:

Output format (order preserved):
[
  {"electric_profile1": [..T hourly..]},
  {"electric_profile2": [..]},
  ...
]

Usage
-----
generate_profiles_numbered(json_path, chr_dir)
"""

import json
import sys
from typing import List, Dict
import numpy as np
from final_electric_profiles import load_chr_profiles, generate_profile


def generate_profiles_numbered(json_path: str, chr_dir: str, year: int = 2025) -> List[Dict[str, List[float]]]:
    """
    Create one hourly profile per dwelling, preserving input order, and return:
    [
      {"electric_profile1": [...]},
      {"electric_profile2": [...]},
      ...
    ]
    """
    # 1) Load input dwellings (root must be a list)
    with open(json_path, "r", encoding="utf-8") as f:
        dwellings = json.load(f)
    if not isinstance(dwellings, list):
        raise ValueError("JSON root must be a list of dwellings.")

    # 2) Load CHR profiles once
    chr_profiles = load_chr_profiles(chr_dir)

    # 3) Generate profiles in the same order; number keys starting at 1
    out: List[Dict[str, List[float]]] = []
    for i, rec in enumerate(dwellings, start=1):
        prof_np: np.ndarray = generate_profile(rec, chr_profiles, year=year)
        out.append({f"electric_profile{i}": prof_np.astype(float).tolist()})
    return out


# Generate profiles and write to JSON:

json_path = "scenario_generator/Electricity_profiles/front_data_fornes.json" # path to input JSON
chr_dir = "scenario_generator/Electricity_profiles/Updated_profiles" # path to CHR*.csv files
out_path = "scenario_generator/Electricity_profiles/Fornes_profiles.json" # path to JSON output

profiles = generate_profiles_numbered(json_path, chr_dir) # generate profiles function
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(profiles, f, indent=2)
