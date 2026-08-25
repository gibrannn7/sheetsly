'use client';

import React, { useEffect } from 'react';
import { useTranslation } from '../../lib/i18n';

export const LanguageOnboardingModal: React.FC = () => {
  const { language, setLanguage, dictionary, showOnboarding, dismissOnboarding } = useTranslation();

  // Handle Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showOnboarding) {
        dismissOnboarding();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showOnboarding, dismissOnboarding]);

  if (!showOnboarding) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-lang-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div className="bg-white w-full max-w-md rounded-xl border border-slate-300 shadow-xl p-6 space-y-5">
        {/* Header */}
        <div className="space-y-1.5">
          <div className="w-8 h-8 rounded-md bg-slate-900 text-white font-mono font-bold text-sm flex items-center justify-center mb-3">
            S
          </div>
          <h2 id="onboarding-lang-title" className="text-base font-bold text-slate-900">
            {dictionary.onboarding.title}
          </h2>
          <p className="text-xs text-slate-600 leading-relaxed">
            {dictionary.onboarding.subtitle}
          </p>
        </div>

        {/* Language Selection Buttons */}
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setLanguage('en')}
            className={`p-3.5 rounded-lg border text-left transition-all cursor-pointer ${
              language === 'en'
                ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                : 'bg-slate-50 text-slate-800 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <span className="block text-xs font-bold">English</span>
            <span className={`block text-[10px] mt-0.5 ${language === 'en' ? 'text-slate-300' : 'text-slate-500'}`}>
              Default / Canonical
            </span>
          </button>

          <button
            type="button"
            onClick={() => setLanguage('id')}
            className={`p-3.5 rounded-lg border text-left transition-all cursor-pointer ${
              language === 'id'
                ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                : 'bg-slate-50 text-slate-800 border-slate-200 hover:bg-slate-100'
            }`}
          >
            <span className="block text-xs font-bold">Bahasa Indonesia</span>
            <span className={`block text-[10px] mt-0.5 ${language === 'id' ? 'text-slate-300' : 'text-slate-500'}`}>
              Lokalisasi Penuh
            </span>
          </button>
        </div>

        <p className="text-[11px] text-slate-500">
          {dictionary.onboarding.changeLater}
        </p>

        {/* Action Button */}
        <div className="pt-2 flex justify-end">
          <button
            type="button"
            onClick={dismissOnboarding}
            className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-semibold shadow-2xs transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-slate-900"
          >
            {dictionary.onboarding.confirm}
          </button>
        </div>
      </div>
    </div>
  );
};
