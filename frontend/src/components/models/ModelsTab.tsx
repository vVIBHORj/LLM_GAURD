import React from 'react';
import { Model } from '../../types';

interface ModelsTabProps {
  models: Model[];
  selectedModel: string;
  onSelectModel: (id: string) => void;
  onNavigateTab: (tab: any) => void;
}

export const ModelsTab: React.FC<ModelsTabProps> = ({
  models,
  selectedModel,
  onSelectModel,
  onNavigateTab,
}) => {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-100 tracking-tight">
            Local Ollama Model Registry
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Synchronized with Ollama daemon. Evaluated under strict single-model VRAM residency.
          </p>
        </div>
        <span className="text-xs font-mono text-gray-500">
          Showing {models.length} Discovered Models
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {models.map((m) => {
          const isSelected = selectedModel === m.id;
          const sizeGb = m.disk_size_bytes ? (m.disk_size_bytes / 1024 ** 3).toFixed(2) : 'N/A';
          const isLarge = sizeGb !== 'N/A' && parseFloat(sizeGb) > 3.0;

          return (
            <div
              key={m.id}
              className={`doppelrand-shell transition-all duration-300 ${
                isSelected ? 'ring-2 ring-cyan-500/50 shadow-glow-cyan' : ''
              }`}
            >
              <div className="doppelrand-core p-5 flex flex-col justify-between h-full space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-cyan-400">
                      {m.parameter_size || 'LOCAL LLM'}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/[0.06] text-gray-300 font-mono ring-1 ring-white/10">
                      {m.quantization || 'Q4_K_M'}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-gray-100 mt-2 font-mono">
                    {m.name}
                  </h3>

                  <div className="mt-3 space-y-1.5 text-xs font-mono text-gray-400">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Context Limit:</span>
                      <span className="text-gray-300">{m.context_window_default || 2048} tokens</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Storage Footprint:</span>
                      <span className="text-gray-300">{sizeGb} GB</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Hardware Residency:</span>
                      <span className={isLarge ? 'text-cyber-amber' : 'text-cyber-emerald'}>
                        {isLarge ? 'Spills ~3.5GB to RAM' : 'Fully In VRAM'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-white/[0.04] flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-[11px] font-mono text-cyber-emerald">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyber-emerald animate-pulse" />
                    READY
                  </span>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => {
                        onSelectModel(m.id);
                        onNavigateTab('security');
                      }}
                      className="island-btn bg-white/[0.06] hover:bg-white/[0.12] text-white text-xs group"
                    >
                      <span>Audit</span>
                      <span className="btn-badge-icon">
                        <svg className="w-3.5 h-3.5 text-cyber-rose" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
                        </svg>
                      </span>
                    </button>
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
