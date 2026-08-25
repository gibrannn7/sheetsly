'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';

interface LanguageSwitcherProps {
  className?: string;
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({ className = '' }) => {
  const { language, setLanguage } = useTranslation();

  return (
    <div
      role="group"
      aria-label="Language selection"
      className={`inline-flex items-center p-0.5 bg-slate-100 border border-slate-300 rounded-md text-xs font-mono shadow-2xs ${className}`}
    >
      <button
        type="button"
        onClick={() => setLanguage('en')}
        aria-pressed={language === 'en'}
        aria-label="Switch language to English"
        className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-slate-900 ${
          language === 'en'
            ? 'bg-slate-900 text-white shadow-2xs'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
        }`}
      >
        EN
      </button>

      <button
        type="button"
        onClick={() => setLanguage('id')}
        aria-pressed={language === 'id'}
        aria-label="Ganti bahasa ke Bahasa Indonesia"
        className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-slate-900 ${
          language === 'id'
            ? 'bg-slate-900 text-white shadow-2xs'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
        }`}
      >
        ID
      </button>
    </div>
  );
};
