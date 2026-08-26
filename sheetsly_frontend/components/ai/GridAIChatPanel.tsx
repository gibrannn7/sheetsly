'use client';

import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../lib/api';
import { AgentExecutionResult, AgentResponseStatus, TransactionAuditRecordDTO } from '../../lib/types';
import { useTranslation } from '../../lib/i18n';

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
  const { dictionary } = useTranslation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [undoLoading, setUndoLoading] = useState(false);
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
      });

      const agentMsg: ChatMessage = {
        id: `msg_agent_${Date.now()}`,
        sender: 'agent',
        text: result.message || 'Instruksi telah diproses.',
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
        text: err.message || 'Gagal memproses permintaan.',
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
        text: res.message || 'Perubahan terakhir telah dibatalkan (Rollback).',
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
        text: `Gagal membatalkan: ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setUndoLoading(false);
    }
  };

  const quickPrompts = [
    'buatkan total penjualan',
    'hitung rata-rata sales',
    'buat total profit',
  ];

  return (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-xl w-80 sm:w-96 transition-colors">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900/80">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 font-mono tracking-tight">
            SPREADSHEET AGENT
          </h3>
        </div>
        <div className="flex items-center gap-1.5">
          {canUndo && (
            <button
              type="button"
              onClick={handleUndo}
              disabled={undoLoading}
              title="Batalkan perubahan terakhir"
              className="px-2 py-1 text-[11px] font-semibold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 border border-amber-200 dark:border-amber-800 rounded hover:bg-amber-100 dark:hover:bg-amber-900 transition-colors cursor-pointer"
            >
              {undoLoading ? 'Rolling back...' : '↩ Undo'}
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

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 text-xs">
        {messages.length === 0 && (
          <div className="py-8 text-center space-y-2">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Ketik instruksi untuk memodifikasi atau menghitung formula di sheet <span className="font-semibold">{activeSheetName}</span>.
            </p>
            <div className="flex flex-wrap gap-1.5 justify-center pt-2">
              {quickPrompts.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(p)}
                  className="px-2.5 py-1 text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-full border border-slate-200 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-500 transition-colors cursor-pointer"
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
                  ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700'
              }`}
            >
              <p className="whitespace-pre-wrap leading-relaxed">{m.text}</p>

              {/* Status Badge & Verification Card */}
              {m.result && (
                <div className="pt-1 border-t border-slate-200/40 dark:border-slate-700/60 space-y-1 text-[11px]">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`px-1.5 py-0.5 rounded font-mono font-bold text-[10px] ${
                        m.result.status === 'SUCCESS'
                          ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300'
                          : m.result.status === 'CLARIFICATION'
                          ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300'
                          : 'bg-red-100 text-red-800 dark:bg-red-950/80 dark:text-red-300'
                      }`}
                    >
                      {m.result.status}
                    </span>
                    {m.result.affected_ranges.length > 0 && (
                      <span className="text-[10px] text-slate-500 font-mono">
                        Target: {m.result.affected_ranges.join(', ')}
                      </span>
                    )}
                  </div>

                  {/* Clarification Options */}
                  {m.result.clarification && m.result.clarification.options.length > 0 && (
                    <div className="pt-2 space-y-1">
                      <p className="text-[11px] font-semibold text-amber-800 dark:text-amber-300">
                        {m.result.clarification.question}
                      </p>
                      <div className="flex flex-wrap gap-1 pt-1">
                        {m.result.clarification.options.map((opt, oIdx) => (
                          <button
                            key={oIdx}
                            type="button"
                            onClick={() => handleSend(opt)}
                            className="px-2 py-1 text-[10px] font-semibold bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer text-slate-800 dark:text-slate-200"
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
            <span className="text-xs">Agent sedang memvalidasi dan memproses...</span>
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
            placeholder="Ketik instruksi... (misal: buat total penjualan)"
            className="flex-1 px-3 py-1.5 text-xs bg-white dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-md focus:outline-none focus:ring-1 focus:ring-slate-500 text-slate-900 dark:text-slate-100 placeholder:text-slate-400"
          />
          <button
            type="submit"
            disabled={isProcessing || !inputQuery.trim()}
            className="px-3 py-1.5 text-xs font-semibold bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-md hover:bg-slate-800 dark:hover:bg-white disabled:opacity-50 transition-colors cursor-pointer"
          >
            Kirim
          </button>
        </form>
      </div>
    </div>
  );
};
