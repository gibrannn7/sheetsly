'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { api } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import { CellData, ChartActionSpecDTO, SheetDataGridResponse } from '../../lib/types';
import { downloadCsv, downloadWorkbookExport, tableToCsv } from '../../lib/export';
import { useWorkspace } from '../../lib/workspace/WorkspaceContext';
import { GridAIChatPanel } from '../ai/GridAIChatPanel';
import { ChartFullscreenModal } from '../ai/ChartFullscreenModal';

interface ActualDataViewerProps {
  datasetId: string;
  sheetName: string;
}

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

const colLetterToIndex = (col: string): number => {
  let index = 0;
  for (let i = 0; i < col.length; i++) {
    index = index * 26 + (col.charCodeAt(i) - 64);
  }
  return index;
};

const indexToColLetter = (index: number): string => {
  let temp = index;
  let letter = '';
  while (temp > 0) {
    const mod = (temp - 1) % 26;
    letter = String.fromCharCode(65 + mod) + letter;
    temp = Math.floor((temp - mod) / 26);
  }
  return letter;
};

export const ActualDataViewer: React.FC<ActualDataViewerProps> = ({ datasetId, sheetName }) => {
  const { dictionary, t } = useTranslation();
  const { actualDataState, updateActualDataState } = useWorkspace();

  const page = actualDataState.page;
  const pageSize = actualDataState.pageSize;
  const searchQuery = actualDataState.searchQuery;
  const selectedCell = actualDataState.selectedCell;

  const [debouncedQuery, setDebouncedQuery] = useState(searchQuery);
  const [gridData, setGridData] = useState<SheetDataGridResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAgentPanel, setShowAgentPanel] = useState(false);
  const [selectedChartForModal, setSelectedChartForModal] = useState<ChartActionSpecDTO | null>(null);
  const [selectedRange, setSelectedRange] = useState<string | null>(null);
  const [virtualBoundaryRows, setVirtualBoundaryRows] = useState<number>(1000);

  // Name Box & Formula Bar Editing State
  const [nameBoxInput, setNameBoxInput] = useState<string>('A1');
  const [formulaInput, setFormulaInput] = useState<string>('');
  const [isEditingFormula, setIsEditingFormula] = useState(false);
  const [formulaSubmitLoading, setFormulaSubmitLoading] = useState(false);

  const fetchGrid = useCallback(() => {
    setIsLoading(true);
    api
      .getSheetDataGrid(datasetId, sheetName, page, pageSize, debouncedQuery)
      .then((data) => {
        setGridData(data);
        setIsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load sheet grid', err);
        setIsLoading(false);
      });
  }, [datasetId, sheetName, page, pageSize, debouncedQuery]);

  // Debounce search query input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 150);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    fetchGrid();
  }, [fetchGrid]);

  // Sync selected cell with Name Box & Formula Bar
  useEffect(() => {
    if (selectedCell) {
      setNameBoxInput(selectedCell.coordinate.cell_ref);
      const val = selectedCell.formula
        ? selectedCell.formula
        : selectedCell.original_value !== null && selectedCell.original_value !== undefined
        ? String(selectedCell.original_value)
        : '';
      setFormulaInput(val);
      setSelectedRange(selectedCell.coordinate.cell_ref);
    }
  }, [selectedCell]);

  const realTotalRows = gridData?.total_rows ?? 0;
  const isSearching = debouncedQuery.trim().length > 0;
  const totalRowsForPagination = isSearching ? realTotalRows : Math.max(virtualBoundaryRows, realTotalRows);
  const totalPages = Math.max(1, Math.ceil(totalRowsForPagination / pageSize));

  const startRow = realTotalRows === 0 && isSearching ? 0 : (page - 1) * pageSize + 1;
  const endRow = (page - 1) * pageSize + pageSize;

  const setPage = (p: number | ((prev: number) => number)) => {
    const newPage = typeof p === 'function' ? p(page) : p;
    updateActualDataState({ page: newPage });
  };

  const handlePageSizeChange = (newSize: number) => {
    updateActualDataState({ pageSize: newSize, page: 1 });
  };

  const handleClearSearch = () => {
    updateActualDataState({ searchQuery: '', page: 1 });
    setDebouncedQuery('');
  };

  const setSelectedCell = (cell: CellData | null) => {
    updateActualDataState({ selectedCell: cell });
  };

  // Jump to coordinate or range from Name Box
  const handleNameBoxSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const raw = nameBoxInput.trim().toUpperCase();
    if (!raw) return;

    // Check if it's a range (e.g. B2:B9002 or N2:N20)
    if (raw.includes(':')) {
      const parts = raw.split(':');
      const startRef = parts[0];
      const match = startRef.match(/^([A-Z]+)(\d+)$/);
      if (match) {
        const colLetter = match[1];
        const rowNum = parseInt(match[2], 10);
        const targetPage = Math.max(1, Math.ceil(rowNum / pageSize));
        if (rowNum > virtualBoundaryRows) {
          setVirtualBoundaryRows(Math.max(virtualBoundaryRows, rowNum + 100));
        }
        setPage(targetPage);
        setSelectedRange(raw);
        const dummyStartCell: CellData = {
          coordinate: {
            row: rowNum,
            column: colLetterToIndex(colLetter),
            cell_ref: startRef,
          },
          data_type: 'null',
          original_value: null,
          parsed_value: null,
          formula: null,
          is_empty: true,
        };
        setSelectedCell(dummyStartCell);
      }
      return;
    }

    // Single cell coordinate (e.g. N2 or N9002 or B25)
    const match = raw.match(/^([A-Z]+)(\d+)$/);
    if (match) {
      const colLetter = match[1];
      const rowNum = parseInt(match[2], 10);
      const targetPage = Math.max(1, Math.ceil(rowNum / pageSize));
      if (rowNum > virtualBoundaryRows) {
        setVirtualBoundaryRows(Math.max(virtualBoundaryRows, rowNum + 100));
      }
      setPage(targetPage);
      setSelectedRange(raw);

      const cell: CellData = {
        coordinate: {
          row: rowNum,
          column: colLetterToIndex(colLetter),
          cell_ref: raw,
        },
        data_type: 'null',
        original_value: null,
        parsed_value: null,
        formula: null,
        is_empty: true,
      };
      setSelectedCell(cell);
    }
  };

  // Submit formula or value edit from Formula Bar
  const handleFormulaSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedCell || formulaSubmitLoading) return;

    const trimmed = formulaInput.trim();
    setFormulaSubmitLoading(true);

    try {
      if (trimmed.startsWith('=')) {
        // Execute as write formula instruction
        await api.executeAgentAction({
          dataset_id: datasetId,
          user_request: `Tulis rumus ${trimmed} di ${selectedCell.coordinate.cell_ref}`,
          active_sheet_name: sheetName,
        });
      } else {
        // Execute as write value instruction
        await api.executeAgentAction({
          dataset_id: datasetId,
          user_request: `Tulis nilai '${trimmed}' di ${selectedCell.coordinate.cell_ref}`,
          active_sheet_name: sheetName,
        });
      }
      setIsEditingFormula(false);
      fetchGrid();
    } catch (err: any) {
      console.error('Failed to submit cell edit', err);
    } finally {
      setFormulaSubmitLoading(false);
    }
  };

  const isNumericValue = (cell: CellData) => {
    return ['integer', 'float', 'currency', 'percentage'].includes(cell.data_type);
  };

  const isDateValue = (cell: CellData) => {
    return ['date', 'datetime'].includes(cell.data_type);
  };

  // Helper to check if a specific cell matches the active search query
  const isCellMatch = (cell: CellData): boolean => {
    const q = debouncedQuery.trim().toLowerCase();
    if (!q) return false;
    if (cell.original_value !== null && cell.original_value !== undefined && String(cell.original_value).toLowerCase().includes(q)) return true;
    if (cell.parsed_value !== null && cell.parsed_value !== undefined && String(cell.parsed_value).toLowerCase().includes(q)) return true;
    if (cell.formula && cell.formula.toLowerCase().includes(q)) return true;
    return false;
  };

  // Compute effective column headers (minimum 26 columns A..Z, extended on demand)
  const effectiveColumnHeaders = React.useMemo(() => {
    const populatedHeaders = gridData?.column_headers ?? [];
    let count = Math.max(26, populatedHeaders.length);
    if (selectedCell) {
      const match = selectedCell.coordinate.cell_ref.match(/^([A-Z]+)/);
      if (match) {
        const cIdx = colLetterToIndex(match[1]);
        if (cIdx > count) count = cIdx + 2;
      }
    }
    const headers: string[] = [];
    for (let i = 1; i <= count; i++) {
      headers.push(indexToColLetter(i));
    }
    return headers;
  }, [gridData?.column_headers, selectedCell]);

  // Compute effective rows for current page (real data padded with virtual empty cells)
  const effectiveRows: CellData[][] = React.useMemo(() => {
    if (isSearching) {
      if (!gridData || !gridData.rows) return [];
      return gridData.rows;
    }
    const rows: CellData[][] = [];
    const realRows = gridData?.rows ?? [];

    for (let r = 0; r < pageSize; r++) {
      const rowNumber = (page - 1) * pageSize + r + 1;
      const realRow = realRows[r];

      if (realRow && realRow.length > 0) {
        const paddedRow = [...realRow];
        for (let c = realRow.length; c < effectiveColumnHeaders.length; c++) {
          const colLetter = effectiveColumnHeaders[c];
          paddedRow.push({
            coordinate: { row: rowNumber, column: c + 1, cell_ref: `${colLetter}${rowNumber}` },
            data_type: 'null' as const,
            original_value: null,
            parsed_value: null,
            formula: null,
            is_empty: true,
          });
        }
        rows.push(paddedRow);
      } else {
        // Virtual empty row
        const emptyRow = effectiveColumnHeaders.map((colLetter, cIdx) => ({
          coordinate: { row: rowNumber, column: cIdx + 1, cell_ref: `${colLetter}${rowNumber}` },
          data_type: 'null' as const,
          original_value: null,
          parsed_value: null,
          formula: null,
          is_empty: true,
        }));
        rows.push(emptyRow);
      }
    }
    return rows;
  }, [isSearching, gridData, page, pageSize, effectiveColumnHeaders]);

  // Generate compact pagination item list
  const getPaginationItems = (): (number | string)[] => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    if (page <= 4) {
      return [1, 2, 3, 4, 5, '...', totalPages];
    }

    if (page >= totalPages - 3) {
      return [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
    }

    return [1, '...', page - 1, page, page + 1, '...', totalPages];
  };

  const [isExporting, setIsExporting] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(e.target as Node)) {
        setShowExportMenu(false);
      }
    };
    if (showExportMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showExportMenu]);

  const handleExport = async (format: 'xlsx' | 'csv') => {
    setIsExporting(true);
    setShowExportMenu(false);
    setExportError(null);
    try {
      await downloadWorkbookExport(datasetId, format, format === 'csv' ? sheetName : undefined);
    } catch (err: any) {
      console.error('Export failed', err);
      setExportError(err.message || 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  const handleFocusCell = (cellRef: string) => {
    if (!cellRef) return;
    const cleanRef = cellRef.includes(':') ? cellRef.split(':')[0] : cellRef;
    const match = cleanRef.match(/^([A-Z]+)(\d+)$/);
    if (match) {
      const colLetter = match[1];
      const rowNum = parseInt(match[2], 10);
      const targetPage = Math.max(1, Math.ceil(rowNum / pageSize));
      if (rowNum > virtualBoundaryRows) {
        setVirtualBoundaryRows(Math.max(virtualBoundaryRows, rowNum + 100));
      }
      setPage(targetPage);
      setNameBoxInput(cleanRef);
      setSelectedRange(cleanRef);
      const colIndex = colLetterToIndex(colLetter);
      const rowOffset = (rowNum - 1) % pageSize;
      const targetRow = (targetPage === page && gridData?.rows) ? gridData.rows[rowOffset] : undefined;
      const existingCell = targetRow && targetRow[colIndex - 1] ? targetRow[colIndex - 1] : undefined;
      if (existingCell) {
        setSelectedCell(existingCell);
      } else {
        setSelectedCell({
          coordinate: {
            row: rowNum,
            column: colIndex,
            cell_ref: cleanRef,
          },
          data_type: 'null',
          original_value: null,
          parsed_value: null,
          formula: null,
          is_empty: true,
        });
      }
    }
  };

  return (
    <div className="flex flex-col lg:flex-row gap-4 items-start">
      <div className="flex-1 w-full space-y-3 min-w-0">
        {/* Grid Container */}
        <div className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs overflow-hidden transition-colors">
          {/* Header Toolbar */}
          <div className="p-3 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 transition-colors">
            {/* Left: Sheet Title + Search Input */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center space-x-1.5">
                <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">
                  {dictionary.grid.title}
                </h3>
                <span className="text-slate-500 dark:text-slate-400 font-mono text-xs font-normal">({sheetName})</span>
              </div>

              {/* Search Input Box */}
              <div className="relative flex items-center min-w-[200px] sm:min-w-[240px]">
                <div className="absolute left-2.5 text-slate-400 dark:text-slate-500 pointer-events-none flex items-center">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => {
                    updateActualDataState({ searchQuery: e.target.value, page: 1 });
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Escape') {
                      handleClearSearch();
                    }
                  }}
                  placeholder={dictionary.grid.searchPlaceholder}
                  aria-label={dictionary.grid.searchPlaceholder}
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-md pl-8 pr-7 py-1 text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-hidden focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-100 focus:border-slate-900 dark:focus:border-slate-100 transition-colors shadow-2xs"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={handleClearSearch}
                    aria-label={dictionary.grid.clearSearch}
                    title={dictionary.grid.clearSearch}
                    className="absolute right-1.5 p-1 text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 rounded cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Matching Result Badge */}
              {isSearching && !isLoading && gridData && (
                <span className="text-[11px] font-mono text-slate-700 dark:text-slate-300 bg-slate-200/70 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 px-2 py-0.5 rounded font-medium select-none">
                  {t('grid.matchingRows', { count: realTotalRows.toLocaleString() })}
                </span>
              )}
            </div>

            {/* Right: AI Agent + Export + Page Size Selector + Row Range */}
            <div className="flex items-center space-x-2.5">
              {/* AI Agent Chat Toggle Button */}
              <button
                type="button"
                onClick={() => setShowAgentPanel((prev) => !prev)}
                title="Buka Spreadsheet AI Agent Chat"
                className={`inline-flex items-center space-x-1.5 px-2.5 py-1 text-xs font-semibold rounded-md border transition-colors shadow-2xs cursor-pointer ${
                  showAgentPanel
                    ? 'bg-emerald-600 text-white border-emerald-600 dark:bg-emerald-500 dark:text-slate-900'
                    : 'text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border-slate-300 dark:border-slate-700'
                }`}
              >
                <span>AI Agent</span>
              </button>

              {/* Export Dropdown Menu */}
              <div className="relative inline-block text-left" ref={exportMenuRef}>
                <button
                  type="button"
                  onClick={() => setShowExportMenu((prev) => !prev)}
                  disabled={isExporting}
                  title="Download spreadsheet as Excel (.xlsx) or CSV (.csv)"
                  className="inline-flex items-center space-x-1.5 px-2.5 py-1 text-xs font-semibold text-slate-700 dark:text-slate-200 bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md transition-colors shadow-2xs cursor-pointer disabled:opacity-50"
                >
                  {isExporting ? (
                    <div className="w-3.5 h-3.5 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <svg className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  )}
                  <span>{isExporting ? 'Exporting...' : 'Export'}</span>
                  <svg className="w-3 h-3 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showExportMenu && (
                  <div className="absolute right-0 mt-1 w-56 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-lg py-1 z-30 animate-in fade-in-50 duration-100">
                    <button
                      type="button"
                      onClick={() => handleExport('xlsx')}
                      className="w-full text-left px-3 py-2 text-xs hover:bg-slate-100 dark:hover:bg-slate-800 flex items-start space-x-2.5 transition-colors cursor-pointer"
                    >
                      <div className="p-1 rounded bg-emerald-100 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 mt-0.5">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-900 dark:text-slate-100 block">Excel Workbook (.xlsx)</span>
                        <span className="text-[10px] text-slate-500 dark:text-slate-400 block">All sheets with formulas & values</span>
                      </div>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleExport('csv')}
                      className="w-full text-left px-3 py-2 text-xs hover:bg-slate-100 dark:hover:bg-slate-800 flex items-start space-x-2.5 transition-colors cursor-pointer border-t border-slate-100 dark:border-slate-800"
                    >
                      <div className="p-1 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 mt-0.5">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                        </svg>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-900 dark:text-slate-100 block">Active Sheet (.csv)</span>
                        <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Current sheet ({sheetName})</span>
                      </div>
                    </button>
                  </div>
                )}
              </div>

              {/* Page Size Selector */}
              <div className="flex items-center space-x-1.5 text-xs text-slate-600 dark:text-slate-400">
                <span className="text-[11px] font-medium">{dictionary.grid.rowsPerPage}</span>
                <select
                  value={pageSize}
                  onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                  aria-label={dictionary.grid.rowsPerPage}
                  className="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded px-2 py-0.5 text-xs font-mono font-medium text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-100 cursor-pointer shadow-2xs"
                >
                  {PAGE_SIZE_OPTIONS.map((size) => (
                    <option key={size} value={size}>
                      {size}
                    </option>
                  ))}
                </select>
              </div>

              {/* Row Range Metadata */}
              <div className="text-[11px] text-slate-600 dark:text-slate-400 font-mono tabular-nums bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-2 py-0.5 rounded shadow-2xs">
                {t('grid.showingRows', {
                  start: startRow,
                  end: Math.min(endRow, totalRowsForPagination),
                  total: realTotalRows.toLocaleString(),
                })}
              </div>
            </div>
          </div>

          {/* Name Box & Formula Bar Toolbar */}
          <div className="px-3 py-1.5 bg-slate-100/75 dark:bg-slate-950/80 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2 transition-colors">
            {/* Name Box (Cell Reference / Range) */}
            <form onSubmit={handleNameBoxSubmit} className="flex items-center">
              <input
                type="text"
                value={nameBoxInput}
                onChange={(e) => setNameBoxInput(e.target.value)}
                onBlur={handleNameBoxSubmit}
                placeholder={dictionary.grid.nameBoxPlaceholder}
                title={dictionary.grid.jumpToCell}
                className="w-24 sm:w-28 px-2 py-1 text-xs font-mono font-bold uppercase bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded text-slate-800 dark:text-slate-200 text-center focus:outline-none focus:ring-1 focus:ring-slate-500 shadow-2xs"
              />
            </form>

            <span className="text-slate-300 dark:text-slate-700 select-none">|</span>

            {/* Formula Symbol Indicator */}
            <span className="font-mono text-xs font-bold text-slate-500 dark:text-slate-400 select-none px-1">
              fx
            </span>

            {/* Formula / Value Input Field */}
            <form onSubmit={handleFormulaSubmit} className="flex-1 flex items-center gap-1.5">
              <input
                type="text"
                value={formulaInput}
                onChange={(e) => {
                  setFormulaInput(e.target.value);
                  setIsEditingFormula(true);
                }}
                disabled={!selectedCell || formulaSubmitLoading}
                placeholder={selectedCell ? dictionary.grid.formulaBarLabel : dictionary.grid.clickToInspect}
                className="flex-1 px-2.5 py-1 text-xs font-mono bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-500 placeholder:text-slate-400 shadow-2xs"
              />
              {isEditingFormula && (
                <div className="flex items-center gap-1">
                  <button
                    type="submit"
                    disabled={formulaSubmitLoading}
                    title={dictionary.grid.saveCell}
                    className="px-2 py-1 text-[11px] font-bold bg-emerald-600 hover:bg-emerald-700 text-white rounded cursor-pointer transition-colors shadow-2xs"
                  >
                    ✓
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingFormula(false);
                      if (selectedCell) {
                        setFormulaInput(selectedCell.formula || (selectedCell.original_value !== null ? String(selectedCell.original_value) : ''));
                      }
                    }}
                    title={dictionary.grid.cancelEdit}
                    className="px-2 py-1 text-[11px] font-bold bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded hover:bg-slate-300 dark:hover:bg-slate-700 cursor-pointer transition-colors shadow-2xs"
                  >
                    ✕
                  </button>
                </div>
              )}
            </form>
          </div>

          {/* Spreadsheet Data Surface & Floating Worksheet Charts */}
          {isLoading ? (
            <div className="p-14 text-center text-slate-500 dark:text-slate-400 text-xs space-y-1">
              <p className="font-semibold text-slate-700 dark:text-slate-300">{dictionary.common.loading}</p>
              <p className="text-[11px] text-slate-400 dark:text-slate-500">{dictionary.grid.desc}</p>
            </div>
          ) : isSearching && (!gridData || gridData.rows.length === 0) ? (
            <div className="p-12 text-center space-y-2 bg-white dark:bg-slate-900">
              <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 flex items-center justify-center mx-auto">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide">
                {dictionary.grid.noMatchingRowsTitle}
              </h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto">
                {t('grid.noMatchingRowsDesc', { query: debouncedQuery })}
              </p>
              <div className="pt-1">
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="px-3 py-1 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 rounded border border-slate-300 dark:border-slate-700 text-xs font-medium cursor-pointer transition-colors shadow-2xs"
                >
                  {dictionary.grid.clearSearch}
                </button>
              </div>
            </div>
          ) : (
            <div className="relative overflow-x-auto min-h-[480px] max-h-[680px]">
              <table className="w-full text-left text-xs border-collapse font-sans border-spacing-0">
                <thead className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 sticky top-0 z-20 font-mono text-[11px] border-b border-slate-300 dark:border-slate-700 shadow-2xs">
                  <tr>
                    <th className="w-12 min-w-[48px] px-2.5 py-1.5 text-center bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold border-r border-slate-300 dark:border-slate-700 select-none">
                      #
                    </th>
                    {effectiveColumnHeaders.map((colLetter, cIdx) => (
                      <th
                        key={cIdx}
                        className="px-3 py-1.5 font-bold text-center border-r border-slate-300 dark:border-slate-700 min-w-[110px] select-none text-slate-700 dark:text-slate-300"
                      >
                        {colLetter}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-slate-800 dark:text-slate-200">
                  {effectiveRows.map((rowCells, rIdx) => {
                    const rowNumber = rowCells[0]?.coordinate.row ?? (page - 1) * pageSize + rIdx + 1;
                    return (
                      <tr key={rIdx} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors group">
                        <td className="px-2 py-1 text-center font-mono text-slate-500 dark:text-slate-400 bg-slate-100/90 dark:bg-slate-900/90 border-r border-slate-300 dark:border-slate-700 font-semibold select-none text-[11px] tabular-nums">
                          {rowNumber}
                        </td>
                        {rowCells.map((cell, cIdx) => {
                          const isSelected = selectedCell?.coordinate.cell_ref === cell.coordinate.cell_ref;
                          const isMatched = isCellMatch(cell);
                          const isNum = isNumericValue(cell);
                          const isDate = isDateValue(cell);
                          const chartAtThisCell = Object.values(gridData?.charts || {}).find(
                            (c) => c.destination_cell === cell.coordinate.cell_ref
                          );
                          const isChartAnchor = !!chartAtThisCell;
                          const rawString = cell.original_value !== null && cell.original_value !== undefined
                            ? String(cell.original_value)
                            : '';

                          const cellTooltip = `Cell ${cell.coordinate.cell_ref} (${cell.data_type})\nValue: ${rawString || '(empty)'}${
                            cell.formula ? `\nFormula: ${cell.formula}` : ''
                          }${isChartAnchor ? '\n[Chart Anchor Cell]' : ''}`;

                          return (
                            <td
                              key={cIdx}
                              onClick={() => setSelectedCell(cell)}
                              title={cellTooltip}
                              className={`px-2.5 py-1 border-r border-slate-200 dark:border-slate-800 cursor-pointer transition-all ${
                                isChartAnchor ? 'relative' : ''
                              } ${
                                isNum
                                  ? 'min-w-[100px] max-w-[160px] text-right font-mono tabular-nums'
                                  : isDate
                                  ? 'min-w-[110px] max-w-[150px] font-mono text-center'
                                  : 'min-w-[130px] max-w-[240px] text-left'
                              } ${
                                isSelected
                                  ? 'bg-slate-200 dark:bg-slate-800 ring-2 ring-slate-900 dark:ring-slate-100 font-semibold text-slate-900 dark:text-slate-100 z-10 relative'
                                  : isChartAnchor
                                  ? 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 font-medium'
                                  : isMatched
                                  ? 'bg-amber-50 dark:bg-amber-950/60 text-amber-950 dark:text-amber-200 font-medium'
                                  : cell.is_empty
                                  ? 'bg-slate-50/30 dark:bg-slate-900/30 text-slate-300 dark:text-slate-600'
                                  : 'hover:bg-slate-100/60 dark:hover:bg-slate-800/60'
                              }`}
                            >
                              <div className={`flex items-center ${isNum ? 'justify-end' : 'justify-between'} gap-1.5`}>
                                <span
                                  className={`truncate block ${cell.is_empty ? 'text-slate-300 dark:text-slate-600 font-mono' : ''} ${
                                    isMatched ? 'font-semibold text-slate-950 dark:text-amber-200' : ''
                                  }`}
                                >
                                  {cell.is_empty ? '-' : rawString}
                                </span>
                                {cell.formula && (
                                  <span className="px-1 py-0.2 rounded bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-200 text-[9px] font-mono font-bold shrink-0 select-none">
                                    fx
                                  </span>
                                )}
                              </div>

                              {/* Native Worksheet Chart Object anchored to this cell */}
                              {chartAtThisCell && (
                                <div
                                  className="absolute top-0 left-0 z-10 w-[380px] sm:w-[460px] rounded-lg bg-white/95 dark:bg-slate-900/95 backdrop-blur-xs border border-slate-300 dark:border-slate-700 shadow-xl p-3 space-y-2 select-none hover:shadow-2xl hover:border-indigo-400 dark:hover:border-indigo-500 transition-all group pointer-events-auto"
                                  style={{ minHeight: '250px' }}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedChartForModal(chartAtThisCell);
                                  }}
                                >
                                  {/* Header */}
                                  <div className="flex items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-1.5">
                                    <div className="flex items-center gap-1.5 truncate">
                                      <span className="px-1.5 py-0.5 rounded bg-indigo-100 dark:bg-indigo-900/60 text-indigo-700 dark:text-indigo-300 font-mono text-[9px] font-bold uppercase tracking-wider">
                                        {chartAtThisCell.chart_type}
                                      </span>
                                      <span className="font-semibold text-xs text-slate-900 dark:text-slate-100 truncate">
                                        {chartAtThisCell.title}
                                      </span>
                                    </div>
                                    <div className="flex items-center gap-1.5 shrink-0">
                                      <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono font-bold text-[9px]">
                                        {chartAtThisCell.destination_cell}
                                      </span>
                                      <span className="text-[10px] text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors" title={dictionary.agent.chartArtifact?.viewFullscreen || 'Click to view fullscreen'}>
                                        ⛶
                                      </span>
                                    </div>
                                  </div>

                                  {/* Rendered Chart Graphic */}
                                  {chartAtThisCell.image_base64 && (
                                    <div className="relative bg-white dark:bg-slate-950 rounded border border-slate-100 dark:border-slate-800 overflow-hidden p-1 flex items-center justify-center">
                                      <img
                                        src={`data:image/png;base64,${chartAtThisCell.image_base64}`}
                                        alt={chartAtThisCell.title}
                                        className="w-full max-h-44 object-contain select-none transition-transform group-hover:scale-[1.01]"
                                      />
                                    </div>
                                  )}

                                  {/* Footer Meta */}
                                  <div className="flex items-center justify-between text-[9px] text-slate-500 dark:text-slate-400 font-mono pt-0.5">
                                    <span className="truncate max-w-[65%]">
                                      {chartAtThisCell.dimension_column && `${chartAtThisCell.dimension_column}`}
                                      {chartAtThisCell.measure_column && ` → ${chartAtThisCell.measure_column}`}
                                      {chartAtThisCell.aggregation && ` (${chartAtThisCell.aggregation})`}
                                    </span>
                                    <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                                      ✓ {dictionary.agent.chartArtifact?.verifiedTruth || 'Verified Truth'}
                                    </span>
                                  </div>
                                </div>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Compact Pagination Bar */}
          {totalPages > 1 && (
            <div className="p-3 bg-slate-50 dark:bg-slate-950 border-t border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs transition-colors">
              <div className="flex items-center space-x-2 text-slate-500 dark:text-slate-400 font-mono text-[11px] tabular-nums">
                <span>{t('grid.pageOf', { page, totalPages })}</span>
                <span>•</span>
                <span>{t('grid.showingRows', { start: startRow, end: Math.min(endRow, totalRowsForPagination), total: realTotalRows.toLocaleString() })}</span>
              </div>

              <div className="flex items-center space-x-1">
                {/* Previous Button */}
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer disabled:cursor-not-allowed text-xs font-medium focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-slate-900 dark:focus-visible:ring-slate-100"
                >
                  {dictionary.grid.prev}
                </button>

                {/* Numbered Page Buttons with Smart Ellipsis */}
                {getPaginationItems().map((item, idx) => {
                  if (typeof item === 'string') {
                    return (
                      <span
                        key={`ellipsis-${idx}`}
                        className="px-2 py-1 text-slate-400 dark:text-slate-600 font-mono select-none text-xs"
                      >
                        …
                      </span>
                    );
                  }

                  const isCurrent = item === page;
                  return (
                    <button
                      key={`page-${item}`}
                      type="button"
                      onClick={() => setPage(item as number)}
                      aria-current={isCurrent ? 'page' : undefined}
                      className={`min-w-[28px] px-2 py-1 text-xs font-mono font-semibold rounded border transition-colors cursor-pointer focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-slate-900 dark:focus-visible:ring-slate-100 ${
                        isCurrent
                          ? 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 border-slate-900 dark:border-slate-100 shadow-2xs'
                          : 'bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800'
                      }`}
                    >
                      {item}
                    </button>
                  );
                })}

                {/* Next Button */}
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded text-slate-700 dark:text-slate-300 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer disabled:cursor-not-allowed text-xs font-medium focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-slate-900 dark:focus-visible:ring-slate-100"
                >
                  {dictionary.grid.next}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Selected Cell Full Raw Value & Metadata Inspector */}
        {selectedCell && (
          <div className="p-4 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-300 dark:border-slate-700 text-xs space-y-3 shadow-2xs animate-in fade-in duration-100 transition-colors">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2.5">
              <div className="flex items-center space-x-2.5">
                <span className="font-mono font-bold text-xs bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 px-2 py-0.5 rounded shadow-2xs">
                  {selectedCell.coordinate.cell_ref}
                </span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{dictionary.grid.cellInspection}</span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedCell(null)}
                aria-label={dictionary.common.close}
                className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 text-xs font-bold cursor-pointer p-1 rounded hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-700 dark:text-slate-300">
              {/* Full Original Value with wrapping */}
              <div className="p-2.5 bg-white dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-bold tracking-wider">
                  {dictionary.grid.originalValue}
                </span>
                <div className="font-mono font-semibold text-slate-900 dark:text-slate-100 text-xs whitespace-pre-wrap break-words max-h-36 overflow-y-auto">
                  {selectedCell.original_value !== null && selectedCell.original_value !== undefined
                    ? String(selectedCell.original_value)
                    : '(null)'}
                </div>
              </div>

              {/* Parsed Deterministic Value with wrapping */}
              <div className="p-2.5 bg-white dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800 space-y-1">
                <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-bold tracking-wider">
                  {dictionary.grid.parsedValue}
                </span>
                <div className="font-mono font-semibold text-slate-900 dark:text-slate-100 text-xs whitespace-pre-wrap break-words max-h-36 overflow-y-auto">
                  {selectedCell.parsed_value !== null && selectedCell.parsed_value !== undefined
                    ? String(selectedCell.parsed_value)
                    : '(null)'}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
              <div>
                <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-bold">{dictionary.grid.dataType}</span>
                <span className="font-mono text-xs px-2 py-0.5 bg-white dark:bg-slate-950 rounded border border-slate-200 dark:border-slate-800 font-semibold text-slate-800 dark:text-slate-200 inline-block mt-0.5">
                  {selectedCell.data_type}
                </span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-bold">{dictionary.grid.formula}</span>
                <span className="font-mono text-xs text-amber-800 dark:text-amber-400 inline-block mt-0.5 font-semibold">
                  {selectedCell.formula || dictionary.common.none}
                </span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-bold">Row Index</span>
                <span className="font-mono text-xs text-slate-800 dark:text-slate-200 inline-block mt-0.5">
                  Row {selectedCell.coordinate.row}
                </span>
              </div>
              <div>
                <span className="text-slate-500 dark:text-slate-400 block text-[10px] uppercase font-bold">Column Index</span>
                <span className="font-mono text-xs text-slate-800 dark:text-slate-200 inline-block mt-0.5">
                  Col {selectedCell.coordinate.column}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Side AI Agent Chat Panel */}
      {showAgentPanel && (
        <div className="w-full lg:w-96 shrink-0 h-[620px] sticky top-4">
          <GridAIChatPanel
            datasetId={datasetId}
            activeSheetName={sheetName}
            selectedRange={selectedRange || undefined}
            onClearSelection={() => setSelectedRange(null)}
            onGridUpdated={fetchGrid}
            onFocusCell={handleFocusCell}
            onClose={() => setShowAgentPanel(false)}
          />
        </div>
      )}

      <ChartFullscreenModal
        isOpen={!!selectedChartForModal}
        onClose={() => setSelectedChartForModal(null)}
        chart={selectedChartForModal}
      />
    </div>
  );
};
