# -*- coding: utf-8 -*-
import os
import json
import pickle
import math
import numpy as np
import pandas as pd

# -------------------------------
# CARGA DE ENTRADAS BÁSICAS
# -------------------------------

def load_context(context_json_path):
    with open(context_json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_prices_pkl(prices_pkl_path):
    with open(prices_pkl_path, "rb") as f:
        obj = pickle.load(f)

    if isinstance(obj, pd.DataFrame):
        df = obj.copy()
    elif isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
        df = pd.DataFrame(obj)
    elif isinstance(obj, dict):
        try:
            df = pd.DataFrame(obj)
        except ValueError:
            df = pd.json_normalize(obj)
    else:
        try:
            df = pd.DataFrame([vars(obj)])
        except Exception:
            df = pd.DataFrame({"value": [obj]})

    if not isinstance(df.index, pd.DatetimeIndex):
        for col in ("datetime", "timestamp", "date", "time"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                df = df.set_index(col).sort_index()
                break
        else:
            df.index = pd.to_datetime(df.index, errors="coerce", utc=True)
            df = df.sort_index()

    return df.sort_index()

# -------------------------------
# UTILIDADES DE PERIODO/RESOLUCIÓN
# -------------------------------

def select_period(series, period, year=2024, month=None):
    series = series.sort_index()
    if period == "year":
        start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        end   = pd.Timestamp(f"{year+1}-01-01", tz="UTC")
        return series.loc[(series.index >= start) & (series.index < end)]
    if period == "month":
        start = pd.Timestamp(f"{year}-{month:02d}-01", tz="UTC")
        end   = (start + pd.offsets.MonthEnd(1)) + pd.Timedelta(days=1)
        return series.loc[(series.index >= start) & (series.index < end)]
    if period == "mean_day":
        by_hour = series.groupby(series.index.hour).mean()
        idx = pd.date_range(f"{year}-06-15 00:00:00", periods=24, freq="H", tz="UTC")
        return pd.Series(by_hour.values, index=idx, name=series.name)
    raise ValueError("period debe ser 'mean_day', 'month' o 'year'")

def upsample_hourly_to_15min(series_hourly):
    vals = np.repeat(series_hourly.values, 4)
    idx  = pd.date_range(series_hourly.index[0], periods=len(vals), freq="15T", tz=series_hourly.index.tz)
    return pd.Series(vals, index=idx, name=series_hourly.name)

def ensure_resolution(series, resolution):
    resolution = resolution.strip().lower()
    freq = pd.infer_freq(series.index)
    if resolution in ("15t", "15min", "15m"):
        if freq in ("H", "1H"):
            return upsample_hourly_to_15min(series)
        return series.resample("15T").ffill()
    if resolution in ("h", "1h"):
        return series.resample("H").mean()
    return series

def pick_price_column(df):
    if "simples" in df.columns:
        return "simples"
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    df["simples"] = 0.20
    return "simples"

# -------------------------------
# LECTURA DE SERIES DEL CONTEXT
# -------------------------------

def get_elec_series_from_context(context, building_id, year=2024):
    n = int(context.get("timestep_count", 0))
    idx = pd.date_range(f"{year}-01-01 00:00:00", periods=n, freq="H", tz="UTC")
    for bac in context.get("building_asset_context", []):
        if int(bac.get("building_id")) != int(building_id):
            continue
        arr = bac.get("building_consumption", {}).get("elec_consumption", [])
        if not arr:
            return None
        if len(arr) >= n:
            vals = [float(x) if x is not None else 0.0 for x in arr[:n]]
        else:
            pad = [0.0] * (n - len(arr))
            vals = [float(x) if x is not None else 0.0 for x in arr] + pad
        return pd.Series(vals, index=idx, name=f"elec_{building_id}")
    return None

def get_pv_availability_from_context(context, building_id, year=2024):
    n = int(context.get("timestep_count", 0))
    idx_h = pd.date_range(f"{year}-01-01 00:00:00", periods=n, freq="H", tz="UTC")
    for bac in context.get("building_asset_context", []):
        if int(bac.get("building_id")) != int(building_id):
            continue
        for asset in bac.get("building_energy_asset", []):
            if asset.get("generation_system", {}).get("name") != "pv":
                continue
            avail = asset.get("availability_ts", {}).get("value_input1", [])
            if not avail:
                return None
            a = np.array([float(x) if x is not None else 0.0 for x in avail], dtype=float)
            if a.size == 96:
                days = pd.date_range(f"{year}-01-01", f"{year+1}-01-01", freq="D", tz="UTC")[:-1]
                day15 = pd.Series(a, index=pd.date_range(f"{year}-01-01", periods=96, freq="15T", tz="UTC"))
                full15 = pd.concat([day15.copy().set_axis(pd.date_range(d, periods=96, freq="15T", tz="UTC")) for d in days])
                hourly = full15.resample("H").mean()
                return hourly.iloc[:n].rename(f"pv_{building_id}")
            if a.size >= n:
                return pd.Series(a[:n], index=idx_h, name=f"pv_{building_id}")
            if a.size > 0:
                reps = int(math.ceil(n / a.size))
                tiled = np.tile(a, reps)[:n]
                return pd.Series(tiled, index=idx_h, name=f"pv_{building_id}")
    return None

# -------------------------------
# BUILD ENPOWER DATABASE (OBJETO)
# -------------------------------

def build_enpower_database(context, prices_df, period, resolution, year, month, fit_tariff_sell):
    out = {"sizing_params_by_meter": []}

    price_col = pick_price_column(prices_df)
    prices_1h = prices_df[price_col].astype(float).resample("H").mean()
    prices_win = select_period(prices_1h, period=period, year=year, month=month)
    prices_out = ensure_resolution(prices_win, resolution)
    l_buy_template = prices_out.values.tolist()

    seen = set()
    for bac in context.get("building_asset_context", []):
        b_id = int(bac.get("building_id"))
        if b_id in seen:
            continue
        seen.add(b_id)

        s_elec = get_elec_series_from_context(context, b_id, year)
        if s_elec is None:
            continue
        s_win = select_period(s_elec, period=period, year=year, month=month)
        s_out = ensure_resolution(s_win, resolution)

        if float(np.nanmax(s_out.values)) <= 0.0:
            continue

        p_meter_max = 1.2 * float(np.nanmax(s_out.values))

        e_g_factor = []
        s_pv = get_pv_availability_from_context(context, b_id, year)
        if s_pv is not None:
            pv_win = select_period(s_pv, period=period, year=year, month=month)
            pv_out = ensure_resolution(pv_win, resolution).clip(lower=0.0)
            e_g_factor = pv_out.values.tolist()

        l_buy = l_buy_template
        if len(l_buy) != len(s_out):
            if len(l_buy) < len(s_out):
                l_buy = l_buy + [l_buy[-1]] * (len(s_out) - len(l_buy))
            else:
                l_buy = l_buy[:len(s_out)]

        out["sizing_params_by_meter"].append({
            "e_c": s_out.values.astype(float).tolist(),
            "meter_id": b_id,
            "l_buy": l_buy,
            "l_sell": [float(fit_tariff_sell)] * len(l_buy),
            "e_g_factor": e_g_factor,
            "pg_n_init": 0,
            "p_meter_max": p_meter_max
        })

    return out

# -------------------------------
# GUARDAR ARCHIVOS (PY / JSON / PKL)
# -------------------------------

def save_enpower_database_py(enpower_db, output_py_path):
    payload = "# -*- coding: utf-8 -*-\nENPOWER_SIZING_DATABASE = " + json.dumps(enpower_db, indent=2) + "\n"
    dirn = os.path.dirname(output_py_path)
    if dirn:
        os.makedirs(dirn, exist_ok=True)
    with open(output_py_path, "w", encoding="utf-8") as f:
        f.write(payload)
    return output_py_path

def save_enpower_database_json(enpower_db, output_json_path):
    dirn = os.path.dirname(output_json_path)
    if dirn:
        os.makedirs(dirn, exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(enpower_db, f, ensure_ascii=False, indent=2)
    return output_json_path

def save_prices_window_pkl(prices_df, period, resolution, year, month, output_pkl_path):
    price_col = pick_price_column(prices_df)
    prices_1h = prices_df[price_col].astype(float).resample("H").mean()
    win = select_period(prices_1h, period=period, year=year, month=month)
    win = ensure_resolution(win, resolution)
    df_out = pd.DataFrame({price_col: win})
    dirn = os.path.dirname(output_pkl_path)
    if dirn:
        os.makedirs(dirn, exist_ok=True)
    with open(output_pkl_path, "wb") as f:
        pickle.dump(df_out, f)
    return output_pkl_path

# -------------------------------
# with_2_shared_assets (JSON)
# -------------------------------

def build_with_2_shared_assets(enpower_db, period, year, month, max_shared_pv_kw):
    sizing = enpower_db.get("sizing_params_by_meter", [])
    meter_ids = [str(sp["meter_id"]) for sp in sizing]
    weights = np.array([float(sp.get("p_meter_max", 0.0)) for sp in sizing], dtype=float)
    if weights.sum() <= 0:
        weights = np.ones_like(weights)
    percentages = (weights / weights.sum()) * 100.0

    if period == "year":
        start_dt = f"{year}-01-01T00:00:00Z"
        end_dt   = f"{year+1}-01-01T00:00:00Z"
        nrd = 0
    elif period == "month":
        start_dt = f"{year}-{month:02d}-01T00:00:00Z"
        next_m = pd.Timestamp(f"{year}-{month:02d}-01", tz="UTC") + pd.offsets.MonthEnd(1) + pd.Timedelta(days=1)
        end_dt = f"{next_m.year}-{next_m.month:02d}-01T00:00:00Z"
        nrd = 0
    else:  # mean_day
        start_dt = f"{year}-06-15T00:00:00Z"
        end_dt   = f"{year}-06-16T00:00:00Z"
        nrd = 1

    members = []
    for sp in sizing:
        members.append({
            "power_energy_ratio": 1,
            "minimum_new_pv_power": 0,
            "maximum_new_pv_power": 0,
            "minimum_new_storage_capacity": 0,
            "maximum_new_storage_capacity": 0,
            "l_gic": 10, "l_bic": 10,
            "soc_min": 0, "soc_max": 100,
            "eff_bc": 100, "eff_bd": 100,
            "deg_cost": 0.01,
            "meter_id": str(sp["meter_id"])
        })

    ownerships = []
    for sp, pct in zip(sizing, percentages):
        ownerships.append({
            "shared_meter_id": "Meter#3",
            "meter_id": str(sp["meter_id"]),
            "percentage": float(pct)
        })

    shared = [{
        "power_energy_ratio": 1,
        "minimum_new_pv_power": 0,
        "maximum_new_pv_power": float(max_shared_pv_kw),
        "minimum_new_storage_capacity": 0,
        "maximum_new_storage_capacity": 10,
        "l_gic": 10, "l_bic": 10,
        "soc_min": 0, "soc_max": 100,
        "eff_bc": 100, "eff_bd": 100,
        "deg_cost": 0.01,
        "meter_id": "Meter#3"
    }]

    return {
        "start_datetime": start_dt,
        "end_datetime": end_dt,
        "dataset_origin": "INDATA",
        "nr_representative_days": nrd,
        "meter_ids": meter_ids,
        "sizing_params_by_meter": members,
        "shared_meter_ids": ["Meter#3"],
        "ownerships": ownerships,
        "sizing_params_for_shared_meter": shared
    }

def save_with_2_shared_assets(shared_obj, output_txt_path):
    dirn = os.path.dirname(output_txt_path)
    if dirn:
        os.makedirs(dirn, exist_ok=True)
    with open(output_txt_path, "w", encoding="utf-8") as f:
        json.dump(shared_obj, f, ensure_ascii=False, indent=2)
    return output_txt_path
