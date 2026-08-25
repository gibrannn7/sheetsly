'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';
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
  const { dictionary, t } = useTranslation();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 p-3.5 bg-slate-50/80 border border-slate-200 rounded-lg text-xs">
      {/* 1. Sort Results Card */}
      <div className="bg-white border border-slate-200/90 rounded-md p-3 space-y-2 flex flex-col justify-between shadow-2xs">
        <div>
          <div className="flex items-center justify-between">
            <label className="block text-[11px] font-bold text-slate-800 uppercase tracking-wide">
              {dictionary.builder.sortResults}
            </label>
            {sort && (
              <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                {sort.ascending ? 'ASC' : 'DESC'}
              </span>
            )}
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 leading-tight">
            {dictionary.builder.sortHelper}
          </p>
        </div>

        <div className="flex items-center gap-1.5 pt-1">
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
            aria-label={dictionary.builder.sortResults}
            className="flex-1 min-w-0 bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:ring-1 focus:ring-slate-900 focus:outline-hidden cursor-pointer truncate"
          >
            <option value="">{dictionary.builder.naturalOrder}</option>
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
              title={sort.ascending ? dictionary.builder.asc : dictionary.builder.descending}
              className="shrink-0 px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-md text-xs font-semibold text-slate-800 transition-colors cursor-pointer flex items-center gap-1 shadow-2xs"
            >
              <span>{sort.ascending ? dictionary.builder.sortAscendingShort : dictionary.builder.sortDescendingShort}</span>
            </button>
          )}

          {sort && (
            <button
              type="button"
              onClick={() => onChangeSort(null)}
              title={dictionary.builder.clearSort}
              className="shrink-0 p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-md transition-colors cursor-pointer"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* 2. Limit Output Rows Card */}
      <div className="bg-white border border-slate-200/90 rounded-md p-3 space-y-2 flex flex-col justify-between shadow-2xs">
        <div>
          <div className="flex items-center justify-between">
            <label className="block text-[11px] font-bold text-slate-800 uppercase tracking-wide">
              {dictionary.builder.limitRows}
            </label>
            {limit !== null && (
              <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 border border-slate-200">
                TOP {limit}
              </span>
            )}
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 leading-tight">
            {dictionary.builder.limitHelper}
          </p>
        </div>

        <div className="pt-1">
          <select
            value={limit?.toString() || ''}
            onChange={(e) => {
              const val = e.target.value ? parseInt(e.target.value, 10) : null;
              onChangeLimit(val);
            }}
            aria-label={dictionary.builder.limitRows}
            className="w-full bg-white border border-slate-300 rounded-md px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:ring-1 focus:ring-slate-900 focus:outline-hidden cursor-pointer truncate"
          >
            <option value="">{dictionary.builder.allRecords}</option>
            <option value="5">{t('builder.limitTo', { count: 5 })}</option>
            <option value="10">{t('builder.limitTo', { count: 10 })}</option>
            <option value="25">{t('builder.limitTo', { count: 25 })}</option>
            <option value="50">{t('builder.limitTo', { count: 50 })}</option>
            <option value="100">{t('builder.limitTo', { count: 100 })}</option>
          </select>
        </div>
      </div>
    </div>
  );
};

