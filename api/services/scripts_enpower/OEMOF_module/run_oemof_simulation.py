# =============================================================================
# run_oemof_simulation.py
# =============================================================================
import os
import json
import numpy as np
import pandas as pd

from oemof.solph import EnergySystem, buses, components, flows, Model, Investment
from oemof.solph.components import Converter, GenericStorage
from oemof.tools import economics

from api.services.scripts_enpower.helpers.helpers import (
    save_optimized_results_to_dataframe_v2,
    generate_sankey,
    normalize_profile,
    initialise,
    create_datetime_vector,
    get_scalar_prices_from_context
)

from api.services.scripts_enpower.OEMOF_module.OEMOF_to_new_Context import populate_results_in_context
from api.services.scripts_enpower.helpers.custom_constraints import add_joint_capacity_constraint, get_minimum_cap

from typing import Union, Dict, Any, Optional, List


def add_thermal_storage_for_dhw(energysystem, dhw_bus, building_id, storage_kwh: float = 100.0):
    energysystem.add(components.GenericStorage(
        label=f"thermal_storage_dhw_{building_id}",
        nominal_storage_capacity=storage_kwh,
        inputs={dhw_bus: flows.Flow()},
        outputs={dhw_bus: flows.Flow()},
        loss_rate=0.00005,
        initial_storage_level=0.2,
        max_storage_level=1.0,
        inflow_conversion_factor=0.95,
        outflow_conversion_factor=0.95,
    ))


def add_thermal_storage_for_building(energysystem, heat_bus, building_id, storage_kwh: float = 200.0):
    energysystem.add(components.GenericStorage(
        label=f"thermal_storage_heating_{building_id}",
        nominal_storage_capacity=storage_kwh,
        inputs={heat_bus: flows.Flow()},
        outputs={heat_bus: flows.Flow()},
        loss_rate=0.00005,
        initial_storage_level=0.2,
        max_storage_level=1.0,
        inflow_conversion_factor=0.95,
        outflow_conversion_factor=0.95,
    ))


def run_oemof_simulation(context):
    year = 2023
    solver = "cbc"
    include_existing_assets = False
    country_id = None

    print("[1] Loading context and preparing inputs...")
    context: Union[str, Dict[str, Any]]

    if isinstance(context, dict):
        raw_context = context
    else:
        with open(context, "r") as f:
            raw_context = json.load(f)

    buildings_data = initialise(raw_context)

    prices = get_scalar_prices_from_context(raw_context, country_id=country_id)
    electricity_price = float(prices["elec_eur_per_kwh"]) * 1000
    gas_price = float(prices["gas_eur_per_kwh"]) * 10000

    datetime_vector = create_datetime_vector(year)
    energysystem = EnergySystem(timeindex=pd.DatetimeIndex(datetime_vector), infer_last_interval=True)

    print("[2] Creating buses...")

    bus_elec_com = buses.Bus(label="Electricity_Community_Bus")
    bus_gas_com = buses.Bus(label="Gas_Community_Bus")
    bus_bio_com = buses.Bus(label="Biomasa_Community_Bus")
    energysystem.add(bus_elec_com, bus_gas_com, bus_bio_com)

    buses_heat, buses_dhw, buses_cool = {}, {}, {}
    for bid in buildings_data:
        buses_heat[bid] = buses.Bus(label=f"Heating_Local_{bid}")
        buses_dhw[bid] = buses.Bus(label=f"DHW_Local_{bid}")
        buses_cool[bid] = buses.Bus(label=f"Cooling_Local_{bid}")
        energysystem.add(buses_heat[bid], buses_dhw[bid], buses_cool[bid])

    print("[3] Adding grid sources, sinks, and demand profiles...")

    max_export_kW = 115
    energysystem.add(components.Sink(
        label="Excess_Elec_Community",
        inputs={bus_elec_com: flows.Flow(nominal_value=max_export_kW, variable_costs=-0.04)}
    ))

    for bid, b_data in buildings_data.items():
        energysystem.add(components.Source(
            label=f"Electricity_Grid_Source_{bid}",
            outputs={bus_elec_com: flows.Flow(variable_costs=electricity_price)}
        ))
        energysystem.add(components.Source(
            label=f"Gas_Grid_Source_{bid}",
            outputs={bus_gas_com: flows.Flow(variable_costs=gas_price)}
        ))

        if not include_existing_assets:
            energysystem.add(Converter(
                label=f"Gas_to_Heating_{bid}",
                inputs={bus_gas_com: flows.Flow(nominal_value=500)},
                outputs={buses_heat[bid]: flows.Flow()},
                conversion_factors={buses_heat[bid]: 1.0}
            ))
            energysystem.add(Converter(
                label=f"Gas_to_DHW_{bid}",
                inputs={bus_gas_com: flows.Flow(nominal_value=500)},
                outputs={buses_dhw[bid]: flows.Flow()},
                conversion_factors={buses_dhw[bid]: 1.0}
            ))
            print(f"   → Added gas backup via community bus for building {bid}")

        demands = {
            "electricity_demand": bus_elec_com,
            "heating_demand": buses_heat[bid],
            "dhw_demand": buses_dhw[bid],
            "cooling_demand": buses_cool[bid]
        }

        for key, bus in demands.items():
            demand = b_data.building_demand.get(key)
            if demand:
                demand_array = np.array(demand)
                d_max = np.max(demand_array)
                energysystem.add(components.Sink(
                    label=f"{key}_{bid}",
                    inputs={bus: flows.Flow(fix=normalize_profile(demand), nominal_value=d_max)}
                ))

        spill_cost_heat = 1e6
        spill_cost_dhw = 1e6
        spill_cost_cool = 1e6

        energysystem.add(components.Sink(
            label=f"Excess_Heat_{bid}",
            inputs={buses_heat[bid]: flows.Flow(variable_costs=spill_cost_heat)}
        ))
        energysystem.add(components.Sink(
            label=f"Excess_DHW_{bid}",
            inputs={buses_dhw[bid]: flows.Flow(variable_costs=spill_cost_dhw)}
        ))
        energysystem.add(components.Sink(
            label=f"Excess_Cool_{bid}",
            inputs={buses_cool[bid]: flows.Flow(variable_costs=spill_cost_cool)}
        ))

    # ------------------------------------------------------------------
    # Helpers (robust parsing of asset fields)
    # ------------------------------------------------------------------
    def _pick_profile(a: Dict[str, Any]) -> List[float]:
        ts = a.get("availability_ts") or {}
        prof = ts.get("value_input1")
        if prof is None:
            prof = ts.get("value_output1")
        if prof is None:
            prof = a.get("profile")
        return prof if isinstance(prof, list) else [0.0] * 8760

    def _pick_pmax(a: Dict[str, Any]) -> float:
        p = a.get("pmaxmax_scalar", None)
        if p is None:
            p = a.get("pmax_scalar", None)
        try:
            return float(p) if p is not None else 0.0
        except Exception:
            return 0.0

    # ------------------------------------------------------------------
    # Add community-level assets (wind, etc.)  ✅ aquí es donde debe entrar el wind 132
    # ------------------------------------------------------------------
    # for asset in raw_context.get("community_energy_asset", []) or []:
    #     if not asset:
    #         continue
    #     if not asset.get("is_investment_option"):
    #         continue

    #     g_id = (asset.get("generation_system") or {}).get("id")
    #     capex_kw = (asset.get("generation_system") or {}).get("capex_eur_kw", 2850)
    #     lifetime = (asset.get("generation_system") or {}).get("lifetime_years", 20)
    #     epc = economics.annuity(capex_kw, lifetime, 0.05)

    #     pmax = _pick_pmax(asset)
    #     profile = _pick_profile(asset)

    #     if pmax <= 0:
    #         print(f"   - INFO: Skipped community asset {asset.get('name')} (g_id={g_id}) because pmax is {pmax}")
    #         continue

    #     print(f"   → Community asset: {asset.get('name')} | g_id={g_id} | pmax={pmax} kW")

    #     energysystem.add(components.Source(
    #         label=asset.get("name", f"community_asset_{g_id}"),
    #         outputs={bus_elec_com: flows.Flow(
    #             fix=profile,
    #             nominal_value=Investment(ep_costs=epc, maximum=pmax)
    #         )}
    #     ))

    # ------------------------------------------------------------------
    # Add all building-level assets
    # ------------------------------------------------------------------
    for b_context in raw_context.get("building_asset_context", []):
        bid = b_context["building"]["id"]

        for asset in b_context.get("building_energy_asset", []):
            g_id = asset["generation_system"].get("id")
            label = asset["name"]
            is_inv = asset["is_investment_option"]

            if not is_inv and include_existing_assets:
                input_id = asset["generation_system"].get("energy_carrier_input_1_id")
                output_type = label.lower()
                bus_in = bus_gas_com if input_id == 5 else (bus_elec_com if input_id in (12, 24) else None)
                bus_out = (
                    buses_heat[bid] if "heating" in output_type
                    else buses_dhw[bid] if "dhw" in output_type
                    else buses_cool[bid] if "cooling" in output_type
                    else None
                )
                if bus_in and bus_out:
                    efficiency = asset["generation_system"].get("fuel_yield1", 0.9)
                    energysystem.add(Converter(
                        label=label,
                        inputs={bus_in: flows.Flow()},
                        outputs={bus_out: flows.Flow()},
                        conversion_factors={bus_out: efficiency}
                    ))

            else:
                if g_id == 83:  # PV
                    capex_kw = asset["generation_system"].get("capex_eur_kw", 2850)
                    lifetime = asset["generation_system"].get("lifetime_years", 25)
                    epc = economics.annuity(capex_kw, lifetime, 0.05)
                    pmax = asset.get("pmaxmax_scalar", asset.get("pmax_scalar")) or 0.0
                    profile = (asset.get("availability_ts") or {}).get("value_input1") or [0.0] * 8760

                    print(f"   → PV: {label} | Building {bid} | pmax = {pmax:.2f} kW")
                    energysystem.add(components.Source(
                        label=label,
                        outputs={bus_elec_com: flows.Flow(
                            fix=profile,
                            nominal_value=Investment(ep_costs=epc, maximum=pmax)
                        )}
                    ))

                elif g_id in [132, 134]:  # Wind (por si llega a building_asset por error de estructura)
                    capex_kw = asset["generation_system"].get("capex_eur_kw", 2850)
                    lifetime = asset["generation_system"].get("lifetime_years", 20)
                    epc = economics.annuity(capex_kw, lifetime, 0.05)
                    pmax = asset.get("pmaxmax_scalar", asset.get("pmax_scalar")) or 0.0
                    profile = (asset.get("availability_ts") or {}).get("value_input1")
                    if profile is None:
                        profile = (asset.get("availability_ts") or {}).get("value_output1")
                    if profile is None:
                        profile = [0.0] * 8760

                    print(f"   → Wind: {label} | Building {bid} | pmax = {pmax} kW")
                    energysystem.add(components.Source(
                        label=label,
                        outputs={bus_elec_com: flows.Flow(
                            fix=profile,
                            nominal_value=Investment(ep_costs=epc, maximum=pmax)
                        )}
                    ))

                elif g_id in [63, 31, 2]:  # Heat pumps or air conditioning
                    capex_kw = asset["generation_system"].get("capex_eur_kw", 1000)
                    lifetime = asset["generation_system"].get("lifetime_years", 25)
                    epc = economics.annuity(capex_kw, lifetime, 0.05)
                    efficiency = asset["generation_system"].get("fuel_yield1", 2.5)
                    pmax = asset.get("pmaxmax_scalar", asset.get("pmax_scalar")) or 0.0
                    subtype = "heating" if g_id == 63 else "dhw" if g_id == 31 else "cooling"
                    min_cap = get_minimum_cap("HP", pmax, subtype=subtype)
                    bus_out = {63: buses_heat[bid], 31: buses_dhw[bid], 2: buses_cool[bid]}.get(g_id)

                    print(f"   → HP/AirCon: {label} | Building {bid} | pmax={pmax} kW | min={min_cap} kW")
                    energysystem.add(Converter(
                        label=label,
                        inputs={bus_elec_com: flows.Flow()},
                        outputs={bus_out: flows.Flow(nominal_value=Investment(ep_costs=epc, minimum=min_cap, maximum=pmax))},
                        conversion_factors={bus_out: efficiency}
                    ))

                elif g_id in [71, 39]:  # Solar thermal
                    capex_kw = asset["generation_system"].get("capex_eur_kw", 600)
                    lifetime = asset["generation_system"].get("lifetime_years", 20)
                    epc = economics.annuity(capex_kw, lifetime, 0.05)
                    efficiency = asset["generation_system"].get("fuel_yield1", 0.5)
                    profile_raw = (asset.get("availability_ts") or {}).get("value_input1") or [0.0] * 8760
                    thermal_profile = [p * efficiency for p in profile_raw]
                    pmax = asset.get("pmaxmax_scalar", asset.get("pmax_scalar")) or 0.0
                    min_cap = get_minimum_cap("STC", pmax)
                    bus_out = buses_dhw[bid] if g_id == 39 else buses_heat[bid]

                    print(f"   → Solar Thermal: {label} | Building {bid} | pmax={pmax:.2f} | min={min_cap:.2f}")
                    energysystem.add(components.Source(
                        label=label,
                        outputs={bus_out: flows.Flow(
                            fix=thermal_profile,
                            nominal_value=Investment(ep_costs=epc, minimum=min_cap, maximum=pmax)
                        )}
                    ))

                elif g_id in (151, 143):  # DHN technologies (tu biomasa ya la tienes creada en tu versión)
                    print("   → DHN branch reached (151/143). (Mantén aquí tu implementación de biomasa+dhn)")

        add_thermal_storage_for_building(energysystem, buses_heat[bid], bid, storage_kwh=200.0)
        add_thermal_storage_for_dhw(energysystem, buses_dhw[bid], bid, storage_kwh=100.0)

    print("[5] Solving model...")
    model = Model(energysystem)
    add_joint_capacity_constraint(model, raw_context, divisor=6)

    try:
        model.solve(solver=solver, solve_kwargs={"tee": True})
        print("Optimization solved successfully.")
        main_results = model.results()
    except Exception as e:
        print(f"Solver failed: {e}")
        return None

    print("[6] Post-processing results...")
    context_with_results = populate_results_in_context(main_results, raw_context)
    return context_with_results

