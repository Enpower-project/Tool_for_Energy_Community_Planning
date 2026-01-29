# =============================================================================
# helpers.py
# =============================================================================
# What this file does (plain English)
# -----------------------------------
# This module provides practical utility functions used across the
# Energy Optimization Framework. It supports:
#   • Building initialization (reading context and preparing data objects)
#   • Time and weather utilities (creating datetime and EPW structures)
#   • Processing optimization results (flows, Sankey diagrams)
#   • Geometry tools (building areas)
#   • Economic helpers (extracting prices from context)
#
# Most of these tools are called automatically by higher-level scripts
# such as `run_oemof_simulation.py` or `calculate_kpis_from_context.py`.
# =============================================================================

import os
import json
import random
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely import wkt
import matplotlib.pyplot as plt
from matplotlib.sankey import Sankey
import plotly.graph_objects as go
import plotly.offline as pyo
from typing import Union, Dict, Any, Optional

from api.services.scripts_enpower.OEMOF_module.classes_database import BuildingData, BuildingConsumption, BuildingDemand
import api.services.scripts_enpower.helpers.constants as cte
from oemof.solph import components, views

# =============================================================================
# Building initialization
# =============================================================================
def initialise(context_dict):
    """
    Creates BuildingData objects from the context dictionary.
    Each BuildingData stores info about:
      - Building metadata (area, ID, geometry)
      - Energy consumption and demand
      - Associated energy assets
    """
    print("🔄 Running 'initialise' function...")
    buildings = {}

    for building_context in context_dict.get("building_asset_context", []):
        building_id = building_context.get("building", {}).get("id")
        if not building_id:
            continue

        try:
            # Create a building object and attach its basic data
            building = BuildingData(id=building_id)
            building.associate_building_data(building_context.get("building"))
            building.associate_building_consumption(building_context.get("building_consumption"))

            # Reconstruct heating and DHW systems for demand estimation
            temp_gen_profile = {}
            for asset in building_context.get("building_energy_asset", []):
                if not asset.get("is_investment_option") and "Boiler" in asset.get("name", ""):
                    if "Heating" in asset["name"]:
                        temp_gen_profile["heating_system"] = asset["generation_system"]
                    elif "DHW" in asset["name"]:
                        temp_gen_profile["dhw_system"] = asset["generation_system"]

            building.associate_building_demand(temp_gen_profile)
            building.associate_building_energy_asset(building_context.get("building_energy_asset", []))
            buildings[building_id] = building

        except Exception as e:
            print(f"❌ Error initializing building {building_id}: {e}")

    print(f"✅ Initialization complete. {len(buildings)} buildings loaded.")
    return buildings

# =============================================================================
# Time and Weather Helpers
# =============================================================================
def create_datetime_vector(year: int) -> pd.DatetimeIndex:
    """Creates an hourly datetime index for a full year."""
    return pd.date_range(start=f'{year}-01-01 00:00:00', end=f'{year}-12-31 23:00:00', freq='h')

def extract_day_hour(datetime_vector: pd.DatetimeIndex):
    """Returns two arrays: day of year and hour of day for each timestamp."""
    return datetime_vector.dayofyear, datetime_vector.hour

def create_epw_dataframe(datetime_vector, epw_data):
    """
    Converts EPW weather data (Dry Bulb Temperature, Radiation) into a DataFrame.
    Each row represents one hour of the year.
    """
    days_of_year, hours = extract_day_hour(datetime_vector)
    epw = pd.DataFrame({
        'datetime': datetime_vector,
        'day_of_year': days_of_year,
        'hour': hours,
        'T': epw_data['Dry Bulb Temperature'],
        'Ig': epw_data['Global Horizontal Radiation'],
        'Id': epw_data['Diffuse Horizontal Radiation']
    }).set_index('datetime')
    return epw

# =============================================================================
# Optimization results and Sankey diagram
# =============================================================================
def normalize_profile(profile):
    """Normalizes a list of values to a range between 0 and 1."""
    if not profile:
        return profile
    max_value = max(profile)
    return [x / max_value if max_value != 0 else 0 for x in profile]

def save_optimized_results_to_dataframe_v2(model, results):
    """
    Collects all flow results from the optimization and merges them into one DataFrame.
    Each row shows source, target, datetime, and flow value.
    """
    
    print("🔄 Running 'save_optimized_results_to_dataframe_v2'...")

    all_flows = []
    for (src, tgt), data in results.items():
        if 'sequences' in data and isinstance(data['sequences'], pd.DataFrame):
            df = data['sequences'].copy()
            if 'flow' not in df.columns:
                continue
            df['source'] = src.label
            df['target'] = tgt.label
            df.index.name = 'datetime'
            all_flows.append(df.reset_index())

    if not all_flows:
        print("❌ No valid flows found in results.")
        return pd.DataFrame(columns=['datetime', 'source', 'target', 'flow'])

    final_df = pd.concat(all_flows, ignore_index=True)
    return final_df[['datetime', 'source', 'target', 'flow']]

def generate_sankey(results_df, label_path="_sankey", label_title="Energy Flow", filter_intermediate=False):
    """
    Creates an HTML Sankey diagram showing energy flows (PV, HP, Grid, etc.).
    Each line width is proportional to the total energy flow between two nodes.
    """
    print(f"\n🎨 Generating Sankey diagram (filter_intermediate={filter_intermediate})...")

    df = results_df.groupby(['source', 'target'])['flow'].sum().reset_index()
    df = df[df['flow'] > 1]

    if df.empty:
        print("⚠️ No flow data available.")
        return

    # Optional: remove intermediate buses for cleaner visualization
    if filter_intermediate:
        intermediates = ["GridToCom_", "Distribucion_Elec_", "Distribucion_Gas_", "GasToCom_"]

        def is_intermediate(label): return any(label.startswith(p) for p in intermediates)
        def final_target(df, node):
            while True:
                row = df[df["source"] == node]
                if row.empty: return node
                next_node = row.iloc[0]["target"]
                if not is_intermediate(next_node): return next_node
                node = next_node

        direct_links = []
        seen = set()

        for _, row in df.iterrows():
            src, tgt, val = row["source"], row["target"], row["flow"]
            if is_intermediate(src) or is_intermediate(tgt): continue
            final = final_target(df, tgt)
            if (src, final) not in seen:
                direct_links.append({"source": src, "target": final, "flow": val})
                seen.add((src, final))
        df = pd.DataFrame(direct_links)

    # Label setup
    all_labels = pd.unique(df[['source', 'target']].values.ravel())
    label_idx = {label: i for i, label in enumerate(all_labels)}
    src_idx = [label_idx[s] for s in df['source']]
    tgt_idx = [label_idx[t] for t in df['target']]
    values = df['flow']

    # Basic color mapping for technologies
    def classify(label):
        l = label.lower()
        if "pv" in l: return "pv"
        if "solar_thermal" in l or "stc" in l: return "stc"
        if "wind" in l: return "wind"
        if "hp" in l: return "hp"
        if "boiler" in l: return "boiler"
        if "grid" in l and "gas" not in l: return "grid_elec"
        if "gas" in l and "grid" in l: return "grid_gas"
        if "electric" in l: return "electric"
        if "heating" in l: return "thermal"
        if "dhw" in l: return "dhw"
        if "cool" in l: return "cool"
        if "excess" in l: return "excess"
        return "other"

    color_map = {
        "pv": "#FFD700",         # yellow
        "stc": "#FFA500",        # orange
        "wind": "#87CEEB",       # sky blue
        "hp": "#00CED1",         # cyan
        "boiler": "#B22222",     # firebrick
        "grid_elec": "#708090",  # slate gray
        "grid_gas": "#A0522D",   # sienna
        "electric": "#1E90FF",   # dodger blue
        "thermal": "#FF4500",    # orange red
        "dhw": "#FF69B4",        # hot pink
        "cool": "#00BFFF",       # deep sky blue
        "excess": "#999999",     # grey
        "other": "#D3D3D3"       # light grey
    }

    node_colors = [color_map.get(classify(lbl), "#D3D3D3") for lbl in all_labels]

    # Build and export Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=25, thickness=20, line=dict(color="black", width=0.5),
            label=all_labels, color=node_colors
        ),
        link=dict(source=src_idx, target=tgt_idx, value=values)
    )])
    fig.update_layout(title_text=label_title, font_size=12, height=800)
    filename = os.path.join("data", f"sankey_diagram{label_path}.html")
    fig.write_html(filename)
    print(f"✅ Sankey diagram saved: {filename}")


# =============================================================================
# Geometry tools
# =============================================================================
def calculate_building_areas(buildings, projected_crs="EPSG:3857"):
    """
    Computes the rooftop area (in m²) for each building geometry.
    Used to estimate possible capacity for PV or STC.
    """
    areas = {}
    for bid, building in buildings.items():
        if building.geometry:
            try:
                geom = wkt.loads(building.geometry)
                gdf = gpd.GeoDataFrame({"geometry": [geom]}, crs="EPSG:4326")
                gdf_proj = gdf.to_crs(projected_crs)
                area = gdf_proj.geometry.area.iloc[0]
                areas[bid] = area
                print(f"Building {bid}: Area = {area:.2f} m²")
            except Exception as e:
                print(f"⚠️ Error calculating area for building {bid}: {e}")
    return areas

# =============================================================================
# Price extraction helper
# =============================================================================
def get_scalar_prices_from_context(ctx,country_id):
    """
    Finds average import prices for electricity and gas from the context structure.
    These are usually stored in 'national_energy_carrier_production' entries.
    Returns: {'elec_eur_per_kwh': ..., 'gas_eur_per_kwh': ...}
    """

    def pick_price(nlist, key) -> Optional[float]:
        if not isinstance(nlist, list):
            return None
        if country_id is not None:
            for r in nlist:
                if r.get("country_id") == country_id and r.get(key) is not None:
                    return float(r[key])
        for r in nlist:
            if r.get(key) is not None:
                return float(r[key])
        return None

    elec = None
    gas  = None

    buildings = (ctx or {}).get("building_asset_context", [])
    for b in buildings:
        gsp = (b or {}).get("generation_system_profile") or {}

        # Electricity import price
        elec_in = ((gsp.get("electricity_system") or {}).get("energy_carrier_input_1") or {})
        elec_nat = elec_in.get("national_energy_carrier_production") or []
        if elec is None:
            elec = pick_price(elec_nat, "house_costs_eur_kwh")

        # Gas import price (try DHW first, then Heating)
        dhw_in = ((gsp.get("dhw_system") or {}).get("energy_carrier_input_1") or {})
        dhw_nat = dhw_in.get("national_energy_carrier_production") or []
        if gas is None:
            gas = pick_price(dhw_nat, "house_costs_eur_kwh")

        if gas is None:
            heat_in = ((gsp.get("heating_system") or {}).get("energy_carrier_input_1") or {})
            heat_nat = heat_in.get("national_energy_carrier_production") or []
            gas = pick_price(heat_nat, "house_costs_eur_kwh")

        if elec is not None and gas is not None:
            break

    return {
        "elec_eur_per_kwh": float(elec or 0.0),
        "gas_eur_per_kwh": float(gas or 0.0),
    }
