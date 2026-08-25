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
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300">
            <span>Vertical Table ({confPct}%)</span>
          </span>
        );
      case 'HORIZONTAL':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-50 text-blue-800 border border-blue-300">
            <span>Horizontal Layout ({confPct}%)</span>
          </span>
        );
      case 'AMBIGUOUS':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-800 border border-amber-300">
            <span>Ambiguous Layout ({confPct}%)</span>
          </span>
        );
      case 'IRREGULAR':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-800 border border-rose-300">
            <span>Irregular Structure ({confPct}%)</span>
          </span>
        );
    }
  };

  const getDataTypeBadge = (dt: DataType) => {
    return (
      <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-semibold bg-slate-100 text-slate-700 border border-slate-200">
        {dt}
      </span>
    );
  };

  const getSemanticBadge = (sem: SemanticType) => {
    const labels: Record<SemanticType, { text: string; style: string }> = {
      numeric_measure: { text: 'Measure', style: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
      categorical: { text: 'Category', style: 'bg-slate-100 text-slate-800 border-slate-300' },
      temporal: { text: 'Temporal', style: 'bg-purple-50 text-purple-800 border-purple-200' },
      identifier: { text: 'Identifier', style: 'bg-amber-50 text-amber-900 border-amber-200 font-bold' },
      text: { text: 'Text', style: 'bg-slate-100 text-slate-600 border-slate-200' },
      boolean: { text: 'Boolean', style: 'bg-pink-50 text-pink-800 border-pink-200' },
      unknown: { text: 'Unknown', style: 'bg-gray-100 text-gray-500 border-gray-200' },
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
      <div className="p-8 text-center bg-white rounded-lg border border-slate-200">
        <p className="text-xs text-slate-500">{dictionary.tables.noTables}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {tables.map((table, idx) => (
        <div key={table.table_id || idx} className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
          {/* Table Header Card */}
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center space-x-3">
              <div className="w-7 h-7 rounded bg-slate-900 text-white flex items-center justify-center font-bold text-xs font-mono">
                T{idx + 1}
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900 flex items-center space-x-2">
                  <span>{table.name}</span>
                  <span className="font-mono text-[11px] text-slate-500 font-normal">({table.range_address})</span>
                </h3>
                <div className="flex items-center space-x-2 text-[11px] text-slate-500 mt-0.5">
                  <span>
                    <strong>{table.row_count}</strong> {dictionary.common.rows}
                  </span>
                  <span>•</span>
                  <span>
                    <strong>{table.column_count}</strong> {dictionary.common.columns}
                  </span>
                  {table.header_range && (
                    <>
                      <span>•</span>
                      <span>
                        Header: <code className="bg-slate-200/80 px-1 py-0.2 rounded text-[10px] font-mono">{table.header_range}</code>
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
            <div className="px-4 py-2 bg-slate-50/80 border-b border-slate-200 text-[11px] text-slate-600">
              <span className="font-semibold text-slate-700 mr-2">Structural Signals:</span>
              <span className="text-slate-600">{table.orientation_reasons.join(' ')}</span>
            </div>
          )}

          {/* Detected Columns Schema */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-600 border-b border-slate-200 uppercase tracking-wider text-[10px]">
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
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {table.columns.map((col) => (
                  <tr key={col.index} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-3.5 py-2 font-mono text-slate-400 text-center">{col.index + 1}</td>
                    <td className="px-3.5 py-2 font-semibold text-slate-900">{col.name}</td>
                    <td className="px-3.5 py-2 font-mono text-slate-500 text-[11px]">
                      Col {col.source_column_letter} {col.original_header_cell ? `(${col.original_header_cell})` : ''}
                    </td>
                    <td className="px-3.5 py-2">{getDataTypeBadge(col.data_type)}</td>
                    <td className="px-3.5 py-2">{getSemanticBadge(col.semantic_type)}</td>
                    <td className="px-3.5 py-2 text-right font-mono">
                      {col.null_count > 0 ? (
                        <span className="text-amber-700 font-bold">{col.null_count}</span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                    <td className="px-3.5 py-2 text-right font-mono">{col.unique_count}</td>
                    <td className="px-3.5 py-2 font-mono text-[11px] text-slate-600 truncate max-w-xs">
                      {col.sample_values && col.sample_values.length > 0 ? (
                        col.sample_values.map((v, i) => (
                          <span key={i} className="inline-block bg-slate-100 px-1 py-0.2 rounded mr-1 mb-0.5 border border-slate-200">
                            {String(v)}
                          </span>
                        ))
                      ) : (
                        <span className="text-slate-400">-</span>
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
