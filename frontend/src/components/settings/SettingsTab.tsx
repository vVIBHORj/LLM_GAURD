import React from 'react';

export const SettingsTab: React.FC = () => {
  return (
    <div className="space-y-6 animate-fade-in max-w-4xl">
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6 space-y-5">
          <div className="border-b border-white/[0.06] pb-3">
            <h2 className="text-lg font-bold text-gray-100">
              Hardware Environment & Infrastructure Settings
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Calibrated for local-first execution on Windows 11 with NVIDIA RTX 3050.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-xl bg-oled-950/70 border border-white/[0.06]">
              <span className="text-gray-500 uppercase text-[10px]">OLLAMA SERVER ADDRESS</span>
              <div className="text-cyan-400 font-semibold mt-1">http://127.0.0.1:11434</div>
              <div className="text-[11px] text-gray-500 mt-1">Explicit IPv4 binding to bypass Node IPv6 resolution</div>
            </div>

            <div className="p-3.5 rounded-xl bg-oled-950/70 border border-white/[0.06]">
              <span className="text-gray-500 uppercase text-[10px]">PRE-FLIGHT RAM BUFFER</span>
              <div className="text-cyber-emerald font-semibold mt-1">1,500 MB Mandatory Buffer</div>
              <div className="text-[11px] text-gray-500 mt-1">Blocks memory exhaustion on 16GB host system</div>
            </div>

            <div className="p-3.5 rounded-xl bg-oled-950/70 border border-white/[0.06]">
              <span className="text-gray-500 uppercase text-[10px]">PROMPTFOO CLI HARNESS</span>
              <div className="text-gray-200 font-semibold mt-1">v0.126.0 (Subprocess Orchestrator)</div>
              <div className="text-[11px] text-gray-500 mt-1">Managed child process with kill-tree timeout protection</div>
            </div>

            <div className="p-3.5 rounded-xl bg-oled-950/70 border border-white/[0.06]">
              <span className="text-gray-500 uppercase text-[10px]">GPU RESIDENCY PROTOCOL</span>
              <div className="text-cyber-emerald font-semibold mt-1">Single-Model Serial Queue</div>
              <div className="text-[11px] text-gray-500 mt-1">Flushes previous weights before loading next model</div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-oled-950/70 border border-white/[0.06] text-xs font-mono space-y-1">
            <div className="text-gray-400 font-bold mb-1">Empirically Verified Hardware Profile:</div>
            <div className="text-gray-500">• CPU: Intel Core i7-12700H (14 cores, 20 logical threads)</div>
            <div className="text-gray-500">• GPU: NVIDIA GeForce RTX 3050 Laptop GPU (4096 MiB VRAM, Compute 8.6)</div>
            <div className="text-gray-500">• Host Memory: 16.0 GB DDR5 RAM</div>
            <div className="text-gray-500">• Database: SQLite 3 with PRAGMA journal_mode = WAL</div>
          </div>
        </div>
      </div>
    </div>
  );
};
