'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';

export const LandingArchitectureFlow: React.FC = () => {
  const { dictionary } = useTranslation();
  const t = dictionary.landing.architecture;

  const stages = [
    {
      num: '01',
      title: t.stage1Title,
      desc: t.stage1Desc,
      tag: 'Input',
    },
    {
      num: '02',
      title: t.stage2Title,
      desc: t.stage2Desc,
      tag: 'AST Plan',
    },
    {
      num: '03',
      title: t.stage3Title,
      desc: t.stage3Desc,
      tag: 'Python Matrix',
    },
    {
      num: '04',
      title: t.stage4Title,
      desc: t.stage4Desc,
      tag: 'Safety Gate',
    },
    {
      num: '05',
      title: t.stage5Title,
      desc: t.stage5Desc,
      tag: 'Lineage & Audit',
    },
  ];

  return (
    <div className="w-full space-y-8">
      {/* Principle Callout */}
      <div className="p-6 md:p-8 rounded-xl bg-[#0d0f14] text-white border border-zinc-800 space-y-3">
        <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400">
          Core Architectural Separation
        </div>
        <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-white font-sans leading-snug">
          {t.ruleQuote}
        </h3>
        <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed font-sans max-w-3xl">
          {t.whyDesc}
        </p>
      </div>

      {/* Stepped Sequential Pipeline */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5">
        {stages.map((stage) => (
          <div
            key={stage.num}
            className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 flex flex-col justify-between space-y-3"
          >
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-zinc-500">
                  {stage.num}
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-900 text-zinc-400 border border-zinc-800">
                  {stage.tag}
                </span>
              </div>

              <h4 className="text-xs font-bold text-zinc-100 leading-snug">
                {stage.title}
              </h4>

              <p className="text-[11px] text-zinc-400 leading-relaxed">
                {stage.desc}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* 3 Core Architecture Pillars */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5">
          <div className="text-xs font-bold text-zinc-200">
            {t.pillar1}
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            {t.pillar1Desc}
          </p>
        </div>

        <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5">
          <div className="text-xs font-bold text-zinc-200">
            {t.pillar2}
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            {t.pillar2Desc}
          </p>
        </div>

        <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5">
          <div className="text-xs font-bold text-zinc-200">
            {t.pillar3}
          </div>
          <p className="text-xs text-zinc-400 leading-relaxed">
            {t.pillar3Desc}
          </p>
        </div>
      </div>
    </div>
  );
};
