import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';
import { LanguageProvider } from '../lib/i18n';
import { ThemeProvider } from '../lib/theme/ThemeContext';
import { WorkspaceProvider } from '../lib/workspace/WorkspaceContext';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
  display: 'swap',
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Sheetsly — Deterministic Spreadsheet Intelligence Workspace',
  description: 'Evidence-based spreadsheet intelligence platform combining deterministic analytical execution and visual traceability.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col font-sans bg-slate-100 dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-slate-200 dark:selection:bg-slate-800 selection:text-slate-900 dark:selection:text-slate-100 transition-colors duration-150">
        <ThemeProvider>
          <LanguageProvider>
            <WorkspaceProvider>{children}</WorkspaceProvider>
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
