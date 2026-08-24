'use client';

import React from 'react';
import { ColumnMetadata, SortSpec } from '../../lib/types';

interface SortLimitBuilderProps {
  columns: ColumnMetadata[];
  sort: SortSpec | null;
  limit: number | null;
  onChangeSort: (sort: SortSpec | null) => void;
  onChangeLimit: (limit: number | null) => void;
}

export const SortLimitBuilder: React.FC<SortLimitBuilderProps> = ({
  columns,
  sort,
  limit,
  onChangeSort,
  onChangeLimit,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 bg-slate-50 border border-slate-200 rounded-md text-xs">
      {/* Sort Section */}
      <div className="space-y-1">
        <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-wider">Sort Results (Optional)</label>
        <div className="flex items-center gap-1.5">
          <select
            value={sort?.column || ''}
            onChange={(e) => {
              const col = e.target.value;
              if (!col) {
                onChangeSort(null);
              } else {
                onChangeSort({
                  column: col,
                  ascending: sort?.ascending ?? false,
                });
              }
            }}
            className="flex-1 bg-white border border-slate-300 rounded-md px-2.5 py-1 text-xs text-slate-800"
          >
            <option value="">Natural dataset order</option>
            {columns.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} ({c.data_type})
              </option>
            ))}
          </select>

          {sort && (
            <button
              type="button"
              onClick={() => onChangeSort({ ...sort, ascending: !sort.ascending })}
              className="px-2 py-1 bg-white hover:bg-slate-50 border border-slate-300 rounded-md text-xs font-semibold text-slate-700 cursor-pointer"
            >
              {sort.ascending ? 'ASC ↑' : 'DESC ↓'}
            </button>
          )}
        </div>
      </div>

      {/* Limit Section */}
      <div className="space-y-1">
        <label className="block text-[10px] font-bold text-slate-600 uppercase tracking-wider">Limit Output Rows (Optional)</label>
        <div className="flex items-center gap-1.5">
          <select
            value={limit?.toString() || ''}
            onChange={(e) => {
              const val = e.target.value ? parseInt(e.target.value, 10) : null;
              onChangeLimit(val);
            }}
            className="w-full bg-white border border-slate-300 rounded-md px-2.5 py-1 text-xs text-slate-800"
          >
            <option value="">All matching records</option>
            <option value="5">Limit to top 5</option>
            <option value="10">Limit to top 10</option>
            <option value="25">Limit to top 25</option>
            <option value="50">Limit to top 50</option>
            <option value="100">Limit to top 100</option>
          </select>
        </div>
      </div>
    </div>
  );
};
