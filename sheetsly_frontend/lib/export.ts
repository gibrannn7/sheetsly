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
