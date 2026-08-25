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
  const { dictionary } = useTranslation();
  const [showExplanation, setShowExplanation] = useState(false);

  const getSeverityBadge = (severity: IssueSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase bg-rose-100 text-rose-900 border border-rose-300">
            Critical
          </span>
        );
      case 'WARNING':
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-900 border border-amber-300">
            Warning
          </span>
        );
      case 'INFO':
        return (
          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase bg-blue-100 text-blue-900 border border-blue-300">
            Info
          </span>
        );
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-emerald-800 bg-emerald-50 border-emerald-300';
    if (score >= 75) return 'text-amber-800 bg-amber-50 border-amber-300';
    return 'text-rose-800 bg-rose-50 border-rose-300';
  };

  return (
    <>
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 bg-slate-50">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center space-x-2">
              <span>{dictionary.quality.hygieneScore}</span>
              <span className="text-slate-500 font-normal font-mono">({sheetName})</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">{report.summary}</p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={() => setShowExplanation(true)}
              className="text-[11px] font-semibold text-slate-600 hover:text-slate-900 underline cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400 rounded px-1"
            >
              {dictionary.quality.howAssessedButton}
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
            <div className="flex items-center space-x-3 p-3.5 bg-emerald-50 rounded-md border border-emerald-200 text-emerald-900 text-xs">
              <svg className="w-4 h-4 flex-shrink-0 text-emerald-700" fill="currentColor" viewBox="0 0 20 20">
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
                  className="p-3 rounded-md border border-slate-200 bg-slate-50 hover:bg-slate-100/70 transition-colors text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getSeverityBadge(issue.severity)}
                      <span className="font-mono text-[11px] font-semibold text-slate-800">
                        {issue.issue_type}
                      </span>
                      {issue.column_name && (
                        <span className="text-slate-500">
                          in <strong className="text-slate-800">{issue.column_name}</strong>
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] font-mono text-slate-500">
                      {issue.affected_cells_count} {dictionary.quality.affectedCells}
                    </span>
                  </div>

                  <p className="text-slate-700 leading-relaxed">{issue.message}</p>

                  {issue.sample_locations && issue.sample_locations.length > 0 && (
                    <div className="flex items-center space-x-2 pt-1">
                      <span className="text-[10px] uppercase font-bold text-slate-400">{dictionary.quality.sampleLocations}:</span>
                      <div className="flex flex-wrap gap-1">
                        {issue.sample_locations.map((loc, lIdx) => (
                          <span
                            key={lIdx}
                            className="font-mono text-[10px] bg-white border border-slate-200 px-1 py-0.2 rounded text-slate-700 font-semibold"
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
