import os
import numpy as np
import pandas as pd
from demandlib import bdew  # Required for farm and commercial profiles


# =============================================================================
# Configuration
# -----------------------------------------------------------------------------
# We assume each household is represented by a *linear combination* of CHRxx
# profiles (hourly CSVs) scaled by:
#   (a) the count of people/devices in that category from the JSON record, and
#   (b) a simple factor for that category.
#
# IMPORTANT: The CSVs must exist in `profile_dir` and each must contain a single
# column with the *same length* (ideally 8,760 rows = one year hourly).
# =============================================================================

# JSON field name -> CHR file base name
CHR_MAP = {
    "adults_working_out_of_home": "CHR35",
    "adults_working_remotely":    "CHR62",
    "adults_unemployed":          "CHR36",
    "students_working":           "CHR13",
    "students_unemployed":        "CHR11",
    "children":                   "CHR36",
    "retired_people":             "CHR58",
}

# Per-category multiplicative factor (unitless) applied to its CHR profile
FACTORS = {
    "adults_working_out_of_home": 0.81,
    "adults_working_remotely":    0.77,
    "adults_unemployed":          0.66,
    "students_working":           0.75,
    "students_unemployed":        0.80,
    "children":                   0.53,
    "retired_people":             0.43,
}

# -------- Commercial profiles -------------------------------
# Mapping use_id/use_name -> BDEW key (g0..g7)
COMMERCIAL_USE_MAP = {
    4: "g1",  # 4: offices -> G1
    5: "g0",  # 5: trade   -> G0
    6: "g4",  # 6: education (G1->G4 changed for specifc school profile from CEA)
}

# Annual intensity per m² (kWh/m²·year) — CityEnergyAnalyst values
# for the function "inputs/building-properties/internal_loads.dbf" as the sum of Ea_Wm2 and El_Wm2 into kWh/m²·year for each defined use, where: 
# Ea_Wm2(Peak specific electrical load due to computers and devices) + El_Wm2 (Peak specific electrical load due to artificial lighting)

PER_SQM = {
    "g0": 309.23, #ENPOWER use g0_comercio_general, CEA use RETAIL
    "g1": 200.60, #ENPOWER use g1_oficinas_talleres, CEA use OFFICE
    "g2": 104.24, #ENPOWER use g2_gimnasios_restaurantes, CEA use GYM
    "g3": 182.21, #ENPOWER use g3_operacion_continua, CEA use INDUSTRIAL
    "g4": 157.68, #ENPOWER use g4_tienda_peluqueria, CEA use SCHOOL
    "g5": 204.11, #ENPOWER use g5_panaderia, CEA use FOODSTORE
    "g6": 77.96, #ENPOWER use g6_cines_entretenimiento, CEA use RESTAURANT, this was not included before
}


# =============================================================================
# Household profiles
# =============================================================================

def load_chr_profiles(profile_dir: str = ".") -> dict:
    """
    Load and validate the CHRxx CSV profiles needed for household profiles.

    Parameters
    ----------
    profile_dir : str
        Directory where CHR*.csv files are located.

    Returns
    -------
    dict[str, np.ndarray]
        Mapping like {"CHR35": array([...]), "CHR62": array([...]), ...}.
        All arrays have identical length (checked).

    Raises
    ------
    FileNotFoundError
        If any required CHR CSV is missing.
    ValueError
        If loaded CHR arrays do not share the same length.
    """
    tags = set(CHR_MAP.values())
    prof = {}

    for tag in tags:
        fp = os.path.join(profile_dir, f"{tag}.csv")
        if not os.path.exists(fp):
            raise FileNotFoundError(f"Missing CHR CSV: {fp}")
        # Expect a single column with hourly values (floats)
        prof[tag] = pd.read_csv(fp, header=None)[0].to_numpy(dtype=float)

    # Basic consistency check: every CHR must have the same number of rows
    lengths = {t: len(v) for t, v in prof.items()}
    if len(set(lengths.values())) != 1:
        raise ValueError(f"Inconsistent CHR lengths (rows per file): {lengths}")

    return prof


def make_household_profile(record: dict, chr_profiles: dict) -> np.ndarray:
    """
    Build a household's hourly load profile by summing CHR components.

    Logic
    -----
    For each of the 7 household keys in CHR_MAP, we:
      1) Read the *count* from the JSON record (negative -> 0).
      2) Multiply the corresponding CHR series by: count * FACTORS[key].
      3) Sum into the final hourly profile.

    Parameters
    ----------
    record : dict
        A single dwelling object from the JSON input. Only the keys in CHR_MAP
        are used; all other fields are ignored.
    chr_profiles : dict[str, np.ndarray]
        Output of `load_chr_profiles()` (pre-loaded CHR series).

    Returns
    -------
    np.ndarray
        1D array of hourly values (same length as CHR CSVs, typically 8,760).

    Notes
    -----
    - Units depend on the CHR CSVs; typically kWh per hour.
    - The combination is linear and has no internal normalization.
    """
    n = len(next(iter(chr_profiles.values())))
    out = np.zeros(n, dtype=float)

    for key, tag in CHR_MAP.items():
        # Count must be a non-negative integer; invalid/missing -> 0
        try:
            count = int(record.get(key, 0))
        except Exception:
            count = 0
        if count < 0:
            count = 0

        if count:
            out += count * FACTORS[key] * chr_profiles[tag]

    return out


# =============================================================================
# Farm profiles (optional route if record['farm'] == True)
# -----------------------------------------------------------------------------
# If `farm` is true but no extra fields are provided, use sensible defaults and
# generate a BDEW SLP scaled by an annual kWh.
# =============================================================================

def make_farm_profile(year: int = 2025, farm_type: str = "l1", ha: float = 1.0) -> np.ndarray:
    
    """ REVISAR LO DE 18_000 """
    
    """
    Generate a farm hourly profile.

    Approach
    --------
    Uses demandlib BDEW standard load profiles (SLPs), scaled to an *annual*
    energy target derived from hectares and a per-hectare intensity.

    Parameters
    ----------
    year : int
        Year for BDEW SLPs.
    farm_type : str
        Simplified farm type key (e.g., 'l1').
    ha : float
        Hectares (size proxy).

    Returns
    -------
    np.ndarray
        1D array of hourly values (resampled hourly from BDEW profile).

    Notes
    -----
    - PER_HA is a placeholder; replace with real value when available.
    - BDEW keys typically use the prefix before '_' to select the sector.
    """
    PER_HA = {"l1": 944}  # kWh/ha/year Extracted from “MANUAL DE BUENAS PRÁCTICAS DE AHORRO Y EFICIENCIA ENERGÉTICA EN EXPLOTACIONES DE VACUNO LECHERO” 
    sector_prefix = {"l1": "l1_dairy_farm"}.get(farm_type, "l1_dairy_farm").split("_")[0]
    annual_kwh = PER_HA.get(farm_type, PER_HA["l1"]) * float(ha)

    df = bdew.ElecSlp(year=year).get_scaled_profiles({sector_prefix: annual_kwh})
    # Ensure a 1D vector of hourly values
    return df.resample("h").sum().to_numpy().ravel()


# =============================================================================
# Commercial profiles
# =============================================================================

def make_commercial_profile(
    year: int = 2025,
    use_id: int | None = None,
    area_sqm: float = 100.0,
    intensity_kwh_per_m2: float | None = None,  # optional override
) -> np.ndarray:
    """
    Generate a commercial hourly load profile based on BDEW scaling by floor area.

    Selection:
      - use_id in {4,5,6}
    Scaling:
      - annual_kwh = intensity_kwh_per_m2 * area_sqm
        (uses PER_SQM[gX] unless 'intensity_kwh_per_m2' is provided)
    """
    # Resolve BDEW key (gX) by numeric id only
    key = COMMERCIAL_USE_MAP.get(use_id, "g0")

    # Sanitize area
    try:
        area = float(area_sqm)
    except Exception:
        area = 0.0
    if area < 0:
        area = 0.0

    intensity = float(intensity_kwh_per_m2) if intensity_kwh_per_m2 is not None else PER_SQM.get(key, PER_SQM["g0"])
    annual_kwh = intensity * area

    df = bdew.ElecSlp(year=year).get_scaled_profiles({key: annual_kwh})
    return df.resample("h").sum().to_numpy().ravel()


# =============================================================================
# Single routing entry point
# =============================================================================

def generate_profile(record: dict, chr_profiles: dict, year: int = 2025) -> np.ndarray:
    """
    Route to the correct generator using the rule:
      - If record['farm'] is True  -> generate farm profile
      - If use_id in {4,5,6}       -> commercial profile
      - Else                       -> generate household profile

    Parameters
    ----------
    record : dict
        A single JSON dwelling. We only need:
          - adults_working_out_of_home
          - adults_working_remotely
          - adults_unemployed
          - students_working
          - students_unemployed
          - children
          - retired_people
          - farm (bool)  # routing flag
    chr_profiles : dict[str, np.ndarray]
        Output of `load_chr_profiles(profile_dir)`.
    year : int
        Year passed to farm profile generation (household does not use it).

    Returns
    -------
    np.ndarray
        1D hourly profile for the dwelling.
    """
    # Compatibility: accept records that still have 'building_use_id'
    if "use_id" not in record and "building_use_id" in record:
        record = dict(record)  # avoid mutating the caller's dict
        record["use_id"] = record["building_use_id"]

    # 1) Farm
    if bool(record.get("farm", False)):
        return make_farm_profile(year=year)

    # 2) Commercial (ids 4,5,6 only)
    use_id = record.get("use_id", None)
    if use_id in (4, 5, 6):
        return make_commercial_profile(
            year=year,
            use_id=use_id,
            area_sqm=record.get("area_sqm", 100.0),
            intensity_kwh_per_m2=record.get("intensity_kwh_per_m2"),  # optional per-building override
        )

    # 3) Household
    return make_household_profile(record, chr_profiles)