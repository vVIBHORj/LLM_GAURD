import React from 'react';
import { RAGReport } from '../../types';

interface RagTabProps {
  ragReport: RAGReport | null;
  selectedModel: string;
  onRunRag: () => void;
  loading: boolean;
}

export const RagTab: React.FC<RagTabProps> = ({
  ragReport,
  selectedModel,
  onRunRag,
  loading,
}) => {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Control Panel */}
      <div className="doppelrand-shell">
        <div className="doppelrand-core p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span className="font-semibold uppercase tracking-wider">
                  RAG Triad Reliability Evaluator
                </span>
              </div>
              <h2 className="text-lg font-bold text-gray-100 mt-1">
                Context Relevance & Answer Groundedness
              </h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Evaluates retrieval accuracy and hallucination defense using local embeddings (<code className="text-cyan-400 font-mono">qwen3-embedding:0.6b</code>) and generation.
              </p>
            </div>

            <button
              onClick={onRunRag}
              disabled={loading}
              className="island-btn bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-50 group font-bold shadow-glow-cyan"
            >
              <span>{loading ? 'Evaluating Triad...' : 'Run RAG Triad Evaluation'}</span>
              <span className="btn-badge-icon bg-white/20">
                <svg className="w-3.5 h-3.5 text-white group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* RAG Report Results */}
      {ragReport ? (
        <div className="space-y-6 animate-fade-up">
          {/* Triad Metric Gauges */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            <div className="doppelrand-shell">
              <div className="doppelrand-core p-4">
                <div className="text-[11px] font-mono text-gray-500">CONTEXT RELEVANCE</div>
                <div className="text-2xl font-bold text-cyan-400 font-mono mt-1">
                  {(ragReport.avg_context_relevance * 100).toFixed(0)}%
                </div>
                <div className="text-[11px] text-gray-400 font-mono mt-1">
                  Query ↔ Context Cosine Match
                </div>
              </div>
            </div>

            <div className="doppelrand-shell">
              <div className="doppelrand-core p-4">
                <div className="text-[11px] font-mono text-gray-500">ANSWER FAITHFULNESS</div>
                <div className="text-2xl font-bold text-emerald-400 font-mono mt-1">
                  {(ragReport.avg_faithfulness * 100).toFixed(0)}%
                </div>
                <div className="text-[11px] text-gray-400 font-mono mt-1">
                  Grounded in Retrieved Context
                </div>
              </div>
            </div>

            <div className="doppelrand-shell">
              <div className="doppelrand-core p-4">
                <div className="text-[11px] font-mono text-gray-500">ANSWER RELEVANCE</div>
                <div className="text-2xl font-bold text-purple-400 font-mono mt-1">
                  {(ragReport.avg_answer_relevance * 100).toFixed(0)}%
                </div>
                <div className="text-[11px] text-gray-400 font-mono mt-1">
                  Direct Response to User Intent
                </div>
              </div>
            </div>

            <div className="doppelrand-shell">
              <div className="doppelrand-core p-4">
                <div className="text-[11px] font-mono text-gray-500">TRIAD COMPOSITE SCORE</div>
                <div className="text-2xl font-bold text-white font-mono mt-1">
                  {(ragReport.rag_triad_score * 100).toFixed(0)}%
                </div>
                <div className="text-[11px] text-cyan-400 font-mono mt-1">
                  Harmonic Reliability Mean
                </div>
              </div>
            </div>
          </div>

          {/* Query Breakdown */}
          <div className="doppelrand-shell">
            <div className="doppelrand-core p-6 space-y-4">
              <h3 className="text-sm font-bold text-gray-100 border-b border-white/[0.06] pb-3">
                Evaluated Retrieval & Generation Breakdown
              </h3>

              <div className="space-y-3">
                {ragReport.query_evaluations.map((q, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-oled-950/70 border border-white/[0.06] text-xs font-mono space-y-2"
                  >
                    <div className="flex justify-between items-center text-gray-200 font-bold">
                      <span>Query #{idx + 1}: "{q.query}"</span>
                      <div className="flex space-x-3 text-[11px]">
                        <span className="text-cyan-400">Relevance: {(q.context_relevance * 100).toFixed(0)}%</span>
                        <span className="text-emerald-400">Faithfulness: {(q.faithfulness * 100).toFixed(0)}%</span>
                      </div>
                    </div>

                    <div className="text-gray-400 bg-oled-900/60 p-2.5 rounded-lg border border-white/[0.04]">
                      <span className="text-gray-500">Retrieved Context: </span>
                      {q.retrieved_chunk}
                    </div>

                    <div className="text-gray-200 bg-oled-900/90 p-2.5 rounded-lg border border-white/[0.06]">
                      <span className="text-cyan-400">Generated Answer: </span>
                      "{q.generated_answer}"
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="doppelrand-shell text-center py-16">
          <div className="doppelrand-core p-12 space-y-3">
            <div className="w-12 h-12 mx-auto rounded-2xl bg-white/[0.04] border border-white/10 flex items-center justify-center text-2xl">
              🧠
            </div>
            <h3 className="text-sm font-bold text-gray-200">No RAG Evaluation Performed</h3>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              Click "Run RAG Triad Evaluation" to test {selectedModel} on context relevance, hallucination resistance, and answer faithfulness.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
