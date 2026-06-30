import json
import io
import time
import requests
from requests.auth import HTTPBasicAuth

from api.constants import SITEC_API_URL, SITEC_USER, SITEC_PASSWORD

def _day_hour_range(month, day, year=2024):
    """
    Parameters
    ----------
    month : int
        Month number (1..12).
    day : int
        Day number within the selected month.
    year : int
        Reference year (non-leap assumed for 8760 series).

    Returns
    -------
    tuple
        (start_hour_index, end_hour_index_exclusive)

    Definition
    ----------
    Computes the hourly slice for one selected day in a non-leap-year 8760 series.
    """
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month < 1 or month > 12:
        raise ValueError("month must be in [1..12].")
    if day < 1 or day > days_in_month[month - 1]:
        raise ValueError("day is out of range for the selected month.")

    start_day = sum(days_in_month[: month - 1]) + (day - 1)
    start_hour = start_day * 24
    end_hour = start_hour + 24
    return start_hour, end_hour


def _day_start_end_iso(month, day, year=2024):
    """
    Parameters
    ----------
    month : int
        Month number (1..12).
    day : int
        Day number within the selected month.
    year : int
        Year.

    Returns
    -------
    tuple
        (start_datetime_iso, end_datetime_iso)

    Definition
    ----------
    Returns day start and next-day start in ISO-8601 Zulu format.
    """
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month < 1 or month > 12:
        raise ValueError("month must be in [1..12].")
    if day < 1 or day > days_in_month[month - 1]:
        raise ValueError("day is out of range for the selected month.")

    start = f"{year:04d}-{month:02d}-{day:02d}T00:00:00Z"

    if day < days_in_month[month - 1]:
        end = f"{year:04d}-{month:02d}-{day + 1:02d}T00:00:00Z"
    else:
        if month == 12:
            end = f"{year + 1:04d}-01-01T00:00:00Z"
        else:
            end = f"{year:04d}-{month + 1:02d}-01T00:00:00Z"

    return start, end

def build_enpower_database_from_unified_context_daily(unified_context, month=6, day=15, year=2024):
    """
    Parameters
    ----------
    unified_context : dict
        Unified context containing the same structure as the monthly builder.
    month : int
        Month number (1..12).
    day : int
        Day number within the selected month.
    year : int
        Year used only for day-count logic (8760 non-leap assumed).

    Returns
    -------
    tuple
        (enpower_database_py_code: str, intervals_15min: int, start_datetime: str, end_datetime: str)

    Definition
    ----------
    Builds ENPOWER_SIZING_DATABASE as a Python module string for one selected day:
    - e_c from elec_consumption hourly -> day slice -> 15-min
    - l_buy/l_sell from GRID (gen_id 79)
    - e_g_factor from PV (gen_id 83) availability_ts.value_input1 hourly -> day slice -> 15-min
    - Adds "Meter#pv" with e_c all zeros and prices/generation copied from the last building
    """
    bacs = unified_context.get("building_asset_context", []) or []
    if not isinstance(bacs, list) or not bacs:
        raise ValueError("unified_context has no building_asset_context entries.")

    h0, h1 = _day_hour_range(month=month, day=day, year=year)
    start_datetime, end_datetime = _day_start_end_iso(month=month, day=day, year=year)
    day_hours = h1 - h0
    intervals = day_hours * 4

    def hourly_to_15min(hourly_values):
        out = []
        for v in hourly_values:
            out.extend([float(v)] * 4)
        return out

    def get_building_id(bctx):
        if bctx.get("building_id") is not None:
            return str(bctx["building_id"])
        building = bctx.get("building", {})
        if isinstance(building, dict) and building.get("id") is not None:
            return str(building["id"])
        raise KeyError("Unable to find building id (building_id or building.id).")

    def get_building_use_id(bctx):
        if bctx.get("building_use_id") is not None:
            return int(bctx["building_use_id"])
        building = bctx.get("building", {})
        if isinstance(building, dict) and building.get("building_use_id") is not None:
            return int(building["building_use_id"])
        raise KeyError("Unable to find building_use_id (building_use_id or building.building_use_id).")

    def get_grid_prices_from_building(bctx):
        building_use_id = get_building_use_id(bctx)

        assets = bctx.get("building_energy_asset", []) or []
        if not isinstance(assets, list):
            raise ValueError("building_energy_asset must be a list.")

        grid_asset = None
        for a in assets:
            if isinstance(a, dict) and int(a.get("generation_system_id", -1)) == 79:
                grid_asset = a
                break
        if grid_asset is None:
            raise ValueError("GRID asset not found (generation_system_id == 79).")

        gs = grid_asset.get("generation_system", {}) or {}
        ec_in1 = gs.get("energy_carrier_input_1", {}) or {}
        nep = ec_in1.get("national_energy_carrier_production", []) or []
        if not isinstance(nep, list) or not nep or not isinstance(nep[0], dict):
            raise ValueError("GRID national_energy_carrier_production is missing/invalid.")

        record = nep[0]

        house_buy = record.get("house_costs_eur_kwh", None)
        non_house_buy = record.get("non_h_costs_eur_kwh", None)
        sell_fit = record.get("fit_tariff_eur_kwh", None)
        if sell_fit is None:
            raise ValueError("fit_tariff_eur_kwh not found in GRID national_energy_carrier_production[0].")

        if building_use_id in (1, 2, 3):
            if house_buy is None:
                raise ValueError("house_costs_eur_kwh missing for household building.")
            l_buy_value = float(house_buy)
        else:
            if non_house_buy is None:
                raise ValueError("non_h_costs_eur_kwh missing for non-household building.")
            l_buy_value = float(non_house_buy)

        l_sell_value = float(sell_fit)
        return l_buy_value, l_sell_value

    def get_pv_generation_factor_15min(bctx):
        assets = bctx.get("building_energy_asset", []) or []
        if not isinstance(assets, list):
            raise ValueError("building_energy_asset must be a list.")

        pv_asset = None
        for a in assets:
            if isinstance(a, dict) and int(a.get("generation_system_id", -1)) == 83:
                pv_asset = a
                break
        if pv_asset is None:
            raise ValueError("PV asset not found (generation_system_id == 83).")

        hourly = (pv_asset.get("availability_ts") or {}).get("value_input1", [])
        if not (isinstance(hourly, list) and len(hourly) == 8760):
            raise ValueError("PV availability_ts.value_input1 must be a list of 8760 hourly values.")

        slice_hourly = hourly[h0:h1]
        eg_15min = hourly_to_15min(slice_hourly)

        if len(eg_15min) != intervals:
            raise ValueError(f"PV e_g_factor daily length mismatch. Expected {intervals}, got {len(eg_15min)}")

        return eg_15min

    sizing_params_by_meter = []

    last_l_buy = None
    last_l_sell = None
    last_e_g_factor = None
    agg_e_c_15min = []

    for bctx in bacs:
        bid = get_building_id(bctx)

        elec_hourly = (bctx.get("building_consumption") or {}).get("elec_consumption", [])
        if not (isinstance(elec_hourly, list) and len(elec_hourly) == 8760):
            raise ValueError(f"Building {bid} elec_consumption must be a list of 8760 hourly values.")

        slice_hourly = elec_hourly[h0:h1]
        e_c_15min = hourly_to_15min(slice_hourly)
        if len(e_c_15min) != intervals:
            raise ValueError(f"Building {bid} daily e_c length mismatch. Expected {intervals}, got {len(e_c_15min)}")

        l_buy_value, l_sell_value = get_grid_prices_from_building(bctx)
        last_l_buy = l_buy_value
        last_l_sell = l_sell_value

        e_g_factor_15min = get_pv_generation_factor_15min(bctx)
        last_e_g_factor = e_g_factor_15min

        agg_e_c_15min.extend(e_c_15min)

        sizing_params_by_meter.append(
            {
                "e_c": e_c_15min,
                "meter_id": bid,
                "l_buy": [float(l_buy_value)] * intervals,
                "l_sell": [float(l_sell_value)] * intervals,
                "e_g_factor": e_g_factor_15min,
                "pg_n_init": 0,
                "p_meter_max": float(max(e_c_15min) if e_c_15min else 0.0),
            }
        )

    if last_l_buy is None or last_l_sell is None or last_e_g_factor is None:
        raise RuntimeError("Unable to build Meter#pv daily data (missing prices or PV generation factor).")

    pv_meter = {
        "e_c": [0.0] * intervals,
        "meter_id": "Meter#pv",
        "l_buy": [float(last_l_buy)] * intervals,
        "l_sell": [float(last_l_sell)] * intervals,
        "e_g_factor": last_e_g_factor,
        "pg_n_init": 0,
        "p_meter_max": (max(agg_e_c_15min) if agg_e_c_15min else 0.0) * 1.2,
    }

    ENPOWER_SIZING_DATABASE = {"sizing_params_by_meter": sizing_params_by_meter + [pv_meter]}

    enpower_database_py_code = (
        "# -*- coding: utf-8 -*-\n"
        "ENPOWER_SIZING_DATABASE = "
        + json.dumps(ENPOWER_SIZING_DATABASE, indent=4)
        + "\n"
    )

    return enpower_database_py_code, intervals, start_datetime, end_datetime

def build_with_2_assets_txt_daily(unified_context, month=6, day=15, dataset_origin="INDATA"):
    """
    Parameters
    ----------
    unified_context : dict
        Unified context containing building_asset_context and building_energy_asset entries.
    month : int
        Month number (1..12).
    day : int
        Day number within the selected month.
    dataset_origin : str
        Dataset origin label expected by SITEC.

    Returns
    -------
    str
        JSON payload text for POST /sizing_with_shared_assets.

    Definition
    ----------
    Builds daily sizing payload with:
    - shared_meter_id fixed to "Meter#pv"
    - nr_representative_days fixed to 0
    - ownerships equal shares summing to 100
    - per-building maximum_new_pv_power set to PV pmaxmax_scalar (roof potential)
    - shared PV max = sum(per-building PV pmaxmax_scalar)
    """
    start_datetime, end_datetime = _day_start_end_iso(month=month, day=day, year=2024)

    shared_meter_id = "Meter#pv"
    nr_representative_days = 0
    pv_margin_factor = 1

    default_meter_params = {
        "power_energy_ratio": 1,
        "minimum_new_pv_power": 0,
        "maximum_new_pv_power": 0,
        "minimum_new_storage_capacity": 0,
        "maximum_new_storage_capacity": 0,
        "l_gic": 10,
        "l_bic": 10,
        "soc_min": 0,
        "soc_max": 100,
        "eff_bc": 100,
        "eff_bd": 100,
        "deg_cost": 0.01,
    }

    default_shared_params = {
        "power_energy_ratio": 1,
        "minimum_new_pv_power": 0,
        "maximum_new_pv_power": 0,
        "minimum_new_storage_capacity": 0,
        "maximum_new_storage_capacity": 10,
        "l_gic": 10,
        "l_bic": 10,
        "soc_min": 0,
        "soc_max": 100,
        "eff_bc": 100,
        "eff_bd": 100,
        "deg_cost": 0.01,
    }

    bacs = unified_context.get("building_asset_context", [])
    if not isinstance(bacs, list) or not bacs:
        raise ValueError("unified_context['building_asset_context'] must be a non-empty list.")

    def get_building_id(bctx):
        if bctx.get("building_id") is not None:
            return str(bctx["building_id"])
        building = bctx.get("building", {})
        if isinstance(building, dict) and building.get("id") is not None:
            return str(building["id"])
        raise KeyError("Unable to find building id.")

    def get_pv_pmaxmax_scalar(bctx, pv_generation_system_id=83):
        assets = bctx.get("building_energy_asset", [])
        if not isinstance(assets, list):
            assets = []

        for a in assets:
            try:
                if int(a.get("generation_system_id", -1)) == int(pv_generation_system_id) and a.get("pmaxmax_scalar") is not None:
                    return float(a["pmaxmax_scalar"])
            except (TypeError, ValueError):
                continue

        for a in assets:
            if isinstance(a, dict) and a.get("pmaxmax_scalar") is not None:
                try:
                    return float(a["pmaxmax_scalar"])
                except (TypeError, ValueError):
                    return 0.0

        return 0.0

    meter_ids = []
    sizing_params_by_meter = []
    pv_roof_sum = 0.0

    for bctx in bacs:
        bid = get_building_id(bctx)
        meter_ids.append(bid)

        pv_max_building = max(0.0, float(get_pv_pmaxmax_scalar(bctx)))
        pv_roof_sum += pv_max_building

        entry = dict(default_meter_params)
        entry["meter_id"] = bid
        entry["maximum_new_pv_power"] = pv_max_building
        sizing_params_by_meter.append(entry)

    n = len(meter_ids)
    if n == 0:
        raise ValueError("No building meter_ids found.")

    equal_share = 100.0 / float(n)
    ownerships = [{"shared_meter_id": shared_meter_id, "meter_id": bid, "percentage": equal_share} for bid in meter_ids]

    shared_pv_max = pv_roof_sum * pv_margin_factor

    shared_entry = dict(default_shared_params)
    shared_entry["maximum_new_pv_power"] = float(shared_pv_max)
    shared_entry["meter_id"] = shared_meter_id

    payload = {
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "dataset_origin": dataset_origin,
        "nr_representative_days": nr_representative_days,
        "meter_ids": meter_ids,
        "sizing_params_by_meter": sizing_params_by_meter,
        "shared_meter_ids": [shared_meter_id],
        "ownerships": ownerships,
        "sizing_params_for_shared_meter": [shared_entry],
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)

def upload_enpower_database(enpower_database_py_code, timeout_s=120):

    url = f"{SITEC_API_URL}/upload/enpower_database"
    auth = HTTPBasicAuth(SITEC_USER, SITEC_PASSWORD)

    headers = {"Accept": "application/json"}

    file_stream = io.BytesIO(enpower_database_py_code.encode("utf-8"))
    files = {"file": ("enpower_database.py", file_stream, "text/x-python")}

    response = requests.post(
        url=url,
        auth=auth,
        headers=headers,
        files=files,
        timeout=timeout_s
    )

    if not response.ok:
        raise RuntimeError(
            f"SITEC upload failed | Status: {response.status_code} | Response: {response.text}"
        )

    if "application/json" in response.headers.get("Content-Type", "").lower():
        return response.json()

    return {"message": response.text}


def upload_prices_and_tariffs(prices_and_tariffs, timeout_s=120):

    url = f"{SITEC_API_URL}/upload/prices_and_tariffs"
    auth = HTTPBasicAuth(SITEC_USER, SITEC_PASSWORD)

    headers = {"Accept": "application/json"}

    if isinstance(prices_and_tariffs, list):
        json_content = json.dumps(prices_and_tariffs, ensure_ascii=False)
    elif isinstance(prices_and_tariffs, str):
        parsed = json.loads(prices_and_tariffs)
        if not isinstance(parsed, list):
            raise TypeError("prices_and_tariffs JSON root must be a list.")
        json_content = json.dumps(parsed, ensure_ascii=False)
    else:
        raise TypeError("prices_and_tariffs must be a list or a JSON string whose root is a list.")

    if not json_content.lstrip().startswith("["):
        raise RuntimeError("Internal error: prices_and_tariffs upload content is not a JSON list.")

    file_stream = io.BytesIO(json_content.encode("utf-8"))
    files = {"file": ("prices_and_tariffs.json", file_stream, "application/json")}

    response = requests.post(
        url=url,
        auth=auth,
        headers=headers,
        files=files,
        timeout=timeout_s
    )

    if not response.ok:
        raise RuntimeError(
            f"SITEC upload failed | Status: {response.status_code} | Response: {response.text}"
        )

    if "application/json" in response.headers.get("Content-Type", "").lower():
        return response.json()

    return {"message": response.text}


def sizing_with_shared_assets(sizing_request_txt, timeout_s=300):

    url = f"{SITEC_API_URL}/sizing_with_shared_assets"
    auth = HTTPBasicAuth(SITEC_USER, SITEC_PASSWORD)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = json.loads(sizing_request_txt)

    response = requests.post(
        url=url,
        auth=auth,
        headers=headers,
        json=payload,
        timeout=timeout_s
    )

    if not response.ok:
        raise RuntimeError(
            f"SITEC sizing_with_shared_assets failed | Status: {response.status_code} | Response: {response.text}"
        )

    return response.json()


def get_sizing_results(order_id):


    url = f"{SITEC_API_URL}/get_sizing/{order_id}"
    auth = HTTPBasicAuth(SITEC_USER, SITEC_PASSWORD)

    headers = {
        "Accept": "application/json"
    }

    attempt = 0
    max_attempts = 10
    wait_seconds = 2
    
    while attempt < max_attempts:

        response = requests.get(
            url=url,
            auth=auth,
            headers=headers,
            timeout=120
        )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 202:
            time.sleep(wait_seconds)
            attempt += 1
            continue

        raise RuntimeError(
            f"SITEC get_sizing failed | "
            f"Status: {response.status_code} | Response: {response.text}"
        )

    raise TimeoutError(
        f"Sizing result not ready after {max_attempts} attempts."
    )

def build_prices_and_tariffs_list(intervals, value=0.0106):

    return [float(value)] * int(intervals)

def build_enpower_database_from_unified_context(unified_context, month=6, year=2024):

    bacs = unified_context.get("building_asset_context", []) or []
    if not isinstance(bacs, list) or not bacs:
        raise ValueError("unified_context has no building_asset_context entries.")

    # Non-leap month slicing for 8760
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if not isinstance(month, int) or month < 1 or month > 12:
        raise ValueError("month must be in [1..12].")

    start_day = sum(days_in_month[: month - 1])
    month_days = days_in_month[month - 1]
    h0 = start_day * 24
    h1 = (start_day + month_days) * 24

    month_hours = h1 - h0
    intervals = month_hours * 4

    def hourly_to_15min(hourly_values):
        out = []
        for v in hourly_values:
            out.extend([float(v)] * 4)
        return out

    def get_building_id(bctx):
        if bctx.get("building_id") is not None:
            return str(bctx["building_id"])
        building = bctx.get("building", {})
        if isinstance(building, dict) and building.get("id") is not None:
            return str(building["id"])
        raise KeyError("Unable to find building id (building_id or building.id).")

    def get_building_use_id(bctx):
        if bctx.get("building_use_id") is not None:
            return int(bctx["building_use_id"])
        building = bctx.get("building", {})
        if isinstance(building, dict) and building.get("building_use_id") is not None:
            return int(building["building_use_id"])
        raise KeyError("Unable to find building_use_id (building_use_id or building.building_use_id).")

    def get_grid_prices_from_building(bctx):
        """
        Returns (l_buy_value, l_sell_value) as floats from GRID (generation_system_id == 79).
        """
        building_use_id = get_building_use_id(bctx)

        assets = bctx.get("building_energy_asset", []) or []
        if not isinstance(assets, list):
            raise ValueError("building_energy_asset must be a list.")

        grid_asset = None
        for a in assets:
            if isinstance(a, dict) and int(a.get("generation_system_id", -1)) == 79:
                grid_asset = a
                break
        if grid_asset is None:
            raise ValueError("GRID asset not found (generation_system_id == 79).")

        gs = grid_asset.get("generation_system", {}) or {}
        ec_in1 = gs.get("energy_carrier_input_1", {}) or {}
        nep = ec_in1.get("national_energy_carrier_production", []) or []
        if not isinstance(nep, list) or not nep or not isinstance(nep[0], dict):
            raise ValueError("GRID national_energy_carrier_production is missing/invalid.")

        record = nep[0]

        house_buy = record.get("house_costs_eur_kwh", None)
        non_house_buy = record.get("non_h_costs_eur_kwh", None)
        sell_fit = record.get("fit_tariff_eur_kwh", None)
        if sell_fit is None:
            raise ValueError("fit_tariff_eur_kwh not found in GRID national_energy_carrier_production[0].")

        if building_use_id in (1, 2, 3):
            if house_buy is None:
                raise ValueError("house_costs_eur_kwh missing for household building.")
            l_buy_value = float(house_buy)
        else:
            if non_house_buy is None:
                raise ValueError("non_h_costs_eur_kwh missing for non-household building.")
            l_buy_value = float(non_house_buy)

        l_sell_value = float(sell_fit)
        return l_buy_value, l_sell_value

    def get_pv_generation_factor_15min(bctx):

        assets = bctx.get("building_energy_asset", []) or []
        if not isinstance(assets, list):
            raise ValueError("building_energy_asset must be a list.")

        pv_asset = None
        for a in assets:
            if isinstance(a, dict) and int(a.get("generation_system_id", -1)) == 83:
                pv_asset = a
                break
        if pv_asset is None:
            raise ValueError("PV asset not found (generation_system_id == 83).")

        hourly = (pv_asset.get("availability_ts") or {}).get("value_input1", [])
        if not (isinstance(hourly, list) and len(hourly) == 8760):
            raise ValueError("PV availability_ts.value_input1 must be a list of 8760 hourly values.")

        slice_hourly = hourly[h0:h1]
        eg_15min = hourly_to_15min(slice_hourly)

        if len(eg_15min) != intervals:
            raise ValueError(f"PV e_g_factor length mismatch. Expected {intervals}, got {len(eg_15min)}")

        return eg_15min

    sizing_params_by_meter = []

    last_l_buy = None
    last_l_sell = None
    last_e_g_factor = None

    # heuristic for pv_meter p_meter_max
    agg_e_c_15min = []

    for bctx in bacs:
        bid = get_building_id(bctx)

        # Consumption
        elec_hourly = (bctx.get("building_consumption") or {}).get("elec_consumption", [])
        if not (isinstance(elec_hourly, list) and len(elec_hourly) == 8760):
            raise ValueError(f"Building {bid} elec_consumption must be a list of 8760 hourly values.")

        slice_hourly = elec_hourly[h0:h1]
        e_c_15min = hourly_to_15min(slice_hourly)
        if len(e_c_15min) != intervals:
            raise ValueError(f"Building {bid} e_c length mismatch. Expected {intervals}, got {len(e_c_15min)}")

        # Grid prices
        l_buy_value, l_sell_value = get_grid_prices_from_building(bctx)
        last_l_buy = l_buy_value
        last_l_sell = l_sell_value

        # PV generation factor
        e_g_factor_15min = get_pv_generation_factor_15min(bctx)
        last_e_g_factor = e_g_factor_15min

        agg_e_c_15min.extend(e_c_15min)

        sizing_params_by_meter.append(
            {
                "e_c": e_c_15min,
                "meter_id": bid,
                "l_buy": [float(l_buy_value)] * intervals,
                "l_sell": [float(l_sell_value)] * intervals,
                "e_g_factor": e_g_factor_15min,
                "pg_n_init": 0,
                "p_meter_max": float(max(e_c_15min) if e_c_15min else 0.0),
            }
        )

    if last_l_buy is None or last_l_sell is None or last_e_g_factor is None:
        raise RuntimeError("Unable to build Meter#pv data (missing prices or PV generation factor).")

    pv_meter = {
        "e_c": [0.0] * intervals,
        "meter_id": "Meter#pv",
        "l_buy": [float(last_l_buy)] * intervals,
        "l_sell": [float(last_l_sell)] * intervals,
        "e_g_factor": last_e_g_factor,
        "pg_n_init": 0,
        "p_meter_max": (max(agg_e_c_15min) if agg_e_c_15min else 0.0) * 1.2,
    }

    ENPOWER_SIZING_DATABASE = {"sizing_params_by_meter": sizing_params_by_meter + [pv_meter]}

    enpower_database_py_code = (
        "# -*- coding: utf-8 -*-\n"
        "ENPOWER_SIZING_DATABASE = "
        + json.dumps(ENPOWER_SIZING_DATABASE, indent=4)
        + "\n"
    )

    return enpower_database_py_code, intervals


import json


def build_with_2_assets_txt(unified_context, month=6, dataset_origin="INDATA"):


    # Month boundaries (non-leap assumption)
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if month < 1 or month > 12:
        raise ValueError("month must be in [1..12].")

    start_datetime = f"2024-{month:02d}-01T00:00:00Z"
    if month == 12:
        end_datetime = "2025-01-01T00:00:00Z"
    else:
        end_datetime = f"2024-{month+1:02d}-01T00:00:00Z"

    shared_meter_id = "Meter#pv"
    nr_representative_days = 0
    pv_margin_factor = 1

    # Default blocks (keep as you had)
    default_meter_params = {
        "power_energy_ratio": 1,
        "minimum_new_pv_power": 0,
        "maximum_new_pv_power": 0,  # will be overwritten per building
        "minimum_new_storage_capacity": 0,
        "maximum_new_storage_capacity": 0,
        "l_gic": 10,
        "l_bic": 10,
        "soc_min": 0,
        "soc_max": 100,
        "eff_bc": 100,
        "eff_bd": 100,
        "deg_cost": 0.01,
    }

    default_shared_params = {
        "power_energy_ratio": 1,
        "minimum_new_pv_power": 0,
        "maximum_new_pv_power": 0,  # will be set from sum roof potential
        "minimum_new_storage_capacity": 0,
        "maximum_new_storage_capacity": 10,
        "l_gic": 10,
        "l_bic": 10,
        "soc_min": 0,
        "soc_max": 100,
        "eff_bc": 100,
        "eff_bd": 100,
        "deg_cost": 0.001,
    }

    bacs = unified_context.get("building_asset_context", [])
    if not isinstance(bacs, list) or not bacs:
        raise ValueError("unified_context['building_asset_context'] must be a non-empty list.")

    def get_building_id(bctx):
        if bctx.get("building_id") is not None:
            return str(bctx["building_id"])
        building = bctx.get("building", {})
        if isinstance(building, dict) and building.get("id") is not None:
            return str(building["id"])
        raise KeyError("Unable to find building id.")

    def get_pv_pmaxmax_scalar(bctx, pv_generation_system_id=83):
        """
        Returns PV pmaxmax_scalar for a building.
        - Primary: asset with generation_system_id == 83 and pmaxmax_scalar present
        - Fallback: first asset that has pmaxmax_scalar
        """
        assets = bctx.get("building_energy_asset", [])
        if not isinstance(assets, list):
            assets = []

        # Primary rule: PV by generation_system_id
        for a in assets:
            try:
                if int(a.get("generation_system_id", -1)) == int(pv_generation_system_id) and a.get("pmaxmax_scalar") is not None:
                    return float(a["pmaxmax_scalar"])
            except (TypeError, ValueError):
                continue

        # Fallback: any pmaxmax_scalar
        for a in assets:
            if isinstance(a, dict) and a.get("pmaxmax_scalar") is not None:
                try:
                    return float(a["pmaxmax_scalar"])
                except (TypeError, ValueError):
                    return 0.0

        return 0.0

    meter_ids = []
    sizing_params_by_meter = []
    pv_roof_sum = 0.0
    pv_roof_by_building = {}

    for bctx in bacs:
        bid = get_building_id(bctx)
        meter_ids.append(bid)

        pv_max_building = max(0.0, float(get_pv_pmaxmax_scalar(bctx)))
        pv_roof_by_building[bid] = pv_max_building
        pv_roof_sum += pv_max_building

        entry = dict(default_meter_params)
        entry["meter_id"] = bid

        # KEY CHANGE: per-building PV max based on roof potential
        entry["maximum_new_pv_power"] = pv_max_building

        sizing_params_by_meter.append(entry)

    n = len(meter_ids)
    if n == 0:
        raise ValueError("No building meter_ids found.")

    # Ownership equal shares in 0..100 scale
    equal_share = 100.0 / float(n)
    ownerships = [{"shared_meter_id": shared_meter_id, "meter_id": bid, "percentage": equal_share} for bid in meter_ids]

    # Shared PV max = sum roof potential + margin
    shared_pv_max = pv_roof_sum * pv_margin_factor

    shared_entry = dict(default_shared_params)
    shared_entry["maximum_new_pv_power"] = float(shared_pv_max)
    shared_entry["meter_id"] = shared_meter_id

    payload = {
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "dataset_origin": dataset_origin,
        "nr_representative_days": nr_representative_days,
        "meter_ids": meter_ids,
        "sizing_params_by_meter": sizing_params_by_meter,
        "shared_meter_ids": [shared_meter_id],
        "ownerships": ownerships,
        "sizing_params_for_shared_meter": [shared_entry],
    }

    return json.dumps(payload, ensure_ascii=False, indent=2)

def poll_sizing_results(order_id, sleep_s=2, max_attempts=60):

    last = None
    for _ in range(int(max_attempts)):
        last = get_sizing_results(order_id)
        return last  # if this endpoint already blocks until ready
        time.sleep(sleep_s)
    return last
def update_unified_context(selected_combo, unified_context, sitec_results):

    # ------------------------------------------------------------
    # 0) Skip if scenario is not PV+Battery (id=19, label PV+Battery)
    # ------------------------------------------------------------
    is_pv_battery = (
        isinstance(selected_combo, dict)
        and int(selected_combo.get("id", -1)) == 19
        and str(selected_combo.get("combination", "")).strip() == "PV+Battery"
    )
    if not is_pv_battery:
        return unified_context

    if not isinstance(unified_context, dict):
        raise TypeError("unified_context must be a dict.")
    if not isinstance(sitec_results, dict):
        raise TypeError("sitec_results must be a dict.")

    # ------------------------------------------------------------
    # 1) Extract per-meter installed PV from SITEC results
    # ------------------------------------------------------------
    meter_outputs = sitec_results.get("meter_investment_outputs", [])
    if not isinstance(meter_outputs, list):
        # If structure differs, do not break pipeline; skip safely
        return unified_context

    installed_pv_by_building_id = {}

    for row in meter_outputs:
        if not isinstance(row, dict):
            continue

        meter_id_raw = row.get("meter_id", None)
        if meter_id_raw is None:
            continue

        meter_id_str = str(meter_id_raw).strip()

        # Ignore shared meters (e.g. "Meter#pv")
        if meter_id_str.startswith("Meter#"):
            continue

        try:
            building_id_int = int(meter_id_str)
        except Exception:
            # If SITEC uses other ids, we skip that entry
            continue

        try:
            installed_pv = float(row.get("installed_pv", 0.0) or 0.0)
        except Exception:
            installed_pv = 0.0

        installed_pv_by_building_id[building_id_int] = installed_pv

    # If there is no data, skip
    if not installed_pv_by_building_id:
        return unified_context

    # ------------------------------------------------------------
    # 2) If all installed PV values are 0 => keep unified_context unchanged
    # ------------------------------------------------------------
    max_installed = max(installed_pv_by_building_id.values()) if installed_pv_by_building_id else 0.0
    if max_installed <= 0.0:
        return unified_context

    # ------------------------------------------------------------
    # 3) Apply PV sizing to unified_context PV assets (generation_system_id == 83)
    # ------------------------------------------------------------
    bacs = unified_context.get("building_asset_context", [])
    if not isinstance(bacs, list):
        return unified_context

    def _get_building_id_int(bctx):
        if bctx.get("building_id") is not None:
            return int(bctx["building_id"])
        building = bctx.get("building", {})
        if isinstance(building, dict) and building.get("id") is not None:
            return int(building["id"])
        raise KeyError("Unable to find building id in building_asset_context entry.")

    updated_any = False

    for bctx in bacs:
        try:
            b_id = _get_building_id_int(bctx)
        except Exception:
            continue

        if b_id not in installed_pv_by_building_id:
            continue

        new_pmax = float(installed_pv_by_building_id[b_id])

        # If SITEC gives 0 for this building, do not force-change it
        if new_pmax <= 0.0:
            continue

        assets = bctx.get("building_energy_asset", [])
        if not isinstance(assets, list):
            continue

        for asset in assets:
            if not isinstance(asset, dict):
                continue
            if int(asset.get("generation_system_id", -1)) == 83:
                asset["pmax_scalar"] = new_pmax
                updated_any = True

    # If nothing was updated (mapping mismatch), keep as-is
    if not updated_any:
        return unified_context

    return unified_context
