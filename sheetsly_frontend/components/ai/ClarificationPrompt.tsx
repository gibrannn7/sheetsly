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
    <div className="bg-amber-50/70 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-lg p-4 space-y-3 text-xs shadow-2xs transition-colors">
      <div className="flex items-center space-x-2 border-b border-amber-200 dark:border-amber-800/80 pb-2">
        <span className="px-2 py-0.5 rounded bg-amber-200 dark:bg-amber-900 text-amber-900 dark:text-amber-100 font-bold text-[10px] uppercase tracking-wider">
          {dictionary.ai.clarification.title}
        </span>
        <span className="font-semibold text-amber-950 dark:text-amber-200">
          {dictionary.ai.clarification.badge}
        </span>
      </div>

      <div className="space-y-1">
        <p className="font-semibold text-slate-900 dark:text-slate-100 text-sm">{clarification.question}</p>
        <p className="text-slate-600 dark:text-slate-400 text-xs">{clarification.reason}</p>
      </div>

      {/* Selectable Options List */}
      {clarification.options.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
            {dictionary.ai.clarification.prompt}
          </span>
          <div className="flex flex-wrap gap-2">
            {clarification.options.map((opt) => (
              <button
                key={opt}
                type="button"
                disabled={isLoading}
                onClick={() => onSelectOption(clarification.target_parameter, opt)}
                className="px-3 py-1.5 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600 rounded-md text-xs font-semibold text-slate-800 dark:text-slate-200 shadow-2xs cursor-pointer transition-colors focus-visible:ring-2 focus-visible:ring-slate-900 dark:focus-visible:ring-slate-100 disabled:opacity-50"
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
