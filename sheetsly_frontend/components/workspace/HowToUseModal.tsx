'use client';

import React, { useEffect, useState } from 'react';
import { useTranslation } from '../../lib/i18n';

interface HowToUseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type GuideSection =
  | 'getting-started'
  | 'workflow'
  | 'ingestion'
  | 'dataset-profiling'
  | 'analysis-builder'
  | 'visualization'
  | 'ai-architecture'
  | 'ai-questions'
  | 'ai-results'
  | 'provenance'
  | 'troubleshooting';

export const HowToUseModal: React.FC<HowToUseModalProps> = ({ isOpen, onClose }) => {
  const { dictionary } = useTranslation();
  const [activeSection, setActiveSection] = useState<GuideSection>('getting-started');

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const secDict = dictionary.howToUse.sections;

  const sectionsList: { id: GuideSection; title: string }[] = [
    { id: 'getting-started', title: secDict.gettingStarted.navTitle },
    { id: 'workflow', title: secDict.workflow.navTitle },
    { id: 'ingestion', title: secDict.ingestion.navTitle },
    { id: 'dataset-profiling', title: secDict.datasetProfiling.navTitle },
    { id: 'analysis-builder', title: secDict.analysisBuilder.navTitle },
    { id: 'visualization', title: secDict.visualization.navTitle },
    { id: 'ai-architecture', title: secDict.aiArchitecture.navTitle },
    { id: 'ai-questions', title: secDict.aiQuestions.navTitle },
    { id: 'ai-results', title: secDict.aiResults.navTitle },
    { id: 'provenance', title: secDict.provenance.navTitle },
    { id: 'troubleshooting', title: secDict.troubleshooting.navTitle },
  ];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="how-to-use-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div className="bg-white w-full max-w-4xl max-h-[88vh] rounded-xl border border-slate-300 shadow-xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 rounded bg-slate-900 text-white flex items-center justify-center text-xs font-bold font-mono">
              ?
            </div>
            <div>
              <h2 id="how-to-use-title" className="text-sm font-bold text-slate-900">
                {dictionary.howToUse.title}
              </h2>
              <p className="text-xs text-slate-500">
                {dictionary.howToUse.subtitle}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close guide"
            className="p-1.5 text-slate-400 hover:text-slate-700 rounded-md hover:bg-slate-200/60 transition-colors cursor-pointer text-xs font-bold"
          >
            ✕
          </button>
        </div>

        {/* Modal Body: Sidebar Nav + Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Navigation Sidebar */}
          <nav aria-label="Guide sections" className="w-64 border-r border-slate-200 bg-slate-50/70 p-3 overflow-y-auto space-y-1">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2 py-1">
              {dictionary.howToUse.tocTitle}
            </div>
            {sectionsList.map((sec) => (
              <button
                key={sec.id}
                type="button"
                onClick={() => setActiveSection(sec.id)}
                className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer block ${
                  activeSection === sec.id
                    ? 'bg-slate-900 text-white font-semibold shadow-2xs'
                    : 'text-slate-600 hover:bg-slate-200/50 hover:text-slate-900'
                }`}
              >
                {sec.title}
              </button>
            ))}
          </nav>

          {/* Section Content Area */}
          <div className="flex-1 p-6 overflow-y-auto text-xs text-slate-700 space-y-4">
            {/* 1. Getting Started */}
            {activeSection === 'getting-started' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.gettingStarted.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.gettingStarted.body1}
                  </p>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                  <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px]">{secDict.gettingStarted.archTitle}</h4>
                  <p className="leading-relaxed font-bold text-slate-900">
                    {secDict.gettingStarted.archRule}
                  </p>
                  <p className="text-slate-600 leading-relaxed">
                    {secDict.gettingStarted.archDesc}
                  </p>
                </div>

                <div className="space-y-2">
                  <h4 className="font-bold text-slate-900 text-xs">{secDict.gettingStarted.formatsTitle}</h4>
                  <ul className="list-disc list-inside space-y-1 text-slate-600 pl-1">
                    <li>{secDict.gettingStarted.excelFormats}</li>
                    <li>{secDict.gettingStarted.csvFormats}</li>
                    <li>{secDict.gettingStarted.fileSizeLimit}</li>
                  </ul>
                </div>
              </div>
            )}

            {/* 2. Recommended Workflow */}
            {activeSection === 'workflow' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.workflow.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.workflow.intro}
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-2.5">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">{secDict.workflow.step1Title}</span>
                    <span className="text-slate-700">{secDict.workflow.step1Desc}</span>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">{secDict.workflow.step2Title}</span>
                    <span className="text-slate-700">{secDict.workflow.step2Desc}</span>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">{secDict.workflow.step3Title}</span>
                    <strong className="text-slate-900">{secDict.workflow.step3Desc}</strong>
                    <ul className="list-disc list-inside mt-1 text-slate-600 space-y-0.5 pl-2">
                      <li>{secDict.workflow.step3Ai}</li>
                      <li>{secDict.workflow.step3Builder}</li>
                    </ul>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">{secDict.workflow.step4Title}</span>
                    <span className="text-slate-700">{secDict.workflow.step4Desc}</span>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-mono font-bold text-slate-900 text-xs mr-2">{secDict.workflow.step5Title}</span>
                    <span className="text-slate-700">{secDict.workflow.step5Desc}</span>
                  </div>
                </div>
              </div>
            )}

            {/* 3. Upload & Ingestion */}
            {activeSection === 'ingestion' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.ingestion.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.ingestion.intro}
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded bg-slate-200 text-slate-800 font-mono font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">{secDict.ingestion.step1Title}</span>
                    <div>
                      <span className="text-slate-700">{secDict.ingestion.step1Desc}</span>
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded bg-slate-200 text-slate-800 font-mono font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">{secDict.ingestion.step2Title}</span>
                    <div>
                      <span className="text-slate-700">{secDict.ingestion.step2Desc}</span>
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded bg-slate-200 text-slate-800 font-mono font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">{secDict.ingestion.step3Title}</span>
                    <div>
                      <span className="text-slate-700">{secDict.ingestion.step3Desc}</span>
                    </div>
                  </div>
                  <div className="flex items-start space-x-2">
                    <span className="w-5 h-5 rounded bg-slate-200 text-slate-800 font-mono font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">{secDict.ingestion.step4Title}</span>
                    <div>
                      <span className="text-slate-700">{secDict.ingestion.step4Desc}</span>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                  <span className="font-bold text-slate-800 block mb-0.5">{secDict.ingestion.readyTitle}</span>
                  <p className="text-slate-600 leading-relaxed">
                    {secDict.ingestion.readyDesc}
                  </p>
                </div>
              </div>
            )}

            {/* 4. Tables & Schema Types */}
            {activeSection === 'dataset-profiling' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.datasetProfiling.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.datasetProfiling.intro}
                  </p>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
                      {secDict.datasetProfiling.measureTitle}
                    </span>
                    <p className="text-slate-700">{secDict.datasetProfiling.measureDesc}</p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-200 text-slate-800 border border-slate-300">
                      {secDict.datasetProfiling.categoryTitle}
                    </span>
                    <p className="text-slate-700">{secDict.datasetProfiling.categoryDesc}</p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-300">
                      {secDict.datasetProfiling.identifierTitle}
                    </span>
                    <p className="text-slate-700">{secDict.datasetProfiling.identifierDesc}</p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-900 border border-purple-300">
                      {secDict.datasetProfiling.temporalTitle}
                    </span>
                    <p className="text-slate-700">{secDict.datasetProfiling.temporalDesc}</p>
                  </div>
                </div>
              </div>
            )}

            {/* 5. Analysis Builder */}
            {activeSection === 'analysis-builder' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.analysisBuilder.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.analysisBuilder.intro}
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-1">{secDict.analysisBuilder.operationsTitle}</strong>
                    <ul className="grid grid-cols-2 gap-1 text-slate-600 font-mono text-[11px]">
                      <li>• SUM (Total)</li>
                      <li>• AVERAGE (Mean)</li>
                      <li>• COUNT_ROWS (Records)</li>
                      <li>• COUNT_VALUES (Non-nulls)</li>
                      <li>• DISTINCT_COUNT (Uniques)</li>
                      <li>• MIN / MAX (Extremes)</li>
                      <li>• MEDIAN (50th percentile)</li>
                      <li>• GROUP_BY (Dimensions)</li>
                      <li>• FILTER (Slice records)</li>
                      <li>• SORT / LIMIT (Rankings)</li>
                    </ul>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-1">{secDict.analysisBuilder.filterOpsTitle}</strong>
                    <p className="text-slate-600 leading-relaxed">
                      {secDict.analysisBuilder.filterOpsDesc}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 6. Visualizations */}
            {activeSection === 'visualization' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.visualization.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.visualization.intro}
                  </p>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-2">
                  <h4 className="font-bold text-slate-900 text-xs">{secDict.visualization.rulesTitle}</h4>
                  <ul className="list-disc list-inside space-y-1 text-slate-600">
                    <li>{secDict.visualization.pieRule}</li>
                    <li>{secDict.visualization.lineRule}</li>
                    <li>{secDict.visualization.scatterRule}</li>
                    <li>{secDict.visualization.histogramRule}</li>
                  </ul>
                </div>

                <p className="text-slate-600">
                  {secDict.visualization.footerNote}
                </p>
              </div>
            )}

            {/* 7. AI Architecture & Truth */}
            {activeSection === 'ai-architecture' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.aiArchitecture.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.aiArchitecture.intro}
                  </p>
                </div>

                <div className="p-4 bg-slate-900 text-white rounded-lg font-mono text-[11px] space-y-2">
                  <div className="text-slate-400 uppercase text-[10px] font-bold tracking-wider">{secDict.aiArchitecture.pipelineTitle}</div>
                  <div>{secDict.aiArchitecture.userStep}</div>
                  <div className="text-slate-400">{secDict.aiArchitecture.qwenStep}</div>
                  <div className="text-emerald-400">{secDict.aiArchitecture.jsonStep}</div>
                  <div className="text-slate-400">{secDict.aiArchitecture.guardrailStep}</div>
                  <div className="text-amber-400">{secDict.aiArchitecture.gateStep}</div>
                  <div className="text-slate-400">{secDict.aiArchitecture.pythonStep}</div>
                  <div className="text-blue-300">{secDict.aiArchitecture.calcStep}</div>
                  <div className="text-slate-400">{secDict.aiArchitecture.groundingStep}</div>
                  <div className="text-white">{secDict.aiArchitecture.resultStep}</div>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-1">
                  <strong className="text-slate-900">{secDict.aiArchitecture.whyMattersTitle}</strong>
                  <p className="text-slate-600 leading-relaxed">
                    {secDict.aiArchitecture.whyMattersDesc}
                  </p>
                </div>
              </div>
            )}

            {/* 8. Asking Good AI Questions */}
            {activeSection === 'ai-questions' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.aiQuestions.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.aiQuestions.intro}
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md">
                    <span className="font-bold text-emerald-900 block mb-1 text-[11px] uppercase">{secDict.aiQuestions.supportedTitle}</span>
                    <ul className="space-y-1 font-mono text-[11px] text-emerald-950">
                      <li>&bull; &ldquo;What is the total revenue?&rdquo; / &ldquo;Berapa total revenue?&rdquo; &rarr; SUM(Revenue)</li>
                      <li>&bull; &ldquo;Show average units sold by region&rdquo; / &ldquo;Tampilkan rata-rata unit per wilayah&rdquo; &rarr; GROUP_BY(Region) + AVG(Units)</li>
                      <li>&bull; &ldquo;What is total revenue in the North region?&rdquo; &rarr; SUM(Revenue) with FILTER(Region == &apos;North&apos;)</li>
                      <li>&bull; &ldquo;Find the top 5 products by revenue&rdquo; &rarr; GROUP_BY(Product) + SORT(DESC) + LIMIT(5)</li>
                    </ul>
                  </div>

                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-md">
                    <span className="font-bold text-amber-900 block mb-1 text-[11px] uppercase">{secDict.aiQuestions.ambiguousTitle}</span>
                    <p className="text-amber-950 mb-1">
                      {secDict.aiQuestions.ambiguousExample}
                    </p>
                    <p className="text-slate-600">
                      {secDict.aiQuestions.ambiguousDesc}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* 9. Understanding AI Results */}
            {activeSection === 'ai-results' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.aiResults.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.aiResults.intro}
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-bold text-slate-900 block">{secDict.aiResults.card1Title}</span>
                    <p className="text-slate-600">{secDict.aiResults.card1Desc}</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-bold text-slate-900 block">{secDict.aiResults.card2Title}</span>
                    <p className="text-slate-600">{secDict.aiResults.card2Desc}</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-bold text-slate-900 block">{secDict.aiResults.card3Title}</span>
                    <p className="text-slate-600">{secDict.aiResults.card3Desc}</p>
                  </div>
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <span className="font-bold text-slate-900 block">{secDict.aiResults.card4Title}</span>
                    <p className="text-slate-600">{secDict.aiResults.card4Desc}</p>
                  </div>
                </div>
              </div>
            )}

            {/* 10. Data Provenance & Evidence */}
            {activeSection === 'provenance' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.provenance.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.provenance.intro}
                  </p>
                </div>

                <div className="p-3 bg-slate-50 border border-slate-200 rounded-md space-y-2 font-mono text-[11px]">
                  <div className="text-slate-500 font-bold uppercase text-[10px]">{secDict.provenance.sampleTitle}</div>
                  <div>{secDict.provenance.sampleRange}</div>
                  <div>{secDict.provenance.sampleRows}</div>
                  <div>{secDict.provenance.sampleFilters}</div>
                  <div>{secDict.provenance.sampleDuration}</div>
                </div>

                <p className="text-slate-600 leading-relaxed">
                  {secDict.provenance.guaranteeDesc}
                </p>
              </div>
            )}

            {/* 11. Troubleshooting */}
            {activeSection === 'troubleshooting' && (
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-bold text-slate-900">{secDict.troubleshooting.heading}</h3>
                  <p className="text-slate-600 mt-1 leading-relaxed">
                    {secDict.troubleshooting.intro}
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-0.5">{secDict.troubleshooting.offlineTitle}</strong>
                    <p className="text-slate-600">
                      {secDict.troubleshooting.offlineDesc}
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-0.5">{secDict.troubleshooting.blockedTitle}</strong>
                    <p className="text-slate-600">
                      {secDict.troubleshooting.blockedDesc}
                    </p>
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-md">
                    <strong className="text-slate-900 block mb-0.5">{secDict.troubleshooting.largeTitle}</strong>
                    <p className="text-slate-600">
                      {secDict.troubleshooting.largeDesc}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <div className="text-[11px] text-slate-500 font-mono">
            {dictionary.howToUse.footerText}
          </div>

          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-xs font-semibold shadow-2xs cursor-pointer transition-colors"
          >
            {dictionary.howToUse.returnButton}
          </button>
        </div>
      </div>
    </div>
  );
};
