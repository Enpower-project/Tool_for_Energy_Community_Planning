# 📂 scenario_generator/

This folder contains the logic for **generating energy system contexts** and **technology recommendations** based on user preferences and country-specific data. It integrates demand profile generation, building asset structuring, and renewable energy system (RES) suggestions to support simulation modules (OEMOF or SITEC).

---

## 📄 RESbased_scenario_generator.py

Main entry point for generating recommended technologies based on:
- Country selection
- User goals (e.g. self-sufficiency, electrification, etc.)

### Key Function:
- **res_based_generator_list_technologies(inputs_users)**  
  Returns a ranked dictionary of recommended actions (e.g. `solar_fleet`, `heat_pump`) based on a multicriteria decision-making logic that merges:
  - Goal relevance
  - Country suitability (from `country_scenarios_recommended.json`)

Supports user profiles from the front-end like:

```json
{"goals": "3", "country": "AT"}
```

Also includes helper functions for scoring, filtering, and matching IDs from CSV/json lookup tables.

---

## 📄 country_RES_library.py

Defines the `Country` class and functions to:
- Load country-level RES-related data and scenarios
- Retrieve properties used for technology suitability assessment

### Key Function:
- **country_res_recommendations(country_code)**  
  Loads boolean flags like `HighDHN`, `Allow_gas`, `SmartHeating`, etc., used in the recommendation engine.

---

## 📄 context_creation.py

Contains asset-generation logic and PVGIS data integration.

### Key Functional Areas:
- **Geometry & Centroid**:  
  `get_centroid(...)`: Calculates the centroid of a set of buildings.

- **PVGIS-based Profiles**:  
  `call_PVGIS(...)`: Fetches PV, wind, and STC hourly profiles.

- **Unified Asset Generation**:  
  `create_unified_building_assets(...)`  
  `create_unified_community_assets(...)`  
  These functions translate recommended actions (e.g., HP, STC, PV) into structured building and community energy assets.

---

## 📄 get_new_context.py

Main script to generate a new energy context (ready for simulation) based on:
- An initial community context
- User goals and recommended actions

### Key Function:
- **resbased_generator_context_creation(goal, community_context, recommendations_dic)**  
  - Calls `call_PVGIS`, generates profiles  
  - Builds assets with investment options  
  - Assigns metadata (name, timestamp)  
  - Returns an updated simulation-ready context

---

## 📄 context_creation.py (continued)

Also includes demand assignment logic for different user profiles and detailed building-level baseline generation.

### Key Functions:
- **baseline_pathway_simple(...)**  
  Builds a simplified context with uniform buildings and default profiles.

- **baseline_pathway_intermediate(...)**  
  Uses actual building geometry, occupants, and Thermagrid-compatible data for detailed asset context generation.

- **generate_demand_inputs(...)**, **demand_thermagrid(...)**  
  Interface with PVGIS and Thermagrid logic to enrich the context with temperature, irradiance, and realistic demand profiles.

---

## 📄 function_documentation.md

Optional Markdown file documenting key utility functions:
- Self-consumption and self-sufficiency calculations
- KPI processing
- Electricity profile aggregation
- Final energy instantiation

Useful as a developer reference for the KPI and demand logic used across modules.

---

## How It All Connects

```mermaid
graph TD
    A[User Inputs (Country, Goal)] --> B(res_based_generator_list_technologies)
    B --> C{Actions (IDs, Names)}
    C --> D[get_new_context.py]
    D --> E[call_PVGIS & Profiles]
    D --> F[create_unified_building_assets]
    D --> G[create_unified_community_assets]
    F & G --> H[New OEMOF/SITEC Context]
```

---

## Typical Use Flow

```python
from scenario_generator.RESbased_scenario_generator import res_based_generator_list_technologies
from scenario_generator.get_new_context import resbased_generator_context_creation

# Step 1: Get technology recommendations
actions = res_based_generator_list_technologies({
    "goals": "3", "country": "DE"
})

# Step 2: Create context with those actions
new_context = resbased_generator_context_creation("self_sufficiency", base_context, actions)
```

---

## Output

A fully structured `context` dictionary containing:
- Standardized building energy assets
- Demand profiles
- Community-level RES assets
- Time series and metadata ready for simulation

---

## Dependencies

- `pandas`, `geopandas`, `pvlib`, `pyproj`, `shapely`
- Internal folders: `RESlibrary/`, `Electricity_profiles/`

---