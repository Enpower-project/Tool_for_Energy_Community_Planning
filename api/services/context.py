import json
from typing import List
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from geoalchemy2.shape import to_shape
from geoalchemy2.elements import WKBElement
from fastapi.encoders import jsonable_encoder

from api.services.scripts.module_integration import calculate_indicators
from api.models.schemas.context import ContextIn
from api.models.models import (
    Building,
    BuildingAssetContext,
    BuildingConsumption,
    BuildingEnergyAsset,
    CommunityEnergyAsset,
    DemandProfile,
    Context,
    EnergyCarrier,
    GenerationSystem,
    GenerationSystemProfile,
    Node
)

def create_baseline(input_data: ContextIn, db: Session, author:str):
    try:
        context = Context(**input_data.model_dump(exclude=["building_asset_context"]))
        context.author = author
        for data in input_data.building_asset_context:
            building_asset_context = BuildingAssetContext(
                **data.model_dump(exclude=["building", "building_consumption"])
            )
            building_asset_context.building = Building(**data.building.model_dump(exclude=["demandprofile"]))
            building_asset_context.building.demandprofile = DemandProfile(**data.building.demandprofile.model_dump())
            building_asset_context.building_consumption = BuildingConsumption(
                **data.building_consumption.model_dump()
            )
            context.building_asset_context.append(building_asset_context)

        db.add(context)
        db.commit()
        db.refresh(context)
        return context

    except Exception as ex:
        print(repr(ex))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating DB",
        )


def get_baseline_context_list(db: Session) -> List[Context]:
    building_geometries_subquery = (
        db.query(
            BuildingAssetContext.context_id,
            func.ST_Collect(Building.geom).label("collected_geom"),
        )
        .join(Building, Building.id == BuildingAssetContext.building_id)
        .group_by(BuildingAssetContext.context_id)
    ).subquery()

    context_list_db = (
        db.query(
            Context.id,
            Context.name,
            Context.start_date,
            Context.timestep_count,
            Context.timestep_duration,
            Context.author,
            Context.creation_date,
            Context.description,
            Context.context_parent,
            building_geometries_subquery.c.collected_geom,
            func.ST_Centroid(building_geometries_subquery.c.collected_geom).label(
                "geom"
            ),
        )
        .join(
            building_geometries_subquery,
            Context.id == building_geometries_subquery.c.context_id,
        )
        .order_by(Context.creation_date.desc())
        .all()
    )

    return context_list_db


def get_baseline_by_id_context(id: int, db: Session):
    context_db = db.query(Context).filter(Context.id == id).first()
    if context_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context not found",
        )
    return context_db

def delete_baseline_by_id_context(id: int, db: Session, author:str):
    context_db = db.query(Context).filter(Context.id == id).first()
    
    if context_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context not found",
        )
    
    if(author != context_db.author):
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )

    db.delete(context_db) 
    db.commit() 
    return context_db

def rename_context_by_id(id: int, db: Session, author:str, name:str):
    context_db = db.query(Context).filter(Context.id == id).first()
    
    if context_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context not found",
        )
    
    if(author != context_db.author):
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )

    context_db.name = name
    db.commit() 
    db.refresh(context_db)

    return context_db

def get_alternatives_list(id: int, db: Session):    
    building_geometries_subquery = (
        db.query(
            BuildingAssetContext.context_id,
            func.ST_Collect(Building.geom).label("collected_geom"),
        )
        .join(Building, Building.id == BuildingAssetContext.building_id)
        .group_by(BuildingAssetContext.context_id)
    ).subquery()

    context_list_db = (
        db.query(
            Context.id,
            Context.name,
            Context.start_date,
            Context.timestep_count,
            Context.timestep_duration,
            Context.author,
            Context.creation_date,
            Context.description,
            Context.context_parent,
            building_geometries_subquery.c.collected_geom,
            func.ST_Centroid(building_geometries_subquery.c.collected_geom).label(
                "geom"
            ),
        )
        .join(
            building_geometries_subquery,
            Context.id == building_geometries_subquery.c.context_id,
        )
        .filter(Context.context_parent == id)
        .order_by(Context.creation_date.desc())
        .all()
    )

    return context_list_db

def get_context(id: int, db: Session):
    context = (
        db.query(Context)
            .filter(Context.id == id).options(
                # joinedload(Context.node)
                #     .joinedload(Node.community_energy_asset_input),                
                # joinedload(Context.node)
                #     .joinedload(Node.community_energy_asset_output),
                join_system_types_community(),
                join_energy_carriers_community(),
                joinedload(Context.building_asset_context)
                    .subqueryload(BuildingAssetContext.building_consumption),
                # joinedload(Context.building_asset_context)
                #     .joinedload(BuildingAssetContext.building_energy_asset),
                join_system_types_building(),
                join_energy_carriers_building(),
                join_multi_time_series(),
                joinedload(Context.building_asset_context)
                    .joinedload(BuildingAssetContext.building),
                join_system_types(),
                join_energy_carriers()
            )
            .first()
    )

    if context is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Context not found")
    
    for node in context.node:
        if(isinstance(node.geom, WKBElement)):
            node.geom = to_shape(node.geom).wkt

    for building_asset_context in context.building_asset_context:
        if(isinstance(building_asset_context.building.geom, WKBElement)):
            building_asset_context.building.geom = to_shape(building_asset_context.building.geom).wkt
    kpis = calculate_indicators(jsonable_encoder(context))

    return {"context": context, "kpis": kpis}

def join_system_type_community(inputoutput):
    return (
        join_generation_system_community(inputoutput)
            .joinedload(GenerationSystem.system_type)
    )

def join_system_types_community():
    return (
        join_system_type_community(Node.community_energy_asset_input),
        join_system_type_community(Node.community_energy_asset_output)
    )


def join_generation_system_community(inputoutput):
    return (
        joinedload(Context.node)
            .joinedload(inputoutput)
                .joinedload(CommunityEnergyAsset.generation_system)
    )

def join_energy_carrier_community(inputoutput, energy_carrier):
    return (
        join_generation_system_community(inputoutput)
            .joinedload(energy_carrier)
                .joinedload(EnergyCarrier.national_energy_carrier_production)
    )


def join_inner_energy_carriers_community(inputoutput):
    return (
        join_energy_carrier_community(inputoutput, GenerationSystem.energy_carrier_input_1),
        join_energy_carrier_community(inputoutput, GenerationSystem.energy_carrier_input_2),
        join_energy_carrier_community(inputoutput, GenerationSystem.energy_carrier_output_1),
        join_energy_carrier_community(inputoutput, GenerationSystem.energy_carrier_output_2),
    )

def join_energy_carriers_community():
    return(
        join_inner_energy_carriers_community(Node.community_energy_asset_input),
        join_inner_energy_carriers_community(Node.community_energy_asset_output)
    )

def join_system_types_building():
    return(
        joinedload(Context.building_asset_context)
            .joinedload(BuildingAssetContext.building_energy_asset)
                .joinedload(BuildingEnergyAsset.generation_system)
                    .joinedload(GenerationSystem.system_type)
    )

def join_energy_carrier_building(energy_carrier):
    return (
        joinedload(Context.building_asset_context)
            .joinedload(BuildingAssetContext.building_energy_asset)
                .joinedload(BuildingEnergyAsset.generation_system)
                    .joinedload(energy_carrier)
                        .joinedload(EnergyCarrier.national_energy_carrier_production)
    )

def join_energy_carriers_building():
    return (
        join_energy_carrier_building(GenerationSystem.energy_carrier_input_1),
        join_energy_carrier_building(GenerationSystem.energy_carrier_input_2),
        join_energy_carrier_building(GenerationSystem.energy_carrier_output_1),
        join_energy_carrier_building(GenerationSystem.energy_carrier_output_2),
    )

def join_multi_time_series():
    return (
        joinedload(Context.building_asset_context)
            .joinedload(BuildingAssetContext.building_energy_asset)
                .subqueryload(BuildingEnergyAsset.availability_ts)
    )

def join_generation_system_profile(generation_system_profile):
    return (
        joinedload(Context.building_asset_context)
            .joinedload(BuildingAssetContext.generation_system_profile)
                .joinedload(generation_system_profile)
    )

def join_system_type(generation_system_profile):
    return (
        join_generation_system_profile(generation_system_profile)
            .joinedload(GenerationSystem.system_type)
    )

def join_system_types():
    return (
        join_system_type(GenerationSystemProfile.electricity_system),
        join_system_type(GenerationSystemProfile.heating_system),
        join_system_type(GenerationSystemProfile.cooling_system),
        join_system_type(GenerationSystemProfile.dhw_system)
    )

def join_energy_carrier(generation_system_profile, energy_carrier):
    return (
        join_generation_system_profile(generation_system_profile)
            .joinedload(energy_carrier)
                .joinedload(EnergyCarrier.national_energy_carrier_production)
    )

def join_inner_energy_carriers(generation_system_profile):
    return (
        join_energy_carrier(generation_system_profile, GenerationSystem.energy_carrier_input_1),
        join_energy_carrier(generation_system_profile, GenerationSystem.energy_carrier_input_2),
        join_energy_carrier(generation_system_profile, GenerationSystem.energy_carrier_output_1),
        join_energy_carrier(generation_system_profile, GenerationSystem.energy_carrier_output_2),
    )

def join_energy_carriers():
    return (
        join_inner_energy_carriers(GenerationSystemProfile.electricity_system),
        join_inner_energy_carriers(GenerationSystemProfile.heating_system),
        join_inner_energy_carriers(GenerationSystemProfile.cooling_system),
        join_inner_energy_carriers(GenerationSystemProfile.dhw_system)
    )