'use client';

import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import {
  AIStatusResponse,
  NaturalLanguageQueryResponse,
  TableRegion,
  TimingBreakdown,
} from '../../lib/types';
import { useWorkspace } from '../../lib/workspace/WorkspaceContext';
import { AnalysisResultView } from '../builder/AnalysisResultView';
import { AIModelSelector } from './AIModelSelector';
import { ClarificationPrompt } from './ClarificationPrompt';
import { EvidenceExplanationCard } from './EvidenceExplanationCard';
import { HowDoesThisWorkModal } from './HowDoesThisWorkModal';
import { PlanInterpretationCard } from './PlanInterpretationCard';

interface AIQueryWorkspaceProps {
  datasetId: string;
  sheetName: string;
  tables: TableRegion[];
}

export const AIQueryWorkspace: React.FC<AIQueryWorkspaceProps> = ({
  datasetId,
  sheetName,
  tables,
}) => {
  const { dictionary, t } = useTranslation();
  const { aiState, updateAIState, addAIHistoryItem } = useWorkspace();

  const query = aiState.query;
  const lastResponse = aiState.lastResponse;
  const selectedModel = aiState.selectedModel;
  const suggestedQueries = aiState.suggestedQueries;

  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>('');
  const [aiStatus, setAiStatus] = useState<AIStatusResponse | null>(null);
  const [showHowItWorksModal, setShowHowItWorksModal] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleModelChange = (newModelId: string) => {
    updateAIState({ selectedModel: newModelId });
  };

  // Fetch AI Status & Suggested Queries on sheet change
  useEffect(() => {
    let isMounted = true;
    api
      .getAIStatus()
      .then((status) => {
        if (isMounted) setAiStatus(status);
      })
      .catch(() => {});

    if (suggestedQueries.length === 0) {
      api
        .getSuggestedQueries(datasetId, sheetName)
        .then((res) => {
          if (isMounted) updateAIState({ suggestedQueries: res.suggested_queries || [] });
        })
        .catch(() => {});
    }

    return () => {
      isMounted = false;
    };
  }, [datasetId, sheetName, suggestedQueries.length]);

  const handleExecuteQuery = async (
    customQuery?: string,
    clarificationSelection?: Record<string, string>
  ) => {
    const q = (customQuery || query).trim();
    if (!q) return;

    setLoading(true);
    setError(null);

    try {
      // Stage 1: Network call to AI Planner
      setCurrentStage(dictionary.ai.stagePlanning);
      const planRes = await api.planQueryWithAI({
        query: q,
        dataset_id: datasetId,
        sheet_name: sheetName,
        model: selectedModel,
        clarification_selection: clarificationSelection || null,
      });

      // Handle early exit outcomes (Clarification, Rejection, Unsupported, Provider Error)
      if (planRes.status !== 'EXECUTION_READY' || !planRes.planned_instruction) {
        const partialResponse: NaturalLanguageQueryResponse = {
          status: planRes.status,
          user_query: planRes.user_query,
          intent_summary: planRes.intent_summary,
          model_used: planRes.model_used || selectedModel,
          planned_instruction: planRes.planned_instruction,
          clarification: planRes.clarification,
          error_message: planRes.error_message,
          timing: planRes.timing,
        };
        addAIHistoryItem(q, partialResponse);
        if (customQuery) updateAIState({ query: customQuery });
        return;
      }

      // Stage 2: Execution of deterministic engine & visualization
      setCurrentStage(dictionary.ai.stageExecuting);
      const fullRes = await api.queryWithAI({
        query: q,
        dataset_id: datasetId,
        sheet_name: sheetName,
        model: selectedModel,
        preplanned_instruction: planRes.planned_instruction,
        generate_visualization: true,
      });

      // Merge planner timing with execution timing
      const mergedTiming: TimingBreakdown = {
        schema_resolution_ms: planRes.timing?.schema_resolution_ms || fullRes.timing?.schema_resolution_ms || 0,
        qwen_planning_ms: planRes.timing?.qwen_planning_ms || 0,
        guardrail_validation_ms: fullRes.timing?.guardrail_validation_ms || 0,
        deterministic_execution_ms: fullRes.timing?.deterministic_execution_ms || 0,
        visualization_ms: fullRes.timing?.visualization_ms || 0,
        evidence_explanation_ms: fullRes.timing?.evidence_explanation_ms || 0,
        total_duration_ms: roundTo2(
          (planRes.timing?.total_duration_ms || 0) + (fullRes.timing?.total_duration_ms || 0)
        ),
      };

      const finalResponse: NaturalLanguageQueryResponse = {
        ...fullRes,
        model_used: fullRes.model_used || selectedModel,
        timing: mergedTiming,
      };

      addAIHistoryItem(q, finalResponse);
      if (customQuery) updateAIState({ query: customQuery });
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'An unexpected error occurred during query processing.');
      }
      updateAIState({ lastResponse: null });
    } finally {
      setLoading(false);
      setCurrentStage('');
    }
  };

  const handleClarificationSelection = (paramName: string, selectedValue: string) => {
    const selection = { [paramName]: selectedValue };
    handleExecuteQuery(lastResponse?.user_query || query, selection);
  };

  return (
    <>
      <div className="space-y-5">
        {/* 1. Header & AI Model Selector / Provider Status */}
        <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs p-4 space-y-3.5 transition-colors">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
            <div>
              <h2 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
                {dictionary.ai.title}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {dictionary.ai.desc}
              </p>
            </div>

            <div className="flex items-center space-x-2.5">
              <button
                type="button"
                onClick={() => setShowHowItWorksModal(true)}
                className="inline-flex items-center gap-1 px-2 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded-md text-[11px] font-medium cursor-pointer transition-colors shadow-2xs focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400"
              >
                <span className="font-mono text-[10px] w-3.5 h-3.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold">
                  ?
                </span>
                <span>{dictionary.ai.howDoesThisWork}</span>
              </button>

              {aiStatus?.configured ? (
                <AIModelSelector
                  value={selectedModel}
                  onChange={handleModelChange}
                  availableModels={aiStatus.available_models}
                  disabled={loading}
                />
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                  {dictionary.ai.fallbackMode}
                </span>
              )}
            </div>
          </div>

          {/* Query Input Bar */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleExecuteQuery();
            }}
            className="space-y-2.5"
          >
            <div className="relative flex items-center">
              <input
                type="text"
                value={query}
                onChange={(e) => updateAIState({ query: e.target.value })}
                placeholder={dictionary.ai.placeholder}
                disabled={loading}
                className="w-full pl-3.5 pr-32 py-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md text-xs text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-100 focus:border-slate-900 dark:focus:border-slate-100 font-sans disabled:opacity-50 transition-colors"
              />
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="absolute right-1 px-3.5 py-1.5 bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-900 rounded text-xs font-semibold shadow-2xs disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed transition-colors"
              >
                {loading ? dictionary.ai.processing : dictionary.ai.runQuery}
              </button>
            </div>

            {/* Truthful Stage Indicator (during live execution) */}
            {loading && currentStage && (
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded text-xs text-slate-700 dark:text-slate-300 font-sans">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-700 dark:bg-slate-300 animate-pulse" />
                <span className="font-medium">{currentStage}</span>
              </div>
            )}

            {/* Schema-Derived Suggestions */}
            {!loading && suggestedQueries.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider select-none">
                  {dictionary.ai.suggestions}
                </span>
                {suggestedQueries.map((sq, idx) => (
                  <button
                    key={idx}
                    type="button"
                    disabled={loading}
                    onClick={() => handleExecuteQuery(sq)}
                    className="px-2.5 py-0.5 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded text-[11px] transition-colors cursor-pointer disabled:opacity-40 text-left font-medium"
                  >
                    {sq}
                  </button>
                ))}
              </div>
            )}
          </form>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="p-3.5 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 rounded-md text-xs text-rose-800 dark:text-rose-300 space-y-1">
            <div className="font-bold">{dictionary.common.error}</div>
            <p>{error}</p>
          </div>
        )}

        {/* 2. Structured AI Pipeline Presentation */}
        {lastResponse ? (
          <div className="space-y-4">
            {/* A. Clarification Prompt (when query is ambiguous) */}
            {lastResponse.status === 'CLARIFICATION_REQUIRED' && lastResponse.clarification && (
              <ClarificationPrompt
                clarification={lastResponse.clarification}
                onSelectOption={handleClarificationSelection}
                isLoading={loading}
              />
            )}

            {/* B. Validation Rejection (Guardrail caught an invalid operation) */}
            {lastResponse.status === 'VALIDATION_FAILED' && (
              <div className="p-4 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 rounded-md text-xs text-rose-900 dark:text-rose-200 space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="px-1.5 py-0.2 rounded bg-rose-200 dark:bg-rose-900 text-rose-900 dark:text-rose-100 font-bold text-[10px] uppercase">
                    {dictionary.ai.guardrailBlocked}
                  </span>
                  <span className="font-bold">{dictionary.ai.schemaViolation}</span>
                </div>
                <p>{lastResponse.error_message}</p>
                {lastResponse.planned_instruction && (
                  <div className="pt-2">
                    <span className="text-[10px] font-bold uppercase text-rose-700 dark:text-rose-400 block mb-1">
                      {dictionary.ai.rejectedPlan}
                    </span>
                    <PlanInterpretationCard
                      instruction={lastResponse.planned_instruction}
                      intentSummary={lastResponse.intent_summary}
                    />
                  </div>
                )}
              </div>
            )}

            {/* C. Unsupported Query */}
            {lastResponse.status === 'UNSUPPORTED_QUERY' && (
              <div className="p-4 bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800 rounded-md text-xs text-amber-900 dark:text-amber-200 space-y-1">
                <div className="font-bold">{dictionary.ai.unsupported}</div>
                <p>{lastResponse.error_message || dictionary.ai.unsupportedDefault}</p>
              </div>
            )}

            {/* D. Provider Error */}
            {lastResponse.status === 'PROVIDER_ERROR' && (
              <div className="p-4 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md text-xs text-slate-800 dark:text-slate-200 space-y-1.5">
                <div className="font-bold text-slate-900 dark:text-slate-100">{dictionary.ai.providerUnavailable}</div>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  {lastResponse.error_message &&
                  (lastResponse.error_message.includes('not configured') ||
                    lastResponse.error_message.includes('not set') ||
                    lastResponse.error_message.includes('unconfigured'))
                    ? dictionary.ai.providerUnconfiguredDesc
                    : dictionary.ai.providerOfflineDesc}
                </p>
              </div>
            )}

            {/* D2. Calculation Engine Execution Error */}
            {lastResponse.status === 'EXECUTION_ERROR' && (
              <div className="p-4 bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 rounded-md text-xs text-rose-900 dark:text-rose-200 space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="px-1.5 py-0.5 rounded bg-rose-200 dark:bg-rose-900 text-rose-900 dark:text-rose-100 font-bold text-[10px] uppercase">
                    {dictionary.common.error}
                  </span>
                  <span className="font-bold">{dictionary.ai.executionErrorTitle}</span>
                </div>
                <p className="leading-relaxed">
                  {lastResponse.error_message || dictionary.ai.executionErrorDesc}
                </p>
                {lastResponse.planned_instruction && (
                  <div className="pt-2">
                    <span className="text-[10px] font-bold uppercase text-rose-700 dark:text-rose-400 block mb-1">
                      {dictionary.ai.rejectedPlan}
                    </span>
                    <PlanInterpretationCard
                      instruction={lastResponse.planned_instruction}
                      intentSummary={lastResponse.intent_summary}
                    />
                  </div>
                )}
              </div>
            )}

            {/* E. Successful Deterministic Execution */}
            {lastResponse.status === 'EXECUTION_READY' && (
              <div className="space-y-4">
                {/* 1. Plan Inspection Card */}
                {lastResponse.planned_instruction && (
                  <PlanInterpretationCard
                    instruction={lastResponse.planned_instruction}
                    intentSummary={lastResponse.intent_summary}
                  />
                )}

                {/* 2. Evidence Explanation Card */}
                {lastResponse.explanation && (
                  <EvidenceExplanationCard explanation={lastResponse.explanation} />
                )}

                {/* 3. Stage Latency Breakdown Badge */}
                {lastResponse.timing && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs space-y-2 transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                        {dictionary.ai.stageLatency}
                      </span>
                      <span className="font-mono text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                        {t('ai.total', { duration: formatSeconds(lastResponse.timing.total_duration_ms) })}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 pt-1 font-mono text-[11px]">
                      <div className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                        <div className="text-[10px] font-sans text-slate-400 dark:text-slate-500 uppercase">{dictionary.ai.schemaStage}</div>
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{lastResponse.timing.schema_resolution_ms}ms</div>
                      </div>
                      <div className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                        <div className="text-[10px] font-sans text-slate-400 dark:text-slate-500 uppercase">{dictionary.ai.qwenPlanStage}</div>
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{formatSeconds(lastResponse.timing.qwen_planning_ms)}</div>
                      </div>
                      <div className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                        <div className="text-[10px] font-sans text-slate-400 dark:text-slate-500 uppercase">{dictionary.ai.guardrailStage}</div>
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{lastResponse.timing.guardrail_validation_ms}ms</div>
                      </div>
                      <div className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                        <div className="text-[10px] font-sans text-slate-400 dark:text-slate-500 uppercase">{dictionary.ai.pythonCalcStage}</div>
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{lastResponse.timing.deterministic_execution_ms}ms</div>
                      </div>
                      <div className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                        <div className="text-[10px] font-sans text-slate-400 dark:text-slate-500 uppercase">{dictionary.ai.visualizerStage}</div>
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{lastResponse.timing.visualization_ms}ms</div>
                      </div>
                      <div className="bg-white dark:bg-slate-950 p-2 rounded border border-slate-200 dark:border-slate-800">
                        <div className="text-[10px] font-sans text-slate-400 dark:text-slate-500 uppercase">{dictionary.ai.explainerStage}</div>
                        <div className="font-semibold text-slate-800 dark:text-slate-200">{formatSeconds(lastResponse.timing.evidence_explanation_ms)}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 4. Verified Result View (Single or Multi-Analysis Report) */}
                {lastResponse.sub_analyses && lastResponse.sub_analyses.length > 0 ? (
                  <div className="space-y-6 pt-2">
                    <div className="px-3 py-2 bg-slate-100 dark:bg-slate-800 rounded-md text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center justify-between">
                      <span>Laporan Analisis Menyeluruh ({lastResponse.sub_analyses.length} Modul Analisis Terverifikasi)</span>
                    </div>
                    {lastResponse.sub_analyses.map((sub, idx) => (
                      <div key={idx} className="p-4 border border-slate-200 dark:border-slate-800 rounded-lg bg-white dark:bg-slate-900 space-y-3 shadow-2xs">
                        <div className="flex items-center space-x-2 text-xs font-bold text-slate-900 dark:text-slate-100 pb-2 border-b border-slate-100 dark:border-slate-800">
                          <span className="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 font-mono text-[11px]">{idx + 1}</span>
                          <span>{sub.intent_summary}</span>
                        </div>
                        {sub.explanation && (
                          <EvidenceExplanationCard explanation={sub.explanation} />
                        )}
                        {sub.analytical_result && (
                          <AnalysisResultView datasetId={datasetId} result={sub.analytical_result} />
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  lastResponse.analytical_result && (
                    <AnalysisResultView
                      datasetId={datasetId}
                      result={lastResponse.analytical_result}
                    />
                  )
                )}

                {/* 5. Suggested Follow-Up Queries */}
                {lastResponse.suggested_next_queries && lastResponse.suggested_next_queries.length > 0 && (
                  <div className="p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg text-xs space-y-2 transition-colors">
                    <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                      {dictionary.ai.suggestedNext}
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {lastResponse.suggested_next_queries.map((nq, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleExecuteQuery(nq)}
                          className="px-2.5 py-1 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded text-xs font-medium cursor-pointer transition-colors shadow-2xs text-left"
                        >
                          {nq}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          /* Empty State before any query is run */
          <div className="bg-white dark:bg-slate-900 rounded-lg border border-dashed border-slate-300 dark:border-slate-700 p-8 text-center space-y-2 transition-colors">
            <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
              {dictionary.ai.readyTitle}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
              {dictionary.ai.readyDesc}
            </p>
            <div className="pt-2 text-[11px] font-mono text-slate-400 dark:text-slate-500">
              {dictionary.ai.readyExample}
            </div>
          </div>
        )}
      </div>

      <HowDoesThisWorkModal
        isOpen={showHowItWorksModal}
        onClose={() => setShowHowItWorksModal(false)}
      />
    </>
  );
};

function roundTo2(val: number): number {
  return Math.round(val * 100) / 100;
}

function formatSeconds(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(2)}s`;
}
