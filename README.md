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
  <img src="https://img.shields.io/badge/AI_Layer-DashScope_Qwen-624AFF?style=flat-square&logo=alibabacloud&logoColor=white" alt="AI Layer" />
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
| **AI Model Selector** | Allowlist-controlled AI model selection (7 models supported) | User Selection | Selected Model Configuration | **COMPLETED** |
| **AI Guardrail** | Pre-execution schema and data type validation gate | Instruction + Schema | Validated / Blocked Plan | **COMPLETED** |
| **Analytical Engine** | Authoritative calculation of mathematical truth | Instruction + Data | Verified Result & Row Counts | **COMPLETED** |
| **Evidence & Provenance** | Grounded explanation citing exact cell ranges & lineage | Result + Lineage | Factual Provenance Trace | **COMPLETED** |
| **Visualization Engine** | Static high-res chart generation with lineage audit footers | Result / Instruction | Rendered PNG Chart Artifact | **COMPLETED** |
| **Smart Generate Chart** | Deterministic schema-aware chart discovery and ranking | Table Schema & Data | Ranked Visualizations (Up to 5) | **COMPLETED** |
| **How to Use & Guidance** | Comprehensive 11-section in-app guide & explanatory modals | User Interaction | Interactive Modal Guidance | **COMPLETED** |
| **Multilingual Localization** | Canonical English base with complete Indonesian UI translation | Language Toggle (EN/ID) | Localized Interface | **COMPLETED** |
| **Cross-Sheet Joins** | Relational reconciliation across separate worksheets | Multi-Sheet Dataset | Joined Analytical Table | **PLANNED (Post-MVP)** |

> **Architecture Note**: In accordance with [`BLUEPRINT.md`](./BLUEPRINT.md), the core system focuses on establishing authoritative single-worksheet multi-table ground truth with cell-level lineage and AI planning before introducing cross-sheet joins (Phases 3 & 4 in future releases).

---

## 2. Architecture & Principle: One Engine, Multiple Interfaces

Sheetsly implements a single, authoritative execution pipeline shared equally by visual click-based UI controls and natural-language query planners:

```
User Natural Language Query                          Point-and-Click Operation Builder
(English or Indonesian)                                      │
           │                                                 │
           ▼                                                 │
[AI Query Planner Layer]                                     │
(Provider Adapter / Client)                                  │
[Current Provider: Alibaba DashScope / Qwen]                 │
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
                         │                               ▲
                         ▼                               │
            [Evidence-Based Explainer]     [Smart Generate Chart Engine]
            (Cites Exact Lineage           (Schema-Aware Deterministic
             Coordinates & Row Counts)      Heuristic Discovery & Ranking)
```

### Core Architecture Rules
1. **AI Interprets Intent, Python Calculates Truth**: The AI compiles natural language questions into validated `AnalyticalInstruction` models. It never performs arithmetic or invents numbers.
2. **Ambiguity Stops Execution (No Guessing)**: When a question has multiple valid interpretations (e.g. *"What is the total?"* on a table with both `Units` and `Revenue`), execution stops immediately and returns a structured clarification prompt with schema options.
3. **Hard AI Guardrails**: Every AI-planned instruction must pass the `InstructionValidator` (type validation, valid columns, valid operators) before execution. If validation fails, execution is blocked and the error is displayed.
4. **Evidence Grounding & Source Lineage**: Explanations cite only verified `AnalyticalResult` values and `CalculationLineage` coordinates (e.g. `Sheet1!E2:E9801`, $N$ included rows).
5. **Deterministic Fallback**: If the AI provider is offline or unconfigured, the system continues running seamlessly in Deterministic Fallback Mode with 100% functionality via the Operation Builder and Smart Visualization engine.
6. **Language Independence of Underlying Truth**: English remains canonical. Translations apply exclusively to presentation and user guidance. Dataset values, column names, cell references, and mathematical calculations are never translated.

---

## 3. Implemented Modules & Capabilities

### A. Spreadsheet Ingestion & Inspection (Phase 1)
- **Cell Preservation**: Reads raw cell values, evaluated values, and formula strings (`fx`) using OpenPyXL with coordinate retention (`CellCoordinate`).
- **File Validation**: Supports `.xlsx`, `.xls`, `.xlsm`, `.xltx`, and `.csv` up to 50 MB.
- **Truthful Ingestion UX**: Responsive horizontal progress bar reflecting actual background parsing and profiling operations.
- **Dynamic Actual Spreadsheet Viewer**: High-performance paginated grid table with adaptive CSS truncation, rich hover inspection tooltips, cell coordinate inspection card, selectable page sizes (`10`, `25`, `50`, `100`), compact pagination with smart ellipsis (`1 2 3 ... 10`), and tabular numeral row count tracking (`Showing 51–100 of 9,800 rows`).

### B. Sheet Understanding & Table Profiling (Phase 2)
- **Table Detection**: Boundary detection identifying multi-table layouts within a single worksheet.
- **Orientation Analysis**: Determines `VERTICAL`, `HORIZONTAL`, `AMBIGUOUS`, or `IRREGULAR` layout with confidence scoring and structural signals.
- **Column Semantic Typing**: Profiles columns into `numeric_measure`, `categorical`, `temporal`, `identifier`, `boolean`, and `text`.
- **Data Quality & Hygiene Scoring**: Automated 0–100 quality scoring checking for missing values, mixed data types, and duplicate rows.

### C. Deterministic Analytical Engine (Phase 5)
- **Typed Instruction Model**: Strongly-typed `AnalyticalInstruction` validating operation, target column, filters, multi-grouping, and sorting before calculation.
- **Supported Operations**: `SUM`, `AVERAGE`, `MIN`, `MAX`, `MEDIAN`, `COUNT_ROWS`, `COUNT_VALUES`, `DISTINCT_COUNT`, `FILTER`, `SORT`, `GROUP_BY`, `SUMIFS`, `COUNTIFS`.
- **Pre-execution Guardrails**: Immediate rejection of invalid operations (e.g. calculating arithmetic mean on text strings).
- **Calculation Lineage**: Every result includes exact source worksheet and cell range addresses (e.g. `Sheet1!E2:E9801`), included/excluded row counts, filter conditions, and deterministic execution steps.

### D. Deterministic Visualization Engine & Smart Generate (Phase 6 & Smart Generator)
- **Supported Chart Types**: `BAR`, `LINE`, `PIE`, `AREA`, `SCATTER`, `HISTOGRAM`.
- **Intelligent "Smart Generate Chart"**: Deterministic, schema-aware visualization engine that evaluates table semantics without requiring manual chart configuration or LLM inference.
  - Automatically derives time-series trends (`LINE` / `AREA`), categorical comparisons (`BAR`), part-to-whole proportions (`PIE` strictly $\le 7$ non-negative categories), numeric correlations (`SCATTER`), and continuous distributions (`HISTOGRAM`).
  - **Identifier & High-Cardinality Protection**: Automatically filters primary keys and unique identifiers (e.g. `Order ID`, `SKU`, `User ID`) and rejects unreadable charts on high-cardinality columns (e.g. 9,800-bar charts).
  - **Deduplication & Ranking**: Ranks candidates by analytical business value, enforces dimension and metric diversity, and caps output to top 5 visualizations with complete "Why this chart?" explainability disclosures.
- **Conservative Compatibility**: Rule-based shape validation (e.g. pie charts rejected if negative values exist or categories $> 7$; scatter plots require two numeric columns).
- **Headless Static Rendering**: High-resolution Matplotlib/Seaborn image generation stored in session storage and served via `/api/v1/datasets/{id}/charts/{chart_id}/image`.
- **Integrated Lineage Footers**: Rendered charts include an audit footer linking the graphic to its source worksheet, cell range, and record count.

### E. Interactive Operation Builder UI (Phase 7)
- **Point-and-Click Interface**: Build complex analytical queries without writing formulas or SQL.
- **Type-Adaptive Filters**: 13 supported filter operators (`equals`, `contains`, `greater_than`, `between`, `in_list`, etc.) with `AND`/`OR` combination logic.
- **Multi-Aggregation Grouping**: Group by multiple dimensions simultaneously and calculate independent aggregate metrics.
- **Sort & Limit Controls**: Rank and limit top $N$ output rows.

### F. AI Natural Language Query Planner & Guardrails (Phase 8)
- **Intent Translation**: AI layer translates natural-language questions in English or Indonesian into validated `AnalyticalInstruction` JSON.
- **Proactive Disambiguation**: Returns structured `CLARIFICATION` prompts when queries are ambiguous, enabling users to click candidate column options.
- **AI Guardrail Validation**: Pre-execution check verifying that all planned columns and operations exist in the physical schema.
- **Evidence-Based Explainer**: Grounded summaries citing verified numbers, source cell ranges, row counts, and calculation steps.
- **Execution Stage Latency Grid**: Monospaced latency badges detailing milliseconds for Schema Resolution, AI Planning, Guardrails, Python Calculation, Visualization, and Explainer.
- **In-App Guide (`How to Use`)**: 11-section comprehensive workflow modal accessible from navigation.

### G. Multi-Language Localization (English Base + Indonesian UI)
- **First-Class Indonesian UMKM Support**: Full presentation-layer Indonesian translation tailored for Indonesian business operators and micro/small/medium enterprises.
- **Language Switcher**: Instant `EN | ID` segmented toggle in navigation.
- **First-Visit Onboarding Modal**: Lightweight, dismissible language selector with `localStorage` persistence.
- **Bilingual AI Query Planning**: AI understands questions in both Indonesian (e.g. *"Berapa total pendapatan?"*, *"Tampilkan rata-rata unit per wilayah"*) and English, mapping terms accurately to physical column names without hallucination.

### H. AI Model Selector, Help Modals & Quality UX (Phase 8.1)
- **Interactive Model Selector**: Compact UI dropdown in the AI Query Planner supporting 11 allowlisted models grouped by provider:
  - **Qwen**: `qwen3.5-plus` (`Based` / default), `qwen3.6-plus`, `qwen3.7-plus`, `qwen3.6-flash`, `qwen3.7-flash`
  - **DeepSeek**: `deepseek-v4-flash`
  - **Google Gemini**: `gemini-2.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.6-flash`, `gemini-3.7-flash`
- **Authoritative Backend Allowlist**: Strict Pydantic model validation on `NaturalLanguageQueryRequest` rejecting arbitrary or unapproved model names with HTTP 422 before execution.
- **Consistent Educational Modals**:
  - `How does this work?` modal detailing the 6-step analytical pipeline and the core principle *"AI interprets intent. Python calculates truth."*
  - `How Smart Generate works` modal detailing the 5-step deterministic schema-aware chart recommendation pipeline.
  - `How this is assessed` modal inside the Data Quality panel explaining the exact deterministic evaluation criteria (broken formulas, missing cells, mixed types, duplicate identifiers, duplicate rows) and scoring deduction rules (-15 / -5 / -2 pts).

---

## 4. End-to-End Execution Pipeline

```
1. User Ingestion
   ├── File Upload (.xlsx / .csv)
   ├── 2D Cell Coordinate Parsing
   ├── Table & Orientation Detection
   └── Column Semantic Profiling & Hygiene Scoring
   │
   ▼
2. Analysis Path Selection
   ├── Option A: Point-and-Click Operation Builder
   └── Option B: AI Natural Language Query Planner (EN / ID)
   │
   ▼
3. Pre-Execution Guardrails (InstructionValidator)
   ├── Column Existence & Type Compatibility Check
   └── Proactive Ambiguity Detection (Clarification Required)
   │
   ▼
4. Authoritative Deterministic Execution (Python / Pandas)
   │
   ▼
5. Verified AnalyticalResult
   ├── Formatted Metric & Structured Table
   ├── Exact Cell Range Lineage (e.g. Sheet1!E2:E9801)
   ├── Optional Matplotlib Visualization (Bar, Line, Pie, Area, Scatter, Histogram)
   └── Evidence-Grounded Factual Explanation
```

---

## 5. Repository Structure

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
│   ├── tests/                           # 70 automated unit & integration tests
│   └── app/
│       ├── main.py                      # FastAPI application entrypoint & lifespan
│       ├── core/                        # Configuration, logging, domain errors
│       ├── api/                         # REST API routes (/api/v1)
│       │   ├── router.py                # Router aggregator
│       │   └── routes/                  # Datasets, Sheets, Analytics, Visualization, AI
│       ├── storage/                     # Isolated filesystem manager
│       └── engine/
│           ├── ingestion/               # OpenPyXL parser, orientation, quality engine
│           ├── analytics/               # Analytical engine, filters, aggregations, lineage
│           ├── visualization/           # Chart selector, renderer, recommendation, smart generator
│           └── ai/                      # Qwen client, planner, guardrails, explainer, orchestrator
│
└── sheetsly_frontend/                   # Next.js 16 Frontend Workspace
    ├── .env.example                     # Frontend environment variable template
    ├── .gitignore                       # Frontend Git ignore rules
    ├── package.json                     # Node.js dependencies (Next.js 16, React 19, Tailwind v4)
    ├── tsconfig.json                    # TypeScript compiler configuration
    ├── next.config.ts                   # Next.js configuration
    ├── app/
    │   ├── layout.tsx                   # Root layout with LanguageProvider & Geist fonts
    │   ├── globals.css                  # Tailwind v4 theme tokens, animations, & tabular numbers
    │   └── page.tsx                     # Workspace coordinator & tab router
    ├── components/
    │   ├── upload/                      # SpreadsheetUploader with progressive loading
    │   ├── workspace/                   # SheetList, DetectedTablesViewer, ActualDataViewer,
    │   │                                # DataQualityPanel, VisualizationViewer, WorkbookHeader,
    │   │                                # HowToUseModal, LanguageSwitcher, LanguageOnboardingModal
    │   ├── builder/                     # OperationBuilder, OperationSelector, FilterBuilder,
    │   │                                # GroupByBuilder, SortLimitBuilder, AnalysisResultView
    │   └── ai/                          # AIQueryWorkspace, PlanInterpretationCard,
    │                                    # ClarificationPrompt, EvidenceExplanationCard
    └── lib/
        ├── types.ts                     # TypeScript domain contracts & timing models
        ├── api.ts                       # Typed REST API client
        └── i18n/                        # Multilingual localization system (en / id)
            ├── types.ts                 # Translation dictionary schema
            ├── context.tsx              # LanguageContext & useTranslation hook
            └── translations/            # English (en.ts) & Indonesian (id.ts) dictionaries
```

---

## 6. Prerequisites

- **Python**: `3.10` or higher (developed and verified on Python `3.12`)
- **Node.js**: `18.18` or higher (Next.js 16 compatible)
- **Package Manager**: `npm` (v9+) or `pnpm`
- **Operating System**: Windows, macOS, or Linux

---

## 7. Setup & Execution Guide

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

# 5. Configure DashScope / Qwen API credentials in .env:
# DASHSCOPE_API_KEY=your_dashscope_api_key
# QWEN_MODEL=qwen3.5-plus
# QWEN_BASE_URL=https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1
# QWEN_ENABLE_THINKING=false

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

## 8. Environment Variables Reference

### Backend (`sheetsly_backend/.env`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `APP_NAME` | String | `Sheetsly` | Application identifier name. |
| `APP_ENV` | String | `development` | Runtime environment (`development`, `production`). |
| `DEBUG` | Boolean | `true` | Enables detailed debug logs and API documentation at `/docs`. |
| `BACKEND_HOST` | String | `127.0.0.1` | Network interface to bind backend server. |
| `BACKEND_PORT` | Integer | `8000` | HTTP port for backend server. |
| `FRONTEND_URL` | String | `http://localhost:3000` | Primary frontend origin for CORS policies. |
| `CORS_ORIGINS` | String | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated list of allowed CORS origins. |
| `MAX_UPLOAD_SIZE_MB` | Integer | `50` | Maximum allowed file upload size in megabytes. |
| `TEMP_FILE_DIRECTORY` | String | `./storage/temp` | Directory for session-scoped dataset files and charts. |
| `DASHSCOPE_API_KEY` | Secret | `""` | DashScope / Alibaba Cloud Model Studio API key. |
| `QWEN_MODEL` | String | `qwen3.5-plus` | Qwen model identifier (e.g. `qwen3.5-plus`, `qwen-max`). |
| `QWEN_BASE_URL` | String | `https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1` | OpenAI-compatible endpoint URL for DashScope Singapore workspace. |
| `QWEN_ENABLE_THINKING` | Boolean | `false` | Set to `false` for rapid sub-5s analytical planning, or `true` for extended reasoning mode. |
| `DATABASE_ENABLED` | Boolean | `false` | Database toggle (disabled in MVP). |

### Frontend (`sheetsly_frontend/.env.local`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Public URL | `http://127.0.0.1:8000/api/v1` | Base REST API URL accessed by browser client. |

---

## 9. REST API Reference (`/api/v1`)

### AI Natural Language Query Endpoints (Phase 8)
- `POST /api/v1/ai/query` &mdash; Executes end-to-end natural language query: AI Planner &rarr; AI Guardrail &rarr; Python Engine &rarr; Visualizer &rarr; Evidence Explainer. Supports `preplanned_instruction` to skip planning when pre-compiled.
- `POST /api/v1/ai/plan-only` &mdash; Generates planned `AnalyticalInstruction` or `ClarificationRequest` with `TimingBreakdown` without running calculations.
- `GET /api/v1/ai/suggest/{dataset_id}` &mdash; Generates 3–5 schema-derived analytical questions for a dataset/worksheet.
- `GET /api/v1/ai/status` &mdash; Reports AI provider configuration readiness status without exposing secrets.
- `GET /api/v1/ai/diagnostics` &mdash; Returns safe provider connectivity diagnostics (masks API keys as `sk-ws-****`).

### Ingestion & Worksheet Endpoints (Phases 1 & 2)
- `GET /api/v1/health` &mdash; Health check and service readiness status.
- `POST /api/v1/datasets/upload` &mdash; Uploads `.xlsx`/`.csv` file; triggers inspection and returns `WorkbookOverview`.
- `GET /api/v1/datasets/{id}` &mdash; Retrieves cached metadata and quality report for a dataset.
- `GET /api/v1/datasets/{id}/sheets` &mdash; Lists detected worksheets, table candidates, and dimensions.
- `GET /api/v1/datasets/{id}/sheets/{sheet_name}/data` &mdash; Paginated 2D cell grid with formulas and raw/parsed values.
- `DELETE /api/v1/datasets/{id}` &mdash; Deletes temporary dataset session and generated chart artifacts.

### Deterministic Analytics Endpoints (Phase 5)
- `POST /api/v1/datasets/{id}/analyze` &mdash; Executes an `AnalyticalInstruction` and returns a verified `AnalyticalResult`.
- `GET /api/v1/operations/catalog` &mdash; Returns list of supported analytical operations and parameters.

### Deterministic Visualization & Smart Generate Endpoints (Phase 6 & Smart Generator)
- `POST /api/v1/datasets/{id}/visualize` &mdash; Renders a static Matplotlib chart from a verified `AnalyticalResult`.
- `POST /api/v1/datasets/{id}/visualize/from-instruction` &mdash; Executes analysis and renders chart in a single pipeline step.
- `POST /api/v1/datasets/{id}/visualize/smart-generate` &mdash; Evaluates table schema heuristics and generates up to 5 ranked charts with "Why this chart?" explainability metadata.
- `POST /api/v1/visualization/recommend` &mdash; Recommends compatible chart types for a given analytical result.
- `GET /api/v1/datasets/{id}/charts/{chart_id}/image` &mdash; Serves the static PNG image artifact.

---

## 10. Automated Testing & Verification

### Running Backend Tests (Pytest)
```powershell
cd sheetsly_backend
python -m pytest -p no:pytest_ethereum
```
*Current test suite: **71 unit & integration tests** covering ingestion, data grid search, quality scoring, scalar aggregations, multi-grouping, filters, lineage, chart rendering, deterministic smart chart generation (10 scenarios in `test_smart_visualization.py`), AI planning, guardrails, explainer, and REST API routes (**100% passing**).*

### Running Frontend Production Build
```powershell
cd sheetsly_frontend
npm run build
```
*Compiled in Next.js 16 (Turbopack + TypeScript) with **0 TypeScript and ESLint errors**.*

---

## 11. Frontend Design & Impeccable Quality Standards

The frontend interface strictly conforms to the **Impeccable `Operate` Mode** design standards:
- **Zero AI Slop**: No emojis, no glowing cards, no glassmorphism, no purple/blue AI gradients, and no fake blinking/pulsing activity dots.
- **Truthful Loading**: Horizontal indeterminate progress bar for file ingestion; multi-stage textual status transitions for AI queries (`"Planning analytical query with AI..."` &rarr; `"Executing deterministic analysis in Python..."`).
- **Typography & Alignment**: Uses Google Geist Sans for clean UI labels and Google Geist Mono for cell coordinates and numbers (`font-variant-numeric: tabular-nums`).
- **Accessibility**: All interactive elements have visible focus rings (`focus-visible:ring-2`), accessible `aria-label` tags on icon buttons, keyboard ESC dismissal on all modals, and WCAG AA contrast ratios ($\ge 4.5:1$).

---

## 12. Current Limitations & Operational Boundaries

1. **Single-Worksheet Target per Query**: Current analytical operations target a single selected worksheet and table region. Cross-worksheet relational joins are planned for Phases 3 & 4.
2. **Session-Scoped Storage**: Datasets and chart artifacts are stored in local session directories (`storage/temp/`) and cleaned up upon server restart or session deletion.
3. **AI Provider Latency**: When `QWEN_ENABLE_THINKING=true`, extended reasoning mode on DashScope may require ~30–40s per query; setting `QWEN_ENABLE_THINKING=false` reduces query planning latency to ~4–5s.
4. **File Size Ceiling**: Maximum supported upload size is 50 MB.

---

## 13. Security & Secret Management

1. **Server-Side Isolation**: AI credentials (`DASHSCOPE_API_KEY`) and endpoints remain strictly on the backend and are never exposed to the frontend client.
2. **Untracked Environment Secrets**: `.gitignore` strictly protects `.env`, `.env.local`, `.venv`, and temporary storage caches.
3. **Masked Diagnostics**: The `/api/v1/ai/diagnostics` endpoint masks API keys (e.g. `sk-ws-****`) to prevent secret leakage in logs.
4. **Pre-Execution AI Guardrails**: All LLM outputs pass structural schema validation before execution, preventing arbitrary code execution or invalid database queries.
