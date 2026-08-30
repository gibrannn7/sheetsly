'use client';

import React, { createContext, useContext, useState } from 'react';
import {
  AggregationSpec,
  AnalyticalResult,
  CellData,
  ChartType,
  FilterCondition,
  NaturalLanguageQueryResponse,
  OperationType,
  SmartChartItem,
  SortSpec,
  VisualizationResponse,
  WorkbookOverview,
} from '../types';

export type WorkspaceTab = 'ai' | 'builder' | 'tables' | 'data' | 'visualize' | 'quality';

export interface AIQueryState {
  query: string;
  lastResponse: NaturalLanguageQueryResponse | null;
  selectedModel: string;
  suggestedQueries: string[];
  history: Array<{ query: string; response: NaturalLanguageQueryResponse; timestamp: number }>;
}

export interface AnalysisBuilderState {
  selectedTableId: string;
  operation: OperationType;
  targetColumn: string;
  filters: FilterCondition[];
  filterCombination: 'AND' | 'OR';
  groupByColumns: string[];
  aggregations: AggregationSpec[];
  sort: SortSpec | null;
  limit: number | null;
  result: AnalyticalResult | null;
}

export interface VisualizationState {
  selectedTableId: string;
  activeTab: 'smart' | 'custom';
  selectedDimCol: string;
  selectedMetricCol: string;
  selectedChartType: ChartType;
  customVizResponse: VisualizationResponse | null;
  smartCharts: SmartChartItem[];
  smartEmptyReason: string | null;
}

export interface ActualDataState {
  page: number;
  pageSize: number;
  searchQuery: string;
  selectedCell: CellData | null;
}

export interface WorkspaceContextValue {
  overview: WorkbookOverview | null;
  activeSheetName: string;
  activeViewMode: WorkspaceTab;
  setOverview: (overview: WorkbookOverview | null) => void;
  setActiveSheetName: (name: string) => void;
  setActiveViewMode: (tab: WorkspaceTab) => void;
  resetWorkspace: () => void;

  // AI Workspace State
  aiState: AIQueryState;
  updateAIState: (partial: Partial<AIQueryState>) => void;
  addAIHistoryItem: (query: string, response: NaturalLanguageQueryResponse) => void;

  // Analysis Builder State
  builderState: AnalysisBuilderState;
  updateBuilderState: (partial: Partial<AnalysisBuilderState>) => void;

  // Visualization State
  visualizationState: VisualizationState;
  updateVisualizationState: (partial: Partial<VisualizationState>) => void;

  // Actual Data State
  actualDataState: ActualDataState;
  updateActualDataState: (partial: Partial<ActualDataState>) => void;
}

const defaultAIState: AIQueryState = {
  query: '',
  lastResponse: null,
  selectedModel: 'gemini-3.1-flash-lite',
  suggestedQueries: [],
  history: [],
};

const defaultBuilderState: AnalysisBuilderState = {
  selectedTableId: '',
  operation: 'SUM',
  targetColumn: '',
  filters: [],
  filterCombination: 'AND',
  groupByColumns: [],
  aggregations: [],
  sort: null,
  limit: null,
  result: null,
};

const defaultVisualizationState: VisualizationState = {
  selectedTableId: '',
  activeTab: 'custom',
  selectedDimCol: '',
  selectedMetricCol: '',
  selectedChartType: 'BAR',
  customVizResponse: null,
  smartCharts: [],
  smartEmptyReason: null,
};

const defaultActualDataState: ActualDataState = {
  page: 1,
  pageSize: 50,
  searchQuery: '',
  selectedCell: null,
};

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

const WORKSPACE_STORAGE_KEY = 'sheetsly_workspace_active_id';

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [overview, setOverviewState] = useState<WorkbookOverview | null>(null);
  const [activeSheetName, setActiveSheetName] = useState<string>('');
  const [activeViewMode, setActiveViewMode] = useState<WorkspaceTab>('ai');

  const [aiState, setAiState] = useState<AIQueryState>(() => {
    try {
      if (typeof window !== 'undefined') {
        const savedModel = localStorage.getItem('sheetsly_selected_model');
        if (savedModel) {
          return { ...defaultAIState, selectedModel: savedModel };
        }
      }
    } catch {}
    return defaultAIState;
  });

  const [builderState, setBuilderState] = useState<AnalysisBuilderState>(defaultBuilderState);
  const [visualizationState, setVisualizationState] = useState<VisualizationState>(defaultVisualizationState);
  const [actualDataState, setActualDataState] = useState<ActualDataState>(defaultActualDataState);

  const setOverview = (newOverview: WorkbookOverview | null) => {
    setOverviewState(newOverview);
    if (newOverview) {
      try {
        localStorage.setItem(WORKSPACE_STORAGE_KEY, newOverview.dataset_id);
      } catch {}
      if (newOverview.sheets.length > 0 && !activeSheetName) {
        setActiveSheetName(newOverview.sheets[0].name);
      }
    } else {
      try {
        localStorage.removeItem(WORKSPACE_STORAGE_KEY);
      } catch {}
      setActiveSheetName('');
      setAiState(defaultAIState);
      setBuilderState(defaultBuilderState);
      setVisualizationState(defaultVisualizationState);
      setActualDataState(defaultActualDataState);
    }
  };

  const resetWorkspace = () => {
    setOverview(null);
  };

  const updateAIState = (partial: Partial<AIQueryState>) => {
    setAiState((prev) => {
      const next = { ...prev, ...partial };
      if (partial.selectedModel) {
        try {
          localStorage.setItem('sheetsly_selected_model', partial.selectedModel);
        } catch {}
      }
      return next;
    });
  };

  const addAIHistoryItem = (query: string, response: NaturalLanguageQueryResponse) => {
    setAiState((prev) => ({
      ...prev,
      lastResponse: response,
      history: [{ query, response, timestamp: Date.now() }, ...prev.history.slice(0, 19)],
    }));
  };

  const updateBuilderState = (partial: Partial<AnalysisBuilderState>) => {
    setBuilderState((prev) => ({ ...prev, ...partial }));
  };

  const updateVisualizationState = (partial: Partial<VisualizationState>) => {
    setVisualizationState((prev) => ({ ...prev, ...partial }));
  };

  const updateActualDataState = (partial: Partial<ActualDataState>) => {
    setActualDataState((prev) => ({ ...prev, ...partial }));
  };

  return (
    <WorkspaceContext.Provider
      value={{
        overview,
        activeSheetName,
        activeViewMode,
        setOverview,
        setActiveSheetName,
        setActiveViewMode,
        resetWorkspace,
        aiState,
        updateAIState,
        addAIHistoryItem,
        builderState,
        updateBuilderState,
        visualizationState,
        updateVisualizationState,
        actualDataState,
        updateActualDataState,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = (): WorkspaceContextValue => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
};
