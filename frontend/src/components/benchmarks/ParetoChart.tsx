import React, { useState } from 'react';
import {
  filterValidChartPoints,
  calculateChartBounds,
  sortParetoFrontier,
  formatMetricNumber,
  formatAccuracyPercent,
} from './paretoUtils';

export interface ParetoChartPoint {
  model_id: string;
  run_id?: string | null;
  tokens_per_sec: number;
  accuracy_rate: number;
  peak_vram_mb?: number | null;
  peak_ollama_vram_mb?: number | null;
  gpu_name?: string | null;
  gpu_source?: string | null;
  is_pareto: boolean;
  status: string;
}

export interface ParetoChartProps {
  points?: ParetoChartPoint[];
  selectedModel?: string;
  onSelectModel?: (modelId: string) => void;
}

function calculateTicks(min: number, max: number, count: number): number[] {
  if (min === max) return [min];
  const step = (max - min) / (count - 1);
  const ticks: number[] = [];
  for (let i = 0; i < count; i++) {
    ticks.push(min + i * step);
  }
  return ticks;
}

export const ParetoChart: React.FC<ParetoChartProps> = ({
  points = [],
  selectedModel,
  onSelectModel,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<ParetoChartPoint | null>(null);

  // Filter only genuine measured benchmark points with valid numbers (rejects null, negative, NaN)
  const validPoints = filterValidChartPoints(points);

  // SVG dimensions
  const width = 640;
  const height = 320;
  const padding = { top: 35, right: 45, bottom: 50, left: 60 };

  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  // Empty state if no valid data
  if (validPoints.length === 0) {
    return (
      <div className="w-full h-64 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-lg p-6 text-center font-mono">
        <div className="w-10 h-10 rounded-full bg-cyan-500/10 flex items-center justify-center text-cyan-400 mb-3">
          📊
        </div>
        <div className="text-sm font-semibold text-gray-300">
          No Empirical Benchmark Data Plotted
        </div>
        <p className="text-xs text-gray-500 mt-1 max-w-sm">
          No models in the selected benchmark report have completed evaluations with valid throughput and accuracy measurements.
        </p>
      </div>
    );
  }

  // Dynamic bounds calculation
  const bounds = calculateChartBounds(validPoints);
  const { minX, maxX, minY, maxY, spanX, spanY } = bounds;

  const scaleX = (val: number) => padding.left + ((val - minX) / spanX) * plotW;
  const scaleY = (val: number) => padding.top + plotH - ((val - minY) / spanY) * plotH;

  // Generate 4-5 dynamic tick marks
  const xTicks = calculateTicks(minX, maxX, 5);
  const yTicks = calculateTicks(minY, maxY, 5);

  // Extract non-dominated Pareto frontier points sorted in ascending throughput order
  const paretoPoints = sortParetoFrontier(validPoints);

  // Construct SVG path along the Pareto frontier
  const paretoPath = paretoPoints.reduce((acc, curr, idx) => {
    const x = scaleX(curr.tokens_per_sec);
    const y = scaleY(curr.accuracy_rate);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  return (
    <div className="relative w-full">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full h-auto overflow-visible select-none font-mono"
      >
        <defs>
          <linearGradient id="pareto-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#10B981" />
            <stop offset="100%" stopColor="#06B6D4" />
          </linearGradient>
        </defs>

        {/* Dynamic Y Grid Lines & Labels */}
        {yTicks.map((acc) => {
          const y = scaleY(acc);
          return (
            <g key={`y-${acc.toFixed(2)}`}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeDasharray="3 3"
              />
              <text
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                fontSize="10"
                fill="#6B7280"
              >
                {(acc * 100).toFixed(0)}%
              </text>
            </g>
          );
        })}

        {/* Dynamic X Grid Lines & Labels */}
        {xTicks.map((speed) => {
          const x = scaleX(speed);
          return (
            <g key={`x-${speed.toFixed(1)}`}>
              <line
                x1={x}
                y1={padding.top}
                x2={x}
                y2={height - padding.bottom}
                stroke="rgba(255, 255, 255, 0.05)"
                strokeDasharray="3 3"
              />
              <text
                x={x}
                y={height - padding.bottom + 18}
                textAnchor="middle"
                fontSize="10"
                fill="#6B7280"
              >
                {speed.toFixed(0)} t/s
              </text>
            </g>
          );
        })}

        {/* Main Axes */}
        <line
          x1={padding.left}
          y1={height - padding.bottom}
          x2={width - padding.right}
          y2={height - padding.bottom}
          stroke="rgba(255, 255, 255, 0.15)"
        />
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={height - padding.bottom}
          stroke="rgba(255, 255, 255, 0.15)"
        />

        {/* Axis Titles */}
        <text
          x={width / 2}
          y={height - 12}
          textAnchor="middle"
          fontSize="11"
          fontWeight="500"
          fill="#9CA3AF"
          fontFamily="Plus Jakarta Sans, sans-serif"
        >
          Inference Throughput (Tokens / Second) →
        </text>
        <text
          x={18}
          y={height / 2}
          textAnchor="middle"
          fontSize="11"
          fontWeight="500"
          fill="#9CA3AF"
          transform={`rotate(-90 18 ${height / 2})`}
          fontFamily="Plus Jakarta Sans, sans-serif"
        >
          Accuracy Rate (%) →
        </text>

        {/* Pareto Frontier Area fill (only if multiple pareto points) */}
        {paretoPoints.length > 1 && (
          <path
            d={`${paretoPath} L ${scaleX(paretoPoints[paretoPoints.length - 1].tokens_per_sec)} ${height - padding.bottom} L ${scaleX(paretoPoints[0].tokens_per_sec)} ${height - padding.bottom} Z`}
            fill="url(#pareto-gradient)"
            opacity="0.10"
          />
        )}

        {/* Pareto Frontier Line */}
        {paretoPoints.length > 1 && (
          <path
            d={paretoPath}
            fill="none"
            stroke="#10B981"
            strokeWidth="2.5"
            strokeLinecap="round"
            className="drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]"
          />
        )}

        {/* Data Nodes */}
        {validPoints.map((p) => {
          const cx = scaleX(p.tokens_per_sec);
          const cy = scaleY(p.accuracy_rate);
          const isHovered = hoveredPoint?.model_id === p.model_id;
          const isSelected = selectedModel === p.model_id;

          // Compute readable label positioning preventing clipping near edges
          const labelY = cy - 12 < padding.top ? cy + 18 : cy - 12;
          let textAnchor: 'start' | 'middle' | 'end' = 'middle';
          let labelX = cx;
          if (cx > width - padding.right - 35) {
            textAnchor = 'end';
            labelX = cx - 8;
          } else if (cx < padding.left + 35) {
            textAnchor = 'start';
            labelX = cx + 8;
          }

          const shortName = p.model_id.replace(':latest', '');

          return (
            <g
              key={p.model_id}
              className="cursor-pointer transition-transform duration-200"
              onMouseEnter={() => setHoveredPoint(p)}
              onMouseLeave={() => setHoveredPoint(null)}
              onClick={() => onSelectModel && onSelectModel(p.model_id)}
            >
              {/* Outer pulsing halo for Pareto Optimal models */}
              {p.is_pareto && (
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered || isSelected ? 14 : 9}
                  fill="none"
                  stroke="#10B981"
                  strokeWidth="1.5"
                  strokeOpacity={isHovered || isSelected ? '0.8' : '0.35'}
                  className="animate-pulse"
                />
              )}

              {/* Selected model indicator ring */}
              {isSelected && (
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 18 : 13}
                  fill="none"
                  stroke="#38BDF8"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                />
              )}

              {/* Core node */}
              <circle
                cx={cx}
                cy={cy}
                r={isHovered ? 6 : p.is_pareto ? 5 : 4}
                fill={p.is_pareto ? '#10B981' : '#38BDF8'}
                stroke="#090D15"
                strokeWidth="2"
                className="transition-all duration-200"
              />

              {/* Model Label */}
              <text
                x={labelX}
                y={labelY}
                textAnchor={textAnchor}
                fontSize="10"
                fontWeight={p.is_pareto ? '600' : '400'}
                fill={p.is_pareto ? '#34D399' : '#94A3B8'}
                className="pointer-events-none"
              >
                {shortName}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Floating Interactive Tooltip */}
      {hoveredPoint && (
        <div
          className="absolute z-30 pointer-events-none doppelrand-shell -translate-x-1/2 -translate-y-full"
          style={{
            left: `${Math.max(100, Math.min(width - 100, scaleX(hoveredPoint.tokens_per_sec)))}px`,
            top: `${Math.max(10, scaleY(hoveredPoint.accuracy_rate) - 14)}px`,
          }}
        >
          <div className="doppelrand-core p-3 text-xs font-mono space-y-1.5 min-w-[210px]">
            <div className="flex items-center justify-between font-bold text-gray-100 pb-1 border-b border-white/[0.08]">
              <span className="truncate max-w-[130px]">{hoveredPoint.model_id}</span>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded font-semibold ${
                  hoveredPoint.is_pareto
                    ? 'bg-cyber-emerald/20 text-cyber-emerald ring-1 ring-cyber-emerald/30'
                    : 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/30'
                }`}
              >
                {hoveredPoint.is_pareto ? 'PARETO OPTIMAL' : 'DOMINATED'}
              </span>
            </div>

            <div className="text-gray-400 text-[11px] flex justify-between">
              <span>Throughput:</span>
              <span className="text-cyan-400 font-semibold">{formatMetricNumber(hoveredPoint.tokens_per_sec, 't/s', 1)}</span>
            </div>
            <div className="text-gray-400 text-[11px] flex justify-between">
              <span>Accuracy:</span>
              <span className="text-emerald-400 font-semibold">
                {formatAccuracyPercent(hoveredPoint.accuracy_rate)}
              </span>
            </div>

            {hoveredPoint.peak_vram_mb != null && (
              <div className="text-gray-400 text-[11px] flex justify-between">
                <span>Peak GPU VRAM:</span>
                <span className="text-gray-200">{formatMetricNumber(hoveredPoint.peak_vram_mb, 'MB', 0)}</span>
              </div>
            )}

            {hoveredPoint.peak_ollama_vram_mb != null && (
              <div className="text-gray-400 text-[11px] flex justify-between">
                <span>Model VRAM:</span>
                <span className="text-purple-300">{formatMetricNumber(hoveredPoint.peak_ollama_vram_mb, 'MB', 0)}</span>
              </div>
            )}

            {hoveredPoint.gpu_name && (
              <div className="text-gray-500 text-[10px] pt-1 border-t border-white/[0.04] truncate">
                GPU: {hoveredPoint.gpu_name} {hoveredPoint.gpu_source ? `(${hoveredPoint.gpu_source})` : ''}
              </div>
            )}

            {hoveredPoint.run_id && (
              <div className="text-gray-600 text-[9px] truncate">
                Run: {hoveredPoint.run_id}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
