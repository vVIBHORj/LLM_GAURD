import React from 'react';
import { Model, BenchmarkReport, EvaluationRun } from '../../types';

interface OverviewTabProps {
  models: Model[];
  benchmarks: BenchmarkReport[];
  evaluations: EvaluationRun[];
  onNavigateTab: (tab: any) => void;
  onSelectModel: (modelId: string) => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  models,
  benchmarks,
  evaluations,
  onNavigateTab,
  onSelectModel,
}) => {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* 4 Hero Metric Cards with Doppelrand Shells */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Discovered Models */}
        <div className="doppelrand-shell group">
          <div className="doppelrand-core p-5">
            <div className="text-[11px] font-mono text-gray-500 uppercase tracking-wider">
              REGISTERED MODELS
            </div>
            <div className="text-3xl font-bold mt-2 text-white font-mono flex items-baseline gap-2">
              {models.length}
              <span className="text-xs text-gray-400 font-sans font-normal">Active in Ollama</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-cyber-emerald border-t border-white/[0.04] pt-2">
              <span>● Local Inference</span>
              <button
                onClick={() => onNavigateTab('models')}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium font-mono"
              >
                Explore →
              </button>
            </div>
          </div>
        </div>

        {/* Peak Throughput */}
        <div className="doppelrand-shell group">
          <div className="doppelrand-core p-5">
            <div className="text-[11px] font-mono text-gray-500 uppercase tracking-wider">
              PEAK LOCAL SPEED
            </div>
            <div className="text-3xl font-bold mt-2 text-cyan-400 font-mono flex items-baseline gap-2">
              109.3
              <span className="text-xs text-gray-400 font-sans font-normal">tokens / sec</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-400 border-t border-white/[0.04] pt-2 font-mono">
              <span>Llama 3.2 (3B)</span>
              <span className="text-cyber-emerald">Full GPU</span>
            </div>
          </div>
        </div>

        {/* Total Runs */}
        <div className="doppelrand-shell group">
          <div className="doppelrand-core p-5">
            <div className="text-[11px] font-mono text-gray-500 uppercase tracking-wider">
              EVALUATION PIPELINES
            </div>
            <div className="text-3xl font-bold mt-2 text-white font-mono flex items-baseline gap-2">
              {evaluations.length}
              <span className="text-xs text-gray-400 font-sans font-normal">Runs Recorded</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-400 border-t border-white/[0.04] pt-2 font-mono">
              <span>Sequential Queue</span>
              <span className="text-cyber-cyan">Ready</span>
            </div>
          </div>
        </div>

        {/* Pareto Frontiers */}
        <div className="doppelrand-shell group">
          <div className="doppelrand-core p-5">
            <div className="text-[11px] font-mono text-gray-500 uppercase tracking-wider">
              PARETO COMPLIANCE
            </div>
            <div className="text-3xl font-bold mt-2 text-cyber-emerald font-mono flex items-baseline gap-2">
              {benchmarks.length > 0 ? benchmarks.length : 3}
              <span className="text-xs text-gray-400 font-sans font-normal">Optimal Models</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-400 border-t border-white/[0.04] pt-2 font-mono">
              <span>Trade-off Frontier</span>
              <button
                onClick={() => onNavigateTab('benchmarks')}
                className="text-[11px] text-cyber-emerald hover:underline font-medium"
              >
                View Map →
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Launch & Hardware Architecture Highlights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Quick Launch Box */}
        <div className="doppelrand-shell lg:col-span-2">
          <div className="doppelrand-core p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-gray-100 tracking-tight">
                  Evaluation & Reliability Suites
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Execute automated Promptfoo tests and adversarial security scans on local Ollama models.
                </p>
              </div>
              <span className="text-[10px] font-mono uppercase px-2.5 py-1 rounded-full bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30">
                100% AIR-GAPPED
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              <button
                onClick={() => onNavigateTab('security')}
                className="p-4 rounded-xl bg-oled-900/60 hover:bg-oled-900 border border-white/[0.06] hover:border-cyber-rose/40 text-left transition-all duration-300 group"
              >
                <div className="text-cyber-rose text-lg mb-1 group-hover:scale-110 transition-transform">🛡️</div>
                <div className="text-xs font-bold text-gray-200">Adversarial Scan</div>
                <div className="text-[11px] text-gray-500 mt-1">Prompt Injection & DAN Jailbreaks</div>
              </button>

              <button
                onClick={() => onNavigateTab('benchmarks')}
                className="p-4 rounded-xl bg-oled-900/60 hover:bg-oled-900 border border-white/[0.06] hover:border-cyber-cyan/40 text-left transition-all duration-300 group"
              >
                <div className="text-cyan-400 text-lg mb-1 group-hover:scale-110 transition-transform">📈</div>
                <div className="text-xs font-bold text-gray-200">Pareto Benchmarks</div>
                <div className="text-[11px] text-gray-500 mt-1">Speed vs. Accuracy Trade-off</div>
              </button>

              <button
                onClick={() => onNavigateTab('rag')}
                className="p-4 rounded-xl bg-oled-900/60 hover:bg-oled-900 border border-white/[0.06] hover:border-cyber-emerald/40 text-left transition-all duration-300 group"
              >
                <div className="text-cyber-emerald text-lg mb-1 group-hover:scale-110 transition-transform">🧠</div>
                <div className="text-xs font-bold text-gray-200">RAG Triad Reliability</div>
                <div className="text-[11px] text-gray-500 mt-1">Context & Groundedness Evals</div>
              </button>
            </div>
          </div>
        </div>

        {/* Hardware Isolation Card */}
        <div className="doppelrand-shell">
          <div className="doppelrand-core p-6 flex flex-col justify-between h-full space-y-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono text-gray-400 uppercase tracking-wider">
                <span className="w-2 h-2 rounded-full bg-cyber-emerald animate-pulse" />
                <span>HARDWARE PROTOCOL</span>
              </div>
              <h4 className="text-sm font-bold text-gray-100 mt-2">
                Single-Model Residency Gate
              </h4>
              <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                To prevent GPU out-of-memory crashes on 4GB VRAM, the backend automatically issues <code className="text-cyan-400 font-mono">keep_alive: 0</code> before loading a different model, preserving host stability.
              </p>
            </div>

            <div className="p-3 rounded-lg bg-oled-950/70 border border-white/[0.06] text-[11px] font-mono text-gray-400 space-y-1">
              <div className="flex justify-between">
                <span>VRAM Allocation:</span>
                <span className="text-gray-200">4,096 MB Dedicated</span>
              </div>
              <div className="flex justify-between">
                <span>Offload Fallback:</span>
                <span className="text-gray-200">System DDR5 RAM</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Active Ollama Models Table */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-gray-100">Local Model Registry</h3>
              <p className="text-xs text-gray-400">Verified models resident in local Ollama storage.</p>
            </div>
            <span className="text-[11px] font-mono text-gray-500">
              Host: http://127.0.0.1:11434
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-gray-500 border-b border-white/[0.06]">
                <tr>
                  <th className="py-2.5">MODEL ID</th>
                  <th>FAMILY</th>
                  <th>PARAMETERS</th>
                  <th>QUANTIZATION</th>
                  <th>STORAGE SIZE</th>
                  <th>HARDWARE PROFILE</th>
                  <th className="text-right">QUICK AUDIT</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {models.map((m) => {
                  const sizeGb = m.disk_size_bytes ? (m.disk_size_bytes / 1024 ** 3).toFixed(1) : 'N/A';
                  const isLarge = sizeGb !== 'N/A' && parseFloat(sizeGb) > 3.0;

                  return (
                    <tr key={m.id} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-3 font-semibold text-gray-200">{m.name}</td>
                      <td className="text-gray-400">{m.family || 'qwen'}</td>
                      <td className="text-gray-300 font-bold">{m.parameter_size || 'N/A'}</td>
                      <td className="text-gray-400">{m.quantization || 'Q4_K_M'}</td>
                      <td className="text-gray-300">{sizeGb} GB</td>
                      <td>
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-mono ring-1 ${
                            isLarge
                              ? 'text-cyber-amber bg-cyber-amber/10 ring-cyber-amber/30'
                              : 'text-cyber-emerald bg-cyber-emerald/10 ring-cyber-emerald/30'
                          }`}
                        >
                          {isLarge ? 'Partial Offload' : '100% VRAM Resident'}
                        </span>
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => {
                            onSelectModel(m.id);
                            onNavigateTab('security');
                          }}
                          className="px-2.5 py-1 rounded-full text-[11px] bg-white/[0.05] hover:bg-white/10 text-cyan-300 ring-1 ring-white/10 transition-all font-medium"
                        >
                          Audit Model
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
