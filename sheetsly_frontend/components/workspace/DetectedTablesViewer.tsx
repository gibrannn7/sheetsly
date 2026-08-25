'use client';

import React from 'react';
import { useTranslation } from '../../lib/i18n';
import { DataType, OrientationType, SemanticType, TableRegion } from '../../lib/types';

interface DetectedTablesViewerProps {
  tables: TableRegion[];
  sheetName: string;
}

export const DetectedTablesViewer: React.FC<DetectedTablesViewerProps> = ({ tables, sheetName }) => {
  const { dictionary } = useTranslation();

  const getOrientationBadge = (orientation: OrientationType, confidence: number) => {
    const confPct = Math.round(confidence * 100);
    switch (orientation) {
      case 'VERTICAL':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
            <span>Vertical Table ({confPct}%)</span>
          </span>
        );
      case 'HORIZONTAL':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-800 dark:text-blue-300 border border-blue-300 dark:border-blue-800">
            <span>Horizontal Layout ({confPct}%)</span>
          </span>
        );
      case 'AMBIGUOUS':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
            <span>Ambiguous Layout ({confPct}%)</span>
          </span>
        );
      case 'IRREGULAR':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800">
            <span>Irregular Structure ({confPct}%)</span>
          </span>
        );
    }
  };

  const getDataTypeBadge = (dt: DataType) => {
    return (
      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
        {dt}
      </span>
    );
  };

  const getSemanticBadge = (sem: SemanticType) => {
    const labels: Record<SemanticType, { text: string; style: string }> = {
      numeric_measure: { text: 'Measure', style: 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800' },
      categorical: { text: 'Category', style: 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border-slate-300 dark:border-slate-700' },
      temporal: { text: 'Temporal', style: 'bg-purple-50 dark:bg-purple-950/50 text-purple-800 dark:text-purple-300 border-purple-200 dark:border-purple-800' },
      identifier: { text: 'Identifier', style: 'bg-amber-50 dark:bg-amber-950/50 text-amber-900 dark:text-amber-300 border-amber-200 dark:border-amber-800 font-bold' },
      text: { text: 'Text', style: 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700' },
      boolean: { text: 'Boolean', style: 'bg-pink-50 dark:bg-pink-950/50 text-pink-800 dark:text-pink-300 border-pink-200 dark:border-pink-800' },
      unknown: { text: 'Unknown', style: 'bg-gray-100 dark:bg-slate-800 text-gray-500 dark:text-slate-400 border-gray-200 dark:border-slate-700' },
    };
    const conf = labels[sem] || labels.unknown;
    return (
      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${conf.style}`}>
        {conf.text}
      </span>
    );
  };

  if (tables.length === 0) {
    return (
      <div className="p-8 text-center bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800">
        <p className="text-xs text-slate-500 dark:text-slate-400">{dictionary.tables.noTables}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {tables.map((table, idx) => (
        <div key={table.table_id || idx} className="bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 shadow-2xs overflow-hidden transition-colors">
          {/* Table Header Card */}
          <div className="p-4 bg-slate-50 dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 transition-colors">
            <div className="flex items-center space-x-3">
              <div className="w-7 h-7 rounded bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 flex items-center justify-center font-bold text-xs font-mono shadow-2xs">
                T{idx + 1}
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center space-x-2">
                  <span>{table.name}</span>
                  <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400 font-normal">({table.range_address})</span>
                </h3>
                <div className="flex items-center space-x-2 text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  <span>
                    <strong className="text-slate-800 dark:text-slate-200">{table.row_count}</strong> {dictionary.common.rows}
                  </span>
                  <span>•</span>
                  <span>
                    <strong className="text-slate-800 dark:text-slate-200">{table.column_count}</strong> {dictionary.common.columns}
                  </span>
                  {table.header_range && (
                    <>
                      <span>•</span>
                      <span>
                        Header: <code className="bg-slate-200/80 dark:bg-slate-800 px-1 py-0.2 rounded text-[10px] font-mono text-slate-800 dark:text-slate-200">{table.header_range}</code>
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {getOrientationBadge(table.orientation, table.orientation_confidence)}
            </div>
          </div>

          {/* Orientation Evidence Reasons */}
          {table.orientation_reasons && table.orientation_reasons.length > 0 && (
            <div className="px-4 py-2 bg-slate-50/80 dark:bg-slate-950/80 border-b border-slate-200 dark:border-slate-800 text-[11px] text-slate-600 dark:text-slate-400">
              <span className="font-semibold text-slate-700 dark:text-slate-300 mr-2">Structural Signals:</span>
              <span className="text-slate-600 dark:text-slate-400">{table.orientation_reasons.join(' ')}</span>
            </div>
          )}

          {/* Detected Columns Schema */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-3.5 py-2 font-bold w-12 text-center">#</th>
                  <th className="px-3.5 py-2 font-bold">{dictionary.tables.columnName}</th>
                  <th className="px-3.5 py-2 font-bold">Source Ref</th>
                  <th className="px-3.5 py-2 font-bold">{dictionary.tables.dataType}</th>
                  <th className="px-3.5 py-2 font-bold">{dictionary.tables.semanticType}</th>
                  <th className="px-3.5 py-2 font-bold text-right">{dictionary.tables.nulls}</th>
                  <th className="px-3.5 py-2 font-bold text-right">{dictionary.tables.uniques}</th>
                  <th className="px-3.5 py-2 font-bold">{dictionary.tables.samples}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-mono">
                {table.columns.map((col) => (
                  <tr key={col.index} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-3.5 py-2 text-slate-400 dark:text-slate-500 text-center">{col.index + 1}</td>
                    <td className="px-3.5 py-2 font-semibold text-slate-900 dark:text-slate-100 font-sans">{col.name}</td>
                    <td className="px-3.5 py-2 text-slate-500 dark:text-slate-400 text-[11px]">
                      Col {col.source_column_letter} {col.original_header_cell ? `(${col.original_header_cell})` : ''}
                    </td>
                    <td className="px-3.5 py-2">{getDataTypeBadge(col.data_type)}</td>
                    <td className="px-3.5 py-2">{getSemanticBadge(col.semantic_type)}</td>
                    <td className="px-3.5 py-2 text-right">
                      {col.null_count > 0 ? (
                        <span className="text-amber-700 dark:text-amber-400 font-bold">{col.null_count}</span>
                      ) : (
                        <span className="text-slate-400 dark:text-slate-500">0</span>
                      )}
                    </td>
                    <td className="px-3.5 py-2 text-right">{col.unique_count}</td>
                    <td className="px-3.5 py-2 text-[11px] text-slate-600 dark:text-slate-400 truncate max-w-xs">
                      {col.sample_values && col.sample_values.length > 0 ? (
                        col.sample_values.map((v, i) => (
                          <span key={i} className="inline-block bg-slate-100 dark:bg-slate-800 px-1 py-0.2 rounded mr-1 mb-0.5 border border-slate-200 dark:border-slate-700">
                            {String(v)}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-400 dark:text-slate-500">-</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
};
