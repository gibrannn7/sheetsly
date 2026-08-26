'use client';

import React, { useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import {
  AggregationSpec,
  AnalyticalInstruction,
  ColumnMetadata,
  FilterCondition,
  OperationType,
  SortSpec,
  TableRegion,
} from '../../lib/types';
import { useWorkspace } from '../../lib/workspace/WorkspaceContext';
import { AnalysisResultView } from './AnalysisResultView';
import { FilterBuilder } from './FilterBuilder';
import { GroupByBuilder } from './GroupByBuilder';
import { OperationSelector } from './OperationSelector';
import { SortLimitBuilder } from './SortLimitBuilder';
import { AnalysisBuilderHelpModal } from '../workspace/AnalysisBuilderHelpModal';

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
  const { builderState, updateBuilderState } = useWorkspace();
  const [showHelpModal, setShowHelpModal] = useState(false);

  const selectedTableId = builderState.selectedTableId || tables[0]?.table_id || '';
  const activeTable = tables.find((t) => t.table_id === selectedTableId) || tables[0];

  const columns: ColumnMetadata[] = activeTable?.columns || [];
  const numericColumns = columns.filter((c) =>
    ['integer', 'float', 'currency', 'percentage'].includes(c.data_type)
  );

  const operation = builderState.operation;
  const targetColumn = builderState.targetColumn || numericColumns[0]?.name || columns[0]?.name || '';
  const filters = builderState.filters;
  const filterCombination = builderState.filterCombination;
  const groupByColumns = builderState.groupByColumns.length > 0 ? builderState.groupByColumns : [columns[0]?.name || ''];
  const aggregations: AggregationSpec[] = builderState.aggregations.length > 0 ? builderState.aggregations : [
    {
      column: numericColumns[0]?.name || columns[0]?.name || '',
      operation: 'SUM' as const,
      alias: `SUM_${numericColumns[0]?.name || columns[0]?.name || ''}`,
    },
  ];
  const sort = builderState.sort;
  const limit = builderState.limit;
  const result = builderState.result;

  // Execution State
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

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
      updateBuilderState({ result: res });
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'An error occurred during calculation.');
      }
      updateBuilderState({ result: null });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="space-y-5">
        {/* Configuration Form Card */}
        <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs p-5 space-y-4 transition-colors">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-slate-200 dark:border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                  {dictionary.builder.title}
                </h2>
                <button
                  type="button"
                  onClick={() => setShowHelpModal(true)}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded text-[10px] font-medium cursor-pointer transition-colors shadow-2xs"
                  title={dictionary.builder.howItWorksBtn}
                >
                  <span className="font-mono text-[9px] w-3 h-3 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold">
                    ?
                  </span>
                  <span>{dictionary.builder.howItWorksBtn}</span>
                </button>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {dictionary.builder.desc}
              </p>
            </div>

            {/* Table Selector */}
            {tables.length > 1 && (
              <div className="flex items-center space-x-2">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">
                  {dictionary.tables.targetTable}:
                </span>
                <select
                  value={selectedTableId}
                  onChange={(e) => {
                    updateBuilderState({ selectedTableId: e.target.value, result: null });
                  }}
                  className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-2.5 py-1 font-medium text-slate-800 dark:text-slate-200 cursor-pointer"
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
              updateBuilderState({ operation: op, result: null });
            }}
          />

          {/* 2. Target Column Selection (for scalar ops) */}
          {requiresTargetColumn && (
            <div className="space-y-1.5 pt-2 border-t border-slate-200 dark:border-slate-800">
              <label className="block text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                {dictionary.builder.targetColumn}{' '}
                {isNumericOperation && (
                  <span className="text-slate-500 dark:text-slate-400 font-normal">
                    (numeric measures only)
                  </span>
                )}
              </label>
              <select
                value={targetColumn}
                onChange={(e) => updateBuilderState({ targetColumn: e.target.value })}
                className="w-full sm:w-80 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-800 dark:text-slate-200 font-medium focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-100 cursor-pointer"
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
            <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
              <GroupByBuilder
                columns={columns}
                groupByColumns={groupByColumns}
                aggregations={aggregations}
                onChangeGroupByColumns={(cols) => updateBuilderState({ groupByColumns: cols })}
                onChangeAggregations={(aggs) => updateBuilderState({ aggregations: aggs })}
              />
            </div>
          )}

          {/* 4. Filters Configuration */}
          <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
            <FilterBuilder
              columns={columns}
              filters={filters}
              filterCombination={filterCombination}
              onChangeFilters={(f) => updateBuilderState({ filters: f })}
              onChangeCombination={(c) => updateBuilderState({ filterCombination: c })}
            />
          </div>

          {/* 5. Sort and Limit Controls */}
          <div className="pt-2 border-t border-slate-200 dark:border-slate-800">
            <SortLimitBuilder
              columns={columns}
              sort={sort}
              limit={limit}
              onChangeSort={(s) => updateBuilderState({ sort: s })}
              onChangeLimit={(l) => updateBuilderState({ limit: l })}
            />
          </div>

          {/* Action Trigger Card */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end">
            <button
              type="button"
              onClick={handleExecute}
              disabled={loading || !activeTable}
              className="px-5 py-2 text-xs font-semibold bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-md hover:bg-slate-800 dark:hover:bg-white disabled:opacity-50 transition-colors shadow-xs cursor-pointer"
            >
              {loading ? dictionary.builder.executing : dictionary.builder.runAnalysis}
            </button>
          </div>
        </div>

        {/* Validation or Engine Errors */}
        {error && (
          <div className="p-4 bg-rose-50 dark:bg-rose-950/40 rounded-lg border border-rose-200 dark:border-rose-800 text-rose-900 dark:text-rose-200 text-xs">
            <h3 className="font-bold mb-1">{dictionary.builder.validationError}</h3>
            <p>{error}</p>
          </div>
        )}

        {/* Result Presentation */}
        {result ? (
          <AnalysisResultView
            datasetId={datasetId}
            result={result}
            onReset={() => updateBuilderState({ result: null })}
          />
        ) : (
          !loading &&
          !error && (
            <div className="bg-white dark:bg-slate-900 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 p-8 text-center space-y-1.5 transition-colors">
              <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                {dictionary.builder.noAnalysisYet}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
                {dictionary.builder.noAnalysisDesc}
              </p>
            </div>
          )
        )}
      </div>

      <AnalysisBuilderHelpModal
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
      />
    </>
  );
};
