'use client';

import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../lib/api';
import { AgentExecutionResult, AgentResponseStatus, AIModelOption, ChartActionSpecDTO, TransactionAuditRecordDTO } from '../../lib/types';
import { useTranslation } from '../../lib/i18n';
import { AIModelSelector, FALLBACK_AI_MODELS } from './AIModelSelector';
import { SpreadsheetAgentHelpModal } from './SpreadsheetAgentHelpModal';
import { ChartFullscreenModal } from './ChartFullscreenModal';

interface GridAIChatPanelProps {
  datasetId: string;
  activeSheetName: string;
  selectedRange?: string;
  onClearSelection?: () => void;
  onGridUpdated: () => void;
  onFocusCell?: (cellRef: string) => void;
  onClose?: () => void;
}

interface ChatMessage {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  result?: AgentExecutionResult;
}

export const GridAIChatPanel: React.FC<GridAIChatPanelProps> = ({
  datasetId,
  activeSheetName,
  selectedRange,
  onClearSelection,
  onGridUpdated,
  onFocusCell,
  onClose,
}) => {
  const { dictionary, t } = useTranslation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [undoLoading, setUndoLoading] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [selectedChartModal, setSelectedChartModal] = useState<ChartActionSpecDTO | null>(null);
  const [availableModels, setAvailableModels] = useState<AIModelOption[]>(FALLBACK_AI_MODELS);
  const [selectedModelId, setSelectedModelId] = useState<string>('qwen3.5-397b-a17b');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync undo availability
  const refreshHistory = async () => {
    try {
      const hist = await api.getAgentHistory(datasetId);
      setCanUndo(hist.can_undo);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    refreshHistory();
  }, [datasetId, activeSheetName]);

  useEffect(() => {
    const savedModel = typeof window !== 'undefined' ? localStorage.getItem('sheetsly_preferred_model') : null;
    if (savedModel && savedModel !== 'qwen3.5-plus') {
      setSelectedModelId(savedModel);
    }
    api
      .getAIStatus()
      .then((status) => {
        if (status.available_models && status.available_models.length > 0) {
          setAvailableModels(status.available_models);
          if (status.default_model && !savedModel) {
            setSelectedModelId(status.default_model);
          }
        }
      })
      .catch((err) => console.warn('Could not fetch AI models:', err));
  }, []);

  const handleModelChange = (modelId: string) => {
    setSelectedModelId(modelId);
    if (typeof window !== 'undefined') {
      localStorage.setItem('sheetsly_preferred_model', modelId);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  const handleSend = async (overrideQuery?: string) => {
    const queryToSend = overrideQuery || inputQuery.trim();
    if (!queryToSend || isProcessing) return;

    const userMsg: ChatMessage = {
      id: `msg_user_${Date.now()}`,
      sender: 'user',
      text: queryToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!overrideQuery) {
      setInputQuery('');
      if (textareaRef.current) {
        textareaRef.current.style.height = '38px';
        textareaRef.current.style.overflowY = 'hidden';
      }
    }
    setIsProcessing(true);

    try {
      const result = await api.executeAgentAction({
        dataset_id: datasetId,
        user_request: queryToSend,
        active_sheet_name: activeSheetName,
        selected_range: selectedRange || undefined,
        model_id: selectedModelId,
      });

      const agentMsg: ChatMessage = {
        id: `msg_agent_${Date.now()}`,
        sender: 'agent',
        text: result.message || dictionary.agent.defaultDone,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        result: result,
      };

      setMessages((prev) => [...prev, agentMsg]);

      if (result.status === 'SUCCESS' || result.status === 'ROLLBACK_SUCCESS') {
        onGridUpdated();
        await refreshHistory();
        if (result.affected_ranges && result.affected_ranges.length > 0 && onFocusCell) {
          const firstTarget = result.affected_ranges[0];
          onFocusCell(firstTarget);
        } else if (result.transaction?.actions && result.transaction.actions.length > 0 && onFocusCell) {
          const firstAct = result.transaction.actions[0];
          const target = firstAct.target_cell || (firstAct.target_range ? firstAct.target_range.split(':')[0] : null);
          if (target) {
            onFocusCell(target);
          }
        }
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `msg_agent_err_${Date.now()}`,
        sender: 'agent',
        text: err.message || dictionary.agent.failed,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleUndo = async () => {
    if (undoLoading || !canUndo) return;
    setUndoLoading(true);

    try {
      const res = await api.undoAgentAction(datasetId, activeSheetName);
      const undoMsg: ChatMessage = {
        id: `msg_undo_${Date.now()}`,
        sender: 'agent',
        text: res.message || dictionary.agent.undoSuccess,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        result: res,
      };
      setMessages((prev) => [...prev, undoMsg]);
      onGridUpdated();
      await refreshHistory();
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `msg_undo_err_${Date.now()}`,
        sender: 'agent',
        text: t('agent.undoError', { error: err.message }),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setUndoLoading(false);
    }
  };

  const quickPrompts = [
    dictionary.agent.quickPrompts.p1,
    dictionary.agent.quickPrompts.p2,
    dictionary.agent.quickPrompts.p3,
  ];

  return (
    <>
      <div className="flex flex-col h-full bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-xl w-80 sm:w-96 transition-colors">
        {/* Unified Header: [Sheet context] [qwen3.5-397b-a17b ▾] [Close] */}
        <div className="px-3 py-2 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between gap-2 bg-slate-50 dark:bg-slate-950 transition-colors">
          {/* Left: Sheet Badge & Help Button */}
          <div className="flex items-center gap-1.5 min-w-0 shrink">
            <span
              title={`Active Worksheet: ${activeSheetName}`}
              className="px-2 py-0.5 rounded bg-slate-200/80 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-mono text-[11px] font-bold truncate max-w-[90px] sm:max-w-[110px] select-none border border-slate-300 dark:border-slate-700"
            >
              {activeSheetName}
            </span>
            <button
              type="button"
              onClick={() => setShowHelpModal(true)}
              className="inline-flex items-center justify-center w-4 h-4 bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded text-[10px] font-bold font-mono cursor-pointer transition-colors shrink-0"
              title={dictionary.agent.howItWorksBtn}
            >
              ?
            </button>
          </div>

          {/* Middle: Compact Model Selector */}
          <div className="flex items-center shrink-0">
            <AIModelSelector
              value={selectedModelId}
              onChange={handleModelChange}
              availableModels={availableModels}
              disabled={isProcessing}
            />
          </div>

          {/* Right: Undo & Close Buttons */}
          <div className="flex items-center gap-1 shrink-0">
            {canUndo && (
              <button
                type="button"
                onClick={handleUndo}
                disabled={undoLoading}
                title={dictionary.agent.undoTitle}
                className="px-2 py-1 text-[11px] font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded hover:bg-slate-100 dark:hover:bg-slate-750 transition-colors shadow-2xs cursor-pointer"
              >
                {undoLoading ? dictionary.agent.rollingBack : dictionary.agent.undoBtn}
              </button>
            )}
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                aria-label={dictionary.common.close}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 p-1 text-sm rounded cursor-pointer transition-colors"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3 text-xs">
          {messages.length === 0 && (
            <div className="text-center py-6 space-y-3">
              <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center mx-auto text-xs font-mono font-bold">
                AI
              </div>
              <div className="space-y-1">
                <p className="font-semibold text-slate-800 dark:text-slate-200 text-xs">
                  {dictionary.agent.emptyTitle}
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
                  {dictionary.agent.emptySubtitle}
                </p>
              </div>

              {/* Quick Prompts */}
              <div className="pt-2 space-y-1.5 text-left">
                <span className="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider block px-1 font-mono">
                  {dictionary.agent.quickPromptsTitle}
                </span>
                {quickPrompts.map((promptText, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSend(promptText)}
                    disabled={isProcessing}
                    className="w-full text-left p-2 rounded bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/60 text-slate-700 dark:text-slate-300 text-[11px] font-mono transition-colors cursor-pointer block"
                  >
                    &ldquo;{promptText}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-2.5 space-y-1.5 text-xs shadow-2xs ${
                  msg.sender === 'user'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-medium'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
                }`}
              >
                <div className="whitespace-pre-wrap break-words">{msg.text}</div>

                {/* Primary Chart Artifact Card */}
                {msg.result?.transaction?.actions && (
                  (() => {
                    const chartAction = msg.result.transaction.actions.find(
                      (a) => a.action_type === 'CREATE_CHART' && a.chart_spec
                    );
                    const chartSpec = chartAction?.chart_spec;
                    if (!chartSpec) return null;

                    return (
                      <div
                        onClick={() => setSelectedChartModal(chartSpec)}
                        className="mt-2 p-2.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500 shadow-2xs hover:shadow-xs transition-all cursor-pointer group space-y-2 select-none"
                        role="button"
                        tabIndex={0}
                        title={dictionary.agent.chartArtifact?.viewFullscreen || 'Click to view fullscreen'}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            setSelectedChartModal(chartSpec);
                          }
                        }}
                      >
                        <div className="flex items-center justify-between gap-1.5 border-b border-slate-100 dark:border-slate-800 pb-1.5">
                          <div className="flex items-center gap-1.5 min-w-0">
                            <span className="px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 font-mono text-[9px] font-bold uppercase tracking-wider">
                              {chartSpec.chart_type}
                            </span>
                            <span className="font-semibold text-xs text-slate-900 dark:text-slate-100 truncate">
                              {chartSpec.title}
                            </span>
                          </div>
                          <span className="text-[10px] text-slate-400 dark:text-slate-500 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors shrink-0">
                            ⛶
                          </span>
                        </div>

                        {chartSpec.image_base64 && (
                          <div className="relative bg-slate-50 dark:bg-slate-950 rounded border border-slate-100 dark:border-slate-800 overflow-hidden p-1 flex items-center justify-center">
                            <img
                              src={`data:image/png;base64,${chartSpec.image_base64}`}
                              alt={chartSpec.title}
                              className="w-full max-h-36 object-contain select-none transition-transform group-hover:scale-[1.01]"
                            />
                          </div>
                        )}

                        <div className="flex items-center justify-between text-[10px] text-slate-500 dark:text-slate-400 font-mono pt-0.5">
                          <span className="truncate max-w-[65%]">
                            {chartSpec.dimension_column && `${chartSpec.dimension_column}`}
                            {chartSpec.measure_column && ` → ${chartSpec.measure_column}`}
                            {chartSpec.aggregation && ` (${chartSpec.aggregation})`}
                          </span>
                          <div className="flex items-center gap-1.5 shrink-0">
                            {chartSpec.destination_cell && (
                              <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-[9px]">
                                {chartSpec.destination_cell}
                              </span>
                            )}
                            <span className="text-emerald-600 dark:text-emerald-400 font-semibold text-[9px]">
                              ✓ {dictionary.agent.chartArtifact?.verifiedTruth || 'Verified'}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })()
                )}

                {/* Agent Action Execution Details */}
                {msg.result && msg.result.transaction && msg.result.transaction.actions.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 space-y-2">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-slate-500 dark:text-slate-400 block font-mono">
                      {dictionary.agent.mutationDetails}
                    </span>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {msg.result.transaction.actions.map((act) => (
                        <div
                          key={act.action_id}
                          className="text-[10px] font-mono p-2 bg-white/80 dark:bg-slate-900/80 rounded border border-slate-200/80 dark:border-slate-700/80 text-slate-700 dark:text-slate-300 space-y-1.5"
                        >
                          <div className="flex items-center justify-between gap-1">
                            <span className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1">
                              {act.action_type === 'CREATE_CHART' && <span className="px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-[9px]">CHART</span>}
                              {act.action_type === 'CREATE_KPI' && <span className="px-1.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 text-[9px]">KPI</span>}
                              {act.action_type}
                            </span>
                            {act.target_cell && <span className="text-slate-500 dark:text-slate-400 font-semibold">[{act.target_cell}]</span>}
                            {act.target_range && <span className="text-slate-500 dark:text-slate-400 font-semibold">[{act.target_range}]</span>}
                          </div>

                          {/* KPI Spec Card Preview */}
                          {act.kpi_spec && (
                            <div className="p-2 rounded bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-0.5">
                              <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium">{act.kpi_spec.title}</div>
                              <div className="text-sm font-bold text-slate-900 dark:text-slate-100">{act.kpi_spec.formatted_value}</div>
                              <div className="text-[9px] text-emerald-600 dark:text-emerald-400 font-medium">✓ Verified Python Truth</div>
                            </div>
                          )}

                          {act.formula && <div className="text-amber-800 dark:text-amber-400 font-semibold">{act.formula}</div>}
                          {act.value !== undefined && act.value !== null && (
                            <div className="text-slate-800 dark:text-slate-200">{String(act.value)}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <span className="text-[9px] text-slate-400 dark:text-slate-500 font-mono mt-0.5 px-1">
                {msg.timestamp}
              </span>
            </div>
          ))}

          {isProcessing && (
            <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 p-2">
              <div className="w-3.5 h-3.5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs">{dictionary.agent.processing}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form with Selected Range Badge & Multiline Composer */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 transition-colors space-y-2">
          {selectedRange && (
            <div className="flex items-center justify-between px-2 py-1 bg-slate-200/80 dark:bg-slate-800 rounded border border-slate-300 dark:border-slate-700 text-[11px] font-mono text-slate-700 dark:text-slate-300">
              <span className="truncate">
                {t('agent.selectedRangeContext', { range: selectedRange })}
              </span>
              {onClearSelection && (
                <button
                  type="button"
                  onClick={onClearSelection}
                  className="p-0.5 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 cursor-pointer ml-1"
                  title={dictionary.agent.removeSelectionContext}
                >
                  ✕
                </button>
              )}
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-end gap-2"
          >
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputQuery}
              onChange={(e) => {
                setInputQuery(e.target.value);
                if (textareaRef.current) {
                  textareaRef.current.style.height = '38px';
                  const scrollH = textareaRef.current.scrollHeight;
                  const targetH = Math.min(scrollH, 110);
                  textareaRef.current.style.height = `${Math.max(38, targetH)}px`;
                  textareaRef.current.style.overflowY = scrollH > 110 ? 'auto' : 'hidden';
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={isProcessing}
              placeholder={dictionary.agent.multilinePlaceholder || dictionary.agent.inputPlaceholder}
              className="flex-1 px-3 py-2 text-xs bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-slate-500 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 resize-none max-h-[110px] min-h-[38px] overflow-y-hidden overflow-x-hidden whitespace-pre-wrap break-words leading-relaxed transition-[height]"
            />
            <button
              type="submit"
              disabled={isProcessing || !inputQuery.trim()}
              className="px-3.5 py-2 text-xs font-semibold bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-md hover:bg-slate-800 dark:hover:bg-white disabled:opacity-50 transition-colors cursor-pointer shrink-0 min-h-[38px]"
            >
              {dictionary.agent.sendBtn}
            </button>
          </form>
        </div>
      </div>

      <SpreadsheetAgentHelpModal
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
      />

      <ChartFullscreenModal
        isOpen={!!selectedChartModal}
        onClose={() => setSelectedChartModal(null)}
        chart={selectedChartModal}
      />
    </>
  );
};
