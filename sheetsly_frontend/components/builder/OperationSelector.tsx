'use client';

import React from 'react';
import { OperationType } from '../../lib/types';

interface OperationOption {
  value: OperationType;
  label: string;
  category: 'summarize' | 'group' | 'slice';
  description: string;
  requiresNumeric?: boolean;
}

export const OPERATION_OPTIONS: OperationOption[] = [
  // Summarize / Scalar
  { value: 'SUM', label: 'Total (SUM)', category: 'summarize', description: 'Calculates the arithmetic sum of numeric values', requiresNumeric: true },
  { value: 'AVERAGE', label: 'Average (AVG)', category: 'summarize', description: 'Calculates the arithmetic mean of numeric values', requiresNumeric: true },
  { value: 'COUNT_ROWS', label: 'Count Rows', category: 'summarize', description: 'Counts the total number of records in the selection' },
  { value: 'COUNT_VALUES', label: 'Count Values', category: 'summarize', description: 'Counts non-empty values in a specific column' },
  { value: 'DISTINCT_COUNT', label: 'Unique Values', category: 'summarize', description: 'Counts distinct non-empty values in a column' },
  { value: 'MIN', label: 'Minimum', category: 'summarize', description: 'Finds the smallest numeric or date value' },
  { value: 'MAX', label: 'Maximum', category: 'summarize', description: 'Finds the largest numeric or date value' },
  { value: 'MEDIAN', label: 'Median', category: 'summarize', description: 'Calculates the 50th percentile value', requiresNumeric: true },

  // Group & Pivot
  { value: 'GROUP_BY', label: 'Group By', category: 'group', description: 'Groups records by dimension(s) and computes aggregate metrics' },

  // Slice & Sort
  { value: 'FILTER', label: 'Filter Rows', category: 'slice', description: 'Filters table records matching specific criteria' },
  { value: 'SORT', label: 'Sort Rows', category: 'slice', description: 'Orders table records ascending or descending' },
];

interface OperationSelectorProps {
  selectedOperation: OperationType;
  onSelectOperation: (op: OperationType) => void;
}

export const OperationSelector: React.FC<OperationSelectorProps> = ({
  selectedOperation,
  onSelectOperation,
}) => {
  const currentOp = OPERATION_OPTIONS.find((o) => o.value === selectedOperation) || OPERATION_OPTIONS[0];

  return (
    <div className="space-y-2.5">
      <label className="block text-xs font-bold text-slate-800 uppercase tracking-wide">
        Operation
      </label>

      {/* Categorized Operation Grid */}
      <div className="space-y-2.5">
        <div>
          <div className="text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-wider">Summarize & Calculate</div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
            {OPERATION_OPTIONS.filter((o) => o.category === 'summarize').map((op) => (
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
            <div className="text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-wider">Group & Aggregate</div>
            <div className="grid grid-cols-1 gap-1.5">
              {OPERATION_OPTIONS.filter((o) => o.category === 'group').map((op) => (
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
            <div className="text-[10px] font-bold text-slate-500 mb-1 uppercase tracking-wider">Slice & Order</div>
            <div className="grid grid-cols-2 gap-1.5">
              {OPERATION_OPTIONS.filter((o) => o.category === 'slice').map((op) => (
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
