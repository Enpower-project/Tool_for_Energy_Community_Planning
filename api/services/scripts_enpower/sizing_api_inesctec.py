# -*- coding: utf-8 -*-
import os
import json
import pickle
import math
from typing import Optional, Tuple, Dict, List

import pandas as pd
import numpy as np

# ------------------------------------------------------------
# CARGA DE ENTRADAS
# ------------------------------------------------------------

def load_context(path_json: str) -> dict:
    with open(path_json, "r", encoding="utf-8") as f:
        return json.load(f)

def load_prices_pkl(path_pkl: str) -> pd.DataFrame:
    with open(path_pkl, "rb") as f:
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

    # Índice temporal
    if not isinstance(df.index, pd.DatetimeIndex):
        for col in ("datetime", "timestamp", "date", "time"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                df = df.set_index(col).sort_index()
                break
        else:
            # Si no hay columna de fecha, intenta convertir el índice actual
            df.index = pd.to_datetime(df.index, errors="coerce", utc=True)
            df = df.sort_index()

    return df.sort_index()

# ------------------------------------------------------------
# UTILIDADES SIMPLES: PERIODO, RESOLUCIÓN Y SERIES
# ------------------------------------------------------------

def select_period(series: pd.Series, period: str, year: int = 2024, month: Optional[int] = None) -> pd.Series:
    """
    period: "mean_day" | "month" | "year"
    year:   2024 por defecto
    month:  1..12 (solo cuando period == "month")
    """
    series = series.sort_index()
    if period == "year":
        start = pd.Timestamp(f"{year}-01-01", tz="UTC")
        end   = pd.Timestamp(f"{year+1}-01-01", tz="UTC")
        return series.loc[(series.index >= start) & (series.index < end)]
    elif period == "month":
        if month is None:
            raise ValueError("Debes indicar month=1..12 cuando period='month'")
        start = pd.Timestamp(f"{year}-{month:02d}-01", tz="UTC")
        end   = (start + pd.offsets.MonthEnd(1)) + pd.Timedelta(days=1)
        return series.loc[(series.index >= start) & (series.index < end)]
    elif period == "mean_day":
        # Día promedio: media por hora a lo largo del año
        by_hour = series.groupby(series.index.hour).mean()
        idx = pd.date_range(f"{year}-06-15 00:00:00", periods=24, freq="H", tz="UTC")
        return pd.Series(by_hour.values, index=idx, name=series.name)
    else:
        raise ValueError("period debe ser 'mean_day', 'month' o 'year'")

def upsample_hourly_to_15min(series_hourly: pd.Series) -> pd.Series:
    """Convierte una serie horaria en 15 min repitiendo cada hora 4 veces (simple y robusto)."""
    vals = np.repeat(series_hourly.values, 4)
    idx  = pd.date_range(series_hourly.index[0], periods=len(vals), freq="15T", tz=series_hourly.index.tz)
    return pd.Series(vals, index=idx, name=series_hourly.name)

def ensure_resolution(series: pd.Series, resolution: str) -> pd.Series:
    """
    Si resolution == "15T": si es horaria, repetir 4x; si ya está a 15T, devolver tal cual.
    Si resolution == "1H": hacer media a 1H si viene a 15T; si ya es horaria, devolver tal cual.
    """
    resolution = resolution.strip().lower()
    # Intento de inferencia
    freq = pd.infer_freq(series.index)
    if resolution in ("15t", "15min", "15m"):
        if freq in ("H", "1H"):
            return upsample_hourly_to_15min(series)
        else:
            # si ya está a 15T (o más fina), nos quedamos con 15T por ffill
            return series.resample("15T").ffill()
    elif resolution in ("h", "1h"):
        return series.resample("H").mean()
    else:
        # por defecto, devolvemos tal cual
        return series

def pick_price_column(df: pd.DataFrame) -> str:
    if "simples" in df.columns:
        return "simples"
    # si no hay 'simples', coge la primera columna numérica
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    # si no hay numéricas, creamos una constante
    df["simples"] = 0.20
    return "simples"

# ------------------------------------------------------------
# LECTURA DE SERIES DESDE EL CONTEXT
# ------------------------------------------------------------

def get_elec_series_from_context(context: dict, b_id: int, year: int = 2024) -> Optional[pd.Series]:
    """
    Devuelve serie horaria (kW) de consumo eléctrico para building_id = b_id.
    Espera 'timestep_count' (e.g., 8760) y 'elec_consumption' en el context.
    """
    n = int(context.get("timestep_count", 0))
    idx = pd.date_range(f"{year}-01-01 00:00:00", periods=n, freq="H", tz="UTC")

    for bac in context.get("building_asset_context", []):
        if int(bac.get("building_id")) == b_id:
            arr = bac.get("building_consumption", {}).get("elec_consumption", [])
            if not arr:
                return None
            # ajustar longitud a n
            if len(arr) >= n:
                vals = [float(x) if x is not None else 0.0 for x in arr[:n]]
            else:
                pad = [0.0] * (n - len(arr))
                vals = [float(x) if x is not None else 0.0 for x in arr] + pad
            return pd.Series(vals, index=idx, name=f"elec_{b_id}")
    return None

def get_pv_availability_from_context(context: dict, b_id: int, year: int = 2024) -> Optional[pd.Series]:
    """
    Devuelve serie horaria (0..1) de disponibilidad FV si el edificio la tiene.
    - Si llega un día a 15 min (96), se replica por todos los días de 'year' y se promedia por hora.
    - Si llega horaria, se usa tal cual.
    """
    n = int(context.get("timestep_count", 0))
    idx_h = pd.date_range(f"{year}-01-01 00:00:00", periods=n, freq="H", tz="UTC")

    for bac in context.get("building_asset_context", []):
        if int(bac.get("building_id")) != b_id:
            continue
        for asset in bac.get("building_energy_asset", []):
            if asset.get("generation_system", {}).get("name") == "pv":
                avail = asset.get("availability_ts", {}).get("value_input1", [])
                if not avail:
                    return None
                a = np.array([float(x) if x is not None else 0.0 for x in avail], dtype=float)
                if a.size == 96:
                    days = pd.date_range(f"{year}-01-01", f"{year+1}-01-01", freq="D", tz="UTC")[:-1]
                    day15 = pd.Series(a, index=pd.date_range(f"{year}-01-01", periods=96, freq="15T", tz="UTC"))
                    full15 = pd.concat([day15.copy().set_axis(pd.date_range(d, periods=96, freq="15T", tz="UTC")) for d in days])
                    hourly = full15.resample("H").mean()
                    return hourly.iloc[:n].rename(f"pv_{b_id}")
                else:
                    # si viene horaria o distinta longitud, rearmar a n horas por truncado/tiling
                    if a.size >= n:
                        return pd.Series(a[:n], index=idx_h, name=f"pv_{b_id}")
                    else:
                        reps = int(math.ceil(n / a.size)) if a.size > 0 else 1
                        tiled = np.tile(a, reps)[:n]
                        return pd.Series(tiled, index=idx_h, name=f"pv_{b_id}")
    return None

# ------------------------------------------------------------
# CONSTRUCCIÓN DE ENPOWER_DATABASE (OBJETO)
# ------------------------------------------------------------

def build_enpower_database(context: dict,
                           prices_df: pd.DataFrame,
                           period: str = "mean_day",
                           resolution: str = "15T",
                           year: int = 2024,
                           month: Optional[int] = None,
                           fit_tariff_sell: float = 0.0) -> dict:
    """
    Devuelve ENPOWER_SIZING_DATABASE (diccionario) para TODOS los edificios con consumo > 0.
    - p_meter_max = 1.2 * max(e_c)
    - pg_n_init   = 0
    - l_sell      = fit_tariff_sell (constante)
    - l_buy       = columna 'simples' (si existe) o primera numérica del PKL
    - e_g_factor  = perfil PV si está en el context
    """
    out = {"sizing_params_by_meter": []}

    # Elegir columna de precios
    price_col = pick_price_column(prices_df)
    # Precios a 1H para normalizar y seleccionar periodo; luego ajustamos resolución
    prices_1h = prices_df[price_col].astype(float).resample("H").mean()
    prices_win = select_period(prices_1h, period=period, year=year, month=month)
    prices_out = ensure_resolution(prices_win, resolution=resolution)
    l_buy_template = prices_out.values.tolist()

    # Recorrer edificios del context
    seen_ids = set()
    for bac in context.get("building_asset_context", []):
        b_id = int(bac.get("building_id"))
        if b_id in seen_ids:
            continue
        seen_ids.add(b_id)

        s_elec = get_elec_series_from_context(context, b_id, year=year)
        if s_elec is None:
            continue

        # Selección de periodo y resolución
        s_win = select_period(s_elec, period=period, year=year, month=month)
        s_out = ensure_resolution(s_win, resolution=resolution)

        # Omitir si todo es 0 en ese periodo
        if float(np.nanmax(s_out.values)) <= 0.0:
            continue

        # p_meter_max = 1.2 * pico
        p_meter_max = 1.2 * float(np.nanmax(s_out.values))

        # e_g_factor (si hay PV)
        s_pv = get_pv_availability_from_context(context, b_id, year=year)
        if s_pv is not None:
            pv_win = select_period(s_pv, period=period, year=year, month=month)
            pv_out = ensure_resolution(pv_win, resolution=resolution).clip(lower=0.0)
            e_g_factor = pv_out.values.tolist()
        else:
            e_g_factor = []

        # l_buy (igual longitud que e_c)
        l_buy = l_buy_template
        if len(l_buy) != len(s_out):
            # recortar o rellenar último valor para cuadrar
            if len(l_buy) < len(s_out):
                l_buy = l_buy + [l_buy[-1]] * (len(s_out) - len(l_buy))
            else:
                l_buy = l_buy[:len(s_out)]

        sizing_item = {
            "e_c": s_out.values.astype(float).tolist(),
            "meter_id": b_id,
            "l_buy": l_buy,
            "l_sell": [float(fit_tariff_sell)] * len(l_buy),
            "e_g_factor": e_g_factor,
            "pg_n_init": 0,
            "p_meter_max": p_meter_max
        }
        out["sizing_params_by_meter"].append(sizing_item)

    return out

# ------------------------------------------------------------
# ESCRITURA DE SALIDAS (una función por salida)
# ------------------------------------------------------------

def save_enpower_database_py(enpower_db: dict, out_path_py: str) -> None:
    payload = "# -*- coding: utf-8 -*-\nENPOWER_SIZING_DATABASE = " + json.dumps(enpower_db, indent=2) + "\n"
    os.makedirs(os.path.dirname(out_path_py), exist_ok=True)
    with open(out_path_py, "w", encoding="utf-8") as f:
        f.write(payload)

def save_enpower_database_json(enpower_db: dict, out_path_json: str) -> None:
    os.makedirs(os.path.dirname(out_path_json), exist_ok=True)
    with open(out_path_json, "w", encoding="utf-8") as f:
        json.dump(enpower_db, f, ensure_ascii=False, indent=2)

def save_prices_window_pkl(prices_df: pd.DataFrame,
                           period: str,
                           resolution: str,
                           out_path_pkl: str,
                           year: int = 2024,
                           month: Optional[int] = None) -> None:
    """
    Guarda un PKL con la columna de precios elegida, recortado al periodo y resolución.
    (Sencillo: solo una columna, p. ej. 'simples').
    """
    price_col = pick_price_column(prices_df)
    prices_1h = prices_df[price_col].astype(float).resample("H").mean()
    win = select_period(prices_1h, period=period, year=year, month=month)
    win = ensure_resolution(win, resolution=resolution)
    df_out = pd.DataFrame({price_col: win})
    os.makedirs(os.path.dirname(out_path_pkl), exist_ok=True)
    with open(out_path_pkl, "wb") as f:
        pickle.dump(df_out, f)

# ------------------------------------------------------------
# (OPCIONAL) with_2_shared_assets.txt SIMPLE
# ------------------------------------------------------------

def build_with_2_shared_assets(enpower_db: dict,
                               period: str,
                               resolution: str,
                               year: int = 2024,
                               month: Optional[int] = None,
                               shared_meter_id: str = "Meter#3",
                               max_shared_pv_kw: float = 58.0) -> dict:
    """Versión simple: miembros con 0 de PV y almacenamiento; shared meter con 58 kW."""
    sizing = enpower_db.get("sizing_params_by_meter", [])
    meter_ids = [f"Meter#{x['meter_id']}" for x in sizing]

    # Pesos ∝ p_meter_max
    weights = np.array([x.get("p_meter_max", 0.0) for x in sizing], dtype=float)
    if weights.sum() <= 0:
        weights = np.ones_like(weights)
    ownership_pct = (weights / weights.sum()) * 100.0

    # Parámetros por miembro
    sp_members = []
    for x in sizing:
        sp_members.append({
            "power_energy_ratio": 1,
            "minimum_new_pv_power": 0,
            "maximum_new_pv_power": 0,
            "minimum_new_storage_capacity": 0,
            "maximum_new_storage_capacity": 0,
            "l_gic": 10, "l_bic": 10,
            "soc_min": 0, "soc_max": 100,
            "eff_bc": 100, "eff_bd": 100,
            "deg_cost": 0.01,
            "meter_id": f"Meter#{x['meter_id']}"
        })

    ownerships = [{"shared_meter_id": shared_meter_id, "meter_id": m, "percentage": float(p)}
                  for m, p in zip(meter_ids, ownership_pct)]

    sp_shared = [{
        "power_energy_ratio": 1,
        "minimum_new_pv_power": 0,
        "maximum_new_pv_power": float(max_shared_pv_kw),
        "minimum_new_storage_capacity": 0,
        "maximum_new_storage_capacity": 0,
        "l_gic": 10, "l_bic": 10,
        "soc_min": 0, "soc_max": 100,
        "eff_bc": 100, "eff_bd": 100,
        "deg_cost": 0.01,
        "meter_id": shared_meter_id
    }]

    # Ventanas de tiempo sencillas
    if period == "year":
        start_dt = f"{year}-01-01T00:00:00Z"
        end_dt   = f"{year+1}-01-01T00:00:00Z"
        nrdays   = 0
    elif period == "month":
        start_dt = f"{year}-{month:02d}-01T00:00:00Z"
        # fin = primer día del siguiente mes
        next_m = pd.Timestamp(f"{year}-{month:02d}-01", tz="UTC") + pd.offsets.MonthEnd(1) + pd.Timedelta(days=1)
        end_dt = f"{next_m.year}-{next_m.month:02d}-01T00:00:00Z"
        nrdays = 0
    else:  # mean_day
        start_dt = f"{year}-06-15T00:00:00Z"
        end_dt   = f"{year}-06-16T00:00:00Z"
        nrdays   = 1

    return {
        "start_datetime": start_dt,
        "end_datetime": end_dt,
        "dataset_origin": "INDATA",
        "nr_representative_days": nrdays,
        "meter_ids": meter_ids,
        "sizing_params_by_meter": sp_members,
        "shared_meter_ids": [shared_meter_id],
        "ownerships": ownerships,
        "sizing_params_for_shared_meter": sp_shared
    }

def save_with_2_shared_assets(shared_obj: dict, out_path_txt: str) -> None:
    os.makedirs(os.path.dirname(out_path_txt), exist_ok=True
    )
    with open(out_path_txt, "w", encoding="utf-8") as f:
        json.dump(shared_obj, f, ensure_ascii=False, indent=2)

# ------------------------------------------------------------
# USO DE EJEMPLO (ajusta rutas a tu carpeta 'data')
# ------------------------------------------------------------
if __name__ == "__main__":
    # Entradas (ajusta rutas)
    data_dir = os.path.join(os.getcwd(), "data")
    ctx_path = os.path.join(data_dir, "final_context_scenario_1.json")     # <- tu context
    pkl_path = os.path.join(data_dir, "prices_and_tariffs.pkl")            # <- tu PKL
    out_dir  = os.path.join(os.getcwd(), "outputs_simple")
    os.makedirs(out_dir, exist_ok=True)

    # Parámetros sencillos
    PERIOD     = "mean_day"   # "mean_day" | "month" | "year"
    RESOLUTION = "15T"        # "15T" | "1H"
    YEAR       = 2024
    MONTH      = 7            # solo se usa si PERIOD == "month"
    FIT_SELL   = 0.0          # l_sell constante

    # 1) Cargar entradas
    context = load_context(ctx_path)
    prices  = load_prices_pkl(pkl_path)

    # 2) Construir ENPOWER_DATABASE (objeto)
    enpower_db = build_enpower_database(context, prices,
                                        period=PERIOD,
                                        resolution=RESOLUTION,
                                        year=YEAR,
                                        month=MONTH,
                                        fit_tariff_sell=FIT_SELL)

    # 3) Guardar salidas:
    #   - .py obligatorio
    save_enpower_database_py(enpower_db, os.path.join(out_dir, "enpower_database.py"))
    #   - .json (útil para inspección)
    save_enpower_database_json(enpower_db, os.path.join(out_dir, "enpower_database.json"))
    #   - prices_and_tariffs recortado al periodo/resolución
    save_prices_window_pkl(prices, PERIOD, RESOLUTION, os.path.join(out_dir, "prices_and_tariffs.pkl"),
                           year=YEAR, month=MONTH)

    # (Opcional) with_2_shared_assets.txt
    shared = build_with_2_shared_assets(enpower_db, PERIOD, RESOLUTION, year=YEAR, month=MONTH,
                                        shared_meter_id="Meter#3", max_shared_pv_kw=58.0)
    save_with_2_shared_assets(shared, os.path.join(out_dir, "with_2_shared_assets.txt"))

    print("Listo. Ficheros en:", out_dir)
