def merge_building_assets(context, new_assets):
    """
    Merges new assets into the existing building_asset_context by matching id_temp.

    Parameters
    ----------
    context: dict
        Existing community context with building assets.
    new_assets: dict
        New data containing updated building_energy_asset values.

    Returns
    -------
    dict
        Updated context with merged building energy assets.
    """
    # Index building_asset_context by id_temp for quick access
    # context_dict = {c["id_temp"]: c for c in context.get("building_asset_context") or []}
    context_dict = {c["id_temp"]: c for c in (context.get("building_asset_context") or []) if isinstance(c, dict) and "id_temp" in c}
    list_of_hps = {1, 2, 3, 4, 5, 6, 7, 8, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 41, 61, 62, 63, 64, 65, 66,
                   67, 68, 73}

    # Iterate through the new building energy assets
    for asset in (new_assets.get("building_energy_asset") or []):
        if asset is not None:
            id_temp = asset.get("id_temp")
    
            if id_temp in context_dict:
                # Get the existing building_energy_asset list
                building_energy_assets = context_dict[id_temp].setdefault("building_energy_asset", [])
    
                # Find the matching asset by id_temp
                existing_asset = next((a for a in building_energy_assets if a.get("id_temp") == id_temp), None)
    
                if existing_asset:
                    # Update existing asset fields
                    existing_asset["pmax_scalar"] = asset.get("pmax_scalar", existing_asset.get("pmax_scalar"))
                    existing_asset_system = existing_asset["generation_system"].get("id", 83)
    
                    if "availability_ts" in asset and asset["availability_ts"] is not None:
                        if existing_asset_system in list_of_hps:
                            existing_asset["availability_ts"] = {
                                "value_input1": asset["availability_ts"].get("value_input1", []),
                                "value_input2": asset["availability_ts"].get("value_input2", []),
                                "value_output1": asset["availability_ts"].get("value_output1", []),
                                "value_output2": asset["availability_ts"].get("value_output2", []),
                            }
                        else:
                            existing_asset["availability_ts"] = {
                                "value_output1": asset["availability_ts"].get("value_output1", []),
                                "value_output2": asset["availability_ts"].get("value_output2", []),
                            }
        else:
            print("no change is made in building energy assets")
    return context


def merge_community_assets(context, new_assets):
    """
    Merges new community assets into the existing community_energy_asset by matching id_temp.

    Parameters
    ----------
    context: dict
        Existing community context with community assets.
    new_assets: dict
        New data containing updated community_energy_asset values.

    Returns
    -------
    dict
        Updated context with merged community energy assets.
    """
    # Index community_energy_asset by id_temp for quick access
    context_assets = context.get("community_energy_asset") or []
    context_asset_dict = {asset['id_temp']: asset for asset in context_assets if 'id_temp' in asset}
    list_of_hps = {1, 2, 3, 4, 5, 6, 7, 8, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 41, 61, 62, 63, 64, 65, 66,
                   67, 68, 73}

    # Iterate through the new community energy assets
    for asset in (new_assets.get("community_energy_asset") or []):
        if asset is not None: 
            id_temp = asset.get("id_temp")
    
            if id_temp in context_asset_dict:
                existing_asset = context_asset_dict[id_temp]
                existing_asset_system = existing_asset["generation_system"].get("id", 83)
    
                # Update scalar value
                existing_asset["pmax_scalar"] = asset.get("pmax_scalar", existing_asset.get("pmax_scalar"))
    
                if "availability_ts" not in existing_asset or existing_asset["availability_ts"] is None:
                    existing_asset["availability_ts"] = {
                        "id_temp": None,
                        "name": "Name",
                        "value_input1": [],
                        "value_input2": [],
                        "value_output1": [],
                        "value_output2": [],
                        "testcase": "TC_0",
                    }
    
                if "availability_ts" in asset and asset["availability_ts"] is not None:
                    try:
                        if existing_asset_system in list_of_hps:
                            existing_asset["availability_ts"].update({
                                "value_input1": asset["availability_ts"].get("value_input1", []),
                                "value_input2": asset["availability_ts"].get("value_input2", []),
                                "value_output1": asset["availability_ts"].get("value_output1", []),
                                "value_output2": asset["availability_ts"].get("value_output2", []),
                            })
                        else:
                            existing_asset["availability_ts"].update({
                                "value_output1": asset["availability_ts"].get("value_output1", []),
                                "value_output2": asset["availability_ts"].get("value_output2", []),
                            })
                    except KeyError as e:
                        print(f"KeyError encountered: {e} for asset with id_temp {id_temp}")
        else:
            print("no change is made in building energy assets")
    # Update the context with the merged assets
    context['community_energy_asset'] = context_assets
    return context
#
# # Example usage:
# data = {
#     "id": 1,
#     "name": "Baseline Ispaster",
#     "start_date": "2023-01-01",
#     "timestep_count": 8760,
#     "timestep_duration": 3600000,
#     "creation_date": "2024-11-03",
#     "context_parent": None,
#     "author": "andgab",
#     "description": "This is the baseline of Ispaster, without including building assets and community assets. The data now stored corresponds to the outputs of the City Energy Analyst model",
#     "node": [
#         {
#             "id": 1,
#             "geom": "POINT (-3 41)",
#             "name": "TEST",
#             "context_id": 1,
#             "community_energy_asset_output": [],
#             "community_energy_asset_input": []
#         }
#     ],
#     "building_asset_context": [
#         {
#             "id": 6,
#             "building_energy_asset": []
#         },
#         {
#             "id": 7,
#             "building_energy_asset": []
#         }
#     ]
# }
#
# new_building_assets = {
#     "building_energy_asset": [
#         {
#             "id_temp": 1,
#             "generation_system_id": 83,
#             "pmaxmin_scalar": 0,
#             "availability_ts_id": None,
#             "pmax_scalar": 2,
#             "pmaxmax_scalar": 62.3,
#             "building_asset_context_id": 6,
#             "availability_ts": {
#                 "temp_id": None,
#                 "name": "pv_building_6",
#                 "value_input1": [0.0, 0.05552, 0.18315]
#             }
#         }
#     ]
# }
#
# new_community_assets = {
#     "community_energy_asset": [
#         {
#             "id_temp": 1,
#             "generation_system_id": 79,
#             "pmaxmin_scalar": None,
#             "availability_ts_id": None,
#             "pmax_scalar": None,
#             "pmaxmax_scalar": None,
#             "input_node": {
#                 "id_temp": 1,
#                 "geom": "POINT (-2.5438995325737133 43.362092317437714)",
#                 "name": "GRID"
#             },
#             "output_node": None
#         },
#         {
#             "id_temp": 2,
#             "generation_system_id": 83,
#             "pmaxmin_scalar": 0,
#             "availability_ts_id": None,
#             "pmax_scalar": 60,
#             "pmaxmax_scalar": 100,
#             "input_node": {
#                 "id_temp": 1,
#                 "geom": "POINT (-2.5438995325737133 43.362092317437714)",
#                 "name": "pv_input"
#             },
#             "output_node": {
#                 "id_temp": 1,
#                 "geom": "POINT (-2.5438995325737133 43.362092317437714)",
#                 "name": "pv_output"
#             }
#         }
#     ]
# }
#
# import json
# input_file = r"D:\Documents\localres\backend\localres_api\outputs\SC1_ispaster_pv_on_roofs_output.json"  # Replace with your input JSON file path
#
# with open(input_file, 'r') as file:
#     data = json.load(file)
#
# input_file_ARTELYS = r"D:\Documents\localres\backend\localres_api\outputs\SC1_ispaster_pv_on_roofs_output.json"  # Replace with your input JSON file path
#
# with open(input_file_ARTELYS, 'r') as file:
#     new_info_ARTELYS = json.load(file)
#
#
# # Merge the data and print the result
# merged_data = merge_building_assets(data, new_info_ARTELYS)
# merged_data_2 = merge_community_assets(merged_data, new_comm)
# print('test')
