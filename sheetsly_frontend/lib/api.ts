/**
 * Sheetsly API client communicating with FastAPI backend.
 */

import {
  AIStatusResponse,
  AnalyticalInstruction,
  AnalyticalResult,
  ChartRecommendation,
  ChartType,
  NaturalLanguageQueryRequest,
  NaturalLanguageQueryResponse,
  QueryPlanOnlyResponse,
  SheetDataGridResponse,
  SheetMetadata,
  SmartGenerateRequest,
  SmartGenerateResponse,
  SuggestedQueriesResponse,
  VisualizationResponse,
  WorkbookOverview,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  code: string;
  details?: Record<string, any>;
  statusCode: number;

  constructor(message: string, code: string = 'API_ERROR', statusCode: number = 500, details?: Record<string, any>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      errorData = { error: { message: response.statusText, code: 'HTTP_ERROR' } };
    }
    const err = errorData.error || errorData;
    throw new ApiError(
      err.message || 'An error occurred during API request',
      err.code || 'HTTP_ERROR',
      response.status,
      err.details
    );
  }
  return response.json();
}

export const api = {
  async checkHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse(res);
  },

  async uploadSpreadsheet(file: File): Promise<WorkbookOverview> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<WorkbookOverview>(res);
  },

  async getDatasetOverview(datasetId: string): Promise<WorkbookOverview> {
    const res = await fetch(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}`);
    return handleResponse<WorkbookOverview>(res);
  },

  async getSheetMetadata(datasetId: string, sheetName: string): Promise<SheetMetadata> {
    const res = await fetch(
      `${API_BASE}/datasets/${encodeURIComponent(datasetId)}/sheets/${encodeURIComponent(sheetName)}`
    );
    return handleResponse<SheetMetadata>(res);
  },

  async getSheetDataGrid(
    datasetId: string,
    sheetName: string,
    page: number = 1,
    pageSize: number = 50,
    search?: string
  ): Promise<SheetDataGridResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (search && search.trim()) {
      params.append('q', search.trim());
    }
    const res = await fetch(
      `${API_BASE}/datasets/${encodeURIComponent(datasetId)}/sheets/${encodeURIComponent(sheetName)}/data?${params}`
    );
    return handleResponse<SheetDataGridResponse>(res);
  },

  async analyzeDataset(datasetId: string, instruction: AnalyticalInstruction): Promise<AnalyticalResult> {
    const res = await fetch(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(instruction),
    });
    return handleResponse<AnalyticalResult>(res);
  },

  async getOperationsCatalog(): Promise<any> {
    const res = await fetch(`${API_BASE}/operations/catalog`);
    return handleResponse(res);
  },

  async visualizeResult(
    datasetId: string,
    result: AnalyticalResult,
    chartType?: ChartType,
    title?: string
  ): Promise<VisualizationResponse> {
    const res = await fetch(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}/visualize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dataset_id: datasetId,
        analytical_result: result,
        chart_type: chartType,
        title,
      }),
    });
    return handleResponse<VisualizationResponse>(res);
  },

  async visualizeFromInstruction(
    datasetId: string,
    instruction: AnalyticalInstruction,
    chartType?: ChartType,
    title?: string
  ): Promise<VisualizationResponse> {
    const res = await fetch(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}/visualize/from-instruction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        instruction,
        chart_type: chartType,
        title,
      }),
    });
    return handleResponse<VisualizationResponse>(res);
  },

  async smartGenerateCharts(
    datasetId: string,
    request: SmartGenerateRequest = {}
  ): Promise<SmartGenerateResponse> {
    const res = await fetch(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}/visualize/smart-generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<SmartGenerateResponse>(res);
  },

  async recommendChart(result: AnalyticalResult): Promise<ChartRecommendation> {
    const res = await fetch(`${API_BASE}/visualization/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(result),
    });
    return handleResponse<ChartRecommendation>(res);
  },

  getChartImageUrl(datasetId: string, chartId: string): string {
    return `${API_BASE}/datasets/${encodeURIComponent(datasetId)}/charts/${encodeURIComponent(chartId)}/image`;
  },

  resolveImageUrl(relativeOrAbsoluteUrl: string): string {
    if (!relativeOrAbsoluteUrl) return '';
    if (relativeOrAbsoluteUrl.startsWith('http://') || relativeOrAbsoluteUrl.startsWith('https://')) {
      return relativeOrAbsoluteUrl;
    }
    // Remove trailing /api/v1 from API_BASE if relativeUrl already contains /api/v1
    const baseWithoutApi = API_BASE.replace(/\/api\/v1\/?$/, '');
    const cleanPath = relativeOrAbsoluteUrl.startsWith('/') ? relativeOrAbsoluteUrl : `/${relativeOrAbsoluteUrl}`;
    return `${baseWithoutApi}${cleanPath}`;
  },

  async deleteDataset(datasetId: string): Promise<void> {
    await fetch(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}`, {
      method: 'DELETE',
    });
  },

  // --------------------------------------------------------------------------
  // AI Query Planning & Execution (Phase 8)
  // --------------------------------------------------------------------------

  async getAIStatus(): Promise<AIStatusResponse> {
    const res = await fetch(`${API_BASE}/ai/status`);
    return handleResponse<AIStatusResponse>(res);
  },

  async queryWithAI(request: NaturalLanguageQueryRequest): Promise<NaturalLanguageQueryResponse> {
    const res = await fetch(`${API_BASE}/ai/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<NaturalLanguageQueryResponse>(res);
  },

  async planQueryWithAI(request: NaturalLanguageQueryRequest): Promise<QueryPlanOnlyResponse> {
    const res = await fetch(`${API_BASE}/ai/plan-only`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<QueryPlanOnlyResponse>(res);
  },

  async getSuggestedQueries(datasetId: string, sheetName?: string): Promise<SuggestedQueriesResponse> {
    const url = sheetName
      ? `${API_BASE}/ai/suggest/${encodeURIComponent(datasetId)}?sheet_name=${encodeURIComponent(sheetName)}`
      : `${API_BASE}/ai/suggest/${encodeURIComponent(datasetId)}`;
    const res = await fetch(url);
    return handleResponse<SuggestedQueriesResponse>(res);
  },

  // --------------------------------------------------------------------------
  // Spreadsheet Agent & Grid Mutation (Phase 8)
  // --------------------------------------------------------------------------

  async executeAgentAction(request: import('./types').AgentActionRequest): Promise<import('./types').AgentExecutionResult> {
    const res = await fetch(`${API_BASE}/agent/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<import('./types').AgentExecutionResult>(res);
  },

  async undoAgentAction(datasetId: string, activeSheetName?: string): Promise<import('./types').AgentExecutionResult> {
    const res = await fetch(`${API_BASE}/agent/undo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dataset_id: datasetId, active_sheet_name: activeSheetName }),
    });
    return handleResponse<import('./types').AgentExecutionResult>(res);
  },

  async getAgentHistory(datasetId: string): Promise<import('./types').AgentHistoryResponse> {
    const res = await fetch(`${API_BASE}/agent/history/${encodeURIComponent(datasetId)}`);
    return handleResponse<import('./types').AgentHistoryResponse>(res);
  },

  // --------------------------------------------------------------------------
  // Smart Analytics & Visualization (Phase 9)
  // --------------------------------------------------------------------------

  async executeGranularAnalytics(
    datasetId: string,
    query: string,
    activeSheetName?: string
  ): Promise<import('./types').ExplainableAnalyticsResultDTO> {
    const res = await fetch(`${API_BASE}/datasets/${encodeURIComponent(datasetId)}/granular-analytics`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, active_sheet_name: activeSheetName }),
    });
    return handleResponse<import('./types').ExplainableAnalyticsResultDTO>(res);
  },
};


