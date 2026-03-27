import { useI18n } from "../hooks/useI18n";

export function RagDebugPanel({ debug }) {
  const { t } = useI18n();

  if (!debug) {
    return null;
  }

  return (
    <div className="debug-panel">
      <div className="debug-metrics">
        <div>
          <span className="metric-label">{t("debug.topK")}</span>
          <strong>{debug.top_k}</strong>
        </div>
        <div>
          <span className="metric-label">{t("debug.minScore")}</span>
          <strong>{debug.min_score}</strong>
        </div>
        <div>
          <span className="metric-label">{t("debug.memoryTasks")}</span>
          <strong>{debug.memory_task_count}</strong>
        </div>
      </div>

      <div className="debug-blocks">
        <DebugBlock title={t("debug.ragContext")} text={debug.context_preview} />
        <DebugBlock title={t("debug.memoryContext")} text={debug.memory_context_preview} />
        <DebugBlock title={t("debug.fullContext")} text={debug.full_context_preview} />
      </div>

      {debug.retrieval_error ? (
        <p className="trace-error">{t("debug.retrievalError", { message: debug.retrieval_error })}</p>
      ) : null}
    </div>
  );
}

function DebugBlock({ title, text }) {
  const { t } = useI18n();

  return (
    <div className="debug-block">
      <p className="section-eyebrow">{title}</p>
      <pre>{text || t("debug.noData")}</pre>
    </div>
  );
}
