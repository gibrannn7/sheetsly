'use client';

import React, { useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import {
  AggregationSpec,
  AnalyticalInstruction,
  AnalyticalResult,
  ColumnMetadata,
  FilterCondition,
  OperationType,
  SortSpec,
  TableRegion,
} from '../../lib/types';
import { AnalysisResultView } from './AnalysisResultView';
import { FilterBuilder } from './FilterBuilder';
import { GroupByBuilder } from './GroupByBuilder';
import { OperationSelector } from './OperationSelector';
import { SortLimitBuilder } from './SortLimitBuilder';

interface OperationBuilderProps {
  datasetId: string;
  sheetName: string;
  tables: TableRegion[];
}

export const OperationBuilder: React.FC<OperationBuilderProps> = ({
  datasetId,
  sheetName,
  tables,
}) => {
  const { dictionary } = useTranslation();
  const [selectedTableId, setSelectedTableId] = useState<string>(tables[0]?.table_id || '');
  const activeTable = tables.find((t) => t.table_id === selectedTableId) || tables[0];

  const columns: ColumnMetadata[] = activeTable?.columns || [];
  const numericColumns = columns.filter((c) =>
    ['integer', 'float', 'currency', 'percentage'].includes(c.data_type)
  );

  // Operation Builder State
  const [operation, setOperation] = useState<OperationType>('SUM');
  const [targetColumn, setTargetColumn] = useState<string>(numericColumns[0]?.name || columns[0]?.name || '');
  const [filters, setFilters] = useState<FilterCondition[]>([]);
  const [filterCombination, setFilterCombination] = useState<'AND' | 'OR'>('AND');
  const [groupByColumns, setGroupByColumns] = useState<string[]>([columns[0]?.name || '']);
  const [aggregations, setAggregations] = useState<AggregationSpec[]>([
    {
      column: numericColumns[0]?.name || columns[0]?.name || '',
      operation: 'SUM',
      alias: `SUM_${numericColumns[0]?.name || columns[0]?.name || ''}`,
    },
  ]);
  const [sort, setSort] = useState<SortSpec | null>(null);
  const [limit, setLimit] = useState<number | null>(null);

  // Execution State
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyticalResult | null>(null);

  const isNumericOperation = ['SUM', 'AVERAGE', 'MEDIAN'].includes(operation);
  const requiresTargetColumn = [
    'SUM',
    'AVERAGE',
    'MIN',
    'MAX',
    'MEDIAN',
    'COUNT_VALUES',
    'DISTINCT_COUNT',
    'SUMIF',
    'SUMIFS',
    'COUNTIF',
    'COUNTIFS',
  ].includes(operation);

  const handleExecute = async () => {
    if (!activeTable) return;
    setLoading(true);
    setError(null);

    try {
      const instruction: AnalyticalInstruction = {
        operation,
        dataset_id: datasetId,
        sheet_name: sheetName,
        table_id: activeTable.table_id,
        target_column: requiresTargetColumn ? targetColumn : undefined,
        filters: filters.length > 0 ? filters : [],
        filter_combination: filterCombination,
        group_by_columns: operation === 'GROUP_BY' ? groupByColumns : [],
        aggregations: operation === 'GROUP_BY' ? aggregations : [],
        sort: sort || undefined,
        limit: limit || undefined,
      };

      const res = await api.analyzeDataset(datasetId, instruction);
      setResult(res);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'An error occurred during calculation.');
      }
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Configuration Form Card */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-slate-200">
          <div>
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">{dictionary.builder.title}</h2>
            <p className="text-xs text-slate-500">
              {dictionary.builder.desc}
            </p>
          </div>

          {/* Table Selector */}
          {tables.length > 1 && (
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-600">Target Table:</span>
              <select
                value={selectedTableId}
                onChange={(e) => {
                  setSelectedTableId(e.target.value);
                  setResult(null);
                }}
                className="text-xs bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1 font-medium text-slate-800"
              >
                {tables.map((t) => (
                  <option key={t.table_id} value={t.table_id}>
                    {t.name} ({t.range_address})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* 1. Operation Selection */}
        <OperationSelector
          selectedOperation={operation}
          onSelectOperation={(op) => {
            setOperation(op);
            setResult(null);
          }}
        />

        {/* 2. Target Column Selection (for scalar ops) */}
        {requiresTargetColumn && (
          <div className="space-y-1.5 pt-2 border-t border-slate-200">
            <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide">
              {dictionary.builder.targetColumn} {isNumericOperation && <span className="text-slate-500 font-normal">(numeric measures only)</span>}
            </label>
            <select
              value={targetColumn}
              onChange={(e) => setTargetColumn(e.target.value)}
              className="w-full sm:w-80 bg-white border border-slate-300 rounded-md px-3 py-1.5 text-xs text-slate-800 font-medium focus:ring-1 focus:ring-slate-900"
            >
              {(isNumericOperation ? numericColumns : columns).map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} ({c.data_type})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* 3. Group By Configuration (for GROUP_BY op) */}
        {operation === 'GROUP_BY' && (
          <div className="pt-2 border-t border-slate-200">
            <GroupByBuilder
              columns={columns}
              groupByColumns={groupByColumns}
              aggregations={aggregations}
              onChangeGroupByColumns={setGroupByColumns}
              onChangeAggregations={setAggregations}
            />
          </div>
        )}

        {/* 4. Filters Configuration */}
        <div className="pt-2 border-t border-slate-200">
          <FilterBuilder
            columns={columns}
            filters={filters}
            filterCombination={filterCombination}
            onChangeFilters={setFilters}
            onChangeCombination={setFilterCombination}
          />
        </div>

        {/* 5. Sort and Limit Controls */}
        <div className="pt-2 border-t border-slate-200">
          <SortLimitBuilder
            columns={columns}
            sort={sort}
            limit={limit}
            onChangeSort={setSort}
            onChangeLimit={setLimit}
          />
        </div>

        {/* Execute Action Bar */}
        <div className="pt-3 border-t border-slate-200 flex items-center justify-between">
          <div className="text-xs text-slate-500 font-mono text-[11px]">
            Target: <span className="font-semibold text-slate-800">{activeTable?.name}</span> ({activeTable?.data_range || activeTable?.range_address})
          </div>

          <button
            type="button"
            onClick={handleExecute}
            disabled={loading || !activeTable}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-semibold shadow-2xs disabled:opacity-50 cursor-pointer transition-colors"
          >
            {loading ? dictionary.builder.executing : dictionary.builder.runAnalysis}
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-800 space-y-1">
          <div className="font-bold">{dictionary.builder.validationError}</div>
          <p>{error}</p>
        </div>
      )}

      {/* Result Presentation */}
      {result ? (
        <AnalysisResultView
          datasetId={datasetId}
          result={result}
          onReset={() => setResult(null)}
        />
      ) : (
        !loading &&
        !error && (
          <div className="bg-white rounded-lg border border-dashed border-slate-300 p-8 text-center space-y-1.5">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">{dictionary.builder.noAnalysisYet}</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {dictionary.builder.noAnalysisDesc}
            </p>
          </div>
        )
      )}
    </div>
  );
};
