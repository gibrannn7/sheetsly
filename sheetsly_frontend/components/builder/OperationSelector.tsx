'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';
import { OperationType } from '../../lib/types';

interface OperationOption {
  value: OperationType;
  label: string;
  category: 'summarize' | 'group' | 'slice';
  description: string;
  requiresNumeric?: boolean;
}

interface OperationSelectorProps {
  selectedOperation: OperationType;
  onSelectOperation: (op: OperationType) => void;
}

export const OperationSelector: React.FC<OperationSelectorProps> = ({
  selectedOperation,
  onSelectOperation,
}) => {
  const { dictionary } = useTranslation();

  const operationOptions: OperationOption[] = [
    // Summarize / Scalar
    {
      value: 'SUM',
      label: dictionary.builder.operations.sumLabel,
      category: 'summarize',
      description: dictionary.builder.operations.sumDesc,
      requiresNumeric: true,
    },
    {
      value: 'AVERAGE',
      label: dictionary.builder.operations.avgLabel,
      category: 'summarize',
      description: dictionary.builder.operations.avgDesc,
      requiresNumeric: true,
    },
    {
      value: 'COUNT_ROWS',
      label: dictionary.builder.operations.countRowsLabel,
      category: 'summarize',
      description: dictionary.builder.operations.countRowsDesc,
    },
    {
      value: 'COUNT_VALUES',
      label: dictionary.builder.operations.countValuesLabel,
      category: 'summarize',
      description: dictionary.builder.operations.countValuesDesc,
    },
    {
      value: 'DISTINCT_COUNT',
      label: dictionary.builder.operations.distinctCountLabel,
      category: 'summarize',
      description: dictionary.builder.operations.distinctCountDesc,
    },
    {
      value: 'MIN',
      label: dictionary.builder.operations.minLabel,
      category: 'summarize',
      description: dictionary.builder.operations.minDesc,
    },
    {
      value: 'MAX',
      label: dictionary.builder.operations.maxLabel,
      category: 'summarize',
      description: dictionary.builder.operations.maxDesc,
    },
    {
      value: 'MEDIAN',
      label: dictionary.builder.operations.medianLabel,
      category: 'summarize',
      description: dictionary.builder.operations.medianDesc,
      requiresNumeric: true,
    },

    // Group & Pivot
    {
      value: 'GROUP_BY',
      label: dictionary.builder.operations.groupByLabel,
      category: 'group',
      description: dictionary.builder.operations.groupByDesc,
    },

    // Slice & Sort
    {
      value: 'FILTER',
      label: dictionary.builder.operations.filterLabel,
      category: 'slice',
      description: dictionary.builder.operations.filterDesc,
    },
    {
      value: 'SORT',
      label: dictionary.builder.operations.sortLabel,
      category: 'slice',
      description: dictionary.builder.operations.sortDesc,
    },
  ];

  const currentOp = operationOptions.find((o) => o.value === selectedOperation) || operationOptions[0];

  return (
    <div className="space-y-2.5">
      <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide">
        {dictionary.builder.operation}
      </label>

      {/* Categorized Operation Grid */}
      <div className="space-y-2.5">
        <div>
          <div className="text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-wider">
            {dictionary.builder.summarizeCategory}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
            {operationOptions
              .filter((o) => o.category === 'summarize')
              .map((op) => (
                <button
                  key={op.value}
                  type="button"
                  onClick={() => onSelectOperation(op.value)}
                  className={`px-2.5 py-1.5 text-xs font-medium rounded-md border text-left transition-colors cursor-pointer ${
                    selectedOperation === op.value
                      ? 'bg-slate-900 border-slate-900 text-white font-semibold'
                      : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {op.label}
                </button>
              ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <div>
            <div className="text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-wider">
              {dictionary.builder.groupCategory}
            </div>
            <div className="grid grid-cols-1 gap-1.5">
              {operationOptions
                .filter((o) => o.category === 'group')
                .map((op) => (
                  <button
                    key={op.value}
                    type="button"
                    onClick={() => onSelectOperation(op.value)}
                    className={`px-2.5 py-1.5 text-xs font-medium rounded-md border text-left transition-colors cursor-pointer ${
                      selectedOperation === op.value
                        ? 'bg-slate-900 border-slate-900 text-white font-semibold'
                        : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    {op.label}
                  </button>
                ))}
            </div>
          </div>

          <div>
            <div className="text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-wider">
              {dictionary.builder.sliceCategory}
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {operationOptions
                .filter((o) => o.category === 'slice')
                .map((op) => (
                  <button
                    key={op.value}
                    type="button"
                    onClick={() => onSelectOperation(op.value)}
                    className={`px-2.5 py-1.5 text-xs font-medium rounded-md border text-left transition-colors cursor-pointer ${
                      selectedOperation === op.value
                        ? 'bg-slate-900 border-slate-900 text-white font-semibold'
                        : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    {op.label}
                  </button>
                ))}
            </div>
          </div>
        </div>
      </div>

      {/* Description helper text */}
      <div className="p-2 bg-slate-50 border border-slate-200 rounded-md text-[11px] text-slate-600">
        <span className="font-semibold text-slate-800">{currentOp.label}:</span> {currentOp.description}
      </div>
    </div>
  );
};
