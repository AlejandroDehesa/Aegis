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
          </dl>

          {step.error_message ? (
            <p className="trace-error">{t("taskDetail.errorPrefix", { message: step.error_message })}</p>
          ) : null}
        </article>
      ))}
    </div>
  );
}
