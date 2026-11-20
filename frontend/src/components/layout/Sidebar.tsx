import React from 'react';

export type TabType = 'overview' | 'models' | 'evaluations' | 'benchmarks' | 'security' | 'rag' | 'analytics' | 'settings';

interface SidebarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  health: any;
}

const NAV_ITEMS: { id: TabType; label: string; icon: string; category?: string }[] = [
  { id: 'overview', label: 'Command Center', icon: '⚡' },
  { id: 'models', label: 'Model Registry', icon: '📦' },
  { id: 'evaluations', label: 'Promptfoo Evals', icon: '🧪' },
  { id: 'benchmarks', label: 'Pareto Frontier', icon: '📈' },
  { id: 'security', label: 'Adversarial Red-Team', icon: '🛡️' },
  { id: 'rag', label: 'RAG Triad Reliability', icon: '🧠' },
  { id: 'analytics', label: 'Leaderboard & Recs', icon: '🏆' },
  { id: 'settings', label: 'Hardware Spec', icon: '⚙️' },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab, health }) => {
  return (
    <aside className="w-64 bg-oled-950/90 border-r border-white/[0.06] flex flex-col justify-between backdrop-blur-xl z-20">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-white/[0.06] flex items-center space-x-3.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 via-cyan-500 to-emerald-400 p-0.5 shadow-glow-cyan">
            <div className="w-full h-full bg-oled-950 rounded-[10px] flex items-center justify-center font-extrabold text-xs tracking-wider text-cyan-300">
              LG
            </div>
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight text-gray-100 flex items-center gap-1.5">
              LocalLLM Guard
            </h1>
            <p className="text-[10px] text-gray-500 font-mono tracking-tight">
              Local-First AI Testing
            </p>
          </div>
        </div>

        {/* Navigation Item List */}
        <nav className="p-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all duration-300 ease-spring-fluid ${
                  isActive
                    ? 'bg-white/[0.08] text-white shadow-bezel-inner ring-1 ring-white/10 font-semibold'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/[0.03]'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <span className="text-sm opacity-90">{item.icon}</span>
                  <span className="tracking-tight">{item.label}</span>
                </div>
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#06B6D4]" />
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Runtime Hardware & Engine Status */}
      <div className="p-4 border-t border-white/[0.06] bg-oled-900/40">
        <div className="space-y-2 text-[11px] font-mono">
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Ollama API (IPv4)</span>
            <span className="text-cyber-emerald flex items-center gap-1.5 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-cyber-emerald animate-pulse" />
              {health?.ollama?.status === 'ONLINE' ? '127.0.0.1:11434' : (health?.ollama?.status || 'ONLINE')}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-500">Promptfoo CLI</span>
            <span className="text-cyber-cyan flex items-center gap-1.5 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-cyber-cyan" />
              v{health?.promptfoo?.version || '0.126.0'}
            </span>
          </div>
          <div className="flex items-center justify-between text-gray-500 pt-1 border-t border-white/[0.04]">
            <span>Acceleration</span>
            <span className="text-gray-400">RTX 3050 (4GB)</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
