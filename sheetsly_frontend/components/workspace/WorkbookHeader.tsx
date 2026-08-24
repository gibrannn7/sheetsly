'use client';

import React, { useState } from 'react';
import { WorkbookOverview } from '../../lib/types';
import { HowToUseModal } from './HowToUseModal';

interface WorkbookHeaderProps {
  overview: WorkbookOverview;
  onReset: () => void;
}

export const WorkbookHeader: React.FC<WorkbookHeaderProps> = ({ overview, onReset }) => {
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'bg-emerald-50 text-emerald-800 border-emerald-300';
    if (score >= 75) return 'bg-amber-50 text-amber-800 border-amber-300';
    return 'bg-rose-50 text-rose-800 border-rose-300';
  };

  return (
    <>
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 px-6 py-2.5 flex items-center justify-between shadow-2xs">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-md bg-slate-900 flex items-center justify-center text-white font-bold text-sm font-mono">
              S
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 leading-tight">Sheetsly</h1>
              <p className="text-[10px] text-slate-500 font-medium">Spreadsheet Intelligence Workspace</p>
            </div>
          </div>

          <div className="h-5 w-px bg-slate-200 mx-1" />

          <div className="flex items-center space-x-3 text-xs">
            <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded bg-slate-100 font-medium text-slate-800">
              <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="truncate max-w-[200px] font-mono text-[11px]" title={overview.filename}>
                {overview.filename}
              </span>
            </div>

            <span className="text-slate-400 font-mono text-[11px]">({formatBytes(overview.file_size_bytes)})</span>

            <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px]">
              {overview.sheet_count} Sheet{overview.sheet_count > 1 ? 's' : ''}
            </span>

            <div
              className={`flex items-center space-x-1.5 px-2 py-0.5 rounded border text-[11px] font-semibold ${getScoreColor(
                overview.overall_quality_score
              )}`}
            >
              <span>Hygiene: {overview.overall_quality_score}/100</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={() => setIsHelpOpen(true)}
            aria-label="Open How to Use Guide"
            className="inline-flex items-center space-x-1.5 px-2.5 py-1 text-xs font-semibold text-slate-700 bg-slate-50 hover:bg-slate-100 border border-slate-300 rounded-md transition-colors shadow-2xs cursor-pointer focus-visible:ring-2 focus-visible:ring-slate-900"
          >
            <span className="w-3.5 h-3.5 rounded-full bg-slate-800 text-white font-mono text-[10px] flex items-center justify-center font-bold">
              ?
            </span>
            <span>How to Use</span>
          </button>

          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center space-x-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-md transition-colors shadow-2xs cursor-pointer focus-visible:ring-2 focus-visible:ring-slate-900"
          >
            <svg className="w-3.5 h-3.5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span>Open Another File</span>
          </button>
        </div>
      </header>

      {/* Guide Modal */}
      <HowToUseModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />
    </>
  );
};
