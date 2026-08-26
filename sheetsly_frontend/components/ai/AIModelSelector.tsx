'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useTranslation } from '../../lib/i18n';
import { AIModelOption } from '../../lib/types';

export const FALLBACK_AI_MODELS: AIModelOption[] = [
  { id: 'qwen3.5-397b-a17b', label: 'Qwen 3.5 397B', provider: 'qwen', provider_label: 'Qwen', is_default: true },
  { id: 'qwen3.5-flash', label: 'Qwen 3.5 Flash', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.6-plus', label: 'Qwen 3.6 Plus', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.7-plus', label: 'Qwen 3.7 Plus', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.6-flash', label: 'Qwen 3.6 Flash', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.7-flash', label: 'Qwen 3.7 Flash', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash', provider: 'deepseek', provider_label: 'DeepSeek' },
  { id: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', provider: 'gemini', provider_label: 'Google Gemini' },
  { id: 'gemini-3.1-flash-lite', label: 'Gemini 3.1 Flash Lite', provider: 'gemini', provider_label: 'Google Gemini' },
  { id: 'gemini-3.5-flash-lite', label: 'Gemini 3.5 Flash Lite', provider: 'gemini', provider_label: 'Google Gemini' },
  { id: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash', provider: 'gemini', provider_label: 'Google Gemini' },
  { id: 'gemini-3.6-flash', label: 'Gemini 3.6 Flash', provider: 'gemini', provider_label: 'Google Gemini' },
];

interface AIModelSelectorProps {
  value: string;
  onChange: (modelId: string) => void;
  availableModels?: AIModelOption[];
  disabled?: boolean;
}

export const AIModelSelector: React.FC<AIModelSelectorProps> = ({
  value,
  onChange,
  availableModels,
  disabled = false,
}) => {
  const { dictionary } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const models = availableModels && availableModels.length > 0 ? availableModels : FALLBACK_AI_MODELS;
  const currentModel = models.find((m) => m.id === value) || models[0];

  // Group models by provider
  const groups: { [key: string]: { label: string; models: AIModelOption[] } } = {};
  models.forEach((m) => {
    let groupKey = m.provider || 'qwen';
    let groupLabel = m.provider_label || (groupKey === 'gemini' ? 'Google Gemini' : groupKey === 'deepseek' ? 'DeepSeek' : 'Qwen');
    if (!groups[groupKey]) {
      groups[groupKey] = { label: groupLabel, models: [] };
    }
    groups[groupKey].models.push(m);
  });

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  return (
    <div className="relative inline-block text-left" ref={containerRef}>
      {/* Trigger Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={dictionary.modelSelector.selectModel}
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium transition-colors cursor-pointer border ${
          isOpen
            ? 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-400 dark:border-slate-600 ring-2 ring-slate-400/20'
            : 'bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-300 dark:border-slate-700 shadow-2xs'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''} focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-slate-400`}
      >
        <span className="font-semibold text-slate-900 dark:text-slate-100">{currentModel.id}</span>
        {currentModel.badge && (
          <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-semibold border border-slate-200 dark:border-slate-700">
            {currentModel.badge}
          </span>
        )}
        <svg
          className={`w-3 h-3 text-slate-500 dark:text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Popover Dropdown */}
      {isOpen && (
        <div
          role="listbox"
          aria-label={dictionary.modelSelector.selectModel}
          className="absolute right-0 mt-1 w-60 rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg py-1 z-50 focus:outline-hidden animate-in fade-in zoom-in-95 duration-100 max-h-80 overflow-y-auto"
        >
          <div className="px-2.5 py-1.5 border-b border-slate-100 dark:border-slate-800">
            <p className="text-[10px] uppercase tracking-wider font-bold text-slate-500 dark:text-slate-400 font-mono">
              {dictionary.modelSelector.selectModel}
            </p>
          </div>
          <div className="py-1 divide-y divide-slate-100 dark:divide-slate-800">
            {Object.entries(groups).map(([groupKey, group]) => (
              <div key={groupKey} className="py-1">
                <div className="px-2.5 py-1 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider font-mono">
                  {group.label}
                </div>
                {group.models.map((model) => {
                  const isSelected = model.id === currentModel.id;
                  return (
                    <button
                      key={model.id}
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => {
                        onChange(model.id);
                        setIsOpen(false);
                      }}
                      className={`w-full text-left px-2.5 py-1.5 text-xs font-mono flex items-center justify-between transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-semibold'
                          : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                      }`}
                    >
                      <div className="flex items-center space-x-1.5">
                        <span>{model.label}</span>
                        {model.badge && (
                          <span
                            className={`text-[9px] px-1 py-0.2 rounded font-semibold ${
                              isSelected
                                ? 'bg-slate-800 dark:bg-slate-200 text-white dark:text-slate-900'
                                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                            }`}
                          >
                            {model.badge}
                          </span>
                        )}
                      </div>
                      {isSelected && (
                        <svg className="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </button>
                  );
                })}
              </div>
            ))}
          </div>
          <div className="px-2.5 py-1.5 border-t border-slate-100 dark:border-slate-800 text-[10px] text-slate-400 dark:text-slate-500 font-mono">
            AI interprets intent. Python calculates truth.
          </div>
        </div>
      )}
    </div>
  );
};
