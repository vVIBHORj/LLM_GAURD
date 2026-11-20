import React, { useState, useEffect } from 'react';
import { EvaluationRun, Dataset } from '../../types';

interface EvaluationsTabProps {
  evaluations: EvaluationRun[];
  datasets: Dataset[];
  selectedModel: string;
  onSubmitEval: (datasetId: string, modelId: string) => void;
  loading: boolean;
}

export const EvaluationsTab: React.FC<EvaluationsTabProps> = ({
  evaluations,
  datasets,
  selectedModel,
  onSubmitEval,
  loading,
}) => {
  // Start with empty string; populate once datasets load from API
  const [selectedDataset, setSelectedDataset] = useState<string>('');

  // Auto-select first dataset when datasets array populates
  useEffect(() => {
    if (datasets.length > 0 && !selectedDataset) {
      setSelectedDataset(datasets[0].id);
    }
  }, [datasets, selectedDataset]);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header and Queue Submission */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="font-semibold uppercase tracking-wider">
                  Sequential Queue Orchestrator
                </span>
              </div>
              <h2 className="text-lg font-bold text-gray-100 mt-1">
                Promptfoo Subprocess Evaluation Runner
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Executes YAML assertions via managed child subprocesses over IPv4 http://127.0.0.1:11434.
              </p>
            </div>

            <button
              onClick={() => onSubmitEval(selectedDataset, selectedModel)}
              disabled={loading || !selectedDataset}
              className="island-btn bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50 group font-bold shadow-glow-cyan"
            >
              <span>{loading ? 'Submitting to Queue...' : 'Enqueue Evaluation'}</span>
              <span className="btn-badge-icon bg-white/20">
                <svg className="w-3.5 h-3.5 text-white group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
              </span>
            </button>
          </div>

          {/* Dataset Selector Bar */}
          <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <span className="text-xs font-mono text-gray-400">Select Test Dataset:</span>
            <div className="flex flex-wrap gap-2">
              {datasets.map((d) => (
                <button
                  key={d.id}
                  onClick={() => setSelectedDataset(d.id)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all ${
                    selectedDataset === d.id
                      ? 'bg-white/10 text-cyan-300 ring-1 ring-cyan-500/40 font-semibold'
                      : 'bg-white/[0.03] text-gray-400 hover:text-gray-200 ring-1 ring-white/5'
                  }`}
                >
                  {d.name} ({d.test_case_count ?? 0} Tests)
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Pre-Seeded Test Suites Highlight */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="doppelrand-shell">
          <div className="doppelrand-core p-5 space-y-2">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-cyan-400 font-bold">PROMPTFOO RIGOROUS SECURITY</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 ring-1 ring-cyan-500/20">
                12 ASSERTIONS
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Automated `not-contains` assertions targeting instruction injection, DAN jailbreaks, PII exfiltration, and admin token theft.
            </p>
          </div>
        </div>

        <div className="doppelrand-shell">
          <div className="doppelrand-core p-5 space-y-2">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-emerald-400 font-bold">INSTRUCTION REASONING SUITE</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 ring-1 ring-emerald-500/20">
                REASONING BENCH
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              Multi-step logic deduction, structured JSON schema validation, and constraint-bound arithmetic verification.
            </p>
          </div>
        </div>
      </div>

      {/* Evaluation Runs History */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-100">
              Evaluation Run Ledger (Stored in SQLite & JSONL)
            </h3>
            <span className="text-xs font-mono text-gray-500">
              {evaluations.length} Runs Recorded
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-gray-500 border-b border-white/[0.06]">
                <tr>
                  <th className="py-2.5">RUN ID</th>
                  <th>MODEL</th>
                  <th>STATUS</th>
                  <th>PASSED / TOTAL</th>
                  <th>THROUGHPUT</th>
                  <th>VRAM PEAK</th>
                  <th>STARTED</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {evaluations.length > 0 ? (
                  evaluations.map((ev) => {
                    const passed = ev.progress?.passed_tests ?? 0;
                    const total = ev.progress?.total_tests ?? 0;
                    const accuracy = total > 0 ? Math.round((passed / total) * 100) : null;
                    return (
                      <tr key={ev.id} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3 text-cyan-400 font-semibold">{ev.id.slice(0, 8)}…</td>
                        <td className="text-gray-200">{ev.model_id}</td>
                        <td>
                          <span className={`px-2 py-0.5 rounded-full text-[10px] ring-1 ${
                            ev.status === 'COMPLETED'
                              ? 'text-cyber-emerald bg-cyber-emerald/10 ring-cyber-emerald/30'
                              : ev.status === 'RUNNING'
                              ? 'text-cyan-400 bg-cyan-500/10 ring-cyan-500/30 animate-pulse'
                              : ev.status === 'FAILED'
                              ? 'text-red-400 bg-red-500/10 ring-red-500/30'
                              : 'text-gray-400 bg-white/5 ring-white/10'
                          }`}>
                            ● {ev.status}
                          </span>
                        </td>
                        <td className="text-gray-300">
                          {total > 0 ? (
                            <span>
                              <span className="text-emerald-400 font-bold">{passed}</span>
                              {accuracy !== null && <span className="text-gray-500 ml-1">({accuracy}%)</span>}
                              <span className="text-gray-500"> / {total}</span>
                            </span>
                          ) : (
                            <span className="text-gray-600 italic">pending</span>
                          )}
                        </td>
                        <td className="text-cyan-400">
                          {ev.tokens_per_second_avg != null
                            ? `${ev.tokens_per_second_avg.toFixed(1)} t/s`
                            : <span className="text-gray-600">—</span>}
                        </td>
                        <td className="text-gray-400">
                          {ev.peak_vram_mb != null
                            ? `${ev.peak_vram_mb.toFixed(0)} MB`
                            : <span className="text-gray-600">—</span>}
                        </td>
                        <td className="text-gray-500">
                          {ev.started_at
                            ? new Date(ev.started_at).toLocaleTimeString()
                            : new Date(ev.created_at).toLocaleTimeString()}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-gray-500 italic">
                      No evaluation runs yet. Click "Enqueue Evaluation" to run the Promptfoo suite against {selectedModel}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
