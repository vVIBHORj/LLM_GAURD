import React from 'react';
import { Telemetry } from '../../types';

interface TelemetryProps {
  telemetry: Telemetry | null;
}

export const TelemetryGauges: React.FC<TelemetryProps> = ({ telemetry }) => {
  if (!telemetry) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="doppelrand-shell">
            <div className="doppelrand-core p-4 h-24 bg-oled-850/50" />
          </div>
        ))}
      </div>
    );
  }

  const ramUsed = telemetry.ram?.used_percent || 0;
  const vramUsed = telemetry.gpu?.vram_usage_percent || 0;
  const cpuUsed = telemetry.cpu?.usage_percent || 0;
  const safety = telemetry.hardware_safety_status || 'SAFE';

  const safetyStyle =
    safety === 'SAFE'
      ? { badge: 'text-cyber-emerald bg-cyber-emerald/10 ring-cyber-emerald/30', glow: 'shadow-glow-emerald', label: 'READY' }
      : safety === 'WARNING'
      ? { badge: 'text-cyber-amber bg-cyber-amber/10 ring-cyber-amber/30', glow: '', label: 'WARNING' }
      : { badge: 'text-cyber-rose bg-cyber-rose/10 ring-cyber-rose/30', glow: 'shadow-glow-rose', label: 'THROTTLED' };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. CPU Utilization */}
      <div className="doppelrand-shell group">
        <div className="doppelrand-core p-4 flex flex-col justify-between h-full">
          <div>
            <div className="flex justify-between items-center text-[11px] font-mono tracking-wider text-gray-400">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyber-cyan animate-pulse" />
                CPU COMPUTE
              </span>
              <span className="text-gray-200 font-semibold">{cpuUsed.toFixed(1)}%</span>
            </div>
            <div className="mt-2.5 w-full bg-oled-950/80 h-1.5 rounded-full overflow-hidden p-0.5 ring-1 ring-white/5">
              <div
                className="bg-gradient-to-r from-blue-500 to-cyan-400 h-full rounded-full transition-all duration-700 ease-spring-fluid"
                style={{ width: `${Math.min(100, Math.max(2, cpuUsed))}%` }}
              />
            </div>
          </div>
          <div className="mt-3 flex justify-between items-center text-[10px] font-mono text-gray-500 border-t border-white/[0.04] pt-2">
            <span>Intel i7-12700H</span>
            <span className="text-gray-400">{telemetry.cpu?.cores_logical || 20} Cores Active</span>
          </div>
        </div>
      </div>

      {/* 2. System RAM */}
      <div className="doppelrand-shell group">
        <div className="doppelrand-core p-4 flex flex-col justify-between h-full">
          <div>
            <div className="flex justify-between items-center text-[11px] font-mono tracking-wider text-gray-400">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyber-blue" />
                SYSTEM RAM
              </span>
              <span className="text-gray-200 font-semibold">{ramUsed.toFixed(1)}%</span>
            </div>
            <div className="mt-2.5 w-full bg-oled-950/80 h-1.5 rounded-full overflow-hidden p-0.5 ring-1 ring-white/5">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-spring-fluid ${
                  ramUsed > 85
                    ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                    : 'bg-gradient-to-r from-blue-500 to-indigo-400'
                }`}
                style={{ width: `${Math.min(100, Math.max(2, ramUsed))}%` }}
              />
            </div>
          </div>
          <div className="mt-3 flex justify-between items-center text-[10px] font-mono text-gray-500 border-t border-white/[0.04] pt-2">
            <span>16GB Host DDR5</span>
            <span className="text-gray-400 font-medium">
              {(telemetry.ram?.free_mb / 1024).toFixed(1)} GB Free
            </span>
          </div>
        </div>
      </div>

      {/* 3. GPU VRAM */}
      <div className="doppelrand-shell group">
        <div className="doppelrand-core p-4 flex flex-col justify-between h-full">
          <div>
            <div className="flex justify-between items-center text-[11px] font-mono tracking-wider text-gray-400">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-cyber-emerald animate-pulse" />
                NVIDIA VRAM
              </span>
              <span className="text-gray-200 font-semibold">{vramUsed.toFixed(1)}%</span>
            </div>
            <div className="mt-2.5 w-full bg-oled-950/80 h-1.5 rounded-full overflow-hidden p-0.5 ring-1 ring-white/5">
              <div
                className={`h-full rounded-full transition-all duration-700 ease-spring-fluid ${
                  vramUsed > 85
                    ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                    : 'bg-gradient-to-r from-emerald-500 to-teal-400'
                }`}
                style={{ width: `${Math.min(100, Math.max(2, vramUsed))}%` }}
              />
            </div>
          </div>
          <div className="mt-3 flex justify-between items-center text-[10px] font-mono text-gray-500 border-t border-white/[0.04] pt-2">
            <span>RTX 3050 Laptop</span>
            <span className="text-cyber-emerald font-medium">
              {telemetry.gpu?.allocated_mb?.toFixed(0) || 0} / 4096 MB
            </span>
          </div>
        </div>
      </div>

      {/* 4. Pre-Flight Hardware Gate */}
      <div className="doppelrand-shell group">
        <div className="doppelrand-core p-4 flex flex-col justify-between h-full">
          <div>
            <div className="flex justify-between items-center text-[11px] font-mono tracking-wider text-gray-400">
              <span>PRE-FLIGHT GATE</span>
              <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono ring-1 font-semibold ${safetyStyle.badge}`}>
                ● {safetyStyle.label}
              </span>
            </div>
            <div className="mt-2 text-xs font-medium text-gray-200">
              {telemetry.can_run_evaluation ? 'Single-Model Execution Ready' : 'Execution Queue Throttled'}
            </div>
          </div>
          <div className="mt-3 flex justify-between items-center text-[10px] font-mono text-gray-500 border-t border-white/[0.04] pt-2">
            <span>RAM Safety Floor</span>
            <span className="text-gray-400">&gt;= 1.5 GB Buffer</span>
          </div>
        </div>
      </div>
    </div>
  );
};
