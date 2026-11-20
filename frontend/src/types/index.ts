export interface Telemetry {
  cpu: {
    usage_percent: number;
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
    vram_usage_percent: number;
  };
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
  tokens_per_sec: number;
  accuracy_rate: number;
  peak_vram_mb: number;
  is_pareto_optimal: boolean;
}

export interface BenchmarkReport {
  id: string;
  title: string;
  model_ids: string[];
  generated_at: string;
  results: {
    model_id: string;
    accuracy_score: number;
    speed_tokens_sec: number;
    avg_latency_ms: number;
    peak_vram_mb: number;
    memory_efficiency_score: number;
    rank: number;
  }[];
  pareto_frontier: ParetoPoint[];
}

export interface SecurityReport {
  id: string;
  model_id: string;
  total_attacks: number;
  defended_attacks: number;
  defense_rate: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  category_breakdown: Record<string, number>;
  attack_details: {
    category: string;
    attack_vector: string;
    prompt: string;
    model_response: string;
    defended: boolean;
    risk_level: string;
    reason: string;
  }[];
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
