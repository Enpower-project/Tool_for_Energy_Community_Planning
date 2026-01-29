# ENPOWER – Scripts testing guide

**Created by CARTIF**

ENPOWER – Scripts testing guide
Created by CARTIF

## Overview
This folder contains the core ENPOWER backend scripts used to generate:
- A baseline energy scenario
- One alternative scenario, based on predefined goals and technology combinations

This document explains how to run local tests using the provided testing script and
which values are valid for goal and selected_combo.

The objective is to allow developers to quickly test the full pipeline
without needing to understand all internal modules.

## Test script
The recommended entry point for testing is:

test_full_pipeline.py

This script:
1. Generates a baseline context and baseline KPIs
2. Uses the baseline output as input for an alternative scenario
3. Saves a single JSON output with all results

Run it with:
python test_full_pipeline.py

## Goal definition
Structure:
goal = {
    "goals": "<GOAL_ID>",
    "country": "<COUNTRY_CODE>"
}

Available goals:
1  Higher rate of renewable energy
2  Higher efficiency
3  Energy self-sufficiency
4  Decarbonisation of heating & cooling
5  Electrification
6  E-mobility (NOT IMPLEMENTED – do not use)

Important:
Goal "6" (E-mobility) is still under development and must not be used for testing.

Country codes:
ES  Spain
PT  Portugal
FR  France
IT  Italy

## Technology combinations (`selected_combo`)
Structure:
selected_combo = {
    "id": <INT>,
    "combination": "<TECH_STRING>"
}

Technology codes:
PV       Photovoltaics
TS       Solar thermal
Wind     Wind
HP       Heat pump
DHN      District heating network
Battery  Electrical storage
CS       Charging stations

Available combinations:
1   HP
2   TS
3   Wind
4   HP+TS
5   HP+Wind
6   HP+PV
7   TS+Wind
8   TS+PV
9   Wind+PV
10  HP+TS+Wind
11  HP+TS+PV
12  HP+Wind+PV
13  TS+Wind+PV
14  HP+TS+Wind+PV
15  DHN
16  PV
17  Battery #not integrated yet
18  CS #not integrated yet
19  PV+Battery #not integrated yet
20  PV+CS #not integrated yet
21  Battery+CS #not integrated yet
22  PV+Battery+CS #not integrated yet

Important limitation:
Combinations including Charging Stations (CS) are experimental and not validated.
They should only be used for structural tests.

## Recommended test cases
Case 1 – Renewable penetration
goal = {"goals": "1", "country": "ES"}
selected_combo = {"id": 9, "combination": "Wind+PV"}

Case 2 – Electrification
goal = {"goals": "5", "country": "ES"}
selected_combo = {"id": 6, "combination": "HP+PV"}

Case 3 – Heating & cooling decarbonisation
goal = {"goals": "4", "country": "ES"}
selected_combo = {"id": 14, "combination": "HP+TS+Wind+PV"}

## Output
Each execution generates a JSON file under:
api/services/scripts_enpower/data/outputs_pruebas/

## Notes
- Not all technology combinations are guaranteed to converge for all datasets.
- If a test fails, the issue is usually related to input data or catalogues.
- E-mobility related features are explicitly excluded from the current testing scope.

End of document.
