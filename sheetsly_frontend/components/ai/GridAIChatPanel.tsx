'use client';

import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../lib/api';
import { AgentExecutionResult, AgentResponseStatus, AIModelOption, TransactionAuditRecordDTO } from '../../lib/types';
import { useTranslation } from '../../lib/i18n';
import { AIModelSelector, FALLBACK_AI_MODELS } from './AIModelSelector';
import { SpreadsheetAgentHelpModal } from './SpreadsheetAgentHelpModal';

interface GridAIChatPanelProps {
  datasetId: string;
  activeSheetName: string;
  onGridUpdated: () => void;
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
  onGridUpdated,
  onClose,
}) => {
  const { dictionary, t } = useTranslation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [undoLoading, setUndoLoading] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const [availableModels, setAvailableModels] = useState<AIModelOption[]>(FALLBACK_AI_MODELS);
  const [selectedModelId, setSelectedModelId] = useState<string>('qwen3.5-397b-a17b');
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
    if (!overrideQuery) setInputQuery('');
    setIsProcessing(true);

    try {
      const result = await api.executeAgentAction({
        dataset_id: datasetId,
        user_request: queryToSend,
        active_sheet_name: activeSheetName,
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

      if (result.status === 'SUCCESS') {
        onGridUpdated();
        await refreshHistory();
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
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/80">
          <div className="flex items-center gap-2">
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 font-mono tracking-tight">
              {dictionary.agent.title}
            </h3>
            <button
              type="button"
              onClick={() => setShowHelpModal(true)}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-700 rounded text-[10px] font-medium cursor-pointer transition-colors shadow-2xs"
              title={dictionary.agent.howItWorksBtn}
            >
              <span className="font-mono text-[9px] w-3 h-3 rounded bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center font-bold">
                ?
              </span>
            </button>
          </div>
          <div className="flex items-center gap-1.5">
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
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 text-sm rounded cursor-pointer"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Model Selector Bar */}
        <div className="px-4 py-2 border-b border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50 flex items-center justify-between">
          <AIModelSelector
            value={selectedModelId}
            onChange={handleModelChange}
            availableModels={availableModels}
            disabled={isProcessing}
          />
        </div>

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto p-3 space-y-3 text-xs">
          {messages.length === 0 && (
            <div className="py-8 text-center space-y-2">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t('agent.emptyInstruction', { sheetName: activeSheetName })}
              </p>
              <div className="flex flex-wrap gap-1.5 justify-center pt-2">
                {quickPrompts.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSend(p)}
                    className="px-2.5 py-1 text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded border border-slate-200 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-500 transition-colors cursor-pointer"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${
                m.sender === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-2.5 space-y-1.5 ${
                  m.sender === 'user'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-medium'
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
                }`}
              >
                <p className="text-xs leading-relaxed whitespace-pre-wrap">{m.text}</p>

                {/* Structured Result Badges */}
                {m.result && (
                  <div className="space-y-1 pt-1 border-t border-slate-200/50 dark:border-slate-700/50 text-[10px] font-mono">
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold">STATUS:</span>
                      <span
                        className={`px-1 py-0.2 rounded font-bold ${
                          m.result.status === 'SUCCESS'
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                            : m.result.status === 'CLARIFICATION'
                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                            : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                        }`}
                      >
                        {m.result.status}
                      </span>
                    </div>

                    {m.result.clarification && (
                      <div className="p-2 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 rounded text-amber-900 dark:text-amber-200 space-y-1 mt-1">
                        <p className="font-sans text-xs font-semibold">{m.result.clarification.question}</p>
                        <div className="flex flex-wrap gap-1 pt-1">
                          {m.result.clarification.options.map((opt, oIdx) => (
                            <button
                              key={oIdx}
                              type="button"
                              onClick={() => handleSend(opt)}
                              className="px-2 py-0.5 bg-white dark:bg-slate-900 border border-amber-300 dark:border-amber-700 rounded text-[11px] font-sans font-medium text-amber-900 dark:text-amber-200 hover:bg-amber-100 dark:hover:bg-amber-900 transition-colors cursor-pointer"
                            >
                              {opt}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <span className="block text-[9px] opacity-60 text-right">
                  {m.timestamp}
                </span>
              </div>
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

        {/* Input Form */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/80">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={isProcessing}
              placeholder={dictionary.agent.inputPlaceholder}
              className="flex-1 px-3 py-1.5 text-xs bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-slate-500 text-slate-900 dark:text-slate-100 placeholder:text-slate-400"
            />
            <button
              type="submit"
              disabled={isProcessing || !inputQuery.trim()}
              className="px-3 py-1.5 text-xs font-semibold bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-md hover:bg-slate-800 dark:hover:bg-white disabled:opacity-50 transition-colors cursor-pointer"
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
    </>
  );
};
