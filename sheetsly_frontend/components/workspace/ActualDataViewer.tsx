'use client';

import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import { CellData, SheetDataGridResponse } from '../../lib/types';

interface ActualDataViewerProps {
  datasetId: string;
  sheetName: string;
}

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

export const ActualDataViewer: React.FC<ActualDataViewerProps> = ({ datasetId, sheetName }) => {
  const { dictionary, t } = useTranslation();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [gridData, setGridData] = useState<SheetDataGridResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCell, setSelectedCell] = useState<CellData | null>(null);

  // Debounce search query input (150ms for responsive, snappy typing)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 150);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Reset page to 1 and clear search if sheetName changes
  useEffect(() => {
    setPage(1);
    setSearchQuery('');
    setDebouncedQuery('');
    setSelectedCell(null);
  }, [sheetName, datasetId]);

  // Fetch paginated grid slice whenever sheet, page, pageSize, or debouncedQuery changes
  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setSelectedCell(null);

    api
      .getSheetDataGrid(datasetId, sheetName, page, pageSize, debouncedQuery)
      .then((data) => {
        if (isMounted) {
          setGridData(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error('Failed to load sheet grid', err);
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [datasetId, sheetName, page, pageSize, debouncedQuery]);

  const totalRows = gridData?.total_rows ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));

  const startRow = totalRows === 0 ? 0 : (page - 1) * pageSize + 1;
  const endRow = Math.min(page * pageSize, totalRows);

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setPage(1); // Reset to page 1 to prevent out-of-bounds page jumps
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setDebouncedQuery('');
    setPage(1);
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

  // Generate compact pagination item list (e.g. 1 2 3 ... 10)
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

  const isSearching = debouncedQuery.trim().length > 0;

  return (
    <div className="space-y-4">
      {/* Grid Container */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        {/* Header Toolbar */}
        <div className="p-3 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
          {/* Left: Sheet Title + Search Input */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-1.5">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                {dictionary.grid.title}
              </h3>
              <span className="text-slate-500 font-mono text-xs font-normal">({sheetName})</span>
            </div>

            {/* Search Input Box */}
            <div className="relative flex items-center min-w-[200px] sm:min-w-[240px]">
              <div className="absolute left-2.5 text-slate-400 pointer-events-none flex items-center">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setPage(1);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    handleClearSearch();
                  }
                }}
                placeholder={dictionary.grid.searchPlaceholder}
                aria-label={dictionary.grid.searchPlaceholder}
                className="w-full bg-white border border-slate-300 rounded-md pl-8 pr-7 py-1 text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-1 focus:ring-slate-900 focus:border-slate-900 transition-colors shadow-2xs"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  aria-label={dictionary.grid.clearSearch}
                  title={dictionary.grid.clearSearch}
                  className="absolute right-1.5 p-1 text-slate-400 hover:text-slate-700 rounded cursor-pointer hover:bg-slate-100 transition-colors"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>

            {/* Matching Result Badge */}
            {isSearching && !isLoading && gridData && (
              <span className="text-[11px] font-mono text-slate-700 bg-slate-200/70 border border-slate-300 px-2 py-0.5 rounded font-medium select-none">
                {t('grid.matchingRows', { count: totalRows.toLocaleString() })}
              </span>
            )}
          </div>

          {/* Right: Page Size Selector + Row Range */}
          <div className="flex items-center space-x-3">
            {/* Page Size Selector */}
            <div className="flex items-center space-x-1.5 text-xs text-slate-600">
              <span className="text-[11px] font-medium">{dictionary.grid.rowsPerPage}</span>
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(Number(e.target.value))}
                aria-label={dictionary.grid.rowsPerPage}
                className="bg-white border border-slate-300 rounded px-2 py-0.5 text-xs font-mono font-medium text-slate-800 focus:outline-hidden focus:ring-1 focus:ring-slate-900 cursor-pointer shadow-2xs"
              >
                {PAGE_SIZE_OPTIONS.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </select>
            </div>

            {/* Row Range Metadata */}
            {gridData && totalRows > 0 && (
              <div className="text-[11px] text-slate-600 font-mono tabular-nums bg-white border border-slate-200 px-2 py-0.5 rounded shadow-2xs">
                {t('grid.showingRows', { start: startRow, end: endRow, total: totalRows.toLocaleString() })}
              </div>
            )}
          </div>
        </div>

        {/* Spreadsheet Data Surface */}
        {isLoading ? (
          <div className="p-14 text-center text-slate-500 text-xs space-y-1">
            <p className="font-semibold text-slate-700">{dictionary.common.loading}</p>
            <p className="text-[11px] text-slate-400">{dictionary.grid.desc}</p>
          </div>
        ) : !gridData || gridData.rows.length === 0 ? (
          isSearching ? (
            <div className="p-12 text-center space-y-2 bg-white">
              <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                {dictionary.grid.noMatchingRowsTitle}
              </h4>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                {t('grid.noMatchingRowsDesc', { query: debouncedQuery })}
              </p>
              <div className="pt-1">
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded border border-slate-300 text-xs font-medium cursor-pointer transition-colors shadow-2xs"
                >
                  {dictionary.grid.clearSearch}
                </button>
              </div>
            </div>
          ) : (
            <div className="p-14 text-center text-slate-400 text-xs">
              {dictionary.grid.noRows}
            </div>
          )
        ) : (
          <div className="overflow-x-auto max-h-[520px]">
            <table className="w-full text-left text-xs border-collapse font-sans border-spacing-0">
              <thead className="bg-slate-100 text-slate-600 sticky top-0 z-10 font-mono text-[11px] border-b border-slate-300 shadow-2xs">
                <tr>
                  <th className="w-12 min-w-[48px] px-2.5 py-1.5 text-center bg-slate-200 text-slate-600 font-bold border-r border-slate-300 select-none">
                    #
                  </th>
                  {gridData.column_headers.map((colLetter, cIdx) => (
                    <th
                      key={cIdx}
                      className="px-3 py-1.5 font-bold text-center border-r border-slate-300 min-w-[110px] select-none text-slate-700"
                    >
                      {colLetter}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-800">
                {gridData.rows.map((rowCells, rIdx) => {
                  const rowNumber = rowCells[0]?.coordinate.row ?? (page - 1) * pageSize + rIdx + 1;
                  return (
                    <tr key={rIdx} className="hover:bg-slate-50/80 transition-colors group">
                      <td className="px-2 py-1 text-center font-mono text-slate-500 bg-slate-100/90 border-r border-slate-300 font-semibold select-none text-[11px] tabular-nums">
                        {rowNumber}
                      </td>
                      {rowCells.map((cell, cIdx) => {
                        const isSelected = selectedCell?.coordinate.cell_ref === cell.coordinate.cell_ref;
                        const isMatched = isCellMatch(cell);
                        const isNum = isNumericValue(cell);
                        const isDate = isDateValue(cell);
                        const rawString = cell.original_value !== null && cell.original_value !== undefined
                          ? String(cell.original_value)
                          : '';

                        const cellTooltip = `Cell ${cell.coordinate.cell_ref} (${cell.data_type})\nValue: ${rawString || '(empty)'}${
                          cell.formula ? `\nFormula: ${cell.formula}` : ''
                        }`;

                        return (
                          <td
                            key={cIdx}
                            onClick={() => setSelectedCell(cell)}
                            title={cellTooltip}
                            className={`px-2.5 py-1 border-r border-slate-200 cursor-pointer transition-all ${
                              isNum
                                ? 'min-w-[100px] max-w-[160px] text-right font-mono tabular-nums'
                                : isDate
                                ? 'min-w-[110px] max-w-[150px] font-mono text-center'
                                : 'min-w-[130px] max-w-[240px] text-left'
                            } ${
                              isSelected
                                ? 'bg-slate-200 ring-2 ring-slate-900 font-semibold text-slate-900 z-10 relative'
                                : isMatched
                                ? 'bg-amber-50 text-amber-950 font-medium'
                                : cell.is_empty
                                ? 'bg-slate-50/30 text-slate-300'
                                : 'hover:bg-slate-100/60'
                            }`}
                          >
                            <div className={`flex items-center ${isNum ? 'justify-end' : 'justify-between'} gap-1.5`}>
                              <span
                                className={`truncate block ${cell.is_empty ? 'text-slate-300 font-mono' : ''} ${
                                  isMatched ? 'font-semibold text-slate-950' : ''
                                }`}
                              >
                                {cell.is_empty ? '-' : rawString}
                              </span>
                              {cell.formula && (
                                <span className="px-1 py-0.2 rounded bg-amber-100 text-amber-800 text-[9px] font-mono font-bold shrink-0 select-none">
                                  fx
                                </span>
                              )}
                            </div>
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
        {gridData && totalPages > 1 && (
          <div className="p-3 bg-slate-50 border-t border-slate-200 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-center space-x-2 text-slate-500 font-mono text-[11px] tabular-nums">
              <span>{t('grid.pageOf', { page, totalPages })}</span>
              <span>•</span>
              <span>{t('grid.showingRows', { start: startRow, end: endRow, total: totalRows.toLocaleString() })}</span>
            </div>

            <div className="flex items-center space-x-1">
              {/* Previous Button */}
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 bg-white border border-slate-300 rounded text-slate-700 disabled:opacity-40 hover:bg-slate-50 cursor-pointer disabled:cursor-not-allowed text-xs font-medium focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-slate-900"
              >
                {dictionary.grid.prev}
              </button>

              {/* Numbered Page Buttons with Smart Ellipsis */}
              {getPaginationItems().map((item, idx) => {
                if (typeof item === 'string') {
                  return (
                    <span
                      key={`ellipsis-${idx}`}
                      className="px-2 py-1 text-slate-400 font-mono select-none text-xs"
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
                    onClick={() => setPage(item)}
                    aria-current={isCurrent ? 'page' : undefined}
                    className={`min-w-[28px] px-2 py-1 text-xs font-mono font-semibold rounded border transition-colors cursor-pointer focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-slate-900 ${
                      isCurrent
                        ? 'bg-slate-900 text-white border-slate-900 shadow-2xs'
                        : 'bg-white text-slate-700 border-slate-300 hover:bg-slate-100'
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
                className="px-2.5 py-1 bg-white border border-slate-300 rounded text-slate-700 disabled:opacity-40 hover:bg-slate-50 cursor-pointer disabled:cursor-not-allowed text-xs font-medium focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-slate-900"
              >
                {dictionary.grid.next}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Selected Cell Full Raw Value & Metadata Inspector */}
      {selectedCell && (
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-300 text-xs space-y-3 shadow-2xs animate-in fade-in duration-100">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2.5">
            <div className="flex items-center space-x-2.5">
              <span className="font-mono font-bold text-xs bg-slate-900 text-white px-2 py-0.5 rounded shadow-2xs">
                {selectedCell.coordinate.cell_ref}
              </span>
              <span className="font-bold text-slate-900">{dictionary.grid.cellInspection}</span>
            </div>
            <button
              type="button"
              onClick={() => setSelectedCell(null)}
              aria-label={dictionary.common.close}
              className="text-slate-400 hover:text-slate-700 text-xs font-bold cursor-pointer p-1 rounded hover:bg-slate-200 transition-colors"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-700">
            {/* Full Original Value with wrapping */}
            <div className="p-2.5 bg-white rounded border border-slate-200 space-y-1">
              <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">
                {dictionary.grid.originalValue}
              </span>
              <div className="font-mono font-semibold text-slate-900 text-xs whitespace-pre-wrap break-words max-h-36 overflow-y-auto">
                {selectedCell.original_value !== null && selectedCell.original_value !== undefined
                  ? String(selectedCell.original_value)
                  : '(null)'}
              </div>
            </div>

            {/* Parsed Deterministic Value with wrapping */}
            <div className="p-2.5 bg-white rounded border border-slate-200 space-y-1">
              <span className="text-slate-500 block text-[10px] uppercase font-bold tracking-wider">
                {dictionary.grid.parsedValue}
              </span>
              <div className="font-mono font-semibold text-slate-900 text-xs whitespace-pre-wrap break-words max-h-36 overflow-y-auto">
                {selectedCell.parsed_value !== null && selectedCell.parsed_value !== undefined
                  ? String(selectedCell.parsed_value)
                  : '(null)'}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">{dictionary.grid.dataType}</span>
              <span className="font-mono text-xs px-2 py-0.5 bg-white rounded border border-slate-200 font-semibold text-slate-800 inline-block mt-0.5">
                {selectedCell.data_type}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">{dictionary.grid.formula}</span>
              <span className="font-mono text-xs text-amber-800 inline-block mt-0.5 font-semibold">
                {selectedCell.formula || dictionary.common.none}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">Row Index</span>
              <span className="font-mono text-xs text-slate-800 inline-block mt-0.5">
                Row {selectedCell.coordinate.row}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">Column Index</span>
              <span className="font-mono text-xs text-slate-800 inline-block mt-0.5">
                Col {selectedCell.coordinate.column}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
