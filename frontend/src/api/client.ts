const BASE_URL = '/api/v1';

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });
  const json = await res.json();
  if (!json.success && json.detail) {
    throw new Error(json.detail);
  }
  return json.data;
}

export const api = {
  getHealth: () => fetchJSON<any>('/health'),
  getTelemetry: () => fetchJSON<any>('/monitoring/telemetry'),
  getModels: () => fetchJSON<any>('/models'),
  syncModels: () => fetchJSON<any>('/models/sync', { method: 'POST' }),
  getDatasets: () => fetchJSON<any>('/datasets'),
  createDataset: (data: any) => fetchJSON<any>('/datasets', { method: 'POST', body: JSON.stringify(data) }),
  getEvaluations: () => fetchJSON<any>('/evaluations'),
  submitEvaluation: (data: any) => fetchJSON<any>('/evaluations', { method: 'POST', body: JSON.stringify(data) }),
  getEvaluationResults: (runId: string) => fetchJSON<any>(`/evaluations/${runId}/results`),
  getBenchmarks: () => fetchJSON<any>('/benchmarks'),
  createBenchmark: (data: any) => fetchJSON<any>('/benchmarks', { method: 'POST', body: JSON.stringify(data) }),
  getSecurityVectors: () => fetchJSON<any>('/security/vectors'),
  scanSecurity: (data: any) => fetchJSON<any>('/security/scan', { method: 'POST', body: JSON.stringify(data) }),
  evaluateRAG: (data: any) => fetchJSON<any>('/rag/evaluate', { method: 'POST', body: JSON.stringify(data) }),
  getRankings: () => fetchJSON<any>('/analytics/rankings'),
  recommendModel: (data: any) => fetchJSON<any>('/analytics/recommend', { method: 'POST', body: JSON.stringify(data) }),
};
