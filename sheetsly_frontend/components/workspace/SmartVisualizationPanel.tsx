'use client';

import React, { useState } from 'react';
import { ChartDataDTO, ExplainableAnalyticsResultDTO } from '../../lib/types';
import { useTranslation } from '../../lib/i18n';

interface SmartVisualizationPanelProps {
  analyticsResult?: ExplainableAnalyticsResultDTO | null;
  onQuerySubmit?: (query: string) => void;
  isLoading?: boolean;
}

export const SmartVisualizationPanel: React.FC<SmartVisualizationPanelProps> = ({
  analyticsResult,
  onQuerySubmit,
  isLoading = false,
}) => {
  const { dictionary } = useTranslation();
  const [customQuery, setCustomQuery] = useState('');

  const chart = analyticsResult?.chart_data;

  const quickPrompts = [
    'tampilkan tren penjualan bulanan',
    'bandingkan penjualan per region',
    'top 5 produk berdasarkan profit',
    'korelasi sales dan profit',
  ];

  return (
    <div className="space-y-4">
      {/* Header & Query Bar */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-2xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800 dark:text-slate-200">
              Smart Analytics & Visualization
            </h3>
          </div>
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
            EVIDENCE-BASED ENGINE
          </span>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (customQuery.trim() && onQuerySubmit) {
              onQuerySubmit(customQuery.trim());
            }
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={customQuery}
            onChange={(e) => setCustomQuery(e.target.value)}
            placeholder="Tanyakan analisis... (misal: tampilkan tren penjualan bulanan)"
            className="flex-1 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-500"
          />
          <button
            type="submit"
            disabled={isLoading || !customQuery.trim()}
            className="px-4 py-1.5 text-xs font-semibold bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-md hover:bg-slate-800 dark:hover:bg-white disabled:opacity-50 transition-colors cursor-pointer"
          >
            {isLoading ? 'Menganalisis...' : 'Visualisasikan'}
          </button>
        </form>

        <div className="flex flex-wrap gap-1.5 pt-1">
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setCustomQuery(p);
                if (onQuerySubmit) onQuerySubmit(p);
              }}
              className="px-2.5 py-0.5 text-[11px] bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded border border-slate-200 dark:border-slate-700 transition-colors cursor-pointer"
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Main Visualization Display */}
      {chart && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Chart Canvas Card */}
          <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-2xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
              <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 font-mono">
                {chart.title}
              </h4>
              <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700">
                {chart.chart_type}
              </span>
            </div>

            {/* Render KPI Card */}
            {chart.chart_type === 'KPI' ? (
              <div className="p-8 text-center bg-slate-50 dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 space-y-2">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {chart.summary_metric || 'Total Metric'}
                </span>
                <div className="text-3xl font-extrabold font-mono text-emerald-600 dark:text-emerald-400">
                  {typeof chart.summary_value === 'number'
                    ? chart.summary_value.toLocaleString()
                    : chart.summary_value}
                </div>
              </div>
            ) : (
              /* Bar / Line / Table Visualization Preview */
              <div className="space-y-2">
                <div className="max-h-72 overflow-y-auto space-y-1.5 p-2 bg-slate-50 dark:bg-slate-950 rounded-md border border-slate-200 dark:border-slate-800 text-xs">
                  {chart.labels.map((lbl, idx) => {
                    const val = chart.datasets[0]?.values[idx];
                    const maxVal = Math.max(...chart.datasets[0]?.values.map((v: any) => (typeof v === 'number' ? v : 0)), 1);
                    const pct = typeof val === 'number' ? Math.min(100, Math.max(5, (val / maxVal) * 100)) : 50;

                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between font-mono text-[11px]">
                          <span className="font-semibold text-slate-800 dark:text-slate-200">{lbl}</span>
                          <span className="text-emerald-700 dark:text-emerald-400 font-bold">
                            {typeof val === 'number' ? val.toLocaleString() : val}
                          </span>
                        </div>
                        <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                          <div
                            className="bg-emerald-500 h-full rounded-full transition-all duration-500"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Factual Provenance & Lineage Card */}
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-2xs space-y-3 text-xs">
            <div className="border-b border-slate-200 dark:border-slate-800 pb-2 flex items-center justify-between">
              <h5 className="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider text-[11px]">
                Data Provenance
              </h5>
            </div>

            <div className="space-y-2 text-[11px]">
              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Source Sheets</span>
                <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                  {chart.provenance.source_sheets.join(', ')}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Source Columns</span>
                <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                  {chart.provenance.source_columns.join(', ')}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Ranges Sampled</span>
                <span className="font-mono font-semibold text-emerald-700 dark:text-emerald-400">
                  {chart.provenance.source_ranges.join(', ')}
                </span>
              </div>

              <div>
                <span className="text-slate-500 block text-[10px] uppercase font-bold">Aggregation Method</span>
                <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                  {chart.provenance.aggregation}
                </span>
              </div>

              <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
                <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 px-2 py-1 rounded w-full justify-center">
                  ✓ {chart.provenance.verification_status}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
