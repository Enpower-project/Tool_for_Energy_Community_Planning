"""
Helper module with canonical classes for unified building and community energy assets,
including consumption and demand structures.

Originally authored by: andgab (2024)
"""

import numpy as np
import api.services.scripts_enpower.helpers.constants as cte

# =============================================================================
# DOTDICT: Helper class for attribute-style access to dict keys
# -----------------------------------------------------------------------------
# Plain explanation:
# This small class lets you use "data.key" instead of "data['key']".
# It does not change the data itself; it only makes it easier to read.
# =============================================================================

class dotdict(dict):
    """
    Enables attribute-style access for dictionaries.
    Example: data['key'] can be accessed as data.key
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

# =============================================================================
# ENERGY ASSET CLASSES
# -----------------------------------------------------------------------------
# Plain explanation:
# These classes describe energy assets that can belong to a building
# or to the whole community. They store:
#   • basic information (name, technology id)
#   • investment limits (if it is an option to invest)
#   • timeseries placeholders for inputs and outputs
# Later, other parts of the framework fill in the results (e.g., sizes and profiles).
# =============================================================================

class EnergyAsset:
    """
    Canonical base class for any energy asset (building or community level).
    """
    def __init__(self, generation_system, name, is_investment_option=False, **kwargs):
        self.generation_system = generation_system or {}
        self.generation_system_id = self.generation_system.get('id')
        self.name = name
        self.is_investment_option = is_investment_option

        # --- Investment parameters ---
        # If this is an investment option, keep the allowed min/max installed capacity.
        self.pmaxmax_scalar = kwargs.get("pmaxmax_scalar") if is_investment_option else None
        self.pmaxmin_scalar = kwargs.get("pmaxmin_scalar", 0) if is_investment_option else None

        # --- Simulation results ---
        # pmax_scalar will later store the chosen (optimized) installed capacity.
        # availability_ts holds time series for inputs/outputs (to be filled after simulation).
        self.pmax_scalar = None
        self.availability_ts = {
            "name": f"ts_{self.name}",
            "value_input1": kwargs.get("profile", []),
            "value_input2": [],
            "value_output1": [],
            "value_output2": []
        }

    def _base_to_dict(self):
        """Builds a dictionary representation of the asset."""
        obj = {
            "id_temp": None,
            "generation_system_id": self.generation_system_id,
            "name": self.name,
            "is_investment_option": self.is_investment_option,
            "generation_system": self.generation_system,
            "pmax_scalar": self.pmax_scalar,
            "availability_ts": self.availability_ts
        }
        if self.is_investment_option:
            obj.update({
                "pmaxmin_scalar": self.pmaxmin_scalar,
                "pmaxmax_scalar": self.pmaxmax_scalar
            })
        return obj


class BuildingEnergyAsset(EnergyAsset):
    """Represents a building-level energy asset."""
    def __init__(self, building_id, **kwargs):
        super().__init__(**kwargs)
        self.building_id = building_id

    def to_dict(self):
        # For building assets, include the building id in the exported dictionary.
        obj = self._base_to_dict()
        obj = self._base_to_dict()
        obj["building_asset_context_id"] = self.building_id
        return obj


class CommunityEnergyAsset(EnergyAsset):
    """Represents a shared community-level energy asset."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.geom = kwargs.get("geom", "POINT (0 0)")

    def to_dict(self):
        # For community assets, include a small input node section with geometry and name.
        obj = self._base_to_dict()
        obj["input_node"] = {"geom": self.geom, "name": self.name}
        return obj


# =============================================================================
# BUILDING CONSUMPTION AND DEMAND STRUCTURES
# -----------------------------------------------------------------------------
# Plain explanation:
# • BuildingConsumption stores annual energy consumption time series (as given or derived).
# • BuildingDemand stores the corresponding demands the model needs to meet.
#   Demands can be recalculated using simple efficiency factors (fuel_yield1).
# =============================================================================

class BuildingConsumption:
    """
    Stores and processes the annual consumption time series per building.
    """
    def __init__(self, building_consumption_id_temp, elec_consumption):
        self.building_consumption_id_temp = building_consumption_id_temp
        hours = 8760
        # Start with empty thermal/cooling; electricity may be provided
        self.heat_consumption = [0] * hours
        self.dhw_consumption = [0] * hours
        self.elec_consumption = elec_consumption if elec_consumption is not None else [0] * hours
        self.cool_consumption = [0] * hours

    def add_existing_consumptions(self, heat_consumption, dhw_consumption, cool_consumption):
        # Fill in given time series (length should be 8760 each)
        self.heat_consumption = heat_consumption
        self.dhw_consumption = dhw_consumption
        self.cool_consumption = cool_consumption

    def to_dict(self):
        # Export format used elsewhere in the framework
        return {
            cte.ID: self.building_consumption_id_temp,
            cte.HEAT_CONSUMPTION: self.heat_consumption,
            cte.DHW_CONSUMPTION: self.dhw_consumption,
            cte.ELECTRICITY_CONSUMPTION: self.elec_consumption,
            cte.COOL_CONSUMPTION: self.cool_consumption
        }

    def re_calculate_consumption(self, demand, fuel_yield1, type=cte.HEAT_CONSUMPTION):
        # Convert demand into consumption using an efficiency factor (fuel_yield1).
        # If no data, keep zeros; otherwise, scale each hour.
        if demand is None or fuel_yield1 is None or fuel_yield1 == 0:
            output = [0] * 8760
        else:
            output = [x / fuel_yield1 for x in demand]

        # Store the result in the right field
        if type == cte.HEAT_CONSUMPTION:
            self.heat_consumption = output
        elif type == cte.DHW_CONSUMPTION:
            self.dhw_consumption = output
        elif type == cte.COOL_CONSUMPTION:
            self.cool_consumption = output


class BuildingDemand:
    """
    Stores and calculates building-level demand profiles from consumption.
    """
    def __init__(self, electricity_consumption):
        hours = 8760
        self.heating_demand = [0] * hours
        self.dhw_demand = [0] * hours
        # Electricity demand is often known directly (e.g., measured or provided)
        self.electricity_demand = electricity_consumption if electricity_consumption is not None else [0] * hours
        self.cooling_demand = [0] * hours

    def to_dict(self):
        # Export format used by the model builder
        return {
            cte.HEATING_DEMAND: self.heating_demand,
            cte.DHW_DEMAND: self.dhw_demand,
            cte.ELECTRICITY_DEMAND: self.electricity_demand,
            cte.COOLING_DEMAND: self.cooling_demand
        }

    def re_calculate_demand(self, consumption, fuel_yield1, type=cte.HEATING_DEMAND):
        # Convert consumption into demand using an efficiency factor (fuel_yield1).
        # If the factor or data is missing, keep a zero series.
        if consumption is None or fuel_yield1 is None:
            output = [0] * 8760
        else:
            output = [x * fuel_yield1 for x in consumption]

        # Store the result in the matching demand series
        if type == cte.HEATING_DEMAND:
            self.heating_demand = output
        elif type == cte.DHW_DEMAND:
            self.dhw_demand = output
        elif type == cte.COOLING_DEMAND:
            self.cooling_demand = output

class BuildingData:
    """
    Aggregates all building-related metadata, energy assets, consumption and demand.
    """
    def __init__(self, id, **kwargs):
        self.id = id
        self.name = None
        self.building_energy_assets = []
        self.building_consumption = {}
        self.building_demand = {}
       # Basic building info (geometry, year, use, etc.) taken from constants keys
        self.geometry = kwargs.get(cte.GEOMETRY)
        self.construction_year = kwargs.get(cte.CONSTRUCTION_YEAR)
        self.building_use_id = kwargs.get(cte.BUILDING_USE_ID)
        self.subdivision_community = kwargs.get(cte.SUBDIVISION_COMMUNITY)
        self.subdivision_total = kwargs.get(cte.SUBDIVISION_TOTAL)
        # Which systems the building currently uses (electricity, DHW, cooling, heating)
        self.generation_system_for_electricity = kwargs.get(cte.ELECTRICITY_SYSTEM)
        self.generation_system_for_dhw = kwargs.get(cte.DHW_SYSTEM)
        self.generation_system_for_cooling = kwargs.get(cte.COOLING_SYSTEM)
        self.generation_system_for_heating = kwargs.get(cte.HEATING_SYSTEM)

    def associate_building_data(self, building):
        # Copy general metadata from a "building" dict.
        if not building:
            return
        self.geometry = building.get(cte.GEOMETRY)
        self.construction_year = building.get(cte.CONSTRUCTION_YEAR)
        self.building_use_id = building.get(cte.BUILDING_USE_ID)
        self.subdivision_community = building.get(cte.SUBDIVISION_COMMUNITY)
        self.subdivision_total = building.get(cte.SUBDIVISION_TOTAL)

    def associate_building_consumption(self, consumption_data):
        # Load the building’s consumption time series from a dict.
        if not consumption_data:
            return
        elec = [float(v) for v in consumption_data.get(cte.ELECTRICITY_CONSUMPTION, [])]
        dhw = [float(v) for v in consumption_data.get(cte.DHW_CONSUMPTION, [])]
        heat = [float(v) for v in consumption_data.get(cte.HEAT_CONSUMPTION, [])]
        cool = [float(v) for v in consumption_data.get(cte.COOL_CONSUMPTION, [])]

        building_consumption = BuildingConsumption(consumption_data.get("id"), elec_consumption=elec)
        building_consumption.add_existing_consumptions(heat, dhw, cool)
        self.building_consumption = building_consumption

    def associate_building_demand(self, generation_system_profile):
        # Using the chosen/known systems, convert consumption into demand profiles
        # (simple multipliers via fuel_yield1).
        if not self.building_consumption:
            return
        demand = BuildingDemand(self.building_consumption.elec_consumption)

        dhw_system = (generation_system_profile or {}).get(cte.DHW_SYSTEM, {})
        heat_system = (generation_system_profile or {}).get(cte.HEATING_SYSTEM, {})
        cool_system = (generation_system_profile or {}).get(cte.COOLING_SYSTEM, {})

        demand.re_calculate_demand(self.building_consumption.dhw_consumption, dhw_system.get(cte.FUEL_YIELD_1, 0), cte.DHW_DEMAND)
        demand.re_calculate_demand(self.building_consumption.heat_consumption, heat_system.get(cte.FUEL_YIELD_1, 0), cte.HEATING_DEMAND)
        demand.re_calculate_demand(self.building_consumption.cool_consumption, cool_system.get(cte.FUEL_YIELD_1, 0), cte.COOLING_DEMAND)

        self.building_demand = demand.to_dict()

    def associate_generation_system_info(self, generation_system_profile):
        # Store which generation systems the building uses (for later reference).
        if not generation_system_profile:
            return
        self.generation_system_for_electricity = generation_system_profile.get(cte.ELECTRICITY_SYSTEM)
        self.generation_system_for_dhw = generation_system_profile.get(cte.DHW_SYSTEM)
        self.generation_system_for_cooling = generation_system_profile.get(cte.COOLING_SYSTEM)
        self.generation_system_for_heating = generation_system_profile.get(cte.HEATING_SYSTEM)

    def associate_building_energy_asset(self, asset_list):
        """
        Accepts a list of energy asset dictionaries and converts them to dotdicts for internal use.
        """
        if not asset_list:
            return
        self.building_energy_assets = [dotdict(asset) for asset in asset_list]


# =============================================================================
# Final Energy and KPIs
# -----------------------------------------------------------------------------
# Plain explanation:
# • FinalEnergy stores an energy time series and provides monthly and yearly sums.
# • BuildingKPIs multiplies that final energy by factors (PEF, CO2, costs)
#   to produce hourly/monthly/yearly indicators ready for reporting.
# =============================================================================

class FinalEnergy:
    def __init__(self, id):
        self.id = id
        self.name = None
        self.final = False
        self._hourly_data = [0] * 8760
        self.monthly_data = [0] * 12
        self.yearly_data = 0
        self.recalculate()

    @property
    def hourly_data(self):
        return self._hourly_data

    @hourly_data.setter
    def hourly_data(self, new_hourly_data):
        if len(new_hourly_data) != 8760:
            raise ValueError("Hourly data must have 8760 values.")
        self._hourly_data = [0 if v is None else v for v in new_hourly_data]
        self.recalculate()

    def recalculate(self):
        # Whenever hourly data changes, update monthly and yearly totals.
        self.monthly_data = self.calculate_monthly(self._hourly_data)
        self.yearly_data = sum(self._hourly_data)

    def calculate_monthly(self, hourly_data):
        # Split the 8760 series into months (typical hour counts per month).
        hours_per_month = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
        monthly_data = []
        start = 0
        for hours in hours_per_month:
            monthly_data.append(sum(hourly_data[start:start + hours]))
            start += hours
        return monthly_data

    def final_energy_to_dict(self):
        # Export format: hour/month/year for reporting and KPI modules.
        return {
            "name": self.name, "final": self.final,
            "hour": self._hourly_data[:],
            "month": self.monthly_data[:],
            "year": self.yearly_data
        }

    def add_new_consumption(self, consumption):
        # Add another time series to the existing one (hour by hour).
        if len(consumption) != 8760:
            raise ValueError("Consumption data must have 8760 values.")
        self._hourly_data = [self._hourly_data[i] + (consumption[i] or 0) for i in range(8760)]
        self.recalculate()


class BuildingKPIs:
    def __init__(self, final_energy_instance, kpi_data):
        # Keep a reference to the final energy and basic carrier info
        self.final_energy = final_energy_instance
        self.energy_carrier_name = final_energy_instance.name
        self.energy_carrier_id = kpi_data['energy_carrier_id']
        # Load factors; if missing, treat them as zero (safe default)
        self.pef_tot = kpi_data.get('pef_tot', 0.0) or 0
        self.pef_nren = kpi_data.get('pef_nren', 0.0) or 0
        self.f_co2_eq_g_kwh = kpi_data.get('f_co2_eq_g_kwh', 0.0) or 0
        self.pef_ren = kpi_data.get('pef_ren', 0.0) or 0
        self.non_h_costs_eur_kwh = kpi_data.get('non_h_costs_eur_kwh', 0.0) or 0
        self.house_costs_eur_kwh = kpi_data.get('house_costs_eur_kwh', 0.0) or 0
        self.calculate_kpis()

    def calculate_kpis(self):
        # Multiply hourly final energy by each factor to get KPIs over time.
        hourly_data = self.final_energy.hourly_data
        self.PEF_total = [h * self.pef_tot for h in hourly_data]
        self.PEF_nren = [h * self.pef_nren for h in hourly_data]
        self.PEF_ren = [h * self.pef_ren for h in hourly_data]
        self.co2 = [h * self.f_co2_eq_g_kwh for h in hourly_data]
        self.non_h_costs = [h * self.non_h_costs_eur_kwh for h in hourly_data]
        self.household_costs = [h * self.house_costs_eur_kwh for h in hourly_data]

        # Aggregate to monthly and yearly values (with unit scaling where needed).
        self.PEF_total_monthly = [v * 1e-3 for v in self.calculate_monthly(self.PEF_total)]
        self.PEF_nren_monthly = [v * 1e-3 for v in self.calculate_monthly(self.PEF_nren)]
        self.PEF_ren_monthly = [v * 1e-3 for v in self.calculate_monthly(self.PEF_ren)]
        self.co2_monthly = [v * 1e-6 for v in self.calculate_monthly(self.co2)]
        self.non_h_costs_monthly = [v * 1e-3 for v in self.calculate_monthly(self.non_h_costs)]
        self.household_costs_monthly = [v * 1e-3 for v in self.calculate_monthly(self.household_costs)]

        self.PEF_total_yearly = sum(self.PEF_total) * 1e-3
        self.PEF_nren_yearly = sum(self.PEF_nren) * 1e-3
        self.PEF_ren_yearly = sum(self.PEF_ren) * 1e-3
        self.co2_yearly = sum(self.co2) * 1e-6
        self.non_h_costs_yearly = sum(self.non_h_costs) * 1e-3
        self.household_costs_yearly = sum(self.household_costs) * 1e-3

    def calculate_monthly(self, hourly_data):
        # Helper to group any hourly series by month (same month lengths as above).
        hours_per_month = [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
        monthly_data = []
        start = 0
        for hours in hours_per_month:
            monthly_data.append(sum(hourly_data[start:start + hours]))
            start += hours
        return monthly_data

    def to_dict(self):
        # Export KPIs in a structured way (hourly, monthly, yearly) for reporting.
        return {
            "energy_carrier_name": self.energy_carrier_name,
            "energy_carrier_id": self.energy_carrier_id,
            "PEF_total_hourly": self.PEF_total,
            "PEF_total_monthly": self.PEF_total_monthly,
            "PEF_total_yearly": self.PEF_total_yearly,
            "PEF_nren_hourly": self.PEF_nren,
            "PEF_nren_monthly": self.PEF_nren_monthly,
            "PEF_nren_yearly": self.PEF_nren_yearly,
            "PEF_ren_hourly": self.PEF_ren,
            "PEF_ren_monthly": self.PEF_ren_monthly,
            "PEF_ren_yearly": self.PEF_ren_yearly,
            "co2_hourly": self.co2,
            "co2_monthly": self.co2_monthly,
            "co2_yearly": self.co2_yearly,
            "non_h_costs_hourly": self.non_h_costs,
            "non_h_costs_monthly": self.non_h_costs_monthly,
            "non_h_costs_yearly": self.non_h_costs_yearly,
            "household_costs_hourly": self.household_costs,
            "household_costs_monthly": self.household_costs_monthly,
            "household_costs_yearly": self.household_costs_yearly
        }
