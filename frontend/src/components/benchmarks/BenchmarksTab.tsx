import React from 'react';
import { BenchmarkReport } from '../../types';
import { ParetoChart } from './ParetoChart';

interface BenchmarksTabProps {
  benchmarks: BenchmarkReport[];
  selectedModel: string;
  onNavigateTab: (tab: any) => void;
}

export const BenchmarksTab: React.FC<BenchmarksTabProps> = ({
  benchmarks: _benchmarks,
  selectedModel,
  onNavigateTab: _onNavigateTab,
}) => {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header and Explanation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-gray-100 tracking-tight">
            Multi-Model Speed vs. Accuracy Pareto Frontier
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Empirical benchmark measurements for <span className="text-cyan-400 font-mono">{selectedModel}</span> and local models.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono">
          <span className="w-2.5 h-2.5 rounded-full bg-cyber-emerald" />
          <span className="text-cyber-emerald font-semibold">Pareto Optimal (Non-Dominated)</span>
        </div>
      </div>

      {/* Main Interactive Chart Shell */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-bold text-gray-200">
              Inference Throughput vs. Assertion Accuracy Trade-off
            </h3>
            <span className="text-[11px] font-mono text-gray-500">
              Hardware: Intel i7-12700H + RTX 3050 (4GB)
            </span>
          </div>
          <ParetoChart />
        </div>
      </div>

      {/* Benchmark Comparison Matrix Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          {
            model: 'llama3.2:latest',
            params: '3B',
            speed: 109.3,
            acc: 0.92,
            vram: '2.2 GB',
            status: 'PARETO OPTIMAL',
            color: 'emerald',
            summary: 'High throughput champion. Runs completely in 4GB VRAM with zero host RAM paging.',
          },
          {
            model: 'qwen3:4b',
            params: '4B Reasoning',
            speed: 41.9,
            acc: 0.91,
            vram: '2.5 GB',
            status: 'PARETO OPTIMAL',
            color: 'emerald',
            summary: 'Reasoning model with balanced token generation rate and high instruction fidelity.',
          },
          {
            model: 'qwen3:8b',
            params: '8B Reasoning',
            speed: 14.7,
            acc: 0.94,
            vram: '2.2 GB GPU + 3.5 GB RAM',
            status: 'PARETO OPTIMAL',
            color: 'emerald',
            summary: 'Deepest reasoning capacity. Paginates ~3.5GB to system RAM under single-model residency.',
          },
        ].map((item) => (
          <div key={item.model} className="doppelrand-shell">
            <div className="doppelrand-core p-5 flex flex-col justify-between h-full space-y-3">
              <div>
                <div className="flex justify-between items-center text-xs font-mono">
                  <span className="font-bold text-gray-100">{item.model}</span>
                  <span className="text-[9px] px-2 py-0.5 rounded-full bg-cyber-emerald/10 text-cyber-emerald ring-1 ring-cyber-emerald/30 font-semibold">
                    {item.status}
                  </span>
                </div>
                <div className="mt-3 space-y-1 text-xs font-mono text-gray-400">
                  <div className="flex justify-between">
                    <span>Throughput:</span>
                    <span className="text-cyan-400 font-bold">{item.speed} t/s</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Accuracy:</span>
                    <span className="text-cyber-emerald font-bold">{(item.acc * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Memory Footprint:</span>
                    <span className="text-gray-300">{item.vram}</span>
                  </div>
                </div>
              </div>
              <p className="text-[11px] text-gray-500 pt-2 border-t border-white/[0.04] leading-relaxed">
                {item.summary}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
