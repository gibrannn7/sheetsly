'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { en } from './translations/en';
import { id } from './translations/id';
import { SupportedLanguage, TranslationDictionary } from './types';

const STORAGE_KEY = 'sheetsly_language';
const ONBOARDED_KEY = 'sheetsly_onboarded_lang';

interface LanguageContextType {
  language: SupportedLanguage;
  setLanguage: (lang: SupportedLanguage) => void;
  dictionary: TranslationDictionary;
  t: (keyPath: string, params?: Record<string, string | number>) => string;
  showOnboarding: boolean;
  dismissOnboarding: () => void;
}

const dictionaries: Record<SupportedLanguage, TranslationDictionary> = {
  en,
  id,
};

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<SupportedLanguage>('en');
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);
  const [isMounted, setIsMounted] = useState<boolean>(false);

  useEffect(() => {
    setIsMounted(true);
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      const hasOnboarded = localStorage.getItem(ONBOARDED_KEY);

      if (stored === 'en' || stored === 'id') {
        setLanguageState(stored);
      } else {
        // First time visitor: show onboarding
        if (!hasOnboarded) {
          setShowOnboarding(true);
        }
      }
    } catch {
      // LocalStorage unavailable (e.g. private mode or SSR)
    }
  }, []);

  const setLanguage = (lang: SupportedLanguage) => {
    setLanguageState(lang);
    try {
      localStorage.setItem(STORAGE_KEY, lang);
      localStorage.setItem(ONBOARDED_KEY, 'true');
    } catch {}
  };

  const dismissOnboarding = () => {
    setShowOnboarding(false);
    try {
      localStorage.setItem(ONBOARDED_KEY, 'true');
    } catch {}
  };

  const dictionary = dictionaries[language] || dictionaries.en;

  /**
   * Helper to retrieve nested translated string by dotted key path (e.g. 'common.openAnotherFile')
   * with optional parameter interpolation (e.g. { page: 1, totalPages: 5 })
   */
  const t = (keyPath: string, params?: Record<string, string | number>): string => {
    const keys = keyPath.split('.');
    let current: any = dictionary;

    for (const key of keys) {
      if (current && typeof current === 'object' && key in current) {
        current = current[key];
      } else {
        // Fallback to English dictionary
        let fallback: any = dictionaries.en;
        for (const fKey of keys) {
          if (fallback && typeof fallback === 'object' && fKey in fallback) {
            fallback = fallback[fKey];
          } else {
            return keyPath;
          }
        }
        current = fallback;
        break;
      }
    }

    if (typeof current !== 'string') {
      return keyPath;
    }

    if (params) {
      let result = current;
      for (const [pKey, pVal] of Object.entries(params)) {
        result = result.replaceAll(`{${pKey}}`, String(pVal));
      }
      return result;
    }

    return current;
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        dictionary,
        t,
        showOnboarding: isMounted ? showOnboarding : false,
        dismissOnboarding,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export const useTranslation = () => {
  const { language, setLanguage, dictionary, t, showOnboarding, dismissOnboarding } = useLanguage();
  return { language, setLanguage, dictionary, t, showOnboarding, dismissOnboarding };
};
