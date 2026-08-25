'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { SpreadsheetUploader } from '../components/upload/SpreadsheetUploader';
import { WorkbookHeader } from '../components/workspace/WorkbookHeader';
import { SheetList } from '../components/workspace/SheetList';
import { DetectedTablesViewer } from '../components/workspace/DetectedTablesViewer';
import { ActualDataViewer } from '../components/workspace/ActualDataViewer';
import { DataQualityPanel } from '../components/workspace/DataQualityPanel';
import { VisualizationViewer } from '../components/workspace/VisualizationViewer';
import { OperationBuilder } from '../components/builder/OperationBuilder';
import { AIQueryWorkspace } from '../components/ai/AIQueryWorkspace';
import { HowToUseModal } from '../components/workspace/HowToUseModal';
import { LanguageSwitcher } from '../components/workspace/LanguageSwitcher';
import { ThemeSwitcher } from '../components/workspace/ThemeSwitcher';
import { LanguageOnboardingModal } from '../components/workspace/LanguageOnboardingModal';
import { useTranslation } from '../lib/i18n';
import { useWorkspace } from '../lib/workspace/WorkspaceContext';
import { WorkbookOverview } from '../lib/types';

export default function Home() {
  const { dictionary } = useTranslation();
  const router = useRouter();
  const {
    overview,
    activeSheetName,
    activeViewMode,
    setOverview,
    setActiveSheetName,
    setActiveViewMode,
    resetWorkspace,
  } = useWorkspace();

  const [isHelpOpen, setIsHelpOpen] = useState<boolean>(false);

  const handleUploadSuccess = (data: WorkbookOverview) => {
    setOverview(data);
    if (data.sheets.length > 0) {
      setActiveSheetName(data.sheets[0].name);
    }
    // Update route to active session for shareable/refreshable URL
    router.push(`/workspace/${data.dataset_id}`);
  };

  const handleReset = () => {
    resetWorkspace();
  };

  const currentSheet = overview?.sheets.find((s) => s.name === activeSheetName) || overview?.sheets[0];

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors">
      {!overview ? (
        // Landing / Upload Screen
        <div className="flex-1 flex flex-col justify-between items-center px-4 py-8 max-w-5xl mx-auto w-full">
          {/* Top Bar on Landing Page */}
          <div className="w-full flex items-center justify-between pb-6">
            <div className="flex items-center space-x-2.5">
              <img
                src="/assets/logo.png"
                alt="Sheetsly Logo"
                className="w-8 h-8 object-contain rounded-md shadow-2xs"
              />
              <div>
                <span className="text-sm font-bold text-slate-900 dark:text-slate-100 leading-none block">
                  {dictionary.common.appName}
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">
                  {dictionary.common.tagline}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <ThemeSwitcher />
              <LanguageSwitcher />

              <button
                type="button"
                onClick={() => setIsHelpOpen(true)}
                aria-label={dictionary.nav.howToUse}
                title={dictionary.nav.howToUse}
                className="h-7 px-2.5 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md transition-colors shadow-2xs cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400 whitespace-nowrap"
              >
                <span className="w-3.5 h-3.5 rounded-full bg-slate-800 dark:bg-slate-200 text-white dark:text-slate-900 font-mono text-[10px] flex items-center justify-center font-bold shrink-0">
                  ?
                </span>
                <span>{dictionary.nav.howToUse}</span>
              </button>
            </div>
          </div>

          <div className="text-center max-w-2xl my-auto py-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 text-xs font-semibold mb-4 border border-slate-300 dark:border-slate-700">
              <span>{dictionary.upload.heroBadge}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
              {dictionary.upload.heroTitle}
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-2.5 max-w-xl mx-auto leading-relaxed">
              {dictionary.upload.heroDesc}
            </p>

            <div className="mt-6">
              <SpreadsheetUploader onUploadSuccess={handleUploadSuccess} />
            </div>
          </div>

          {/* Architectural Pillars */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3.5 w-full mt-4 text-xs text-slate-600 dark:text-slate-400">
            <div className="p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs">
              <div className="font-bold text-slate-900 dark:text-slate-100 mb-1">{dictionary.upload.pillars.aiTitle}</div>
              <p className="text-slate-500 dark:text-slate-400 text-[11px] leading-relaxed">
                {dictionary.upload.pillars.aiDesc}
              </p>
            </div>
            <div className="p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs">
              <div className="font-bold text-slate-900 dark:text-slate-100 mb-1">{dictionary.upload.pillars.engineTitle}</div>
              <p className="text-slate-500 dark:text-slate-400 text-[11px] leading-relaxed">
                {dictionary.upload.pillars.engineDesc}
              </p>
            </div>
            <div className="p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs">
              <div className="font-bold text-slate-900 dark:text-slate-100 mb-1">{dictionary.upload.pillars.lineageTitle}</div>
              <p className="text-slate-500 dark:text-slate-400 text-[11px] leading-relaxed">
                {dictionary.upload.pillars.lineageDesc}
              </p>
            </div>
            <div className="p-4 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs">
              <div className="font-bold text-slate-900 dark:text-slate-100 mb-1">{dictionary.upload.pillars.builderTitle}</div>
              <p className="text-slate-500 dark:text-slate-400 text-[11px] leading-relaxed">
                {dictionary.upload.pillars.builderDesc}
              </p>
            </div>
          </div>

          {/* Landing Footer */}
          <div className="pt-6 text-center text-[11px] text-slate-400 dark:text-slate-500 font-mono">
            {dictionary.upload.footerText}
          </div>
        </div>
      ) : (
        // Active Workspace Screen
        <div className="flex-1 flex flex-col">
          <WorkbookHeader overview={overview} onReset={handleReset} />

          <SheetList
            sheets={overview.sheets}
            activeSheetName={activeSheetName || overview.sheets[0]?.name || ''}
            onSelectSheet={(name) => setActiveSheetName(name)}
          />

          {/* View Mode Navigation Bar */}
          <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-2 flex items-center justify-between gap-3 overflow-x-auto transition-colors">
            <div className="flex items-center gap-1.5 shrink-0">
              <button
                type="button"
                onClick={() => setActiveViewMode('ai')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'ai'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.aiQuery}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('builder')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'builder'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.analysisBuilder}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('tables')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'tables'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.detectedTables} ({currentSheet?.tables.length ?? 0})
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('data')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'data'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.spreadsheetGrid} ({currentSheet?.total_rows ?? 0} {dictionary.common.rows})
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('visualize')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'visualize'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.visualizations}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('quality')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                  activeViewMode === 'quality'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <span>{dictionary.nav.dataQuality}</span>
                {currentSheet && (
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      activeViewMode === 'quality'
                        ? 'bg-slate-800 dark:bg-slate-200 text-white dark:text-slate-900'
                        : currentSheet.quality_report.overall_score >= 90
                        ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300'
                        : 'bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300'
                    }`}
                  >
                    {currentSheet.quality_report.overall_score}/100
                  </span>
                )}
              </button>
            </div>

            {currentSheet && (
              <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono shrink-0 hidden md:block">
                {dictionary.common.usedRange}: <span className="font-bold text-slate-700 dark:text-slate-300">{currentSheet.used_range}</span>
              </div>
            )}
          </div>

          {/* Main Content Area: Persist all components in DOM without unmounting */}
          <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
            {currentSheet ? (
              <div className="w-full">
                <div className={activeViewMode === 'ai' ? 'block' : 'hidden'}>
                  <AIQueryWorkspace
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                </div>

                <div className={activeViewMode === 'builder' ? 'block' : 'hidden'}>
                  <OperationBuilder
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                </div>

                <div className={activeViewMode === 'tables' ? 'block' : 'hidden'}>
                  <DetectedTablesViewer
                    tables={currentSheet.tables}
                    sheetName={currentSheet.name}
                  />
                </div>

                <div className={activeViewMode === 'data' ? 'block' : 'hidden'}>
                  <ActualDataViewer
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                  />
                </div>

                <div className={activeViewMode === 'visualize' ? 'block' : 'hidden'}>
                  <VisualizationViewer
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                </div>

                <div className={activeViewMode === 'quality' ? 'block' : 'hidden'}>
                  <DataQualityPanel
                    report={currentSheet.quality_report}
                    sheetName={currentSheet.name}
                  />
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 dark:text-slate-400 text-xs">
                {dictionary.nav.selectWorksheet}
              </div>
            )}
          </main>
        </div>
      )}

      {/* Global How to Use Modal */}
      <HowToUseModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />

      {/* First-Visit Language Onboarding Modal */}
      <LanguageOnboardingModal />
    </div>
  );
}
