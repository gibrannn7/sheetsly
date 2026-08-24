'use client';

import React, { useEffect, useState } from 'react';

interface HowToUseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type GuideSection =
  | 'getting-started'
  | 'ingestion'
  | 'dataset-profiling'
  | 'analysis-builder'
  | 'visualization'
  | 'ai-architecture'
  | 'ai-questions'
  | 'ai-results'
  | 'provenance'
  | 'troubleshooting'
  | 'workflow';

interface SectionItem {
  id: GuideSection;
  title: string;
  category: string;
}

const SECTIONS: SectionItem[] = [
  { id: 'getting-started', title: '1. Getting Started', category: 'Overview' },
  { id: 'workflow', title: '2. Recommended Workflow', category: 'Overview' },
  { id: 'ingestion', title: '3. Upload & Ingestion', category: 'Data Understanding' },
  { id: 'dataset-profiling', title: '4. Tables & Schema Types', category: 'Data Understanding' },
  { id: 'analysis-builder', title: '5. Analysis Builder', category: 'Deterministic Analysis' },
  { id: 'visualization', title: '6. Visualizations', category: 'Deterministic Analysis' },
  { id: 'ai-architecture', title: '7. AI Architecture & Truth', category: 'AI Intelligence' },
  { id: 'ai-questions', title: '8. Asking Good AI Questions', category: 'AI Intelligence' },
  { id: 'ai-results', title: '9. Understanding AI Results', category: 'AI Intelligence' },
  { id: 'provenance', title: '10. Data Provenance & Evidence', category: 'Auditing' },
  { id: 'troubleshooting', title: '11. Troubleshooting & Fallback', category: 'Auditing' },
];

export const HowToUseModal: React.FC<HowToUseModalProps> = ({ isOpen, onClose }) => {
  const [activeSection, setActiveSection] = useState<GuideSection>('getting-started');

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="how-to-use-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div className="bg-white w-full max-w-4xl max-h-[88vh] rounded-xl border border-slate-300 shadow-xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 rounded bg-slate-900 text-white flex items-center justify-center text-xs font-bold font-mono">
              ?
            </div>
            <div>
              <h2 id="how-to-use-title" className="text-sm font-bold text-slate-900">
                How to Use Sheetsly
              </h2>
              <p className="text-xs text-slate-500">
                Comprehensive guide to deterministic spreadsheet intelligence and AI query planning.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close guide"
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-200/60 transition-colors cursor-pointer text-xs font-bold"
          >
            ✕
          </button>
        </div>

        {/* Modal Body: Sidebar Nav + Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Navigation Sidebar */}
          <nav aria-label="Guide sections" className="w-64 border-r border-slate-200 bg-slate-50/70 p-3 overflow-y-auto space-y-1">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2 py-1">
              Table of Contents
            </div>
            {SECTIONS.map((sec) => (
              <button
                key={sec.id}
                type="button"
                onClick={() => setActiveSection(sec.id)}
                className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer block ${
                  activeSection === sec.id
                    ? 'bg-slate-900 text-white font-semibold shadow-2xs'
                    : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900'
                }`}
              >
                {sec.title}
              </button>
            ))}
          </nav>

          {/* Section Content Area */}
          <div className="flex-1 p-6 overflow-y-auto text-xs text-slate-700 space-y-4">
            {/* 1. Getting Started */}
            {activeSection === 'getting-started' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">1. Getting Started with Sheetsly</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    Sheetsly is an interactive spreadsheet intelligence platform designed to eliminate analytical guesswork. It turns raw spreadsheets into structured, verifiable insights with exact cell-level provenance.
                  </p>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                  <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px]">Key Architectural Foundation</h4>
                  <p className="leading-relaxed">
                    <strong>&ldquo;Qwen interprets intent. Python calculates truth.&rdquo;</strong>
                  </p>
                  <p className="text-slate-600 leading-relaxed">
                    Unlike ordinary AI chatbots that estimate or hallucinate calculations, Sheetsly routes every analytical question through a validated deterministic Python engine. The AI translates your questions into structured instructions, while Python performs the mathematical calculation directly against your spreadsheet cells.
                  </p>
                </div>

                <div className="space-y-2">
                  <h4 className="font-bold text-slate-900 text-xs">Supported File Formats</h4>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 pl-1">
                    <li><strong>Excel Workbooks:</strong> <code className="font-mono bg-slate-100 px-1 rounded">.xlsx</code>, <code className="font-mono bg-slate-100 px-1 rounded">.xls</code>, <code className="font-mono bg-slate-100 px-1 rounded">.xlsm</code>, <code className="font-mono bg-slate-100 px-1 rounded">.xltx</code></li>
                    <li><strong>Delimited Files:</strong> <code className="font-mono bg-slate-100 px-1 rounded">.csv</code> (comma-separated values)</li>
                    <li><strong>File Size Ceiling:</strong> Up to 50 MB per workbook.</li>
                  </ul>
                </div>
              </div>
            )}

            {/* 2. Recommended Workflow */}
            {activeSection === 'workflow' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">2. Recommended Analytical Workflow</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    Follow this end-to-end workflow to analyze any spreadsheet with complete confidence:
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-2.5">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">Step 1</span>
                    <strong className="text-slate-900">Upload & Ingest:</strong> Drop your file. The system inspects structure, parses cells, detects tables, profiles types, and assesses data hygiene.
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">Step 2</span>
                    <strong className="text-slate-900">Inspect Structure:</strong> Review detected tables, column types (measures vs dimensions), and data quality score.
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">Step 3</span>
                    <strong className="text-slate-900">Choose Analysis Path:</strong>
                    <ul className="list-disc list-inside mt-1 text-slate-600 space-y-0.5 pl-2">
                      <li><strong>AI Query Planner:</strong> Ask natural-language questions in plain English or Indonesian.</li>
                      <li><strong>Analysis Builder:</strong> Use the point-and-click UI to build custom aggregations, multi-grouping, and filters without formulas.</li>
                    </ul>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">Step 4</span>
                    <strong className="text-slate-900">Verify Plan & Lineage:</strong> Inspect the planned instruction, row count, and source cell coordinates (e.g. <code className="font-mono">Sheet1!E2:E9801</code>).
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">Step 5</span>
                    <strong className="text-slate-900">Visualize & Export:</strong> Generate conservative charts (Bar, Line, Pie, Area, Scatter, Histogram) and download high-resolution PNGs.
                  </div>
                </div>
              </div>
            )}

            {/* 3. Upload & Ingestion */}
            {activeSection === 'ingestion' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">3. Upload & Ingestion Lifecycle</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    When you drop a file, Sheetsly executes an atomic ingestion pipeline on the backend:
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded bg-slate-200 text-slate-800 font-mono font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">1</span>
                    <div>
                      <strong className="text-slate-900">Secure Temporary Storage:</strong> Saves the file to a session-scoped directory in <code className="font-mono">storage/temp/</code>.
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded bg-slate-200 text-slate-800 font-mono font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">2</span>
                    <div>
                      <strong className="text-slate-900">2D Cell Coordinate Parser:</strong> Preserves raw values, evaluated values, and formula strings (<code className="font-mono text-amber-700">fx</code>) with coordinate retention.
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded bg-slate-200 text-slate-800 font-mono font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">3</span>
                    <div>
                      <strong className="text-slate-900">Table & Orientation Detection:</strong> Detects multiple tables per sheet and determines layout (<code className="font-mono">VERTICAL</code>, <code className="font-mono">HORIZONTAL</code>, <code className="font-mono">AMBIGUOUS</code>).
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded bg-slate-200 text-slate-800 font-mono font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">4</span>
                    <div>
                      <strong className="text-slate-900">Data Quality & Hygiene Scoring:</strong> Analyzes missing values, mixed data types, and duplicate rows, producing a 0–100 hygiene score.
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                  <span className="font-bold text-slate-800 block mb-0.5">What &ldquo;Dataset Ready&rdquo; Means:</span>
                  <p className="text-slate-600 leading-relaxed">
                    Once ingestion completes, the workspace unlocks all tabs: AI Query Planner, Analysis Builder, Detected Tables, Cell Grid, Visualizations, and Quality Report.
                  </p>
                </div>
              </div>
            )}

            {/* 4. Tables & Schema Types */}
            {activeSection === 'dataset-profiling' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">4. Tables & Semantic Column Types</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    Sheetsly profiles every column to prevent invalid calculations (e.g. attempting to sum a phone number or customer name):
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
                      MEASURE (Numeric)
                    </span>
                    <p className="text-slate-700">Columns containing quantifiable numbers (e.g. <code className="font-mono">Revenue</code>, <code className="font-mono">Units</code>, <code className="font-mono">Salary</code>). Eligible for <code className="font-mono">SUM</code>, <code className="font-mono">AVERAGE</code>, <code className="font-mono">MEDIAN</code>.</p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-800 border border-slate-300">
                      CATEGORY (Dimension)
                    </span>
                    <p className="text-slate-700">Columns representing qualitative groups (e.g. <code className="font-mono">Region</code>, <code className="font-mono">Department</code>, <code className="font-mono">Product</code>). Eligible for grouping and category axes.</p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                      IDENTIFIER
                    </span>
                    <p className="text-slate-700">Unique keys or IDs (e.g. <code className="font-mono">EmployeeID</code>, <code className="font-mono">OrderNumber</code>). Protected against accidental arithmetic aggregation.</p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-900 border border-purple-300">
                      TEMPORAL
                    </span>
                    <p className="text-slate-700">Dates, timestamps, and fiscal periods (e.g. <code className="font-mono">OrderDate</code>, <code className="font-mono">Year</code>). Used for time series trend analysis and Area/Line charts.</p>
                  </div>
                </div>
              </div>
            )}

            {/* 5. Analysis Builder */}
            {activeSection === 'analysis-builder' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">5. Operation Builder (Point-and-Click Analysis)</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    The Operation Builder allows users to perform multi-stage data operations without writing Excel formulas or SQL queries.
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-1">Supported Operation Types:</strong>
                    <ul className="grid grid-cols-2 gap-1 text-slate-600 font-mono text-[11px]">
                      <li>• SUM (Total)</li>
                      <li>• AVERAGE (Mean)</li>
                      <li>• COUNT_ROWS (Records)</li>
                      <li>• COUNT_VALUES (Non-nulls)</li>
                      <li>• DISTINCT_COUNT (Uniques)</li>
                      <li>• MIN / MAX (Extremes)</li>
                      <li>• MEDIAN (50th percentile)</li>
                      <li>• GROUP_BY (Dimensions)</li>
                      <li>• FILTER (Slice records)</li>
                      <li>• SORT / LIMIT (Rankings)</li>
                    </ul>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-1">Filter Operators:</strong>
                    <p className="text-slate-600 leading-relaxed">
                      13 operators supported: <code className="font-mono">equals</code>, <code className="font-mono">not_equals</code>, <code className="font-mono">contains</code>, <code className="font-mono">starts_with</code>, <code className="font-mono">ends_with</code>, <code className="font-mono">greater_than</code>, <code className="font-mono">less_than</code>, <code className="font-mono">between</code>, <code className="font-mono">in_list</code>, <code className="font-mono">is_empty</code>, etc. with <code className="font-mono">AND</code> / <code className="font-mono">OR</code> logic.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 6. Visualizations */}
            {activeSection === 'visualization' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">6. Deterministic Visualization Engine</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    Sheetsly generates static publication-ready charts using Matplotlib/Seaborn with conservative shape validation.
                  </p>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-2">
                  <h4 className="font-bold text-slate-900 text-xs">Conservative Compatibility Rules</h4>
                  <ul className="list-disc list-inside space-y-1 text-slate-600">
                    <li><strong>Pie / Donut Charts:</strong> Recommended only for single-series part-to-whole data with &le;10 positive categories. Rejected if negative values exist.</li>
                    <li><strong>Line / Area Charts:</strong> Recommended when the X-axis is a temporal or ordered sequence.</li>
                    <li><strong>Scatter Plots:</strong> Requires two numeric columns for correlation analysis.</li>
                    <li><strong>Histograms:</strong> Requires a single continuous numeric metric for distribution binning.</li>
                  </ul>
                </div>

                <p className="text-slate-600">
                  Every chart includes an integrated lineage footer linking the visualization directly to its source range (e.g. <code className="font-mono">Sheet1!A1:E6</code>) and row count.
                </p>
              </div>
            )}

            {/* 7. AI Architecture & Truth */}
            {activeSection === 'ai-architecture' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">7. AI Architecture: Why Qwen Does Not Calculate</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    The core differentiator of Sheetsly is its zero-hallucination execution pipeline:
                  </p>
                </div>

                <div className="p-4 bg-slate-900 text-white rounded-lg font-mono text-[11px] space-y-2">
                  <div className="text-slate-400 uppercase text-[10px] font-bold tracking-wider">Execution Pipeline</div>
                  <div>User Natural Language Question</div>
                  <div className="text-slate-400">↓ (Qwen 3.5 Plus Intent Translation)</div>
                  <div className="text-emerald-400">Structured AnalyticalInstruction (JSON)</div>
                  <div className="text-slate-400">↓ (AI Guardrail Schema & Type Checks)</div>
                  <div className="text-amber-400">Instruction Validation Gate</div>
                  <div className="text-slate-400">↓ (Authoritative Execution)</div>
                  <div className="text-blue-300">Python / Pandas Deterministic Calculation</div>
                  <div className="text-slate-400">↓ (Evidence Grounding)</div>
                  <div className="text-white">Verified Result + Cell Lineage (e.g. Sheet1!E2:E9801)</div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                  <strong className="text-slate-900">Why this matters:</strong>
                  <p className="text-slate-600 leading-relaxed">
                    LLMs frequently produce subtle arithmetic errors when summing large numbers or applying complex filters. By confining Qwen strictly to intent parsing, your numbers are 100% mathematically proven and auditable.
                  </p>
                </div>
              </div>
            )}

            {/* 8. Asking Good AI Questions */}
            {activeSection === 'ai-questions' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">8. Asking Good AI Questions</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    You can ask questions in natural language. Sheetsly automatically resolves column names, operations, and filters.
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md">
                    <span className="font-bold text-emerald-900 block mb-1 text-[11px] uppercase">Supported / Clear Questions (Recommended):</span>
                    <ul className="space-y-1 font-mono text-[11px] text-emerald-950">
                      <li>&bull; &ldquo;What is the total revenue?&rdquo; &rarr; SUM(Revenue)</li>
                      <li>&bull; &ldquo;Show average units sold by region&rdquo; &rarr; GROUP_BY(Region) + AVG(Units)</li>
                      <li>&bull; &ldquo;What is total revenue in the North region?&rdquo; &rarr; SUM(Revenue) with FILTER(Region == &apos;North&apos;)</li>
                      <li>&bull; &ldquo;Find the top 5 products by revenue&rdquo; &rarr; GROUP_BY(Product) + SORT(DESC) + LIMIT(5)</li>
                    </ul>
                  </div>

                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
                    <span className="font-bold text-amber-900 block mb-1 text-[11px] uppercase">Ambiguous Questions (Triggers Disambiguation):</span>
                    <p className="text-amber-950 mb-1">
                      &ldquo;What is the total?&rdquo; (When table has both <code className="font-mono">Units</code> and <code className="font-mono">Revenue</code>).
                    </p>
                    <p className="text-slate-600">
                      Instead of guessing, Sheetsly presents an interactive button prompt asking you to pick the target column.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 9. Understanding AI Results */}
            {activeSection === 'ai-results' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">9. Understanding AI Output Cards</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    Every AI query response is divided into 4 transparent cards:
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-bold text-slate-900 block">1. Planned Analytical Instruction:</span>
                    <p className="text-slate-600">Shows the operation, target column, filters, and grouping dimensions planned by Qwen.</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-bold text-slate-900 block">2. Evidence-Based Analysis:</span>
                    <p className="text-slate-600">Plain English factual summary citing exact source cell coordinates and row counts.</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-bold text-slate-900 block">3. Execution Stage Latency Breakdown:</span>
                    <p className="text-slate-600">Monospaced latency badges showing exact milliseconds for Schema, Qwen Planning, Guardrails, Python Calculation, and Visualization.</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-bold text-slate-900 block">4. Verified Result & Lineage Trace:</span>
                    <p className="text-slate-600">The authoritative numerical answer calculated by Python with complete row inclusion metrics.</p>
                  </div>
                </div>
              </div>
            )}

            {/* 10. Data Provenance & Evidence */}
            {activeSection === 'provenance' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">10. Data Provenance & Source Cell Traceability</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    Every result produced by Sheetsly contains a strict audit trail:
                  </p>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-2 font-mono text-[11px]">
                  <div className="text-slate-500 font-bold uppercase text-[10px]">Sample Provenance Metadata</div>
                  <div>Source Range: <span className="font-bold text-slate-900">Sheet1!E2:E9801</span></div>
                  <div>Row Inclusion: <span className="font-bold text-slate-900">9,800 of 9,800 records (0 excluded)</span></div>
                  <div>Filters Applied: <span className="font-bold text-slate-900">None</span></div>
                  <div>Execution Duration: <span className="font-bold text-slate-900">5.82 ms</span></div>
                </div>

                <p className="text-slate-600 leading-relaxed">
                  This guarantees that any stakeholder or compliance auditor can verify the exact cells in the original spreadsheet that contributed to the final metric.
                </p>
              </div>
            )}

            {/* 11. Troubleshooting */}
            {activeSection === 'troubleshooting' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">11. Troubleshooting & Fallback Modes</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    How to resolve common operational scenarios:
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-0.5">AI Provider Offline / Unconfigured:</strong>
                    <p className="text-slate-600">
                      If <code className="font-mono bg-white px-1 border rounded">DASHSCOPE_API_KEY</code> is not configured or network connectivity fails, Sheetsly activates <strong>Deterministic Fallback Mode</strong>. You can continue using the point-and-click <strong>Analysis Builder</strong> and <strong>Visualizations</strong> with 100% full analytical functionality.
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-0.5">AI Guardrail Blocked Execution:</strong>
                    <p className="text-slate-600">
                      If a query attempts an invalid operation (e.g. summing text columns or referencing non-existent columns), the guardrail blocks execution before calculation and explains the schema conflict.
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-0.5">Large Dataset Ingestion (~2 MB+):</strong>
                    <p className="text-slate-600">
                      For files with &gt;9,000 rows, ingestion may take 5–15 seconds. An active horizontal progress bar indicates background processing.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div className="text-[11px] text-slate-500 font-mono">
            Sheetsly v1.0 &bull; Deterministic Spreadsheet Intelligence
          </div>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-semibold shadow-2xs cursor-pointer transition-colors"
          >
            Got it, return to workspace
          </button>
        </div>
      </div>
    </div>
  );
};
