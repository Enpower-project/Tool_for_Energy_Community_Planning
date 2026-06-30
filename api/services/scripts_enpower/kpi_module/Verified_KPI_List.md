# ✅ Verified KPI List and Calculation Summary (Internal Reference)

This document lists **only the KPIs actually implemented in the current KPI module codebase**.  
All entries were verified directly in the uploaded Python files — no assumptions or inferred items are included.

---

## ⚙️ 1. Energy KPIs (Implemented)

| KPI | Variable / Constant | Description | Calculation Logic | Source |
|------|----------------------|--------------|------------------|--------|
| **Peak Heat Demand [kWh]** | `KPI_PEAK_HEAT_DEMAND_VALUE` | Maximum hourly heating demand per building. | `max(demand_profile[HEATING_DEMAND])` | `key_performance_indicators.py` |
| **Peak Electric Demand [kWh]** | `KPI_PEAK_ELEC_DEMAND_VALUE` | Maximum hourly electricity demand. | `max(total_electricity_use[building_id])` | `key_performance_indicators.py` |
| **Total Primary Energy [kWh]** | `TOTAL_PRIMARY_ENERGY_VALUE` | Total primary energy consumption (sum of all carriers). | Sum of `energy_instance.PEF_total` across energy carriers. | `key_performance_indicators.py` |
| **Renewable Primary Energy [kWh]** | *(internal variable)* | Renewable portion of total primary energy. | Sum of `energy_instance.PEF_ren` for each carrier. | `key_performance_indicators.py` |
| **Non-Renewable Primary Energy [kWh]** | *(internal variable)* | Non-renewable portion of total primary energy. | Sum of `energy_instance.PEF_nren` for each carrier. | `key_performance_indicators.py` |
| **CO₂ Emissions [kg]** | *(derived)* | Total CO₂ emissions for all carriers. | Sum of `energy_instance.co2 / 1000` for each carrier. | `key_performance_indicators.py` |
| **Household Energy Costs [€]** | *(derived)* | Energy costs for household consumers. | Sum of `energy_instance.household_costs`. | `key_performance_indicators.py` |
| **Non-Household Energy Costs [€]** | *(derived)* | Energy costs for non-household consumers. | Sum of `energy_instance.non_h_costs`. | `key_performance_indicators.py` |
| **Self-Consumption [kWh]** | `KPI_self_consumption()` | PV energy used directly onsite. | `sum(min(pv_profile, load_profile))` | `KPI_module.py` |
| **Self-Sufficiency [%]** | `KPI_self_sufficiency()` | Share of total load covered by PV. | `(sum(min(pv_profile, load_profile)) / total_load)` | `KPI_module.py` |

---

## 🌱 2. Environmental KPIs (Implemented)

| KPI | Variable / Constant | Description | Calculation Logic | Source |
|------|----------------------|--------------|------------------|--------|
| **Total CO₂ Emissions [kg]** | *(implicit)* | Total annual emissions for the building. | Computed directly from energy carrier CO₂ factors. | `key_performance_indicators.py` |
| **Trees Required for CO₂ Offset [trees]** | `"Trees_number"` | Equivalent number of trees needed to offset total CO₂ emissions. | `trees_number(citizen_kpis_factors, total_co2)` | `key_performance_indicators.py` → `KPI_module.py` |
| **Streaming Emission Hours [h]** | `"streaming_emissionhours"` | Equivalent streaming time that would emit the same CO₂. | `streaming_emission_hours(citizen_kpis_factors, total_co2)` | `key_performance_indicators.py` → `KPI_module.py` |
| **ICV Kilometers Equivalent [km]** | `"ICV_km"` | Equivalent distance driven by internal combustion car for same CO₂. | `icv_km(citizen_kpis_factors, total_co2)` | `key_performance_indicators.py` → `KPI_module.py` |

---

## 👥 3. User-Equivalent / Communication KPIs (Implemented)

| KPI | Variable / Constant | Description | Calculation Logic | Source |
|------|----------------------|--------------|------------------|--------|
| **Equivalent TV Hours [h]** | `EQUIVALENT_TV_HOURS_VALUE` (`"TV_h"`) | Energy translated to TV watching hours. | `tv_h(citizen_kpis_factors, total_primary_energy)` | `key_performance_indicators.py` |
| **Equivalent Streaming Hours [h]** | `EQUIVALENT_STREAMING_HOURS_VALUE` (`"streaming_hours"`) | Energy translated to online streaming time. | `streaming_h(citizen_kpis_factors, total_primary_energy)` | `key_performance_indicators.py` |
| **Pizza Consumption Equivalent [pizza]** | `PIZZA_CONSUMPTION_COMPARISON_VALUE` (`"Pizza_h"`) | Energy equivalent to number of pizzas baked. | `pizza_h(citizen_kpis_factors, total_primary_energy)` | `key_performance_indicators.py` |
| **Battery Usage (Phone Charges)** | `BATTERY_USAGE_ESTIMATION_VALUE` (`"Battery_charges"`) | Equivalent number of smartphone charges. | `battery_charges(citizen_kpis_factors, total_primary_energy)` | `key_performance_indicators.py` |
| **Electric Car Charging Equivalent [charges]** | `ELECTRIC_CAR_CHARGING_ESTIMATION_VALUE` (`"ElCar_charges"`) | Number of EV full charges equivalent to total energy. | `el_car_charges(citizen_kpis_factors, total_primary_energy)` | `key_performance_indicators.py` |
| **Wine Bottles Equivalent [bottles]** | `"Wine_bottles"` | Number of wine bottles that could be produced with same energy. | `wine_bottles(citizen_kpis_factors, total_primary_energy)` | `key_performance_indicators.py` |

---

## ✅ Summary

The module currently implements **three groups of KPIs**:

1. **Energy performance KPIs:** primary energy, CO₂, self-consumption, self-sufficiency, peaks.  
2. **Environmental KPIs:** emissions-based equivalents (trees, cars, streaming).  
3. **User-equivalence KPIs:** awareness metrics for communication and dashboards.

All verified against function calls and variable assignments in:  
- `key_performance_indicators.py`  
- `KPI_module.py`  
- Supporting JSON catalogues (`energy_carrier.json`, `generation_systems_catalogue.json`)

---
