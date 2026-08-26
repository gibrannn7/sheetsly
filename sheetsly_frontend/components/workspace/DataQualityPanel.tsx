'use client';

import React, { useState } from 'react';
import { useTranslation } from '../../lib/i18n';
import { DataQualityReport, IssueSeverity } from '../../lib/types';
import { DataQualityExplanationModal } from './DataQualityExplanationModal';

interface DataQualityPanelProps {
  report: DataQualityReport;
  sheetName: string;
}

export const DataQualityPanel: React.FC<DataQualityPanelProps> = ({ report, sheetName }) => {
  const { dictionary, t } = useTranslation();
  const [showExplanation, setShowExplanation] = useState(false);

  const getSeverityBadge = (severity: IssueSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase bg-rose-100 dark:bg-rose-950/60 text-rose-900 dark:text-rose-200 border border-rose-300 dark:border-rose-800">
            {dictionary.quality.critical}
          </span>
        );
      case 'WARNING':
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase bg-amber-100 dark:bg-amber-950/60 text-amber-900 dark:text-amber-200 border border-amber-300 dark:border-amber-800">
            {dictionary.quality.warning}
          </span>
        );
      case 'INFO':
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase bg-blue-100 dark:bg-blue-950/60 text-blue-900 dark:text-blue-200 border border-blue-300 dark:border-blue-800">
            {dictionary.quality.info}
          </span>
        );
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/50 border-emerald-300 dark:border-emerald-800';
    if (score >= 75) return 'text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/50 border-amber-300 dark:border-amber-800';
    return 'text-rose-800 dark:text-rose-300 bg-rose-50 dark:bg-rose-950/50 border-rose-300 dark:border-rose-800';
  };

  const summaryText =
    report.issues.length === 0
      ? t('quality.qualityScorePassed', { score: report.overall_score })
      : t('quality.qualityScoreIssues', { score: report.overall_score, count: report.issues.length });

  return (
    <>
      <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs overflow-hidden transition-colors">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-50 dark:bg-slate-950 transition-colors">
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide flex items-center space-x-2">
              <span>{dictionary.quality.hygieneScore}</span>
              <span className="text-slate-500 dark:text-slate-400 font-normal font-mono">({sheetName})</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{summaryText}</p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={() => setShowExplanation(true)}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md hover:bg-slate-50 dark:hover:bg-slate-750 transition-colors shadow-2xs cursor-pointer"
            >
              <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{dictionary.quality.howAssessedButton}</span>
            </button>

            <div
              className={`flex items-center space-x-2 px-2.5 py-1 rounded border font-semibold text-xs ${getScoreColor(
                report.overall_score
              )}`}
            >
              <span>{dictionary.common.hygiene}:</span>
              <span className="font-bold">{report.overall_score} / 100</span>
            </div>
          </div>
        </div>

        {/* Issues list */}
        <div className="p-4">
          {report.issues.length === 0 ? (
            <div className="flex items-center space-x-3 p-3.5 bg-emerald-50 dark:bg-emerald-950/40 rounded-md border border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 text-xs">
              <svg className="w-4 h-4 flex-shrink-0 text-emerald-700 dark:text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <p className="font-semibold">{dictionary.quality.noIssues}</p>
              </div>
            </div>
          ) : (
            <div className="space-y-2.5">
              {report.issues.map((issue, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-md border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 hover:bg-slate-100/70 dark:hover:bg-slate-800/70 transition-colors text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getSeverityBadge(issue.severity)}
                      <span className="font-mono text-[11px] font-semibold text-slate-800 dark:text-slate-200">
                        {issue.issue_type}
                      </span>
                      {issue.column_name && (
                        <span className="text-slate-500 dark:text-slate-400">
                          {t('quality.inColumn', { col: issue.column_name })}
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                      {issue.affected_cells_count} {dictionary.quality.affectedCells}
                    </span>
                  </div>

                  <p className="text-slate-700 dark:text-slate-300 leading-relaxed">{issue.message}</p>

                  {issue.sample_locations && issue.sample_locations.length > 0 && (
                    <div className="flex items-center space-x-2 pt-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500">{dictionary.quality.sampleLocations}:</span>
                      <div className="flex flex-wrap gap-1">
                        {issue.sample_locations.map((loc, lIdx) => (
                          <span
                            key={lIdx}
                            className="font-mono text-[10px] bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-1 py-0.2 rounded text-slate-700 dark:text-slate-300 font-semibold"
                          >
                            {loc}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <DataQualityExplanationModal
        isOpen={showExplanation}
        onClose={() => setShowExplanation(false)}
      />
    </>
  );
};
