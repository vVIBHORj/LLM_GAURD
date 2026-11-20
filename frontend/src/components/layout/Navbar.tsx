import React from 'react';
import { Model } from '../../types';

interface NavbarProps {
  activeTab: string;
  models: Model[];
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
  onSyncModels: () => void;
  loading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  models,
  selectedModel,
  onSelectModel,
  onSyncModels,
  loading,
}) => {
  return (
    <header className="h-16 px-6 border-b border-white/[0.06] bg-oled-900/60 backdrop-blur-xl flex items-center justify-between z-10">
      {/* Current Section Indicator */}
      <div className="flex items-center space-x-3">
        <span className="text-[11px] font-mono uppercase tracking-widest text-gray-500">
          SURFACE //
        </span>
        <h2 className="text-sm font-semibold capitalize tracking-tight text-gray-100 flex items-center gap-2">
          {activeTab}
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
        </h2>
      </div>

      {/* Target Model Selector & Action Button */}
      <div className="flex items-center space-x-4">
        {/* Model Selector Island */}
        <div className="flex items-center bg-oled-950/70 ring-1 ring-white/10 rounded-full pl-3 pr-1 py-1 text-xs font-mono">
          <span className="text-[10px] tracking-wider text-gray-500 mr-2 uppercase">TARGET:</span>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            className="bg-transparent text-gray-200 text-xs font-mono font-medium focus:outline-none cursor-pointer pr-2"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id} className="bg-oled-900 text-gray-200">
                {m.name} {m.parameter_size ? `(${m.parameter_size})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Sync Island Button ("Button-in-Button" Pattern) */}
        <button
          onClick={onSyncModels}
          disabled={loading}
          className="island-btn bg-white/5 hover:bg-white/10 text-gray-200 disabled:opacity-50 group"
          title="Synchronize installed Ollama models"
        >
          <span>{loading ? 'Syncing...' : 'Sync Ollama'}</span>
          <span className="btn-badge-icon">
            <svg
              className={`w-3.5 h-3.5 text-cyan-400 ${loading ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </span>
        </button>
      </div>
    </header>
  );
};
