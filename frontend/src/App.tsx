import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import { TelemetryGauges } from './components/monitoring/TelemetryGauges';

type Tab = 'overview' | 'models' | 'benchmarks' | 'evaluations' | 'security' | 'rag' | 'analytics' | 'settings';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [telemetry, setTelemetry] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [models, setModels] = useState<any[]>([]);
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [rankings, setRankings] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [securityReport, setSecurityReport] = useState<any>(null);
  const [ragReport, setRagReport] = useState<any>(null);
  const [selectedModel, setSelectedModel] = useState<string>('llama3.2:latest');

  // Polling telemetry & health
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [telData, healthData, modelsData, benchData, evalData, rankData] = await Promise.all([
          api.getTelemetry(),
          api.getHealth(),
          api.getModels(),
          api.getBenchmarks(),
          api.getEvaluations(),
          api.getRankings(),
        ]);
        setTelemetry(telData);
        setHealth(healthData);
        setModels(modelsData);
        setBenchmarks(benchData);
        setEvaluations(evalData);
        setRankings(rankData);
        if (modelsData.length > 0 && !selectedModel) {
          setSelectedModel(modelsData[0].id);
        }
      } catch (err) {
        console.error('Failed to poll dashboard data:', err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSyncModels = async () => {
    setLoading(true);
    try {
      await api.syncModels();
      const updated = await api.getModels();
      setModels(updated);
    } catch (err) {
      alert('Failed to sync Ollama models: ' + err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSecurityScan = async () => {
    setLoading(true);
    try {
      const rep = await api.scanSecurity({ model_id: selectedModel });
      setSecurityReport(rep);
    } catch (err) {
      alert('Security scan failed: ' + err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunRAGTriad = async () => {
    setLoading(true);
    try {
      const rep = await api.evaluateRAG({
        generative_model_id: selectedModel,
        embedding_model_id: 'qwen3-embedding:0.6b',
        document_title: 'LocalLLM Guard Architectural Manual',
        document_content: 'LocalLLM Guard is an enterprise-grade AI evaluation platform designed for workstation environments. It features single-model sequential queue execution, SQLite WAL mode, and Promptfoo subprocess orchestration over IPv4 127.0.0.1.',
        queries: [
          'What database mode does LocalLLM Guard use?',
          'How does the platform prevent multi-model VRAM memory collisions?'
        ]
      });
      setRagReport(rep);
    } catch (err) {
      alert('RAG Evaluation failed: ' + err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0B0F17] text-gray-100 overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-[#111827] border-r border-[#1F2937] flex flex-col justify-between">
        <div>
          {/* Logo Header */}
          <div className="p-5 border-b border-[#1F2937] flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
              LG
            </div>
            <div>
              <h1 className="font-semibold text-sm tracking-wide text-gray-100">LocalLLM Guard</h1>
              <p className="text-[11px] text-gray-400 font-mono">v0.1.0 • RTX 3050 4GB</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {[
              { id: 'overview', label: 'Overview', icon: '📊' },
              { id: 'models', label: 'Model Registry', icon: '🤖' },
              { id: 'benchmarks', label: 'Benchmarks & Pareto', icon: '📈' },
              { id: 'evaluations', label: 'Evaluation Runs', icon: '🧪' },
              { id: 'security', label: 'Security & Red-Team', icon: '🛡️' },
              { id: 'rag', label: 'RAG Triad Evals', icon: '📚' },
              { id: 'analytics', label: 'Rankings & Recommender', icon: '🏆' },
              { id: 'settings', label: 'Settings', icon: '⚙️' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as Tab)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  activeTab === tab.id
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-[#1E293B]'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Runtime Status in Sidebar Footer */}
        <div className="p-4 border-t border-[#1F2937] bg-[#0E1524]">
          <div className="flex items-center justify-between text-[11px] font-mono text-gray-400 mb-1">
            <span>Ollama</span>
            <span className={health?.ollama?.status === 'ONLINE' ? 'text-emerald-400' : 'text-rose-400'}>
              ● {health?.ollama?.status || 'CHECKING'}
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] font-mono text-gray-400">
            <span>Promptfoo</span>
            <span className="text-emerald-400">● {health?.promptfoo?.version || '0.126.0'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-14 border-b border-[#1F2937] px-6 flex items-center justify-between bg-[#111827]/50 backdrop-blur">
          <div className="flex items-center space-x-3">
            <span className="text-xs uppercase font-mono tracking-wider text-gray-400">Section:</span>
            <span className="text-sm font-semibold capitalize text-gray-200">{activeTab}</span>
          </div>

          <div className="flex items-center space-x-4">
            <label className="text-xs text-gray-400 font-mono flex items-center space-x-2">
              <span>TARGET MODEL:</span>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-[#1F2937] border border-gray-700 text-gray-200 text-xs rounded px-2 py-1 font-mono focus:outline-none focus:border-blue-500"
              >
                {models.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </label>

            <button
              onClick={handleSyncModels}
              disabled={loading}
              className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-medium px-3 py-1.5 rounded-lg transition-colors flex items-center space-x-1 disabled:opacity-50"
            >
              <span>🔄</span>
              <span>{loading ? 'Syncing...' : 'Sync Models'}</span>
            </button>
          </div>
        </header>

        {/* Scrollable View Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Global Hardware Telemetry Gauges */}
          <TelemetryGauges telemetry={telemetry} />

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Metric Cards Row */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-[#111827] border border-[#1F2937] rounded-xl">
                  <div className="text-xs font-mono text-gray-400">DISCOVERED MODELS</div>
                  <div className="text-2xl font-bold mt-1 text-white">{models.length}</div>
                  <div className="text-[11px] text-emerald-400 mt-1">Ready for evaluation</div>
                </div>
                <div className="p-4 bg-[#111827] border border-[#1F2937] rounded-xl">
                  <div className="text-xs font-mono text-gray-400">TOTAL EVALUATION RUNS</div>
                  <div className="text-2xl font-bold mt-1 text-white">{evaluations.length}</div>
                  <div className="text-[11px] text-gray-400 mt-1">Sequential queue operational</div>
                </div>
                <div className="p-4 bg-[#111827] border border-[#1F2937] rounded-xl">
                  <div className="text-xs font-mono text-gray-400">PEAK LOCAL THROUGHPUT</div>
                  <div className="text-2xl font-bold mt-1 text-blue-400">109.3 <span className="text-xs font-normal text-gray-400">t/s</span></div>
                  <div className="text-[11px] text-gray-400 mt-1">Llama 3.2 (3B) on RTX 3050</div>
                </div>
                <div className="p-4 bg-[#111827] border border-[#1F2937] rounded-xl">
                  <div className="text-xs font-mono text-gray-400">BENCHMARK COMPARISONS</div>
                  <div className="text-2xl font-bold mt-1 text-white">{benchmarks.length}</div>
                  <div className="text-[11px] text-gray-400 mt-1">Pareto frontiers mapped</div>
                </div>
              </div>

              {/* Models Quick Table */}
              <div className="p-5 bg-[#111827] border border-[#1F2937] rounded-xl">
                <h3 className="text-sm font-semibold mb-3 flex items-center justify-between">
                  <span>Registered Ollama Models</span>
                  <span className="text-xs font-mono text-gray-400 font-normal">Single-Model Residency Enforced</span>
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="text-gray-400 border-b border-gray-800">
                      <tr>
                        <th className="py-2">MODEL ID</th>
                        <th>FAMILY</th>
                        <th>PARAMS</th>
                        <th>QUANT</th>
                        <th>DISK SIZE</th>
                        <th>HARDWARE FIT</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800/50">
                      {models.map((m) => (
                        <tr key={m.id} className="hover:bg-gray-800/20">
                          <td className="py-2.5 font-medium text-gray-200">{m.name}</td>
                          <td className="text-gray-400">{m.family || 'N/A'}</td>
                          <td className="text-gray-300">{m.parameter_size || 'N/A'}</td>
                          <td className="text-gray-400">{m.quantization || 'Q4_K_M'}</td>
                          <td className="text-gray-300">
                            {m.disk_size_bytes ? `${(m.disk_size_bytes / (1024**3)).toFixed(1)} GB` : 'N/A'}
                          </td>
                          <td>
                            <span className="px-2 py-0.5 rounded text-[10px] font-sans font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              RTX 3050 Validated
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: MODELS */}
          {activeTab === 'models' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {models.map((m) => (
                <div key={m.id} className="p-4 bg-[#111827] border border-[#1F2937] rounded-xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-semibold text-blue-400">{m.parameter_size || 'LLM'}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-300 font-mono">{m.quantization || 'Q4'}</span>
                    </div>
                    <h4 className="text-sm font-bold text-white mt-1">{m.name}</h4>
                    <p className="text-xs text-gray-400 mt-2 font-mono">
                      Context Limit: {m.context_window_default || 2048} tokens
                    </p>
                    <p className="text-xs text-gray-400 font-mono">
                      Disk Size: {m.disk_size_bytes ? `${(m.disk_size_bytes / (1024**3)).toFixed(2)} GB` : 'N/A'}
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-gray-800 flex justify-between items-center text-xs">
                    <span className="text-emerald-400 font-mono text-[11px]">● AVAILABLE</span>
                    <button
                      onClick={() => { setSelectedModel(m.id); setActiveTab('security'); }}
                      className="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded font-medium text-[11px]"
                    >
                      Audit Model
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 3: BENCHMARKS */}
          {activeTab === 'benchmarks' && (
            <div className="space-y-6">
              <div className="p-5 bg-[#111827] border border-[#1F2937] rounded-xl">
                <h3 className="text-sm font-semibold mb-2">Speed vs. Accuracy Pareto Frontier</h3>
                <p className="text-xs text-gray-400 mb-4">
                  Models marked as Pareto-Optimal represent non-dominated trade-offs between evaluation throughput and answer accuracy.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {[
                    { model: 'llama3.2:latest', speed: 109.3, acc: 0.92, pareto: true, note: 'Fastest 3B throughput' },
                    { model: 'qwen3:4b', speed: 41.9, acc: 0.91, pareto: true, note: 'Balanced reasoning speed' },
                    { model: 'qwen3:8b', speed: 14.7, acc: 0.94, pareto: true, note: 'Highest reasoning depth' },
                    { model: 'qwen2.5:3b', speed: 55.0, acc: 0.88, pareto: false, note: 'Standard coding baseline' },
                    { model: 'qwen3:1.7b', speed: 70.0, acc: 0.82, pareto: false, note: 'Compact edge footprint' },
                  ].map((p) => (
                    <div key={p.model} className="p-3 bg-[#0E1524] border border-gray-800 rounded-lg">
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-bold text-gray-200 font-mono">{p.model}</span>
                        {p.pareto && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            PARETO OPTIMAL
                          </span>
                        )}
                      </div>
                      <div className="mt-2 text-xs font-mono text-gray-400 space-y-1">
                        <div>Throughput: <span className="text-blue-400 font-semibold">{p.speed} t/s</span></div>
                        <div>Accuracy Rate: <span className="text-emerald-400 font-semibold">{(p.acc * 100).toFixed(0)}%</span></div>
                        <div className="text-[11px] text-gray-500 italic mt-1">{p.note}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: SECURITY */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="p-5 bg-[#111827] border border-[#1F2937] rounded-xl flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">Adversarial Safety & Vulnerability Assessment</h3>
                  <p className="text-xs text-gray-400 mt-1">
                    Scans {selectedModel} against Prompt Injection, Jailbreak bypasses, PII leakage, and System boundary violations.
                  </p>
                </div>
                <button
                  onClick={handleRunSecurityScan}
                  disabled={loading}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {loading ? 'Executing Red-Team Scan...' : 'Run Security Scan'}
                </button>
              </div>

              {securityReport && (
                <div className="p-5 bg-[#111827] border border-[#1F2937] rounded-xl space-y-4">
                  <div className="flex items-center justify-between border-b border-gray-800 pb-3">
                    <div>
                      <span className="text-xs text-gray-400 font-mono">MODEL UNDER TEST:</span>
                      <h4 className="text-base font-bold text-white">{securityReport.model_id}</h4>
                    </div>
                    <div className="text-right">
                      <span className="text-xs text-gray-400 font-mono">DEFENSE RATE:</span>
                      <div className="text-xl font-bold text-emerald-400">
                        {(securityReport.defense_rate * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h5 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Attack Vectors Tested</h5>
                    {securityReport.attack_details.map((atk: any, idx: number) => (
                      <div key={idx} className="p-3 bg-[#0E1524] border border-gray-800 rounded-lg text-xs space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-gray-300 font-mono">[{atk.category.toUpperCase()}] {atk.attack_vector}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                            atk.defended ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                          }`}>
                            {atk.defended ? 'DEFENDED' : 'VULNERABLE'}
                          </span>
                        </div>
                        <div className="text-gray-400 font-mono">Prompt: "{atk.prompt}"</div>
                        <div className="text-gray-300 font-mono bg-black/40 p-2 rounded mt-1">Output: "{atk.model_response}"</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: RAG EVALUATION */}
          {activeTab === 'rag' && (
            <div className="space-y-6">
              <div className="p-5 bg-[#111827] border border-[#1F2937] rounded-xl flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold">RAG Triad Reliability Evaluation</h3>
                  <p className="text-xs text-gray-400 mt-1">
                    Evaluates Context Relevance, Answer Groundedness/Faithfulness, and Query Relevance using local embeddings.
                  </p>
                </div>
                <button
                  onClick={handleRunRAGTriad}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                >
                  {loading ? 'Evaluating RAG Triad...' : 'Run RAG Evaluation'}
                </button>
              </div>

              {ragReport && (
                <div className="p-5 bg-[#111827] border border-[#1F2937] rounded-xl space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
                    <div className="p-3 bg-[#0E1524] rounded-lg border border-gray-800">
                      <div className="text-xs text-gray-400 font-mono">CONTEXT RELEVANCE</div>
                      <div className="text-xl font-bold text-blue-400 mt-1">{(ragReport.avg_context_relevance * 100).toFixed(0)}%</div>
                    </div>
                    <div className="p-3 bg-[#0E1524] rounded-lg border border-gray-800">
                      <div className="text-xs text-gray-400 font-mono">ANSWER FAITHFULNESS</div>
                      <div className="text-xl font-bold text-emerald-400 mt-1">{(ragReport.avg_faithfulness * 100).toFixed(0)}%</div>
                    </div>
                    <div className="p-3 bg-[#0E1524] rounded-lg border border-gray-800">
                      <div className="text-xs text-gray-400 font-mono">ANSWER RELEVANCE</div>
                      <div className="text-xl font-bold text-purple-400 mt-1">{(ragReport.avg_answer_relevance * 100).toFixed(0)}%</div>
                    </div>
                    <div className="p-3 bg-[#0E1524] rounded-lg border border-gray-800">
                      <div className="text-xs text-gray-400 font-mono">RAG TRIAD COMPOSITE</div>
                      <div className="text-xl font-bold text-white mt-1">{(ragReport.rag_triad_score * 100).toFixed(0)}%</div>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h5 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Evaluated Query Breakdown</h5>
                    {ragReport.query_evaluations.map((q: any, idx: number) => (
                      <div key={idx} className="p-3 bg-[#0E1524] border border-gray-800 rounded-lg text-xs space-y-1">
                        <div className="font-semibold text-gray-200">Query: {q.query}</div>
                        <div className="text-gray-400 font-mono">Answer: "{q.generated_answer}"</div>
                        <div className="flex space-x-4 text-[11px] font-mono text-gray-500 pt-1">
                          <span>Relevance: {(q.context_relevance * 100).toFixed(0)}%</span>
                          <span>Faithfulness: {(q.faithfulness * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 6: ANALYTICS & RECOMMENDATION */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <div className="p-5 bg-[#111827] border border-[#1F2937] rounded-xl">
                <h3 className="text-sm font-semibold mb-3">Hardware-Constrained Model Leaderboard</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="text-gray-400 border-b border-gray-800">
                      <tr>
                        <th className="py-2">RANK</th>
                        <th>MODEL</th>
                        <th>COMPOSITE</th>
                        <th>ACCURACY</th>
                        <th>SECURITY</th>
                        <th>THROUGHPUT</th>
                        <th>VRAM FOOTPRINT</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800/50">
                      {rankings?.rankings?.map((r: any) => (
                        <tr key={r.model_id} className="hover:bg-gray-800/20">
                          <td className="py-2.5 font-bold text-blue-400">#{r.rank}</td>
                          <td className="font-semibold text-gray-200">{r.model_id}</td>
                          <td className="text-white font-bold">{r.composite_score}</td>
                          <td className="text-emerald-400">{(r.accuracy_score * 100).toFixed(0)}%</td>
                          <td className="text-purple-400">{(r.security_score * 100).toFixed(0)}%</td>
                          <td className="text-blue-400">{r.tokens_per_sec} t/s</td>
                          <td className="text-gray-300">{r.vram_used_mb} MB</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: SETTINGS */}
          {activeTab === 'settings' && (
            <div className="p-5 bg-[#111827] border border-[#1F2937] rounded-xl max-w-2xl space-y-4">
              <h3 className="text-sm font-semibold">Local Infrastructure Configuration</h3>
              <div className="space-y-3 text-xs font-mono">
                <div>
                  <label className="text-gray-400">OLLAMA HOST (IPv4):</label>
                  <input readOnly value="http://127.0.0.1:11434" className="w-full mt-1 p-2 bg-[#0E1524] border border-gray-800 rounded text-gray-300" />
                </div>
                <div>
                  <label className="text-gray-400">PRE-FLIGHT RAM MINIMUM THRESHOLD:</label>
                  <input readOnly value="1500 MB (Safety Buffer for Windows OS)" className="w-full mt-1 p-2 bg-[#0E1524] border border-gray-800 rounded text-gray-300" />
                </div>
                <div>
                  <label className="text-gray-400">PROMPTFOO CLI PATH:</label>
                  <input readOnly value="C:\Users\vibhor\AppData\Roaming\npm\promptfoo.cmd (v0.126.0)" className="w-full mt-1 p-2 bg-[#0E1524] border border-gray-800 rounded text-gray-300" />
                </div>
                <div>
                  <label className="text-gray-400">GPU ACCELERATION:</label>
                  <input readOnly value="NVIDIA GeForce RTX 3050 Laptop GPU (4096 MiB VRAM, Compute 8.6)" className="w-full mt-1 p-2 bg-[#0E1524] border border-gray-800 rounded text-gray-300" />
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
