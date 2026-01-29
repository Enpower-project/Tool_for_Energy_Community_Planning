import pandas as pd
import copy
from api.services.scripts_enpower.OEMOF_module.classes_database import BuildingEnergyAsset, CommunityEnergyAsset
from api.services.scripts_enpower.kpi_module.key_performance_indicators import load_energy_system_catalogue
from pvlib.iotools.pvgis import get_pvgis_hourly
from pvlib.iotools import get_pvgis_tmy
from pvlib.irradiance import get_total_irradiance
import geopandas as gpd
from shapely import wkt
from shapely.errors import GEOSException
from pvlib.location import Location
import api.services.scripts_enpower.helpers.constants as cte
import numpy as np
from api.services.scripts_enpower.helpers.wind_module import generate_realistic_wind_profile

# =============================================================================
# AUXILIARY FUNCTIONS
# =============================================================================

def get_centroid(group_of_geoms, target_epsg=4326):
    """
    Calculates the centroid of a group of building geometries.

    Parameters:
        group_of_geoms (dict): Dictionary of building geometries in WKT format.
        target_epsg (int): EPSG code for the output CRS.

    Returns:
        gdf (GeoDataFrame): Geometries as a GeoDataFrame.
        community_centroid (Point): The centroid of the geometries in the target CRS.
    """
    geoms_list, names_list, ids_list = [], [], []
    for building_id, data in group_of_geoms.items():
        try:
            geom_str = data.get("geom")
            if not isinstance(geom_str, str):
                continue
            geometry = wkt.loads(geom_str)
            if not geometry.is_valid:
                geometry = geometry.buffer(0)
            geoms_list.append(geometry)
            names_list.append(data.get("name"))
            ids_list.append(building_id)
        except (GEOSException, TypeError) as e:
            print(f"Error loading geometry for building {building_id}: {e}")
    if not geoms_list:
        return gpd.GeoDataFrame(), None
    gdf = gpd.GeoDataFrame({"id": ids_list, "name": names_list, "geometry": geoms_list}, crs=f"EPSG:{target_epsg}")
    gdf_projected = gdf.to_crs(epsg=3857)
    community_centroid_projected = gdf_projected.unary_union.centroid
    community_centroid = gpd.GeoSeries([community_centroid_projected], crs=3857).to_crs(epsg=target_epsg).iloc[0]
    return gdf, community_centroid


def call_PVGIS(longitude, latitude, tilt_angle, use_realistic_wind=True, collector_area=1.0):
    """
    Calls the PVGIS API to retrieve PV, wind, and STC profiles for a given location.

    Returns:
        Tuple of (pv_profile, wind_profile, stc_profile), each as hourly values (8760 points).
    """
    URL = "https://re.jrc.ec.europa.eu/api/v5_3/"

    try:
        # --- 1. PV profile call ---
        pv_data = get_pvgis_hourly(
            latitude, longitude,
            start=2023, end=2023,
            components=True,
            surface_tilt=tilt_angle,
            surface_azimuth=180,
            outputformat='json',
            usehorizon=True,
            pvcalculation=True,
            peakpower=1,
            pvtechchoice='crystSi',
            mountingplace='free',
            loss=0,
            trackingtype=0,
            url=URL
        )

        df_pv = pd.DataFrame(pv_data["outputs"]["hourly"]) if isinstance(pv_data, dict) else pd.DataFrame(pv_data[0])
        if 'P' not in df_pv.columns:
            raise ValueError("Missing 'P' column in PVGIS PV profile data.")
        pv_profile_in_kWh_kWp = [x / 1000 for x in df_pv['P'].tolist()]  # W → kW

        # --- 2. STC profile from irradiance components ---
        ghi_data = get_pvgis_hourly(
            latitude, longitude,
            start=2023, end=2023,
            components=True,
            surface_tilt=tilt_angle,
            surface_azimuth=180,
            outputformat='json',
            usehorizon=True,
            pvcalculation=False,
            peakpower=1,
            url=URL
        )

        df_ghi = pd.DataFrame(ghi_data["outputs"]["hourly"]) if isinstance(ghi_data, dict) else pd.DataFrame(ghi_data[0])
        required_cols = {"poa_direct", "poa_sky_diffuse", "poa_ground_diffuse"}
        if required_cols.issubset(df_ghi.columns):
            df_ghi["G_total"] = (
                df_ghi["poa_direct"] +
                df_ghi["poa_sky_diffuse"] +
                df_ghi["poa_ground_diffuse"]
            )
            stc_profile = (df_ghi["G_total"] * collector_area / 1000).tolist()  # Wh/m² × m² → kWh
        else:
            print("⚠️ PVGIS GHI columns received:", df_ghi.columns.tolist())
            raise ValueError("Missing irradiance components required to compute STC profile.")

        # --- 3. Wind profile ---
        if use_realistic_wind:
            wind_profile = generate_realistic_wind_profile(latitude, longitude, year=2023)
        else:
            tmy_data, *_ = get_pvgis_tmy(latitude, longitude, map_variables=False, url=URL)
            tmy_data.index = pd.to_datetime(tmy_data.index)
            WS10m = tmy_data['WS10m'].tolist()
            wind_profile = wind_power(WS10m)

        return pv_profile_in_kWh_kWp, wind_profile, stc_profile

    except Exception as e:
        print(f"Error calling PVGIS: {e}")
        return [0]*8760, [0]*8760, [0]*8760


def wind_power(wind_speed):
    """
    Converts wind speed into normalized power output based on a predefined turbine curve.
    """
    wind_speed_table = [0, 1.85, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20.01]
    power_table = [0, 0, 80, 500, 1350, 2800, 4700, 7000, 9600, 12300, 15500, 17800, 18500, 18000, 17500, 17500, 0]
    power_table = [p / 20000 for p in power_table]  # Normalize
    return np.interp(wind_speed, wind_speed_table, power_table).tolist()

# =============================================================================
# ASSET CREATION LOGIC
# =============================================================================

def create_unified_building_assets(original_building_context, action_keys, common_profiles):
    """
    Creates a unified list of building-level energy assets by migrating existing systems
    and appending new investment options.
    """
    building_id = original_building_context["building"]["id"]
    gen_profile = original_building_context.get("generation_system_profile", {})
    energy_systems_catalogue = load_energy_system_catalogue()
    
    unified_asset_list = []

    # Step 1: Migrate existing systems (Boilers and Chillers)
    for system_key in ["heating_system", "dhw_system", "cooling_system"]: 
        if gen_profile.get(system_key):
            system_info = gen_profile[system_key]
            
            if system_key == "heating_system":
                purpose = "Heating"
                asset_name_prefix = "Boiler"
            elif system_key == "dhw_system":
                purpose = "DHW"
                asset_name_prefix = "Boiler"
            else:
                purpose = "Cooling"
                asset_name_prefix = "Chiller"
            
            asset_name = f"{asset_name_prefix}_{purpose}_{building_id}_0"
            existing_asset = BuildingEnergyAsset(
                building_id=building_id,
                generation_system=system_info,
                name=asset_name,
                is_investment_option=False
            )
            unified_asset_list.append(existing_asset.to_dict())

    # Step 1b: Preserve electricity grid as an existing asset (metadata for KPIs)
    # We keep the grid as a non-investment asset so KPI modules can still read carrier/PEF/emissions.
    if gen_profile.get("electricity_system"):
        system_info = gen_profile["electricity_system"]
        asset_name = f"Grid_Electricity_{building_id}_0"
        existing_grid_asset = BuildingEnergyAsset(
            building_id=building_id,
            generation_system=system_info,
            name=asset_name,
            is_investment_option=False  # existing asset, not an investment option
            # No availability_ts required for grid purchase; OEMOF builds its own Sources
        )
        unified_asset_list.append(existing_grid_asset.to_dict())

    # Step 1b (fallback): If only electricity_system_id is present, fetch from catalogue
    elif gen_profile.get("electricity_system_id") is not None:
        try:
            elec_id = gen_profile["electricity_system_id"]
            system_info = next((s for s in energy_systems_catalogue if s.get("id") == elec_id), None)
            if system_info:
                asset_name = f"Grid_Electricity_{building_id}_0"
                existing_grid_asset = BuildingEnergyAsset(
                    building_id=building_id,
                    generation_system=system_info,
                    name=asset_name,
                    is_investment_option=False
                )
                unified_asset_list.append(existing_grid_asset.to_dict())
        except Exception as e:
            print(f"   - INFO: Skipped grid fallback for building {building_id} (error: {e})")

    # Step 2: Add new investment options
    if 3 in action_keys:  # PV
        pv_system_info = next((s for s in energy_systems_catalogue if s.get("id") == 83), {})
        pv_asset = BuildingEnergyAsset(
            building_id=building_id,
            generation_system=pv_system_info,
            name=f"PV_{building_id}",
            is_investment_option=True,
            pmaxmax_scalar=original_building_context["building"]["area_conditioned"] / 6,
            profile=common_profiles.get("pv_profile", [])
        )
        unified_asset_list.append(pv_asset.to_dict())
    
    if 10 in action_keys:  # Heat Pumps
        try:
            hp_heat_info = next((s for s in energy_systems_catalogue if s.get("id") == 63), {})
            hp_heat_info['energy_carrier_input_1_id'] = 24  # elec_usage
            hp_heat_info['energy_carrier_input_2_id'] = 15  # air
            hp_heat_info['energy_carrier_output_1_id'] = 11  # heat
            hp_heat_asset = BuildingEnergyAsset(
                building_id=building_id,
                generation_system=hp_heat_info,
                name=f"HP_{building_id}_heating_0",
                is_investment_option=True,
                pmaxmax_scalar=max(common_profiles.get(f"demand_{building_id}", {}).get("heating_demand", [0])) * 0.7
            )
            if hp_heat_asset.pmaxmax_scalar > 0:
                unified_asset_list.append(hp_heat_asset.to_dict())
        except (ValueError, KeyError) as e:
            print(f"   - INFO: Skipped heating HP for building {building_id} (no demand or error: {e})")

        try:
            hp_dhw_info = next((s for s in energy_systems_catalogue if s.get("id") == 31), {})
            hp_dhw_info['energy_carrier_input_1_id'] = 24
            hp_dhw_info['energy_carrier_input_2_id'] = 15
            hp_dhw_info['energy_carrier_output_1_id'] = 11
            hp_dhw_asset = BuildingEnergyAsset(
                building_id=building_id,
                generation_system=hp_dhw_info,
                name=f"HP_{building_id}_dhw_0",
                is_investment_option=True,
                pmaxmax_scalar=max(common_profiles.get(f"demand_{building_id}", {}).get("dhw_demand", [0])) * 0.7
            )
            if hp_dhw_asset.pmaxmax_scalar > 0:
                unified_asset_list.append(hp_dhw_asset.to_dict())
        except (ValueError, KeyError) as e:
            print(f"   - INFO: Skipped DHW HP for building {building_id} (no demand or error: {e})")

        try:
            ac_info = next((s for s in energy_systems_catalogue if s.get("id") == 2), {})
            ac_info['energy_carrier_input_1_id'] = 24
            ac_info['energy_carrier_output_1_id'] = 17
            ac_asset = BuildingEnergyAsset(
                building_id=building_id,
                generation_system=ac_info,
                name=f"AC_{building_id}_cooling_0",
                is_investment_option=True,
                pmaxmax_scalar=max(common_profiles.get(f"demand_{building_id}", {}).get("cooling_demand", [0])) * 0.7
            )
            if ac_asset.pmaxmax_scalar > 0:
                unified_asset_list.append(ac_asset.to_dict())
        except (ValueError, KeyError) as e:
            print(f"   - INFO: Skipped Air Conditioner for building {building_id} (no demand or error: {e})")

    if 7 in action_keys:  # Solar Thermal
        try:
            stc_heating = next((s for s in energy_systems_catalogue if s.get("id") == 71), {})
            stc_dhw = next((s for s in energy_systems_catalogue if s.get("id") == 39), {})

            heating_demand = common_profiles.get(f"demand_{building_id}", {}).get("heating_demand", [])
            dhw_demand = common_profiles.get(f"demand_{building_id}", {}).get("dhw_demand", [])

            # Scale approx. 70% of peak demand (same as HP logic)
            if heating_demand:
                asset = BuildingEnergyAsset(
                    building_id=building_id,
                    generation_system=stc_heating,
                    name=f"STC_Heating_{building_id}_0",
                    is_investment_option=True,
                    pmaxmax_scalar=original_building_context["building"]["area_conditioned"] / 4, #max(heating_demand) * 0.7,
                    profile=common_profiles.get("stc_profile", [])
                )
                unified_asset_list.append(asset.to_dict())

            if dhw_demand:
                asset = BuildingEnergyAsset(
                    building_id=building_id,
                    generation_system=stc_dhw,
                    name=f"STC_DHW_{building_id}_0",
                    is_investment_option=True,
                    pmaxmax_scalar=original_building_context["building"]["area_conditioned"] / 4, #max(dhw_demand) * 0.7,
                    profile=common_profiles.get("stc_profile", [])
                )
                unified_asset_list.append(asset.to_dict())

        except Exception as e:
            print(f"   - INFO: Skipped STC for building {building_id} (error: {e})")
    if 4 in action_keys:  # Wind (por building)
        wind_system_info = next((s for s in energy_systems_catalogue if s.get("id") == 132), {})
        
        wind_profile = common_profiles.get("wind_profile")
        if not isinstance(wind_profile, list) or len(wind_profile) != 8760:
            print("wind_profile inválido en common_profiles. [0]*8760")
            wind_profile = [0.0] * 8760

        # pmax por building: ejemplo usando área (ajústalo a tu criterio)
        pmax = max(0.0, (original_building_context["building"]["area_conditioned"] or 0) / 10.0)

        wind_asset = BuildingEnergyAsset(
            building_id=building_id,
            generation_system=wind_system_info,
            name=f"Wind_{building_id}",
            is_investment_option=True,
            pmaxmax_scalar=pmax,
            profile=wind_profile
        )
        if wind_asset.pmaxmax_scalar > 0:
            unified_asset_list.append(wind_asset.to_dict())
    if 18 in action_keys:  # DHN
            dhn_heating = next((s for s in energy_systems_catalogue if s.get("id") == 143), {})
            dhn_dhw = next((s for s in energy_systems_catalogue if s.get("id") == 151), {})

            heating_demand = common_profiles.get(f"demand_{building_id}", {}).get("heating_demand", [])
            dhw_demand = common_profiles.get(f"demand_{building_id}", {}).get("dhw_demand", [])
            if heating_demand:
                asset = BuildingEnergyAsset(
                    building_id=building_id,
                    generation_system=dhn_heating,
                    name=f"DHN_Heating_{building_id}_0",
                    is_investment_option=True,
                    pmaxmax_scalar=max(common_profiles.get(f"demand_{building_id}", {}).get("heating_demand", [0])) * 0.9#max(heating_demand) * 0.7,
                )
                unified_asset_list.append(asset.to_dict())

            if dhw_demand:
                asset = BuildingEnergyAsset(
                    building_id=building_id,
                    generation_system=dhn_dhw,
                    name=f"DHN_DHW_{building_id}_0",
                    is_investment_option=True,
                    pmaxmax_scalar=max(common_profiles.get(f"demand_{building_id}", {}).get("dhw_demand", [0])) * 0.9
                )
                unified_asset_list.append(asset.to_dict())
    return unified_asset_list

# def create_unified_community_assets(action_keys, common_profiles):
#     """
#     Creates a list of community-level energy assets.
#     """
#     community_asset_list = []
#     energy_systems_catalogue = load_energy_system_catalogue()

#     if 4 in action_keys:  # Wind
#         wind_system_info = next((s for s in energy_systems_catalogue if s.get("id") == 132), {})

#         wind_profile = common_profiles.get("wind_profile")
#         if not isinstance(wind_profile, list) or len(wind_profile) != 8760:
#             print("wind_profile inválido en common_profiles. [0]*8760")
#             wind_profile = [0.0] * 8760

#         wind_asset = CommunityEnergyAsset(
#             generation_system=wind_system_info,
#             name="Community_wind_turbine_default",
#             is_investment_option=True,
#             pmaxmax_scalar=2000,
#             profile=wind_profile,
#             geom=common_profiles.get("community_centroid_wkt", "POINT (0 0)")
#         )
#         community_asset_list.append(wind_asset.to_dict())

#     return community_asset_list
