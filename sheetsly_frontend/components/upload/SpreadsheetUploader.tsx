'use client';

import React, { useState, useRef } from 'react';
import { api, ApiError } from '../../lib/api';
import { WorkbookOverview } from '../../lib/types';

interface SpreadsheetUploaderProps {
  onUploadSuccess: (overview: WorkbookOverview) => void;
}

interface ActiveFileInfo {
  name: string;
  sizeFormatted: string;
}

export const SpreadsheetUploader: React.FC<SpreadsheetUploaderProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [activeFile, setActiveFile] = useState<ActiveFileInfo | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const handleFile = async (file: File) => {
    const validExtensions = ['.xlsx', '.xls', '.csv', '.xlsm', '.xltx'];
    const fileNameLower = file.name.toLowerCase();
    const hasValidExt = validExtensions.some((ext) => fileNameLower.endsWith(ext));

    if (!hasValidExt) {
      setErrorMessage(`Unsupported file format. Please upload an Excel (.xlsx, .xls, .xlsm) or CSV file.`);
      return;
    }

    setErrorMessage(null);
    setActiveFile({
      name: file.name,
      sizeFormatted: formatFileSize(file.size),
    });
    setIsUploading(true);

    try {
      const overview = await api.uploadSpreadsheet(file);
      onUploadSuccess(overview);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err?.message || 'Failed to process spreadsheet file. Ensure the backend server is running.');
      }
    } finally {
      setIsUploading(false);
      setActiveFile(null);
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isUploading) {
      setIsDragging(true);
    }
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (isUploading) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto p-4">
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
          isUploading
            ? 'border-slate-400 bg-slate-50 cursor-not-allowed'
            : isDragging
            ? 'border-slate-700 bg-slate-100/70 cursor-pointer'
            : 'border-slate-300 hover:border-slate-400 bg-white hover:bg-slate-50/50 cursor-pointer'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.csv,.xlsm,.xltx"
          disabled={isUploading}
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          {isUploading ? (
            /* Active Ingestion Processing View */
            <div className="w-full max-w-md space-y-3.5 py-1">
              <div className="flex items-center justify-center">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                  Dataset Ingestion Active
                </span>
              </div>

              <div className="p-3.5 bg-white border border-slate-200 rounded-md text-left space-y-2.5 shadow-2xs">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-900 truncate max-w-[280px]">
                    {activeFile?.name || 'Spreadsheet file'}
                  </span>
                  <span className="font-mono text-[11px] text-slate-500 tabular-nums">
                    {activeFile?.sizeFormatted}
                  </span>
                </div>

                <div className="text-[11px] text-slate-700 font-medium">
                  Processing spreadsheet...
                </div>

                {/* Truthful Indeterminate Horizontal Progress Bar */}
                <div
                  role="progressbar"
                  aria-label="Dataset ingestion in progress"
                  aria-busy="true"
                  className="w-full h-1.5 bg-slate-100 border border-slate-200 rounded-full overflow-hidden relative"
                >
                  <div className="h-full bg-slate-900 rounded-full indeterminate-progress-bar" />
                </div>
              </div>

              <p className="text-[11px] text-slate-500 max-w-sm mx-auto leading-relaxed">
                Parsing worksheet structure, detecting tables, profiling column types, and analyzing data hygiene scores.
              </p>
            </div>
          ) : (
            /* Default Dropzone View */
            <>
              <div className="w-11 h-11 rounded-md bg-slate-100 flex items-center justify-center text-slate-700 border border-slate-200">
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.8}
                    d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>

              <div>
                <p className="text-xs font-semibold text-slate-800">
                  Select or drop spreadsheet file, or <span className="text-slate-900 underline font-bold">browse</span>
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Supports Excel (.xlsx, .xls, .xlsm) and CSV files up to 50MB
                </p>
              </div>

              <div className="flex items-center space-x-3 text-[11px] text-slate-500 pt-1">
                <span>Deterministic Calculation</span>
                <span className="text-slate-300">|</span>
                <span>Cell Coordinate Traceability</span>
                <span className="text-slate-300">|</span>
                <span>Data Quality Profiling</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Actionable Error Banner */}
      {errorMessage && (
        <div className="mt-3 p-3.5 rounded-md bg-rose-50 border border-rose-200 text-rose-900 text-xs space-y-1">
          <div className="font-bold flex items-center space-x-1.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-rose-600" />
            <span>File Ingestion Error</span>
          </div>
          <p className="text-[11px] text-rose-700">{errorMessage}</p>
        </div>
      )}
    </div>
  );
};
