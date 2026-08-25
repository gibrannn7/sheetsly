'use client';

import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import {
  AnalyticalInstruction,
  ChartType,
  SmartChartItem,
  TableRegion,
  VisualizationResponse,
} from '../../lib/types';

interface VisualizationViewerProps {
  datasetId: string;
  sheetName: string;
  tables: TableRegion[];
}

export const VisualizationViewer: React.FC<VisualizationViewerProps> = ({
  datasetId,
  sheetName,
  tables,
}) => {
  const { dictionary } = useTranslation();
  const [selectedTableId, setSelectedTableId] = useState<string>(tables[0]?.table_id || '');
  const activeTable = tables.find((t) => t.table_id === selectedTableId) || tables[0];

  // Active sub-tab: 'smart' (Smart Generated Visualizations) vs 'custom' (Custom Manual Builder)
  const [activeTab, setActiveTab] = useState<'smart' | 'custom'>('custom');

  // Custom Chart Builder State
  const categoricalCols = activeTable?.columns.filter(
    (c) => c.data_type === 'string' || c.semantic_type === 'categorical' || c.semantic_type === 'temporal'
  ) || [];
  const numericCols = activeTable?.columns.filter(
    (c) => ['integer', 'float', 'currency', 'percentage'].includes(c.data_type)
  ) || [];

  const [selectedDimCol, setSelectedDimCol] = useState<string>('');
  const [selectedMetricCol, setSelectedMetricCol] = useState<string>('');
  const [selectedChartType, setSelectedChartType] = useState<ChartType>('BAR');

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [customVizResponse, setCustomVizResponse] = useState<VisualizationResponse | null>(null);

  // Smart Generate State
  const [smartLoading, setSmartLoading] = useState<boolean>(false);
  const [smartStage, setSmartStage] = useState<string>('');
  const [smartCharts, setSmartCharts] = useState<SmartChartItem[]>([]);
  const [smartEmptyReason, setSmartEmptyReason] = useState<string | null>(null);
  const [smartError, setSmartError] = useState<string | null>(null);
  const [expandedWhyIdx, setExpandedWhyIdx] = useState<number | null>(null);

  const SUPPORTED_CHARTS: { type: ChartType; label: string; desc: string }[] = [
    { type: 'BAR', label: dictionary.visualization.charts.bar, desc: dictionary.visualization.charts.barDesc },
    { type: 'LINE', label: dictionary.visualization.charts.line, desc: dictionary.visualization.charts.lineDesc },
    { type: 'PIE', label: dictionary.visualization.charts.pie, desc: dictionary.visualization.charts.pieDesc },
    { type: 'AREA', label: dictionary.visualization.charts.area, desc: dictionary.visualization.charts.areaDesc },
    { type: 'SCATTER', label: dictionary.visualization.charts.scatter, desc: dictionary.visualization.charts.scatterDesc },
    { type: 'HISTOGRAM', label: dictionary.visualization.charts.histogram, desc: dictionary.visualization.charts.histogramDesc },
  ];

  // Initialize selected columns when table changes
  useEffect(() => {
    if (activeTable) {
      if (categoricalCols.length > 0 && !selectedDimCol) {
        setSelectedDimCol(categoricalCols[0].name);
      }
      if (numericCols.length > 0 && !selectedMetricCol) {
        setSelectedMetricCol(numericCols[0].name);
      }
    }
  }, [selectedTableId, activeTable]);

  // Execute Smart Generate
  const handleSmartGenerate = async () => {
    if (!activeTable) return;
    setSmartLoading(true);
    setSmartError(null);
    setSmartEmptyReason(null);
    setExpandedWhyIdx(null);

    try {
      setSmartStage(dictionary.visualization.analyzingStructure);
      await new Promise((resolve) => setTimeout(resolve, 150)); // Truthful brief UI transition

      setSmartStage(dictionary.visualization.selectingVisualizations);
      await new Promise((resolve) => setTimeout(resolve, 150));

      setSmartStage(dictionary.visualization.generatingCharts);
      const res = await api.smartGenerateCharts(datasetId, {
        sheet_name: sheetName,
        table_id: activeTable.table_id,
        max_charts: 5,
      });

      setSmartCharts(res.charts);
      if (res.charts.length === 0) {
        setSmartEmptyReason(res.empty_reason || dictionary.visualization.noSmartChartsDesc);
      }
      setActiveTab('smart');
    } catch (err: any) {
      if (err instanceof ApiError) {
        setSmartError(err.message);
      } else {
        setSmartError(err.message || 'Failed to execute smart chart generation.');
      }
    } finally {
      setSmartLoading(false);
      setSmartStage('');
    }
  };

  // Execute Custom Manual Chart Generation
  const handleGenerateCustomChart = async (chartTypeToUse = selectedChartType) => {
    if (!activeTable) return;
    setLoading(true);
    setError(null);

    try {
      let instruction: AnalyticalInstruction;

      if (chartTypeToUse === 'HISTOGRAM') {
        instruction = {
          operation: 'FILTER',
          dataset_id: datasetId,
          sheet_name: sheetName,
          table_id: activeTable.table_id,
          target_column: selectedMetricCol || numericCols[0]?.name,
        };
      } else if (chartTypeToUse === 'SCATTER') {
        instruction = {
          operation: 'FILTER',
          dataset_id: datasetId,
          sheet_name: sheetName,
          table_id: activeTable.table_id,
        };
      } else {
        const dim = selectedDimCol || categoricalCols[0]?.name || activeTable.columns[0]?.name;
        const metric = selectedMetricCol || numericCols[0]?.name || activeTable.columns[1]?.name;

        instruction = {
          operation: 'GROUP_BY',
          dataset_id: datasetId,
          sheet_name: sheetName,
          table_id: activeTable.table_id,
          group_by_columns: [dim],
          aggregations: [
            {
              column: metric,
              operation: 'SUM',
              alias: `Total_${metric}`,
            },
          ],
          sort: {
            column: `Total_${metric}`,
            ascending: false,
          },
          limit: 10,
        };
      }

      const res = await api.visualizeFromInstruction(datasetId, instruction, chartTypeToUse);
      setCustomVizResponse(res);
      setSelectedChartType(chartTypeToUse);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'Failed to render chart.');
      }
      setCustomVizResponse(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* 1. Header Toolbar with Smart Generate and Custom Builder Controls */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-4 space-y-3.5">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              {dictionary.visualization.title}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {dictionary.visualization.desc}
            </p>
          </div>

          <div className="flex items-center space-x-2.5">
            {/* Table Selector if multiple tables exist */}
            {tables.length > 1 && (
              <select
                value={selectedTableId}
                onChange={(e) => setSelectedTableId(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1.5 font-medium text-slate-800 focus:ring-1 focus:ring-slate-900"
              >
                {tables.map((t) => (
                  <option key={t.table_id} value={t.table_id}>
                    {t.name} ({t.range_address})
                  </option>
                ))}
              </select>
            )}

            {/* Smart Generate Button */}
            <button
              type="button"
              onClick={handleSmartGenerate}
              disabled={smartLoading || loading || !activeTable}
              className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-semibold shadow-2xs disabled:opacity-50 cursor-pointer transition-colors flex items-center space-x-1.5 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-900"
            >
              <svg className="w-3.5 h-3.5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>{dictionary.visualization.smartGenerateBtn}</span>
            </button>
          </div>
        </div>

        {/* Truthful Stage Loading Indicator */}
        {smartLoading && smartStage && (
          <div className="flex items-center space-x-2 px-3.5 py-2 bg-slate-50 border border-slate-200 rounded-md text-xs text-slate-700 font-medium">
            <span className="w-2 h-2 rounded-full bg-slate-800 animate-pulse" />
            <span>{smartStage}</span>
          </div>
        )}

        {/* Mode Navigation Tabs */}
        <div className="flex items-center space-x-2 pt-1 border-b border-slate-100 pb-2">
          {smartCharts.length > 0 && (
            <button
              type="button"
              onClick={() => setActiveTab('smart')}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                activeTab === 'smart'
                  ? 'bg-slate-900 text-white shadow-2xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200/70'
              }`}
            >
              {dictionary.visualization.smartChartsTab} ({smartCharts.length})
            </button>
          )}

          <button
            type="button"
            onClick={() => setActiveTab('custom')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
              activeTab === 'custom'
                ? 'bg-slate-900 text-white shadow-2xs'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200/70'
            }`}
          >
            {dictionary.visualization.customBuilderTab}
          </button>
        </div>

        {/* Custom Manual Builder Controls (when activeTab is 'custom') */}
        {activeTab === 'custom' && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
            <div>
              <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide mb-1">
                {dictionary.visualization.dimension}
              </label>
              <select
                value={selectedDimCol}
                onChange={(e) => setSelectedDimCol(e.target.value)}
                className="w-full text-xs bg-white border border-slate-300 rounded-md p-2 text-slate-800 font-medium focus:ring-1 focus:ring-slate-900"
              >
                {activeTable?.columns.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.data_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide mb-1">
                {dictionary.visualization.metric}
              </label>
              <select
                value={selectedMetricCol}
                onChange={(e) => setSelectedMetricCol(e.target.value)}
                className="w-full text-xs bg-white border border-slate-300 rounded-md p-2 text-slate-800 font-medium focus:ring-1 focus:ring-slate-900"
              >
                {numericCols.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.data_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide">
                  {dictionary.visualization.chartType}
                </label>
                <button
                  type="button"
                  onClick={() => handleGenerateCustomChart(selectedChartType)}
                  disabled={loading || !activeTable}
                  className="text-[11px] font-semibold text-slate-900 underline hover:text-slate-700 cursor-pointer disabled:opacity-50"
                >
                  {loading ? dictionary.visualization.rendering : dictionary.visualization.generateChart}
                </button>
              </div>
              <div className="grid grid-cols-3 gap-1.5">
                {SUPPORTED_CHARTS.map((c) => (
                  <button
                    key={c.type}
                    type="button"
                    onClick={() => {
                      setSelectedChartType(c.type);
                      if (customVizResponse) {
                        handleGenerateCustomChart(c.type);
                      }
                    }}
                    className={`px-2 py-1.5 text-[11px] font-semibold rounded-md border text-center transition-all cursor-pointer ${
                      selectedChartType === c.type
                        ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                        : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    {c.type}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Error Banners */}
      {(error || smartError) && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-900 flex items-start space-x-2">
          <span className="font-bold text-rose-700">{dictionary.visualization.rejection}</span>
          <span>{error || smartError}</span>
        </div>
      )}

      {/* 2. Smart Generated Visualization Set */}
      {activeTab === 'smart' && (
        <div className="space-y-6">
          {smartEmptyReason && smartCharts.length === 0 ? (
            <div className="bg-white rounded-lg border border-dashed border-slate-300 p-8 text-center space-y-2">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                {dictionary.visualization.noSmartChartsTitle}
              </h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                {smartEmptyReason}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {smartCharts.map((item, idx) => {
                const isWhyOpen = expandedWhyIdx === idx;
                return (
                  <div
                    key={item.chart_id}
                    className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden"
                  >
                    {/* Header */}
                    <div className="p-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50">
                      <div className="space-y-0.5">
                        <div className="flex items-center space-x-2">
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-900 text-white uppercase shadow-2xs">
                            {item.chart_type}
                          </span>
                          <h4 className="text-xs font-bold text-slate-900">{item.title}</h4>
                        </div>
                        <p className="text-[11px] text-slate-500">{item.analytical_intent}</p>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() => setExpandedWhyIdx(isWhyOpen ? null : idx)}
                          className="px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:text-slate-900 bg-white border border-slate-300 rounded shadow-2xs cursor-pointer hover:bg-slate-50 transition-colors"
                        >
                          {dictionary.visualization.whyThisChart}
                        </button>

                        <a
                          href={api.resolveImageUrl(item.visualization.image_url)}
                          download={`${item.chart_id}.png`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold rounded shadow-2xs transition-colors"
                        >
                          {dictionary.visualization.downloadPng}
                        </a>
                      </div>
                    </div>

                    {/* "Why this chart?" Explainer Card */}
                    {isWhyOpen && (
                      <div className="px-4 py-3 bg-slate-100/90 border-b border-slate-200 text-xs space-y-1 animate-in fade-in duration-100">
                        <div className="flex items-center gap-1.5 font-bold text-slate-900 text-[11px] uppercase tracking-wider">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-800" />
                          <span>{dictionary.visualization.whyThisChart}</span>
                        </div>
                        <p className="text-slate-700 text-[11px] leading-relaxed pl-3">{item.why_this_chart}</p>
                      </div>
                    )}

                    {/* Chart Image */}
                    <div className="p-6 flex justify-center items-center bg-white min-h-[340px]">
                      <img
                        src={`${api.resolveImageUrl(item.visualization.image_url)}?t=${Date.now()}`}
                        alt={item.title}
                        className="max-h-[440px] w-auto object-contain rounded border border-slate-200 shadow-2xs"
                      />
                    </div>

                    {/* Lineage & Provenance Footer */}
                    <div className="p-3.5 bg-slate-50 border-t border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">
                          {dictionary.visualization.sheetAndTable}
                        </span>
                        <span className="font-medium text-slate-800 font-mono text-[11px]">
                          {item.visualization.chart_metadata.sheet_name} / {item.visualization.chart_metadata.table_id}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">
                          {dictionary.visualization.sourceRange}
                        </span>
                        <span className="font-mono font-medium text-slate-800 text-[11px]">
                          {item.visualization.chart_metadata.source_range}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">
                          {dictionary.visualization.rowsInScope}
                        </span>
                        <span className="font-medium text-slate-800 font-mono text-[11px]">
                          {item.visualization.chart_metadata.rows_included} {dictionary.common.records}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-bold">
                          {dictionary.visualization.generatedAt}
                        </span>
                        <span className="font-medium text-slate-800 font-mono text-[11px]">
                          {new Date(item.visualization.chart_metadata.generated_at).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 3. Custom Manual Chart Presentation (when activeTab is 'custom') */}
      {activeTab === 'custom' && (
        <div>
          {customVizResponse ? (
            <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
              <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
                <div>
                  <h4 className="text-xs font-bold text-slate-900">{customVizResponse.chart_metadata.title}</h4>
                  <p className="text-[11px] text-slate-500">
                    Type: <span className="font-semibold text-slate-700">{customVizResponse.chart_metadata.chart_type}</span> | Source:{' '}
                    <span className="font-mono text-slate-700">{customVizResponse.chart_metadata.source_range}</span>
                  </p>
                </div>

                <a
                  href={api.resolveImageUrl(customVizResponse.image_url)}
                  download={`${customVizResponse.chart_metadata.chart_id}.png`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold rounded shadow-2xs transition-colors"
                >
                  {dictionary.visualization.downloadPng}
                </a>
              </div>

              <div className="p-6 flex justify-center items-center bg-white min-h-[360px]">
                <img
                  src={`${api.resolveImageUrl(customVizResponse.image_url)}?t=${Date.now()}`}
                  alt={customVizResponse.chart_metadata.title}
                  className="max-h-[460px] w-auto object-contain rounded border border-slate-200 shadow-2xs"
                />
              </div>

              {/* Lineage & Provenance Footer */}
              <div className="p-3.5 bg-slate-50 border-t border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    {dictionary.visualization.sheetAndTable}
                  </span>
                  <span className="font-medium text-slate-800 font-mono text-[11px]">
                    {customVizResponse.chart_metadata.sheet_name} / {customVizResponse.chart_metadata.table_id}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    {dictionary.visualization.sourceRange}
                  </span>
                  <span className="font-mono font-medium text-slate-800 text-[11px]">
                    {customVizResponse.chart_metadata.source_range}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    {dictionary.visualization.rowsInScope}
                  </span>
                  <span className="font-medium text-slate-800 font-mono text-[11px]">
                    {customVizResponse.chart_metadata.rows_included} {dictionary.common.records}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase font-bold">
                    {dictionary.visualization.generatedAt}
                  </span>
                  <span className="font-medium text-slate-800 font-mono text-[11px]">
                    {new Date(customVizResponse.chart_metadata.generated_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            !loading &&
            !error && (
              <div className="bg-white rounded-lg border border-dashed border-slate-300 p-10 text-center space-y-2">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                  {dictionary.visualization.noChartYet}
                </h4>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  {dictionary.visualization.noChartDesc}
                </p>
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => handleGenerateCustomChart('BAR')}
                    className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-semibold shadow-2xs cursor-pointer transition-colors"
                  >
                    {dictionary.visualization.quickBar}
                  </button>
                </div>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
};
