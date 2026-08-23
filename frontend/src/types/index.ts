// TypeScript types for DiskMind frontend

export interface StorageSummary {
  health_score: number;
  utilization_pct: number;
  used_bytes: number;
  free_bytes: number;
  total_bytes: number;
  used_gb: number;
  free_gb: number;
  total_gb: number;
  duplicate_wasted_bytes: number;
  duplicate_wasted_gb: number;
  inactive_bytes: number;
  cache_bytes: number;
  anomaly_count: number;
  pending_recommendations: number;
  total_recoverable_bytes: number;
  total_recoverable_gb: number;
  days_until_90pct: number;
}

export interface StorageSnapshot {
  id: number;
  recorded_at: number;
  mount_point: string;
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  file_count: number;
  daily_growth_bytes: number;
  utilization_pct: number;
}

export interface Forecast {
  model_type: string;
  training_samples: number;
  avg_daily_growth_bytes: number;
  current_used_bytes: number;
  total_bytes: number;
  predictions: {
    [key: string]: {
      used_bytes: number;
      free_bytes: number;
      utilization_pct: number;
    };
  };
  thresholds: {
    days_until_90pct: number;
    days_until_95pct: number;
    days_until_100pct: number;
  };
  daily_series: Array<{
    day: number;
    used_bytes: number;
    utilization_pct: number;
  }>;
}

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'PROTECTED' | 'UNKNOWN';
export type RecAction = 'CLEANUP' | 'ARCHIVE' | 'KEEP' | 'REVIEW';
export type RecStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'EXECUTED' | 'UNDONE';

export interface Recommendation {
  id: number;
  created_at: number;
  action: RecAction;
  target_path: string;
  target_type: string;
  size_bytes: number;
  confidence: number;
  risk_level: RiskLevel;
  risk_score: number;
  reason: string;
  explanation: string;
  status: RecStatus;
  duplicate_group: string | null;
  category: string | null;
}

export interface DuplicateFile {
  path: string;
  size_bytes: number;
  accessed_at: number;
  modified_at: number;
  risk_level: RiskLevel;
  application: string | null;
}

export interface DuplicateGroup {
  content_hash: string;
  file_count: number;
  total_wasted_bytes: number;
  size_bytes: number;
  file_type: string;
  confidence: number;
  detection_type: string;
  files: DuplicateFile[];
}

export interface Anomaly {
  id: number;
  detected_at: number;
  anomaly_score: number;
  growth_gb: number;
  description: string;
  top_directories: string;
  is_resolved: number;
}

export interface SimulationResult {
  selected_recommendations: number;
  total_recoverable_bytes: number;
  total_recoverable_gb: number;
  before: {
    used_bytes: number;
    free_bytes: number;
    utilization_pct: number;
    used_gb: number;
    free_gb: number;
    days_until_90pct: number;
    days_until_95pct: number;
    days_until_100pct: number;
  };
  after: {
    used_bytes: number;
    free_bytes: number;
    utilization_pct: number;
    used_gb: number;
    free_gb: number;
    days_until_90pct: number;
    days_until_95pct: number;
    days_until_100pct: number;
  };
  impact: {
    days_gained_until_90pct: number;
    utilization_reduction_pct: number;
  };
  recommendations: Array<{
    id: number;
    category: string;
    reason: string;
    size_gb: number;
    risk_level: RiskLevel;
  }>;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  tool_calls?: Array<{ tool: string; result: unknown }>;
}

export interface FileTypeBreakdown {
  file_type: string;
  file_count: number;
  total_bytes: number;
  total_gb: number;
}

export interface DirectoryInfo {
  top_dir: string;
  total_size: number;
  file_count: number;
}
