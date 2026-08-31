'use client';

import React, { useState } from 'react';
import { useTranslation } from '../../lib/i18n';

type ExampleTab = 'formula' | 'analytical' | 'chart';

export const LandingExamplesSection: React.FC = () => {
  const { dictionary } = useTranslation();
  const [activeTab, setActiveTab] = useState<ExampleTab>('formula');
  const t = dictionary.landing.examples;

  return (
    <div className="w-full space-y-6">
      {/* Tab Selectors */}
      <div className="flex items-center justify-center">
        <div className="inline-flex p-0.5 rounded-lg bg-slate-200/80 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-xs font-semibold">
          <button
            type="button"
            onClick={() => setActiveTab('formula')}
            className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
              activeTab === 'formula'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {t.tab1Label}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('analytical')}
            className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
              activeTab === 'analytical'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {t.tab2Label}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('chart')}
            className={`px-3.5 py-1.5 rounded-md transition-all cursor-pointer ${
              activeTab === 'chart'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {t.tab3Label}
          </button>
        </div>
      </div>

      {/* Example Box */}
      <div className="p-6 md:p-8 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
        {activeTab === 'formula' && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            <div className="md:col-span-6 space-y-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                  Formula Insertion
                </span>
                <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Natural Language to Excel Formula
                </h4>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-xs text-slate-800 dark:text-slate-200">
                <div className="text-[10px] text-slate-400 font-sans uppercase font-bold mb-1">Instruction</div>
                <p>&ldquo;{t.ex1UserPrompt}&rdquo;</p>
              </div>

              <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1 leading-relaxed">
                <p>• Identifies data rows in <code>Sheet1!D2:D7</code></p>
                <p>• Verifies target cell <code>D10</code> is empty</p>
                <p>• Inserts genuine formula <code>=SUM(D2:D7)</code> rather than static arithmetic</p>
              </div>
            </div>

            <div className="md:col-span-6 p-5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300">Transaction Output</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold">
                  2 Cells Mutated
                </span>
              </div>

              <div className="space-y-2">
                <div className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex justify-between items-center">
                  <span className="text-slate-500">Cell C10</span>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">&quot;TOTAL&quot;</span>
                </div>
                <div className="p-2.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex justify-between items-center">
                  <span className="text-slate-500">Cell D10</span>
                  <span className="font-semibold text-slate-900 dark:text-slate-100">=SUM(D2:D7)</span>
                </div>
              </div>

              <div className="text-[11px] text-slate-500 pt-1 font-sans">
                {t.ex1Lineage}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytical' && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            <div className="md:col-span-6 space-y-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                  Deterministic Query
                </span>
                <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Zero-Hallucination Query Execution
                </h4>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-xs text-slate-800 dark:text-slate-200">
                <div className="text-[10px] text-slate-400 font-sans uppercase font-bold mb-1">Question</div>
                <p>&ldquo;{t.ex2UserPrompt}&rdquo;</p>
              </div>

              <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1 leading-relaxed">
                <p>• AST generator parses aggregation and sort criteria</p>
                <p>• Python executes exact calculation on matrix range <code>Sheet1!B2:D7</code></p>
                <p>• Provides full coordinate lineage without LLM math approximation</p>
              </div>
            </div>

            <div className="md:col-span-6 p-5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2 font-sans">
                <span className="text-[11px] font-bold text-slate-900 dark:text-slate-100">Result</span>
                <span className="text-[10px] font-mono text-slate-500">12.4ms Runtime</span>
              </div>

              <div className="p-3.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 font-sans">
                <div className="text-base font-bold text-slate-900 dark:text-slate-100">
                  North Region ($64,200)
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 font-sans">
                  Accounted for 43.3% of total sales across 6 regional territories.
                </p>
              </div>

              <div className="text-[11px] text-slate-500 font-mono">
                {t.ex2Lineage}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'chart' && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            <div className="md:col-span-6 space-y-4">
              <div className="space-y-1">
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
                  Visualization
                </span>
                <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">
                  Context-Aware Chart Placement
                </h4>
              </div>

              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 font-mono text-xs text-slate-800 dark:text-slate-200">
                <div className="text-[10px] text-slate-400 font-sans uppercase font-bold mb-1">Instruction</div>
                <p>&ldquo;{t.ex3UserPrompt}&rdquo;</p>
              </div>

              <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1 leading-relaxed">
                <p>• Validates category cardinality meets chart rules (&le;7 categories for pie)</p>
                <p>• Renders clean static SVG chart with exact percentage splits</p>
                <p>• Places visualization artifact into target coordinates <code>B12:G24</code></p>
              </div>
            </div>

            <div className="md:col-span-6 p-5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-3 text-xs">
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2 font-mono">
                <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300">Chart Artifact</span>
                <span className="text-[10px] text-slate-500">Destination: B12:G24</span>
              </div>

              <div className="p-3 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex items-center justify-around">
                <div className="w-20 h-20">
                  <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#475569" strokeWidth="24" strokeDasharray="65 175" strokeDashoffset="0" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#64748b" strokeWidth="24" strokeDasharray="50 190" strokeDashoffset="-65" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#94a3b8" strokeWidth="24" strokeDasharray="45 195" strokeDashoffset="-115" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#cbd5e1" strokeWidth="24" strokeDasharray="35 205" strokeDashoffset="-160" />
                  </svg>
                </div>
                <div className="space-y-1 font-mono text-[10px] text-slate-600 dark:text-slate-400">
                  <div>North: $64.2k (43%)</div>
                  <div>East: $38.2k (26%)</div>
                  <div>Central: $27.1k (18%)</div>
                  <div>South: $18.7k (13%)</div>
                </div>
              </div>

              <div className="text-[11px] text-slate-500 font-mono">
                {t.ex3Lineage}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
