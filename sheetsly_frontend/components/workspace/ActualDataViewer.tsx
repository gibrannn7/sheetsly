'use client';

import React, { useEffect, useState } from 'react';
import { api } from '../../lib/api';
import { useTranslation } from '../../lib/i18n';
import { CellData, SheetDataGridResponse } from '../../lib/types';

interface ActualDataViewerProps {
  datasetId: string;
  sheetName: string;
}

export const ActualDataViewer: React.FC<ActualDataViewerProps> = ({ datasetId, sheetName }) => {
  const { dictionary, t } = useTranslation();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [gridData, setGridData] = useState<SheetDataGridResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCell, setSelectedCell] = useState<CellData | null>(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    setSelectedCell(null);

    api
      .getSheetDataGrid(datasetId, sheetName, page, pageSize)
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
  }, [datasetId, sheetName, page, pageSize]);

  const totalPages = gridData ? Math.max(1, Math.ceil(gridData.total_rows / pageSize)) : 1;

  const isNumericValue = (cell: CellData) => {
    return ['integer', 'float', 'currency', 'percentage'].includes(cell.data_type);
  };

  return (
    <div className="space-y-4">
      {/* Grid Container */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
        <div className="p-3 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              {dictionary.grid.title} ({sheetName})
            </h3>
          </div>
          {gridData && (
            <div className="text-[11px] text-slate-500 font-mono">
              Showing rows {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, gridData.total_rows)} of {gridData.total_rows}
            </div>
          )}
        </div>

        {isLoading ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <p className="font-semibold text-slate-700">{dictionary.common.loading}</p>
            <p className="text-[11px] text-slate-400 mt-0.5">{dictionary.grid.desc}</p>
          </div>
        ) : !gridData || gridData.rows.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No data rows found in this sheet.</div>
        ) : (
          <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-left text-xs border-collapse font-sans border-spacing-0">
              <thead className="bg-slate-100 text-slate-600 sticky top-0 z-10 font-mono text-[11px] border-b border-slate-300">
                <tr>
                  <th className="w-12 px-2.5 py-1.5 text-center bg-slate-200 text-slate-600 font-bold border-r border-slate-300 select-none">
                    #
                  </th>
                  {gridData.column_headers.map((colLetter, cIdx) => (
                    <th key={cIdx} className="px-3 py-1.5 font-bold text-center border-r border-slate-300 min-w-[120px] select-none">
                      {colLetter}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-slate-800">
                {gridData.rows.map((rowCells, rIdx) => {
                  const rowNumber = rowCells[0]?.coordinate.row ?? (page - 1) * pageSize + rIdx + 1;
                  return (
                    <tr key={rIdx} className="hover:bg-slate-50 transition-colors">
                      <td className="px-2 py-1 text-center font-mono text-slate-500 bg-slate-100 border-r border-slate-300 font-semibold select-none text-[11px]">
                        {rowNumber}
                      </td>
                      {rowCells.map((cell, cIdx) => {
                        const isSelected = selectedCell?.coordinate.cell_ref === cell.coordinate.cell_ref;
                        const isNum = isNumericValue(cell);
                        return (
                          <td
                            key={cIdx}
                            onClick={() => setSelectedCell(cell)}
                            className={`px-2.5 py-1 border-r border-slate-200 truncate max-w-[220px] cursor-pointer transition-all ${
                              isSelected
                                ? 'bg-slate-200 ring-2 ring-slate-900 font-semibold text-slate-900 z-10 relative'
                                : cell.is_empty
                                ? 'bg-slate-50/40 text-slate-300'
                                : ''
                            } ${isNum ? 'text-right font-mono' : 'text-left'}`}
                            title={`Cell ${cell.coordinate.cell_ref}: ${cell.original_value ?? '(empty)'}`}
                          >
                            <div className={`flex items-center ${isNum ? 'justify-end' : 'justify-between'}`}>
                              <span className="truncate">
                                {cell.is_empty ? '-' : String(cell.original_value)}
                              </span>
                              {cell.formula && (
                                <span className="ml-1 px-1 py-0.2 rounded bg-amber-100 text-amber-800 text-[9px] font-mono font-bold flex-shrink-0">
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

        {/* Pagination Bar */}
        {gridData && gridData.total_rows > pageSize && (
          <div className="p-2.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs">
            <span className="text-slate-500 font-mono text-[11px]">
              {t('grid.pageOf', { page, totalPages })}
            </span>
            <div className="flex items-center space-x-1.5">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-2.5 py-1 bg-white border border-slate-300 rounded text-slate-700 disabled:opacity-40 hover:bg-slate-50 cursor-pointer disabled:cursor-not-allowed text-xs font-medium"
              >
                {dictionary.grid.prev}
              </button>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-2.5 py-1 bg-white border border-slate-300 rounded text-slate-700 disabled:opacity-40 hover:bg-slate-50 cursor-pointer disabled:cursor-not-allowed text-xs font-medium"
              >
                {dictionary.grid.next}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Selected Cell Trace Details */}
      {selectedCell && (
        <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-300 text-xs space-y-2">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="flex items-center space-x-2">
              <span className="font-mono font-bold text-xs bg-slate-900 text-white px-2 py-0.5 rounded">
                {selectedCell.coordinate.cell_ref}
              </span>
              <span className="font-semibold text-slate-800">{dictionary.grid.cellInspection}</span>
            </div>
            <button
              type="button"
              onClick={() => setSelectedCell(null)}
              className="text-slate-400 hover:text-slate-700 text-xs font-bold cursor-pointer px-1"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-slate-700 pt-1">
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">{dictionary.grid.originalValue}</span>
              <span className="font-mono font-semibold text-slate-900">
                {selectedCell.original_value !== null ? String(selectedCell.original_value) : '(null)'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">{dictionary.grid.parsedValue}</span>
              <span className="font-mono font-semibold text-slate-900">
                {selectedCell.parsed_value !== null ? String(selectedCell.parsed_value) : '(null)'}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">{dictionary.grid.dataType}</span>
              <span className="font-mono px-1.5 py-0.2 bg-white rounded border border-slate-200 font-semibold text-slate-800">
                {selectedCell.data_type}
              </span>
            </div>
            <div>
              <span className="text-slate-500 block text-[10px] uppercase font-bold">{dictionary.grid.formula}</span>
              <span className="font-mono text-amber-800">
                {selectedCell.formula || dictionary.common.none}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
