'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';
import { EvidenceExplanation } from '../../lib/types';

interface EvidenceExplanationCardProps {
  explanation: EvidenceExplanation;
}

export const EvidenceExplanationCard: React.FC<EvidenceExplanationCardProps> = ({
  explanation,
}) => {
  const { dictionary } = useTranslation();

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden text-xs">
      <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="font-bold text-slate-800 uppercase tracking-wide text-[11px]">
            {dictionary.ai.evidenceCard.title}
          </span>
        </div>
        <span className="text-slate-500 font-mono text-[11px]">
          Source: {explanation.source_evidence}
        </span>
      </div>

      <div className="p-4 space-y-3">
        {/* Core Factual Narrative */}
        <div className="p-3 bg-slate-50 rounded-md border border-slate-200 space-y-1">
          <p className="font-semibold text-slate-900 leading-relaxed text-sm">
            {explanation.summary}
          </p>
          <p className="text-slate-700 leading-relaxed">
            {explanation.factual_statement}
          </p>
        </div>

        {/* Numbered Calculation Steps */}
        {explanation.calculation_steps.length > 0 && (
          <div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
              {dictionary.ai.evidenceCard.verifiedSteps}:
            </span>
            <ol className="space-y-1 bg-slate-50 p-3 rounded-md border border-slate-200 font-mono text-[11px] text-slate-700">
              {explanation.calculation_steps.map((step, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-slate-400 font-bold select-none">{idx + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Hygiene / Coverage Warnings */}
        {explanation.warnings && explanation.warnings.length > 0 && (
          <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-md text-amber-900 text-[11px] space-y-0.5">
            <span className="font-bold uppercase text-[10px]">Data Coverage Caveat:</span>
            {explanation.warnings.map((w, idx) => (
              <p key={idx}>{w}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
