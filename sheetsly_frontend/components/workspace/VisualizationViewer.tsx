'use client';

import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import {
  AnalyticalInstruction,
  ChartType,
  ExplainableAnalyticsResultDTO,
  TableRegion,
} from '../../lib/types';
import { useWorkspace } from '../../lib/workspace/WorkspaceContext';
import { SmartGenerateExplanationModal } from './SmartGenerateExplanationModal';
import { SmartVisualizationPanel } from './SmartVisualizationPanel';

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
  const { visualizationState, updateVisualizationState } = useWorkspace();

  const selectedTableId = visualizationState.selectedTableId || tables[0]?.table_id || '';
  const activeTable = tables.find((t) => t.table_id === selectedTableId) || tables[0];

  // Active sub-tab: 'smart' vs 'custom'
  const activeTab = visualizationState.activeTab;

  // Modal explanation state
  const [isHowSmartWorksOpen, setIsHowSmartWorksOpen] = useState<boolean>(false);

  // Custom Chart Builder State
  const categoricalCols = activeTable?.columns.filter(
    (c) => c.data_type === 'string' || c.semantic_type === 'categorical' || c.semantic_type === 'temporal'
  ) || [];
  const numericCols = activeTable?.columns.filter(
    (c) => ['integer', 'float', 'currency', 'percentage'].includes(c.data_type)
  ) || [];

  const selectedDimCol = visualizationState.selectedDimCol || categoricalCols[0]?.name || activeTable?.columns[0]?.name || '';
  const selectedMetricCol = visualizationState.selectedMetricCol || numericCols[0]?.name || activeTable?.columns[1]?.name || '';
  const selectedChartType = visualizationState.selectedChartType;
  const customVizResponse = visualizationState.customVizResponse;

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Smart Generate State
  const [smartLoading, setSmartLoading] = useState<boolean>(false);
  const [smartStage, setSmartStage] = useState<string>('');
  const smartCharts = visualizationState.smartCharts;
  const smartEmptyReason = visualizationState.smartEmptyReason;
  const [smartError, setSmartError] = useState<string | null>(null);

  // Phase 9: Smart Granular Analytics State
  const [granularResult, setGranularResult] = useState<ExplainableAnalyticsResultDTO | null>(null);
  const [granularLoading, setGranularLoading] = useState<boolean>(false);

  const handleGranularQuery = async (query: string) => {
    setGranularLoading(true);
    try {
      const res = await api.executeGranularAnalytics(datasetId, query, sheetName);
      setGranularResult(res);
    } catch (err) {
      console.error('Failed to execute granular analytics', err);
    } finally {
      setGranularLoading(false);
    }
  };
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
      if (categoricalCols.length > 0 && !visualizationState.selectedDimCol) {
        updateVisualizationState({ selectedDimCol: categoricalCols[0].name });
      }
      if (numericCols.length > 0 && !visualizationState.selectedMetricCol) {
        updateVisualizationState({ selectedMetricCol: numericCols[0].name });
      }
    }
  }, [selectedTableId, activeTable]);

  // Execute Smart Generate
  const handleSmartGenerate = async () => {
    if (!activeTable) return;
    setSmartLoading(true);
    setSmartError(null);
    setExpandedWhyIdx(null);

    try {
      setSmartStage(dictionary.visualization.analyzingStructure);
      await new Promise((resolve) => setTimeout(resolve, 150));

      setSmartStage(dictionary.visualization.selectingVisualizations);
      await new Promise((resolve) => setTimeout(resolve, 150));

      setSmartStage(dictionary.visualization.generatingCharts);
      const res = await api.smartGenerateCharts(datasetId, {
        sheet_name: sheetName,
        table_id: activeTable.table_id,
        max_charts: 5,
      });

      updateVisualizationState({
        smartCharts: res.charts,
        smartEmptyReason: res.charts.length === 0 ? (res.empty_reason || dictionary.visualization.noSmartChartsDesc) : null,
        activeTab: 'smart',
      });
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
      updateVisualizationState({
        customVizResponse: res,
        selectedChartType: chartTypeToUse,
      });
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'Failed to render chart.');
      }
      updateVisualizationState({ customVizResponse: null });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Smart Visualization & Granular Analytics Engine (Phase 9) */}
      <SmartVisualizationPanel
        analyticsResult={granularResult}
        onQuerySubmit={handleGranularQuery}
        isLoading={granularLoading}
      />

      {/* 1. Header Toolbar with Smart Generate and Custom Builder Controls */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs p-4 space-y-3.5 transition-colors">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
              {dictionary.visualization.title}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              {dictionary.visualization.desc}
            </p>
          </div>

          <div className="flex items-center space-x-2.5">
            {/* Table Selector if multiple tables exist */}
            {tables.length > 1 && (
              <select
                value={selectedTableId}
                onChange={(e) => updateVisualizationState({ selectedTableId: e.target.value })}
                className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-2.5 py-1.5 font-medium text-slate-800 dark:text-slate-200 focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-100 cursor-pointer"
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
              className="px-3.5 py-1.5 bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-900 rounded-md text-xs font-semibold shadow-2xs disabled:opacity-50 cursor-pointer transition-colors flex items-center space-x-1.5 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-900 dark:focus-visible:ring-slate-100"
            >
              <svg className="w-3.5 h-3.5 text-slate-300 dark:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>{dictionary.visualization.smartGenerateBtn}</span>
            </button>

            {/* How it works modal trigger */}
            <button
              type="button"
              onClick={() => setIsHowSmartWorksOpen(true)}
              className="px-2.5 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700 rounded-md text-xs font-medium cursor-pointer transition-colors flex items-center space-x-1 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400"
              title={dictionary.visualization.howItWorksBtn}
            >
              <span className="font-mono text-[10px] w-3.5 h-3.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold">
                ?
              </span>
              <span>{dictionary.visualization.howItWorksBtn}</span>
            </button>
          </div>
        </div>

        {/* Truthful Stage Loading Indicator */}
        {smartLoading && smartStage && (
          <div className="flex items-center space-x-2 px-3.5 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-md text-xs text-slate-700 dark:text-slate-300 font-medium">
            <span className="w-2 h-2 rounded-full bg-slate-800 dark:bg-slate-200 animate-pulse" />
            <span>{smartStage}</span>
          </div>
        )}

        {/* Mode Navigation Tabs */}
        <div className="flex items-center space-x-2 pt-1 border-b border-slate-100 dark:border-slate-800 pb-2">
          {smartCharts.length > 0 && (
            <button
              type="button"
              onClick={() => updateVisualizationState({ activeTab: 'smart' })}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
                activeTab === 'smart'
                  ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200/70 dark:hover:bg-slate-700'
              }`}
            >
              {dictionary.visualization.smartChartsTab} ({smartCharts.length})
            </button>
          )}

          <button
            type="button"
            onClick={() => updateVisualizationState({ activeTab: 'custom' })}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors cursor-pointer ${
              activeTab === 'custom'
                ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200/70 dark:hover:bg-slate-700'
            }`}
          >
            {dictionary.visualization.customBuilderTab}
          </button>
        </div>

        {/* Custom Manual Builder Controls */}
        {activeTab === 'custom' && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
            <div>
              <label className="block text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide mb-1">
                {dictionary.visualization.dimension}
              </label>
              <select
                value={selectedDimCol}
                onChange={(e) => updateVisualizationState({ selectedDimCol: e.target.value })}
                className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md p-2 text-slate-800 dark:text-slate-200 font-medium focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-100 cursor-pointer"
              >
                {activeTable?.columns.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.data_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide mb-1">
                {dictionary.visualization.metric}
              </label>
              <select
                value={selectedMetricCol}
                onChange={(e) => updateVisualizationState({ selectedMetricCol: e.target.value })}
                className="w-full text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md p-2 text-slate-800 dark:text-slate-200 font-medium focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-100 cursor-pointer"
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
                <label className="block text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                  {dictionary.visualization.chartType}
                </label>
                <button
                  type="button"
                  onClick={() => handleGenerateCustomChart(selectedChartType)}
                  disabled={loading || !activeTable}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded-md text-[11px] font-medium transition-colors shadow-2xs cursor-pointer disabled:opacity-50"
                >
                  <span>{loading ? dictionary.visualization.rendering : dictionary.visualization.generateChart}</span>
                </button>
              </div>
              <div className="grid grid-cols-3 gap-1.5">
                {SUPPORTED_CHARTS.map((c) => (
                  <button
                    key={c.type}
                    type="button"
                    onClick={() => {
                      updateVisualizationState({ selectedChartType: c.type });
                      if (customVizResponse) {
                        handleGenerateCustomChart(c.type);
                      }
                    }}
                    className={`px-2 py-1.5 text-[11px] font-semibold rounded-md border text-center transition-all cursor-pointer ${
                      selectedChartType === c.type
                        ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 border-slate-900 dark:border-slate-100 shadow-2xs'
                        : 'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'
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
        <div className="p-3.5 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 rounded-md text-xs text-rose-900 dark:text-rose-300 flex items-start space-x-2">
          <span className="font-bold text-rose-700 dark:text-rose-400">{dictionary.visualization.rejection}</span>
          <span>{error || smartError}</span>
        </div>
      )}

      {/* 2. Smart Generated Visualization Set */}
      {activeTab === 'smart' && (
        <div className="space-y-6">
          {smartEmptyReason && smartCharts.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 p-8 text-center space-y-2">
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                {dictionary.visualization.noSmartChartsTitle}
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
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
                    className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs overflow-hidden transition-colors"
                  >
                    {/* Header */}
                    <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-50 dark:bg-slate-950 transition-colors">
                      <div className="space-y-0.5">
                        <div className="flex items-center space-x-2">
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 uppercase shadow-2xs">
                            {item.chart_type}
                          </span>
                          <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">{item.title}</h4>
                        </div>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400">{item.analytical_intent}</p>
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          type="button"
                          onClick={() => setExpandedWhyIdx(isWhyOpen ? null : idx)}
                          className="px-2.5 py-1 text-[11px] font-semibold text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded shadow-2xs cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                        >
                          {dictionary.visualization.whyThisChart}
                        </button>

                        <a
                          href={api.resolveImageUrl(item.visualization.image_url)}
                          download={`${item.chart_id}.png`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-3 py-1 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold rounded shadow-2xs transition-colors"
                        >
                          {dictionary.visualization.downloadPng}
                        </a>
                      </div>
                    </div>

                    {/* "Why this chart?" Explainer Card */}
                    {isWhyOpen && (
                      <div className="px-4 py-3 bg-slate-100/90 dark:bg-slate-950/90 border-b border-slate-200 dark:border-slate-800 text-xs space-y-1 animate-in fade-in duration-100">
                        <div className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-slate-100 text-[11px] uppercase tracking-wider">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-800 dark:bg-slate-200" />
                          <span>{dictionary.visualization.whyThisChart}</span>
                        </div>
                        <p className="text-slate-700 dark:text-slate-300 text-[11px] leading-relaxed pl-3">{item.why_this_chart}</p>
                      </div>
                    )}

                    {/* Chart Image */}
                    <div className="p-6 flex justify-center items-center bg-white dark:bg-slate-900 min-h-[340px]">
                      <img
                        src={`${api.resolveImageUrl(item.visualization.image_url)}?t=${Date.now()}`}
                        alt={item.title}
                        className="max-h-[440px] w-auto object-contain rounded border border-slate-200 dark:border-slate-700 shadow-2xs"
                      />
                    </div>

                    {/* Lineage & Provenance Footer */}
                    <div className="p-3.5 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div>
                        <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">
                          {dictionary.visualization.sheetAndTable}
                        </span>
                        <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                          {item.visualization.chart_metadata.sheet_name} / {item.visualization.chart_metadata.table_id}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">
                          {dictionary.visualization.sourceRange}
                        </span>
                        <span className="font-mono font-medium text-slate-800 dark:text-slate-200 text-[11px]">
                          {item.visualization.chart_metadata.source_range}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">
                          {dictionary.visualization.rowsInScope}
                        </span>
                        <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                          {item.visualization.chart_metadata.rows_included} {dictionary.common.records}
                        </span>
                      </div>
                      <div>
                        <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">
                          {dictionary.visualization.generatedAt}
                        </span>
                        <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
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

      {/* 3. Custom Manual Chart Presentation */}
      {activeTab === 'custom' && (
        <div>
          {customVizResponse ? (
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs overflow-hidden transition-colors">
              <div className="p-3.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-950">
                <div>
                  <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">{customVizResponse.chart_metadata.title}</h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Type: <span className="font-semibold text-slate-700 dark:text-slate-300">{customVizResponse.chart_metadata.chart_type}</span> | Source:{' '}
                    <span className="font-mono text-slate-700 dark:text-slate-300">{customVizResponse.chart_metadata.source_range}</span>
                  </p>
                </div>

                <a
                  href={api.resolveImageUrl(customVizResponse.image_url)}
                  download={`${customVizResponse.chart_metadata.chart_id}.png`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-3 py-1 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold rounded shadow-2xs transition-colors"
                >
                  {dictionary.visualization.downloadPng}
                </a>
              </div>

              <div className="p-6 flex justify-center items-center bg-white dark:bg-slate-900 min-h-[360px]">
                <img
                  src={`${api.resolveImageUrl(customVizResponse.image_url)}?t=${Date.now()}`}
                  alt={customVizResponse.chart_metadata.title}
                  className="max-h-[460px] w-auto object-contain rounded border border-slate-200 dark:border-slate-700 shadow-2xs"
                />
              </div>

              {/* Lineage & Provenance Footer */}
              <div className="p-3.5 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">
                    {dictionary.visualization.sheetAndTable}
                  </span>
                  <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                    {customVizResponse.chart_metadata.sheet_name} / {customVizResponse.chart_metadata.table_id}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">
                    {dictionary.visualization.sourceRange}
                  </span>
                  <span className="font-mono font-medium text-slate-800 dark:text-slate-200 text-[11px]">
                    {customVizResponse.chart_metadata.source_range}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">
                    {dictionary.visualization.rowsInScope}
                  </span>
                  <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                    {customVizResponse.chart_metadata.rows_included} {dictionary.common.records}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">
                    {dictionary.visualization.generatedAt}
                  </span>
                  <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                    {new Date(customVizResponse.chart_metadata.generated_at).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            !loading &&
            !error && (
              <div className="bg-white dark:bg-slate-900 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 p-10 text-center space-y-2">
                <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                  {dictionary.visualization.noChartYet}
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
                  {dictionary.visualization.noChartDesc}
                </p>
                <div className="pt-2">
                  <button
                    type="button"
                    onClick={() => handleGenerateCustomChart('BAR')}
                    className="px-4 py-1.5 bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-900 rounded-md text-xs font-semibold shadow-2xs cursor-pointer transition-colors"
                  >
                    {dictionary.visualization.quickBar}
                  </button>
                </div>
              </div>
            )
          )}
        </div>
      )}

      {/* Smart Generate Explanation Modal */}
      <SmartGenerateExplanationModal
        isOpen={isHowSmartWorksOpen}
        onClose={() => setIsHowSmartWorksOpen(false)}
      />
    </div>
  );
};
