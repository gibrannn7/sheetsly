'use client';

import React from 'react';
import { AggregationSpec, ColumnMetadata } from '../../lib/types';

interface GroupByBuilderProps {
  columns: ColumnMetadata[];
  groupByColumns: string[];
  aggregations: AggregationSpec[];
  onChangeGroupByColumns: (cols: string[]) => void;
  onChangeAggregations: (aggs: AggregationSpec[]) => void;
}

const AGGREGATION_OPS: { value: AggregationSpec['operation']; label: string; requiresNumeric?: boolean }[] = [
  { value: 'SUM', label: 'SUM (Total)', requiresNumeric: true },
  { value: 'AVERAGE', label: 'AVERAGE (Mean)', requiresNumeric: true },
  { value: 'COUNT_ROWS', label: 'COUNT (Rows in Group)' },
  { value: 'COUNT_VALUES', label: 'COUNT (Non-null Values)' },
  { value: 'DISTINCT_COUNT', label: 'DISTINCT (Unique Values)' },
  { value: 'MIN', label: 'MIN (Minimum)' },
  { value: 'MAX', label: 'MAX (Maximum)' },
  { value: 'MEDIAN', label: 'MEDIAN (Median)', requiresNumeric: true },
];

export const GroupByBuilder: React.FC<GroupByBuilderProps> = ({
  columns,
  groupByColumns,
  aggregations,
  onChangeGroupByColumns,
  onChangeAggregations,
}) => {
  const numericColumns = columns.filter((c) =>
    ['integer', 'float', 'currency', 'percentage'].includes(c.data_type)
  );

  const handleAddGroupByCol = () => {
    const available = columns.find((c) => !groupByColumns.includes(c.name));
    if (available) {
      onChangeGroupByColumns([...groupByColumns, available.name]);
    }
  };

  const handleRemoveGroupByCol = (index: number) => {
    const next = groupByColumns.filter((_, i) => i !== index);
    onChangeGroupByColumns(next);
  };

  const handleUpdateGroupByCol = (index: number, colName: string) => {
    const next = [...groupByColumns];
    next[index] = colName;
    onChangeGroupByColumns(next);
  };

  const handleAddAggregation = () => {
    const defaultCol = numericColumns[0]?.name || columns[0]?.name || '';
    const newAgg: AggregationSpec = {
      column: defaultCol,
      operation: 'SUM',
      alias: `SUM_${defaultCol}`,
    };
    onChangeAggregations([...aggregations, newAgg]);
  };

  const handleUpdateAggregation = (index: number, updated: Partial<AggregationSpec>) => {
    const next = [...aggregations];
    next[index] = { ...next[index], ...updated };
    onChangeAggregations(next);
  };

  const handleRemoveAggregation = (index: number) => {
    const next = aggregations.filter((_, i) => i !== index);
    onChangeAggregations(next);
  };

  return (
    <div className="space-y-4 p-3.5 bg-slate-50 border border-slate-200 rounded-lg">
      {/* 1. Grouping Dimension Selection */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-800 uppercase tracking-wide">
            Group by Dimension(s)
          </label>
          <button
            type="button"
            onClick={handleAddGroupByCol}
            disabled={groupByColumns.length >= columns.length}
            className="text-xs text-slate-700 hover:text-slate-950 font-semibold cursor-pointer disabled:opacity-40"
          >
            + Add Dimension
          </button>
        </div>

        <div className="space-y-1.5">
          {groupByColumns.map((colName, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <span className="text-xs text-slate-500 font-mono w-4">{idx + 1}.</span>
              <select
                value={colName}
                onChange={(e) => handleUpdateGroupByCol(idx, e.target.value)}
                className="flex-1 bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:ring-1 focus:ring-slate-900"
              >
                {columns.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.data_type})
                  </option>
                ))}
              </select>

              {groupByColumns.length > 1 && (
                <button
                  type="button"
                  onClick={() => handleRemoveGroupByCol(idx)}
                  className="px-2 py-1 text-slate-400 hover:text-rose-600 text-xs font-bold"
                  title="Remove dimension"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 2. Multi-Aggregation Specs */}
      <div className="space-y-2 pt-3 border-t border-slate-200">
        <div className="flex items-center justify-between">
          <label className="text-xs font-bold text-slate-800 uppercase tracking-wide">
            Aggregated Metrics ({aggregations.length})
          </label>
          <button
            type="button"
            onClick={handleAddAggregation}
            className="text-xs text-slate-700 hover:text-slate-950 font-semibold cursor-pointer"
          >
            + Add Metric
          </button>
        </div>

        <div className="space-y-2">
          {aggregations.map((agg, idx) => (
            <div key={idx} className="flex flex-wrap items-center gap-2 p-2 bg-white border border-slate-200 rounded-md text-xs">
              <span className="text-[11px] font-semibold text-slate-500">Calculate</span>

              {/* Aggregation Function */}
              <select
                value={agg.operation}
                onChange={(e) => {
                  const op = e.target.value as AggregationSpec['operation'];
                  handleUpdateAggregation(idx, {
                    operation: op,
                    alias: `${op}_${agg.column}`,
                  });
                }}
                className="bg-slate-50 border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 font-semibold focus:ring-1 focus:ring-slate-900"
              >
                {AGGREGATION_OPS.map((op) => (
                  <option key={op.value} value={op.value}>
                    {op.label}
                  </option>
                ))}
              </select>

              <span className="text-[11px] font-semibold text-slate-500">of</span>

              {/* Target Column */}
              <select
                value={agg.column}
                onChange={(e) => {
                  const cName = e.target.value;
                  handleUpdateAggregation(idx, {
                    column: cName,
                    alias: `${agg.operation}_${cName}`,
                  });
                }}
                className="bg-slate-50 border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 font-medium focus:ring-1 focus:ring-slate-900"
              >
                {columns.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name} ({c.data_type})
                  </option>
                ))}
              </select>

              <span className="text-[11px] font-semibold text-slate-500">as</span>

              {/* Custom Alias */}
              <input
                type="text"
                placeholder="Column header"
                value={agg.alias || ''}
                onChange={(e) => handleUpdateAggregation(idx, { alias: e.target.value })}
                className="flex-1 min-w-[100px] bg-slate-50 border border-slate-300 rounded px-2 py-1 text-xs text-slate-800 focus:ring-1 focus:ring-slate-900"
              />

              {aggregations.length > 1 && (
                <button
                  type="button"
                  onClick={() => handleRemoveAggregation(idx)}
                  aria-label={`Remove aggregation metric for ${agg.column}`}
                  className="px-1.5 py-0.5 text-slate-400 hover:text-rose-600 focus-visible:ring-2 focus-visible:ring-rose-500 text-xs font-bold"
                  title="Remove metric"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
