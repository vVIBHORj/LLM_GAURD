import React, { useState } from 'react';

export interface ParetoPointData {
  model_id: string;
  tokens_per_sec: number;
  accuracy_rate: number;
  vram_mb: number;
  is_pareto: boolean;
  notes: string;
}

const DEFAULT_POINTS: ParetoPointData[] = [
  { model_id: 'llama3.2:latest', tokens_per_sec: 109.3, accuracy_rate: 0.92, vram_mb: 2200, is_pareto: true, notes: 'Fastest 3B inference in VRAM' },
  { model_id: 'qwen3:4b', tokens_per_sec: 41.9, accuracy_rate: 0.91, vram_mb: 2500, is_pareto: true, notes: 'Optimal reasoning speed/quality' },
  { model_id: 'qwen3:8b', tokens_per_sec: 14.7, accuracy_rate: 0.94, vram_mb: 5200, is_pareto: true, notes: 'Maximum reasoning depth' },
  { model_id: 'qwen3:1.7b', tokens_per_sec: 70.0, accuracy_rate: 0.82, vram_mb: 1400, is_pareto: false, notes: 'Ultra-compact edge model' },
  { model_id: 'qwen2.5:3b', tokens_per_sec: 55.0, accuracy_rate: 0.88, vram_mb: 1900, is_pareto: false, notes: 'Standard coding baseline' },
];

export const ParetoChart: React.FC<{ points?: ParetoPointData[] }> = ({ points = DEFAULT_POINTS }) => {
  const [hoveredPoint, setHoveredPoint] = useState<ParetoPointData | null>(null);

  // SVG dimensions
  const width = 640;
  const height = 320;
  const padding = { top: 30, right: 40, bottom: 50, left: 60 };

  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  // Max X: 120 t/s, Max Y: 1.0 (100%)
  const maxX = 120;
  const minX = 0;
  const maxY = 1.0;
  const minY = 0.7; // zoom in on meaningful accuracy range (70% - 100%)

  const scaleX = (val: number) => padding.left + ((val - minX) / (maxX - minX)) * plotW;
  const scaleY = (val: number) => padding.top + plotH - ((val - minY) / (maxY - minY)) * plotH;

  // Sort pareto points by X for line rendering
  const paretoPoints = points
    .filter((p) => p.is_pareto)
    .sort((a, b) => a.tokens_per_sec - b.tokens_per_sec);

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
        {/* Subtle Grid Lines */}
        {[0.75, 0.8, 0.85, 0.9, 0.95, 1.0].map((acc) => {
          const y = scaleY(acc);
          return (
            <g key={acc}>
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

        {[20, 40, 60, 80, 100, 120].map((speed) => {
          const x = scaleX(speed);
          return (
            <g key={speed}>
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
                {speed} t/s
              </text>
            </g>
          );
        })}

        {/* Axes */}
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

        {/* Axis Labels */}
        <text
          x={width / 2}
          y={height - 12}
          textAnchor="middle"
          fontSize="11"
          fontWeight="500"
          fill="#9CA3AF"
          fontFamily="Plus Jakarta Sans"
        >
          Generation Speed (Tokens / Second) →
        </text>
        <text
          x={18}
          y={height / 2}
          textAnchor="middle"
          fontSize="11"
          fontWeight="500"
          fill="#9CA3AF"
          transform={`rotate(-90 18 ${height / 2})`}
          fontFamily="Plus Jakarta Sans"
        >
          Accuracy Rate →
        </text>

        {/* Pareto Frontier Curve Area fill */}
        {paretoPoints.length > 1 && (
          <path
            d={`${paretoPath} L ${scaleX(paretoPoints[paretoPoints.length - 1].tokens_per_sec)} ${height - padding.bottom} L ${scaleX(paretoPoints[0].tokens_per_sec)} ${height - padding.bottom} Z`}
            fill="url(#pareto-gradient)"
            opacity="0.12"
          />
        )}

        <defs>
          <linearGradient id="pareto-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#10B981" />
            <stop offset="100%" stopColor="#06B6D4" />
          </linearGradient>
        </defs>

        {/* Pareto Frontier Line */}
        {paretoPoints.length > 1 && (
          <path
            d={paretoPath}
            fill="none"
            stroke="#10B981"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeDasharray="none"
            className="drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]"
          />
        )}

        {/* Data Points */}
        {points.map((p) => {
          const cx = scaleX(p.tokens_per_sec);
          const cy = scaleY(p.accuracy_rate);
          const isHovered = hoveredPoint?.model_id === p.model_id;

          return (
            <g
              key={p.model_id}
              className="cursor-pointer transition-transform duration-300"
              onMouseEnter={() => setHoveredPoint(p)}
              onMouseLeave={() => setHoveredPoint(null)}
            >
              {/* Outer halo */}
              {p.is_pareto && (
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 14 : 9}
                  fill="none"
                  stroke="#10B981"
                  strokeWidth="1.5"
                  strokeOpacity={isHovered ? '0.7' : '0.3'}
                  className="animate-pulse"
                />
              )}

              {/* Core node */}
              <circle
                cx={cx}
                cy={cy}
                r={isHovered ? 6 : 4.5}
                fill={p.is_pareto ? '#10B981' : '#3B82F6'}
                stroke="#090D15"
                strokeWidth="2"
                className="transition-all duration-300"
              />

              {/* Point Label */}
              <text
                x={cx}
                y={cy - 12}
                textAnchor="middle"
                fontSize="10"
                fontWeight={p.is_pareto ? '600' : '400'}
                fill={p.is_pareto ? '#34D399' : '#94A3B8'}
                className="pointer-events-none"
              >
                {p.model_id.split(':')[0]}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Floating Tooltip */}
      {hoveredPoint && (
        <div
          className="absolute z-20 pointer-events-none doppelrand-shell -translate-x-1/2 -translate-y-full"
          style={{
            left: `${scaleX(hoveredPoint.tokens_per_sec)}px`,
            top: `${scaleY(hoveredPoint.accuracy_rate) - 14}px`,
          }}
        >
          <div className="doppelrand-core p-3 text-xs font-mono space-y-1 min-w-[180px]">
            <div className="flex items-center justify-between font-bold text-gray-100">
              <span>{hoveredPoint.model_id}</span>
              {hoveredPoint.is_pareto && (
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyber-emerald/20 text-cyber-emerald ring-1 ring-cyber-emerald/30">
                  PARETO
                </span>
              )}
            </div>
            <div className="text-gray-400 text-[11px] flex justify-between">
              <span>Speed:</span>
              <span className="text-cyan-400 font-semibold">{hoveredPoint.tokens_per_sec} t/s</span>
            </div>
            <div className="text-gray-400 text-[11px] flex justify-between">
              <span>Accuracy:</span>
              <span className="text-emerald-400 font-semibold">{(hoveredPoint.accuracy_rate * 100).toFixed(0)}%</span>
            </div>
            <div className="text-gray-500 text-[10px] italic pt-1 border-t border-white/[0.04]">
              {hoveredPoint.notes}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
