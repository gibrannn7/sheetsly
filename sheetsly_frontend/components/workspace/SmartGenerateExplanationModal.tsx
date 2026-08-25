'use client';

import React, { useEffect, useRef } from 'react';
import { useTranslation } from '../../lib/i18n';

interface SmartGenerateExplanationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SmartGenerateExplanationModal: React.FC<SmartGenerateExplanationModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { dictionary } = useTranslation();
  const modalRef = useRef<HTMLDivElement>(null);

  // Close on Escape key and prevent background scroll
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

  if (!isOpen) return null;

  const t = dictionary.smartGenerateModal;

  const steps = [
    { num: '1', title: t.step1Title, desc: t.step1Desc },
    { num: '2', title: t.step2Title, desc: t.step2Desc },
    { num: '3', title: t.step3Title, desc: t.step3Desc },
    { num: '4', title: t.step4Title, desc: t.step4Desc },
    { num: '5', title: t.step5Title, desc: t.step5Desc },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 dark:bg-black/70 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="smart-generate-modal-title"
    >
      <div
        ref={modalRef}
        className="w-full max-w-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-xl shadow-xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-150 transition-colors"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 transition-colors">
          <div>
            <h3 id="smart-generate-modal-title" className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide">
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
          {/* Summary Box */}
          <div className="p-3.5 bg-slate-900 dark:bg-slate-950 text-white rounded-lg space-y-1 shadow-xs border border-slate-800">
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-bold tracking-wider">
                {t.howWorksTitle}
              </span>
            </div>
            <p className="text-slate-200 text-xs leading-relaxed pt-0.5">
              {t.howWorksDesc}
            </p>
          </div>

          {/* Numbered 5-Step Pipeline */}
          <div className="space-y-2.5 pt-1">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {t.stepsTitle}
            </h4>
            {steps.map((step) => (
              <div
                key={step.num}
                className="flex items-start gap-3 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/70"
              >
                <div className="w-5 h-5 rounded bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-mono font-bold text-[11px] flex items-center justify-center shrink-0 mt-0.5">
                  {step.num}
                </div>
                <div className="space-y-0.5">
                  <h5 className="font-bold text-slate-900 dark:text-slate-100 text-xs">{step.title}</h5>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed text-[11px]">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Heuristic Notice */}
          <div className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
            <span className="font-semibold text-slate-800 dark:text-slate-200">Analytical Principle: </span>
            {t.footerNote}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end px-5 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 transition-colors">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-md text-xs font-semibold bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-white transition-colors cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            {t.close}
          </button>
        </div>
      </div>
    </div>
  );
};
