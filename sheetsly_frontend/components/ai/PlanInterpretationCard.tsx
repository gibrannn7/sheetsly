'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';
import { AnalyticalInstruction } from '../../lib/types';

interface PlanInterpretationCardProps {
  instruction: AnalyticalInstruction;
  intentSummary?: string;
}

export const PlanInterpretationCard: React.FC<PlanInterpretationCardProps> = ({
  instruction,
  intentSummary,
}) => {
  const { dictionary } = useTranslation();

  return (
    <div className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg p-3.5 space-y-2.5 text-xs transition-colors">
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
        <div className="flex items-center space-x-2">
          <span className="px-2 py-0.5 rounded bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-mono text-[10px] font-bold">
            {instruction.operation}
          </span>
          <span className="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide text-[11px]">
            {dictionary.ai.planCard.title}
          </span>
        </div>
        <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
          Target: {instruction.sheet_name} / {instruction.table_id || 'Primary Table'}
        </span>
      </div>

      {intentSummary && (
        <p className="text-slate-700 dark:text-slate-300 font-medium leading-snug">
          {intentSummary}
        </p>
      )}

      {/* Breakdown of planned parameters */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1 text-[11px]">
        <div>
          <span className="text-slate-400 dark:text-slate-500 block uppercase font-bold text-[10px]">{dictionary.ai.planCard.targetColumn}</span>
          <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
            {instruction.target_column || '(Entire Selection)'}
          </span>
        </div>

        {instruction.group_by_columns && instruction.group_by_columns.length > 0 && (
          <div>
            <span className="text-slate-400 dark:text-slate-500 block uppercase font-bold text-[10px]">{dictionary.ai.planCard.groupBy}</span>
            <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
              {instruction.group_by_columns.join(', ')}
            </span>
          </div>
        )}

        <div>
          <span className="text-slate-400 dark:text-slate-500 block uppercase font-bold text-[10px]">{dictionary.ai.planCard.filters}</span>
          <span className="font-mono text-slate-700 dark:text-slate-300">
            {instruction.filters && instruction.filters.length > 0
              ? `${instruction.filters.length} rules (${instruction.filter_combination || 'AND'})`
              : dictionary.common.none}
          </span>
        </div>

        <div>
          <span className="text-slate-400 dark:text-slate-500 block uppercase font-bold text-[10px]">{dictionary.ai.planCard.sort} / {dictionary.ai.planCard.limit}</span>
          <span className="font-mono text-slate-700 dark:text-slate-300">
            {instruction.sort
              ? `${instruction.sort.column} (${instruction.sort.ascending ? 'ASC' : 'DESC'})`
              : dictionary.builder.naturalOrder}
            {instruction.limit ? ` [Limit ${instruction.limit}]` : ''}
          </span>
        </div>
      </div>
    </div>
  );
};
