'use client';

import React from 'react';
import { SheetMetadata } from '../../lib/types';

interface SheetListProps {
  sheets: SheetMetadata[];
  activeSheetName: string;
  onSelectSheet: (name: string) => void;
}

export const SheetList: React.FC<SheetListProps> = ({
  sheets,
  activeSheetName,
  onSelectSheet,
}) => {
  return (
    <div className="bg-slate-100 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 px-6 py-1.5 flex items-center space-x-1.5 overflow-x-auto transition-colors">
      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mr-2 flex-shrink-0">
        Worksheets:
      </span>
      {sheets.map((sheet) => {
        const isActive = sheet.name === activeSheetName;
        return (
          <button
            key={sheet.name}
            type="button"
            onClick={() => onSelectSheet(sheet.name)}
            className={`flex items-center space-x-2 px-3 py-1 rounded-md text-xs font-semibold transition-all flex-shrink-0 cursor-pointer ${
              isActive
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs border border-slate-300 dark:border-slate-700 ring-1 ring-slate-300/50 dark:ring-slate-700/50'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-200/70 dark:hover:bg-slate-800/70 border border-transparent'
            }`}
          >
            <svg
              className={`w-3.5 h-3.5 ${isActive ? 'text-slate-800 dark:text-slate-200' : 'text-slate-400 dark:text-slate-500'}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.8}
                d="M3 10h18M3 14h18m-9-4v8m-7 4h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <span>{sheet.name}</span>
            <span className="text-[10px] px-1 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 font-mono">
              {sheet.total_rows}r × {sheet.total_columns}c
            </span>
            {sheet.tables.length > 0 && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                {sheet.tables.length} {sheet.tables.length === 1 ? 'table' : 'tables'}
              </span>
            )}
            {sheet.is_hidden && (
              <span className="text-[9px] px-1 rounded bg-amber-100 dark:bg-amber-950/50 text-amber-800 dark:text-amber-300 font-medium">
                Hidden
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
