'use client';

import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from '../../lib/i18n';
import { ChartActionSpecDTO } from '../../lib/types';

interface ChartFullscreenModalProps {
  isOpen: boolean;
  onClose: () => void;
  chart: ChartActionSpecDTO | null;
}

export const ChartFullscreenModal: React.FC<ChartFullscreenModalProps> = ({
  isOpen,
  onClose,
  chart,
}) => {
  const { dictionary } = useTranslation();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || !mounted || !chart) return null;

  const t = dictionary.agent.chartArtifact;

  const modalContent = (
    <div
      className="fixed inset-0 z-9999 flex items-center justify-center p-4 sm:p-6 bg-slate-900/70 dark:bg-black/80 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl shadow-2xl w-full max-w-3xl max-h-[92vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150 transition-colors"
        role="dialog"
        aria-modal="true"
        aria-labelledby="chart-modal-title"
      >
        {/* Header */}
        <div className="px-5 py-3.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between gap-3 bg-slate-50 dark:bg-slate-950 transition-colors">
          <div className="flex items-center gap-2 min-w-0">
            <span className="px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 font-mono text-[10px] font-bold uppercase tracking-wider">
              {chart.chart_type}
            </span>
            <h3 id="chart-modal-title" className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100 truncate">
              {chart.title}
            </h3>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {chart.destination_cell && (
              <span className="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-mono text-[10px] font-bold">
                {t.destination}: {chart.destination_cell}
              </span>
            )}
            <button
              type="button"
              onClick={onClose}
              className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 p-1 text-sm rounded cursor-pointer transition-colors"
              aria-label={t.close}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-xs">
          {/* Main Chart Graphic */}
          {chart.image_base64 && (
            <div className="bg-white dark:bg-slate-950 rounded-lg border border-slate-200 dark:border-slate-800 p-3 flex items-center justify-center shadow-2xs">
              <img
                src={`data:image/png;base64,${chart.image_base64}`}
                alt={chart.title}
                className="w-full max-h-[460px] object-contain select-none"
              />
            </div>
          )}

          {/* Metadata & Verification Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-0.5">
              <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block font-mono">
                {t.category}
              </span>
              <p className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                {chart.dimension_column || chart.category_column || '-'}
              </p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-0.5">
              <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block font-mono">
                {t.measure}
              </span>
              <p className="font-semibold text-slate-800 dark:text-slate-200 truncate">
                {chart.measure_column || '-'}
              </p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-0.5">
              <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block font-mono">
                {t.aggregation}
              </span>
              <p className="font-semibold text-slate-800 dark:text-slate-200 truncate font-mono">
                {chart.aggregation || 'SUM'}
              </p>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 space-y-0.5">
              <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider block font-mono">
                {t.destination}
              </span>
              <p className="font-semibold text-slate-800 dark:text-slate-200 truncate font-mono">
                {chart.destination_cell || '-'}
              </p>
            </div>
          </div>

          {/* Verification Status */}
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-emerald-50/80 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 text-emerald-800 dark:text-emerald-300 text-[11px] font-mono">
            <span className="font-semibold flex items-center gap-1.5">
              <span>✓</span> {t.verifiedTruth}
            </span>
            <span className="text-[10px] text-emerald-700/80 dark:text-emerald-400/80">
              {chart.provenance_note || 'Deterministic Python Engine'}
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-end bg-slate-50 dark:bg-slate-950">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-900 rounded-md text-xs font-semibold cursor-pointer transition-colors shadow-2xs"
          >
            {t.close}
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};
