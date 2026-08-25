'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';
import { ColumnMetadata, FilterCondition, FilterOperator } from '../../lib/types';

interface FilterBuilderProps {
  columns: ColumnMetadata[];
  filters: FilterCondition[];
  filterCombination: 'AND' | 'OR';
  onChangeFilters: (filters: FilterCondition[]) => void;
  onChangeCombination: (combination: 'AND' | 'OR') => void;
}

const OPERATOR_LABELS: { operator: FilterOperator; label: string; types: string[] }[] = [
  { operator: 'equals', label: 'equals (=)', types: ['all'] },
  { operator: 'not_equals', label: 'does not equal (!=)', types: ['all'] },
  { operator: 'contains', label: 'contains', types: ['string', 'text'] },
  { operator: 'not_contains', label: 'does not contain', types: ['string', 'text'] },
  { operator: 'starts_with', label: 'starts with', types: ['string', 'text'] },
  { operator: 'ends_with', label: 'ends with', types: ['string', 'text'] },
  { operator: 'greater_than', label: 'greater than (>)', types: ['integer', 'float', 'currency', 'percentage', 'date', 'datetime'] },
  { operator: 'greater_or_equal', label: 'greater than or equal (>=)', types: ['integer', 'float', 'currency', 'percentage', 'date', 'datetime'] },
  { operator: 'less_than', label: 'less than (<)', types: ['integer', 'float', 'currency', 'percentage', 'date', 'datetime'] },
  { operator: 'less_or_equal', label: 'less than or equal (<=)', types: ['integer', 'float', 'currency', 'percentage', 'date', 'datetime'] },
  { operator: 'between', label: 'is between [min, max]', types: ['integer', 'float', 'currency', 'percentage', 'date', 'datetime'] },
  { operator: 'in_list', label: 'is in list', types: ['all'] },
  { operator: 'is_empty', label: 'is empty / null', types: ['all'] },
  { operator: 'is_not_empty', label: 'is not empty', types: ['all'] },
];

export const FilterBuilder: React.FC<FilterBuilderProps> = ({
  columns,
  filters,
  filterCombination,
  onChangeFilters,
  onChangeCombination,
}) => {
  const { dictionary } = useTranslation();

  const getCompatibleOperators = (colName: string) => {
    const col = columns.find((c) => c.name === colName);
    const colType = col?.data_type || 'string';
    return OPERATOR_LABELS.filter((op) => op.types.includes('all') || op.types.includes(colType));
  };

  const handleAddFilter = () => {
    const defaultCol = columns[0]?.name || '';
    const newCondition: FilterCondition = {
      column: defaultCol,
      operator: 'equals',
      value: '',
    };
    onChangeFilters([...filters, newCondition]);
  };

  const handleUpdateFilter = (index: number, updated: Partial<FilterCondition>) => {
    const nextFilters = [...filters];
    nextFilters[index] = { ...nextFilters[index], ...updated };
    onChangeFilters(nextFilters);
  };

  const handleRemoveFilter = (index: number) => {
    const nextFilters = filters.filter((_, i) => i !== index);
    onChangeFilters(nextFilters);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-slate-800 uppercase tracking-wide">
          {dictionary.builder.filters} ({filters.length})
        </label>

        {filters.length > 1 && (
          <div className="flex items-center space-x-1.5 text-xs">
            <span className="text-slate-500 font-medium">{dictionary.builder.match}</span>
            <button
              type="button"
              onClick={() => onChangeCombination('AND')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold border transition-colors cursor-pointer ${
                filterCombination === 'AND'
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
              }`}
            >
              {dictionary.builder.matchAll}
            </button>
            <button
              type="button"
              onClick={() => onChangeCombination('OR')}
              className={`px-2 py-0.5 rounded text-[11px] font-bold border transition-colors cursor-pointer ${
                filterCombination === 'OR'
                  ? 'bg-slate-900 text-white border-slate-900'
                  : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
              }`}
            >
              {dictionary.builder.matchAny}
            </button>
          </div>
        )}
      </div>

      {filters.length === 0 ? (
        <div className="p-3 bg-slate-50 border border-dashed border-slate-300 rounded-md text-center">
          <p className="text-xs text-slate-500 mb-2">{dictionary.builder.noFilters}</p>
          <button
            type="button"
            onClick={handleAddFilter}
            className="px-3 py-1 bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 text-xs font-semibold rounded-md shadow-2xs cursor-pointer transition-colors"
          >
            {dictionary.builder.addFilter}
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {filters.map((filter, idx) => {
            const compatibleOps = getCompatibleOperators(filter.column);
            const isBetween = filter.operator === 'between';
            const isEmptyCheck = filter.operator === 'is_empty' || filter.operator === 'is_not_empty';

            return (
              <div
                key={idx}
                className="flex flex-wrap items-center gap-2 p-2.5 bg-slate-50 border border-slate-200 rounded-md text-xs"
              >
                {/* Column Dropdown */}
                <select
                  value={filter.column}
                  onChange={(e) => handleUpdateFilter(idx, { column: e.target.value })}
                  className="bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:ring-1 focus:ring-slate-900"
                >
                  {columns.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name} ({c.data_type})
                    </option>
                  ))}
                </select>

                {/* Operator Dropdown */}
                <select
                  value={filter.operator}
                  onChange={(e) => handleUpdateFilter(idx, { operator: e.target.value as FilterOperator })}
                  className="bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs text-slate-800 focus:ring-1 focus:ring-slate-900"
                >
                  {compatibleOps.map((op) => (
                    <option key={op.operator} value={op.operator}>
                      {op.label}
                    </option>
                  ))}
                </select>

                {/* Operand Value Input */}
                {!isEmptyCheck && (
                  <div className="flex-1 min-w-[140px] flex items-center gap-1.5">
                    {isBetween ? (
                      <div className="flex items-center gap-1 w-full">
                        <input
                          type="text"
                          placeholder="Min"
                          value={Array.isArray(filter.value) ? filter.value[0] || '' : ''}
                          onChange={(e) => {
                            const currentMax = Array.isArray(filter.value) ? filter.value[1] || '' : '';
                            handleUpdateFilter(idx, { value: [e.target.value, currentMax] });
                          }}
                          className="w-1/2 bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs text-slate-800 focus:ring-1 focus:ring-slate-900"
                        />
                        <span className="text-slate-400 text-xs font-semibold">to</span>
                        <input
                          type="text"
                          placeholder="Max"
                          value={Array.isArray(filter.value) ? filter.value[1] || '' : ''}
                          onChange={(e) => {
                            const currentMin = Array.isArray(filter.value) ? filter.value[0] || '' : '';
                            handleUpdateFilter(idx, { value: [currentMin, e.target.value] });
                          }}
                          className="w-1/2 bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs text-slate-800 focus:ring-1 focus:ring-slate-900"
                        />
                      </div>
                    ) : (
                      <input
                        type="text"
                        placeholder={filter.operator === 'in_list' ? 'val1, val2, val3' : 'Target value'}
                        value={Array.isArray(filter.value) ? filter.value.join(', ') : filter.value ?? ''}
                        onChange={(e) => {
                          const val = filter.operator === 'in_list' ? e.target.value.split(',').map((s) => s.trim()) : e.target.value;
                          handleUpdateFilter(idx, { value: val });
                        }}
                        className="w-full bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs text-slate-800 focus:ring-1 focus:ring-slate-900"
                      />
                    )}
                  </div>
                )}

                {/* Remove Condition Button */}
                <button
                  type="button"
                  onClick={() => handleRemoveFilter(idx)}
                  aria-label={`Remove filter condition for ${filter.column}`}
                  className="px-2 py-1 text-slate-400 hover:text-rose-600 focus-visible:ring-2 focus-visible:ring-rose-500 text-xs font-bold rounded cursor-pointer transition-colors"
                  title="Remove condition"
                >
                  ✕
                </button>
              </div>
            );
          })}

          <button
            type="button"
            onClick={handleAddFilter}
            className="text-xs text-slate-700 hover:text-slate-900 font-semibold py-1 flex items-center gap-1 cursor-pointer"
          >
            {dictionary.builder.addAnotherFilter}
          </button>
        </div>
      )}
    </div>
  );
};
