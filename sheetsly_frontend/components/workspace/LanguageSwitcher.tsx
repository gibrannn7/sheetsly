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
      className={`inline-flex items-center h-7 p-0.5 bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md text-xs font-mono select-none shadow-2xs transition-colors ${className}`}
    >
      <button
        type="button"
        onClick={() => setLanguage('en')}
        aria-pressed={language === 'en'}
        aria-label="Switch language to English"
        className={`h-full inline-flex items-center px-1.5 rounded text-[11px] font-bold transition-all cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400 ${
          language === 'en'
            ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
            : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
        }`}
      >
        EN
      </button>

      <button
        type="button"
        onClick={() => setLanguage('id')}
        aria-pressed={language === 'id'}
        aria-label="Ganti bahasa ke Bahasa Indonesia"
        className={`h-full inline-flex items-center px-1.5 rounded text-[11px] font-bold transition-all cursor-pointer focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400 ${
          language === 'id'
            ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
            : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
        }`}
      >
        ID
      </button>
    </div>
  );
};
