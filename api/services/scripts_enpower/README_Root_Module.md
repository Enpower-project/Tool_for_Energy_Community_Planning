# Root Module — Energy Optimization Framework

This README orients new contributors to the **top-level scripts** that tie together the framework’s subsystems
(`helpers`, `OEMOF_module`, `kpi_module`, `scenario_generator`, and `data`). It explains what each main script does,
how they interconnect, and how to run the end‑to‑end pipeline.

---

## 1) What lives here

```
.
├─ data/                     # input/output JSON, pickle, and intermediate results
├─ helpers/                  # utilities, constants, wind, and custom constraints
├─ kpi_module/               # KPI calculators and equivalence factors
├─ OEMOF_module/             # core OEMOF simulation engine and post-processing
├─ scenario_generator/       # context and recommendation builders
├─ calculate_kpis_from_context.py
├─ inesctec_api_call.py
├─ module_integration.py
├─ run_full_pipeline.py
└─ requirements.txt
```

Think of these top‑level scripts as **entry points** to common workflows: running the full optimization, converting
results to KPIs, and connecting with external services.

---

## 2) Quick start: run the full pipeline

End‑to‑end run from **user context → recommended techs → OEMOF → final context → (optional) truncated**:

```python
from run_full_pipeline import run_full_pipeline

final_context = run_full_pipeline(
    context_path="data/initial_context.json",
    output_context_path="data/final_context.json",
    goal=1,                     # optimization goal
    country="ES",               # country for recommendations
    preferred_combination="HP+PV"  # optional (e.g., "TS+Wind+PV")
)
```

**What this does under the hood:**

1. **Get technology recommendations** for `(goal, country)` and translate them to OEMOF codes.  
2. **Pick a valid tech combination** (use your preferred one if available).  
3. **Generate a unified context** compatible with OEMOF.  
4. **Run the OEMOF simulation** and save an updated context with results.  
5. **Truncate large arrays** into a compact JSON for analysis or transfer.

The function returns the **final context dict** and saves helper files in `data/` (intermediate + final JSON).

---

## 3) Main scripts

### A) `run_full_pipeline.py` — one function to run it all

`run_full_pipeline(...)` orchestrates the full workflow:
- Fetches technology recommendations and **maps action names → OEMOF codes** (PV, TS, Wind, HP).
- Generates **all valid OEMOF‑compatible combinations**, selects one (user‑preferred or first valid).
- Reads your input context (supports `{"context": {...}}` or bare `{...}`) and **creates the unified context**.
- Runs the OEMOF model and **writes the final context** (with flows, capacities, imports/exports).
- Truncates long lists for a lightweight analysis JSON.

**Inputs:** path to the input context JSON, goal, country, and optional combination string.  
**Outputs:** final context dict; files under `data/` (intermediate + final JSON).

*Typical call:* see Quick start above.

> Implementation details:
> - Uses the scenario generator to list technologies and to build the OEMOF context.
> - Uses the OEMOF runner for the simulation and a truncation helper for compact export.

---

### B) `calculate_kpis_from_context.py` — compute per‑building & community KPIs

Turn a **final context** (with OEMOF results) into a **KPI payload**:

```python
from calculate_kpis_from_context import calculate_energy_kpis_from_context

kpi_payload = calculate_energy_kpis_from_context(final_context, country_id=31)  # optional country override
# kpi_payload = {"totals": {...}, "buildings": [ {...}, ... ]}
```

**What it does:**
- Builds **PEF** and **CO₂** lookups from the context; auto‑detects *electricity* and *gas* carrier IDs.
- For each building: calls a core KPI calculator, then adds **peaks**, **citizen equivalents**, and **intensities** if data is present.
- Sums up community totals and derives **self‑consumption / self‑sufficiency** ratios and **thermal spill**.
- Returns a clean dict with `totals` and `buildings` (optionally writes a `data/final_kpis.json` when run as a script).

**Inputs:** full context dict (after OEMOF).  
**Outputs:** dict with community totals and per‑building KPI dictionaries.

---

### C) `module_integration.py` — glue for front‑end → OEMOF → KPIs

This script exposes **JSON‑in / JSON‑out** helpers for product integration:

- `recommend_to_front_combos(user_input)` returns valid **tech combinations** for a given `(goal, country)`.  
- `run_pipeline_from_context_json(base_context_json, goal, country, selected_combination)` runs the OEMOF pipeline **in‑memory** (accepts a dict instead of a file path) and returns the **final context**.  
- `compute_kpis_from_final_context(final_context, country_id=None)` runs KPI computation on the final context and returns the **KPI payload**.

Use these when integrating with a UI or API layer that prefers Python functions instead of file‑based workflows.

---

### D) `inesctec_api_call.py` — pricing utilities and ENPOWER sizing helpers

- `load_prices_and_tariffs()` loads a `prices_and_tariffs.pkl` from `data/`, normalizes it into a DataFrame, and filters **year 2024**.  
- `scenario_with_shared_assets(context)` small helper to fetch/load a sample scenario with shared assets.  
- `enpower_sizing_database(...)` builds a **Python object** (as text) for sizing parameters that downstream services can import.  
- `api_call(endpoint, method="GET"|"POST", payload=None, files=None)` simple HTTP wrapper with basic auth for external calls.

These utilities are optional and primarily support data preparation or external service integration.

---

## 4) Data flow (big picture)

```
User Context (JSON) ──► Scenario Generator (recommendations & unified context)
                         │
                         └──► OEMOF Module (simulate)
                                │
                                ├──► Final Context (flows, capacities, imports/exports)
                                └──► KPI Module (community + building KPIs)
```

**Where things are saved:**  
- `data/intermediate_<original_context>.json` — unified context (pre‑OEMOF)  
- `data/final_context.json` (or custom path) — OEMOF results merged into context  
- `data/final_context_truncated_for_analysis.json` — compact context (no long arrays)  
- `data/final_kpis.json` — (only when running `calculate_kpis_from_context.py` as a script)

---

## 5) Tips for new contributors

- Start by reading the **Helpers** and **OEMOF Module** READMEs to learn what functions exist and how models are built.
- Use `run_full_pipeline.py` in a sandbox first; confirm that the pipeline runs with your **own context** in `data/`.
- If you extend the KPI set, do it in the KPI module; this script only **assembles** and **exports** what the KPI core computes.
- When adding a new technology, confirm it appears in the **tech translation** and **valid combinations** used by the pipeline.
- Keep intermediate outputs—especially `intermediate_*.json`—they’re great for debugging the model inputs.

---

## 6) Requirements

Install Python dependencies with:

```bash
pip install -r requirements.txt
```
