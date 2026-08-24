'use client';

import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import {
  AnalyticalResult,
  ChartRecommendation,
  ChartType,
  VisualizationResponse,
} from '../../lib/types';

interface AnalysisResultViewProps {
  datasetId: string;
  result: AnalyticalResult;
  onReset?: () => void;
}

export const AnalysisResultView: React.FC<AnalysisResultViewProps> = ({
  datasetId,
  result,
}) => {
  const [recommendation, setRecommendation] = useState<ChartRecommendation | null>(null);
  const [vizResponse, setVizResponse] = useState<VisualizationResponse | null>(null);
  const [selectedChartType, setSelectedChartType] = useState<ChartType | null>(null);
  const [vizLoading, setVizLoading] = useState<boolean>(false);
  const [vizError, setVizError] = useState<string | null>(null);
  const [showLineageDetails, setShowLineageDetails] = useState<boolean>(true);

  // Auto-fetch recommendation on result change
  useEffect(() => {
    setVizResponse(null);
    setVizError(null);
    setSelectedChartType(null);

    api
      .recommendChart(result)
      .then((rec) => {
        setRecommendation(rec);
        if (rec.preferred_type) {
          setSelectedChartType(rec.preferred_type);
        }
      })
      .catch(() => {
        setRecommendation(null);
      });
  }, [result]);

  const handleRenderChart = async (chartType: ChartType) => {
    setVizLoading(true);
    setVizError(null);
    try {
      const res = await api.visualizeResult(datasetId, result, chartType);
      setVizResponse(res);
      setSelectedChartType(chartType);
    } catch (err: any) {
      setVizError(err.message || 'Failed to render chart');
    } finally {
      setVizLoading(false);
    }
  };

  // Check if a table column is numeric based on the first non-null value
  const isColNumeric = (colName: string): boolean => {
    if (!result.table_data?.rows || result.table_data.rows.length === 0) return false;
    for (const row of result.table_data.rows) {
      const val = row[colName];
      if (val !== null && val !== undefined) {
        return typeof val === 'number';
      }
    }
    return false;
  };

  return (
    <div className="space-y-5">
      {/* 1. Primary Result Card */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded bg-slate-200 text-slate-800 text-[11px] font-mono font-bold">
              {result.operation}
            </span>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">Verified Result</h3>
          </div>

          <div className="text-[11px] text-slate-500 font-mono">
            Execution: <span className="font-bold text-slate-700">{result.lineage.execution_time_ms} ms</span>
          </div>
        </div>

        {/* Scalar Presentation */}
        {result.result_type === 'SCALAR' && (
          <div className="p-6 text-center bg-white">
            <span className="text-xs text-slate-500 uppercase tracking-wide font-semibold block mb-1">
              {result.lineage.source_columns.join(', ') || result.operation}
            </span>
            <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 font-mono tracking-tight">
              {result.scalar_formatted || String(result.scalar_value)}
            </div>
            <p className="text-xs text-slate-500 mt-2">
              Calculated across {result.lineage.rows_included} verified rows in range{' '}
              <span className="font-mono font-semibold text-slate-700">{result.lineage.source_range}</span>
            </p>
          </div>
        )}

        {/* Table Presentation */}
        {result.result_type === 'TABLE' && result.table_data && (
          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-xs text-left border-collapse font-sans">
              <thead className="bg-slate-100 text-slate-700 font-semibold border-b border-slate-200 sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-slate-500 w-12 text-center font-mono">#</th>
                  {result.table_data.columns.map((col) => {
                    const isNum = isColNumeric(col);
                    return (
                      <th
                        key={col}
                        className={`px-3 py-2 whitespace-nowrap font-mono text-[11px] ${
                          isNum ? 'text-right' : 'text-left'
                        }`}
                      >
                        {col}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {result.table_data.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-400 text-center select-none">{idx + 1}</td>
                    {result.table_data!.columns.map((col) => {
                      const isNum = isColNumeric(col);
                      return (
                        <td
                          key={col}
                          className={`px-3 py-2 whitespace-nowrap text-slate-800 ${
                            isNum ? 'text-right' : 'text-left'
                          }`}
                        >
                          {row[col] !== null && row[col] !== undefined ? (
                            String(row[col])
                          ) : (
                            <span className="text-slate-300">null</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 2. Calculation Lineage & Audit Trail */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        <div
          onClick={() => setShowLineageDetails(!showLineageDetails)}
          className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between cursor-pointer select-none"
        >
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              Calculation Lineage & Provenance
            </span>
            <span className="px-1.5 py-0.2 rounded bg-slate-200 text-slate-700 text-[10px] font-mono font-bold">
              {result.lineage.rows_included} rows included
            </span>
          </div>

          <span className="text-xs text-slate-500 font-medium">
            {showLineageDetails ? 'Hide Trace' : 'Show Trace'}
          </span>
        </div>

        {showLineageDetails && (
          <div className="p-4 space-y-3 text-xs">
            {/* Provenance Key-Value Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-md border border-slate-200">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Worksheet & Table</span>
                <span className="font-medium text-slate-800 font-mono text-[11px]">
                  {result.lineage.sheet_name} / {result.lineage.table_id}
                </span>
              </div>

              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Source Range</span>
                <span className="font-mono font-medium text-slate-800 text-[11px]">{result.lineage.source_range}</span>
              </div>

              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Row Inclusion</span>
                <span className="font-medium text-slate-800 font-mono text-[11px]">
                  {result.lineage.rows_included} of {result.lineage.total_table_rows} ({result.lineage.rows_excluded} excluded)
                </span>
              </div>

              <div>
                <span className="text-slate-400 block text-[10px] uppercase font-bold">Filters Applied</span>
                <span className="font-medium text-slate-800 font-mono text-[11px]">
                  {result.lineage.filters_applied.length > 0 ? result.lineage.filters_applied.join(', ') : 'None'}
                </span>
              </div>
            </div>

            {/* Step-by-Step Calculation Trace */}
            <div>
              <span className="text-[11px] font-bold text-slate-700 uppercase block mb-1">
                Deterministic Execution Trace
              </span>
              <ol className="space-y-1 bg-slate-50 p-3 rounded-md border border-slate-200 font-mono text-[11px] text-slate-700">
                {result.lineage.calculation_steps.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-slate-400 font-bold select-none">{idx + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </div>

      {/* 3. Integrated Visualization Presentation (Phase 6) */}
      {recommendation && recommendation.compatible_types.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
            <div>
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">Visualize Result</h4>
              <p className="text-[11px] text-slate-500">{recommendation.reason}</p>
            </div>

            {/* Compatible Chart Type Switcher */}
            <div className="flex items-center space-x-1.5">
              {recommendation.compatible_types.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => handleRenderChart(type)}
                  disabled={vizLoading}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-md border transition-colors cursor-pointer ${
                    selectedChartType === type
                      ? 'bg-slate-900 text-white border-slate-900'
                      : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {vizError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-800">
              <span className="font-bold">Rejection:</span> {vizError}
            </div>
          )}

          {vizResponse ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center text-xs text-slate-500">
                <span className="font-medium text-slate-700">{vizResponse.chart_metadata.title}</span>
                <a
                  href={api.resolveImageUrl(vizResponse.image_url)}
                  download={`${vizResponse.chart_metadata.chart_id}.png`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold rounded-md shadow-2xs"
                >
                  Download PNG
                </a>
              </div>

              <div className="p-4 flex justify-center items-center bg-slate-50 rounded-md border border-slate-200 min-h-[300px]">
                <img
                  src={`${api.resolveImageUrl(vizResponse.image_url)}?t=${Date.now()}`}
                  alt={vizResponse.chart_metadata.title}
                  className="max-h-[380px] w-auto object-contain rounded border border-slate-200 shadow-2xs"
                />
              </div>
            </div>
          ) : (
            !vizLoading && (
              <div className="p-4 text-center bg-slate-50 rounded-md border border-dashed border-slate-300">
                <p className="text-xs text-slate-500 mb-2">Select a chart type above to render the visualization.</p>
                {selectedChartType && (
                  <button
                    type="button"
                    onClick={() => handleRenderChart(selectedChartType)}
                    className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-md shadow-2xs cursor-pointer"
                  >
                    Render {selectedChartType} Chart
                  </button>
                )}
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
};
