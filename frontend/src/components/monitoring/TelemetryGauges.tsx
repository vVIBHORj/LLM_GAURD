import React from 'react';

interface TelemetryProps {
  telemetry: any;
}

export const TelemetryGauges: React.FC<TelemetryProps> = ({ telemetry }) => {
  if (!telemetry) return null;

  const ramUsed = telemetry.ram?.used_percent || 0;
  const vramUsed = telemetry.gpu?.vram_usage_percent || 0;
  const cpuUsed = telemetry.cpu?.usage_percent || 0;
  const safety = telemetry.hardware_safety_status || 'SAFE';

  const safetyColor =
    safety === 'SAFE' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' :
    safety === 'WARNING' ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' :
    'text-rose-400 bg-rose-500/10 border-rose-500/20';

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-[#111827] border border-[#1F2937] rounded-xl shadow-lg">
      {/* CPU Gauge */}
      <div className="flex flex-col">
        <div className="flex justify-between items-center text-xs text-gray-400 mb-1">
          <span className="font-medium tracking-wide">CPU UTILIZATION</span>
          <span className="font-mono text-gray-200">{cpuUsed.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
          <div
            className="bg-blue-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, cpuUsed)}%` }}
          />
        </div>
        <span className="text-[11px] text-gray-500 mt-1 font-mono">
          {telemetry.cpu?.cores_logical || 20} Logical Cores
        </span>
      </div>

      {/* RAM Gauge */}
      <div className="flex flex-col">
        <div className="flex justify-between items-center text-xs text-gray-400 mb-1">
          <span className="font-medium tracking-wide">SYSTEM RAM</span>
          <span className="font-mono text-gray-200">{ramUsed.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              ramUsed > 85 ? 'bg-amber-500' : 'bg-blue-500'
            }`}
            style={{ width: `${Math.min(100, ramUsed)}%` }}
          />
        </div>
        <span className="text-[11px] text-gray-400 mt-1 font-mono">
          {(telemetry.ram?.free_mb / 1024).toFixed(1)} GB Free of {(telemetry.ram?.total_mb / 1024).toFixed(1)} GB
        </span>
      </div>

      {/* VRAM Gauge */}
      <div className="flex flex-col">
        <div className="flex justify-between items-center text-xs text-gray-400 mb-1">
          <span className="font-medium tracking-wide">NVIDIA GPU VRAM</span>
          <span className="font-mono text-gray-200">{vramUsed.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              vramUsed > 85 ? 'bg-rose-500' : 'bg-emerald-500'
            }`}
            style={{ width: `${Math.min(100, vramUsed)}%` }}
          />
        </div>
        <span className="text-[11px] text-gray-400 mt-1 font-mono">
          {telemetry.gpu?.allocated_mb?.toFixed(0) || 0} MB / 4096 MB VRAM
        </span>
      </div>

      {/* Hardware Safety Envelope */}
      <div className="flex flex-col justify-center">
        <div className="text-xs text-gray-400 mb-1 font-medium tracking-wide">PRE-FLIGHT GATE</div>
        <div className={`px-2.5 py-1 rounded-md border text-xs font-mono font-medium flex items-center justify-between ${safetyColor}`}>
          <span>STATUS: {safety}</span>
          <span className="text-[10px] uppercase">
            {telemetry.can_run_evaluation ? '● READY' : '■ THROTTLED'}
          </span>
        </div>
      </div>
    </div>
  );
};
