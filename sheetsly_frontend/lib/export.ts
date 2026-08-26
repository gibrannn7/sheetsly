/**
 * Deterministic client-side CSV export utility for spreadsheet data slices and analytical results.
 * Preserves numbers, strings, dates, and quotes values containing commas or newlines.
 */

export function downloadCsv(filename: string, csvContent: string): void {
  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function escapeCsvCell(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  const str = String(value);
  if (str.includes(',') || str.includes('"') || str.includes('\n') || str.includes('\r')) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

export function tableToCsv(headers: string[], rows: unknown[][]): string {
  const headerRow = headers.map(escapeCsvCell).join(',');
  const dataRows = rows.map((row) => row.map(escapeCsvCell).join(',')).join('\n');
  return `${headerRow}\n${dataRows}`;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export async function downloadWorkbookExport(
  datasetId: string,
  format: 'xlsx' | 'csv',
  sheetName?: string,
  defaultFilename?: string
): Promise<void> {
  const url = new URL(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}/export`);
  url.searchParams.append('format', format);
  if (sheetName) {
    url.searchParams.append('sheet_name', sheetName);
  }

  const response = await fetch(url.toString(), { method: 'GET' });
  if (!response.ok) {
    throw new Error(`Failed to export workbook: ${response.statusText}`);
  }

  // Extract filename from content-disposition header if present
  let filename = defaultFilename || `export.${format}`;
  const disposition = response.headers.get('content-disposition');
  if (disposition && disposition.includes('filename=')) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  const blob = await response.blob();
  const downloadUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(downloadUrl);
}
