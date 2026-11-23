export interface Telemetry {
  cpu: {
    usage_percent: number | null;
    cores_logical: number;
    cores_physical: number;
  };
  ram: {
    total_mb: number;
    available_mb: number;
    free_mb: number;
    used_percent: number;
  };
  gpu: {
    available: boolean;
    name: string | null;
    total_mb: number;
    allocated_mb: number;
    free_mb: number;
    reserved_mb?: number | null;
    vram_usage_percent: number;
    gpu_utilization_percent?: number | null;
    temperature_c?: number | null;
    power_w?: number | null;
    source?: string | null;
  };
  ollama?: {
    available: boolean;
    active_models: Array<{
      name: string;
      size_mb: number;
      size_vram_mb: number;
      digest?: string | null;
      details?: Record<string, any> | null;
      expires_at?: string | null;
    }>;
    total_vram_mb: number;
    total_size_mb: number;
    error?: string | null;
  } | null;
  hardware_safety_status: 'SAFE' | 'WARNING' | 'CRITICAL';
  can_run_evaluation: boolean;
  reason: string;
}

export interface Model {
  id: string;
  name: string;
  family?: string;
  parameter_size?: string;
  quantization?: string;
  context_window_default: number;
  disk_size_bytes?: number;
  is_available: boolean;
  last_seen_at: string;
}

export interface ParetoPoint {
  model_id: string;
  run_id?: string | null;
  tokens_per_sec: number;
  accuracy_rate: number;
  peak_vram_mb?: number | null;
  is_pareto_optimal: boolean;
}

export interface ModelBenchmarkScore {
  model_id: string;
  run_id?: string | null;
  status: 'BENCHMARKED' | 'UNBENCHMARKED' | 'INELIGIBLE' | string;
  accuracy_score?: number | null;
  speed_tokens_sec?: number | null;
  avg_latency_ms?: number | null;
  peak_vram_mb?: number | null;
  peak_ollama_vram_mb?: number | null;
  gpu_name?: string | null;
  gpu_source?: string | null;
  memory_efficiency_score?: number | null;
  rank?: number | null;
}

export interface BenchmarkReport {
  id: string;
  title: string;
  dataset_id?: string | null;
  model_ids: string[];
  generation_config?: Record<string, any> | null;
  generated_at: string;
  results: ModelBenchmarkScore[];
  pareto_frontier: ParetoPoint[];
}

export interface AttackDetail {
  category: string;
  attack_vector: string;
  prompt: string;
  model_response: string;
  defended: boolean;
  risk_level: string;
  reason: string;
  thinking_preview?: string | null;
}

export interface SecurityReport {
  id: string;
  model_id: string;
  engine_used?: 'promptfoo' | 'direct';
  total_attacks: number;
  defended_attacks: number;
  defense_rate: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  category_breakdown: Record<string, number>;
  attack_details: AttackDetail[];
  generated_at: string;
}

export interface RAGReport {
  id: string;
  generative_model_id: string;
  embedding_model_id: string;
  total_queries: number;
  avg_context_relevance: number;
  avg_faithfulness: number;
  avg_answer_relevance: number;
  rag_triad_score: number;
  query_evaluations: {
    query: string;
    retrieved_chunk: string;
    generated_answer: string;
    context_relevance: number;
    faithfulness: number;
    answer_relevance: number;
  }[];
  created_at: string;
}

export interface ModelRanking {
  rank: number;
  model_id: string;
  composite_score: number;
  accuracy_score: number;
  security_score: number;
  speed_score: number;
  memory_score: number;
  tokens_per_sec: number;
  vram_used_mb: number;
}

export interface RunProgress {
  total_tests: number;
  completed_tests: number;
  passed_tests: number;
  failed_tests: number;
}

export interface EvaluationRun {
  id: string;
  experiment_id?: string;
  model_id: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  total_duration_seconds?: number;
  tokens_per_second_avg?: number;
  peak_vram_mb?: number;
  peak_ram_mb?: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  progress?: RunProgress;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  task_type: string;
  version: number;
  test_case_count: number;
  created_at: string;
}
