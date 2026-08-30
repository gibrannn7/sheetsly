'use client';

import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from '../../lib/i18n';
import { AIModelOption } from '../../lib/types';

export const FALLBACK_AI_MODELS: AIModelOption[] = [
  { id: 'gemini-3.1-flash-lite', label: 'Gemini 3.1 Flash Lite', provider: 'gemini', provider_label: 'Google Gemini', is_default: true },
  { id: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', provider: 'gemini', provider_label: 'Google Gemini' },
  { id: 'gemini-3.5-flash-lite', label: 'Gemini 3.5 Flash Lite', provider: 'gemini', provider_label: 'Google Gemini' },
  { id: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash', provider: 'gemini', provider_label: 'Google Gemini' },
  { id: 'gemini-3.6-flash', label: 'Gemini 3.6 Flash', provider: 'gemini', provider_label: 'Google Gemini' },
  { id: 'qwen3.5-122b-a10b', label: 'Qwen 3.5 122B', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.5-flash', label: 'Qwen 3.5 Flash', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.6-plus', label: 'Qwen 3.6 Plus', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.7-plus', label: 'Qwen 3.7 Plus', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.6-flash', label: 'Qwen 3.6 Flash', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'qwen3.7-flash', label: 'Qwen 3.7 Flash', provider: 'qwen', provider_label: 'Qwen' },
  { id: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash', provider: 'deepseek', provider_label: 'DeepSeek' },
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
  const [mounted, setMounted] = useState(false);
  const [coords, setCoords] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const models = availableModels && availableModels.length > 0 ? availableModels : FALLBACK_AI_MODELS;
  const currentModel = models.find((m) => m.id === value) || models[0];

  // Group models by provider
  const groups: { [key: string]: { label: string; models: AIModelOption[] } } = {};
  models.forEach((m) => {
    // Strictly filter out retired qwen3.5-plus
    if (m.id === 'qwen3.5-plus') return;
    let groupKey = m.provider || 'qwen';
    let groupLabel = m.provider_label || (groupKey === 'gemini' ? 'Google Gemini' : groupKey === 'deepseek' ? 'DeepSeek' : 'Qwen');
    if (!groups[groupKey]) {
      groups[groupKey] = { label: groupLabel, models: [] };
    }
    groups[groupKey].models.push(m);
  });

  const updateCoords = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const popoverWidth = 260;
      let left = rect.right - popoverWidth;
      if (left < 8) left = 8;
      if (left + popoverWidth > window.innerWidth - 8) {
        left = window.innerWidth - popoverWidth - 8;
      }
      setCoords({
        top: rect.bottom + 4,
        left,
      });
    }
  };

  const toggleDropdown = () => {
    if (disabled) return;
    if (!isOpen) {
      updateCoords();
    }
    setIsOpen((prev) => !prev);
  };

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        buttonRef.current &&
        !buttonRef.current.contains(target) &&
        popoverRef.current &&
        !popoverRef.current.contains(target)
      ) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      window.addEventListener('resize', updateCoords);
      window.addEventListener('scroll', updateCoords, true);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('resize', updateCoords);
      window.removeEventListener('scroll', updateCoords, true);
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
    <div className="relative inline-block text-left">
      {/* Trigger Button */}
      <button
        ref={buttonRef}
        type="button"
        disabled={disabled}
        onClick={toggleDropdown}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={dictionary.modelSelector.selectModel}
        title={`Selected Model: ${currentModel.id}`}
        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-mono font-medium transition-colors cursor-pointer border ${
          isOpen
            ? 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-slate-100 border-slate-400 dark:border-slate-600 ring-1 ring-slate-400/30'
            : 'bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-300 dark:border-slate-700 shadow-2xs'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''} focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-400`}
      >
        <span className="font-semibold text-slate-900 dark:text-slate-100 truncate max-w-[150px] sm:max-w-[180px]">
          {currentModel.id}
        </span>
        <svg
          className={`w-3 h-3 text-slate-500 dark:text-slate-400 shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Popover Dropdown Portal (Rendered directly under document.body with z-[99999] so nothing clips it) */}
      {mounted &&
        isOpen &&
        createPortal(
          <div
            ref={popoverRef}
            role="listbox"
            aria-label={dictionary.modelSelector.selectModel}
            style={{
              position: 'fixed',
              top: `${coords.top}px`,
              left: `${coords.left}px`,
              width: '260px',
            }}
            className="rounded-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl py-1 z-[99999] focus:outline-none animate-in fade-in zoom-in-95 duration-100 max-h-80 overflow-y-auto"
          >
            <div className="px-3 py-1.5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <p className="text-[10px] uppercase tracking-wider font-bold text-slate-500 dark:text-slate-400 font-mono">
                {dictionary.modelSelector.selectModel}
              </p>
              <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                {models.filter((m) => m.id !== 'qwen3.5-plus').length} Models
              </span>
            </div>
            <div className="py-1 divide-y divide-slate-100 dark:divide-slate-800">
              {Object.entries(groups).map(([groupKey, group]) => (
                <div key={groupKey} className="py-1">
                  <div className="px-3 py-1 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider font-mono">
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
                        className={`w-full text-left px-3 py-1.5 text-xs font-mono flex items-center justify-between transition-colors cursor-pointer ${
                          isSelected
                            ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-semibold'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                        }`}
                      >
                        <div className="flex items-center gap-1.5 truncate">
                          <span className="truncate">{model.id}</span>
                          {model.is_default && (
                            <span
                              className={`text-[9px] px-1 py-0.2 rounded font-semibold ${
                                isSelected
                                  ? 'bg-slate-800 text-slate-200 dark:bg-slate-200 dark:text-slate-800'
                                  : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700'
                              }`}
                            >
                              default
                            </span>
                          )}
                        </div>
                        {isSelected && <span className="text-xs font-bold shrink-0 ml-1.5">✓</span>}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
            <div className="px-2.5 py-1.5 border-t border-slate-100 dark:border-slate-800 text-[10px] text-slate-400 dark:text-slate-500 font-mono">
              AI interprets intent. Python calculates truth.
            </div>
          </div>,
          document.body
        )}
    </div>
  );
};
