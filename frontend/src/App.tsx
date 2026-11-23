import React, { useState, useEffect } from 'react';
import { api } from './api/client';
import { Telemetry, Model, BenchmarkReport, EvaluationRun, SecurityReport, RAGReport, Dataset } from './types';
import { Navbar } from './components/layout/Navbar';
import { Sidebar, TabType } from './components/layout/Sidebar';
import { TelemetryGauges } from './components/monitoring/TelemetryGauges';
import { OverviewTab } from './components/overview/OverviewTab';
import { ModelsTab } from './components/models/ModelsTab';
import { BenchmarksTab } from './components/benchmarks/BenchmarksTab';
import { SecurityTab } from './components/security/SecurityTab';
import { EvaluationsTab } from './components/evaluations/EvaluationsTab';
import { RagTab } from './components/rag/RagTab';
import { AnalyticsTab } from './components/analytics/AnalyticsTab';
import { SettingsTab } from './components/settings/SettingsTab';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [models, setModels] = useState<Model[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkReport[]>([]);
  const [evaluations, setEvaluations] = useState<EvaluationRun[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [rankings, setRankings] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [securityReport, setSecurityReport] = useState<SecurityReport | null>(null);
  const [ragReport, setRagReport] = useState<RAGReport | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('llama3.2:latest');
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Polling telemetry & status every 3 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [telData, healthData, modelsData, benchData, evalData, rankData, datasetsData] =
          await Promise.allSettled([
            api.getTelemetry(),
            api.getHealth(),
            api.getModels(),
            api.getBenchmarks(),
            api.getEvaluations(),
            api.getRankings(),
            api.getDatasets(),
          ]);

        if (telData.status === 'fulfilled') setTelemetry(telData.value);
        if (healthData.status === 'fulfilled') setHealth(healthData.value);
        if (modelsData.status === 'fulfilled') {
          setModels(modelsData.value);
          if (modelsData.value.length > 0 && !selectedModel) {
            setSelectedModel(modelsData.value[0].id);
          }
        }
        if (benchData.status === 'fulfilled') setBenchmarks(benchData.value);
        if (evalData.status === 'fulfilled') setEvaluations(evalData.value);
        if (rankData.status === 'fulfilled') setRankings(rankData.value);
        if (datasetsData.status === 'fulfilled') setDatasets(datasetsData.value);
      } catch (err) {
        console.error('Telemetry polling exception:', err);
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
      showToast('Ollama models synchronized successfully.');
    } catch (err: any) {
      showToast(`Sync failed: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSecurityScan = async (engine: 'promptfoo' | 'direct') => {
    setLoading(true);
    try {
      const rep = await api.scanSecurity({
        model_id: selectedModel,
        engine: engine,
      });
      setSecurityReport(rep);
      showToast(`Security scan complete (${engine.toUpperCase()} engine). Defense rate: ${(rep.defense_rate * 100).toFixed(0)}%`);
    } catch (err: any) {
      showToast(`Security scan error: ${err.message || err}`);
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
        document_content:
          'LocalLLM Guard is an enterprise-grade AI evaluation platform designed for workstation environments. It features single-model sequential queue execution, SQLite WAL mode, and Promptfoo subprocess orchestration over IPv4 127.0.0.1.',
        queries: [
          'What database mode does LocalLLM Guard use?',
          'How does the platform prevent multi-model VRAM memory collisions?',
        ],
      });
      setRagReport(rep);
      showToast('RAG Triad evaluation complete.');
    } catch (err: any) {
      showToast(`RAG evaluation error: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitEvaluation = async (datasetId: string, modelId: string) => {
    setLoading(true);
    try {
      await api.submitEvaluation({
        dataset_id: datasetId,
        model_id: modelId,
      });
      const updatedEvals = await api.getEvaluations();
      setEvaluations(updatedEvals);
      showToast(`Evaluation enqueued for ${modelId}. Running sequentially.`);
    } catch (err: any) {
      showToast(`Evaluation enqueue failed: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#05070B] text-gray-100 overflow-hidden font-sans relative">
      {/* Ambient Glow Mesh (Zero layout impact, pure atmosphere) */}
      <div className="ambient-mesh" />

      {/* Toast Notification Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 doppelrand-shell animate-fade-up">
          <div className="doppelrand-core px-4 py-3 text-xs font-mono flex items-center space-x-2 text-cyan-300">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>{toastMessage}</span>
          </div>
        </div>
      )}

      {/* Left Navigation Sidebar */}
      <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} health={health} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden relative z-10">
        <Navbar
          activeTab={activeTab}
          models={models}
          selectedModel={selectedModel}
          onSelectModel={setSelectedModel}
          onSyncModels={handleSyncModels}
          loading={loading}
        />

        {/* Scrollable Viewport */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Always Visible Hardware Telemetry Gauges */}
          <TelemetryGauges telemetry={telemetry} />

          {/* Tab Views */}
          {activeTab === 'overview' && (
            <OverviewTab
              models={models}
              benchmarks={benchmarks}
              evaluations={evaluations}
              onNavigateTab={setActiveTab}
              onSelectModel={setSelectedModel}
            />
          )}

          {activeTab === 'models' && (
            <ModelsTab
              models={models}
              selectedModel={selectedModel}
              onSelectModel={setSelectedModel}
              onNavigateTab={setActiveTab}
            />
          )}

          {activeTab === 'evaluations' && (
            <EvaluationsTab
              evaluations={evaluations}
              datasets={datasets}
              selectedModel={selectedModel}
              onSubmitEval={handleSubmitEvaluation}
              loading={loading}
            />
          )}

          {activeTab === 'benchmarks' && (
            <BenchmarksTab
              benchmarks={benchmarks}
              selectedModel={selectedModel}
              onNavigateTab={setActiveTab}
              datasets={datasets}
              models={models}
              onSelectModel={setSelectedModel}
              loading={loading}
            />
          )}

          {activeTab === 'security' && (
            <SecurityTab
              securityReport={securityReport}
              selectedModel={selectedModel}
              onRunScan={handleRunSecurityScan}
              loading={loading}
            />
          )}

          {activeTab === 'rag' && (
            <RagTab
              ragReport={ragReport}
              selectedModel={selectedModel}
              onRunRag={handleRunRAGTriad}
              loading={loading}
            />
          )}

          {activeTab === 'analytics' && (
            <AnalyticsTab rankings={rankings} selectedModel={selectedModel} />
          )}

          {activeTab === 'settings' && <SettingsTab />}
        </main>
      </div>
    </div>
  );
};
