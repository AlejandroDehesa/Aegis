import { EmptyState } from "./EmptyState";
import { formatDateTime, formatDuration } from "../utils/formatters";
import { StatusBadge } from "./StatusBadge";
import { useI18n } from "../hooks/useI18n";

export function TaskTraceList({ trace }) {
  const { t, locale } = useI18n();

  if (!trace?.length) {
    return (
      <EmptyState
        title={t("trace.emptyTitle")}
        description={t("trace.emptyDescription")}
      />
    );
  }

  return (
    <div className="trace-list">
      {trace.map((step, index) => (
        <article className="trace-item" key={`${step.step_index || index}-${step.agent_name}`}>
          <div className="trace-item-header">
            <div>
              <p className="trace-step-label">
                {t("trace.step", {
                  index: step.step_index || step.step_number || index + 1,
                })}
              </p>
              <h3>{step.agent_name}</h3>
              <p className="trace-step-meta">{step.step_name}</p>
            </div>
            <StatusBadge status={step.status} />
          </div>

          <dl className="trace-grid">
            <div>
              <dt>{t("trace.summary")}</dt>
              <dd className="trace-item-summary">
                {step.short_summary || step.result_preview || t("trace.noSummary")}
              </dd>
            </div>
            <div>
              <dt>{t("trace.duration")}</dt>
              <dd>{formatDuration(step.duration_ms, t("common.notAvailable"))}</dd>
            </div>
            <div>
              <dt>{t("trace.started")}</dt>
              <dd>{formatDateTime(step.started_at, locale, t("common.notAvailable"))}</dd>
            </div>
            <div>
              <dt>{t("trace.finished")}</dt>
              <dd>{formatDateTime(step.finished_at, locale, t("common.notAvailable"))}</dd>
            </div>
            {step.llm_provider ? (
              <div>
                <dt>LLM</dt>
                <dd>
                  {step.llm_provider}
                  {step.llm_model ? ` / ${step.llm_model}` : ""}
                </dd>
              </div>
            ) : null}
            {typeof step.llm_total_tokens === "number" ? (
              <div>
                <dt>LLM tokens</dt>
                <dd>
                  total={step.llm_total_tokens}
                  {typeof step.llm_prompt_tokens === "number" ? `, prompt=${step.llm_prompt_tokens}` : ""}
                  {typeof step.llm_completion_tokens === "number"
                    ? `, completion=${step.llm_completion_tokens}`
                    : ""}
                  {typeof step.llm_fallback_used === "boolean"
                    ? `, fallback=${step.llm_fallback_used ? "yes" : "no"}`
                    : ""}
                </dd>
              </div>
            ) : null}
            {step.rag_enabled !== null && step.rag_enabled !== undefined ? (
              <div>
                <dt>RAG</dt>
                <dd>
                  backend={step.rag_vector_backend || "n/a"}
                  {typeof step.rag_retrieved_chunks_count === "number"
                    ? `, chunks=${step.rag_retrieved_chunks_count}`
                    : ""}
                </dd>
              </div>
            ) : null}
            {Array.isArray(step.rag_documents_used) && step.rag_documents_used.length ? (
              <div>
                <dt>RAG documents</dt>
                <dd>{step.rag_documents_used.join(", ")}</dd>
              </div>
            ) : null}
          </dl>

          {Array.isArray(step.rag_snippets) && step.rag_snippets.length ? (
            <div className="content-block">
              <h3>RAG snippets</h3>
              <ul>
                {step.rag_snippets.map((snippet, snippetIndex) => (
                  <li key={`${step.agent_name}-${snippetIndex}`}>
                    {snippet}
                    {Array.isArray(step.rag_scores) && typeof step.rag_scores[snippetIndex] === "number"
                      ? ` (score: ${step.rag_scores[snippetIndex].toFixed(2)})`
                      : ""}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {step.error_message ? (
            <p className="trace-error">{t("taskDetail.errorPrefix", { message: step.error_message })}</p>
          ) : null}
        </article>
      ))}
    </div>
  );
}
