<div align="center">

# Sheetsly

<p align="center">
  <img src="https://img.shields.io/badge/Next.js_16-000000?style=flat-square&logo=nextdotjs&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/React_19-20232A?style=flat-square&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind_CSS_v4-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white" alt="Pandas" />
  <img src="https://img.shields.io/badge/Multi--Model_AI-Qwen_|_DeepSeek_|_Gemini-624AFF?style=flat-square&logo=openai&logoColor=white" alt="Multi-Model AI" />
</p>

<p align="center">
  <strong>Deterministic Spreadsheet Intelligence, AI Query Planner &amp; State-Aware Spreadsheet Agent</strong><br />
  <em>A verifiable analytics workspace combining natural-language intent planning with authoritative Python calculations, cell-level provenance, and safe spreadsheet mutations.</em>
</p>

</div>

Sheetsly is an AI-powered analytical spreadsheet platform that transforms raw spreadsheets (`.xlsx`, `.xls`, `.xlsm`, `.csv`) into structured, verifiable, and visually explainable analytical insights while providing a state-aware AI Agent to safely operate on the worksheet.

The platform is engineered around an uncompromised foundational rule: **Python remains the authoritative source of numerical truth.** The AI application layer operates strictly as a natural language query planner and evidence-grounded explainer. It is architecturally forbidden from performing arithmetic directly. All mathematical aggregations, filters, groupings, and statistics are computed deterministically by the Python engine with complete cell-level calculation lineage.

---

## 1. Architectural Scope & Implemented Module Matrix

| Module | Purpose | Input | Output | Status |
|---|---|---|---|---|
| **Ingestion & Inspection** | Parse workbook, preserve 2D cell coordinates, validate file format | `.xlsx`, `.xls`, `.xlsm`, `.csv` | Structured Dataset & Table Regions | **COMPLETED** |
| **Actual Spreadsheet Viewer** | Name box jump navigation, formula bar (`fx`), cell editing, inspection, pagination | Dataset | Paginated Grid, Name Box, Formula Bar | **COMPLETED** |
| **Spreadsheet AI Agent** | State-aware workbook operator, multi-intent decomposition, idempotency, atomic undo & rollback | Natural Language / Range | Transactional Action Mutations | **COMPLETED** |
| **Native Worksheet Visualizations** | First-class `CREATE_CHART`, spatial bounding box collision guard, deduplication, XLSX native charts | Natural Language / Range | Native Worksheet Charts, Fullscreen Modal, XLSX Export | **COMPLETED** |
| **Table Detection & Profiling** | Detect table boundaries, layout orientation, and semantic column typing | Worksheet Cells | Table Regions & Column Semantics | **COMPLETED** |
| **Data Quality & Hygiene** | Evaluate structural health, broken formulas, and missing values | Worksheet / Table | 0–100 Hygiene Score & Issues List | **COMPLETED** |
| **Analysis Builder** | Construct multi-stage deterministic calculations point-and-click | User Configuration | Verified `AnalyticalResult` | **COMPLETED** |
| **AI Query Planner** | Translate natural-language questions to structured analytical intent | User Query (EN / ID) | `AnalyticalInstruction` / Clarification | **COMPLETED** |
| **Multi-Sheet AI Context** | Serialize workbook-level schema inventory for multi-sheet disambiguation | Workbook Sheets | Multi-Sheet Schema Inventory | **COMPLETED** |
| **Compact AI Model Selector** | Allowlist-controlled AI model selection (Qwen, DeepSeek, Gemini) | User Selection | Selected Model Configuration | **COMPLETED** |
| **AI Guardrail** | Pre-execution schema and data type validation gate | Instruction + Schema | Validated / Blocked Plan | **COMPLETED** |
| **Analytical Engine** | Authoritative calculation of mathematical truth | Instruction + Data | Verified Result & Row Counts | **COMPLETED** |
| **Evidence & Provenance** | Grounded explanation citing exact cell ranges & lineage | Result + Lineage | Factual Provenance Trace | **COMPLETED** |
| **Visualization Engine** | Static high-res chart generation with lineage audit footers | Result / Instruction | Rendered PNG Chart Artifact | **COMPLETED** |
| **Smart Generate Chart** | Deterministic schema-aware chart discovery and ranking | Table Schema & Data | Ranked Visualizations (Up to 5) | **COMPLETED** |
| **Tab State & URL Persistence**| State-preserving workspace route (`/workspace/[id]`) and tab caching | Workspace Context | Persistent Analytical Workspace | **COMPLETED** |
| **Theme System (Dark Mode)** | User-controlled Light / Dark / System theme toggle with persistence | Theme Context | Adaptive Visual Interface | **COMPLETED** |
| **Safe Tabular CSV Export** | Deterministic CSV download of spreadsheet slices and verified results | Grid / Result Table | Formatted CSV File Download | **COMPLETED** |
| **How to Use & Guidance** | Comprehensive in-app guide, practical examples, & explanatory modals | User Interaction | Interactive Modal Guidance | **COMPLETED** |
| **Multilingual Localization** | Canonical English base with complete Indonesian UI translation | Language Toggle (EN/ID) | Localized Interface | **COMPLETED** |

---

## 2. Product Positioning: AI Query Planner vs. Spreadsheet AI Agent

Sheetsly clearly separates two distinct, complementary AI capabilities to prevent overclaiming and ensure operational safety:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       SHEETSLY WORKSPACE                                        │
├───────────────────────────────────────────────┬─────────────────────────────────────────────────┤
│              AI QUERY PLANNER                 │              SPREADSHEET AI AGENT               │
│         (Read-Only Data Intelligence)         │          (State-Aware Workbook Operator)        │
├───────────────────────────────────────────────┼─────────────────────────────────────────────────┤
│ • Answers questions about data and dimensions │ • Operates directly on the actual spreadsheet   │
│ • Explains dataset structure and hygiene      │ • Executes deterministic formula & value writes │
│ • Discovers patterns, rankings & extremes     │ • Creates native worksheet visualizations       │
│ • Produces verified analytical tables & PNGs  │ • Respects explicit coordinates & selected cell │
│ • 0 spreadsheet mutations (Strictly read-only)│ • State-aware: avoids duplicate/redundant writes│
│ • Grounded explanations with cell lineage     │ • Spatial collision safety (bounding boxes)     │
│ • Multi-sheet inventory context               │ • Full natural-language Undo, Redo & Rollback   │
└───────────────────────────────────────────────┴─────────────────────────────────────────────────┘
```

> **Important Positioning Principle**: The Spreadsheet AI Agent is **not** an unrestricted autonomous black box or a generic "AI Excel replacement." It is a **context-aware, state-aware spreadsheet operator** that acts deterministically, inspects current state before mutation, minimizes changes, avoids overwriting occupied cells without permission, and ensures 100% rollback safety.

---

## 3. Architecture & Core Workflow

Sheetsly implements a single, authoritative execution pipeline shared equally by visual click-based UI controls, query planners, and the spreadsheet agent:

```
User Natural Language Query                          Point-and-Click Operation Builder
(English or Indonesian)                                      │
           │                                                 │
           ▼                                                 │
[Intent Interpretation & Planning Layer]                     │
(Multi-Sheet Workbook Context Aware)                         │
[Selectable Providers: Qwen | DeepSeek | Gemini]             │
           │                                                 │
           ▼                                                 │
[State Inspection & Pre-Condition Check]                     │
(Target Coordinates, Formulas, Values, Charts)               │
           │                                                 │
           ▼                                                 │
[AI Guardrail & Collision Gate]                              │
(Detects Ambiguity / Overlaps / Conflicting Data)            │
           │                                                 │
           ├────────────────────────────┬────────────────────┘
           ▼                            ▼
[Clarification / Conflict UI]   Spreadsheet Actions Sequence
(No Silent Overwrites)          - WRITE_FORMULA
                                - WRITE_VALUE
                                - CREATE_CHART
                                         │
                                         ▼
                                [Instruction Validator]
                                (Type, Bounds & Spatial Checks)
                                         │
                                         ▼
                                [Deterministic Engine]
                                (Python Truth / Formula Evaluator)
                                         │
                                         ▼
                             [Verified Mutation Execution]
                             (Atomic Transaction with Snapshot)
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
            [Spreadsheet Grid Updated]      [Native Worksheet Chart]
            - Formula in target cell        - Rendered at logical anchor
            - Lineage audit trace           - Spatially disjoint placement
            - Reversible with Undo          - Native OpenPyXL XLSX export
```

### The 7-Step Spreadsheet AI Agent Lifecycle

The Spreadsheet AI Agent follows a strict seven-phase deterministic lifecycle:

$$\textbf{Understand} \longrightarrow \textbf{Inspect} \longrightarrow \textbf{Resolve} \longrightarrow \textbf{Plan} \longrightarrow \textbf{Validate} \longrightarrow \textbf{Execute} \longrightarrow \textbf{Verify}$$

1. **Understand**: Interprets the user's natural language request (e.g. `hitung total sales di D10`, `total sales di D10 dan berikan label TOTAL di C10`, `buatkan pie chart di B12 untuk Region berdasarkan Sales`, `ini sebenarnya data apa sih?`, `undo langkah tersebut`).
2. **Inspect**: Examines actual workbook metadata and current grid state (available sheets, tables, column semantics, existing formulas, parsed cell values, selected cell/range, existing charts in `grid.charts`, and occupied 2D bounding boxes). The Agent **never assumes** an unmentioned column exists. If a metric like `Profit` is requested on a table that only contains `Sales`, it rejects the hallucination and clarifies that Profit is unavailable.
3. **Resolve**: Resolves **WHAT** (metric, operation, chart type, dimension, measure) and **WHERE** (explicit coordinate vs. selected cell `"di sini"` / `"cells ini"` vs. safe placement fallback). Explicit coordinates always take precedence over selected-cell context.
4. **Plan**: Decomposes requests into minimal, independent spreadsheet actions (`WRITE_FORMULA`, `WRITE_VALUE`, `CREATE_CHART`). Unnecessary mutations (unrequested labels, formatting, or helper tables) are strictly avoided.
5. **Validate**: Validates column types, cell coordinates, and spatial bounding boxes against existing grid data and charts. Conflicting occupied cells trigger a clarification request instead of a silent destructive overwrite.
6. **Execute**: Applies mutations inside an isolated `MutationTransaction` with pre-mutation snapshots for instant rollback.
7. **Verify**: Confirms numerical values match Python evaluation (`FormulaEvaluator.evaluate`) and returns an evidence-grounded confirmation in the user's language (EN/ID).

---

## 4. State Awareness, Idempotency & Collision Safety

### A. Multi-Intent Decomposition & Partial Satisfaction
When a user submits a multi-part request:
- **Scenario**: User previously calculated `D10 = =SUM(D2:D7)`. Then asks: `total sales di D10 dan berikan label TOTAL di C10`.
- **Behavior**: The agent inspects `D10` and recognizes that the formula `=SUM(D2:D7)` is **already satisfied**. Rather than rejecting the request due to `D10` being occupied or redundantly re-writing `D10`, the agent executes **only** the missing mutation: `WRITE_VALUE[C10] = "TOTAL"`.
- **Response**: *"Total Sales di D10 sudah benar. Label TOTAL ditambahkan di C10."*

### B. Formula & Cell Idempotency
- If the requested formula or exact numerical result already exists in the target cell, the agent makes **0 mutations** and confirms that the result already exists.
- If the target cell contains conflicting data (e.g. `D10` contains `=AVERAGE(D2:D7)` or an unrelated value), the agent refuses to silently overwrite it and returns a `CLARIFICATION` conflict prompt.

### C. Native Worksheet Charting & Spatial Collision Safety
- **Native Grid Anchor**: Charts are anchored at logical cell coordinates (e.g. `B12`) and rendered directly on the spreadsheet surface with zoom, pan, and fullscreen inspection modals.
- **Spatial Bounding Boxes**: Charts occupy physical $7 \times 14$ cell rectangular areas (e.g. `B12:I25`). If a user requests a chart at an explicit cell that overlaps an existing chart region, the agent flags a spatial collision.
- **Dynamic Safe Placement**: Auto-placed charts dynamically calculate free coordinates below all existing chart bounding boxes.
- **Chart Deduplication**: If an equivalent chart `(dimension, measure, type, aggregation)` already exists (e.g. Pie chart of *Sales by Region* at `B12`), repeating the request results in **0 new charts**, returning: *"Pie chart 'Sales by Region' sudah tersedia di B12, jadi saya tidak membuat duplikat."*
- **Native OpenPyXL XLSX Export**: Exporting to `.xlsx` attaches native OpenPyXL chart objects anchored at destination cells, preserving native Excel editing and rendering.

### D. Schema-Aware Multi-Visualization
- For requests like `visualisasikan semua kemungkinan yang relevan dari data ini`:
  - Inspects table schema and identifies meaningful dimensions, temporal fields, and numeric measures.
  - Automatically filters out candidate charts that **already exist** in `grid.charts`.
  - Places remaining visualizations into disjoint, non-overlapping bounding boxes in a single atomic transaction.
  - If all relevant visualizations already exist, it performs 0 mutations and reports that all visualizations are present.

---

## 5. Natural Language Transaction Controls & Read-Only Inspection

### A. Natural Language Undo, Redo, and Cancel
The Agent processes conversational transaction commands directly against the workbook transaction log:

| Intent | Supported Phrases (English & Indonesian) | Effect |
|---|---|---|
| **Undo** | `undo`, `please undo`, `undo langkah tersebut`, `undo perubahan tadi`, `batalkan langkah tadi`, `kembalikan seperti sebelumnya` | Reverts the last committed transaction, restoring cells, charts, and formats. |
| **Redo** | `redo`, `redo langkah tersebut`, `ulangi langkah tadi`, `terapkan kembali` | Re-applies the previously undone transaction cleanly. |
| **Cancel** | `cancel`, `cancel that`, `batalkan operasi ini`, `batalin` | Dismisses any pending clarification or operation with 0 mutations. |
| **Inspect Changes**| `what did you change?`, `where did you put it?`, `show formula`, `perubahan apa yang dilakukan?`, `hasilnya ada di mana?` | Reports exact cell diffs, formulas, and parsed values from the last transaction. |

### B. Read-Only Data Inquiries (Zero Mutations)
The Agent answers contextual workbook questions without modifying the spreadsheet:
- **Dataset Structure**: `ini sebenarnya data apa sih?`, `dataset ini tentang apa?` &rarr; Reports row counts, columns, semantic types, and hygiene score.
- **Cell Inspection**: `apa yang ada di D2?`, `apa isi cell ini?` &rarr; Returns the exact formula string, parsed value, and data type of the coordinate.
- **Deterministic Extremes & Superlatives**: `berapa sales terbesar?`, `region mana dengan sales tertinggi?` &rarr; Computes maximums, minimums, and cross-dimensional rankings via deterministic Python execution with 0 cell mutations.

---

## 6. How to Use Sheetsly

### 1. Ask (Read-Only Insights)
* `"ini sebenarnya data apa sih?"` — Explains dataset purpose, rows, and columns.
* `"region mana dengan sales tertinggi?"` — Computes highest revenue region using deterministic aggregation.
* `"berapa sales terbesar?"` — Identifies scalar extreme values.

### 2. Calculate (Spreadsheet Formulas)
* `"hitung total sales di D10"` — Writes `=SUM(D2:D7)` to `D10`.
* `"hitung average sales di D11"` — Writes `=AVERAGE(D2:D7)` to `D11`.
* `"hitung total keuntungan di E8"` — Resolves semantic metric *keuntungan* to `Profit` column and writes `=SUM(E2:E6)` to `E8`.

### 3. Label & Multi-Intent
* `"total sales di D10 dan berikan label TOTAL di C10"` — Decomposes into `WRITE_VALUE[C10] = "TOTAL"` and `WRITE_FORMULA[D10] = "=SUM(D2:D7)"`.
* If `D10` is already calculated, it safely adds only `TOTAL` to `C10`.

### 4. Visualize (Native Worksheet Charts)
* `"buatkan pie chart di B12 untuk Region berdasarkan Sales"` — Creates a native Pie chart anchored at `B12`.
* `"buatkan bar chart Category berdasarkan Sales"` — Places a Bar chart in the next safe, non-overlapping location.
* `"visualisasikan semua kemungkinan yang relevan dari data ini"` — Generates bounded, schema-aware multi-chart visualizations without duplicates.

### 5. Contextual Selected-Cell Placement
1. Click cell **`B40`** in the spreadsheet grid.
2. In the AI Chat, type: `"buatkan visualisasi sales by region di cells ini"`
3. The Agent anchors the visualization directly at `B40`.

### 6. Natural Language Control
* `"undo langkah tersebut"` — Reverts the previous formula or chart creation.
* `"redo langkah tersebut"` — Restores the reverted transaction.
* `"batalkan operasi ini"` — Cancels pending actions.

### 7. Cell & Change Inspection
* `"apa yang ada di D2?"` — Displays cell `D2` value and formula.
* `"perubahan apa yang dilakukan?"` — Summarizes exact target cells and formulas modified in the last operation.

---

## 7. Supported AI Models & 12-Model Matrix

Sheetsly features a strict allowlist of 12 verified LLM configurations across Google Gemini, Alibaba Cloud Qwen, and DeepSeek:

* **Google Gemini**: `gemini-3.1-flash-lite` (Active Default Base Model), `gemini-2.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.6-flash`
* **Alibaba Cloud Qwen**: `qwen3.5-122b-a10b`, `qwen3.5-flash`, `qwen3.6-plus`, `qwen3.7-plus`, `qwen3.6-flash`, `qwen3.7-flash`
* **DeepSeek**: `deepseek-v4-flash`

> Note: `qwen3.5-plus` and `qwen3.5-397b-a17b` are permanently retired.

---

## 8. Repository Structure

```
sheetsly/
├── README.md                            # Comprehensive platform documentation & guide
├── BLUEPRINT.md                         # Authoritative architectural specification
├── .gitignore                           # Git ignore rules
├── .env.example                         # Environment configuration template
├── sales_q3.csv                         # Sample dataset (Sales)
├── hr_payroll.xlsx                      # Sample dataset (Payroll & Data Quality)
├── correlation_test.csv                 # Sample dataset (Scatter & Histogram)
│
├── sheetsly_backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── api/routes/                  # Datasets, Sheets, Analytics, Visualization, AI, Agent
│   │   ├── core/                        # Configuration, logging, domain error handlers
│   │   └── engine/
│   │       ├── agent/                   # Spreadsheet Agent planner, validator, mutator, transaction manager
│   │       ├── analytics/               # Deterministic formulas, aggregations, lineage tracking
│   │       ├── visualization/           # Headless Matplotlib renderer, chart selector, smart generator
│   │       ├── ingestion/               # OpenPyXL parser, cell preservation, orientation, hygiene
│   │       └── ai/                      # Multi-provider client (Gemini/Qwen/DeepSeek), guardrails, explainer
│   └── tests/                           # 118+ automated unit & integration tests (100% pass rate)
│
└── sheetsly_frontend/                   # Next.js 16 Workspace
    ├── app/
    │   ├── page.tsx                     # Landing page & file upload workflow
    │   └── workspace/[sessionId]/page.tsx # Persistent workspace route with multi-tab state caching
    ├── components/
    │   ├── workspace/                   # ActualDataViewer, DetectedTablesViewer, VisualizationViewer, modals
    │   ├── ai/                          # GridAIChatPanel, AIModelSelector, ChartFullscreenModal
    │   └── builder/                     # OperationBuilder, FilterBuilder, GroupByBuilder
    └── lib/
        ├── api.ts                       # Typed REST API client
        ├── export.ts                    # Safe tabular CSV & full XLSX workbook export utilities
        └── i18n/                        # Multilingual localization system (English & Indonesian)
```

---

## 9. Prerequisites & Installation

### Prerequisites
- **Python**: `3.10` or higher (verified on Python `3.12`)
- **Node.js**: `18.18` or higher (Next.js 16 compatible)
- **Package Manager**: `npm` (v9+) or `pnpm`

### A. Backend Setup (FastAPI)
```powershell
cd sheetsly_backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env

# Configure GEMINI_API_KEY or DASHSCOPE_API_KEY in .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### B. Frontend Setup (Next.js)
```powershell
cd sheetsly_frontend
npm install
Copy-Item .env.example .env.local
npm run dev -- --port 3000
```
Workspace will be live at `http://localhost:3000`.

---

## 10. Automated Testing & Verification

### Running All Agent & Core Backend Tests (Pytest)
```powershell
cd sheetsly_backend
pytest tests/test_phase14_workspace_agent.py \
       tests/test_phase15_agent_visualization.py \
       tests/test_phase16_agent_dashboard.py \
       tests/test_phase17_agent_core.py \
       tests/test_phase18_natural_language_control.py \
       tests/test_phase18y_native_charts.py \
       tests/test_phase19_intent_context_placement.py \
       tests/test_phase20_state_awareness_and_idempotency.py -v
```
*Current test suite: **118 / 118 tests passed (100% passing)**.*

### Running Frontend Production Build
```powershell
cd sheetsly_frontend
npm run build
```
*Compiled in Next.js 16 (Turbopack + TypeScript) with **0 errors and 0 warnings**.*

---

## 11. Design & Impeccable Quality Standards

The frontend interface strictly conforms to the **Impeccable `Operate` Mode** design standards:
- **Zero AI Slop**: No emojis, no glowing cards, no glassmorphism, no purple/blue AI gradients, and no fake blinking/pulsing activity dots.
- **Truthful Loading**: Horizontal indeterminate progress bar for file ingestion; multi-stage textual status transitions for AI queries (`"Planning analytical query with AI..."` &rarr; `"Executing deterministic analysis in Python..."`).
- **Typography & Alignment**: Uses Google Geist Sans for clean UI labels and Google Geist Mono for cell coordinates and numbers (`font-variant-numeric: tabular-nums`).
- **Accessibility & Themes**: All interactive elements have visible focus rings (`focus-visible:ring-2`), accessible `aria-label` tags on icon buttons, keyboard ESC dismissal on all modals, dark mode token parity, and WCAG AA contrast ratios ($\ge 4.5:1$).
