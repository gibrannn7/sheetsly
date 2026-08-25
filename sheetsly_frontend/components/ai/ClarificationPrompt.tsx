'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';
import { ClarificationRequest } from '../../lib/types';

interface ClarificationPromptProps {
  clarification: ClarificationRequest;
  onSelectOption: (paramName: string, selectedValue: string) => void;
  isLoading?: boolean;
}

export const ClarificationPrompt: React.FC<ClarificationPromptProps> = ({
  clarification,
  onSelectOption,
  isLoading,
}) => {
  const { dictionary } = useTranslation();

  return (
    <div className="bg-amber-50/70 border border-amber-300 rounded-lg p-4 space-y-3 text-xs shadow-2xs">
      <div className="flex items-center space-x-2 border-b border-amber-200 pb-2">
        <span className="px-2 py-0.5 rounded bg-amber-200 text-amber-900 font-bold text-[10px] uppercase tracking-wider">
          {dictionary.ai.clarification.title}
        </span>
        <span className="font-semibold text-amber-950">
          {dictionary.ai.clarification.badge}
        </span>
      </div>

      <div className="space-y-1">
        <p className="font-semibold text-slate-900 text-sm">{clarification.question}</p>
        <p className="text-slate-600 text-xs">{clarification.reason}</p>
      </div>

      {/* Selectable Options List */}
      {clarification.options.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
            {dictionary.ai.clarification.prompt}
          </span>
          <div className="flex flex-wrap gap-2">
            {clarification.options.map((opt) => (
              <button
                key={opt}
                type="button"
                disabled={isLoading}
                onClick={() => onSelectOption(clarification.target_parameter, opt)}
                className="px-3 py-1.5 bg-white hover:bg-slate-50 border border-slate-300 hover:border-slate-400 rounded-md text-xs font-semibold text-slate-800 shadow-2xs cursor-pointer transition-colors focus-visible:ring-2 focus-visible:ring-slate-900 disabled:opacity-50"
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
