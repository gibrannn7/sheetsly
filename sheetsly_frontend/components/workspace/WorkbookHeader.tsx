'use client';

import React, { useState } from 'react';
import { useTranslation } from '../../lib/i18n';
import { WorkbookOverview } from '../../lib/types';
import { HowToUseModal } from './HowToUseModal';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeSwitcher } from './ThemeSwitcher';

interface WorkbookHeaderProps {
  overview: WorkbookOverview;
  onReset: () => void;
}

export const WorkbookHeader: React.FC<WorkbookHeaderProps> = ({ overview, onReset }) => {
  const { dictionary } = useTranslation();
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800';
    if (score >= 75) return 'bg-amber-50 dark:bg-amber-950/50 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-800';
    return 'bg-rose-50 dark:bg-rose-950/50 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-800';
  };

  return (
    <>
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-30 px-4 sm:px-6 py-2 flex items-center justify-between gap-3 shadow-2xs transition-colors">
        {/* Left: Brand Identity & Active Workbook Metadata */}
        <div className="flex items-center gap-3 min-w-0 shrink">
          {/* Brand Block */}
          <div className="flex items-center gap-2.5 shrink-0">
            <img
              src="/assets/logo.png"
              alt="Sheetsly Logo"
              className="w-8 h-8 object-contain rounded-md shadow-2xs shrink-0"
            />
            <div className="leading-tight">
              <h1 className="text-sm font-bold text-slate-900 dark:text-slate-100 tracking-tight">{dictionary.common.appName}</h1>
              <p className="text-[10px] text-slate-500 dark:text-slate-400 font-medium hidden md:block">{dictionary.common.tagline}</p>
            </div>
          </div>

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700 shrink-0" />

          {/* Active Workbook Identity */}
          <div className="flex items-center gap-2 min-w-0 shrink text-xs">
            <div
              className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 min-w-0 shrink border border-slate-200/60 dark:border-slate-700/60"
              title={overview.filename}
            >
              <svg className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="truncate max-w-[120px] sm:max-w-[170px] md:max-w-[210px] lg:max-w-[260px] xl:max-w-[320px] font-mono text-[11px] font-medium">
                {overview.filename}
              </span>
            </div>

            <span className="text-slate-400 dark:text-slate-500 font-mono text-[11px] shrink-0 hidden sm:inline">
              ({formatBytes(overview.file_size_bytes)})
            </span>

            <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-medium text-[11px] shrink-0 hidden lg:inline-flex">
              {overview.sheet_count} {overview.sheet_count > 1 ? dictionary.common.sheets : dictionary.common.sheet}
            </span>

            {/* Hygiene Quality Score Indicator */}
            <div
              className={`flex items-center gap-1 px-2 py-0.5 rounded border text-[11px] font-semibold shrink-0 ${getScoreColor(
                overview.overall_quality_score
              )}`}
              title={`${dictionary.common.hygiene}: ${overview.overall_quality_score}/100`}
            >
              <span className="font-medium text-slate-600 dark:text-slate-400">{dictionary.common.hygiene}:</span>
              <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                {overview.overall_quality_score}
                <span className="text-[10px] font-normal opacity-70">/100</span>
              </span>
            </div>
          </div>
        </div>

        {/* Right: Theme, Language & Workspace Actions */}
        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <ThemeSwitcher />
          <LanguageSwitcher />

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700 shrink-0 hidden sm:block" />

          {/* How to Use / Guide Action */}
          <button
            type="button"
            onClick={() => setIsHelpOpen(true)}
            aria-label={dictionary.nav.howToUse}
            title={dictionary.nav.howToUse}
            className="h-7 px-2.5 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 rounded-md transition-colors shadow-2xs cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400 whitespace-nowrap"
          >
            <span className="w-3.5 h-3.5 rounded-full bg-slate-800 dark:bg-slate-200 text-white dark:text-slate-900 font-mono text-[10px] flex items-center justify-center font-bold shrink-0">
              ?
            </span>
            <span className="hidden md:inline">{dictionary.nav.howToUse}</span>
          </button>

          {/* Open Another File Action */}
          <button
            type="button"
            onClick={onReset}
            aria-label={dictionary.common.openAnotherFile}
            title={dictionary.common.openAnotherFile}
            className="h-7 px-2.5 inline-flex items-center gap-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700 rounded-md transition-colors shadow-2xs cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400 whitespace-nowrap"
          >
            <svg className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            <span className="hidden xl:inline">{dictionary.common.openAnotherFile}</span>
          </button>
        </div>
      </header>

      {/* Guide Modal */}
      <HowToUseModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />
    </>
  );
};
