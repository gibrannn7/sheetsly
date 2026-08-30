/**
 * TypeScript data models for Sheetsly Workbook Inspection, Analytics, & Visualization
 */

export type DataType =
  | 'string'
  | 'integer'
  | 'float'
  | 'currency'
  | 'percentage'
  | 'date'
  | 'datetime'
  | 'boolean'
  | 'formula'
  | 'null'
  | 'unknown';

export type OrientationType = 'VERTICAL' | 'HORIZONTAL' | 'AMBIGUOUS' | 'IRREGULAR';

export type SemanticType =
  | 'categorical'
  | 'numeric_measure'
  | 'temporal'
  | 'identifier'
  | 'text'
  | 'boolean'
  | 'unknown';

export type IssueSeverity = 'INFO' | 'WARNING' | 'CRITICAL';

export interface CellCoordinate {
  row: number;
  column: number;
  cell_ref: string;
}

export interface CellData {
  coordinate: CellCoordinate;
  original_value: any;
  parsed_value: any;
  data_type: DataType;
  formula?: string | null;
  is_empty: boolean;
}

export interface ColumnMetadata {
  index: number;
  name: string;
  original_header_cell?: string | null;
  source_column_letter: string;
  data_type: DataType;
  semantic_type: SemanticType;
  type_confidence: number;
  total_count: number;
  null_count: number;
  unique_count: number;
  sample_values: any[];
}

export interface TableRegion {
  table_id: string;
  name: string;
  sheet_name: string;
  range_address: string;
  header_range?: string | null;
  data_range?: string | null;
  header_row_indices: number[];
  orientation: OrientationType;
  orientation_confidence: number;
  orientation_reasons: string[];
  row_count: number;
  column_count: number;
  columns: ColumnMetadata[];
  confidence_score: number;
}

export interface DataQualityIssue {
  issue_type: string;
  severity: IssueSeverity;
  message: string;
  sheet_name: string;
  table_id?: string | null;
  column_name?: string | null;
  affected_cells_count: number;
  sample_locations: string[];
}

export interface DataQualityReport {
  overall_score: number;
  total_issues: number;
  issues: DataQualityIssue[];
  summary: string;
}

export interface SheetMetadata {
  name: string;
  index: number;
  is_hidden: boolean;
  dimensions: string;
  total_rows: number;
  total_columns: number;
  used_range: string;
  empty_rows_count: number;
  empty_cols_count: number;
  merged_cells_regions: string[];
  formula_cells_count: number;
  tables: TableRegion[];
  quality_report: DataQualityReport;
}

export interface WorkbookOverview {
  dataset_id: string;
  filename: string;
  file_size_bytes: number;
  sheet_count: number;
  sheets: SheetMetadata[];
  overall_quality_score: number;
  created_at: string;
}

export interface SheetDataGridResponse {
  dataset_id: string;
  sheet_name: string;
  page: number;
  page_size: number;
  total_rows: number;
  total_columns: number;
  column_headers: string[];
  rows: CellData[][];
  merged_cells: string[];
  charts?: Record<string, ChartActionSpecDTO>;
  kpis?: Record<string, KPIActionSpecDTO>;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// ----------------------------------------------------------------------------
// Analytical Models (Phase 5)
// ----------------------------------------------------------------------------

export type OperationType =
  | 'SUM'
  | 'COUNT_ROWS'
  | 'COUNT_VALUES'
  | 'DISTINCT_COUNT'
  | 'AVERAGE'
  | 'MIN'
  | 'MAX'
  | 'MEDIAN'
  | 'FILTER'
  | 'SORT'
  | 'GROUP_BY'
  | 'SUMIF'
  | 'SUMIFS'
  | 'COUNTIF'
  | 'COUNTIFS';

export type FilterOperator =
  | 'equals'
  | 'not_equals'
  | 'contains'
  | 'not_contains'
  | 'starts_with'
  | 'ends_with'
  | 'greater_than'
  | 'less_than'
  | 'greater_or_equal'
  | 'less_or_equal'
  | 'between'
  | 'is_empty'
  | 'is_not_empty'
  | 'in_list';

export interface FilterCondition {
  column: string;
  operator: FilterOperator;
  value?: any;
  case_sensitive?: boolean;
}

export interface AggregationSpec {
  column: string;
  operation: 'SUM' | 'COUNT_ROWS' | 'COUNT_VALUES' | 'DISTINCT_COUNT' | 'AVERAGE' | 'MIN' | 'MAX' | 'MEDIAN';
  alias?: string | null;
}

export interface SortSpec {
  column: string;
  ascending: boolean;
}

export interface AnalyticalInstruction {
  operation: OperationType;
  dataset_id: string;
  sheet_name: string;
  table_id?: string | null;
  target_column?: string | null;
  group_by_columns?: string[];
  aggregations?: AggregationSpec[];
  filters?: FilterCondition[];
  filter_combination?: 'AND' | 'OR';
  sort?: SortSpec | null;
  limit?: number | null;
  parameters?: Record<string, any>;
}

export interface CalculationLineage {
  dataset_id: string;
  sheet_name: string;
  table_id: string;
  source_range: string;
  source_columns: string[];
  total_table_rows: number;
  rows_included: number;
  rows_excluded: number;
  filters_applied: string[];
  grouping_applied: string[];
  operations_performed: string[];
  calculation_steps: string[];
  execution_time_ms: number;
}

export interface AnalyticalResult {
  result_type: 'SCALAR' | 'TABLE' | 'SERIES' | 'METADATA';
  operation: string;
  scalar_value?: any;
  scalar_formatted?: string | null;
  series_data?: Array<{ label: string; value: any }> | null;
  table_data?: {
    columns: string[];
    rows: Record<string, any>[];
    total_rows: number;
  } | null;
  lineage: CalculationLineage;
}

// ----------------------------------------------------------------------------
// Visualization Models (Phase 6)
// ----------------------------------------------------------------------------

export type ChartType = 'BAR' | 'COLUMN' | 'LINE' | 'PIE' | 'AREA' | 'SCATTER' | 'HISTOGRAM';

export interface ChartSeriesSpec {
  name: string;
  values: (number | null)[];
  color?: string | null;
}

export interface ChartMetadata {
  chart_id: string;
  chart_type: ChartType;
  title: string;
  x_axis_label?: string | null;
  y_axis_label?: string | null;
  x_categories: string[];
  series: ChartSeriesSpec[];
  dataset_id: string;
  sheet_name: string;
  table_id: string;
  source_range: string;
  rows_included: number;
  rows_excluded: number;
  generated_at: string;
  warnings: string[];
}

export interface ChartRecommendation {
  preferred_type?: ChartType | null;
  compatible_types: ChartType[];
  reason: string;
  confidence: number;
}

export interface VisualizationResponse {
  chart_metadata: ChartMetadata;
  image_url: string;
  image_base64?: string | null;
}

export interface SmartChartItem {
  chart_id: string;
  title: string;
  chart_type: ChartType;
  dimension_column?: string | null;
  metric_column?: string | null;
  analytical_intent: string;
  why_this_chart: string;
  rank_score: number;
  instruction: AnalyticalInstruction;
  visualization: VisualizationResponse;
}

export interface SmartGenerateRequest {
  sheet_name?: string | null;
  table_id?: string | null;
  max_charts?: number;
}

export interface SmartGenerateResponse {
  dataset_id: string;
  sheet_name: string;
  table_id: string;
  total_candidates_evaluated: number;
  selected_charts_count: number;
  charts: SmartChartItem[];
  empty_reason?: string | null;
}

// ----------------------------------------------------------------------------
// AI Natural Language Query Models (Phase 8)
// ----------------------------------------------------------------------------

export type AIQueryStatus =
  | 'EXECUTION_READY'
  | 'CLARIFICATION_REQUIRED'
  | 'UNSUPPORTED_QUERY'
  | 'VALIDATION_FAILED'
  | 'PROVIDER_ERROR'
  | 'EXECUTION_ERROR';

export interface ClarificationRequest {
  question: string;
  reason: string;
  target_parameter: string;
  options: string[];
}

export interface EvidenceExplanation {
  summary: string;
  factual_statement: string;
  source_evidence: string;
  calculation_steps: string[];
  warnings: string[];
}

export interface TimingBreakdown {
  schema_resolution_ms: number;
  qwen_planning_ms: number;
  guardrail_validation_ms: number;
  deterministic_execution_ms: number;
  visualization_ms: number;
  evidence_explanation_ms: number;
  total_duration_ms: number;
}

export interface AIModelOption {
  id: string;
  label: string;
  provider?: string;
  provider_label?: string;
  badge?: string;
  is_default?: boolean;
}

export interface NaturalLanguageQueryRequest {
  query: string;
  dataset_id: string;
  sheet_name?: string | null;
  table_id?: string | null;
  model?: string | null;
  generate_visualization?: boolean;
  clarification_selection?: Record<string, string> | null;
  preplanned_instruction?: AnalyticalInstruction | null;
}

export interface QueryPlanOnlyResponse {
  status: AIQueryStatus;
  user_query: string;
  intent_summary: string;
  model_used?: string | null;
  planned_instruction?: AnalyticalInstruction | null;
  clarification?: ClarificationRequest | null;
  sub_plans?: QueryPlanOnlyResponse[] | null;
  error_message?: string | null;
  timing?: TimingBreakdown | null;
}

export interface NaturalLanguageQueryResponse {
  status: AIQueryStatus;
  user_query: string;
  intent_summary: string;
  model_used?: string | null;
  planned_instruction?: AnalyticalInstruction | null;
  clarification?: ClarificationRequest | null;
  analytical_result?: AnalyticalResult | null;
  visualization?: VisualizationResponse | null;
  explanation?: EvidenceExplanation | null;
  sub_analyses?: NaturalLanguageQueryResponse[] | null;
  suggested_next_queries?: string[];
  error_message?: string | null;
  timing?: TimingBreakdown | null;
}

export interface SuggestedQueriesResponse {
  dataset_id: string;
  sheet_name: string;
  suggested_queries: string[];
}

export interface AIStatusResponse {
  configured: boolean;
  model: string;
  default_model?: string;
  available_models?: AIModelOption[];
  enable_thinking: boolean;
  provider: string;
}

// ----------------------------------------------------------------------------
// Spreadsheet Agent & Mutation UI Models (Phase 8)
// ----------------------------------------------------------------------------

export type AgentResponseStatus =
  | 'SUCCESS'
  | 'CLARIFICATION'
  | 'UNSUPPORTED'
  | 'VALIDATION_ERROR'
  | 'EXECUTION_ERROR'
  | 'VERIFICATION_ERROR'
  | 'PERSISTENCE_ERROR'
  | 'ROLLBACK_SUCCESS'
  | 'ROLLBACK_FAILURE';

export interface ChartActionSpecDTO {
  chart_id: string;
  sheet_name?: string | null;
  chart_type: string;
  title: string;
  dimension_column?: string | null;
  category_column?: string | null;
  measure_column?: string | null;
  aggregation?: string;
  destination_cell: string;
  anchor_cell?: string | null;
  width_cols?: number;
  height_rows?: number;
  image_url?: string | null;
  image_base64?: string | null;
  summary_data?: Array<{ category: string; value: number }>;
  source_range?: string | null;
  calculation_reference?: string | null;
  provenance_note?: string | null;
}

export interface KPIActionSpecDTO {
  kpi_id: string;
  title: string;
  measure_column: string;
  aggregation: string;
  calculated_value: any;
  formatted_value: string;
  destination_cell: string;
  source_range?: string | null;
}

export interface SpreadsheetActionDTO {
  action_id: string;
  action_type: string;
  sheet_name: string;
  target_cell?: string | null;
  target_range?: string | null;
  value?: any;
  formula?: string | null;
  description?: string | null;
  chart_spec?: ChartActionSpecDTO | null;
  kpi_spec?: KPIActionSpecDTO | null;
}

export interface CellSnapshotDTO {
  coordinate: string;
  row: number;
  col: number;
  original_value?: any;
  parsed_value?: any;
  data_type?: string;
  formula?: string | null;
  is_empty: boolean;
}

export interface StateDiffDTO {
  target_ref: string;
  before: CellSnapshotDTO;
  after: CellSnapshotDTO;
}

export interface VerificationReportDTO {
  is_verified: boolean;
  total_cells_checked: number;
  planned_modifications_count: number;
  actual_modifications_count: number;
  diff_matches_plan: boolean;
  failures: string[];
  failure_reasons: string[];
  verified_expected_value?: any;
  actual_evaluated_value?: any;
}

export interface MutationTransactionDTO {
  transaction_id: string;
  dataset_id: string;
  sheet_name: string;
  user_request: string;
  resolved_intent: string;
  status: string;
  actions: SpreadsheetActionDTO[];
  diff: StateDiffDTO[];
  verification_report?: VerificationReportDTO | null;
}

export interface AgentClarificationDTO {
  question: string;
  reason: string;
  target_parameter: string;
  options: string[];
}

export interface AgentExecutionResult {
  status: AgentResponseStatus;
  transaction?: MutationTransactionDTO | null;
  message: string;
  affected_ranges: string[];
  clarification?: AgentClarificationDTO | null;
  error_detail?: string | null;
  execution_time_ms: number;
}

export interface AgentActionRequest {
  dataset_id: string;
  user_request: string;
  active_sheet_name?: string;
  selected_range?: string;
  confirmation_context?: Record<string, any>;
  expected_version?: number;
  model_id?: string;
}

export interface AgentUndoRequest {
  dataset_id: string;
  active_sheet_name?: string;
}

export interface TransactionAuditRecordDTO {
  transaction_id: string;
  dataset_id: string;
  sheet_name: string;
  action_types: string[];
  affected_cells: string[];
  status: string;
  verified: boolean;
  rolled_back: boolean;
  timestamp: string;
}

export interface AgentHistoryResponse {
  dataset_id: string;
  current_version: number;
  can_undo: boolean;
  can_redo?: boolean;
  history: TransactionAuditRecordDTO[];
}

// ----------------------------------------------------------------------------
// Smart Visualization & Granular Analytics Models (Phase 9)
// ----------------------------------------------------------------------------

export type CanonicalChartType =
  | 'LINE'
  | 'BAR'
  | 'COLUMN'
  | 'AREA'
  | 'SCATTER'
  | 'PIE'
  | 'DONUT'
  | 'TABLE'
  | 'KPI';

export interface ChartProvenanceDTO {
  dataset_id: string;
  source_sheets: string[];
  source_columns: string[];
  source_ranges: string[];
  filters_applied: string[];
  aggregation: string;
  dimension?: string | null;
  measure: string;
  verification_status: string;
}

export interface ChartDatasetDTO {
  name: string;
  values: any[];
  color?: string | null;
}

export interface ChartDataDTO {
  chart_type: CanonicalChartType;
  title: string;
  labels: string[];
  datasets: ChartDatasetDTO[];
  provenance: ChartProvenanceDTO;
  summary_metric?: string | null;
  summary_value?: any;
}

export interface ExplainableAnalyticsResultDTO {
  question: string;
  resolved_intent: string;
  source_sheets: string[];
  source_columns: string[];
  source_ranges: string[];
  filters_applied: string[];
  aggregation: string;
  grouping?: string | null;
  result_rows: Record<string, any>[];
  calculation_method: string;
  verification_status: string;
  chart_data?: ChartDataDTO | null;
  timing_ms: number;
}


