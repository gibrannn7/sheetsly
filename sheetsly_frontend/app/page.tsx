'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import GradientWaves from '../components/GradientWaves';
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
  const [showScrollTop, setShowScrollTop] = useState<boolean>(false);
  const [isScrolled, setIsScrolled] = useState<boolean>(false);

  // Scroll listener for scroll-aware navbar and scroll-to-top control
  useEffect(() => {
    if (typeof window === 'undefined' || overview) return;
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      setIsScrolled(currentScrollY > 20);
      setShowScrollTop(currentScrollY > 400);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [overview]);

  // Subtle scroll-based reveal effect respecting prefers-reduced-motion
  useEffect(() => {
    if (typeof window === 'undefined' || overview) return;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      document.querySelectorAll('.reveal-on-scroll').forEach((el) => {
        el.classList.add('opacity-100', 'translate-y-0');
        el.classList.remove('opacity-0', 'translate-y-3');
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('opacity-100', 'translate-y-0');
            entry.target.classList.remove('opacity-0', 'translate-y-3');
          }
        });
      },
      { threshold: 0.06 }
    );

    const elements = document.querySelectorAll('.reveal-on-scroll');
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
  }, [overview]);

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

  const handleSmoothScroll = (e: React.MouseEvent<HTMLElement>, targetId: string) => {
    e.preventDefault();
    const el = document.getElementById(targetId);
    if (el) {
      const prefersReducedMotion =
        typeof window !== 'undefined' &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      el.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth' });
      if (typeof window !== 'undefined') {
        window.history.pushState(null, '', `#${targetId}`);
      }
    }
  };

  const scrollToTop = () => {
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({
      top: 0,
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
    });
  };

  const currentSheet = overview?.sheets.find((s) => s.name === activeSheetName) || overview?.sheets[0];
  const land = dictionary.landing;

  return (
    <div className="min-h-screen bg-[#08090d] text-zinc-100 flex flex-col font-sans selection:bg-zinc-800">
      {!overview ? (
        // Deep Graphite / Charcoal Analytical Workspace Landing Page
        <div className="flex-1 flex flex-col w-full relative overflow-x-hidden">
          {/* Scroll-Aware Sticky Navigation Bar (Seamless, Modern, No Bottom Border at Top) */}
          <header
            className={`sticky top-0 z-40 w-full transition-all duration-300 ease-out ${
              isScrolled
                ? 'bg-[#08090d]/80 backdrop-blur-md border-b border-zinc-800/40 shadow-xs'
                : 'bg-transparent border-b border-transparent shadow-none'
            }`}
          >
            <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-6">
              {/* Brand Identity: Logo + Sheetsly Only (No version badge) */}
              <a href="#" className="flex items-center space-x-3 group shrink-0">
                <img
                  src="/assets/logo.png"
                  alt="Sheetsly"
                  className="w-7 h-7 object-contain rounded transition-transform duration-200 group-hover:scale-105"
                />
                <span className="text-sm font-semibold text-white tracking-tight">
                  {dictionary.common.appName}
                </span>
              </a>

              {/* Centered Modern Navigation Anchors */}
              <nav className="hidden md:flex items-center space-x-8 text-xs font-medium text-zinc-400">
                <a
                  href="#workbench"
                  onClick={(e) => handleSmoothScroll(e, 'workbench')}
                  className="hover:text-white transition-colors"
                >
                  {land.nav.showcase}
                </a>
                <a
                  href="#workflow"
                  onClick={(e) => handleSmoothScroll(e, 'workflow')}
                  className="hover:text-white transition-colors"
                >
                  {land.nav.workflow}
                </a>
                <a
                  href="#architecture"
                  onClick={(e) => handleSmoothScroll(e, 'architecture')}
                  className="hover:text-white transition-colors"
                >
                  {land.nav.architecture}
                </a>
                <a
                  href="#agent"
                  onClick={(e) => handleSmoothScroll(e, 'agent')}
                  className="hover:text-white transition-colors"
                >
                  {land.nav.agent}
                </a>
              </nav>

              {/* Right Action Controls */}
              <div className="flex items-center gap-3">
                <LanguageSwitcher />

                <button
                  type="button"
                  onClick={() => setIsHelpOpen(true)}
                  aria-label={dictionary.nav.howToUse}
                  className="h-8 px-3 text-xs font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/60 rounded-md transition-colors cursor-pointer hidden sm:inline-block"
                >
                  {dictionary.nav.howToUse}
                </button>

                <button
                  type="button"
                  onClick={(e) => handleSmoothScroll(e, 'upload-section')}
                  className="h-8 px-3.5 inline-flex items-center justify-center text-xs font-semibold text-zinc-950 bg-white hover:bg-zinc-100 rounded-md transition-colors cursor-pointer whitespace-nowrap shadow-xs"
                >
                  {land.nav.tryApp}
                </button>
              </div>
            </div>
          </header>

          {/* Hero Section with Clearly Visible, Living Green GradientWaves Atmosphere */}
          <section className="relative w-full overflow-hidden pt-10 sm:pt-14 pb-16 sm:pb-22">
            {/* ReactBits GradientWaves Canvas (Clearly Visible Green Data Flow) */}
            <div
              aria-hidden="true"
              className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden opacity-95 [mask-image:linear-gradient(to_bottom,black_65%,transparent_100%)]"
            >
              <GradientWaves
                horizonColor="#012b12"
                waveColor="#057a34"
                crestColor="#15b853"
                speed={0.34}
                amplitude={2.55}
                waveScale={0.6}
                waveRatio={0.9}
                swell={35}
                turbulence={19.5}
                tilt={1.11}
                zoom={1.0}
                height={5.5}
                fogDepth={15}
                detail="medium"
                brightness={1.05}
                opacity={0.95}
                grain={true}
                grainIntensity={0.04}
                mouseInteraction={false}
              />
            </div>

            {/* Seamless Bottom Gradient Fade Dissolving Hero Atmosphere into Next Section */}
            <div
              aria-hidden="true"
              className="absolute bottom-0 inset-x-0 h-32 bg-gradient-to-t from-[#08090d] via-[#08090d]/60 to-transparent pointer-events-none"
            />

            {/* Hero Foreground Content (Sitting Inside the Atmosphere, Not in an Opaque Box) */}
            <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6">
              <div className="inline-block text-[11px] font-mono font-semibold uppercase tracking-widest text-emerald-300 bg-zinc-900/80 px-3 py-1 rounded-full border border-zinc-800 shadow-sm backdrop-blur-xs">
                SPREADSHEET INTELLIGENCE WORKSPACE
              </div>

              <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-[1.12]">
                {land.hero.title} {land.hero.titleHighlight}
              </h1>

              <p className="text-sm sm:text-base text-zinc-300 max-w-2xl mx-auto leading-relaxed">
                {land.hero.subtitle}
              </p>

              {/* Hero Action Buttons (NO ARROWS) */}
              <div className="flex items-center justify-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={(e) => handleSmoothScroll(e, 'upload-section')}
                  className="px-5 py-2.5 bg-white text-zinc-950 text-xs sm:text-sm font-semibold rounded-md hover:bg-zinc-100 transition-colors shadow-sm cursor-pointer"
                >
                  {land.hero.primaryCta}
                </button>
                <button
                  type="button"
                  onClick={() => setIsHelpOpen(true)}
                  className="px-5 py-2.5 bg-zinc-900/80 text-zinc-200 text-xs sm:text-sm font-medium hover:bg-zinc-800 border border-zinc-700 rounded-md transition-colors shadow-sm cursor-pointer backdrop-blur-xs"
                >
                  {land.hero.secondaryCta}
                </button>
              </div>

              {/* Dropzone Container (Translucent so green waves flow behind and around) */}
              <div id="upload-section" className="pt-6 scroll-mt-24 max-w-xl mx-auto">
                <div className="bg-[#0d0f14]/80 rounded-xl p-1.5 backdrop-blur-md shadow-xl border border-zinc-800/80">
                  <SpreadsheetUploader onUploadSuccess={handleUploadSuccess} />
                </div>
                <div className="flex items-center justify-center space-x-3 pt-3 text-[11px] text-zinc-400 font-mono">
                  <span>{land.hero.noHallucination}</span>
                  <span>•</span>
                  <span>{land.hero.instantUndo}</span>
                  <span>•</span>
                  <span>{land.hero.cellTraceability}</span>
                </div>
              </div>
            </div>
          </section>

          {/* Main Content Area with Graphite Atmosphere and Continuous Spacing */}
          <main className="flex-1 max-w-6xl mx-auto px-4 sm:px-6 w-full space-y-24 sm:space-y-32 py-10 sm:py-16 relative">
            {/* Product Workbench (Dominant Visual Proof) */}
            <section id="workbench" className="space-y-4 scroll-mt-24 reveal-on-scroll opacity-0 translate-y-3 transition-all duration-700 ease-out">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400">
                  {land.showcase.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {land.showcase.title}
                </h2>
                <p className="text-xs text-zinc-400 max-w-2xl">
                  {land.showcase.subtitle}
                </p>
              </div>

              <LandingProductShowcase />
            </section>

            {/* Problem / Solution Narrative (Editorial Statement — Text & Data Grounded, No Stock Photos) */}
            <section id="problem-solution" className="scroll-mt-24 reveal-on-scroll opacity-0 translate-y-3 transition-all duration-700 ease-out">
              <div className="p-6 sm:p-8 rounded-xl bg-[#0d0f14] border border-zinc-800 space-y-6 shadow-md">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                  {/* Left: Problem Statement & Real-World Friction */}
                  <div className="lg:col-span-7 space-y-4">
                    <div className="space-y-1.5">
                      <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400">
                        {land.problemSolution.badge}
                      </div>
                      <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                        {land.problemSolution.problemTitle}
                      </h2>
                      <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed">
                        {land.problemSolution.problemDesc}
                      </p>
                    </div>

                    <div className="space-y-2.5 pt-2">
                      <div className="text-xs text-zinc-300">
                        <strong className="text-white">{land.problemSolution.friction1Title}:</strong> {land.problemSolution.friction1Desc}
                      </div>
                      <div className="text-xs text-zinc-300">
                        <strong className="text-white">{land.problemSolution.friction2Title}:</strong> {land.problemSolution.friction2Desc}
                      </div>
                      <div className="text-xs text-zinc-300">
                        <strong className="text-white">{land.problemSolution.friction3Title}:</strong> {land.problemSolution.friction3Desc}
                      </div>
                      <div className="text-xs text-zinc-300">
                        <strong className="text-white">{land.problemSolution.friction4Title}:</strong> {land.problemSolution.friction4Desc}
                      </div>
                    </div>
                  </div>

                  {/* Right: Authentic Analytical Loop Verification Card */}
                  <div className="lg:col-span-5 space-y-3">
                    <div className="p-5 rounded-lg bg-[#090a0e] border border-zinc-800 space-y-3">
                      <div className="text-xs font-bold text-white">
                        {land.problemSolution.solutionTitle}
                      </div>
                      <p className="text-xs text-zinc-400 leading-relaxed">
                        {land.problemSolution.solutionDesc}
                      </p>

                      <div className="pt-3 border-t border-zinc-800 space-y-2">
                        <div className="text-[10px] font-mono uppercase tracking-wider text-zinc-500 font-bold">
                          The 4-Stage Verified Loop
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                          <div className="p-2 rounded bg-[#0d0f14] border border-zinc-800 text-zinc-300">
                            1. {land.problemSolution.loopUnderstand}
                          </div>
                          <div className="p-2 rounded bg-[#0d0f14] border border-zinc-800 text-zinc-300">
                            2. {land.problemSolution.loopAnalyze}
                          </div>
                          <div className="p-2 rounded bg-[#0d0f14] border border-zinc-800 text-zinc-300">
                            3. {land.problemSolution.loopAct}
                          </div>
                          <div className="p-2 rounded bg-[#0d0f14] border border-zinc-800 text-zinc-300">
                            4. {land.problemSolution.loopVerify}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* How It Works (Sequential 01 to 05 Process) */}
            <section id="workflow" className="space-y-6 scroll-mt-24 reveal-on-scroll opacity-0 translate-y-3 transition-all duration-700 ease-out">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400">
                  {land.howItWorks.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {land.howItWorks.title}
                </h2>
                <p className="text-xs text-zinc-400">
                  {land.howItWorks.subtitle}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-5 gap-3.5">
                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-2 shadow-xs">
                  <span className="font-mono text-xs font-bold text-zinc-500">01</span>
                  <h3 className="text-xs font-bold text-white">{land.howItWorks.step1Title}</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">{land.howItWorks.step1Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-2 shadow-xs">
                  <span className="font-mono text-xs font-bold text-zinc-500">02</span>
                  <h3 className="text-xs font-bold text-white">{land.howItWorks.step2Title}</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">{land.howItWorks.step2Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-2 shadow-xs">
                  <span className="font-mono text-xs font-bold text-zinc-500">03</span>
                  <h3 className="text-xs font-bold text-white">{land.howItWorks.step3Title}</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">{land.howItWorks.step3Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-2 shadow-xs">
                  <span className="font-mono text-xs font-bold text-zinc-500">04</span>
                  <h3 className="text-xs font-bold text-white">{land.howItWorks.step4Title}</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">{land.howItWorks.step4Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-2 shadow-xs">
                  <span className="font-mono text-xs font-bold text-zinc-500">05</span>
                  <h3 className="text-xs font-bold text-white">{land.howItWorks.step5Title}</h3>
                  <p className="text-xs text-zinc-400 leading-relaxed">{land.howItWorks.step5Desc}</p>
                </div>
              </div>
            </section>

            {/* Architecture Section */}
            <section id="architecture" className="space-y-6 scroll-mt-24 reveal-on-scroll opacity-0 translate-y-3 transition-all duration-700 ease-out">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400">
                  {land.architecture.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {land.architecture.title}
                </h2>
                <p className="text-xs text-zinc-400">
                  {land.architecture.subtitle}
                </p>
              </div>

              <LandingArchitectureFlow />
            </section>

            {/* Agent Differentiation (Asymmetric Layout) */}
            <section id="agent" className="space-y-6 scroll-mt-24 reveal-on-scroll opacity-0 translate-y-3 transition-all duration-700 ease-out">
              <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
                <div className="md:col-span-5 space-y-3">
                  <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400">
                    {land.agent.badge}
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                    {land.agent.title}
                  </h2>
                  <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                    {land.agent.subtitle}
                  </p>
                </div>

                <div className="md:col-span-7 space-y-3">
                  <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1 shadow-xs">
                    <div className="text-xs font-bold text-white">{land.agent.p1Title}</div>
                    <p className="text-xs text-zinc-400">{land.agent.p1Desc}</p>
                    <div className="text-[11px] font-mono text-emerald-400 pt-1">{land.agent.p1Detail}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1 shadow-xs">
                    <div className="text-xs font-bold text-white">{land.agent.p2Title}</div>
                    <p className="text-xs text-zinc-400">{land.agent.p2Desc}</p>
                    <div className="text-[11px] font-mono text-emerald-400 pt-1">{land.agent.p2Detail}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1 shadow-xs">
                    <div className="text-xs font-bold text-white">{land.agent.p3Title}</div>
                    <p className="text-xs text-zinc-400">{land.agent.p3Desc}</p>
                    <div className="text-[11px] font-mono text-emerald-400 pt-1">{land.agent.p3Detail}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1 shadow-xs">
                    <div className="text-xs font-bold text-white">{land.agent.p4Title}</div>
                    <p className="text-xs text-zinc-400">{land.agent.p4Desc}</p>
                    <div className="text-[11px] font-mono text-emerald-400 pt-1">{land.agent.p4Detail}</div>
                  </div>

                  <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1 shadow-xs">
                    <div className="text-xs font-bold text-white">{land.agent.p5Title}</div>
                    <p className="text-xs text-zinc-400">{land.agent.p5Desc}</p>
                    <div className="text-[11px] font-mono text-emerald-400 pt-1">{land.agent.p5Detail}</div>
                  </div>
                </div>
              </div>
            </section>

            {/* Real Product Examples */}
            <section id="examples" className="space-y-6 scroll-mt-24 reveal-on-scroll opacity-0 translate-y-3 transition-all duration-700 ease-out">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400">
                  {land.examples.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {land.examples.title}
                </h2>
                <p className="text-xs text-zinc-400">
                  {land.examples.subtitle}
                </p>
              </div>

              <LandingExamplesSection />
            </section>

            {/* Capabilities & Business Applications */}
            <section id="capabilities" className="space-y-6 scroll-mt-24 reveal-on-scroll opacity-0 translate-y-3 transition-all duration-700 ease-out">
              <div className="space-y-1">
                <div className="text-[11px] font-mono uppercase tracking-wider text-emerald-400">
                  {land.capabilities.badge}
                </div>
                <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                  {land.capabilities.title}
                </h2>
                <p className="text-xs text-zinc-400">
                  {land.capabilities.subtitle}
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5 shadow-xs">
                  <div className="font-bold text-xs text-white">{land.capabilities.f1Title}</div>
                  <p className="text-xs text-zinc-400">{land.capabilities.f1Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5 shadow-xs">
                  <div className="font-bold text-xs text-white">{land.capabilities.f2Title}</div>
                  <p className="text-xs text-zinc-400">{land.capabilities.f2Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5 shadow-xs">
                  <div className="font-bold text-xs text-white">{land.capabilities.f3Title}</div>
                  <p className="text-xs text-zinc-400">{land.capabilities.f3Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5 shadow-xs">
                  <div className="font-bold text-xs text-white">{land.capabilities.f4Title}</div>
                  <p className="text-xs text-zinc-400">{land.capabilities.f4Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5 shadow-xs">
                  <div className="font-bold text-xs text-white">{land.capabilities.f5Title}</div>
                  <p className="text-xs text-zinc-400">{land.capabilities.f5Desc}</p>
                </div>

                <div className="p-4 rounded-lg bg-[#0d0f14] border border-zinc-800 space-y-1.5 shadow-xs">
                  <div className="font-bold text-xs text-white">{land.capabilities.f6Title}</div>
                  <p className="text-xs text-zinc-400">{land.capabilities.f6Desc}</p>
                </div>
              </div>
            </section>

            {/* Final Action Bar (NO ARROWS) */}
            <section className="p-6 sm:p-8 rounded-xl bg-[#0d0f14] text-white border border-zinc-800 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-md reveal-on-scroll opacity-0 translate-y-3 transition-all duration-700 ease-out">
              <div className="space-y-1 max-w-xl">
                <h2 className="text-lg sm:text-xl font-bold tracking-tight text-white">
                  {land.cta.title}
                </h2>
                <p className="text-xs text-zinc-400">
                  {land.cta.subtitle}
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
                <button
                  type="button"
                  onClick={(e) => handleSmoothScroll(e, 'upload-section')}
                  className="px-5 py-2.5 bg-white text-zinc-950 text-xs font-semibold rounded-md hover:bg-zinc-100 transition-colors cursor-pointer shadow-xs"
                >
                  {land.cta.button}
                </button>
              </div>
            </section>
          </main>

          {/* Quiet Technical Footer (Dark Charcoal / Graphite) */}
          <footer className="w-full border-t border-zinc-800/80 bg-[#06070a] py-8 transition-colors">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-zinc-400">
              <div className="flex items-center space-x-2">
                <img
                  src="/assets/logo.png"
                  alt="Sheetsly Logo"
                  className="w-5 h-5 object-contain rounded"
                />
                <span className="font-semibold text-zinc-200">
                  {dictionary.common.appName}
                </span>
                <span>—</span>
                <span className="text-[11px]">{land.footer.tagline}</span>
              </div>

              <div className="text-center md:text-right space-y-0.5 font-mono text-[10px]">
                <div>{land.footer.privacyNote}</div>
                <div className="text-zinc-500">
                  &copy; 2026 {land.footer.rights}
                </div>
              </div>
            </div>
          </footer>

          {/* Scroll-to-Top Floating Control (Appears after scrolling >400px) */}
          <button
            type="button"
            onClick={scrollToTop}
            aria-label={dictionary.landing.nav.scrollToTop}
            title={dictionary.landing.nav.scrollToTop}
            className={`fixed bottom-6 right-6 z-50 p-2.5 rounded-lg bg-zinc-900/90 text-zinc-300 border border-zinc-700/80 shadow-md hover:bg-zinc-800 hover:text-white backdrop-blur-xs transition-all duration-300 cursor-pointer ${
              showScrollTop
                ? 'opacity-100 translate-y-0 pointer-events-auto'
                : 'opacity-0 translate-y-3 pointer-events-none'
            }`}
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
            </svg>
          </button>
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
          <div className="bg-[#0e1017] border-b border-zinc-800 px-4 sm:px-6 py-2 flex items-center justify-between gap-3 overflow-x-auto transition-colors">
            <div className="flex items-center gap-1.5 shrink-0">
              <button
                type="button"
                onClick={() => setActiveViewMode('ai')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'ai'
                    ? 'bg-white text-zinc-950 shadow-2xs'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`}
              >
                {dictionary.nav.aiQuery}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('builder')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'builder'
                    ? 'bg-white text-zinc-950 shadow-2xs'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`}
              >
                {dictionary.nav.analysisBuilder}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('tables')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'tables'
                    ? 'bg-white text-zinc-950 shadow-2xs'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`}
              >
                {dictionary.nav.detectedTables} ({currentSheet?.tables.length ?? 0})
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('data')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'data'
                    ? 'bg-white text-zinc-950 shadow-2xs'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`}
              >
                {dictionary.nav.spreadsheetGrid} ({currentSheet?.total_rows ?? 0} {dictionary.common.rows})
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('visualize')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer whitespace-nowrap ${
                  activeViewMode === 'visualize'
                    ? 'bg-white text-zinc-950 shadow-2xs'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`}
              >
                {dictionary.nav.visualizations}
              </button>

              <button
                type="button"
                onClick={() => setActiveViewMode('quality')}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md text-[11px] sm:text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                  activeViewMode === 'quality'
                    ? 'bg-white text-zinc-950 shadow-2xs'
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                }`}
              >
                <span>{dictionary.nav.dataQuality}</span>
                {currentSheet && (
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      activeViewMode === 'quality'
                        ? 'bg-zinc-800 text-white'
                        : currentSheet.quality_report.overall_score >= 90
                        ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                        : 'bg-amber-950/80 text-amber-300 border border-amber-800/60'
                    }`}
                  >
                    {currentSheet.quality_report.overall_score}/100
                  </span>
                )}
              </button>
            </div>

            {currentSheet && (
              <div className="text-[11px] text-zinc-400 font-mono shrink-0 hidden md:block">
                {dictionary.common.usedRange}: <span className="font-bold text-zinc-200">{currentSheet.used_range}</span>
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
              <div className="p-8 text-center text-zinc-400 text-xs">
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
