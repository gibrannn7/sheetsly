'use client';

import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import {
  AIStatusResponse,
  NaturalLanguageQueryResponse,
  TableRegion,
  TimingBreakdown,
} from '../../lib/types';
import { AnalysisResultView } from '../builder/AnalysisResultView';
import { ClarificationPrompt } from './ClarificationPrompt';
import { EvidenceExplanationCard } from './EvidenceExplanationCard';
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
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>('');
  const [aiStatus, setAiStatus] = useState<AIStatusResponse | null>(null);
  const [suggestedQueries, setSuggestedQueries] = useState<string[]>([]);
  const [lastResponse, setLastResponse] = useState<NaturalLanguageQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showArchExplainer, setShowArchExplainer] = useState<boolean>(false);

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
      setCurrentStage('Planning analytical query with Qwen...');
      const planRes = await api.planQueryWithAI({
        query: q,
        dataset_id: datasetId,
        sheet_name: sheetName,
        clarification_selection: clarificationSelection || null,
      });

      // Handle early exit outcomes (Clarification, Rejection, Unsupported, Provider Error)
      if (planRes.status !== 'EXECUTION_READY' || !planRes.planned_instruction) {
        setLastResponse({
          status: planRes.status,
          user_query: planRes.user_query,
          intent_summary: planRes.intent_summary,
          planned_instruction: planRes.planned_instruction,
          clarification: planRes.clarification,
          error_message: planRes.error_message,
          timing: planRes.timing,
        });
        if (customQuery) setQuery(customQuery);
        return;
      }

      // Stage 2: Execution of deterministic engine & visualization
      setCurrentStage('Executing deterministic analysis in Python...');
      const fullRes = await api.queryWithAI({
        query: q,
        dataset_id: datasetId,
        sheet_name: sheetName,
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
    <div className="space-y-5">
      {/* 1. Header & AI Provider Status */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs p-4 space-y-3.5">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-200">
          <div>
            <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Natural Language Query Planner
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Ask questions in plain language. Qwen interprets your intent into an Analytical Instruction; Python executes numerical truth.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setShowArchExplainer(!showArchExplainer)}
              className="text-[11px] font-semibold text-slate-600 hover:text-slate-900 underline cursor-pointer"
            >
              {showArchExplainer ? 'Hide Architecture Note' : 'How does this work?'}
            </button>

            {aiStatus?.configured ? (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-100 text-slate-800 border border-slate-300">
                Model: {aiStatus.model}
              </span>
            ) : (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-50 text-slate-600 border border-slate-200">
                Deterministic Fallback Mode
              </span>
            )}
          </div>
        </div>

        {/* Collapsible Architecture Explainer */}
        {showArchExplainer && (
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-md text-xs space-y-1.5 leading-relaxed text-slate-700">
            <div className="font-bold text-slate-900 flex items-center space-x-1.5">
              <span className="font-mono text-[10px] bg-slate-900 text-white px-1.5 py-0.2 rounded">Core Rule</span>
              <span>Qwen interprets intent. Python calculates truth.</span>
            </div>
            <p className="text-slate-600">
              Qwen translates your natural-language question into an <code className="font-mono text-slate-800">AnalyticalInstruction</code>. Before calculation, an AI Guardrail validates that columns and operators match your spreadsheet schema. The Python analytical engine then executes the arithmetic with zero hallucination.
            </p>
          </div>
        )}

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
              placeholder="e.g. What is the total Revenue? or Show average Units by Region"
              disabled={loading}
              className="w-full pl-3.5 pr-32 py-2 bg-white border border-slate-300 rounded-md text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-slate-900 font-sans disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-1 px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-semibold shadow-2xs disabled:opacity-40 cursor-pointer disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Processing...' : 'Run Query'}
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
                Suggestions:
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
          <div className="font-bold">Execution Error</div>
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
                  AI Guardrail Blocked Execution
                </span>
                <span className="font-bold">Pre-execution Schema Violation</span>
              </div>
              <p>{lastResponse.error_message}</p>
              {lastResponse.planned_instruction && (
                <div className="pt-2">
                  <span className="text-[10px] font-bold uppercase text-rose-700 block mb-1">
                    Rejected Instruction Plan:
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
              <div className="font-bold">Query Unsupported by Dataset Schema</div>
              <p>{lastResponse.error_message || 'The question cannot be mapped to the available table operations.'}</p>
            </div>
          )}

          {/* D. Provider Error */}
          {lastResponse.status === 'PROVIDER_ERROR' && (
            <div className="p-4 bg-slate-50 border border-slate-300 rounded-md text-xs text-slate-800 space-y-1.5">
              <div className="font-bold">AI Provider Unavailable</div>
              <p className="text-slate-600">
                AI analysis is currently unavailable because the Qwen provider could not be reached: {lastResponse.error_message}
              </p>
              <p className="text-[11px] text-slate-500">
                Check your <code className="font-mono bg-white px-1 border border-slate-200 rounded">DASHSCOPE_API_KEY</code> in backend <code className="font-mono bg-white px-1 border border-slate-200 rounded">.env</code>, or continue using the point-and-click <strong>Analysis Builder</strong> tab with full deterministic capability.
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
                      Execution Stage Latency
                    </span>
                    <span className="font-mono text-[11px] font-semibold text-slate-700">
                      Total: {formatSeconds(lastResponse.timing.total_duration_ms)}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 pt-1 font-mono text-[11px]">
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <div className="text-[10px] font-sans text-slate-400 uppercase">Schema</div>
                      <div className="font-semibold text-slate-800">{lastResponse.timing.schema_resolution_ms}ms</div>
                    </div>
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <div className="text-[10px] font-sans text-slate-400 uppercase">Qwen Plan</div>
                      <div className="font-semibold text-slate-800">{formatSeconds(lastResponse.timing.qwen_planning_ms)}</div>
                    </div>
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <div className="text-[10px] font-sans text-slate-400 uppercase">Guardrail</div>
                      <div className="font-semibold text-slate-800">{lastResponse.timing.guardrail_validation_ms}ms</div>
                    </div>
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <div className="text-[10px] font-sans text-slate-400 uppercase">Python Calc</div>
                      <div className="font-semibold text-slate-800">{lastResponse.timing.deterministic_execution_ms}ms</div>
                    </div>
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <div className="text-[10px] font-sans text-slate-400 uppercase">Visualizer</div>
                      <div className="font-semibold text-slate-800">{lastResponse.timing.visualization_ms}ms</div>
                    </div>
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <div className="text-[10px] font-sans text-slate-400 uppercase">Explainer</div>
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
                    Suggested Next Questions:
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
            Ready for Natural Language Analysis
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            Enter a question in the search bar above or click one of the suggested questions to compile a verified analytical instruction.
          </p>
          <div className="pt-2 text-[11px] font-mono text-slate-400">
            Example: &ldquo;What is the total revenue?&rdquo; or &ldquo;Show average units by region&rdquo;
          </div>
        </div>
      )}
    </div>
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
