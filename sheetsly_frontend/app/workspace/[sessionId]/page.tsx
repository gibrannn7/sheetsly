'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '../../../lib/api';
import { useWorkspace } from '../../../lib/workspace/WorkspaceContext';
import { WorkbookHeader } from '../../../components/workspace/WorkbookHeader';
import { SheetList } from '../../../components/workspace/SheetList';
import { DetectedTablesViewer } from '../../../components/workspace/DetectedTablesViewer';
import { ActualDataViewer } from '../../../components/workspace/ActualDataViewer';
import { DataQualityPanel } from '../../../components/workspace/DataQualityPanel';
import { VisualizationViewer } from '../../../components/workspace/VisualizationViewer';
import { OperationBuilder } from '../../../components/builder/OperationBuilder';
import { AIQueryWorkspace } from '../../../components/ai/AIQueryWorkspace';
import { LanguageOnboardingModal } from '../../../components/workspace/LanguageOnboardingModal';
import { useTranslation } from '../../../lib/i18n';

export default function WorkspaceSessionPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = Array.isArray(params.sessionId) ? params.sessionId[0] : params.sessionId;
  const { dictionary } = useTranslation();

  const {
    overview,
    activeSheetName,
    activeViewMode,
    setOverview,
    setActiveSheetName,
    setActiveViewMode,
    resetWorkspace,
  } = useWorkspace();

  const [loading, setLoading] = useState(!overview || overview.dataset_id !== sessionId);
  const [loadError, setLoadError] = useState<string | null>(null);
  const isNavigatingAway = React.useRef(false);

  useEffect(() => {
    if (!sessionId || isNavigatingAway.current) return;

    if (!overview || overview.dataset_id !== sessionId) {
      setLoading(true);
      setLoadError(null);
      api
        .getDatasetOverview(sessionId)
        .then((data) => {
          if (isNavigatingAway.current) return;
          setOverview(data);
          if (data.sheets.length > 0 && !activeSheetName) {
            setActiveSheetName(data.sheets[0].name);
          }
          setLoading(false);
        })
        .catch((err) => {
          if (isNavigatingAway.current) return;
          console.error('Failed to restore workspace session', err);
          setLoadError(err.message || 'Workspace session not found or expired.');
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [sessionId, overview, setOverview, activeSheetName, setActiveSheetName]);

  const handleReset = () => {
    isNavigatingAway.current = true;
    resetWorkspace();
    router.push('/');
  };

  const currentSheet = overview?.sheets.find((s) => s.name === activeSheetName) || overview?.sheets[0];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col items-center justify-center p-6 space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-slate-300 dark:border-slate-700 border-t-slate-900 dark:border-t-slate-100 animate-spin" />
        <p className="text-xs font-semibold text-slate-700 dark:text-slate-300 font-mono">
          {dictionary.common.loading || 'Loading workspace session...'}
        </p>
      </div>
    );
  }

  if (loadError || !overview) {
    return (
      <div className="min-h-screen bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col items-center justify-center p-6 space-y-4">
        <div className="p-6 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-lg max-w-md w-full text-center space-y-3 shadow-sm">
          <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">Session Unavailable</h2>
          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            {loadError || 'The requested analytical workspace session could not be retrieved.'}
          </p>
          <div className="pt-2">
            <button
              type="button"
              onClick={() => router.push('/')}
              className="px-4 py-1.5 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs font-semibold rounded-md hover:bg-slate-800 dark:hover:bg-white transition-colors cursor-pointer"
            >
              Upload Workbook
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors">
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

      {/* Main Analytical Content Workspace */}
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

      <LanguageOnboardingModal />
    </div>
  );
}
