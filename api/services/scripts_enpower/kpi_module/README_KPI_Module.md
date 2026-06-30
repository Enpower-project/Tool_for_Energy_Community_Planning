# 📘 KPI Module — Internal Documentation

## 1. Purpose

The **KPI Module** computes all **Key Performance Indicators (KPIs)** related to energy performance, emissions, and costs for individual buildings and for energy communities.  
It takes raw simulation results (mainly consumption and generation time series) and converts them into standardized indicators — such as **primary energy**, **CO₂ emissions**, **self-consumption**, and several **user-friendly equivalents** (e.g., number of trees saved, pizza equivalents, etc.).

This module is designed to be used **after the energy simulation or optimization stage**, and it is called automatically in the post-processing phase of the EnPower platform (OEMOF-based).

---

## 2. General Workflow

The module’s logic is distributed across **three main Python scripts** plus two supporting **JSON catalogues**.

At a high level, the process works as follows:

1. **Input preparation**  
   The simulation or optimization provides time series for energy **consumption**, **generation**, and **asset metadata**.

2. **Data structuring and lookup**  
   The module loads **catalogues** for energy carriers and generation systems, to retrieve efficiencies, conversion factors, and emission coefficients.

3. **Computation of KPIs**  
   The core functions calculate building-level and community-level indicators, aggregating energy balances, primary energy equivalents, costs, and CO₂ emissions.

4. **Formatting for output**  
   Results are returned as structured dictionaries or ORM objects (`BuildingKPIs`, `CommunityEnergyAsset`) that can be stored in the database or exported.

---

## 3. File Overview

### `key_performance_indicators.py` — *Main KPI computation script*

This is the **central logic** of the module.  
It connects all other components and orchestrates the calculation of KPIs at building level.

**Main responsibilities:**
- Load and interpret **energy carrier** and **generation system** catalogues.  
- Build `FinalEnergy` instances for each energy carrier (electricity, gas, diesel, etc.).
- Compute primary energy use, renewable vs non-renewable shares.
- Calculate **CO₂ emissions**, **energy cost intensities**, and **user equivalences**.
- Manage self-consumption, self-sufficiency, and grid interaction.
- Handle fallback logic when catalogues lack specific data (e.g., missing country factors).

**Key functions:**
| Function | Description |
|-----------|-------------|
| `calculate_building_indicators()` | Core function for computing all building-level KPIs. It aggregates energy balances, costs, and emissions. |
| `instantiate_final_energy_with_json()` | Reads `energy_carrier.json` and creates a dictionary of `FinalEnergy` objects. |
| `load_energy_system_catalogue()` | Loads `generation_systems_catalogue.json` and makes it available for lookups. |
| `get_national_energy_carrier_production()` | Retrieves emission and PEF factors for a specific country and carrier. |
| `handle_demand_profile()` | Reconstructs missing demand profiles using generation system yields. |
| `calculate_self_consumption()`, `calculate_self_sufficiency()` | Compute PV-based self-consumption and grid dependency ratios. |
| `check_system_type_to_get_consumption()` | Maps consumption arrays to system type (heating, cooling, DHW). |

**Where to look in the code:**  
- The first ~150 lines define **constants** (KPI names, units, variable keys).  
- The next block (≈ lines 200–600) contains **helper functions** for internal calculations.  
- The lower section (≈ lines 600–1200) implements **building-level KPI aggregation**.

---

### `KPI_module.py` — *Equivalence and conversion factors*

This file defines **thematic conversion factors** and **helper functions** used to translate raw numeric KPIs into **human-readable equivalents**.

**Examples:**
- `tv_h`: Converts kWh into equivalent hours of TV watching.  
- `pizza_h`: Converts kWh into equivalent energy to cook pizzas.  
- `trees_number`: Estimates number of trees required to offset a given CO₂ amount.  
- `el_car_charges`: Equivalent number of EV charges for a given energy.

These are **not core KPIs**, but “impact translation” metrics used for user visualization and dashboards.

**Sections:**
- Top-level constants for energy conversion factors.
- Utility functions for scaling emissions/energy into equivalent units.
- `kpi_ctz_factors` defines the baseline constants for the whole module.

**Purpose:**  
Keep all equivalence definitions **centralized and consistent**, so other scripts (including GUI or report generation modules) can import the same factors.

---

### `energy_consumption.py` — *Low-level energy flow logic*

Handles all **consumption-related calculations** and preprocessing.  
It defines how energy demand and consumption are read, aligned, and summed across end uses (heating, cooling, DHW, electricity).

**Main responsibilities:**
- Combine raw time series from consumption and generation.  
- Fill missing data and ensure all systems have aligned 8760-hour profiles.  
- Aggregate energy use per carrier and per system.

This script is usually imported by higher-level modules (e.g., building or community models).  
It is **not called directly** but serves as a helper for KPI computation and scenario evaluation.

---

## 4. Supporting JSON Catalogues

### `energy_carrier.json`
Defines the **energy carriers** (e.g., electricity, gas, diesel) and their associated parameters for each country.

Each entry includes:
- Primary energy factors (`pef_tot`, `pef_nren`, `pef_ren`)
- CO₂ equivalent emissions (`f_co2_eq_g_kwh`)
- Energy costs for household and non-household users
- Country references and data sources

Used by:
- `get_national_energy_carrier_production()`
- `instantiate_final_energy_with_json()`

Typical location:  
`/catalogues/energy_carrier.json`

---

### `generation_systems_catalogue.json`
Describes each **generation technology** (e.g., PV, HP, boiler, CHP) with:
- Efficiency and yield parameters
- Energy carrier inputs/outputs
- Identification codes for cross-referencing assets

Used by:
- `load_energy_system_catalogue()`
- To determine the system’s behavior and link to energy carriers.

Typical location:  
`/scenario_generator/catalogues/generation_systems_catalogue.json`

---

## 5. Data Flow Summary

```
Energy simulation results (OEMOF / MILP)
          │
          ▼
 Consumption & generation profiles  →  energy_consumption.py
          │
          ▼
     KPI computation core  →  key_performance_indicators.py
          │
          ▼
     Conversion & equivalence  →  KPI_module.py
          │
          ▼
     KPI objects / DB export  →  BuildingKPIs, CommunityEnergyAsset
```

---

## 6. Integration with the Rest of the Platform

The KPI module connects primarily to the **database layer** and the **OEMOF modeling results**.  
It expects as inputs:
- Building or community asset metadata (from the database).
- Time series of consumption and generation.
- Country code (for selecting national energy factors).

Outputs:
- A dictionary or ORM object containing all computed KPIs.
- Can be stored in PostgreSQL or used for dashboard visualization.

---

## 7. Coding Conventions and Best Practices

- Each function returns **standard Python objects** (dicts or lists). Avoid modifying global variables.
- Constants are defined at the top of `key_performance_indicators.py` to ensure consistency across KPIs.
- Time series are assumed to be **hourly (8760 values)**; check alignment before computing.
- The module uses **fallback logic** for missing country data (defaults to EU average, `country_id = 31`).
- All units are **SI-compliant** (`kWh`, `gCO₂eq`, `€/m²`).

---

## 8. How to Extend the Module

When adding new KPIs or equivalences:
1. Define new constants in `key_performance_indicators.py`.
2. If it’s a new equivalence (e.g., “cups of coffee”), add the formula in `KPI_module.py`.
3. Add logic to compute it inside `calculate_building_indicators()`.
4. Test using a known dataset and verify consistency with existing KPIs.
5. Update the JSON catalogues if the KPI depends on new energy carriers or countries.

---

## 9. Quick Navigation Guide

| File | Role | Main Functions / Sections |
|------|------|----------------------------|
| `key_performance_indicators.py` | Core logic and orchestration | `calculate_building_indicators()`, `instantiate_final_energy_with_json()` |
| `KPI_module.py` | User-equivalent conversions | `tv_h`, `trees_number`, `pizza_h`, etc. |
| `energy_consumption.py` | Data preprocessing | Functions for combining and aligning consumption profiles |
| `energy_carrier.json` | National energy factors | Used by all energy-related KPIs |
| `generation_systems_catalogue.json` | System efficiencies | Used to match building assets with generation types |

---
