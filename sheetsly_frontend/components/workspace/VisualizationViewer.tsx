'use client';

import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import {
  AnalyticalInstruction,
  ChartType,
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
  const [vizResponse, setVizResponse] = useState<VisualizationResponse | null>(null);

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

  const handleGenerateChart = async (chartTypeToUse = selectedChartType) => {
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
        // GROUP_BY dim -> SUM(metric)
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
      setVizResponse(res);
      setSelectedChartType(chartTypeToUse);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'Failed to render chart.');
      }
      setVizResponse(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Controls Card */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-slate-200">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">{dictionary.visualization.title}</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {dictionary.visualization.desc}
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {/* Table Selector if multiple tables */}
            {tables.length > 1 && (
              <select
                value={selectedTableId}
                onChange={(e) => setSelectedTableId(e.target.value)}
                className="text-xs bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1.5 font-medium text-slate-800"
              >
                {tables.map((t) => (
                  <option key={t.table_id} value={t.table_id}>
                    {t.name} ({t.range_address})
                  </option>
                ))}
              </select>
            )}

            <button
              onClick={() => handleGenerateChart(selectedChartType)}
              disabled={loading || !activeTable}
              className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-semibold shadow-2xs disabled:opacity-50 cursor-pointer transition-colors focus-visible:ring-2 focus-visible:ring-slate-900"
            >
              {loading ? dictionary.visualization.rendering : dictionary.visualization.generateChart}
            </button>
          </div>
        </div>

        {/* Dimension & Metric Selection */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
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
            <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide mb-1">{dictionary.visualization.chartType}</label>
            <div className="grid grid-cols-3 gap-1.5">
              {SUPPORTED_CHARTS.map((c) => (
                <button
                  key={c.type}
                  type="button"
                  onClick={() => {
                    setSelectedChartType(c.type);
                    if (vizResponse) {
                      handleGenerateChart(c.type);
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
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-900 flex items-start space-x-2">
          <span className="font-bold text-rose-700">{dictionary.visualization.rejection}</span>
          <span>{error}</span>
        </div>
      )}

      {/* Chart Display Area */}
      {vizResponse ? (
        <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
          <div className="p-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
            <div>
              <h4 className="text-xs font-bold text-slate-900">{vizResponse.chart_metadata.title}</h4>
              <p className="text-[11px] text-slate-500">
                Type: <span className="font-semibold text-slate-700">{vizResponse.chart_metadata.chart_type}</span> | Source:{' '}
                <span className="font-mono text-slate-700">{vizResponse.chart_metadata.source_range}</span>
              </p>
            </div>

            <a
              href={api.resolveImageUrl(vizResponse.image_url)}
              download={`${vizResponse.chart_metadata.chart_id}.png`}
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold rounded-md shadow-2xs transition-colors"
            >
              {dictionary.visualization.downloadPng}
            </a>
          </div>

          <div className="p-6 flex justify-center items-center bg-white min-h-[360px]">
            <img
              src={`${api.resolveImageUrl(vizResponse.image_url)}?t=${Date.now()}`}
              alt={vizResponse.chart_metadata.title}
              className="max-h-[460px] w-auto object-contain rounded border border-slate-200 shadow-2xs"
            />
          </div>

          {/* Lineage & Provenance Footer */}
          <div className="p-3.5 bg-slate-50 border-t border-slate-200 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">{dictionary.visualization.sheetAndTable}</span>
              <span className="font-medium text-slate-800 font-mono text-[11px]">
                {vizResponse.chart_metadata.sheet_name} / {vizResponse.chart_metadata.table_id}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">{dictionary.visualization.sourceRange}</span>
              <span className="font-mono font-medium text-slate-800 text-[11px]">
                {vizResponse.chart_metadata.source_range}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">{dictionary.visualization.rowsInScope}</span>
              <span className="font-medium text-slate-800 font-mono text-[11px]">
                {vizResponse.chart_metadata.rows_included} {dictionary.common.records}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px] uppercase font-bold">{dictionary.visualization.generatedAt}</span>
              <span className="font-medium text-slate-800 font-mono text-[11px]">
                {new Date(vizResponse.chart_metadata.generated_at).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      ) : (
        !loading &&
        !error && (
          <div className="bg-white rounded-lg border border-dashed border-slate-300 p-10 text-center space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">{dictionary.visualization.noChartYet}</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {dictionary.visualization.noChartDesc}
            </p>
            <div className="pt-2">
              <button
                type="button"
                onClick={() => handleGenerateChart('BAR')}
                className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-semibold shadow-2xs cursor-pointer transition-colors"
              >
                {dictionary.visualization.quickBar}
              </button>
            </div>
          </div>
        )
      )}
    </div>
  );
};
