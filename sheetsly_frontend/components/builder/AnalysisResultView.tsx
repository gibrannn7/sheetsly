'use client';

import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import {
  AnalyticalResult,
  ChartRecommendation,
  ChartType,
  VisualizationResponse,
} from '../../lib/types';
import { downloadCsv, tableToCsv } from '../../lib/export';

interface AnalysisResultViewProps {
  datasetId: string;
  result: AnalyticalResult;
  onReset?: () => void;
}

export const AnalysisResultView: React.FC<AnalysisResultViewProps> = ({
  datasetId,
  result,
}) => {
  const { dictionary, t } = useTranslation();
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

  const handleExportResultCsv = () => {
    if (result.result_type === 'TABLE' && result.table_data) {
      const headers = result.table_data.columns;
      const rows = result.table_data.rows.map((row) =>
        headers.map((h) => (row[h] !== null && row[h] !== undefined ? row[h] : ''))
      );
      const csvStr = tableToCsv(headers, rows);
      downloadCsv(`${result.operation}_result.csv`, csvStr);
    } else if (result.result_type === 'SCALAR') {
      const colName = result.lineage.source_columns.join('_') || result.operation;
      const csvStr = tableToCsv([colName], [[result.scalar_value]]);
      downloadCsv(`${result.operation}_scalar.csv`, csvStr);
    }
  };

  return (
    <div className="space-y-5">
      {/* 1. Primary Result Card */}
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs overflow-hidden transition-colors">
        <div className="p-3.5 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between transition-colors">
          <div className="flex items-center space-x-2">
            <span className="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-[11px] font-mono font-bold">
              {result.operation}
            </span>
            <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">{dictionary.resultView.verifiedResult}</h3>
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleExportResultCsv}
              title="Download result table as CSV"
              className="inline-flex items-center space-x-1.5 px-2 py-0.5 text-xs font-semibold text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 rounded shadow-2xs transition-colors cursor-pointer"
            >
              <svg className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Export CSV</span>
            </button>

            <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
              {t('resultView.executionDuration', { duration: result.lineage.execution_time_ms })}
            </div>
          </div>
        </div>

        {/* Scalar Presentation */}
        {result.result_type === 'SCALAR' && (
          <div className="p-6 text-center bg-white dark:bg-slate-900">
            <span className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wide font-semibold block mb-1">
              {result.lineage.source_columns.join(', ') || result.operation}
            </span>
            <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-slate-100 font-mono tracking-tight">
              {result.scalar_formatted || String(result.scalar_value)}
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
              {t('resultView.rowsInScope', {
                included: result.lineage.rows_included,
                range: result.lineage.source_range,
              })}
            </p>
          </div>
        )}

        {/* Table Presentation */}
        {result.result_type === 'TABLE' && result.table_data && (
          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-xs text-left border-collapse font-sans">
              <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold border-b border-slate-200 dark:border-slate-700 sticky top-0">
                <tr>
                  <th className="px-3 py-2 text-slate-500 dark:text-slate-400 w-12 text-center font-mono">#</th>
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
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-mono text-slate-800 dark:text-slate-200">
                {result.table_data.rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <td className="px-3 py-2 text-slate-400 dark:text-slate-500 text-center select-none">{idx + 1}</td>
                    {result.table_data!.columns.map((col) => {
                      const isNum = isColNumeric(col);
                      return (
                        <td
                          key={col}
                          className={`px-3 py-2 whitespace-nowrap text-slate-800 dark:text-slate-200 ${
                            isNum ? 'text-right' : 'text-left'
                          }`}
                        >
                          {row[col] !== null && row[col] !== undefined ? (
                            String(row[col])
                          ) : (
                            <span className="text-slate-300 dark:text-slate-600">null</span>
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
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs overflow-hidden transition-colors">
        <div
          onClick={() => setShowLineageDetails(!showLineageDetails)}
          className="p-3 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between cursor-pointer select-none"
        >
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
              {dictionary.resultView.lineageTrace}
            </span>
            <span className="px-1.5 py-0.2 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-[10px] font-mono font-bold">
              {result.lineage.rows_included} {dictionary.common.rows}
            </span>
          </div>

          <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            {showLineageDetails ? 'Hide Trace' : 'Show Trace'}
          </span>
        </div>

        {showLineageDetails && (
          <div className="p-4 space-y-3 text-xs">
            {/* Provenance Key-Value Summary */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 dark:bg-slate-950 p-3 rounded-md border border-slate-200 dark:border-slate-800">
              <div>
                <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">{dictionary.resultView.tableHeader}</span>
                <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                  {result.lineage.sheet_name} / {result.lineage.table_id}
                </span>
              </div>

              <div>
                <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">{dictionary.resultView.sourceRange}</span>
                <span className="font-mono font-medium text-slate-800 dark:text-slate-200 text-[11px]">{result.lineage.source_range}</span>
              </div>

              <div>
                <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">{dictionary.resultView.rowInclusion}</span>
                <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                  {t('resultView.rowsExcluded', {
                    included: result.lineage.rows_included,
                    total: result.lineage.total_table_rows,
                    excluded: result.lineage.rows_excluded,
                  })}
                </span>
              </div>

              <div>
                <span className="text-slate-400 dark:text-slate-500 block text-[10px] uppercase font-bold">{dictionary.resultView.filtersApplied}</span>
                <span className="font-medium text-slate-800 dark:text-slate-200 font-mono text-[11px]">
                  {result.lineage.filters_applied.length > 0 ? result.lineage.filters_applied.join(', ') : dictionary.common.none}
                </span>
              </div>
            </div>

            {/* Step-by-Step Calculation Trace */}
            <div>
              <span className="text-[11px] font-bold text-slate-700 dark:text-slate-300 uppercase block mb-1">
                {dictionary.resultView.lineageTrace}
              </span>
              <ol className="space-y-1 bg-slate-50 dark:bg-slate-950 p-3 rounded-md border border-slate-200 dark:border-slate-800 font-mono text-[11px] text-slate-700 dark:text-slate-300">
                {result.lineage.calculation_steps.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-slate-400 dark:text-slate-500 font-bold select-none">{idx + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </div>

      {/* 3. Integrated Visualization Presentation */}
      {recommendation && recommendation.compatible_types.length > 0 && (
        <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs p-4 space-y-4 transition-colors">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
            <div>
              <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">{dictionary.visualization.title}</h4>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">{recommendation.reason}</p>
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
                      ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 border-slate-900 dark:border-slate-100'
                      : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {vizError && (
            <div className="p-3 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 rounded-md text-xs text-rose-800 dark:text-rose-300">
              <span className="font-bold">{dictionary.visualization.rejection}</span> {vizError}
            </div>
          )}

          {vizResponse ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center text-xs text-slate-500 dark:text-slate-400">
                <span className="font-medium text-slate-700 dark:text-slate-300">{vizResponse.chart_metadata.title}</span>
                <a
                  href={api.resolveImageUrl(vizResponse.image_url)}
                  download={`${vizResponse.chart_metadata.chart_id}.png`}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold rounded-md shadow-2xs"
                >
                  {dictionary.visualization.downloadPng}
                </a>
              </div>

              <div className="p-4 flex justify-center items-center bg-slate-50 dark:bg-slate-950 rounded-md border border-slate-200 dark:border-slate-800 min-h-[300px]">
                <img
                  src={api.resolveImageUrl(vizResponse.image_url)}
                  alt={vizResponse.chart_metadata.title}
                  className="max-h-[380px] w-auto object-contain rounded border border-slate-200 dark:border-slate-700 shadow-2xs"
                />
              </div>
            </div>
          ) : (
            !vizLoading && (
              <div className="p-4 text-center bg-slate-50 dark:bg-slate-950 rounded-md border border-dashed border-slate-300 dark:border-slate-700">
                <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">{dictionary.visualization.noChartDesc}</p>
                {selectedChartType && (
                  <button
                    type="button"
                    onClick={() => handleRenderChart(selectedChartType)}
                    className="px-3 py-1.5 bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-900 text-xs font-semibold rounded-md shadow-2xs cursor-pointer"
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
