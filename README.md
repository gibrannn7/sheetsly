# Sheetsly

> **AI-Assisted Spreadsheet Intelligence Workspace**  
> *Full Implementation (Phases 1, 2, 5, 6, 7 & 8)*

Sheetsly is a deterministic spreadsheet intelligence platform that transforms raw spreadsheets (`.xlsx`, `.xls`, `.csv`) into structured, verifiable, and visually explainable analytical insights.

The platform is engineered around an uncompromised foundational rule: **Python remains the authoritative source of numerical truth.** The Large Language Model (Qwen) operates strictly as a natural language query planner and evidence-grounded explainer. It is architecturally forbidden from performing arithmetic directly. All mathematical aggregations, filters, groupings, and statistics are computed deterministically by the Python engine with complete cell-level calculation lineage.

---

## 1. Project Status & Roadmap

| Phase | Module | Status | Architectural Summary |
|---|---|---|---|
| **Phase 1** | Spreadsheet Ingestion & Inspection | **COMPLETED** | OpenPyXL raw & evaluated parsing, cell coordinate preservation, format validation, and responsive progressive ingestion state. |
| **Phase 2** | Sheet Understanding & Table Profiling | **COMPLETED** | Table boundary detection, orientation heuristics (`VERTICAL`, `HORIZONTAL`, `AMBIGUOUS`), semantic data typing, and 0–100 data hygiene scoring. |
| **Phase 3 & 4** | Advanced Table Relationships & Hybrid Queries | **DEFERRED (Post-MVP)** | Cross-sheet relational join discovery and multi-table semantic reconciliation. |
| **Phase 5** | Deterministic Analytical Engine | **COMPLETED** | Explicit operations (`SUM`, `AVERAGE`, `COUNT_ROWS`, `COUNT_VALUES`, `DISTINCT_COUNT`, `MIN`, `MAX`, `MEDIAN`, `FILTER`, `SORT`, `GROUP_BY`, `SUMIFS`, `COUNTIFS`) with pre-execution validation and cell lineage. |
| **Phase 6** | Deterministic Visualization Engine | **COMPLETED** | Headless Matplotlib/Seaborn rendering (`BAR`, `LINE`, `PIE`, `AREA`, `SCATTER`, `HISTOGRAM`), conservative shape recommendation, and session-scoped PNG artifact generation. |
| **Phase 7** | Interactive Operation Builder UI | **COMPLETED** | Point-and-click Next.js analytical workspace, type-adaptive filter builder, multi-aggregation group-by builder, scalar/table result views, and execution audit trail. |
| **Phase 8** | Qwen Natural Language Query Planner & Guardrails | **COMPLETED** | Natural-language query translation to `AnalyticalInstruction`, schema ambiguity disambiguation, hard pre-execution guardrails, latency breakdown grid, and evidence-grounded explanation. |

---

## 2. Architecture & Principle: One Engine, Multiple Interfaces

Sheetsly implements a single, authoritative execution pipeline shared equally by visual click-based UI controls and natural-language query planners:

```
User Natural Language Query                          Point-and-Click Operation Builder
           │                                                         │
           ▼                                                         │
[Qwen Query Planner] (Qwen 3.5 Plus)                                 │
           │                                                         │
           ▼                                                         │
[Structured Query Plan]                                              │
           │                                                         │
           ▼                                                         │
[AI Guardrail]                                                       │
(Detects Ambiguity / Incompatible Types)                             │
           │                                                         │
           ├────────────────────────────┬────────────────────────────┘
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
                         │
                         ▼
            [Evidence-Based Explainer]
            (Cites Exact Lineage Coordinates & Row Counts)
```

### Core Architecture Rules
1. **Qwen Interprets Intent, Python Calculates Truth**: The LLM compiles natural language questions into validated `AnalyticalInstruction` models. It never performs arithmetic or invents numbers.
2. **Ambiguity Stops Execution (No Guessing)**: When a question has multiple valid interpretations (e.g. *"What is the total?"* on a table with both `Units` and `Revenue`), execution stops immediately and returns a structured clarification prompt with schema options.
3. **Hard AI Guardrails**: Every AI-planned instruction must pass the Phase 5 `InstructionValidator` (type validation, valid columns, valid operators) before execution. If validation fails, execution is blocked and the error is displayed.
4. **Evidence Grounding & Source Lineage**: Explanations cite only verified `AnalyticalResult` values and `CalculationLineage` coordinates (e.g. `Sheet1!E2:E9801`, $N$ included rows).
5. **Deterministic Fallback**: If the AI provider is offline or unconfigured, the system continues running seamlessly in Deterministic Fallback Mode with 100% functionality via the Operation Builder.

---

## 3. Implemented Modules & Capabilities

### A. Spreadsheet Ingestion & Inspection (Phase 1)
- **Supported File Formats**: `.xlsx`, `.xls`, `.xlsm`, `.xltx`, and `.csv` (up to 50MB).
- **Cell Coordinate Preservation**: Retains exact 2D cell addresses (e.g., `A1`, `B4`), raw cell values, evaluated values, and formula strings (`fx`).
- **Truthful Progressive Loading**: Features a restrained horizontal indeterminate progress bar (`role="progressbar"`, `aria-busy="true"`) and interaction locking during large dataset uploads (~9.8k rows / ~2 MB).
- **Session File Management**: Safely isolates uploaded workbooks in temporary session directories (`storage/temp/{dataset_id}/`).

### B. Sheet Profiling & Table Detection (Phase 2)
- **Table Region Detection**: Automatically detects multiple candidate tables within a single worksheet, header rows, data ranges, and total/footer rows.
- **Orientation Heuristics**: Deterministically classifies table layouts as `VERTICAL`, `HORIZONTAL`, `AMBIGUOUS`, or `IRREGULAR` with confidence scores and structural signals.
- **Semantic Type Profiling**: Classifies columns into:
  - `MEASURE`: Numeric columns eligible for arithmetic (`SUM`, `AVERAGE`, `MEDIAN`).
  - `CATEGORY`: Categorical dimensions eligible for grouping and axes.
  - `IDENTIFIER`: Unique keys/IDs protected against arithmetic aggregation.
  - `TEMPORAL`: Dates and timestamps used for time series and trend analysis.
- **Data Quality & Hygiene Engine**: Computes a 0–100 hygiene score identifying missing values, mixed data types, duplicate rows, and broken formulas with exact affected cell coordinates.

### C. Deterministic Analytical Engine (Phase 5)
- **Scalar Aggregations**:
  - `SUM`: Arithmetic total of numeric measures (auto-parses currency symbols `$`, `Rp`, and percentages).
  - `AVERAGE`: Arithmetic mean of numeric values.
  - `COUNT_ROWS`: Total record count in selection.
  - `COUNT_VALUES`: Non-empty value count in target column.
  - `DISTINCT_COUNT`: Unique non-empty value count.
  - `MIN` / `MAX`: Smallest / largest numeric or date values.
  - `MEDIAN`: 50th percentile value.
- **Slicing & Sorting**:
  - `FILTER`: Slices records using 13 operators (`equals`, `not_equals`, `contains`, `not_contains`, `starts_with`, `ends_with`, `greater_than`, `less_than`, `greater_or_equal`, `less_or_equal`, `between`, `in_list`, `is_empty`, `is_not_empty`) with `AND` / `OR` boolean combinations.
  - `SORT`: Orders records ascending or descending with optional row limits.
- **Multi-Dimensional Grouping**:
  - `GROUP_BY`: Groups by one or more dimension columns and computes multiple aggregate metrics with custom column aliases.
- **Conditional Aggregations**:
  - `SUMIF`, `SUMIFS`, `COUNTIF`, `COUNTIFS`: Composable conditional operations.

### D. Deterministic Visualization Engine (Phase 6)
- **Supported Chart Types**: `BAR`, `LINE`, `PIE` (Donut), `AREA`, `SCATTER`, `HISTOGRAM`.
- **Conservative Compatibility Validation**: Rejects invalid chart configurations (e.g., rejecting Pie charts with $>10$ categories or negative numbers, rejecting Scatter plots on categorical columns).
- **Automated Recommendation**: Evaluates `AnalyticalResult` shape and recommends preferred chart types with human-readable rationale.
- **Headless Artifact Generation**: Renders clean static PNG graphics via Matplotlib/Seaborn (`Agg` backend) stored in session storage.

### E. Interactive Operation Builder UI (Phase 7)
- **Point-and-Click Configuration**: 3-category operation grid (`Summarize & Calculate`, `Group & Aggregate`, `Slice & Order`).
- **Type-Adaptive Controls**: Dropdowns filter columns based on detected semantic types (e.g. numeric-only for arithmetic).
- **Execution Audit Trail**: Collapsible lineage panel answering *"How was this calculated?"* with source cell coordinates, row inclusion counts, and execution duration in milliseconds.

### F. Qwen Natural Language Query Planner & Guardrails (Phase 8)
- **Plain-Language Querying**: Type questions such as *"What is the total revenue in the West region?"* or *"Compare units sold across products"*.
- **Plan Inspection Card**: Shows the AI-planned operation, target column, filters, and grouping dimensions for user verification before and after execution.
- **Structured Disambiguation**: Interactive clarification prompt when ambiguous terms or multiple numeric measures are queried.
- **Schema-Derived Suggestions**: Proactively suggests 3–5 logical analytical questions tailored to the active worksheet schema.
- **Truthful Multi-Stage Execution**:
  - *Stage 1*: `"Planning analytical query with Qwen..."`
  - *Stage 2*: `"Executing deterministic analysis in Python..."`
- **Execution Stage Latency Grid**: Reports precise wall-clock latency for:
  `Schema Resolution` | `Qwen Planning` | `Guardrail Validation` | `Python Calculation` | `Visualization` | `Evidence Explainer`
- **Evidence-Based Grounding**: Explanations cite exact source ranges (e.g. `Sales!E2:E6`), row counts, and calculation steps.

### G. In-App Product Guidance & "How to Use" Modal
- **Discoverable In-App Guide**: Accessible via the `How to Use & Architecture` button in the landing page and workspace header without losing dataset state.
- **11-Section Comprehensive Curriculum**:
  1. *Getting Started*
  2. *Recommended Workflow*
  3. *Upload & Ingestion Lifecycle*
  4. *Tables & Semantic Types*
  5. *Analysis Builder*
  6. *Deterministic Visualizations*
  7. *AI Architecture & Truth*
  8. *Asking Good AI Questions*
  9. *Understanding AI Results*
  10. *Data Provenance & Evidence*
  11. *Troubleshooting & Fallback Modes*

---

## 4. End-to-End User Workflow

```
1. Upload Spreadsheet (.xlsx, .xls, .csv)
   │
   ▼
2. Deterministic Ingestion & Profiling
   - Structural parsing & cell retention
   - Table boundary & orientation detection
   - Data hygiene score (0–100)
   │
   ▼
3. Choose Analysis Interaction Mode:
   ├── Mode A: Operation Builder (Point-and-click without Excel formulas)
   │    │
   │    ▼
   │   Construct AnalyticalInstruction
   │
   └── Mode B: AI Query Planner (Natural language with Qwen)
        │
        ▼
       Compile AnalyticalInstruction
        │
        ▼
       AI Guardrail Validation (Schema / Type / Operator check)
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
│   ├── tests/                           # 57 automated unit & integration tests
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
│           ├── visualization/           # Chart selector, renderer, recommendation
│           └── ai/                      # Qwen client, planner, guardrails, explainer, orchestrator
│
└── sheetsly_frontend/                   # Next.js 16 Frontend Workspace
    ├── .env.example                     # Frontend environment variable template
    ├── .gitignore                       # Frontend Git ignore rules
    ├── package.json                     # Node.js dependencies (Next.js 16, React 19, Tailwind v4)
    ├── tsconfig.json                    # TypeScript compiler configuration
    ├── next.config.ts                   # Next.js configuration
    ├── app/
    │   ├── layout.tsx                   # Root layout with Google Geist fonts
    │   ├── globals.css                  # Tailwind v4 theme tokens, animations, & tabular numbers
    │   └── page.tsx                     # Workspace coordinator & tab router
    ├── components/
    │   ├── upload/                      # SpreadsheetUploader with progressive loading
    │   ├── workspace/                   # SheetList, DetectedTablesViewer, ActualDataViewer,
    │   │                                # DataQualityPanel, VisualizationViewer, WorkbookHeader,
    │   │                                # HowToUseModal
    │   ├── builder/                     # OperationBuilder, OperationSelector, FilterBuilder,
    │   │                                # GroupByBuilder, SortLimitBuilder, AnalysisResultView
    │   └── ai/                          # AIQueryWorkspace, PlanInterpretationCard,
    │                                    # ClarificationPrompt, EvidenceExplanationCard
    └── lib/
        ├── types.ts                     # TypeScript domain contracts & timing models
        └── api.ts                       # Typed REST API client
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
| `QWEN_BASE_URL` | String | `https://ws-6avfe6m7o2twqw9n.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1` | OpenAI-compatible endpoint URL for DashScope Singapore workspace. |
| `QWEN_ENABLE_THINKING` | Boolean | `false` | Set to `false` for rapid sub-5s analytical planning, or `true` for extended reasoning mode. |
| `DATABASE_ENABLED` | Boolean | `false` | Database toggle (disabled in MVP). |

### Frontend (`sheetsly_frontend/.env.local`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Public URL | `http://127.0.0.1:8000/api/v1` | Base REST API URL accessed by browser client. |

---

## 9. REST API Reference (`/api/v1`)

### AI Natural Language Query Endpoints (Phase 8)
- `POST /api/v1/ai/query` &mdash; Executes end-to-end natural language query: Qwen Planner &rarr; AI Guardrail &rarr; Python Engine &rarr; Visualizer &rarr; Evidence Explainer. Supports `preplanned_instruction` to skip planning when pre-compiled.
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

### Deterministic Visualization Endpoints (Phase 6)
- `POST /api/v1/datasets/{id}/visualize` &mdash; Renders a static Matplotlib chart from a verified `AnalyticalResult`.
- `POST /api/v1/datasets/{id}/visualize/from-instruction` &mdash; Executes analysis and renders chart in a single pipeline step.
- `POST /api/v1/visualization/recommend` &mdash; Recommends compatible chart types for a given analytical result.
- `GET /api/v1/datasets/{id}/charts/{chart_id}/image` &mdash; Serves the static PNG image artifact.

---

## 10. Automated Testing & Verification

### Running Backend Tests (Pytest)
```powershell
cd sheetsly_backend
python -m pytest -p no:pytest_ethereum
```
*Current test suite: **57 unit & integration tests** covering ingestion, quality scoring, scalar aggregations, multi-grouping, filters, lineage, chart rendering, Qwen planning, guardrails, explainer, and REST API routes (**100% passing**).*

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
- **Truthful Loading**: Horizontal indeterminate progress bar for file ingestion; multi-stage textual status transitions for AI queries (`"Planning analytical query with Qwen..."` &rarr; `"Executing deterministic analysis in Python..."`).
- **Typography & Alignment**: Uses Google Geist Sans for clean UI labels and Google Geist Mono for cell coordinates and numbers (`font-variant-numeric: tabular-nums`).
- **Accessibility**: All interactive elements have visible focus rings (`focus-visible:ring-2`), accessible `aria-label` tags on icon buttons, and WCAG AA contrast ratios ($\ge 4.5:1$).

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
