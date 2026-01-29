from typing import List, Optional

from sqlalchemy import ARRAY, Boolean, CheckConstraint, Column, Date, Double, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, Sequence, String, Table, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.orm.base import Mapped

from geoalchemy2 import Geometry

Base = declarative_base()
metadata = Base.metadata


class BuildingConsumption(Base):
    __tablename__ = 'building_consumption'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='building_consumption_pk'),
    )

    id = mapped_column(Integer)
    elec_consumption = mapped_column(ARRAY(Double(precision=53)))
    heat_consumption = mapped_column(ARRAY(Double(precision=53)))
    cool_consumption = mapped_column(ARRAY(Double(precision=53)))
    dhw_consumption = mapped_column(ARRAY(Double(precision=53)))

    building_asset_context: Mapped[List['BuildingAssetContext']] = relationship('BuildingAssetContext', uselist=True, back_populates='building_consumption')


class BuildingUse(Base):
    __tablename__ = 'building_use'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='building_use_pk'),
    )

    id = mapped_column(Integer)
    name = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=False)
    sort = mapped_column(Integer, nullable=False)
    icon = mapped_column(String(30))
    name_translate = mapped_column(String(60))

    building: Mapped[List['Building']] = relationship('Building', uselist=True, back_populates='building_use')
    building_statistics: Mapped[List['BuildingStatistics']] = relationship('BuildingStatistics', uselist=True, back_populates='building_use')
    building_statistics_profile: Mapped[List['BuildingStatisticsProfile']] = relationship('BuildingStatisticsProfile', uselist=True, back_populates='building_use')


class Context(Base):
    __tablename__ = 'context'
    __table_args__ = (
        ForeignKeyConstraint(['context_parent'], ['context.id'], name='context_context_fk'),
        PrimaryKeyConstraint('id', name='context_pk')
    )

    id = mapped_column(Integer)
    name = mapped_column(String, nullable=False)
    start_date = mapped_column(Date, nullable=False)
    timestep_count = mapped_column(Integer, nullable=False)
    timestep_duration = mapped_column(Integer, nullable=False)
    author = mapped_column(String, nullable=False)
    creation_date = mapped_column(Date, nullable=False)
    description = mapped_column(String, nullable=False)
    context_parent = mapped_column(Integer)

    context: Mapped[Optional['Context']] = relationship('Context', remote_side=[id], back_populates='context_reverse')
    context_reverse: Mapped[List['Context']] = relationship('Context', uselist=True, remote_side=[context_parent], back_populates='context')
    node: Mapped[List['Node']] = relationship('Node', uselist=True, back_populates='context')
    transformation_action: Mapped[List['TransformationAction']] = relationship('TransformationAction', uselist=True, back_populates='context')
    building_asset_context: Mapped[List['BuildingAssetContext']] = relationship('BuildingAssetContext', uselist=True, back_populates='context')


class Country(Base):
    __tablename__ = 'country'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='country_pk'),
    )

    id = mapped_column(Integer)
    name = mapped_column(String, nullable=False)
    code = mapped_column(String, nullable=False)
    cluster = mapped_column(String, nullable=False)
    geom = mapped_column(Geometry)
    related_country_id = mapped_column(Integer)

    building_statistics: Mapped[List['BuildingStatistics']] = relationship('BuildingStatistics', uselist=True, back_populates='country')
    country_statistics: Mapped[List['CountryStatistics']] = relationship('CountryStatistics', uselist=True, back_populates='country')
    national_energy_carrier_production: Mapped[List['NationalEnergyCarrierProduction']] = relationship('NationalEnergyCarrierProduction', uselist=True, back_populates='country')
    building_statistics_profile: Mapped[List['BuildingStatisticsProfile']] = relationship('BuildingStatisticsProfile', uselist=True, back_populates='country')


class DemandProfile(Base):
    __tablename__ = 'demand_profile'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='demand_profile_pkey'),
    )

    id = mapped_column(Integer, Sequence('demand_profile_id_seq1'))
    electricity_demand = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    heating_demand = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    cooling_demand = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    dhw_demand = mapped_column(ARRAY(Double(precision=53)), nullable=False)

    building: Mapped[List['Building']] = relationship('Building', uselist=True, back_populates='demandprofile')


class DemandProfileDefault(Base):
    __tablename__ = 'demand_profile_default'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='demand_profile_pk'),
    )

    id = mapped_column(Integer, Sequence('demand_profile_id_seq'))
    heating_demand = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    cooling_demand = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    dhw_demand = mapped_column(ARRAY(Double(precision=53)), nullable=False)

    building_statistics: Mapped[List['BuildingStatistics']] = relationship('BuildingStatistics', uselist=True, back_populates='demand_profile_default')


class EnergyCarrier(Base):
    __tablename__ = 'energy_carrier'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='energy_carrier_pk'),
    )

    id = mapped_column(Integer)
    name = mapped_column(String, nullable=False)
    final = mapped_column(Boolean, nullable=False)

    generation_system: Mapped[List['GenerationSystem']] = relationship('GenerationSystem', uselist=True, foreign_keys='[GenerationSystem.energy_carrier_input_1_id]', back_populates='energy_carrier_input_1')
    generation_system_: Mapped[List['GenerationSystem']] = relationship('GenerationSystem', uselist=True, foreign_keys='[GenerationSystem.energy_carrier_input_2_id]', back_populates='energy_carrier_input_2')
    generation_system1: Mapped[List['GenerationSystem']] = relationship('GenerationSystem', uselist=True, foreign_keys='[GenerationSystem.energy_carrier_output_1_id]', back_populates='energy_carrier_output_1')
    generation_system2: Mapped[List['GenerationSystem']] = relationship('GenerationSystem', uselist=True, foreign_keys='[GenerationSystem.energy_carrier_output_2_id]', back_populates='energy_carrier_output_2')
    national_energy_carrier_production: Mapped[List['NationalEnergyCarrierProduction']] = relationship('NationalEnergyCarrierProduction', uselist=True, back_populates='energy_carrier')


t_geography_columns = Table(
    'geography_columns', metadata,
    Column('f_table_catalog', String),
    Column('f_table_schema', String),
    Column('f_table_name', String),
    Column('f_geography_column', String),
    Column('coord_dimension', Integer),
    Column('srid', Integer),
    Column('type', Text)
)


t_geometry_columns = Table(
    'geometry_columns', metadata,
    Column('f_table_catalog', String(256)),
    Column('f_table_schema', String),
    Column('f_table_name', String),
    Column('f_geometry_column', String),
    Column('coord_dimension', Integer),
    Column('srid', Integer),
    Column('type', String(30))
)


class Member(Base):
    __tablename__ = 'member'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='member_pkey'),
    )

    id = mapped_column(Integer)
    number_of_family_members = mapped_column(Integer)
    number_of_people_working = mapped_column(Integer)
    number_of_people_students = mapped_column(Integer)
    number_of_people_retired = mapped_column(Integer)
    number_of_toddler = mapped_column(Integer)
    number_of_children = mapped_column(Integer)
    number_of_adult_young = mapped_column(Integer)
    number_of_adult = mapped_column(Integer)
    number_of_senior = mapped_column(Integer)

    building: Mapped['Building'] = relationship('Building', secondary='building_member', back_populates='member')


class MultiTimeSerie(Base):
    __tablename__ = 'multi_time_serie'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='multi_time_serie_pk'),
    )

    id = mapped_column(Integer)
    name = mapped_column(String, nullable=False)
    testcase = mapped_column(String, nullable=False)
    value_input1 = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    value_input2 = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    value_output1 = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    value_output2 = mapped_column(ARRAY(Double(precision=53)), nullable=False)

    time_serie: Mapped[List['TimeSerie']] = relationship('TimeSerie', uselist=True, back_populates='multi_time_serie')
    community_energy_asset: Mapped[List['CommunityEnergyAsset']] = relationship('CommunityEnergyAsset', uselist=True, back_populates='availability_ts')
    building_energy_asset: Mapped[List['BuildingEnergyAsset']] = relationship('BuildingEnergyAsset', uselist=True, back_populates='availability_ts')


class SpatialRefSys(Base):
    __tablename__ = 'spatial_ref_sys'
    __table_args__ = (
        CheckConstraint('srid > 0 AND srid <= 998999', name='spatial_ref_sys_srid_check'),
        PrimaryKeyConstraint('srid', name='spatial_ref_sys_pkey')
    )

    srid = mapped_column(Integer)
    auth_name = mapped_column(String(256))
    auth_srid = mapped_column(Integer)
    srtext = mapped_column(String(2048))
    proj4text = mapped_column(String(2048))


class SystemType(Base):
    __tablename__ = 'system_type'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='system_type_pk'),
    )

    id = mapped_column(Integer)
    name = mapped_column(String, nullable=False)

    generation_system: Mapped[List['GenerationSystem']] = relationship('GenerationSystem', uselist=True, back_populates='system_type')


class Building(Base):
    __tablename__ = 'building'
    __table_args__ = (
        ForeignKeyConstraint(['building_use_id'], ['building_use.id'], name='building_building_use_fk'),
        ForeignKeyConstraint(['demandprofile_id'], ['demand_profile.id'], name='building_demandprofile_fk'),
        PrimaryKeyConstraint('id', name='building_pk')
    )

    id = mapped_column(Integer)
    geom = mapped_column(Geometry, nullable=False)
    area_conditioned = mapped_column(Double(53))
    height = mapped_column(Double(53))
    construction_year = mapped_column(Double(53))
    demandprofile_id = mapped_column(Integer)
    building_use_id = mapped_column(Integer)
    subdivision_community = mapped_column(Integer)
    subdivision_total = mapped_column(Integer)
    occupants = mapped_column(Integer)
    adults_working_out_of_home = mapped_column(Integer)
    adults_working_remotely = mapped_column(Integer)
    adults_unemployed = mapped_column(Integer)
    students_working = mapped_column(Integer)
    students_unemployed = mapped_column(Integer)
    children = mapped_column(Integer)
    retired_people = mapped_column(Integer)
    farm = mapped_column(Boolean)
    building_type_id = mapped_column(Integer, nullable=False)

    building_use: Mapped[Optional['BuildingUse']] = relationship('BuildingUse', back_populates='building')
    demandprofile: Mapped[Optional['DemandProfile']] = relationship('DemandProfile', back_populates='building')
    member: Mapped['Member'] = relationship('Member', secondary='building_member', back_populates='building')
    building_asset_context: Mapped[List['BuildingAssetContext']] = relationship('BuildingAssetContext', uselist=True, back_populates='building')


class BuildingStatistics(Base):
    __tablename__ = 'building_statistics'
    __table_args__ = (
        ForeignKeyConstraint(['building_use_id'], ['building_use.id'], name='building_statistics_building_use_fk'),
        ForeignKeyConstraint(['country_id'], ['country.id'], name='building_statistics_country_fk'),
        ForeignKeyConstraint(['demand_profile_default_id'], ['demand_profile_default.id'], name='building_statistics_demand_profile_default_fk'),
        PrimaryKeyConstraint('id', name='building_statistics_pkey')
    )

    id = mapped_column(Integer)
    country_id = mapped_column(Integer, nullable=False)
    building_use_id = mapped_column(Integer, nullable=False)
    avg_surface_m2 = mapped_column(Double(53), nullable=False)
    common_construction_year = mapped_column(Integer, nullable=False)
    avg_occupation_in_m2_people = mapped_column(Double(53), nullable=False)
    share_sector_in_percent = mapped_column(Double(53), nullable=False)
    avg_yr_u_walls = mapped_column(Double(53), nullable=False)
    avg_yr_u_windows = mapped_column(Double(53), nullable=False)
    avg_yr_u_roof = mapped_column(Double(53), nullable=False)
    avg_yr_u_floor = mapped_column(Double(53), nullable=False)
    demand_profile_default_id = mapped_column(Integer, nullable=False)

    building_use: Mapped['BuildingUse'] = relationship('BuildingUse', back_populates='building_statistics')
    country: Mapped['Country'] = relationship('Country', back_populates='building_statistics')
    demand_profile_default: Mapped['DemandProfileDefault'] = relationship('DemandProfileDefault', back_populates='building_statistics')


class CountryStatistics(Base):
    __tablename__ = 'country_statistics'
    __table_args__ = (
        ForeignKeyConstraint(['country_id'], ['country.id'], name='country_statistics_country_fk'),
        PrimaryKeyConstraint('id', name='country_statistics_pk')
    )

    id = mapped_column(Integer)
    country_id = mapped_column(Integer, nullable=False)
    gdp_base_2015 = mapped_column(Double(53), nullable=False)
    population = mapped_column(Integer, nullable=False)
    population_growth_2050 = mapped_column(Double(53), nullable=False)
    cars_fleet_2020 = mapped_column(Double(53), nullable=False)
    car_battery_electric_perc_2020 = mapped_column(Double(53), nullable=False)
    car_plug_in_hybrid_perc_2020 = mapped_column(Double(53), nullable=False)
    reference = mapped_column(String)
    column10 = mapped_column(String(512))
    column11 = mapped_column(String(16))
    column12 = mapped_column(String(128))

    country: Mapped['Country'] = relationship('Country', back_populates='country_statistics')


class GenerationSystem(Base):
    __tablename__ = 'generation_system'
    __table_args__ = (
        ForeignKeyConstraint(['energy_carrier_input_1_id'], ['energy_carrier.id'], name='generation_system_energy_carrier_input_1_fk'),
        ForeignKeyConstraint(['energy_carrier_input_2_id'], ['energy_carrier.id'], name='generation_system_energy_carrier_input_2_fk'),
        ForeignKeyConstraint(['energy_carrier_output_1_id'], ['energy_carrier.id'], name='generation_system_energy_carrier_output_1_fk'),
        ForeignKeyConstraint(['energy_carrier_output_2_id'], ['energy_carrier.id'], name='generation_system_energy_carrier_output_2_fk'),
        ForeignKeyConstraint(['system_type_id'], ['system_type.id'], name='generation_system_system_type_fk'),
        PrimaryKeyConstraint('id', name='generation_system_pk')
    )

    id = mapped_column(Integer)
    system_type_id = mapped_column(Integer, nullable=False)
    name = mapped_column(String, nullable=False)
    fuel_yield1 = mapped_column(Double(53), nullable=False)
    fuel_yield2 = mapped_column(Double(53))
    capex_eur_kw = mapped_column(Double(53))
    opex_eur_kwh_year = mapped_column(Double(53))
    lifetime_years = mapped_column(Double(53))
    installed_capac_kwth = mapped_column(Double(53))
    equipmentcosts_perc = mapped_column(Double(53))
    installationcosts_perc = mapped_column(Double(53))
    stack_degradation_perc_year = mapped_column(Double(53))
    reference = mapped_column(String)
    energy_carrier_input_1_id = mapped_column(Integer)
    energy_carrier_input_2_id = mapped_column(Integer)
    energy_carrier_output_1_id = mapped_column(Integer)
    energy_carrier_output_2_id = mapped_column(Integer)

    energy_carrier_input_1: Mapped[Optional['EnergyCarrier']] = relationship('EnergyCarrier', foreign_keys=[energy_carrier_input_1_id], back_populates='generation_system')
    energy_carrier_input_2: Mapped[Optional['EnergyCarrier']] = relationship('EnergyCarrier', foreign_keys=[energy_carrier_input_2_id], back_populates='generation_system_')
    energy_carrier_output_1: Mapped[Optional['EnergyCarrier']] = relationship('EnergyCarrier', foreign_keys=[energy_carrier_output_1_id], back_populates='generation_system1')
    energy_carrier_output_2: Mapped[Optional['EnergyCarrier']] = relationship('EnergyCarrier', foreign_keys=[energy_carrier_output_2_id], back_populates='generation_system2')
    system_type: Mapped['SystemType'] = relationship('SystemType', back_populates='generation_system')
    community_energy_asset: Mapped[List['CommunityEnergyAsset']] = relationship('CommunityEnergyAsset', uselist=True, back_populates='generation_system')
    generation_system_profile: Mapped[List['GenerationSystemProfile']] = relationship('GenerationSystemProfile', uselist=True, foreign_keys='[GenerationSystemProfile.cooling_system_id]', back_populates='cooling_system')
    generation_system_profile_: Mapped[List['GenerationSystemProfile']] = relationship('GenerationSystemProfile', uselist=True, foreign_keys='[GenerationSystemProfile.dhw_system_id]', back_populates='dhw_system')
    generation_system_profile1: Mapped[List['GenerationSystemProfile']] = relationship('GenerationSystemProfile', uselist=True, foreign_keys='[GenerationSystemProfile.electricity_system_id]', back_populates='electricity_system')
    generation_system_profile2: Mapped[List['GenerationSystemProfile']] = relationship('GenerationSystemProfile', uselist=True, foreign_keys='[GenerationSystemProfile.heating_system_id]', back_populates='heating_system')
    building_energy_asset: Mapped[List['BuildingEnergyAsset']] = relationship('BuildingEnergyAsset', uselist=True, back_populates='generation_system')


class NationalEnergyCarrierProduction(Base):
    __tablename__ = 'national_energy_carrier_production'
    __table_args__ = (
        ForeignKeyConstraint(['country_id'], ['country.id'], name='national_energy_carrier_production_country_fk'),
        ForeignKeyConstraint(['energy_carrier_id'], ['energy_carrier.id'], name='national_energy_carrier_production_energy_carrier_fk'),
        PrimaryKeyConstraint('id', name='national_energy_carrier_production_pk')
    )

    id = mapped_column(Integer)
    energy_carrier_id = mapped_column(Integer, nullable=False)
    country_id = mapped_column(Integer, nullable=False)
    pef_tot = mapped_column(Double(53))
    pef_nren = mapped_column(Double(53))
    pef_ren = mapped_column(Double(53))
    f_co2_eq_g_kwh = mapped_column(Double(53))
    house_costs_eur_kwh = mapped_column(Double(53))
    non_h_costs_eur_kwh = mapped_column(Double(53))
    fit_tariff_eur_kwh = mapped_column(Double(53))
    # reference = mapped_column(String)

    country: Mapped['Country'] = relationship('Country', back_populates='national_energy_carrier_production')
    energy_carrier: Mapped['EnergyCarrier'] = relationship('EnergyCarrier', back_populates='national_energy_carrier_production')


class Node(Base):
    __tablename__ = 'node'
    __table_args__ = (
        ForeignKeyConstraint(['context_id'], ['context.id'], name='node_context_fk'),
        PrimaryKeyConstraint('id', name='node_pk')
    )

    id = mapped_column(Integer)
    name = mapped_column(String, nullable=False)
    geom = mapped_column(Geometry, nullable=False)
    context_id = mapped_column(Integer)

    context: Mapped[Optional['Context']] = relationship('Context', back_populates='node')
    community_energy_asset_input: Mapped[List['CommunityEnergyAsset']] = relationship('CommunityEnergyAsset', uselist=True, foreign_keys='[CommunityEnergyAsset.input_node_id]', back_populates='input_node')
    community_energy_asset_output: Mapped[List['CommunityEnergyAsset']] = relationship('CommunityEnergyAsset', uselist=True, foreign_keys='[CommunityEnergyAsset.output_node_id]', back_populates='output_node')


class TimeSerie(Base):
    __tablename__ = 'time_serie'
    __table_args__ = (
        ForeignKeyConstraint(['multi_time_serie_id'], ['multi_time_serie.id'], name='time_serie_multi_time_serie_fk'),
        PrimaryKeyConstraint('id', name='time_serie_pk')
    )

    id = mapped_column(Integer)
    multi_time_serie_id = mapped_column(Integer, nullable=False)
    value = mapped_column(ARRAY(Double(precision=53)), nullable=False)
    testcase = mapped_column(String, nullable=False)

    multi_time_serie: Mapped['MultiTimeSerie'] = relationship('MultiTimeSerie', back_populates='time_serie')


class TransformationAction(Base):
    __tablename__ = 'transformation_action'
    __table_args__ = (
        ForeignKeyConstraint(['context_id'], ['context.id'], name='transformation_action_context_fk'),
        PrimaryKeyConstraint('id', name='transformation_action_pk')
    )

    id = mapped_column(Integer)
    param1 = mapped_column(Double(53), nullable=False)
    param2 = mapped_column(Double(53), nullable=False)
    param3 = mapped_column(Double(53), nullable=False)
    param4 = mapped_column(Double(53), nullable=False)
    param5 = mapped_column(Double(53), nullable=False)
    context_id = mapped_column(Integer)

    context: Mapped[Optional['Context']] = relationship('Context', back_populates='transformation_action')


t_building_member = Table(
    'building_member', metadata,
    Column('member_id', Integer, nullable=False),
    Column('building_id', Integer, nullable=False),
    ForeignKeyConstraint(['building_id'], ['building.id'], name='building_member_building_id_fkey'),
    ForeignKeyConstraint(['member_id'], ['member.id'], name='building_member_member_id_fkey'),
    PrimaryKeyConstraint('member_id', 'building_id', name='building_member_pkey')
)


class CommunityEnergyAsset(Base):
    __tablename__ = 'community_energy_asset'
    __table_args__ = (
        ForeignKeyConstraint(['availability_ts_id'], ['multi_time_serie.id'], name='community_energy_asset_multi_time_serie_fk'),
        ForeignKeyConstraint(['generation_system_id'], ['generation_system.id'], name='community_energy_asset_generation_system_fk'),
        ForeignKeyConstraint(['input_node_id'], ['node.id'], name='community_energy_asset_input_node_fk'),
        ForeignKeyConstraint(['output_node_id'], ['node.id'], name='community_energy_asset_output_node_fk'),
        PrimaryKeyConstraint('id', name='community_energy_asset_pk')
    )

    id = mapped_column(Integer)
    input_node_id = mapped_column(Integer, nullable=False)
    generation_system_id = mapped_column(Integer, nullable=False)
    pmax_scalar = mapped_column(Double(53), nullable=False)
    pmaxmin_scalar = mapped_column(Double(53), nullable=False)
    pmaxmax_scalar = mapped_column(Double(53), nullable=False)
    availability_ts_id = mapped_column(Integer)
    output_node_id = mapped_column(Integer)

    availability_ts: Mapped[Optional['MultiTimeSerie']] = relationship('MultiTimeSerie', back_populates='community_energy_asset')
    generation_system: Mapped['GenerationSystem'] = relationship('GenerationSystem', back_populates='community_energy_asset')
    input_node: Mapped['Node'] = relationship('Node', foreign_keys=[input_node_id], back_populates='community_energy_asset_input')
    output_node: Mapped[Optional['Node']] = relationship('Node', foreign_keys=[output_node_id], back_populates='community_energy_asset_output')


class GenerationSystemProfile(Base):
    __tablename__ = 'generation_system_profile'
    __table_args__ = (
        ForeignKeyConstraint(['cooling_system_id'], ['generation_system.id'], name='generation_system_profile_cooling_system_fk'),
        ForeignKeyConstraint(['dhw_system_id'], ['generation_system.id'], name='generation_system_profile_dhw_system_fk'),
        ForeignKeyConstraint(['electricity_system_id'], ['generation_system.id'], name='generation_system_profile_electricity_system_fk'),
        ForeignKeyConstraint(['heating_system_id'], ['generation_system.id'], name='generation_system_profile_heating_system_fk'),
        PrimaryKeyConstraint('id', name='generation_system_profile_pk')
    )

    id = mapped_column(Integer)
    electricity_system_id = mapped_column(Integer)
    heating_system_id = mapped_column(Integer)
    cooling_system_id = mapped_column(Integer)
    dhw_system_id = mapped_column(Integer)

    cooling_system: Mapped[Optional['GenerationSystem']] = relationship('GenerationSystem', foreign_keys=[cooling_system_id], back_populates='generation_system_profile')
    dhw_system: Mapped[Optional['GenerationSystem']] = relationship('GenerationSystem', foreign_keys=[dhw_system_id], back_populates='generation_system_profile_')
    electricity_system: Mapped[Optional['GenerationSystem']] = relationship('GenerationSystem', foreign_keys=[electricity_system_id], back_populates='generation_system_profile1')
    heating_system: Mapped[Optional['GenerationSystem']] = relationship('GenerationSystem', foreign_keys=[heating_system_id], back_populates='generation_system_profile2')
    building_asset_context: Mapped[List['BuildingAssetContext']] = relationship('BuildingAssetContext', uselist=True, back_populates='generation_system_profile')
    building_statistics_profile: Mapped[List['BuildingStatisticsProfile']] = relationship('BuildingStatisticsProfile', uselist=True, back_populates='generation_system_profile')


class BuildingAssetContext(Base):
    __tablename__ = 'building_asset_context'
    __table_args__ = (
        ForeignKeyConstraint(['building_consumption_id'], ['building_consumption.id'], name='building_asset_context_building_consumption_fk'),
        ForeignKeyConstraint(['building_id'], ['building.id'], name='building_asset_context_building_fk'),
        ForeignKeyConstraint(['context_id'], ['context.id'], name='building_asset_context_context_fk'),
        ForeignKeyConstraint(['generation_system_profile_id'], ['generation_system_profile.id'], name='building_asset_context_generation_system_profile_fk'),
        PrimaryKeyConstraint('id', name='building_asset_context_pk')
    )

    id = mapped_column(Integer)
    building_consumption_id = mapped_column(Integer, nullable=False)
    generation_system_profile_id = mapped_column(Integer, nullable=False)
    building_id = mapped_column(Integer, nullable=False)
    context_id = mapped_column(Integer)
    name = mapped_column(String(30))

    building_consumption: Mapped['BuildingConsumption'] = relationship('BuildingConsumption', back_populates='building_asset_context')
    building: Mapped['Building'] = relationship('Building', back_populates='building_asset_context')
    context: Mapped[Optional['Context']] = relationship('Context', back_populates='building_asset_context')
    generation_system_profile: Mapped['GenerationSystemProfile'] = relationship('GenerationSystemProfile', back_populates='building_asset_context')
    building_energy_asset: Mapped[List['BuildingEnergyAsset']] = relationship('BuildingEnergyAsset', uselist=True, back_populates='building_asset_context')


class BuildingStatisticsProfile(Base):
    __tablename__ = 'building_statistics_profile'
    __table_args__ = (
        ForeignKeyConstraint(['building_use_id'], ['building_use.id'], name='building_statistics_profile_building_use_fk'),
        ForeignKeyConstraint(['country_id'], ['country.id'], name='building_statistics_profile_country_fk'),
        ForeignKeyConstraint(['generation_system_profile_id'], ['generation_system_profile.id'], name='building_statistics_profile_generation_system_profile_fk'),
        PrimaryKeyConstraint('id', name='building_statistics_profile_pk')
    )

    id = mapped_column(Integer)
    building_use_id = mapped_column(Integer, nullable=False)
    country_id = mapped_column(Integer, nullable=False)
    u_walls = mapped_column(Double(53), nullable=False)
    u_windows = mapped_column(Double(53), nullable=False)
    u_roof = mapped_column(Double(53), nullable=False)
    u_floor = mapped_column(Double(53), nullable=False)
    generation_system_profile_id = mapped_column(Integer)
    construction_year = mapped_column(Integer)

    building_use: Mapped['BuildingUse'] = relationship('BuildingUse', back_populates='building_statistics_profile')
    country: Mapped['Country'] = relationship('Country', back_populates='building_statistics_profile')
    generation_system_profile: Mapped[Optional['GenerationSystemProfile']] = relationship('GenerationSystemProfile', back_populates='building_statistics_profile')


class BuildingEnergyAsset(Base):
    __tablename__ = 'building_energy_asset'
    __table_args__ = (
        ForeignKeyConstraint(['availability_ts_id'], ['multi_time_serie.id'], name='building_energy_asset_multi_time_serie_fk'),
        ForeignKeyConstraint(['building_asset_context_id'], ['building_asset_context.id'], name='building_energy_asset_building_asset_context_fk'),
        ForeignKeyConstraint(['generation_system_id'], ['generation_system.id'], name='building_energy_asset_generation_system_fk'),
        PrimaryKeyConstraint('id', name='building_energy_asset_pk')
    )

    id = mapped_column(Integer)
    generation_system_id = mapped_column(Integer, nullable=False)
    pmax_scalar = mapped_column(Double(53), nullable=False)
    pmaxmin_scalar = mapped_column(Double(53), nullable=False)
    pmaxmax_scalar = mapped_column(Double(53), nullable=False)
    building_asset_context_id = mapped_column(Integer, nullable=False)
    availability_ts_id = mapped_column(Integer)

    availability_ts: Mapped[Optional['MultiTimeSerie']] = relationship('MultiTimeSerie', back_populates='building_energy_asset')
    building_asset_context: Mapped['BuildingAssetContext'] = relationship('BuildingAssetContext', back_populates='building_energy_asset')
    generation_system: Mapped['GenerationSystem'] = relationship('GenerationSystem', back_populates='building_energy_asset')
