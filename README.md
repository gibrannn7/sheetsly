# Sheetsly

> **AI-Assisted Spreadsheet Intelligence Workspace**  
> *BETA Baseline (Phases 1, 2, 5, 6 & 7)*

Sheetsly is a deterministic spreadsheet intelligence platform that transforms raw spreadsheets (`.xlsx`, `.xls`, `.csv`) into structured, verifiable, and visually explainable analytical insights.

The platform is designed around a fundamental engineering rule: **Python remains the authoritative source of numerical truth.** The user interface never calculates arithmetic, totals, or aggregations independently. Instead, it constructs validated analytical instructions executed by a deterministic Python engine with complete cell-level calculation lineage.

---

## 1. Project Status & Roadmap

| Phase | Module | Status | Architectural Summary |
|---|---|---|---|
| **Phase 1** | Spreadsheet Ingestion & Inspection | **COMPLETED (BETA)** | OpenPyXL raw & evaluated parsing, cell coordinate preservation, format validation. |
| **Phase 2** | Sheet Understanding & Table Profiling | **COMPLETED (BETA)** | Table boundary detection, orientation heuristics (Vertical/Horizontal), semantic data typing, and 0–100 data hygiene scoring. |
| **Phase 3 & 4** | Advanced Table Relationships & Hybrid Queries | **DEFERRED (Post-MVP)** | Cross-sheet join discovery and multi-table semantic reconciliation. |
| **Phase 5** | Deterministic Analytical Engine | **COMPLETED (BETA)** | Explicit operations (`SUM`, `AVERAGE`, `COUNT_ROWS`, `COUNT_VALUES`, `DISTINCT_COUNT`, `MIN`, `MAX`, `MEDIAN`, `FILTER`, `SORT`, `GROUP_BY`, `SUMIFS`, `COUNTIFS`) with pre-execution validation and cell lineage. |
| **Phase 6** | Deterministic Visualization Engine | **COMPLETED (BETA)** | Headless Matplotlib/Seaborn rendering (`BAR`, `LINE`, `PIE`, `AREA`, `SCATTER`, `HISTOGRAM`), conservative recommendation, and PNG artifact generation. |
| **Phase 7** | Interactive Operation Builder UI | **COMPLETED (BETA)** | Point-and-click Next.js analytical workspace, type-adaptive filter builder, multi-aggregation group-by builder, scalar/table result views, and execution audit trail. |
| **Phase 8** | Qwen Natural Language Query Planner | **UPCOMING (NOT IN BETA)** | LLM intent parsing compiling natural language queries into validated `AnalyticalInstruction` payloads. |

---

## 2. Architecture & Principle: One Engine, Multiple Interfaces

Sheetsly implements a single, authoritative execution pipeline shared by both visual click-based UI controls and future natural-language query planners:

```
User Click Interaction (Operation Builder)       [Future] Natural Language Query
                    │                                            │
                    ▼                                            ▼
                    └───────────────┬────────────────────────────┘
                                    │
                                    ▼
                          AnalyticalInstruction
                                    │
                                    ▼
                         [Instruction Validator]
                         (Pre-execution Type & Shape Checks)
                                    │
                                    ▼
                    [Deterministic Analytical Engine]
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
```

### Core Architecture Rules
1. **Authoritative Calculation**: Python / Pandas performs all mathematical calculations. The frontend is strictly a presentation and configuration layer.
2. **Deterministic Contract**: The `AnalyticalInstruction` model acts as the standardized, validated contract between interfaces and the calculation engine.
3. **Traceability**: Every result retains an immutable `CalculationLineage` payload citing exact source worksheets, cell ranges (e.g. `Sales!E2:E128`), included/excluded row counts, and execution step traces.

---

## 3. Current AI Status

> [!IMPORTANT]
> **AI / LLM integration is NOT implemented in the current BETA baseline.**
> 
> There is currently no active LLM performing spreadsheet parsing or calculating numbers. In the upcoming Phase 8, Qwen (or compatible LLMs) will act **solely as a natural language query planner** to compile user questions into validated `AnalyticalInstruction` objects. The LLM will never calculate numerical answers directly from raw spreadsheet data.

---

## 4. Feature Summary

### A. Spreadsheet Ingestion & Understanding (Phases 1 & 2)
- **Supported File Formats**: `.xlsx`, `.xls`, `.xlsm`, `.xltx`, and `.csv` (up to 50MB).
- **Cell Coordinate Preservation**: Retains exact 2D cell addresses (e.g., `A1`, `B4`), raw cell values, evaluated values, and formula strings (`fx`).
- **Table Region Detection**: Automatically detects multiple candidate tables within a single worksheet, header rows, data ranges, and total/footer rows.
- **Orientation Heuristics**: Deterministically classifies table layouts as `VERTICAL`, `HORIZONTAL`, `AMBIGUOUS`, or `IRREGULAR` with confidence percentages.
- **Data Quality & Hygiene Engine**: Computes an overall 0–100 hygiene score, identifying missing values, mixed data types, duplicate records, and broken formulas with exact affected cell coordinates.

### B. Deterministic Analytical Engine (Phase 5)
- **Scalar Aggregations**:
  - `SUM`: Arithmetic total of numeric measures (auto-parses currency symbols `$`, `Rp` and percentages).
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

### C. Deterministic Visualization Engine (Phase 6)
- **Supported Chart Types**: `BAR`, `LINE`, `PIE` (Donut), `AREA`, `SCATTER`, `HISTOGRAM`.
- **Conservative Compatibility Validation**: Rejects invalid chart configurations (e.g., rejecting Pie charts with $>10$ categories or negative numbers, rejecting Scatter plots on categorical columns).
- **Automated Recommendation**: Evaluates `AnalyticalResult` shape and recommends preferred chart types with human-readable rationale.
- **Headless Artifact Generation**: Renders clean static PNG graphics via Matplotlib/Seaborn (`Agg` backend) stored in session-scoped storage.

### D. Interactive Operation Builder UI (Phase 7)
- **Point-and-Click Configuration**: 3-category operation grid (`Summarize & Calculate`, `Group & Aggregate`, `Slice & Order`).
- **Type-Adaptive Controls**: Dropdowns filter columns based on detected semantic types (e.g. numeric-only for arithmetic).
- **Execution Audit Trail**: Collapsible lineage panel answering *"How was this calculated?"* with source cell coordinates, row inclusion counts, and execution duration in milliseconds.

---

## 5. Repository Structure

```
sheetsly/
├── BLUEPRINT.md                         # Authoritative architectural specification
├── README.md                            # Comprehensive developer documentation
├── .gitignore                           # Root Git ignore rules
├── .env.example                         # Root environment configuration template
├── sales_q3.csv                         # Sample verification dataset (Sales)
├── hr_payroll.xlsx                      # Sample verification dataset (Payroll/Quality)
├── correlation_test.csv                 # Sample verification dataset (Scatter/Histogram)
│
├── sheetsly_backend/                    # Python FastAPI Backend
│   ├── .env.example                     # Backend environment variable template
│   ├── .gitignore                       # Backend Git ignore rules
│   ├── pytest.ini                       # Pytest test configuration
│   ├── requirements.txt                 # Backend Python dependencies
│   ├── storage/
│   │   └── temp/                        # Session storage for uploaded files and charts
│   │       └── .gitkeep
│   ├── tests/                           # 42 automated unit & integration tests
│   └── app/
│       ├── main.py                      # FastAPI application entrypoint
│       ├── core/                        # Configuration, logging, domain errors
│       ├── api/                         # REST API routes (/api/v1)
│       ├── storage/                     # Isolated filesystem manager
│       └── engine/
│           ├── ingestion/               # OpenPyXL parser, orientation, quality engine
│           ├── analytics/               # Analytical engine, filters, aggregations, lineage
│           └── visualization/           # Chart selector, renderer, recommendation
│
└── sheetsly_frontend/                   # Next.js 16 Frontend Workspace
    ├── .env.example                     # Frontend environment variable template
    ├── .gitignore                       # Frontend Git ignore rules
    ├── package.json                     # Node.js dependencies (Next.js, React, Tailwind)
    ├── tsconfig.json                    # TypeScript compiler configuration
    ├── next.config.ts                   # Next.js configuration
    ├── app/
    │   ├── layout.tsx                   # Root layout with Google Geist fonts
    │   ├── globals.css                  # Tailwind v4 theme tokens & tabular numbers
    │   └── page.tsx                     # Workspace coordinator & tab router
    ├── components/
    │   ├── upload/                      # File drag-and-drop ingestion component
    │   ├── workspace/                   # Sheet list, table viewer, grid viewer, quality panel
    │   └── builder/                     # Operation selector, filter builder, result viewer
    └── lib/
        ├── types.ts                     # TypeScript domain contracts
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

# 5. Start backend development server
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend will be live at: `http://127.0.0.1:8000` (API documentation at `http://127.0.0.1:8000/docs`).

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
| `DEBUG` | Boolean | `true` | Enables detailed debug logs and traceback reporting. |
| `BACKEND_HOST` | String | `127.0.0.1` | Network interface to bind backend server. |
| `BACKEND_PORT` | Integer | `8000` | HTTP port for backend server. |
| `FRONTEND_URL` | String | `http://localhost:3000` | Primary frontend origin for CORS policies. |
| `CORS_ORIGINS` | String | `http://localhost:3000,http://127.0.0.1:3000` | Comma-separated list of allowed CORS origins. |
| `MAX_UPLOAD_SIZE_MB` | Integer | `50` | Maximum allowed file upload size in megabytes. |
| `TEMP_FILE_DIRECTORY` | String | `./storage/temp` | Directory for session-scoped dataset files and charts. |
| `DASHSCOPE_API_KEY` | Secret | `""` | *(Reserved for Phase 8)* DashScope / Qwen API key. |
| `QWEN_MODEL` | String | `qwen3.5-plus` | *(Reserved for Phase 8)* Model identifier. |
| `DATABASE_ENABLED` | Boolean | `false` | Database toggle (disabled in BETA). |

### Frontend (`sheetsly_frontend/.env.local`)

| Variable | Type | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | Public URL | `http://127.0.0.1:8000/api/v1` | Base REST API URL accessed by browser client. |

---

## 9. REST API Reference (`/api/v1`)

### Ingestion & Worksheet Endpoints
- `GET /api/v1/health` &mdash; Health check and service readiness status.
- `POST /api/v1/datasets/upload` &mdash; Uploads `.xlsx`/`.csv` file; triggers inspection and returns `WorkbookOverview`.
- `GET /api/v1/datasets/{id}` &mdash; Retrieves cached metadata and quality report for a dataset.
- `GET /api/v1/datasets/{id}/sheets` &mdash; Lists detected worksheets, table candidates, and dimensions.
- `GET /api/v1/datasets/{id}/sheets/{sheet_name}/data` &mdash; Paginated 2D cell grid with formulas and raw/parsed values.
- `DELETE /api/v1/datasets/{id}` &mdash; Deletes temporary dataset session and generated chart artifacts.

### Deterministic Analytics Endpoints
- `POST /api/v1/datasets/{id}/analyze` &mdash; Executes an `AnalyticalInstruction` and returns a verified `AnalyticalResult`.
- `GET /api/v1/operations/catalog` &mdash; Returns list of supported analytical operations and parameters.

### Deterministic Visualization Endpoints
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
*Current test suite: **42 tests covering ingestion, quality scoring, scalar aggregations, multi-grouping, filters, lineage, chart rendering, and API routes** (100% passing).*

### Running Frontend Production Build
```powershell
cd sheetsly_frontend
npm run build
```
*Compiled in Next.js 16 (Turbopack + TypeScript) with **0 errors**.*

---

## 11. Frontend Design & Impeccable Quality Standards

The frontend interface strictly conforms to the **Impeccable `Operate` Mode** design standards:
- **Zero AI Slop**: No emojis, no glowing cards, no glassmorphism, no purple/blue AI gradients, and no fake blinking/pulsing activity dots.
- **Truthful States**: Action buttons show truthful text (`"Executing Analysis..."`) without animated spinner loops.
- **Typography**: Uses Google Geist Sans for clean UI labels and Google Geist Mono for cell coordinates and numbers (`font-variant-numeric: tabular-nums`).
- **Accessibility**: All interactive elements have visible focus rings (`focus-visible:ring-2`), accessible `aria-label` tags on icon buttons, and WCAG AA contrast ratios ($\ge 4.5:1$).

---

## 12. Security & Known Limitations

1. **Storage Lifecycle**: Datasets and chart artifacts are stored in temporary local session directories (`storage/temp/{dataset_id}/`). Long-term persistence or database storage is deferred to future milestones.
2. **Single-User Session**: Authentication, user accounts, and multi-tenant access control are not part of the MVP BETA scope.
3. **AI Guardrails**: The LLM interface is intentionally disabled in this baseline to prove deterministic calculation integrity first.

---

## 13. BETA Baseline Notice

This repository represents the frozen **Sheetsly BETA baseline**. All deterministic data ingestion, table profiling, analytical execution, visualization, and Operation Builder UI features are verified and operational. Natural language AI query planning will be added in Phase 8.
