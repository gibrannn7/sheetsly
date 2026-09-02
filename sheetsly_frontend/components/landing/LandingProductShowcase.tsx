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
    <div className="w-full bg-[#0d0f14] border border-zinc-800 rounded-xl overflow-hidden shadow-md">
      {/* Workbench Header Chrome */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between px-4 py-2.5 bg-[#090a0e] border-b border-zinc-800/80 gap-2.5">
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
            <span className="w-2.5 h-2.5 rounded-full bg-zinc-700" />
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono text-zinc-300">
            <span className="font-semibold text-zinc-100">q3_regional_revenue.xlsx</span>
            <span className="text-zinc-600">/</span>
            <span className="text-zinc-400 text-[11px]">Sheet1</span>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center p-0.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs font-medium self-start sm:self-auto overflow-x-auto max-w-full">
          <button
            type="button"
            onClick={() => setActiveTab('agent')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'agent'
                ? 'bg-zinc-800 text-white shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {dictionary.landing.showcase.tabAgent}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('analytics')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'analytics'
                ? 'bg-zinc-800 text-white shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {dictionary.landing.showcase.tabAnalytics}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('visual')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'visual'
                ? 'bg-zinc-800 text-white shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {dictionary.landing.showcase.tabVisual}
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('quality')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
              activeTab === 'quality'
                ? 'bg-zinc-800 text-white shadow-xs'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {dictionary.landing.showcase.tabQuality}
          </button>
        </div>
      </div>

      {/* Mode Sub-Bar */}
      <div className="px-4 py-2 bg-[#0b0d12] border-b border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400">
        <div className="flex items-center space-x-2 truncate">
          <span className="font-semibold text-zinc-200">
            {activeTab === 'agent' && dictionary.landing.showcase.agentHeading}
            {activeTab === 'analytics' && dictionary.landing.showcase.analyticsHeading}
            {activeTab === 'visual' && dictionary.landing.showcase.visualHeading}
            {activeTab === 'quality' && dictionary.landing.showcase.qualityHeading}
          </span>
          <span className="hidden md:inline text-zinc-600">—</span>
          <span className="hidden md:inline text-zinc-400 text-[11px] truncate">
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
                  ? 'bg-zinc-800 border-zinc-700 text-zinc-200 hover:bg-zinc-700'
                  : 'opacity-30 cursor-not-allowed border-transparent text-zinc-600'
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
                  ? 'bg-zinc-800 border-zinc-700 text-zinc-200 hover:bg-zinc-700'
                  : 'opacity-30 cursor-not-allowed border-transparent text-zinc-600'
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
        <div className="lg:col-span-7 xl:col-span-8 p-4 bg-[#0d0f14] flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-zinc-800 overflow-x-auto">
          <div>
            {/* Formula Bar */}
            <div className="flex items-center space-x-2 pb-2.5 mb-2.5 border-b border-zinc-800 text-xs font-mono">
              <div className="px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-zinc-100 font-semibold min-w-[48px] text-center shrink-0">
                {selectedCell}
              </div>
              <div className="text-zinc-500 select-none text-[11px]">fx</div>
              <div className="flex-1 px-2 py-0.5 rounded bg-[#090a0e] border border-zinc-800 text-zinc-300 truncate">
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
            <table className="w-full text-xs font-mono border-collapse border border-zinc-800">
              <thead>
                <tr className="bg-zinc-900/90 text-zinc-400">
                  <th className="w-8 p-1.5 border border-zinc-800 text-center font-normal">#</th>
                  <th className="p-1.5 border border-zinc-800 text-left font-semibold">A (Row ID)</th>
                  <th className="p-1.5 border border-zinc-800 text-left font-semibold">B (Region)</th>
                  <th className="p-1.5 border border-zinc-800 text-left font-semibold">C (Category)</th>
                  <th className="p-1.5 border border-zinc-800 text-right font-semibold">D (Sales Q3)</th>
                  <th className="p-1.5 border border-zinc-800 text-right font-semibold">E (Growth)</th>
                </tr>
              </thead>
              <tbody>
                {STATIC_ROWS.map((row) => {
                  const isTopSeller = row.region === 'North' && activeTab === 'analytics';
                  const inSumRange = activeTab === 'agent' && agentApplied;
                  return (
                    <tr
                      key={row.rowNum}
                      className={`hover:bg-zinc-800/40 transition-colors ${
                        isTopSeller ? 'bg-zinc-800/60' : ''
                      }`}
                    >
                      <td className="p-1.5 border border-zinc-800 text-center bg-[#090a0e] text-zinc-500 select-none">
                        {row.rowNum}
                      </td>
                      <td
                        onClick={() => setSelectedCell(`A${row.rowNum}`)}
                        className="p-1.5 border border-zinc-800 text-zinc-500 cursor-pointer"
                      >
                        RG-{row.rowNum - 1}00
                      </td>
                      <td
                        onClick={() => setSelectedCell(`B${row.rowNum}`)}
                        className={`p-1.5 border border-zinc-800 cursor-pointer ${
                          isTopSeller ? 'font-bold text-white' : 'text-zinc-200'
                        }`}
                      >
                        {row.region}
                      </td>
                      <td
                        onClick={() => setSelectedCell(`C${row.rowNum}`)}
                        className="p-1.5 border border-zinc-800 text-zinc-400 cursor-pointer"
                      >
                        {row.category}
                      </td>
                      <td
                        onClick={() => setSelectedCell(`D${row.rowNum}`)}
                        className={`p-1.5 border border-zinc-800 text-right cursor-pointer font-numeric ${
                          inSumRange ? 'bg-emerald-950/40 text-emerald-300 font-medium' : 'text-zinc-100'
                        }`}
                      >
                        {formatUSD(row.q3)}
                      </td>
                      <td
                        onClick={() => setSelectedCell(`E${row.rowNum}`)}
                        className="p-1.5 border border-zinc-800 text-right text-zinc-300 font-numeric cursor-pointer"
                      >
                        {row.growth}
                      </td>
                    </tr>
                  );
                })}

                {/* Buffer row */}
                <tr>
                  <td className="p-1.5 border border-zinc-800 text-center bg-[#090a0e] text-zinc-500 select-none">
                    8
                  </td>
                  <td className="p-1.5 border border-zinc-800"></td>
                  <td className="p-1.5 border border-zinc-800"></td>
                  <td className="p-1.5 border border-zinc-800"></td>
                  <td className="p-1.5 border border-zinc-800"></td>
                  <td className="p-1.5 border border-zinc-800"></td>
                </tr>

                {/* Row 10: Summary Row */}
                <tr className={agentApplied ? 'bg-zinc-900/60 font-bold' : ''}>
                  <td className="p-1.5 border border-zinc-800 text-center bg-[#090a0e] text-zinc-500 select-none">
                    10
                  </td>
                  <td className="p-1.5 border border-zinc-800"></td>
                  <td className="p-1.5 border border-zinc-800"></td>
                  <td
                    onClick={() => setSelectedCell('C10')}
                    className={`p-1.5 border border-zinc-800 cursor-pointer ${
                      selectedCell === 'C10' ? 'ring-1 ring-zinc-500' : ''
                    }`}
                  >
                    {agentApplied ? (
                      <span className="text-zinc-100 font-bold">TOTAL</span>
                    ) : (
                      <span className="text-zinc-600 italic">—</span>
                    )}
                  </td>
                  <td
                    onClick={() => setSelectedCell('D10')}
                    className={`p-1.5 border border-zinc-800 text-right cursor-pointer font-numeric ${
                      selectedCell === 'D10' ? 'ring-1 ring-zinc-500' : ''
                    }`}
                  >
                    {agentApplied ? (
                      <div className="flex items-center justify-end space-x-1">
                        <span className="text-[10px] text-zinc-500 font-normal">fx</span>
                        <span className="text-emerald-400 font-bold">
                          {formatUSD(q3Total)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-zinc-600 italic">—</span>
                    )}
                  </td>
                  <td className="p-1.5 border border-zinc-800"></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="pt-2.5 mt-2.5 flex items-center justify-between text-[11px] text-zinc-500 font-mono border-t border-zinc-800">
            <span>Range: Sheet1!A1:E7</span>
            <span>Deterministic Matrix Execution</span>
          </div>
        </div>

        {/* Side Panel */}
        <div className="lg:col-span-5 xl:col-span-4 p-4 bg-[#090a0e] flex flex-col justify-between space-y-4">
          {activeTab === 'agent' && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                Workbook Instruction
              </div>

              <div className="p-3 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1 font-mono text-xs text-zinc-300">
                <div className="text-[10px] text-zinc-500 font-sans uppercase font-bold">User Input</div>
                <p>&ldquo;calculate total sales in D10 and label it TOTAL in C10&rdquo;</p>
              </div>

              <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800 space-y-2 text-xs">
                <div className="flex items-center justify-between font-bold text-zinc-200 text-[11px]">
                  <span>2 Mutations Executed</span>
                  <span className="font-mono text-[10px] text-zinc-500">Tx #1042</span>
                </div>
                <div className="space-y-1 font-mono text-[11px] text-zinc-300">
                  <div className="flex items-center justify-between">
                    <span>Cell C10</span>
                    <span className="font-semibold text-zinc-100">&rarr; &quot;TOTAL&quot;</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Cell D10</span>
                    <span className="font-semibold text-emerald-400">&rarr; =SUM(D2:D7)</span>
                  </div>
                </div>
                <div className="pt-1.5 border-t border-zinc-800 flex items-center justify-between text-[10px] text-zinc-400">
                  <span>Collision check</span>
                  <span className="font-semibold text-emerald-400">Target cells empty</span>
                </div>
              </div>

              <p className="text-[11px] text-zinc-400 leading-relaxed">
                The agent inserts genuine Excel formulas (<code>=SUM(D2:D7)</code>) rather than static values, preserving workbook recalculation.
              </p>
            </div>
          )}

          {activeTab === 'analytics' && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                Analytical Query
              </div>

              <div className="p-3 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1 font-mono text-xs text-zinc-300">
                <div className="text-[10px] text-zinc-500 font-sans uppercase font-bold">User Input</div>
                <p>&ldquo;region mana dengan sales tertinggi?&rdquo;</p>
              </div>

              <div className="p-3 rounded-lg bg-zinc-900/90 border border-zinc-800 space-y-2 text-xs">
                <div className="text-[11px] font-bold text-zinc-200">
                  Deterministic Result
                </div>
                <div className="text-sm font-bold text-white font-sans">
                  North Region ($24,600)
                </div>
                <div className="space-y-1 font-mono text-[10px] text-zinc-400 pt-1 border-t border-zinc-800">
                  <div className="flex justify-between">
                    <span>Source Lineage:</span>
                    <span className="font-semibold text-zinc-200">Sheet1!B2:D7</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Execution:</span>
                    <span className="font-semibold text-emerald-400">Python 3.12 (12.4ms)</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'visual' && (
            <div className="space-y-3">
              <div className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                Visualization Generation
              </div>

              <div className="p-3 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-semibold text-zinc-200">
                  <span>Sales by Region (Q3)</span>
                  <span className="text-[10px] text-zinc-500 font-mono">Pie Chart</span>
                </div>

                <div className="h-28 flex items-center justify-center">
                  <svg viewBox="0 0 100 100" className="w-24 h-24 transform -rotate-90">
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#27272a" strokeWidth="24" strokeDasharray="60 180" strokeDashoffset="0" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#3f3f46" strokeWidth="24" strokeDasharray="50 190" strokeDashoffset="-60" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#52525b" strokeWidth="24" strokeDasharray="45 195" strokeDashoffset="-110" />
                    <circle cx="50" cy="50" r="38" fill="none" stroke="#10b981" strokeWidth="24" strokeDasharray="40 200" strokeDashoffset="-155" />
                  </svg>
                </div>

                <div className="grid grid-cols-2 gap-1 text-[10px] font-mono text-zinc-400 pt-1">
                  <div>North: 24%</div>
                  <div>East: 38%</div>
                  <div>Central: 27%</div>
                  <div>West: 20%</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'quality' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                  Data Quality
                </span>
                <span className="text-xs font-bold font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/60">
                  96 / 100
                </span>
              </div>

              <div className="p-3 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-2 text-xs">
                <div className="space-y-1.5 font-mono text-[10px] text-zinc-400">
                  <div className="flex justify-between">
                    <span>Orientation:</span>
                    <span className="font-semibold text-zinc-200">Vertical (Homogeneous)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Header Row:</span>
                    <span className="font-semibold text-zinc-200">Row 1 (Distinct)</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Broken Formulas:</span>
                    <span className="font-semibold text-emerald-400">0 detected</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Duplicate Keys:</span>
                    <span className="font-semibold text-emerald-400">0 detected</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="p-2.5 rounded bg-[#0b0d12] border border-zinc-800 text-[10px] text-zinc-500 font-mono">
            <span>Deterministic engine executes in isolated Python memory without math approximation.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
