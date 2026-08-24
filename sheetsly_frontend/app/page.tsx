'use client';

import React, { useState } from 'react';
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
import { WorkbookOverview } from '../lib/types';

export default function Home() {
  const [overview, setOverview] = useState<WorkbookOverview | null>(null);
  const [activeSheetName, setActiveSheetName] = useState<string>('');
  const [activeViewMode, setActiveViewMode] = useState<'ai' | 'builder' | 'tables' | 'data' | 'visualize' | 'quality'>('ai');
  const [isHelpOpen, setIsHelpOpen] = useState<boolean>(false);

  const handleUploadSuccess = (data: WorkbookOverview) => {
    setOverview(data);
    if (data.sheets.length > 0) {
      setActiveSheetName(data.sheets[0].name);
    }
  };

  const handleReset = () => {
    setOverview(null);
    setActiveSheetName('');
  };

  const currentSheet = overview?.sheets.find((s) => s.name === activeSheetName);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans">
      {!overview ? (
        // Landing / Upload Screen
        <div className="flex-1 flex flex-col justify-between items-center px-4 py-8 max-w-5xl mx-auto w-full">
          {/* Top Bar on Landing Page */}
          <div className="w-full flex items-center justify-between pb-6">
            <div className="flex items-center space-x-2.5">
              <div className="w-8 h-8 rounded-md bg-slate-900 flex items-center justify-center text-white font-bold text-sm font-mono">
                S
              </div>
              <div>
                <span className="text-sm font-bold text-slate-900 leading-none block">Sheetsly</span>
                <span className="text-[10px] text-slate-500 font-medium">Spreadsheet Intelligence Workspace</span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setIsHelpOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-md transition-colors shadow-2xs cursor-pointer focus-visible:ring-2 focus-visible:ring-slate-900"
            >
              <span className="w-3.5 h-3.5 rounded-full bg-slate-800 text-white font-mono text-[10px] flex items-center justify-center font-bold">
                ?
              </span>
              <span>How to Use & Architecture</span>
            </button>
          </div>

          <div className="text-center max-w-2xl my-auto py-6">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-md bg-slate-200 text-slate-800 text-xs font-semibold mb-4 border border-slate-300">
              <span>Deterministic Spreadsheet Intelligence Platform</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Turn your spreadsheet into verified insight.
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-2.5 max-w-xl mx-auto leading-relaxed">
              Upload any spreadsheet to explore detected tables, build calculations without formulas, or ask plain-language questions with Qwen. Every result is computed deterministically in Python with cell-level lineage.
            </p>

            <div className="mt-6">
              <SpreadsheetUploader onUploadSuccess={handleUploadSuccess} />
            </div>
          </div>

          {/* Architectural Pillars */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3.5 w-full mt-4 text-xs text-slate-600">
            <div className="p-4 bg-white rounded-lg border border-slate-200 shadow-2xs">
              <div className="font-bold text-slate-900 mb-1">AI Query Planner</div>
              <p className="text-slate-500 text-[11px] leading-relaxed">
                Qwen translates natural-language intent into structured instructions with proactive ambiguity detection.
              </p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-slate-200 shadow-2xs">
              <div className="font-bold text-slate-900 mb-1">Deterministic Engine</div>
              <p className="text-slate-500 text-[11px] leading-relaxed">
                Python calculates numerical truth. No hallucinations, guessing, or estimated arithmetic.
              </p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-slate-200 shadow-2xs">
              <div className="font-bold text-slate-900 mb-1">Cell-Level Lineage</div>
              <p className="text-slate-500 text-[11px] leading-relaxed">
                Complete audit trail with exact source coordinate ranges (e.g. <code className="font-mono text-slate-700">Sheet1!E2:E128</code>).
              </p>
            </div>
            <div className="p-4 bg-white rounded-lg border border-slate-200 shadow-2xs">
              <div className="font-bold text-slate-900 mb-1">Operation Builder</div>
              <p className="text-slate-500 text-[11px] leading-relaxed">
                Point-and-click analytical interface for aggregations, multi-grouping, sorting, and filters.
              </p>
            </div>
          </div>

          {/* Landing Footer */}
          <div className="pt-6 text-center text-[11px] text-slate-400 font-mono">
            Sheetsly v1.0 &bull; Developed with Python FastAPI &amp; Next.js 16
          </div>
        </div>
      ) : (
        // Active Workspace Screen
        <div className="flex-1 flex flex-col">
          <WorkbookHeader overview={overview} onReset={handleReset} />

          <SheetList
            sheets={overview.sheets}
            activeSheetName={activeSheetName}
            onSelectSheet={(name) => setActiveSheetName(name)}
          />

          {/* View Mode Navigation Bar */}
          <div className="bg-white border-b border-slate-200 px-6 py-2.5 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setActiveViewMode('ai')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeViewMode === 'ai'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                AI Query Planner
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('builder')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeViewMode === 'builder'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Analysis Builder
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('tables')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeViewMode === 'tables'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Detected Tables & Schema ({currentSheet?.tables.length ?? 0})
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('data')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeViewMode === 'data'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Actual Spreadsheet Grid ({currentSheet?.total_rows ?? 0} rows)
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('visualize')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                  activeViewMode === 'visualize'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                Visualizations
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('quality')}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                  activeViewMode === 'quality'
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <span>Data Quality</span>
                {currentSheet && (
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      activeViewMode === 'quality'
                        ? 'bg-slate-800 text-white'
                        : currentSheet.quality_report.overall_score >= 90
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}
                  >
                    {currentSheet.quality_report.overall_score}/100
                  </span>
                )}
              </button>
            </div>

            {currentSheet && (
              <div className="text-xs text-slate-500 font-mono">
                Used Range: <span className="font-bold text-slate-700">{currentSheet.used_range}</span>
              </div>
            )}
          </div>

          {/* Main Content Area */}
          <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
            {currentSheet ? (
              <>
                {activeViewMode === 'ai' && (
                  <AIQueryWorkspace
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                )}

                {activeViewMode === 'builder' && (
                  <OperationBuilder
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                )}

                {activeViewMode === 'tables' && (
                  <DetectedTablesViewer
                    tables={currentSheet.tables}
                    sheetName={currentSheet.name}
                  />
                )}

                {activeViewMode === 'data' && (
                  <ActualDataViewer
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                  />
                )}

                {activeViewMode === 'visualize' && (
                  <VisualizationViewer
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                )}

                {activeViewMode === 'quality' && (
                  <DataQualityPanel
                    report={currentSheet.quality_report}
                    sheetName={currentSheet.name}
                  />
                )}
              </>
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs">Please select a worksheet.</div>
            )}
          </main>
        </div>
      )}

      {/* Global How to Use Modal */}
      <HowToUseModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />
    </div>
  );
}
