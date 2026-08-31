'use client';

import React, { useState } from 'react';
import { useTranslation } from '../../lib/i18n';

type ShowcaseTab = 'agent' | 'analytics' | 'visual' | 'quality';

interface RowData {
  rowNum: number;
  region: string;
  category: string;
  q1: number;
  q2: number;
  q3: number;
  growth: string;
}

const STATIC_ROWS: RowData[] = [
  { rowNum: 2, region: 'North', category: 'Software', q1: 18400, q2: 21200, q3: 24600, growth: '+16.0%' },
  { rowNum: 3, region: 'South', category: 'Hardware', q1: 12100, q2: 13900, q3: 15400, growth: '+10.8%' },
  { rowNum: 4, region: 'East', category: 'Cloud', q1: 29500, q2: 34100, q3: 38200, growth: '+12.0%' },
  { rowNum: 5, region: 'West', category: 'Services', q1: 15300, q2: 17800, q3: 19800, growth: '+11.2%' },
  { rowNum: 6, region: 'Central', category: 'Security', q1: 22800, q2: 24900, q3: 27150, growth: '+9.0%' },
  { rowNum: 7, region: 'EMEA Direct', category: 'Software', q1: 19100, q2: 21500, q3: 23100, growth: '+7.4%' },
];

export const LandingProductShowcase: React.FC = () => {
  const { dictionary } = useTranslation();
  const [activeTab, setActiveTab] = useState<ShowcaseTab>('agent');
  const [agentApplied, setAgentApplied] = useState<boolean>(true);
  const [selectedCell, setSelectedCell] = useState<string>('D10');

  const formatUSD = (val: number) => `$${val.toLocaleString()}`;
  const q3Total = STATIC_ROWS.reduce((acc, r) => acc + r.q3, 0);

  return (
    <div className="w-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden shadow-xs transition-colors">
      {/* Workbench Header Chrome */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between px-4 py-2.5 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 gap-2.5">
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-700" />
            <span className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-700" />
            <span className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-700" />
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono text-slate-700 dark:text-slate-300">
            <span className="font-semibold text-slate-900 dark:text-slate-100">q3_regional_revenue.xlsx</span>
            <span className="text-slate-400 dark:text-slate-600">/</span>
            <span className="text-slate-500 dark:text-slate-400 text-[11px]">Sheet1</span>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center p-0.5 rounded-lg bg-slate-200/80 dark:bg-slate-800 border border-slate-300/80 dark:border-slate-700 text-xs font-medium self-start sm:self-auto overflow-x-auto max-w-full">
          <button
            type="button"
            onClick={() => setActiveTab('agent')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'agent'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {dictionary.landing.showcase.tabAgent}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('analytics')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'analytics'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {dictionary.landing.showcase.tabAnalytics}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('visual')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'visual'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {dictionary.landing.showcase.tabVisual}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('quality')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'quality'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
            }`}
          >
            {dictionary.landing.showcase.tabQuality}
          </button>
        </div>
      </div>

      {/* Mode Sub-Bar */}
      <div className="px-4 py-2 bg-slate-50/60 dark:bg-slate-950/60 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-600 dark:text-slate-400">
        <div className="flex items-center space-x-2 truncate">
          <span className="font-semibold text-slate-900 dark:text-slate-100">
            {activeTab === 'agent' && dictionary.landing.showcase.agentHeading}
            {activeTab === 'analytics' && dictionary.landing.showcase.analyticsHeading}
            {activeTab === 'visual' && dictionary.landing.showcase.visualHeading}
            {activeTab === 'quality' && dictionary.landing.showcase.qualityHeading}
          </span>
          <span className="hidden md:inline text-slate-400 dark:text-slate-600">—</span>
          <span className="hidden md:inline text-slate-500 dark:text-slate-400 text-[11px] truncate">
            {activeTab === 'agent' && dictionary.landing.showcase.agentSubheading}
            {activeTab === 'analytics' && dictionary.landing.showcase.analyticsSubheading}
            {activeTab === 'visual' && dictionary.landing.showcase.visualSubheading}
            {activeTab === 'quality' && dictionary.landing.showcase.qualitySubheading}
          </span>
        </div>

        {activeTab === 'agent' && (
          <div className="flex items-center space-x-1.5 shrink-0">
            <button
              type="button"
              onClick={() => setAgentApplied(false)}
              disabled={!agentApplied}
              className={`px-2 py-0.5 text-[11px] font-mono rounded border transition-colors cursor-pointer ${
                agentApplied
                  ? 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                  : 'opacity-40 cursor-not-allowed border-transparent text-slate-400'
              }`}
            >
              Undo
            </button>
            <button
              type="button"
              onClick={() => setAgentApplied(true)}
              disabled={agentApplied}
              className={`px-2 py-0.5 text-[11px] font-mono rounded border transition-colors cursor-pointer ${
                !agentApplied
                  ? 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                  : 'opacity-40 cursor-not-allowed border-transparent text-slate-400'
              }`}
            >
              Redo
            </button>
          </div>
        )}
      </div>

      {/* Grid + Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[380px]">
        {/* Matrix Area */}
        <div className="lg:col-span-7 xl:col-span-8 p-4 bg-white dark:bg-slate-900 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-slate-200 dark:border-slate-800 overflow-x-auto">
          <div>
            {/* Formula Bar */}
            <div className="flex items-center space-x-2 pb-2.5 mb-2.5 border-b border-slate-200 dark:border-slate-800 text-xs font-mono">
              <div className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-900 dark:text-slate-100 font-semibold min-w-[48px] text-center shrink-0">
                {selectedCell}
              </div>
              <div className="text-slate-400 select-none text-[11px]">fx</div>
              <div className="flex-1 px-2 py-0.5 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 truncate">
                {selectedCell === 'D10' && agentApplied
                  ? '=SUM(D2:D7)'
                  : selectedCell === 'C10' && agentApplied
                  ? 'TOTAL'
                  : selectedCell === 'D2'
                  ? '24600'
                  : selectedCell === 'B2'
                  ? 'North'
                  : selectedCell === 'C2'
                  ? 'Software'
                  : '—'}
              </div>
            </div>

            {/* Matrix Table */}
            <table className="w-full text-xs font-mono border-collapse border border-slate-200 dark:border-slate-800">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400">
                  <th className="w-8 p-1.5 border border-slate-200 dark:border-slate-800 text-center font-normal">#</th>
                  <th className="p-1.5 border border-slate-200 dark:border-slate-800 text-left font-semibold">A (Row ID)</th>
                  <th className="p-1.5 border border-slate-200 dark:border-slate-800 text-left font-semibold">B (Region)</th>
                  <th className="p-1.5 border border-slate-200 dark:border-slate-800 text-left font-semibold">C (Category)</th>
                  <th className="p-1.5 border border-slate-200 dark:border-slate-800 text-right font-semibold">D (Sales Q3)</th>
                  <th className="p-1.5 border border-slate-200 dark:border-slate-800 text-right font-semibold">E (Growth)</th>
                </tr>
              </thead>
              <tbody>
                {STATIC_ROWS.map((row) => {
                  const isTopSeller = row.region === 'North' && activeTab === 'analytics';
                  const inSumRange = activeTab === 'agent' && agentApplied;
                  return (
                    <tr
                      key={row.rowNum}
                      className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors ${
                        isTopSeller ? 'bg-slate-100 dark:bg-slate-800/60' : ''
                      }`}
                    >
                      <td className="p-1.5 border border-slate-200 dark:border-slate-800 text-center bg-slate-50 dark:bg-slate-950 text-slate-400 select-none">
                        {row.rowNum}
                      </td>
                      <td
                        onClick={() => setSelectedCell(`A${row.rowNum}`)}
                        className="p-1.5 border border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 cursor-pointer"
                      >
                        RG-{row.rowNum - 1}00
                      </td>
                      <td
                        onClick={() => setSelectedCell(`B${row.rowNum}`)}
                        className={`p-1.5 border border-slate-200 dark:border-slate-800 cursor-pointer ${
                          isTopSeller ? 'font-bold text-slate-900 dark:text-slate-100' : 'text-slate-800 dark:text-slate-200'
                        }`}
                      >
                        {row.region}
                      </td>
                      <td
                        onClick={() => setSelectedCell(`C${row.rowNum}`)}
                        className="p-1.5 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 cursor-pointer"
                      >
                        {row.category}
                      </td>
                      <td
                        onClick={() => setSelectedCell(`D${row.rowNum}`)}
                        className={`p-1.5 border border-slate-200 dark:border-slate-800 text-right cursor-pointer font-numeric ${
                          inSumRange ? 'bg-slate-100/70 dark:bg-slate-800/50 text-slate-900 dark:text-slate-100 font-medium' : 'text-slate-900 dark:text-slate-100'
                        }`}
                      >
                        {formatUSD(row.q3)}
                      </td>
                      <td
                        onClick={() => setSelectedCell(`E${row.rowNum}`)}
                        className="p-1.5 border border-slate-200 dark:border-slate-800 text-right text-slate-700 dark:text-slate-300 font-numeric cursor-pointer"
                      >
                        {row.growth}
                      </td>
                    </tr>
                  );
                })}

                {/* Buffer rows */}
                <tr>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800 text-center bg-slate-50 dark:bg-slate-950 text-slate-400 select-none">
                    8
                  </td>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800"></td>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800"></td>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800"></td>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800"></td>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800"></td>
                </tr>

                {/* Row 10: Summary Row */}
                <tr className={agentApplied ? 'bg-slate-50 dark:bg-slate-950 font-bold' : ''}>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800 text-center bg-slate-50 dark:bg-slate-950 text-slate-400 select-none">
                    10
                  </td>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800"></td>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800"></td>
                  <td
                    onClick={() => setSelectedCell('C10')}
                    className={`p-1.5 border border-slate-200 dark:border-slate-800 cursor-pointer ${
                      selectedCell === 'C10' ? 'ring-1 ring-slate-500' : ''
                    }`}
                  >
                    {agentApplied ? (
                      <span className="text-slate-900 dark:text-slate-100 font-bold">TOTAL</span>
                    ) : (
                      <span className="text-slate-300 dark:text-slate-700 italic">—</span>
                    )}
                  </td>
                  <td
                    onClick={() => setSelectedCell('D10')}
                    className={`p-1.5 border border-slate-200 dark:border-slate-800 text-right cursor-pointer font-numeric ${
                      selectedCell === 'D10' ? 'ring-1 ring-slate-500' : ''
                    }`}
                  >
                    {agentApplied ? (
                      <div className="flex items-center justify-end space-x-1">
                        <span className="text-[10px] text-slate-400 font-normal">fx</span>
                        <span className="text-slate-900 dark:text-slate-100 font-bold">
                          {formatUSD(q3Total)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-slate-300 dark:text-slate-700 italic">—</span>
                    )}
                  </td>
                  <td className="p-1.5 border border-slate-200 dark:border-slate-800"></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="pt-2.5 mt-2.5 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-mono border-t border-slate-200 dark:border-slate-800">
            <span>Range: Sheet1!A1:E7</span>
            <span>Deterministic Matrix Execution</span>
          </div>
        </div>

        {/* Side Panel */}
        <div className="lg:col-span-5 xl:col-span-4 p-4 bg-slate-50 dark:bg-slate-950 flex flex-col justify-between space-y-4">
          {activeTab === 'agent' && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Workbook Instruction
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 font-mono text-xs text-slate-800 dark:text-slate-200">
                <div className="text-[10px] text-slate-400 font-sans uppercase font-bold">User Input</div>
                <p>&ldquo;calculate total sales in D10 and label it TOTAL in C10&rdquo;</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-100/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
                <div className="flex items-center justify-between font-bold text-slate-900 dark:text-slate-100 text-[11px]">
                  <span>2 Mutations Executed</span>
                  <span className="font-mono text-[10px] text-slate-500">Tx #1042</span>
                </div>
                <div className="space-y-1 font-mono text-[11px] text-slate-700 dark:text-slate-300">
                  <div className="flex items-center justify-between">
                    <span>Cell C10</span>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">&rarr; &quot;TOTAL&quot;</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Cell D10</span>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">&rarr; =SUM(D2:D7)</span>
                  </div>
                </div>
                <div className="pt-1.5 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-600 dark:text-slate-400">
                  <span>Collision check</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">Target cells empty</span>
                </div>
              </div>

              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                The agent inserts genuine Excel formulas (<code>=SUM(D2:D7)</code>) rather than static values, preserving workbook recalculation.
              </p>
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Analytical Query
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1 font-mono text-xs text-slate-800 dark:text-slate-200">
                <div className="text-[10px] text-slate-400 font-sans uppercase font-bold">User Input</div>
                <p>&ldquo;region mana dengan sales tertinggi?&rdquo;</p>
              </div>

              <div className="p-3 rounded-lg bg-slate-100/80 dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
                <div className="text-[11px] font-bold text-slate-900 dark:text-slate-100">
                  Deterministic Result
                </div>
                <div className="text-sm font-bold text-slate-900 dark:text-slate-100 font-sans">
                  North Region ($24,600)
                </div>
                <div className="space-y-1 font-mono text-[10px] text-slate-600 dark:text-slate-400 pt-1 border-t border-slate-200 dark:border-slate-800">
                  <div className="flex justify-between">
                    <span>Source Lineage:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Sheet1!B2:D7</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Execution:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Python 3.12 (12.4ms)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'visual' && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                Visualization Generation
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-800 dark:text-slate-200">
                  <span>Sales by Region (Q3)</span>
                  <span className="text-[10px] text-slate-400 font-mono">Pie Chart</span>
                </div>

                <div className="h-28 flex items-center justify-center">
                  <svg viewBox="0 0 100 100" className="w-24 h-24 transform -rotate-90">
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#475569" strokeWidth="24" strokeDasharray="60 180" strokeDashoffset="0" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#64748b" strokeWidth="24" strokeDasharray="50 190" strokeDashoffset="-60" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#94a3b8" strokeWidth="24" strokeDasharray="45 195" strokeDashoffset="-110" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#cbd5e1" strokeWidth="24" strokeDasharray="40 200" strokeDashoffset="-155" />
                  </svg>
                </div>

                <div className="grid grid-cols-2 gap-1 text-[10px] font-mono text-slate-600 dark:text-slate-400 pt-1">
                  <div>North (24%)</div>
                  <div>East (38%)</div>
                  <div>Central (27%)</div>
                  <div>West (20%)</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'quality' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
                  Data Quality
                </span>
                <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200">
                  96 / 100
                </span>
              </div>

              <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
                <div className="space-y-1.5 font-mono text-[10px] text-slate-600 dark:text-slate-400">
                  <div className="flex justify-between">
                    <span>Orientation:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Vertical (Homogeneous)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Header Row:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">Row 1 (Distinct)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Broken Formulas:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">0 detected</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Duplicate Keys:</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">0 detected</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="p-2.5 rounded bg-slate-100 dark:bg-slate-900 text-[10px] text-slate-500 dark:text-slate-400 font-mono">
            <span>Deterministic engine executes in isolated Python memory without math approximation.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
