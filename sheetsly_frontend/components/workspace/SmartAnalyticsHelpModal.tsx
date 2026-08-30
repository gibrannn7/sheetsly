'use client';

import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from '../../lib/i18n';

interface SmartAnalyticsHelpModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SmartAnalyticsHelpModal: React.FC<SmartAnalyticsHelpModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { dictionary } = useTranslation();
  const modalRef = useRef<HTMLDivElement>(null);
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

  if (!isOpen || !mounted) return null;

  const t = dictionary.smartAnalytics.modal;

  const modalContent = (
    <div
      className="fixed inset-0 z-9999 flex items-center justify-center p-4 bg-slate-900/60 dark:bg-black/75 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="smart-analytics-help-modal-title"
    >
      <div
        ref={modalRef}
        className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-150 transition-colors"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 transition-colors">
          <div>
            <h3 id="smart-analytics-help-modal-title" className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
              {t.title}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{t.subtitle}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t.close}
            className="p-1 rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-800 transition-colors cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-slate-700 dark:text-slate-300 text-xs">
          {/* Core Truth Box */}
          <div className="p-3.5 bg-slate-900 dark:bg-slate-950 text-white rounded-lg space-y-1 shadow-xs border border-slate-800">
            <span className="font-bold text-slate-100 font-mono text-[11px] block uppercase tracking-wider">
              {t.coreTruthTitle}
            </span>
            <p className="text-slate-200 text-xs leading-relaxed">
              {t.coreTruthDesc}
            </p>
          </div>

          {/* Key Capabilities */}
          <div className="space-y-2.5 pt-1">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t.featuresTitle}
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {/* Temporal */}
              <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 space-y-1">
                <span className="font-bold text-slate-900 dark:text-slate-100 font-mono text-[11px] block">
                  {t.temporalTitle}
                </span>
                <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                  {t.temporalDesc}
                </p>
              </div>

              {/* Top-N Ranking */}
              <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 space-y-1">
                <span className="font-bold text-slate-900 dark:text-slate-100 font-mono text-[11px] block">
                  {t.rankingTitle}
                </span>
                <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                  {t.rankingDesc}
                </p>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 space-y-1">
                <span className="font-bold text-slate-900 dark:text-slate-100 font-mono text-[11px] block">
                  {t.multiSheetTitle}
                </span>
                <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                  {t.multiSheetDesc}
                </p>
              </div>

              <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 space-y-1">
                <span className="font-bold text-slate-900 dark:text-slate-100 font-mono text-[11px] block">
                  {t.provenanceTitle}
                </span>
                <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                  {t.provenanceDesc}
                </p>
              </div>
            </div>

            <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 space-y-1">
              <span className="font-bold text-slate-900 dark:text-slate-100 font-mono text-[11px] block">
                {t.clarificationTitle}
              </span>
              <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                {t.clarificationDesc}
              </p>
            </div>
          </div>

          {/* Recommended Examples */}
          <div className="space-y-2 pt-1 border-t border-slate-200 dark:border-slate-800">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t.exampleHeading}
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {t.examples.map((ex, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded border border-slate-200 dark:border-slate-700 font-mono"
                >
                  "{ex}"
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-5 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-900 dark:bg-slate-100 hover:bg-slate-800 dark:hover:bg-white text-white dark:text-slate-900 rounded-md text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
          >
            {t.close}
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};
