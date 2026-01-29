import copy
import re


def _ensure_ts_template(asset: dict) -> None:
    """
    Parameters
    ----------
    asset : dict
        Asset context entry.

    Returns
    -------
    None
        Ensures availability_ts exists and contains value_input1/value_input2/value_output1/value_output2.
    """
    asset.setdefault("availability_ts", {})
    ts = asset["availability_ts"]
    ts.setdefault("value_input1", [])
    ts.setdefault("value_input2", [])
    ts.setdefault("value_output1", [])
    ts.setdefault("value_output2", [])


def _get_generation_system_id(asset: dict):
    """
    Parameters
    ----------
    asset : dict
        Asset context entry.

    Returns
    -------
    int | None
        generation_system id if available.
    """
    if asset.get("generation_system_id") is not None:
        return asset.get("generation_system_id")
    gs = asset.get("generation_system") or {}
    return gs.get("id")


def _is_hp(asset: dict) -> bool:
    """
    Parameters
    ----------
    asset : dict
        Asset context entry.

    Returns
    -------
    bool
        True if the asset is an HP/AC type based on generation_system id.
    """
    return _get_generation_system_id(asset) in (63, 31, 2)


def _carrier_from_bus_label(bus_label: str) -> str:
    """
    Parameters
    ----------
    bus_label : str
        OEMOF bus label.

    Returns
    -------
    str
        Normalized carrier name.
    """
    s = (bus_label or "").lower()
    if "electricity" in s:
        return "electricity"
    if "gas" in s:
        return "gas"
    if "heating_local" in s or "heating" in s:
        return "heating"
    if "dhw_local" in s or "dhw" in s:
        return "dhw"
    if "cooling_local" in s or "cooling" in s:
        return "cooling"
    return "unknown"


def _infer_n_ref_from_context(results_context: dict) -> int:
    """
    Parameters
    ----------
    results_context : dict
        Context that may contain demand profiles or any existing time series.

    Returns
    -------
    int
        Reference length for time series (e.g., 8760). Returns 0 if not found.
    """
    # 1) Try demand profiles
    for bac in results_context.get("building_asset_context", []) or []:
        bd = bac.get("building_demand") or bac.get("building", {}).get("building_demand")
        if isinstance(bd, dict):
            for k in ("electricity_demand", "heating_demand", "dhw_demand", "cooling_demand"):
                arr = bd.get(k)
                if isinstance(arr, list) and len(arr) > 0:
                    return len(arr)

    # 2) Try grid imports if exist
    for bac in results_context.get("building_asset_context", []) or []:
        gi = bac.get("grid_imports") or {}
        for k in ("grid_import_kwh", "gas_import_kwh"):
            arr = gi.get(k)
            if isinstance(arr, list) and len(arr) > 0:
                return len(arr)

    # 3) Try any asset availability_ts already filled (PV/STC)
    for bac in results_context.get("building_asset_context", []) or []:
        for a in bac.get("building_energy_asset", []) or []:
            ts = (a.get("availability_ts") or {})
            for k in ("value_output1", "value_input1", "value_input2"):
                arr = ts.get(k)
                if isinstance(arr, list) and len(arr) > 0:
                    return len(arr)

    for a in results_context.get("community_energy_asset", []) or []:
        ts = (a.get("availability_ts") or {})
        for k in ("value_output1", "value_input1", "value_input2"):
            arr = ts.get(k)
            if isinstance(arr, list) and len(arr) > 0:
                return len(arr)

    return 0


def _fill_hp_zero_series_if_missing(results_context: dict, n_ref: int) -> None:
    """
    Parameters
    ----------
    results_context : dict
        Context updated with results.
    n_ref : int
        Required time series length.

    Returns
    -------
    None
        Ensures HP has value_input2 and value_output1 as arrays (zeros) if missing.
    """
    if n_ref <= 0:
        return

    zeros = [0.0] * n_ref

    for bac in results_context.get("building_asset_context", []) or []:
        for a in bac.get("building_energy_asset", []) or []:
            if not _is_hp(a):
                continue

            _ensure_ts_template(a)
            ts = a["availability_ts"]

            # Electricity input for HP must be stored in input2
            if not isinstance(ts.get("value_input2"), list) or len(ts.get("value_input2")) == 0:
                ts["value_input2"] = zeros

            # Thermal/cooling output is output1 in your current structure
            if not isinstance(ts.get("value_output1"), list) or len(ts.get("value_output1")) == 0:
                ts["value_output1"] = zeros

            # Air stays empty by design:
            # ts["value_input1"] remains []


def populate_results_in_context(oemof_results, original_context):
    """
    Parameters
    ----------
    oemof_results : dict
        OEMOF optimization results (flows, investments).
    original_context : dict
        Input context used to build the model.

    Returns
    -------
    dict
        A new context including optimal capacities and time series results.
    """
    print("\nStarting context update with OEMOF results...")

    results_context = copy.deepcopy(original_context)

    # Create quick-access map (asset name -> asset dict)
    building_assets_map = {}

    for building in results_context.get("building_asset_context", []):
        for asset in building.get("building_energy_asset", []):
            building_assets_map[asset["name"]] = asset

    # Use ONLY building assets
    all_assets_map = building_assets_map

    # 2) Store optimal installed capacities for investment assets (pmax_scalar)
    print("   Phase 1: Saving optimal installed capacities...")
    for (node, _), data in oemof_results.items():
        if "invest" in data.get("scalars", {}) and data["scalars"]["invest"] > 1e-5:
            label = getattr(node, "label", None)
            label = str(label) if label is not None else None
            if not label:
                continue
            value = round(float(data["scalars"]["invest"]), 6)
            # asset = all_assets_map.get(label)
            asset = all_assets_map.get(label)
            if asset:
                asset["pmax_scalar"] = value

    # 3) Store time series (flows)
    print("\n   Phase 2: Storing time series into availability_ts...")

    for (origin, dest), data in oemof_results.items():
        sequences = data.get("sequences", {})
        if "flow" not in sequences:
            continue

        flow_series = (
            sequences["flow"]
            .fillna(0.0)
            .round(6)
            .astype(float)
            .to_list()
        )

        # origin_label = getattr(origin, "label", None)
        # dest_label = getattr(dest, "label", None)
        origin_label = getattr(origin, "label", None)
        dest_label = getattr(dest, "label", None)
        origin_label = str(origin_label) if origin_label is not None else None
        dest_label = str(dest_label) if dest_label is not None else None
        
        if origin_label is None or dest_label is None:
            continue

        # IMPORTANT: here we only store non-zero flows (to avoid overwriting with zeros),
        # but later we fill HP with zeros if it is missing.
        if max((abs(v) for v in flow_series), default=0.0) < 1e-9:
            continue

        # (a) Output of an asset (asset -> bus)
        origin_asset = all_assets_map.get(origin_label)
        if origin_asset:
            _ensure_ts_template(origin_asset)
            origin_asset["availability_ts"]["value_output1"] = flow_series

        # (b) Input to an asset (bus -> asset)
        dest_asset = all_assets_map.get(dest_label)
        if dest_asset:
            _ensure_ts_template(dest_asset)
            bus_carrier = _carrier_from_bus_label(origin_label)

            # Rule: HP electricity must be stored in value_input2; air remains empty
            if _is_hp(dest_asset) and bus_carrier == "electricity":
                dest_asset["availability_ts"]["value_input2"] = flow_series
            else:
                dest_asset["availability_ts"]["value_input1"] = flow_series

        # (c) Grid imports
        match_grid = re.search(r"^(Electricity|Gas)_Grid_Source_(\d+)", origin_label)
        if match_grid:
            carrier_type, building_id_str = match_grid.groups()
            building_id = int(building_id_str)

            for building in results_context.get("building_asset_context", []):
                if building.get("building", {}).get("id") == building_id:
                    building.setdefault("grid_imports", {})
                    key = "grid_import_kwh" if carrier_type == "Electricity" else "gas_import_kwh"
                    building["grid_imports"][key] = flow_series

        # (d) Excess energy
        m = re.match(
            r"^Excess_(?P<carrier>[A-Za-z]+)_(?P<scope>Community|Building)(?:_(?P<bid>\d+))?$",
            dest_label
        )

        carrier = scope = bid = None
        if m:
            g = m.groupdict()
            carrier = g["carrier"]
            scope = g["scope"]
            bid = g.get("bid")
        else:
            m2 = re.match(r"^Excess_(?P<short>(Heat|DHW|Cool))_(?P<bid>\d+)$", dest_label)
            if m2:
                g2 = m2.groupdict()
                carrier_map = {"Heat": "heating", "DHW": "dhw", "Cool": "cooling"}
                carrier = carrier_map.get(g2["short"], g2["short"].lower())
                scope = "Building"
                bid = g2["bid"]

        if carrier and scope:
            key_name = f"{carrier.lower()}_excess_kwh"
            if scope == "Community":
                results_context.setdefault("community_excess", {})[key_name] = flow_series
            elif scope == "Building" and bid is not None:
                building_id = int(bid)
                for building in results_context.get("building_asset_context", []):
                    if building.get("building", {}).get("id") == building_id:
                        building.setdefault("excess", {})[key_name] = flow_series
                        break

    # 4) Ensure HP has arrays even if it never operated (store zeros)
    n_ref = _infer_n_ref_from_context(results_context)
    _fill_hp_zero_series_if_missing(results_context, n_ref=n_ref)

    print("Context successfully updated with simulation results.")
    return results_context



# def _ensure_ts_template(asset_dict):
#     """
#     Ensures SC1-compatible availability_ts structure on an asset.

#     Parameters:
#         asset_dict (dict): Asset dictionary to be patched in place.

#     Returns:
#         dict: The same asset dictionary with a completed 'availability_ts'.
#     """
#     asset_dict.setdefault("availability_ts", {})
#     ts = asset_dict["availability_ts"]

#     # SC1 uses 'temp_id' (not 'id_temp') inside availability_ts
#     if "temp_id" not in ts:
#         ts["temp_id"] = None

#     ts.setdefault("name", f"ts_{asset_dict.get('name', 'asset')}")
#     ts.setdefault("value_input1", [])
#     ts.setdefault("value_input2", [])
#     ts.setdefault("value_output1", [])
#     ts.setdefault("value_output2", [])

#     return asset_dict


# def _ensure_sc1_building_ids(results_context):
#     """
#     Ensures SC1-compatible temp ids in building_asset_context.

#     Parameters:
#         results_context (dict): Context dictionary to be patched in place.

#     Returns:
#         dict: The same context with 'id_temp' and 'building_consumption_id_temp' added where missing.
#     """
#     bac_list = results_context.get("building_asset_context") or []
#     if not isinstance(bac_list, list):
#         return results_context

#     used = set()
#     counter = 1

#     for bac in bac_list:
#         if not isinstance(bac, dict):
#             continue

#         # Prefer keeping existing id_temp if present
#         if bac.get("id_temp") is None:
#             # If SC1-like building_id exists use it to keep a stable link; else fallback to sequential
#             candidate = bac.get("building_id")
#             if candidate is None:
#                 candidate = counter
#                 counter += 1

#             # Ensure uniqueness
#             if candidate in used:
#                 candidate = max(used) + 1 if used else counter

#             bac["id_temp"] = candidate

#         used.add(bac["id_temp"])

#         # SC1 expects building_consumption_id_temp at building block level
#         bac.setdefault("building_consumption_id_temp", bac["id_temp"])

#         # Also ensure assets have the SC1 availability_ts template
#         for asset in bac.get("building_energy_asset", []) or []:
#             if isinstance(asset, dict):
#                 _ensure_ts_template(asset)

#     # Community assets also should have a full availability_ts template
#     for asset in results_context.get("community_energy_asset", []) or []:
#         if isinstance(asset, dict):
#             _ensure_ts_template(asset)

#     return results_context


# def populate_results_in_context(oemof_results, original_context):
#     """
#     Update the context with the optimization results.

#     Plain explanation for energy engineers
#     --------------------------------------
#     - "oemof_results" is the output of the optimization (flows, sizes).
#     - "original_context" is the input description of the community/buildings.
#     - We copy the context and fill in real values (sizes and time series).
#     - We also save the grid imports and the energy that ends up as "excess".

#     What gets written back
#     ----------------------
#     • For each investment asset:
#         - pmax_scalar: the optimal installed capacity.
#     • For each asset (when there is a flow to/from it):
#         - availability_ts.value_output1: its output time series (kWh).
#         - availability_ts.value_input1: its input time series (kWh).
#     • For each building:
#         - grid_imports.grid_import_kwh: electricity imports (kWh).
#         - grid_imports.gas_import_kwh: gas imports (kWh).
#     • For community / building excess:
#         - community_excess.<carrier>_excess_kwh (e.g., elec_excess_kwh)
#         - building.excess.<carrier>_excess_kwh (e.g., heating_excess_kwh)

#     Returns
#     -------
#     dict : a new context with results included.
#     """
#     print("\nStarting context update with OEMOF results...")

#     # Work on a copy so we never alter the original input by mistake.
#     results_context = copy.deepcopy(original_context)
#     results_context = _ensure_sc1_building_ids(results_context)
#     # -------------------------------------------------------------------------
#     # 1) Create quick-access maps from asset names to their entries in context.
#     #    This lets us find the right asset immediately when we see its label
#     #    in the OEMOF results.
#     # -------------------------------------------------------------------------
#     building_assets_map = {}
#     for building in results_context.get("building_asset_context", []):
#         for asset in building.get("building_energy_asset", []):
#             building_assets_map[asset["name"]] = asset

#     community_assets_map = {
#         asset["name"]: asset for asset in results_context.get("community_energy_asset", [])
#     }

#     # One lookup for any asset by its label/name.
#     all_assets_map = {**building_assets_map, **community_assets_map}

#     # -------------------------------------------------------------------------
#     # 2) Store optimal installed capacities for investment assets (pmax_scalar).
#     #    OEMOF puts the chosen size under "scalars" → "invest".
#     #    We only save it if it is larger than a very small threshold.
#     # -------------------------------------------------------------------------
#     print("   Phase 1: Saving optimal installed capacities...")
#     for (node, _), data in oemof_results.items():
#         if 'invest' in data.get('scalars', {}) and data['scalars']['invest'] > 1e-5:
#             label = node.label
#             value = round(data['scalars']['invest'], 4)
#             asset = all_assets_map.get(label)
#             if asset:
#                 asset["pmax_scalar"] = value
#                 print(f"    → Stored pmax_scalar for: {label} → {value:.2f} kW")

#     # -------------------------------------------------------------------------
#     # 3) Save input/output time series for assets and record grid imports.
#     #    We read each flow from OEMOF, clean it, and place it in the right
#     #    part of the context so it can be used by KPI or plotting tools.
#     # -------------------------------------------------------------------------
#     print("\n   Phase 2: Storing time series into availability_ts...")
#     for (origin, dest), data in oemof_results.items():
#         if 'flow' not in data.get('sequences', {}): # OEMOF gives time series under "sequences" → "flow".
#             continue

#         # Convert to a clean python list of floats (no NaN).
#         flow_series = (data['sequences']['flow']
#                .fillna(0.0)        # <- avoid NaN in JSON
#                .round(4)
#                .astype(float)
#                .to_list())

#         # Skip series that are basically zero everywhere.
#         if sum(abs(v) for v in flow_series) < 1:
#             continue

#         origin_label = origin.label
#         dest_label = dest.label

#         # (a) Output of an asset (e.g., PV → electricity bus).
#         origin_asset = all_assets_map.get(origin_label)
#         if origin_asset:
#             _ensure_ts_template(origin_asset)
#             origin_asset["availability_ts"]["value_output1"] = flow_series
#             print(f"    → Stored value_output1 for: {origin_label}")

#         # (b) Input to an asset (e.g., electricity → heat pump).
#         dest_asset = all_assets_map.get(dest_label)
#         if dest_asset:
#             _ensure_ts_template(dest_asset)
#             dest_asset["availability_ts"]["value_output1"] = flow_series
#             print(f"    → Stored value_input1 for: {dest_label}")

#         # (c) Electricity or gas imports from the grid to a particular building.
#         #     We detect labels like "Electricity_Grid_Source_354" or "Gas_Grid_Source_12".
#         match_grid = re.search(r"^(Electricity|Gas)_Grid_Source_(\d+)", origin_label)
#         if match_grid:
#             carrier_type, building_id_str = match_grid.groups()
#             building_id = int(building_id_str)

#             # Find the right building block and save the series.
#             for building in results_context.get("building_asset_context", []):
#                 if building["building"]["id"] == building_id:
#                     if "grid_imports" not in building:
#                         building["grid_imports"] = {}
#                     key = "grid_import_kwh" if carrier_type == "Electricity" else "gas_import_kwh"
#                     building["grid_imports"][key] = flow_series
#                     print(f"    → Stored {key} for building {building_id}")

#         # (d) Excess energy (community or building).
#         #     We support two naming styles:
#         #       • Style A: "Excess_Elec_Community", "Excess_Heating_Building_357"
#         #       • Style B (legacy thermal): "Excess_Heat_354", "Excess_DHW_354"
#         m = re.match(
#             r"^Excess_(?P<carrier>[A-Za-z]+)_(?P<scope>Community|Building)(?:_(?P<bid>\d+))?$",
#             dest_label
#         )

#         carrier = scope = bid = None
#         if m:
#             g = m.groupdict()
#             carrier = g["carrier"]
#             scope = g["scope"]
#             bid = g.get("bid")
#         else:
#             # Style B (legacy thermal per-building without scope keyword):
#             #   - "Excess_Heat_354"
#             #   - "Excess_DHW_354"
#             #   - "Excess_Cool_354"
#             m2 = re.match(r"^Excess_(?P<short>(Heat|DHW|Cool))_(?P<bid>\d+)$", dest_label)
#             if m2:
#                 g2 = m2.groupdict()
#                 # Map short carrier to normalized name
#                 short = g2["short"]
#                 carrier_map = {"Heat": "heating", "DHW": "dhw", "Cool": "cooling"}
#                 carrier = carrier_map.get(short, short.lower())
#                 scope = "Building"
#                 bid = g2["bid"]

#         # If we identified an excess flow, store it in the right place.
#         if carrier and scope:
#             key_name = f"{carrier.lower()}_excess_kwh"  # elec_excess_kwh, heating_excess_kwh, dhw_excess_kwh, cooling_excess_kwh
#             if scope == "Community":
#                 results_context.setdefault("community_excess", {})[key_name] = flow_series
#                 print(f"    → Stored community excess: {key_name}")
#             elif scope == "Building" and bid is not None:
#                 building_id = int(bid)
#                 for building in results_context.get("building_asset_context", []):
#                     if building.get("building", {}).get("id") == building_id or building.get("building_id") == building_id:
#                         building.setdefault("excess", {})[key_name] = flow_series
#                         print(f"    → Stored building {building_id} excess: {key_name}")
#                         break

#     print("Context successfully updated with simulation results.")
#     return results_context


# def truncate_large_lists_in_json(input_path, output_path, max_len=12):
#     """
#     Make a lighter copy of a JSON file by shortening long numeric lists.

#     Why this is useful
#     ------------------
#     Some arrays (time series) can have thousands of values. For a quick check
#     or to send a small example, we sometimes keep only the first few numbers.

#     Parameters
#     ----------
#     input_path : str
#         Path to the original JSON.
#     output_path : str
#         Where to write the shortened JSON.
#     max_len : int
#         Maximum kept length for numeric lists (default: 12).

#     Result
#     ------
#     Writes a trimmed JSON file with the same structure, just shorter arrays.
#     """

#     import json

#     def truncate(obj):
#         # If it is a list of numbers and too long → cut it.
#         if isinstance(obj, list):
#             if len(obj) > max_len and all(isinstance(i, (int, float)) for i in obj):
#                 return obj[:max_len]
#             else:
#                 # Otherwise, keep going inside the list.
#                 return [truncate(i) for i in obj]
#         # If it is a dictionary, apply truncation to each value.
#         elif isinstance(obj, dict):
#             return {k: truncate(v) for k, v in obj.items()}
#         # Numbers or strings are returned as they are.
#         else:
#             return obj

#     # Read the original JSON.
#     with open(input_path, 'r') as f:
#         data = json.load(f)

#     # Create the shortened version.
#     truncated_data = truncate(data)

#     # Save the new JSON.
#     with open(output_path, 'w') as f:
#         json.dump(truncated_data, f, indent=2)

#     print(f"Truncated structure written to: {output_path}")


