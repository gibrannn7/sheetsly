'use client';

import React, { useEffect, useRef } from 'react';
import { useTranslation } from '../../lib/i18n';

interface DataQualityExplanationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DataQualityExplanationModal: React.FC<DataQualityExplanationModalProps> = ({
  isOpen,
  onClose,
}) => {
  const { dictionary } = useTranslation();
  const modalRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
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

  const t = dictionary.dataQualityModal;

  const dimensions = [
    {
      title: t.brokenFormulasTitle,
      desc: t.brokenFormulasDesc,
      severity: 'CRITICAL',
    },
    {
      title: t.duplicateIdentifiersTitle,
      desc: t.duplicateIdentifiersDesc,
      severity: 'CRITICAL',
    },
    {
      title: t.missingValuesTitle,
      desc: t.missingValuesDesc,
      severity: 'WARNING / INFO',
    },
    {
      title: t.mixedTypesTitle,
      desc: t.mixedTypesDesc,
      severity: 'WARNING',
    },
    {
      title: t.duplicateRowsTitle,
      desc: t.duplicateRowsDesc,
      severity: 'WARNING',
    },
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="data-quality-modal-title"
    >
      <div
        ref={modalRef}
        className="w-full max-w-xl bg-white border border-slate-300 rounded-xl shadow-xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-150"
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 bg-slate-50">
          <div>
            <h3 id="data-quality-modal-title" className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              {t.title}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">{t.subtitle}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label={t.close}
            className="p-1 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition-colors cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-4 text-slate-700 text-xs">
          {/* Overview Section */}
          <div className="space-y-1">
            <h4 className="font-bold text-slate-900 text-xs">{t.howAssessedTitle}</h4>
            <p className="text-slate-600 leading-relaxed text-[11px]">{t.howAssessedDesc}</p>
          </div>

          {/* Quality Dimensions List */}
          <div className="space-y-2.5">
            <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider text-[10px] text-slate-500">
              {t.dimensionsTitle}
            </h4>
            <div className="space-y-2">
              {dimensions.map((dim, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded-lg border border-slate-200 bg-slate-50/70 space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900 text-xs">{dim.title}</span>
                    <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                      {dim.severity}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px] leading-relaxed">{dim.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Scoring Methodology Box */}
          <div className="p-3 bg-slate-100 border border-slate-200 rounded-lg space-y-1">
            <h4 className="font-bold text-slate-900 text-xs">{t.scoringTitle}</h4>
            <p className="text-slate-600 text-[11px] leading-relaxed">{t.scoringDesc}</p>
          </div>

          {/* Disclaimer / Scope Note */}
          <div className="p-3 bg-amber-50/70 border border-amber-200/80 rounded-lg space-y-1 text-amber-900">
            <div className="flex items-center gap-1.5 font-bold text-xs">
              <svg className="w-3.5 h-3.5 text-amber-700 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
              <span>{t.disclaimerTitle}</span>
            </div>
            <p className="text-[11px] leading-relaxed text-amber-800">{t.disclaimerText}</p>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end px-5 py-3 border-t border-slate-200 bg-slate-50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 rounded-md text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800 transition-colors cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400"
          >
            {t.close}
          </button>
        </div>
      </div>
    </div>
  );
};
