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
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>('');
  const [aiStatus, setAiStatus] = useState<AIStatusResponse | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('qwen3.5-plus');
  const [showHowItWorksModal, setShowHowItWorksModal] = useState<boolean>(false);
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([]);
  const [lastResponse, setLastResponse] = useState<NaturalLanguageQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize selected model from localStorage on mount
  useEffect(() => {
    try {
      const savedModel = localStorage.getItem('sheetsly_selected_model');
      if (savedModel) {
        setSelectedModel(savedModel);
      }
    } catch {}
  }, []);

  const handleModelChange = (newModelId: string) => {
    setSelectedModel(newModelId);
    try {
      localStorage.setItem('sheetsly_selected_model', newModelId);
    } catch {}
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

    api
      .getSuggestedQueries(datasetId, sheetName)
      .then((res) => {
        if (isMounted) setSuggestedQueries(res.suggested_queries || []);
      })
      .catch(() => {});

    return () => {
      isMounted = false;
    };
  }, [datasetId, sheetName]);

  const handleExecuteQuery = async (
    customQuery?: string,
    clarificationSelection?: Record<string, string>
  ) => {
    const q = (customQuery || query).trim();
    if (!q) return;

    setLoading(true);
    setError(null);

    try {
      // Stage 1: Network call to Qwen Planner
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
        setLastResponse({
          status: planRes.status,
          user_query: planRes.user_query,
          intent_summary: planRes.intent_summary,
          model_used: planRes.model_used || selectedModel,
          planned_instruction: planRes.planned_instruction,
          clarification: planRes.clarification,
          error_message: planRes.error_message,
          timing: planRes.timing,
        });
        if (customQuery) setQuery(customQuery);
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

      setLastResponse({
        ...fullRes,
        model_used: fullRes.model_used || selectedModel,
        timing: mergedTiming,
      });

      if (customQuery) setQuery(customQuery);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'An unexpected error occurred during query processing.');
      }
      setLastResponse(null);
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
        <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-4 space-y-3.5">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
            <div>
              <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                {dictionary.ai.title}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                {dictionary.ai.desc}
              </p>
            </div>

            <div className="flex items-center space-x-2.5">
              <button
                type="button"
                onClick={() => setShowHowItWorksModal(true)}
                className="text-[11px] font-semibold text-slate-600 hover:text-slate-900 underline cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400 rounded px-1"
              >
                {dictionary.ai.howDoesThisWork}
              </button>

              {aiStatus?.configured ? (
                <AIModelSelector
                  value={selectedModel}
                  onChange={handleModelChange}
                  availableModels={aiStatus.available_models}
                  disabled={loading}
                />
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-50 text-slate-600 border border-slate-200">
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
                onChange={(e) => setQuery(e.target.value)}
                placeholder={dictionary.ai.placeholder}
                disabled={loading}
                className="w-full pl-3.5 pr-32 py-2 bg-white border border-slate-300 rounded-md text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 font-sans disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="absolute right-1 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold shadow-2xs disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed transition-colors"
              >
                {loading ? dictionary.ai.processing : dictionary.ai.runQuery}
              </button>
            </div>

            {/* Truthful Stage Indicator (during live execution) */}
            {loading && currentStage && (
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 font-sans">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-slate-700" />
                <span className="font-medium">{currentStage}</span>
              </div>
            )}

            {/* Schema-Derived Suggestions */}
            {!loading && suggestedQueries.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider select-none">
                  {dictionary.ai.suggestions}
                </span>
                {suggestedQueries.map((sq, idx) => (
                  <button
                    key={idx}
                    type="button"
                    disabled={loading}
                    onClick={() => handleExecuteQuery(sq)}
                    className="px-2.5 py-0.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 rounded text-[11px] transition-colors cursor-pointer disabled:opacity-40 text-left font-medium"
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
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-800 space-y-1">
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
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-900 space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="px-1.5 py-0.2 rounded bg-rose-200 text-rose-900 font-bold text-[10px] uppercase">
                    {dictionary.ai.guardrailBlocked}
                  </span>
                  <span className="font-bold">{dictionary.ai.schemaViolation}</span>
                </div>
                <p>{lastResponse.error_message}</p>
                {lastResponse.planned_instruction && (
                  <div className="pt-2">
                    <span className="text-[10px] font-bold uppercase text-rose-700 block mb-1">
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
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-md text-xs text-amber-900 space-y-1">
                <div className="font-bold">{dictionary.ai.unsupported}</div>
                <p>{lastResponse.error_message || dictionary.ai.unsupportedDefault}</p>
              </div>
            )}

            {/* D. Provider Error */}
            {lastResponse.status === 'PROVIDER_ERROR' && (
              <div className="p-4 bg-slate-50 border border-slate-300 rounded-md text-xs text-slate-800 space-y-1.5">
                <div className="font-bold text-slate-900">{dictionary.ai.providerUnavailable}</div>
                <p className="text-slate-600 leading-relaxed">
                  {lastResponse.error_message &&
                  (lastResponse.error_message.includes('not configured') ||
                    lastResponse.error_message.includes('not set') ||
                    lastResponse.error_message.includes('unconfigured'))
                    ? dictionary.ai.providerUnconfiguredDesc
                    : dictionary.ai.providerOfflineDesc}
                </p>
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
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                        {dictionary.ai.stageLatency}
                      </span>
                      <span className="font-mono text-[11px] font-semibold text-slate-700">
                        {t('ai.total', { duration: formatSeconds(lastResponse.timing.total_duration_ms) })}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 pt-1 font-mono text-[11px]">
                      <div className="bg-white p-2 rounded border border-slate-200">
                        <div className="text-[10px] font-sans text-slate-400 uppercase">{dictionary.ai.schemaStage}</div>
                        <div className="font-semibold text-slate-800">{lastResponse.timing.schema_resolution_ms}ms</div>
                      </div>
                      <div className="bg-white p-2 rounded border border-slate-200">
                        <div className="text-[10px] font-sans text-slate-400 uppercase">{dictionary.ai.qwenPlanStage}</div>
                        <div className="font-semibold text-slate-800">{formatSeconds(lastResponse.timing.qwen_planning_ms)}</div>
                      </div>
                      <div className="bg-white p-2 rounded border border-slate-200">
                        <div className="text-[10px] font-sans text-slate-400 uppercase">{dictionary.ai.guardrailStage}</div>
                        <div className="font-semibold text-slate-800">{lastResponse.timing.guardrail_validation_ms}ms</div>
                      </div>
                      <div className="bg-white p-2 rounded border border-slate-200">
                        <div className="text-[10px] font-sans text-slate-400 uppercase">{dictionary.ai.pythonCalcStage}</div>
                        <div className="font-semibold text-slate-800">{lastResponse.timing.deterministic_execution_ms}ms</div>
                      </div>
                      <div className="bg-white p-2 rounded border border-slate-200">
                        <div className="text-[10px] font-sans text-slate-400 uppercase">{dictionary.ai.visualizerStage}</div>
                        <div className="font-semibold text-slate-800">{lastResponse.timing.visualization_ms}ms</div>
                      </div>
                      <div className="bg-white p-2 rounded border border-slate-200">
                        <div className="text-[10px] font-sans text-slate-400 uppercase">{dictionary.ai.explainerStage}</div>
                        <div className="font-semibold text-slate-800">{formatSeconds(lastResponse.timing.evidence_explanation_ms)}</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 4. Verified Result View (Scalar / Table / Chart / Lineage Trace) */}
                {lastResponse.analytical_result && (
                  <AnalysisResultView
                    datasetId={datasetId}
                    result={lastResponse.analytical_result}
                  />
                )}

                {/* 5. Suggested Follow-Up Queries */}
                {lastResponse.suggested_next_queries && lastResponse.suggested_next_queries.length > 0 && (
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                      {dictionary.ai.suggestedNext}
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {lastResponse.suggested_next_queries.map((nq, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => handleExecuteQuery(nq)}
                          className="px-2.5 py-1 bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 rounded text-xs font-medium cursor-pointer transition-colors shadow-2xs text-left"
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
          <div className="bg-white rounded-lg border border-dashed border-slate-300 p-8 text-center space-y-2">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              {dictionary.ai.readyTitle}
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
              {dictionary.ai.readyDesc}
            </p>
            <div className="pt-2 text-[11px] font-mono text-slate-400">
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
