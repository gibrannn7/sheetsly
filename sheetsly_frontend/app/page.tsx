'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { SpreadsheetUploader } from '../components/upload/SpreadsheetUploader';
import { WorkbookHeader } from '../components/workspace/WorkbookHeader';
import { SheetList } from '../components/workspace/SheetList';
import { DetectedTablesViewer } from '../components/workspace/DetectedTablesViewer';
import { ActualDataViewer } from '../components/workspace/ActualDataViewer';
import { DataQualityPanel } from '../components/workspace/DataQualityPanel';
import { VisualizationViewer } from '../components/workspace/VisualizationViewer';
import { OperationBuilder } from '../components/builder/OperationBuilder';
import { AIQueryWorkspace } from '../components/ai/AIQueryWorkspace';
import { HowToUseModal } from '../components/workspace/HowToUseModal';
import { LanguageSwitcher } from '../components/workspace/LanguageSwitcher';
import { ThemeSwitcher } from '../components/workspace/ThemeSwitcher';
import { LanguageOnboardingModal } from '../components/workspace/LanguageOnboardingModal';
import { LandingProductShowcase } from '../components/landing/LandingProductShowcase';
import { LandingArchitectureFlow } from '../components/landing/LandingArchitectureFlow';
import { LandingExamplesSection } from '../components/landing/LandingExamplesSection';
import { useTranslation } from '../lib/i18n';
import { useWorkspace } from '../lib/workspace/WorkspaceContext';
import { WorkbookOverview } from '../lib/types';

export default function Home() {
  const { dictionary } = useTranslation();
  const router = useRouter();
  const {
    overview,
    activeSheetName,
    activeViewMode,
    setOverview,
    setActiveSheetName,
    setActiveViewMode,
    resetWorkspace,
  } = useWorkspace();

  const [isHelpOpen, setIsHelpOpen] = useState<boolean>(false);

  const handleUploadSuccess = (data: WorkbookOverview) => {
    setOverview(data);
    if (data.sheets.length > 0) {
      setActiveSheetName(data.sheets[0].name);
    }
    // Update route to active session for shareable/refreshable URL
    router.push(`/workspace/${data.dataset_id}`);
  };

  const handleReset = () => {
    resetWorkspace();
  };

  const scrollToUpload = () => {
    const el = document.getElementById('upload-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const currentSheet = overview?.sheets.find((s) => s.name === activeSheetName) || overview?.sheets[0];
  const land = dictionary.landing;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors selection:bg-slate-200 dark:selection:bg-slate-800">
      {!overview ? (
        // Restrained, Product-First Landing Page
        <div className="flex-1 flex flex-col w-full">
          {/* Top Sticky Navigation Bar */}
          <header className="sticky top-0 z-40 w-full border-b border-slate-200/80 dark:border-slate-800/80 bg-white/90 dark:bg-slate-950/90 backdrop-blur-sm transition-colors">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
              {/* Logo + App Name */}
              <a href="#" className="flex items-center space-x-2.5">
                <img
                  src="/assets/logo.png"
                  alt="Sheetsly Logo"
                  className="w-7 h-7 object-contain rounded"
                />
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                    {dictionary.common.appName}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 px-1 py-0.2 rounded">
                    v1.0
                  </span>
                </div>
              </a>

              {/* 3 Clean Anchor Navigation Links */}
              <nav className="hidden md:flex items-center space-x-6 text-xs font-medium text-slate-600 dark:text-slate-400">
                <a href="#workbench" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  {land.nav.showcase}
                </a>
                <a href="#workflow" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  {land.nav.workflow}
                </a>
                <a href="#architecture" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  {land.nav.architecture}
                </a>
                <a href="#agent" className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors">
                  {land.nav.agent}
                </a>
              </nav>

              {/* Right Controls */}
              <div className="flex items-center gap-2">
                <ThemeSwitcher />
                <LanguageSwitcher />

                <button
                  type="button"
                  onClick={() => setIsHelpOpen(true)}
                  aria-label={dictionary.nav.howToUse}
                  className="h-7 px-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors cursor-pointer hidden sm:inline-block"
                >
                  {dictionary.nav.howToUse}
                </button>

                <button
                  type="button"
                  onClick={scrollToUpload}
                  className="h-7 px-3 inline-flex items-center justify-center text-xs font-semibold text-white bg-slate-900 dark:bg-slate-100 dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-white rounded transition-colors cursor-pointer whitespace-nowrap"
                >
                  {land.nav.tryApp}
                </button>
              </div>
            </div>
          </header>

          {/* Main Content Area */}
          <main className="flex-1 max-w-6xl mx-auto px-4 sm:px-6 w-full space-y-20 sm:space-y-24 py-10 sm:py-14">
            {/* Hero Section */}
            <section className="text-center space-y-6 max-w-3xl mx-auto pt-2">
              <div className="text-[11px] font-mono font-semibold uppercase tracking-widest text-slate-500 dark:text-slate-400">
                SPREADSHEET INTELLIGENCE WORKSPACE
              </div>

              <h1 className="text-3xl sm:text-5xl font-bold text-slate-900 dark:text-slate-100 tracking-tight leading-[1.15]">
                {land.hero.title} {land.hero.titleHighlight}
              </h1>

              <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed">
                {land.hero.subtitle}
              </p>

              {/* Hero CTAs */}
              <div className="flex items-center justify-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={scrollToUpload}
                  className="px-4 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs sm:text-sm font-semibold rounded hover:bg-slate-800 dark:hover:bg-white transition-colors cursor-pointer"
                >
                  {land.hero.primaryCta}
                </button>
                <button
                  type="button"
                  onClick={() => setIsHelpOpen(true)}
                  className="px-4 py-2 text-slate-700 dark:text-slate-300 text-xs sm:text-sm font-medium hover:text-slate-900 dark:hover:text-slate-100 transition-colors cursor-pointer"
                >
                  {land.hero.secondaryCta}
                </button>
              </div>

              {/* Dropzone Container */}
              <div id="upload-section" className="pt-4 scroll-mt-20 max-w-xl mx-auto">
                <SpreadsheetUploader onUploadSuccess={handleUploadSuccess} />
                <div className="flex items-center justify-center space-x-3 pt-3 text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                  <span>{land.hero.noHallucination}</span>
                  <span>•</span>
                  <span>{land.hero.instantUndo}</span>
                  <span>•</span>
                  <span>{land.hero.cellTraceability}</span>
                </div>
              </div>
            </section>

            {/* Product Workbench (Dominant Visual Proof) */}
            <section id="workbench" className="space-y-4 scroll-mt-20">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                  {land.showcase.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                  {land.showcase.title}
                </h2>
                <p className="text-xs text-slate-600 dark:text-slate-400 max-w-2xl">
                  {land.showcase.subtitle}
                </p>
              </div>

              <LandingProductShowcase />
            </section>

            {/* Problem / Solution Narrative */}
            <section id="problem-solution" className="space-y-6 scroll-mt-20">
              <div className="p-6 sm:p-8 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
                  {/* Left: Problem Statement & Frictions */}
                  <div className="md:col-span-7 space-y-4">
                    <div className="space-y-1">
                      <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                        {land.problemSolution.badge}
                      </div>
                      <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                        {land.problemSolution.problemTitle}
                      </h2>
                      <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                        {land.problemSolution.problemDesc}
                      </p>
                    </div>

                    <div className="space-y-2.5 pt-2">
                      <div className="text-xs text-slate-700 dark:text-slate-300">
                        <strong className="text-slate-900 dark:text-slate-100">{land.problemSolution.friction1Title}:</strong> {land.problemSolution.friction1Desc}
                      </div>
                      <div className="text-xs text-slate-700 dark:text-slate-300">
                        <strong className="text-slate-900 dark:text-slate-100">{land.problemSolution.friction2Title}:</strong> {land.problemSolution.friction2Desc}
                      </div>
                      <div className="text-xs text-slate-700 dark:text-slate-300">
                        <strong className="text-slate-900 dark:text-slate-100">{land.problemSolution.friction3Title}:</strong> {land.problemSolution.friction3Desc}
                      </div>
                      <div className="text-xs text-slate-700 dark:text-slate-300">
                        <strong className="text-slate-900 dark:text-slate-100">{land.problemSolution.friction4Title}:</strong> {land.problemSolution.friction4Desc}
                      </div>
                    </div>
                  </div>

                  {/* Right: Solution Loop */}
                  <div className="md:col-span-5 p-5 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-3">
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100">
                      {land.problemSolution.solutionTitle}
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                      {land.problemSolution.solutionDesc}
                    </p>

                    <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs font-mono text-slate-700 dark:text-slate-300">
                      <span>1. {land.problemSolution.loopUnderstand}</span>
                      <span>&rarr;</span>
                      <span>2. {land.problemSolution.loopAnalyze}</span>
                      <span>&rarr;</span>
                      <span>3. {land.problemSolution.loopAct}</span>
                      <span>&rarr;</span>
                      <span>4. {land.problemSolution.loopVerify}</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* How It Works (Sequential 01 to 05 Process) */}
            <section id="workflow" className="space-y-6 scroll-mt-20">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                  {land.howItWorks.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                  {land.howItWorks.title}
                </h2>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {land.howItWorks.subtitle}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5">
                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
                  <span className="font-mono text-xs font-bold text-slate-400 dark:text-slate-500">01</span>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.howItWorks.step1Title}</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{land.howItWorks.step1Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
                  <span className="font-mono text-xs font-bold text-slate-400 dark:text-slate-500">02</span>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.howItWorks.step2Title}</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{land.howItWorks.step2Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
                  <span className="font-mono text-xs font-bold text-slate-400 dark:text-slate-500">03</span>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.howItWorks.step3Title}</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{land.howItWorks.step3Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
                  <span className="font-mono text-xs font-bold text-slate-400 dark:text-slate-500">04</span>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.howItWorks.step4Title}</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{land.howItWorks.step4Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
                  <span className="font-mono text-xs font-bold text-slate-400 dark:text-slate-500">05</span>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.howItWorks.step5Title}</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">{land.howItWorks.step5Desc}</p>
                </div>
              </div>
            </section>

            {/* Architecture Section */}
            <section id="architecture" className="space-y-6 scroll-mt-20">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                  {land.architecture.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                  {land.architecture.title}
                </h2>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {land.architecture.subtitle}
                </p>
              </div>

              <LandingArchitectureFlow />
            </section>

            {/* Agent Differentiation (Asymmetric Layout) */}
            <section id="agent" className="space-y-6 scroll-mt-20">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
                <div className="md:col-span-5 space-y-3">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                    {land.agent.badge}
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                    {land.agent.title}
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                    {land.agent.subtitle}
                  </p>
                </div>

                <div className="md:col-span-7 space-y-3">
                  <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.agent.p1Title}</div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{land.agent.p1Desc}</p>
                    <div className="text-[11px] font-mono text-slate-500 pt-1">{land.agent.p1Detail}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.agent.p2Title}</div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{land.agent.p2Desc}</p>
                    <div className="text-[11px] font-mono text-slate-500 pt-1">{land.agent.p2Detail}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.agent.p3Title}</div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{land.agent.p3Desc}</p>
                    <div className="text-[11px] font-mono text-slate-500 pt-1">{land.agent.p3Detail}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.agent.p4Title}</div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{land.agent.p4Desc}</p>
                    <div className="text-[11px] font-mono text-slate-500 pt-1">{land.agent.p4Detail}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100">{land.agent.p5Title}</div>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{land.agent.p5Desc}</p>
                    <div className="text-[11px] font-mono text-slate-500 pt-1">{land.agent.p5Detail}</div>
                  </div>
                </div>
              </div>
            </section>

            {/* Real Product Examples */}
            <section id="examples" className="space-y-6 scroll-mt-20">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                  {land.examples.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                  {land.examples.title}
                </h2>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {land.examples.subtitle}
                </p>
              </div>

              <LandingExamplesSection />
            </section>

            {/* Capabilities & Business Use Cases (Structured Matrix) */}
            <section id="capabilities" className="space-y-6 scroll-mt-20">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500">
                  {land.capabilities.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                  {land.capabilities.title}
                </h2>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  {land.capabilities.subtitle}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1.5">
                  <div className="font-bold text-xs text-slate-900 dark:text-slate-100">{land.capabilities.f1Title}</div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{land.capabilities.f1Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1.5">
                  <div className="font-bold text-xs text-slate-900 dark:text-slate-100">{land.capabilities.f2Title}</div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{land.capabilities.f2Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1.5">
                  <div className="font-bold text-xs text-slate-900 dark:text-slate-100">{land.capabilities.f3Title}</div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{land.capabilities.f3Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1.5">
                  <div className="font-bold text-xs text-slate-900 dark:text-slate-100">{land.capabilities.f4Title}</div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{land.capabilities.f4Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1.5">
                  <div className="font-bold text-xs text-slate-900 dark:text-slate-100">{land.capabilities.f5Title}</div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{land.capabilities.f5Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1.5">
                  <div className="font-bold text-xs text-slate-900 dark:text-slate-100">{land.capabilities.f6Title}</div>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{land.capabilities.f6Desc}</p>
                </div>
              </div>
            </section>

            {/* Final Action Bar */}
            <section className="p-6 sm:p-8 rounded-xl bg-slate-900 dark:bg-slate-950 text-white border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-1 max-w-xl">
                <h2 className="text-lg sm:text-xl font-bold tracking-tight text-white">
                  {land.cta.title}
                </h2>
                <p className="text-xs text-slate-300">
                  {land.cta.subtitle}
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
                <button
                  type="button"
                  onClick={scrollToUpload}
                  className="px-4 py-2 bg-white text-slate-900 text-xs font-semibold rounded hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  {land.cta.button} &uarr;
                </button>
              </div>
            </section>
          </main>

          {/* Quiet Technical Footer */}
          <footer className="w-full border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 py-8 transition-colors">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500 dark:text-slate-400">
              <div className="flex items-center space-x-2">
                <img
                  src="/assets/logo.png"
                  alt="Sheetsly Logo"
                  className="w-5 h-5 object-contain rounded"
                />
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {dictionary.common.appName}
                </span>
                <span>—</span>
                <span className="text-[11px]">{land.footer.tagline}</span>
              </div>

              <div className="text-center md:text-right space-y-0.5 font-mono text-[10px]">
                <div>{land.footer.privacyNote}</div>
                <div className="text-slate-400 dark:text-slate-600">
                  &copy; 2026 {land.footer.rights}
                </div>
              </div>
            </div>
          </footer>
        </div>
      ) : (
        // Active Workspace Screen (Preserved Completely)
        <div className="flex-1 flex flex-col">
          <WorkbookHeader overview={overview} onReset={handleReset} />

          <SheetList
            sheets={overview.sheets}
            activeSheetName={activeSheetName || overview.sheets[0]?.name || ''}
            onSelectSheet={(name) => setActiveSheetName(name)}
          />

          {/* View Mode Navigation Bar */}
          <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-2 flex items-center justify-between gap-3 overflow-x-auto transition-colors">
            <div className="flex items-center gap-1.5 shrink-0">
              <button
                type="button"
                onClick={() => setActiveViewMode('ai')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'ai'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.aiQuery}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('builder')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'builder'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.analysisBuilder}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('tables')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'tables'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.detectedTables} ({currentSheet?.tables.length ?? 0})
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('data')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'data'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.spreadsheetGrid} ({currentSheet?.total_rows ?? 0} {dictionary.common.rows})
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('visualize')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'visualize'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                {dictionary.nav.visualizations}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('quality')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                  activeViewMode === 'quality'
                    ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-2xs'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-200'
                }`}
              >
                <span>{dictionary.nav.dataQuality}</span>
                {currentSheet && (
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      activeViewMode === 'quality'
                        ? 'bg-slate-800 dark:bg-slate-200 text-white dark:text-slate-900'
                        : currentSheet.quality_report.overall_score >= 90
                        ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300'
                        : 'bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300'
                    }`}
                  >
                    {currentSheet.quality_report.overall_score}/100
                  </span>
                )}
              </button>
            </div>

            {currentSheet && (
              <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono shrink-0 hidden md:block">
                {dictionary.common.usedRange}: <span className="font-bold text-slate-700 dark:text-slate-300">{currentSheet.used_range}</span>
              </div>
            )}
          </div>

          {/* Main Content Area */}
          <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
            {currentSheet ? (
              <div className="w-full">
                <div className={activeViewMode === 'ai' ? 'block' : 'hidden'}>
                  <AIQueryWorkspace
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                </div>

                <div className={activeViewMode === 'builder' ? 'block' : 'hidden'}>
                  <OperationBuilder
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                </div>

                <div className={activeViewMode === 'tables' ? 'block' : 'hidden'}>
                  <DetectedTablesViewer
                    tables={currentSheet.tables}
                    sheetName={currentSheet.name}
                  />
                </div>

                <div className={activeViewMode === 'data' ? 'block' : 'hidden'}>
                  <ActualDataViewer
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                  />
                </div>

                <div className={activeViewMode === 'visualize' ? 'block' : 'hidden'}>
                  <VisualizationViewer
                    datasetId={overview.dataset_id}
                    sheetName={currentSheet.name}
                    tables={currentSheet.tables}
                  />
                </div>

                <div className={activeViewMode === 'quality' ? 'block' : 'hidden'}>
                  <DataQualityPanel
                    report={currentSheet.quality_report}
                    sheetName={currentSheet.name}
                  />
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 dark:text-slate-400 text-xs">
                {dictionary.nav.selectWorksheet}
              </div>
            )}
          </main>
        </div>
      )}

      {/* Global How to Use Modal */}
      <HowToUseModal isOpen={isHelpOpen} onClose={() => setIsHelpOpen(false)} />

      {/* First-Visit Language Onboarding Modal */}
      <LanguageOnboardingModal />
    </div>
  );
}
