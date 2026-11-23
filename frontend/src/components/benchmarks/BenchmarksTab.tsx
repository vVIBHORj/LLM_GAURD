import React, { useState } from 'react';
import { BenchmarkReport, Dataset, Model } from '../../types';
import { ParetoChart, ParetoChartPoint } from './ParetoChart';
import {
  transformReportToChartPoints,
  formatMetricNumber,
  formatAccuracyPercent,
} from './paretoUtils';
import { api } from '../../api/client';

interface BenchmarksTabProps {
  benchmarks: BenchmarkReport[];
  selectedModel: string;
  onNavigateTab: (tab: any) => void;
  datasets?: Dataset[];
  models?: Model[];
  onSelectModel?: (modelId: string) => void;
  loading?: boolean;
}

export const BenchmarksTab: React.FC<BenchmarksTabProps> = ({
  benchmarks,
  selectedModel,
  onNavigateTab,
  datasets = [],
  models = [],
  onSelectModel,
  loading = false,
}) => {
  const [selectedReportId, setSelectedReportId] = useState<string>('');
  const [datasetFilter, setDatasetFilter] = useState<string>('all');
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [createTitle, setCreateTitle] = useState<string>('Pareto Benchmark Comparison');
  const [createDatasetId, setCreateDatasetId] = useState<string>(datasets[0]?.id || '');
  const [createError, setCreateError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);

  // Filter available reports by dataset
  const filteredReports = datasetFilter === 'all'
    ? benchmarks
    : benchmarks.filter((b) => b.dataset_id === datasetFilter);

  // Identify active report strictly from the filtered list (prevent falling back to reports from other datasets)
  const activeReport =
    filteredReports.find((b) => b.id === selectedReportId) ||
    filteredReports[0] ||
    null;

  // Extract backend-calculated Pareto optimal model IDs directly from the report
  const paretoModelIds = new Set(
    (activeReport?.pareto_frontier || [])
      .filter((p) => p.is_pareto_optimal)
      .map((p) => p.model_id)
  );

  // Convert active report results into ParetoChart points using shared production utility
  const chartPoints: ParetoChartPoint[] = activeReport
    ? transformReportToChartPoints(activeReport, paretoModelIds)
    : [];

  // Identify hardware metadata from benchmarked results
  const hardwareSummary = (() => {
    if (!activeReport) return null;
    const gpuResult = activeReport.results.find((r) => r.gpu_name);
    if (gpuResult?.gpu_name) {
      return `${gpuResult.gpu_name} (${gpuResult.gpu_source || 'direct telemetry'})`;
    }
    return null;
  })();

  // Handle creating a new live benchmark comparison
  const handleCreateBenchmark = async () => {
    if (!createDatasetId) {
      setCreateError('Please select a dataset for the benchmark.');
      return;
    }
    const modelIds = models.map((m) => m.id);
    if (modelIds.length === 0) {
      setCreateError('No local models registered in Ollama to benchmark.');
      return;
    }

    setIsCreating(true);
    setCreateError(null);

    try {
      const newReport = await api.createBenchmark({
        title: createTitle,
        dataset_id: createDatasetId,
        model_ids: modelIds,
        temperature: 0.1,
        num_predict: 256,
        num_ctx: 2048,
        concurrency: 1,
      });

      setSelectedReportId(newReport.id);
      setShowCreateModal(false);
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create benchmark report');
    } finally {
      setIsCreating(false);
    }
  };

  // State 1: Loading
  if (loading && benchmarks.length === 0) {
    return (
      <div className="space-y-6 animate-fade-in font-mono">
        <div className="doppelrand-shell">
          <div className="doppelrand-core p-12 text-center space-y-3">
            <div className="w-8 h-8 mx-auto border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            <div className="text-sm text-gray-300 font-semibold">Loading Benchmark Reports...</div>
            <div className="text-xs text-gray-500">Querying verified evaluation lineage and telemetry.</div>
          </div>
        </div>
      </div>
    );
  }

  // State 2: No Reports Globally
  if (benchmarks.length === 0) {
    return (
      <div className="space-y-6 animate-fade-in">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-gray-100 tracking-tight">
              Multi-Model Speed vs. Accuracy Pareto Frontier
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Empirical multi-model benchmark comparisons and non-dominated Pareto analysis.
            </p>
          </div>
          <button
            onClick={() => onNavigateTab('evaluations')}
            className="text-xs font-mono px-3 py-1.5 rounded bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 border border-cyan-500/30 transition-colors"
          >
            Go to Evaluations Tab →
          </button>
        </div>

        <div className="doppelrand-shell">
          <div className="doppelrand-core p-12 text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-xl font-mono">
              📈
            </div>
            <div>
              <h3 className="text-base font-bold text-gray-200">
                No Benchmark Reports Recorded Yet
              </h3>
              <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto leading-relaxed">
                LocalLLM Guard benchmarks evaluate local models under controlled generation hyperparameters
                (temperature, context window, and concurrency) on a shared dataset to establish true empirical Pareto frontiers.
              </p>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row justify-center gap-3">
              <button
                onClick={() => onNavigateTab('evaluations')}
                className="px-4 py-2 text-xs font-mono font-semibold rounded bg-cyan-500 text-black hover:bg-cyan-400 transition-colors"
              >
                Run Model Evaluations
              </button>
              {datasets.length > 0 && (
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-4 py-2 text-xs font-mono font-semibold rounded bg-white/5 text-gray-200 hover:bg-white/10 border border-white/10 transition-colors"
                >
                  Generate Benchmark Comparison
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Create Benchmark Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="doppelrand-shell w-full max-w-md">
              <div className="doppelrand-core p-6 space-y-4 font-mono">
                <div className="flex justify-between items-center border-b border-white/[0.08] pb-3">
                  <h3 className="text-sm font-bold text-gray-100">Create Benchmark Comparison</h3>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="text-gray-400 hover:text-white text-xs"
                  >
                    ✕
                  </button>
                </div>

                {createError && (
                  <div className="p-3 text-xs bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded">
                    {createError}
                  </div>
                )}

                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-gray-400 mb-1">Benchmark Title</label>
                    <input
                      type="text"
                      value={createTitle}
                      onChange={(e) => setCreateTitle(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-gray-200 focus:outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="block text-gray-400 mb-1">Dataset</label>
                    <select
                      value={createDatasetId}
                      onChange={(e) => setCreateDatasetId(e.target.value)}
                      className="w-full bg-[#0E131F] border border-white/10 rounded px-3 py-2 text-gray-200 focus:outline-none focus:border-cyan-500"
                    >
                      {datasets.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.task_type})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="text-[11px] text-gray-500 pt-2 border-t border-white/[0.04]">
                    Models included: {models.map((m) => m.id).join(', ') || 'No local models'}
                  </div>
                </div>

                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="px-3 py-1.5 text-xs text-gray-400 hover:text-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateBenchmark}
                    disabled={isCreating}
                    className="px-4 py-1.5 text-xs font-semibold rounded bg-cyan-500 text-black hover:bg-cyan-400 disabled:opacity-50"
                  >
                    {isCreating ? 'Evaluating...' : 'Create Benchmark'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // State 3: Reports Exist Globally, but None Match the Selected Dataset
  if (!activeReport) {
    const selectedDatasetObj = datasets.find((d) => d.id === datasetFilter);
    return (
      <div className="space-y-6 animate-fade-in font-sans">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-gray-100 tracking-tight">
              Multi-Model Speed vs. Accuracy Pareto Frontier
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Empirical multi-model benchmark comparisons for evaluated local models.
            </p>
          </div>
        </div>

        {/* Dataset filter bar */}
        <div className="doppelrand-shell">
          <div className="doppelrand-core p-4 flex items-center space-x-3 text-xs font-mono">
            <span className="text-gray-400">Dataset Filter:</span>
            <select
              value={datasetFilter}
              onChange={(e) => setDatasetFilter(e.target.value)}
              className="bg-[#0E131F] border border-white/10 rounded px-2.5 py-1 text-gray-200 focus:outline-none focus:border-cyan-500 font-mono text-xs"
            >
              <option value="all">All Datasets ({benchmarks.length} reports)</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
            <button
              onClick={() => setDatasetFilter('all')}
              className="text-[11px] text-cyan-400 hover:underline"
            >
              Reset to All
            </button>
          </div>
        </div>

        <div className="doppelrand-shell">
          <div className="doppelrand-core p-10 text-center space-y-3 font-mono">
            <div className="text-amber-400 text-lg">⚠️</div>
            <div className="text-sm font-bold text-gray-200">
              No Benchmark Reports for Dataset: {selectedDatasetObj?.name || datasetFilter}
            </div>
            <p className="text-xs text-gray-400 max-w-md mx-auto">
              There are {benchmarks.length} benchmark report(s) available for other datasets, but none matching this dataset yet.
            </p>
            <div className="pt-2 flex justify-center gap-3">
              <button
                onClick={() => setDatasetFilter('all')}
                className="px-3 py-1.5 text-xs font-semibold rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/20"
              >
                View All Reports ({benchmarks.length})
              </button>
              <button
                onClick={() => {
                  setCreateDatasetId(datasetFilter);
                  setShowCreateModal(true);
                }}
                className="px-3 py-1.5 text-xs font-semibold rounded bg-cyan-500 text-black hover:bg-cyan-400"
              >
                Benchmark This Dataset
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Count benchmark status categories
  const benchmarkedCount = activeReport.results.filter((r) => r.status === 'BENCHMARKED').length;
  const unbenchmarkedCount = activeReport.results.filter((r) => r.status === 'UNBENCHMARKED').length;
  const ineligibleCount = activeReport.results.filter((r) => r.status === 'INELIGIBLE').length;

  return (
    <div className="space-y-6 animate-fade-in font-sans">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-gray-100 tracking-tight">
            Multi-Model Speed vs. Accuracy Pareto Frontier
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Empirical benchmark measurements for <span className="text-cyan-400 font-mono">{selectedModel}</span> and evaluated local models.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center space-x-4 text-xs font-mono">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-cyber-emerald" />
            <span className="text-cyber-emerald font-semibold">Pareto Optimal</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-400" />
            <span className="text-sky-400 font-semibold">Dominated</span>
          </div>
        </div>
      </div>

      {/* Report Controls & Filters Bar */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-4 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
          <div className="flex flex-wrap items-center gap-3">
            {/* Report Selector Dropdown */}
            <div className="flex items-center space-x-2">
              <span className="text-gray-400">Report:</span>
              <select
                value={activeReport.id}
                onChange={(e) => setSelectedReportId(e.target.value)}
                className="bg-[#0E131F] border border-white/10 rounded px-2.5 py-1 text-gray-200 focus:outline-none focus:border-cyan-500 font-mono text-xs"
              >
                {filteredReports.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title} ({new Date(r.generated_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>

            {/* Dataset Filter Dropdown */}
            {datasets.length > 0 && (
              <div className="flex items-center space-x-2">
                <span className="text-gray-400">Dataset:</span>
                <select
                  value={datasetFilter}
                  onChange={(e) => {
                    const newFilter = e.target.value;
                    setDatasetFilter(newFilter);
                    const matching = newFilter === 'all'
                      ? benchmarks
                      : benchmarks.filter((b) => b.dataset_id === newFilter);
                    if (matching.length > 0) {
                      setSelectedReportId(matching[0].id);
                    }
                  }}
                  className="bg-[#0E131F] border border-white/10 rounded px-2.5 py-1 text-gray-200 focus:outline-none focus:border-cyan-500 font-mono text-xs"
                >
                  <option value="all">All Datasets ({benchmarks.length})</option>
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Controlled Generation Hyperparameters Badge */}
          {activeReport.generation_config && (
            <div className="flex items-center space-x-3 text-[11px] text-gray-400 bg-white/[0.02] px-2.5 py-1 rounded border border-white/[0.04]">
              <span>T: <strong className="text-cyan-300">{activeReport.generation_config.temperature}</strong></span>
              <span>Predict: <strong className="text-cyan-300">{activeReport.generation_config.num_predict}</strong></span>
              <span>Ctx: <strong className="text-cyan-300">{activeReport.generation_config.num_ctx}</strong></span>
              <span>Conc: <strong className="text-cyan-300">{activeReport.generation_config.concurrency}</strong></span>
            </div>
          )}
        </div>
      </div>

      {/* Partial Data Notice Banner */}
      {(unbenchmarkedCount > 0 || ineligibleCount > 0) && (
        <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs font-mono flex items-start space-x-3 text-amber-300">
          <span className="text-base leading-none">⚠️</span>
          <div>
            <span className="font-semibold">Partial Benchmark Coverage:</span>{' '}
            {benchmarkedCount} model{benchmarkedCount !== 1 ? 's' : ''} benchmarked on this dataset.
            {unbenchmarkedCount > 0 && ` ${unbenchmarkedCount} model${unbenchmarkedCount !== 1 ? 's' : ''} have no completed runs.`}
            {ineligibleCount > 0 && ` ${ineligibleCount} model${ineligibleCount !== 1 ? 's' : ''} excluded due to hyperparameter mismatch.`}
          </div>
        </div>
      )}

      {/* Main Interactive Chart Shell */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-2">
            <div>
              <h3 className="text-sm font-bold text-gray-200">
                Inference Throughput vs. Assertion Accuracy Trade-off
              </h3>
              <p className="text-[11px] text-gray-500 mt-0.5 font-mono">
                Pareto optimal models maximize accuracy without sacrificing throughput under single-model residency.
              </p>
            </div>
            {hardwareSummary && (
              <span className="text-[11px] font-mono text-gray-400 bg-white/[0.03] px-2.5 py-1 rounded border border-white/[0.06]">
                Hardware: {hardwareSummary}
              </span>
            )}
          </div>

          <ParetoChart
            points={chartPoints}
            selectedModel={selectedModel}
            onSelectModel={onSelectModel}
          />
        </div>
      </div>

      {/* Benchmark Comparison Matrix Cards (Dynamic from empirical report results) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {activeReport.results.map((r) => {
          const isPareto = paretoModelIds.has(r.model_id);
          const isSelected = selectedModel === r.model_id;

          let statusBadgeClass = 'bg-cyan-500/10 text-cyan-400 ring-cyan-500/30';
          let statusText = r.status;

          if (r.status === 'BENCHMARKED') {
            if (isPareto) {
              statusBadgeClass = 'bg-cyber-emerald/10 text-cyber-emerald ring-cyber-emerald/30';
              statusText = 'PARETO OPTIMAL';
            } else {
              statusBadgeClass = 'bg-sky-500/10 text-sky-400 ring-sky-500/30';
              statusText = 'DOMINATED';
            }
          } else if (r.status === 'UNBENCHMARKED') {
            statusBadgeClass = 'bg-amber-500/10 text-amber-400 ring-amber-500/30';
            statusText = 'UNBENCHMARKED';
          } else if (r.status === 'INELIGIBLE') {
            statusBadgeClass = 'bg-rose-500/10 text-rose-400 ring-rose-500/30';
            statusText = 'INELIGIBLE';
          }

          return (
            <div
              key={r.model_id}
              onClick={() => onSelectModel && onSelectModel(r.model_id)}
              className={`doppelrand-shell cursor-pointer transition-all ${
                isSelected ? 'ring-1 ring-cyan-500/50' : ''
              }`}
            >
              <div className="doppelrand-core p-5 flex flex-col justify-between h-full space-y-3">
                <div>
                  <div className="flex justify-between items-center text-xs font-mono">
                    <span className="font-bold text-gray-100 truncate max-w-[170px]" title={r.model_id}>
                      {r.model_id}
                    </span>
                    <span className={`text-[9px] px-2 py-0.5 rounded-full ring-1 font-semibold ${statusBadgeClass}`}>
                      {statusText}
                    </span>
                  </div>

                  <div className="mt-3 space-y-1.5 text-xs font-mono text-gray-400">
                    <div className="flex justify-between">
                      <span>Throughput:</span>
                      <span className="text-cyan-400 font-bold">
                        {formatMetricNumber(r.speed_tokens_sec, 't/s', 1)}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span>Accuracy:</span>
                      <span className="text-cyber-emerald font-bold">
                        {formatAccuracyPercent(r.accuracy_score)}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span>Average Latency:</span>
                      <span className="text-gray-200">
                        {formatMetricNumber(r.avg_latency_ms, 'ms', 1)}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span>System Peak VRAM:</span>
                      <span className="text-gray-200">
                        {formatMetricNumber(r.peak_vram_mb, 'MB', 0)}
                      </span>
                    </div>

                    <div className="flex justify-between">
                      <span>Ollama Model VRAM:</span>
                      <span className="text-purple-300">
                        {formatMetricNumber(r.peak_ollama_vram_mb, 'MB', 0)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-white/[0.04] text-[10px] font-mono text-gray-500 space-y-0.5">
                  <div className="flex justify-between truncate">
                    <span>GPU:</span>
                    <span className="text-gray-400 truncate max-w-[140px]" title={r.gpu_name || 'N/A'}>
                      {r.gpu_name || 'N/A'} {r.gpu_source ? `(${r.gpu_source})` : ''}
                    </span>
                  </div>
                  <div className="flex justify-between truncate">
                    <span>Run ID:</span>
                    <span className="text-gray-400 font-mono">
                      {r.run_id ? `${r.run_id.slice(0, 8)}...` : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
