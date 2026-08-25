'use client';

import React, { useRef, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import { WorkbookOverview } from '../../lib/types';

interface SpreadsheetUploaderProps {
  onUploadSuccess: (data: WorkbookOverview) => void;
}

export const SpreadsheetUploader: React.FC<SpreadsheetUploaderProps> = ({ onUploadSuccess }) => {
  const { dictionary } = useTranslation();
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!isUploading) setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (isUploading) return;
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (isUploading) return;
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file: File) => {
    // Client-side extension validation
    const validExtensions = ['.xlsx', '.xls', '.xlsm', '.xltx', '.csv'];
    const fileName = file.name.toLowerCase();
    const isValid = validExtensions.some((ext) => fileName.endsWith(ext));

    if (!isValid) {
      setErrorMessage(
        'Invalid file type. Supported formats are .xlsx, .xls, .xlsm, .xltx, and .csv'
      );
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMessage('File size exceeds the 50MB maximum limit.');
      return;
    }

    setErrorMessage(null);
    setIsUploading(true);

    try {
      const data = await api.uploadSpreadsheet(file);
      onUploadSuccess(data);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to process spreadsheet. Please check the file structure.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full max-w-xl mx-auto">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        aria-busy={isUploading}
        tabIndex={isUploading ? -1 : 0}
        role="button"
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !isUploading) {
            e.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
          isUploading
            ? 'border-slate-300 dark:border-slate-700 bg-slate-50/80 dark:bg-slate-900/80 cursor-wait'
            : isDragging
            ? 'border-slate-800 dark:border-slate-200 bg-slate-100/80 dark:bg-slate-800/80 cursor-copy'
            : 'border-slate-300 dark:border-slate-700 hover:border-slate-500 dark:hover:border-slate-400 bg-white dark:bg-slate-900 cursor-pointer shadow-2xs hover:shadow-xs'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".xlsx,.xls,.xlsm,.xltx,.csv"
          disabled={isUploading}
          className="hidden"
          id="spreadsheet-upload-input"
          aria-label="Upload spreadsheet file"
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          {isUploading ? (
            /* Active Progressive Loading View */
            <div className="w-full max-w-xs space-y-3 py-2">
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block">
                  {dictionary.upload.ingestionActive}
                </span>
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  {dictionary.upload.processing}
                </p>
              </div>

              {/* Truthful Continuous Progress Indicator */}
              <div
                role="progressbar"
                aria-label="Dataset ingestion in progress"
                aria-busy="true"
                className="w-full h-1.5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full overflow-hidden"
              >
                <div className="h-full bg-slate-900 dark:bg-slate-100 rounded-full indeterminate-progress-bar" />
              </div>

              <p className="text-[11px] text-slate-500 dark:text-slate-400 max-w-sm mx-auto leading-relaxed">
                {dictionary.upload.ingestionDesc}
              </p>
            </div>
          ) : (
            /* Default Dropzone View */
            <>
              <div className="w-11 h-11 rounded-md bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
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
                <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                  {dictionary.upload.selectOrDrop} <span className="text-slate-900 dark:text-slate-100 underline font-bold">{dictionary.upload.browse}</span>
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  {dictionary.upload.supports}
                </p>
              </div>

              <div className="flex items-center space-x-3 text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                <span>{dictionary.upload.featureDeterministic}</span>
                <span className="text-slate-300 dark:text-slate-700">|</span>
                <span>{dictionary.upload.featureLineage}</span>
                <span className="text-slate-300 dark:text-slate-700">|</span>
                <span>{dictionary.upload.featureQuality}</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Actionable Error Banner */}
      {errorMessage && (
        <div className="mt-3 p-3.5 rounded-md bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800 text-rose-900 dark:text-rose-200 text-xs space-y-1">
          <div className="font-bold flex items-center space-x-1.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-rose-600" />
            <span>{dictionary.upload.errorTitle}</span>
          </div>
          <p className="text-[11px] text-rose-700 dark:text-rose-300">{errorMessage}</p>
        </div>
      )}
    </div>
  );
};
