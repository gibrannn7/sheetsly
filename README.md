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
  <strong>Deterministic Spreadsheet Intelligence &amp; AI Query Workspace</strong><br />
  <em>A verifiable analytics platform combining natural-language intent planning with authoritative Python calculations and cell-level provenance.</em>
</p>

</div>

Sheetsly is an AI-powered analytical spreadsheet application that transforms raw spreadsheets (`.xlsx`, `.xls`, `.xlsm`, `.csv`) into structured, verifiable, and visually explainable analytical insights.

The platform is engineered around an uncompromised foundational rule: **Python remains the authoritative source of numerical truth.** The AI application layer operates strictly as a natural language query planner and evidence-grounded explainer. It is architecturally forbidden from performing arithmetic directly. All mathematical aggregations, filters, groupings, and statistics are computed deterministically by the Python engine with complete cell-level calculation lineage.

---

## 1. Architectural Scope & Implemented Module Matrix

| Module | Purpose | Input | Output | Status |
|---|---|---|---|---|
| **Ingestion & Inspection** | Parse workbook, preserve 2D cell coordinates, validate file format | `.xlsx`, `.xls`, `.xlsm`, `.csv` | Structured Dataset & Table Regions | **COMPLETED** |
| **Actual Spreadsheet Viewer** | Inspect raw/parsed data with pagination, truncation & cell inspection | Dataset | Paginated Table & Cell Metadata | **COMPLETED** |
| **Table Detection & Profiling** | Detect table boundaries, layout orientation, and semantic column typing | Worksheet Cells | Table Regions & Column Semantics | **COMPLETED** |
| **Data Quality & Hygiene** | Evaluate structural health, broken formulas, and missing values | Worksheet / Table | 0–100 Hygiene Score & Issues List | **COMPLETED** |
| **Analysis Builder** | Construct multi-stage deterministic calculations point-and-click | User Configuration | Verified `AnalyticalResult` | **COMPLETED** |
| **AI Query Planner** | Translate natural-language questions to structured analytical intent | User Query (EN / ID) | `AnalyticalInstruction` / Clarification | **COMPLETED** |
| **Multi-Sheet AI Context** | Serialize workbook-level schema inventory for multi-sheet disambiguation | Workbook Sheets | Multi-Sheet Schema Inventory | **COMPLETED** |
| **12-Model AI Selector** | Allowlist-controlled AI model selection (Qwen, DeepSeek, Gemini) | User Selection | Selected Model Configuration | **COMPLETED** |
| **AI Guardrail** | Pre-execution schema and data type validation gate | Instruction + Schema | Validated / Blocked Plan | **COMPLETED** |
| **Analytical Engine** | Authoritative calculation of mathematical truth | Instruction + Data | Verified Result & Row Counts | **COMPLETED** |
| **Evidence & Provenance** | Grounded explanation citing exact cell ranges & lineage | Result + Lineage | Factual Provenance Trace | **COMPLETED** |
| **Visualization Engine** | Static high-res chart generation with lineage audit footers | Result / Instruction | Rendered PNG Chart Artifact | **COMPLETED** |
| **Smart Generate Chart** | Deterministic schema-aware chart discovery and ranking | Table Schema & Data | Ranked Visualizations (Up to 5) | **COMPLETED** |
| **Tab State & URL Persistence**| State-preserving workspace route (`/workspace/[id]`) and tab caching | Workspace Context | Persistent Analytical Workspace | **COMPLETED** |
| **Theme System (Dark Mode)** | User-controlled Light / Dark / System theme toggle with persistence | Theme Context | Adaptive Visual Interface | **COMPLETED** |
| **Safe Tabular CSV Export** | Deterministic CSV download of spreadsheet slices and verified results | Grid / Result Table | Formatted CSV File Download | **COMPLETED** |
| **How to Use & Guidance** | Comprehensive 11-section in-app guide & explanatory modals | User Interaction | Interactive Modal Guidance | **COMPLETED** |
| **Multilingual Localization** | Canonical English base with complete Indonesian UI translation | Language Toggle (EN/ID) | Localized Interface | **COMPLETED** |

---

## 2. Architecture & Principle: One Engine, Multiple Interfaces

Sheetsly implements a single, authoritative execution pipeline shared equally by visual click-based UI controls and natural-language query planners:

```
User Natural Language Query                          Point-and-Click Operation Builder
(English or Indonesian)                                      │
           │                                                 │
           ▼                                                 │
[AI Query Planner Layer]                                     │
(Multi-Sheet Workbook Context Aware)                         │
[Selectable Providers: Qwen | DeepSeek | Gemini]             │
           │                                                 │
           ▼                                                 │
[Structured Query Plan]                                      │
           │                                                 │
           ▼                                                 │
[AI Guardrail]                                               │
(Detects Ambiguity / Incompatible Types)                     │
           │                                                 │
           ├────────────────────────────┬────────────────────┘
           ▼                            ▼
[Ambiguity Detected]           AnalyticalInstruction
           │                            │
           ▼                            ▼
[Structured Clarification UI]  [Instruction Validator]
                                (Pre-execution Type & Shape Checks)
                                         │
                                         ▼
                                [Deterministic Engine]
                                (Python / Pandas Execution Layer)
                                         │
                                         ▼
                             Verified AnalyticalResult
                                         │
                         ┌───────────────┴───────────────┐
                         ▼                               ▼
            [Tabular / Scalar UI]          [Deterministic Visualization]
            - Formatted Metrics            - Chart Compatibility Check
            - Structured Tables            - Headless Matplotlib Renderer
            - Cell Coordinate Lineage      - Static PNG Artifact + Provenance
            - Safe Tabular CSV Export                    │
                         │                               ▼
                         ▼                 [Smart Generate Chart Engine]
            [Evidence-Based Explainer]     (Schema-Aware Deterministic
            (Cites Exact Lineage            Heuristic Discovery & Ranking)
             Coordinates & Row Counts)
```

### Core Architecture Rules
1. **AI Interprets Intent, Python Calculates Truth**: The AI compiles natural language questions into validated `AnalyticalInstruction` models. It never performs arithmetic or invents numbers.
2. **Multi-Sheet Workbook Awareness**: The AI planner receives a workbook-wide inventory of all sheets, tables, and column data types, enabling accurate sheet selection from natural language queries (e.g. *"Show total revenue in sheet Transactions"*).
3. **Ambiguity Stops Execution (No Guessing)**: When a question has multiple valid interpretations (e.g. *"What is the total?"* on a table with both `Units` and `Revenue`), execution stops immediately and returns a structured clarification prompt with schema options.
4. **Hard AI Guardrails**: Every AI-planned instruction must pass the `InstructionValidator` (type validation, valid columns, valid operators) before execution. If validation fails, execution is blocked and the error is displayed.
5. **Evidence Grounding & Source Lineage**: Explanations cite only verified `AnalyticalResult` values and `CalculationLineage` coordinates (e.g. `Sheet1!E2:E9801`, $N$ included rows).
6. **Deterministic Fallback**: If an AI provider is offline or unconfigured, the system continues running seamlessly in Deterministic Fallback Mode with 100% functionality via the Operation Builder and Smart Visualization engine.
7. **Language Independence of Underlying Truth**: English remains canonical. Translations apply exclusively to presentation and user guidance. Dataset values, column names, cell references, and mathematical calculations are never translated.

---

## 3. Implemented Modules & Capabilities

### A. Spreadsheet Ingestion & Inspection
- **Cell Preservation**: Reads raw cell values, evaluated values, and formula strings (`fx`) using OpenPyXL with coordinate retention (`CellCoordinate`).
- **File Validation**: Supports `.xlsx`, `.xls`, `.xlsm`, `.xltx`, and `.csv` up to 50 MB.
- **Truthful Ingestion UX**: Responsive horizontal progress bar reflecting actual background parsing and profiling operations.
- **Dynamic Actual Spreadsheet Viewer**: High-performance paginated grid table with adaptive CSS truncation, rich hover inspection tooltips, cell coordinate inspection card, selectable page sizes (`10`, `25`, `50`, `100`), compact pagination with smart ellipsis (`1 2 3 ... 10`), debounced real-time column search, and tabular numeral row count tracking (`Showing 51–100 of 9,800 rows`).
- **CSV Data Slice Export**: Deterministic client-side CSV download of filtered grid data and verified calculation tables.

### B. Sheet Understanding & Table Profiling
- **Table Detection**: Boundary detection identifying multi-table layouts within a single worksheet.
- **Orientation Analysis**: Determines `VERTICAL`, `HORIZONTAL`, `AMBIGUOUS`, or `IRREGULAR` layout with confidence scoring and structural signals.
- **Column Semantic Typing**: Profiles columns into `numeric_measure`, `categorical`, `temporal`, `identifier`, `boolean`, and `text`.
- **Data Quality & Hygiene Scoring**: Automated 0–100 quality scoring checking for missing values, mixed data types, and duplicate rows.

### C. Deterministic Analytical Engine
- **Typed Instruction Model**: Strongly-typed `AnalyticalInstruction` validating operation, target column, filters, multi-grouping, and sorting before calculation.
- **Supported Operations**: `SUM`, `AVERAGE`, `MIN`, `MAX`, `MEDIAN`, `COUNT_ROWS`, `COUNT_VALUES`, `DISTINCT_COUNT`, `FILTER`, `SORT`, `GROUP_BY`, `SUMIFS`, `COUNTIFS`.
- **Pre-execution Guardrails**: Immediate rejection of invalid operations (e.g. calculating arithmetic mean on text strings).
- **Calculation Lineage**: Every result includes exact source worksheet and cell range addresses (e.g. `Sheet1!E2:E9801`), included/excluded row counts, filter conditions, and deterministic execution steps.

### D. Deterministic Visualization Engine & Smart Generate
- **Supported Chart Types**: `BAR`, `LINE`, `PIE`, `AREA`, `SCATTER`, `HISTOGRAM`.
- **Intelligent "Smart Generate Chart"**: Deterministic, schema-aware visualization engine that evaluates table semantics without requiring manual chart configuration or LLM inference.
  - Automatically derives time-series trends (`LINE` / `AREA`), categorical comparisons (`BAR`), part-to-whole proportions (`PIE` strictly $\le 7$ non-negative categories), numeric correlations (`SCATTER`), and continuous distributions (`HISTOGRAM`).
  - **Identifier & High-Cardinality Protection**: Automatically filters primary keys and unique identifiers (e.g. `Order ID`, `SKU`, `User ID`) and rejects unreadable charts on high-cardinality columns (e.g. 9,800-bar charts).
  - **Deduplication & Ranking**: Ranks candidates by analytical business value, enforces dimension and metric diversity, and caps output to top 5 visualizations with complete "Why this chart?" explainability disclosures.
- **Conservative Compatibility**: Rule-based shape validation (e.g. pie charts rejected if negative values exist or categories $> 7$; scatter plots require two numeric columns).
- **Headless Static Rendering**: High-resolution Matplotlib/Seaborn image generation stored in session storage and served via `/api/v1/datasets/{id}/charts/{chart_id}/image`.
- **Integrated Lineage Footers**: Rendered charts include an audit footer linking the graphic to its source worksheet, cell range, and record count.

### E. Interactive Operation Builder UI
- **Point-and-Click Interface**: Build complex analytical queries without writing formulas or SQL.
- **Type-Adaptive Filters**: 13 supported filter operators (`equals`, `contains`, `greater_than`, `between`, `in_list`, etc.) with `AND`/`OR` combination logic.
- **Multi-Aggregation Grouping**: Group by multiple dimensions simultaneously and calculate independent aggregate metrics.
- **Sort & Limit Controls**: Rank and limit top $N$ output rows.
- **Export Calculation Results**: Direct CSV export button for verified analysis summaries and grouped datasets.

### F. Multi-Model AI Query Planner & 12-Model Matrix
- **Supported Providers**: Alibaba Cloud Model Studio (Qwen), DeepSeek, and Google Gemini API (v1beta REST generateContent).
- **Active Default Model**: `qwen3.5-397b-a17b` (Note: `qwen3.5-plus` is fully retired).
- **Strict 12-Model Allowlist**:
  - **Qwen**: `qwen3.5-397b-a17b` (Default), `qwen3.5-flash`, `qwen3.6-plus`, `qwen3.7-plus`, `qwen3.6-flash`, `qwen3.7-flash`
  - **DeepSeek**: `deepseek-v4-flash`
  - **Google Gemini**: `gemini-2.5-flash`, `gemini-3.1-flash-lite`, `gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.6-flash`
- **Spreadsheet AI Agent Workflow**:
  - 10-step lifecycle: User instruction $\to$ intent interpretation $\to$ workbook context discovery $\to$ guardrails & safety $\to$ placement guard $\to$ formula preparation $\to$ independent Python verification $\to$ commit on success / atomic rollback on failure.
  - Reversibility: Every committed transaction is recorded and can be reverted at any time using the `↩ Undo` button.
- **Smart Analytics & Granular Temporal Calculations**:
  - Natural-language query execution compiling into verified analytical instructions.
  - Granular temporal calculations supporting Yearly (e.g. 2015, 2016), Quarterly (e.g. 2015 Q1), and continuous Monthly (e.g. 2015-01) date intervals with chronological sorting and Line/Column visualization recommendations.
- **Full Workbook & Slices Export**:
  - **XLSX Export**: Full multi-sheet workbook download preserving all worksheets, names, formulas, and evaluated data.
  - **CSV Export**: Clean CSV download of active worksheet grids or filtered analytical results.
- **Proactive Disambiguation**: Returns structured `CLARIFICATION` prompts when queries are ambiguous, enabling users to click candidate column options.
- **AI Guardrail Validation**: Pre-execution check verifying that all planned columns and operations exist in the physical schema.
- **Evidence-Based Explainer & Level 10 Provenance**: Grounded summaries citing verified numbers, source cell ranges, row counts, calculation steps, and verification status (`VERIFIED_NUMERIC_TRUTH`).
- **Execution Stage Latency Grid**: Monospaced latency badges detailing milliseconds for Schema Resolution, AI Planning, Guardrails, Python Calculation, Visualization, and Explainer.

### G. Workspace State Persistence & Routing
- **Persistent Workspace Route (`/workspace/[sessionId]`)**: Shareable and reloadable URL route preserving active worksheet, tab selection, and analytical state.
- **No State Loss on Tab Navigation**: Persistent DOM rendering ensures that active searches, pagination, custom charts, generated smart charts, Analysis Builder configurations, and AI query history are maintained across tab switches.
- **Theme Switcher**: Segmented `Light | Dark | System` selector with complete dark mode styles across all workspaces, cards, tables, headers, and modals.

### H. Multi-Language Localization (English Base + Indonesian UI)
- **First-Class Indonesian UMKM Support**: Full presentation-layer Indonesian translation tailored for Indonesian business operators and micro/small/medium enterprises.
- **Language Switcher**: Instant `EN | ID` segmented toggle in navigation.
- **First-Visit Onboarding Modal**: Lightweight, dismissible language selector with `localStorage` persistence and brand asset integration.
- **Bilingual AI Query Planning**: AI understands questions in both Indonesian (e.g. *"Berapa total pendapatan?"*, *"Tampilkan rata-rata unit per wilayah"*) and English.
- **Contextual In-App Guidance**: Dedicated contextual help modals for Operation Builder, Smart Analytics, and Spreadsheet AI Agent, alongside the global 11-chapter How-To guide.

---

## 4. Repository Structure

```
sheetsly/
├── BLUEPRINT.md                         # Authoritative architectural specification
├── README.md                            # Comprehensive developer & operator documentation
├── .gitignore                           # Root Git ignore rules
├── .env.example                         # Root environment configuration template
├── sales_q3.csv                         # Sample verification dataset (Sales)
├── hr_payroll.xlsx                      # Sample verification dataset (Payroll/Quality)
├── correlation_test.csv                 # Sample verification dataset (Scatter/Histogram)
├── large_dataset_9800.csv               # Synthetic benchmark dataset (9,800 rows / 2 MB)
│
├── sheetsly_backend/                    # Python FastAPI Backend
│   ├── .env.example                     # Backend environment variable template
│   ├── .gitignore                       # Backend Git ignore rules
│   ├── pytest.ini                       # Pytest test configuration
│   ├── requirements.txt                 # Backend Python dependencies
│   ├── storage/
│   │   └── temp/                        # Session storage for uploaded files and charts
│   │       └── .gitkeep
│   ├── tests/                           # 312 automated unit & integration tests (100% pass rate)
│   └── app/
│       ├── main.py                      # FastAPI application entrypoint & lifespan
│       ├── core/                        # Configuration, logging, domain errors
│       ├── api/                         # REST API routes (/api/v1)
│       │   ├── router.py                # Router aggregator
│       │   └── routes/                  # Datasets, Sheets, Analytics, Visualization, AI, Agent
│       ├── storage/                     # Isolated filesystem manager
│       └── engine/
│           ├── ingestion/               # OpenPyXL parser, orientation, quality engine
│           ├── analytics/               # Analytical engine, filters, aggregations, lineage, temporal
│           ├── visualization/           # Chart selector, renderer, recommendation, smart generator
│           ├── mutation/                # Spreadsheet agent planner, safe placement, verification, rollback
│           └── ai/                      # Multi-provider client (Qwen/DeepSeek/Gemini), planner, guardrails, explainer, orchestrator
│
└── sheetsly_frontend/                   # Next.js 16 Frontend Workspace
    ├── .env.example                     # Frontend environment variable template
    ├── .gitignore                       # Frontend Git ignore rules
    ├── package.json                     # Node.js dependencies (Next.js 16, React 19, Tailwind v4)
    ├── tsconfig.json                    # TypeScript compiler configuration
    ├── next.config.ts                   # Next.js configuration
    ├── public/
    │   └── assets/                      # Brand assets (logo.png)
    ├── app/
    │   ├── layout.tsx                   # Root layout with ThemeProvider, LanguageProvider, WorkspaceProvider
    │   ├── globals.css                  # Tailwind v4 dark variant, theme tokens, & tabular numbers
    │   ├── page.tsx                     # Landing page & initial upload workflow
    │   └── workspace/[sessionId]/page.tsx # Persistent workspace route with multi-tab state caching
    ├── components/
    │   ├── upload/                      # SpreadsheetUploader with progressive loading
    │   ├── workspace/                   # SheetList, DetectedTablesViewer, ActualDataViewer,
    │   │                                # DataQualityPanel, VisualizationViewer, SmartVisualizationPanel,
    │   │                                # WorkbookHeader, ThemeSwitcher, HowToUseModal, LanguageSwitcher,
    │   │                                # SmartAnalyticsHelpModal, AnalysisBuilderHelpModal
    │   ├── builder/                     # OperationBuilder, OperationSelector, FilterBuilder,
    │   │                                # GroupByBuilder, SortLimitBuilder, AnalysisResultView
    │   └── ai/                          # AIQueryWorkspace, AIModelSelector, GridAIChatPanel,
    │                                    # SpreadsheetAgentHelpModal, PlanInterpretationCard,
    │                                    # ClarificationPrompt, EvidenceExplanationCard, HowDoesThisWorkModal
    └── lib/
        ├── types.ts                     # TypeScript domain contracts & timing models
        ├── api.ts                       # Typed REST API client
        ├── export.ts                    # Safe tabular CSV & full XLSX workbook export utilities
        ├── theme/                       # ThemeContext (Light / Dark / System)
        ├── workspace/                   # Centralized WorkspaceContext & session state management
        └── i18n/                        # Multilingual localization system (en / id)
```

---

## 5. Prerequisites

- **Python**: `3.10` or higher (developed and verified on Python `3.12`)
- **Node.js**: `18.18` or higher (Next.js 16 compatible)
- **Package Manager**: `npm` (v9+) or `pnpm`
- **Operating System**: Windows, macOS, or Linux

---

## 6. Setup & Execution Guide

### A. Backend Setup (FastAPI)

```powershell
# 1. Navigate to backend directory
cd sheetsly_backend

# 2. (Optional) Create and activate a Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install required Python packages
pip install -r requirements.txt

# 4. Create environment file from template
Copy-Item .env.example .env

# 5. Configure AI API credentials in .env:
# DASHSCOPE_API_KEY=your_dashscope_api_key
# GEMINI_API_KEY=your_gemini_api_key

# 6. Start backend development server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend will be live at: `http://127.0.0.1:8000` (Swagger interactive docs at `http://127.0.0.1:8000/docs`).

### B. Frontend Setup (Next.js)

```powershell
# 1. Navigate to frontend directory
cd sheetsly_frontend

# 2. Install Node dependencies
npm install

# 3. Create environment file from template
Copy-Item .env.example .env.local

# 4. Start frontend development server
npm run dev -- --port 3000
```
Frontend workspace will be live at: `http://localhost:3000`.

---

## 7. Automated Testing & Verification

### Running Backend Tests (Pytest)
```powershell
cd sheetsly_backend
python -m pytest -p no:pytest_ethereum -v
```
*Current test suite: **312 unit & integration tests** covering ingestion, data grid search, quality scoring, scalar aggregations, multi-grouping, filters, lineage, chart rendering, deterministic smart chart generation, XLSX & CSV export, temporal trends, AI model selector, mutation engine, rollback verification, and REST API routes (**100% passing**).*

### Running Direct Acceptance Certification
```powershell
python scratch/execute_all_manual_acceptance_tests.py
```
*Direct acceptance suite: **23 / 23 test cases passing (100%)**.*

### Running Frontend Production Build
```powershell
cd sheetsly_frontend
npm run build
```
*Compiled in Next.js 16 (Turbopack + TypeScript) with **0 errors and 0 warnings**.*

---

## 8. Frontend Design & Impeccable Quality Standards

The frontend interface strictly conforms to the **Impeccable `Operate` Mode** design standards:
- **Zero AI Slop**: No emojis, no glowing cards, no glassmorphism, no purple/blue AI gradients, and no fake blinking/pulsing activity dots.
- **Truthful Loading**: Horizontal indeterminate progress bar for file ingestion; multi-stage textual status transitions for AI queries (`"Planning analytical query with AI..."` &rarr; `"Executing deterministic analysis in Python..."`).
- **Typography & Alignment**: Uses Google Geist Sans for clean UI labels and Google Geist Mono for cell coordinates and numbers (`font-variant-numeric: tabular-nums`).
- **Accessibility & Themes**: All interactive elements have visible focus rings (`focus-visible:ring-2`), accessible `aria-label` tags on icon buttons, keyboard ESC dismissal on all modals, dark mode token parity, and WCAG AA contrast ratios ($\ge 4.5:1$).
