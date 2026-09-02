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
      className={`inline-flex items-center h-8 p-0.5 bg-zinc-900/90 border border-zinc-800 rounded-md text-xs font-mono select-none shadow-xs transition-colors ${className}`}
    >
      <button
        type="button"
        onClick={() => setLanguage('en')}
        aria-pressed={language === 'en'}
        aria-label="Switch language to English"
        className={`h-full inline-flex items-center px-2 rounded text-[11px] font-semibold transition-all cursor-pointer ${
          language === 'en'
            ? 'bg-zinc-800 text-white shadow-2xs'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        EN
      </button>

      <button
        type="button"
        onClick={() => setLanguage('id')}
        aria-pressed={language === 'id'}
        aria-label="Ganti bahasa ke Bahasa Indonesia"
        className={`h-full inline-flex items-center px-2 rounded text-[11px] font-semibold transition-all cursor-pointer ${
          language === 'id'
            ? 'bg-zinc-800 text-white shadow-2xs'
            : 'text-zinc-400 hover:text-zinc-200'
        }`}
      >
        ID
      </button>
    </div>
  );
};
