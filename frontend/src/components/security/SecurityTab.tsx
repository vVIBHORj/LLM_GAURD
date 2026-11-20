import React, { useState } from 'react';
import { SecurityReport } from '../../types';

interface SecurityTabProps {
  securityReport: SecurityReport | null;
  selectedModel: string;
  onRunScan: (engine: 'promptfoo' | 'direct') => void;
  loading: boolean;
}

export const SecurityTab: React.FC<SecurityTabProps> = ({
  securityReport,
  selectedModel,
  onRunScan,
  loading,
}) => {
  const [engine, setEngine] = useState<'promptfoo' | 'direct'>('promptfoo');
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const toggleExpand = (idx: number) => {
    setExpandedIndex(expandedIndex === idx ? null : idx);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Control Panel with Engine Selection & Trigger */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6 relative overflow-hidden">
          {loading && <div className="radar-scan-line" />}

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono text-cyber-rose">
                <span className="w-2 h-2 rounded-full bg-cyber-rose animate-pulse" />
                <span className="font-semibold uppercase tracking-wider">
                  Adversarial Red-Teaming Scanner
                </span>
              </div>
              <h2 className="text-lg font-bold text-gray-100 mt-1">
                Security Evaluation & Injection Defense for <span className="font-mono text-cyan-400">{selectedModel}</span>
              </h2>
              <p className="text-xs text-gray-400 mt-1 max-w-2xl leading-relaxed">
                Evaluates prompt injection vulnerability, DAN roleplay bypasses, PII leakage, and instruction hierarchy compliance using dual evaluation engines.
              </p>
            </div>

            {/* Engine Selector & Action */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              {/* Engine Toggle */}
              <div className="p-1 rounded-full bg-oled-950/80 ring-1 ring-white/10 flex text-xs font-mono">
                <button
                  type="button"
                  onClick={() => setEngine('promptfoo')}
                  className={`px-3 py-1.5 rounded-full transition-all duration-300 ${
                    engine === 'promptfoo'
                      ? 'bg-cyber-cyan/20 text-cyber-cyan ring-1 ring-cyber-cyan/40 font-semibold'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  Promptfoo Rigorous
                </button>
                <button
                  type="button"
                  onClick={() => setEngine('direct')}
                  className={`px-3 py-1.5 rounded-full transition-all duration-300 ${
                    engine === 'direct'
                      ? 'bg-blue-600/30 text-blue-300 ring-1 ring-blue-500/40 font-semibold'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  Direct Reasoning Probe
                </button>
              </div>

              {/* Primary Scan Button (Button-in-Button Pattern) */}
              <button
                type="button"
                onClick={() => onRunScan(engine)}
                disabled={loading}
                className="island-btn bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white disabled:opacity-50 group font-bold shadow-glow-rose"
              >
                <span>{loading ? 'Running Security Scan...' : 'Run Security Scan'}</span>
                <span className="btn-badge-icon bg-white/20">
                  <svg
                    className={`w-3.5 h-3.5 text-white ${loading ? 'animate-spin' : 'group-hover:scale-110 transition-transform'}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z" />
                  </svg>
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Security Report Results */}
      {securityReport ? (
        <div className="space-y-6 animate-fade-up">
          {/* Top Scorecard Summary */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="doppelrand-shell">
              <div className="doppelrand-core p-4">
                <div className="text-[11px] font-mono text-gray-500">TARGET MODEL</div>
                <div className="text-base font-bold text-white font-mono mt-1 truncate">
                  {securityReport.model_id}
                </div>
                <div className="text-[11px] text-cyan-400 font-mono mt-1">
                  Engine: {securityReport.engine_used?.toUpperCase() || 'PROMPTFOO'}
                </div>
              </div>
            </div>

            <div className="doppelrand-shell">
              <div className="doppelrand-core p-4">
                <div className="text-[11px] font-mono text-gray-500">DEFENSE RATE</div>
                <div className={`text-2xl font-bold font-mono mt-1 ${
                  securityReport.defense_rate >= 0.8
                    ? 'text-cyber-emerald'
                    : securityReport.defense_rate >= 0.5
                    ? 'text-cyber-amber'
                    : 'text-cyber-rose'
                }`}>
                  {(securityReport.defense_rate * 100).toFixed(0)}%
                </div>
                <div className="text-[11px] text-gray-400 font-mono mt-1">
                  {securityReport.defended_attacks} of {securityReport.total_attacks} Defended
                </div>
              </div>
            </div>

            <div className="doppelrand-shell">
              <div className="doppelrand-core p-4">
                <div className="text-[11px] font-mono text-gray-500">OVERALL RISK LEVEL</div>
                <div className={`text-2xl font-bold font-mono mt-1 ${
                  securityReport.risk_level === 'LOW'
                    ? 'text-cyber-emerald'
                    : securityReport.risk_level === 'MEDIUM'
                    ? 'text-cyber-amber'
                    : 'text-cyber-rose'
                }`}>
                  {securityReport.risk_level}
                </div>
                <div className="text-[11px] text-gray-400 font-mono mt-1">
                  Automated Scorecard
                </div>
              </div>
            </div>

            <div className="doppelrand-shell">
              <div className="doppelrand-core p-4">
                <div className="text-[11px] font-mono text-gray-500">EVALUATION TIME</div>
                <div className="text-base font-bold text-gray-200 font-mono mt-1">
                  {new Date(securityReport.generated_at).toLocaleTimeString()}
                </div>
                <div className="text-[11px] text-cyber-emerald font-mono mt-1">
                  ● Air-Gapped Test
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Attack Vectors List */}
          <div className="doppelrand-shell">
            <div className="doppelrand-core p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
                <h3 className="text-sm font-bold text-gray-100">
                  Adversarial Test Vectors Breakdown ({securityReport.attack_details.length} Probes)
                </h3>
                <span className="text-[11px] font-mono text-gray-500">
                  Click any probe to inspect reasoning trace &lt;think&gt;
                </span>
              </div>

              <div className="space-y-3">
                {securityReport.attack_details.map((atk, idx) => {
                  const isExpanded = expandedIndex === idx;

                  const categoryColors: Record<string, string> = {
                    injection: 'text-blue-400 bg-blue-500/10 ring-blue-500/30',
                    jailbreak: 'text-rose-400 bg-rose-500/10 ring-rose-500/30',
                    leakage: 'text-amber-400 bg-amber-500/10 ring-amber-500/30',
                    hierarchy: 'text-purple-400 bg-purple-500/10 ring-purple-500/30',
                    command: 'text-red-400 bg-red-500/10 ring-red-500/30',
                  };

                  return (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-oled-950/70 border border-white/[0.06] hover:border-white/[0.12] transition-all duration-300"
                    >
                      <div
                        className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 cursor-pointer"
                        onClick={() => toggleExpand(idx)}
                      >
                        <div className="flex items-center space-x-2.5">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase ring-1 font-semibold ${
                              categoryColors[atk.category.toLowerCase()] || 'text-gray-400 bg-white/5 ring-white/10'
                            }`}
                          >
                            {atk.category}
                          </span>
                          <span className="text-xs font-bold text-gray-200 font-mono">
                            {atk.attack_vector}
                          </span>
                        </div>

                        <div className="flex items-center space-x-3">
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold ring-1 ${
                              atk.defended
                                ? 'text-cyber-emerald bg-cyber-emerald/10 ring-cyber-emerald/30'
                                : 'text-cyber-rose bg-cyber-rose/10 ring-cyber-rose/30 shadow-glow-rose'
                            }`}
                          >
                            {atk.defended ? '● DEFENDED' : '■ VULNERABLE'}
                          </span>
                          <span className="text-gray-500 text-xs">
                            {isExpanded ? '▲' : '▼'}
                          </span>
                        </div>
                      </div>

                      {/* Prompt */}
                      <div className="mt-2.5 text-xs font-mono text-gray-400">
                        <span className="text-gray-500">Vector: </span>
                        <span className="text-gray-300">"{atk.prompt}"</span>
                      </div>

                      {/* Model Response Preview */}
                      <div className="mt-2 p-2.5 rounded-lg bg-oled-900/90 border border-white/[0.04] text-xs font-mono text-gray-200">
                        <span className="text-gray-500">Response: </span>
                        <span className={atk.defended ? 'text-gray-300' : 'text-rose-300 font-semibold'}>
                          "{atk.model_response || '[Empty Response]'}"
                        </span>
                      </div>

                      {/* Expandable Reasoning Trace Inspector */}
                      {isExpanded && (
                        <div className="mt-3 p-3 rounded-lg bg-oled-900 border border-white/[0.08] text-xs font-mono space-y-2 animate-fade-in">
                          <div className="flex justify-between items-center text-[11px] text-gray-400 border-b border-white/[0.04] pb-1.5">
                            <span className="text-cyan-400 font-semibold">
                              Internal Deliberation / Reasoning Chain (&lt;think&gt;)
                            </span>
                            <span className="text-gray-500">Risk Assessment: {atk.risk_level}</span>
                          </div>
                          <div className="text-gray-400 text-[11px] leading-relaxed max-h-40 overflow-y-auto">
                            {atk.thinking_preview ? (
                              <p className="whitespace-pre-wrap">{atk.thinking_preview}</p>
                            ) : (
                              <p className="italic text-gray-500">
                                No separate thinking trace captured (model generated response directly).
                              </p>
                            )}
                          </div>
                          <div className="text-[11px] text-gray-500 pt-1 border-t border-white/[0.04]">
                            Verdict Reason: <span className="text-gray-300">{atk.reason}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="doppelrand-shell text-center py-16">
          <div className="doppelrand-core p-12 space-y-3">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-white/[0.04] border border-white/10 flex items-center justify-center text-2xl">
              🛡️
            </div>
            <h3 className="text-sm font-bold text-gray-200">No Security Scan Executed</h3>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              Select an engine above and click "Run Security Scan" to test {selectedModel} against 12+ prompt injection and jailbreak attack vectors.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
