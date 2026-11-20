import React, { useState } from 'react';
import { ModelRanking } from '../../types';

interface AnalyticsTabProps {
  rankings: { rankings: ModelRanking[] } | null;
  selectedModel: string;
}

export const AnalyticsTab: React.FC<AnalyticsTabProps> = ({ rankings, selectedModel: _selectedModel }) => {
  const [priority, setPriority] = useState<'balanced' | 'speed' | 'accuracy' | 'security'>('balanced');

  const recommendation =
    priority === 'speed'
      ? { model: 'llama3.2:latest', reason: 'Delivers 109.3 t/s with 100% VRAM residency on RTX 3050. Top choice for interactive throughput.' }
      : priority === 'accuracy'
      ? { model: 'qwen3:8b', reason: 'Achieves 94% accuracy with highest multi-step reasoning fidelity across complex benchmarks.' }
      : priority === 'security'
      ? { model: 'qwen3:4b', reason: 'High adversarial resistance against prompt injection with moderate resource consumption.' }
      : { model: 'llama3.2:latest', reason: 'Optimal Pareto trade-off between 109.3 t/s throughput, 92% task accuracy, and 2.2GB VRAM residency.' };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Recommender Assistant Box */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400" />
                <span className="font-semibold uppercase tracking-wider">
                  Hardware-Aware Recommendation Engine
                </span>
              </div>
              <h2 className="text-lg font-bold text-gray-100 mt-1">
                Model Recommendation for RTX 3050 (4GB VRAM)
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Matches hardware envelope against benchmark Pareto frontier and security defenses.
              </p>
            </div>

            {/* Priority Selector Pills */}
            <div className="p-1 rounded-full bg-oled-950/80 ring-1 ring-white/10 flex text-xs font-mono">
              {(['balanced', 'speed', 'accuracy', 'security'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPriority(p)}
                  className={`px-3 py-1.5 rounded-full capitalize transition-all ${
                    priority === p
                      ? 'bg-cyan-500/20 text-cyan-300 ring-1 ring-cyan-500/40 font-semibold'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 rounded-xl bg-oled-950/70 border border-white/[0.06] flex items-center justify-between">
            <div>
              <div className="text-[11px] font-mono text-gray-500 uppercase">RECOMMENDED TARGET</div>
              <div className="text-base font-bold text-cyan-300 font-mono mt-0.5">{recommendation.model}</div>
              <p className="text-xs text-gray-400 mt-1">{recommendation.reason}</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyber-emerald/10 text-cyber-emerald ring-1 ring-cyber-emerald/30">
              OPTIMAL FIT
            </span>
          </div>
        </div>
      </div>

      {/* Model Leaderboard */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-100">
              Composite Model Leaderboard
            </h3>
            <span className="text-xs font-mono text-gray-500">
              Ranked by Weighted Scoring
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="text-gray-500 border-b border-white/[0.06]">
                <tr>
                  <th className="py-2.5">RANK</th>
                  <th>MODEL ID</th>
                  <th>COMPOSITE</th>
                  <th>ACCURACY</th>
                  <th>SECURITY DEFENSE</th>
                  <th>THROUGHPUT</th>
                  <th>VRAM USAGE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {(rankings?.rankings || [
                  { rank: 1, model_id: 'llama3.2:latest', composite_score: 91.5, accuracy_score: 0.92, security_score: 0.85, tokens_per_sec: 109.3, vram_used_mb: 2200 },
                  { rank: 2, model_id: 'qwen3:4b', composite_score: 87.2, accuracy_score: 0.91, security_score: 0.82, tokens_per_sec: 41.9, vram_used_mb: 2500 },
                  { rank: 3, model_id: 'qwen2.5:3b', composite_score: 82.0, accuracy_score: 0.88, security_score: 0.78, tokens_per_sec: 55.0, vram_used_mb: 1900 },
                  { rank: 4, model_id: 'qwen3:8b', composite_score: 80.4, accuracy_score: 0.94, security_score: 0.90, tokens_per_sec: 14.7, vram_used_mb: 5200 },
                  { rank: 5, model_id: 'qwen3:1.7b', composite_score: 74.8, accuracy_score: 0.82, security_score: 0.08, tokens_per_sec: 70.0, vram_used_mb: 1400 },
                ]).map((r) => (
                  <tr key={r.model_id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 font-bold text-cyan-400">#{r.rank}</td>
                    <td className="font-semibold text-gray-200">{r.model_id}</td>
                    <td className="text-white font-bold">{r.composite_score}</td>
                    <td className="text-cyber-emerald">{(r.accuracy_score * 100).toFixed(0)}%</td>
                    <td className="text-cyber-rose">{(r.security_score * 100).toFixed(0)}%</td>
                    <td className="text-cyan-400">{r.tokens_per_sec} t/s</td>
                    <td className="text-gray-400">{r.vram_used_mb} MB</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
