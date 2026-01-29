from typing import List
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_
from sqlalchemy.orm import Session, joinedload, with_loader_criteria
from geoalchemy2.functions import ST_GeomFromText

from api.constants import SRID
from api.models.models import (
    BuildingStatistics,
    EnergyCarrier,
    BuildingStatisticsProfile,
    BuildingUse,
    Country,
    GenerationSystem,
    GenerationSystemProfile,
    NationalEnergyCarrierProduction
)
from api.models.schemas.baseline import BasicBaselineIn, IntermediateBaseline, IntermediateBaselineIn
from api.models.schemas.context import ContextIn
from api.services.scripts.module_integration import (
    generate_baseline_pathway_intermediate,
    generate_baseline_pathway_simple,
)


def basic_baseline_data(input_data: BasicBaselineIn, db: Session):
    return get_bd_data(input_data, db)


def intermediate_baseline_data(input_data: List[IntermediateBaselineIn], db: Session):
    front_data = transform_data_to_building(front_data)
    building_statistics_profiles, _ = get_intermediate_data(input_data, db)
    return building_statistics_profiles

def transform_data_to_building(input_data: List[IntermediateBaselineIn]):
    buildings = []
    for building in input_data:
        for dwelling in building.dwellings:
            b = IntermediateBaseline(
                geom=building.geom,
                construction_year=building.construction_year,
                subdivision_community=building.subdivision_community,
                subdivision_total=building.subdivision_total,
                occupants=building.occupants,
                building_type_id=building.building_type_id,
                name=building.name,
                building_use_id=dwelling.building_use_id,
                adults_working_out_of_home=dwelling.adults_working_out_of_home,
                adults_working_remotely=dwelling.adults_working_remotely,
                adults_unemployed=dwelling.adults_unemployed,
                students_working=dwelling.students_working,
                students_unemployed=dwelling.students_unemployed,
                children=dwelling.children,
                retired_people=dwelling.retired_people,
                farm=dwelling.farm
            )
            buildings.append(b)
    return buildings

def get_intermediate_data(input_data: List[IntermediateBaseline], db):
    building_statistics_profiles = []
    for building in input_data:
        building_statistics_profile = get_building_statistics_profile(
            db=db,
            country_id=get_country_id(building.geom, db),
            building_use_id=building.building_use_id,
            common_construction_year=building.construction_year,
        )
        if building_statistics_profile:
            building.building_statistics_profile_id = building_statistics_profile.id
        building_statistics_profiles.append(building_statistics_profile)
    return building_statistics_profiles, input_data


def basic_baseline(input_data: BasicBaselineIn, db: Session):
    bd_input_data = get_bd_data(input_data, db)
    baseline, kpis = generate_baseline_pathway_simple(
        data=bd_input_data, front_data=input_data.model_dump()
    )

    return {"baseline": ContextIn.model_validate(baseline), "kpis": kpis}


def intermediate_baseline(front_data: IntermediateBaselineIn, db: Session):
    front_data = transform_data_to_building(front_data)
    bd_input_data, front_data = get_intermediate_data(front_data, db)
    baseline, kpis = generate_baseline_pathway_intermediate(
        data=[jsonable_encoder(bsp) for bsp in bd_input_data],
        front_data=[building.model_dump() for building in front_data],
    )

    return {"baseline": ContextIn.model_validate(baseline), "kpis": kpis}


def get_bd_data(input_data: BasicBaselineIn, db):
    country_id = get_country_id(input_data.location, db)
    building_use_id = get_building_use(input_data.building_use_id, db)

    building_statistics: BuildingStatistics = (
        db.query(BuildingStatistics)
        .options(joinedload(BuildingStatistics.demand_profile_default))
        .filter(
            and_(
                BuildingStatistics.building_use_id == building_use_id,
                BuildingStatistics.country_id == country_id,
            )
        )
        .first()
    )
    building_statistics_profile = get_building_statistics_profile(
        db, country_id, building_use_id, building_statistics.common_construction_year
    )
    return {
        "building_statistics": jsonable_encoder(building_statistics),
        "building_statistics_profile": jsonable_encoder(building_statistics_profile),
    }


def get_building_statistics_profile(
    db, country_id, building_use_id, common_construction_year
):
    building_statistics_profile = (
        db.query(BuildingStatisticsProfile)
        .options(generation_system_profiles(country_id))
        .filter(
            and_(
                BuildingStatisticsProfile.building_use_id == building_use_id,
                BuildingStatisticsProfile.country_id == country_id,
                BuildingStatisticsProfile.construction_year == common_construction_year,
            )
        )
        .first()
    )

    return building_statistics_profile


def generation_system_profile(profile, country_id):
    return (
        joinedload(BuildingStatisticsProfile.generation_system_profile)
        .joinedload(profile)
        .joinedload(GenerationSystem.energy_carrier_input_1)
        .joinedload(EnergyCarrier.national_energy_carrier_production),
        joinedload(BuildingStatisticsProfile.generation_system_profile)
        .joinedload(profile)
        .joinedload(GenerationSystem.energy_carrier_input_2)
        .joinedload(EnergyCarrier.national_energy_carrier_production),
        joinedload(BuildingStatisticsProfile.generation_system_profile)
        .joinedload(profile)
        .joinedload(GenerationSystem.energy_carrier_output_1)
        .joinedload(EnergyCarrier.national_energy_carrier_production),
        joinedload(BuildingStatisticsProfile.generation_system_profile)
        .joinedload(profile)
        .joinedload(GenerationSystem.energy_carrier_output_2)
        .joinedload(EnergyCarrier.national_energy_carrier_production),
        with_loader_criteria(NationalEnergyCarrierProduction, NationalEnergyCarrierProduction.country_id==country_id)
    )


def generation_system_profiles(country_id):
    return (
        generation_system_profile(GenerationSystemProfile.heating_system, country_id),
        generation_system_profile(GenerationSystemProfile.cooling_system, country_id),
        generation_system_profile(GenerationSystemProfile.dhw_system, country_id),
        generation_system_profile(GenerationSystemProfile.electricity_system, country_id),
    )


def get_country_id(location: str, db: Session):
    country: Country = (
        db.query(Country)
        .filter(Country.geom.ST_Contains(ST_GeomFromText(location, SRID)))
        .first()
    )
    if not country:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Country not found for current location",
        )
    return country.id if country.related_country_id is None else country.related_country_id


def get_building_use(building_use_id: int, db: Session):
    building_use: BuildingUse = (
        db.query(BuildingUse).filter(BuildingUse.id == building_use_id).first()
    )
    if not building_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Building Use not found",
        )
    return building_use.id
