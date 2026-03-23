export function RagDebugPanel({ debug }) {
  if (!debug) {
    return null;
  }

  return (
    <div className="debug-panel">
      <div className="debug-metrics">
        <div>
          <span className="metric-label">Top K</span>
          <strong>{debug.top_k}</strong>
        </div>
        <div>
          <span className="metric-label">Min score</span>
          <strong>{debug.min_score}</strong>
        </div>
        <div>
          <span className="metric-label">Memory tasks</span>
          <strong>{debug.memory_task_count}</strong>
        </div>
      </div>

      <div className="debug-blocks">
        <DebugBlock title="RAG Context" text={debug.context_preview} />
        <DebugBlock title="Memory Context" text={debug.memory_context_preview} />
        <DebugBlock title="Full Context" text={debug.full_context_preview} />
      </div>

      {debug.retrieval_error ? (
        <p className="trace-error">Retrieval error: {debug.retrieval_error}</p>
      ) : null}
    </div>
  );
}

function DebugBlock({ title, text }) {
  return (
    <div className="debug-block">
      <p className="section-eyebrow">{title}</p>
      <pre>{text || "No data available."}</pre>
    </div>
  );
}
