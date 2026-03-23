import { EmptyState } from "./EmptyState";
import { formatDateTime, formatDuration } from "../utils/formatters";
import { StatusBadge } from "./StatusBadge";

export function TaskTraceList({ trace }) {
  if (!trace?.length) {
    return (
      <EmptyState
        title="No execution trace yet"
        description="Run the task to capture step-by-step visibility for the orchestration pipeline."
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
                Step {step.step_index || step.step_number || index + 1}
              </p>
              <h3>{step.agent_name}</h3>
              <p className="trace-step-meta">{step.step_name}</p>
            </div>
            <StatusBadge status={step.status} />
          </div>

          <dl className="trace-grid">
            <div>
              <dt>Summary</dt>
              <dd className="trace-item-summary">
                {step.short_summary || step.result_preview || "No summary available"}
              </dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{formatDuration(step.duration_ms)}</dd>
            </div>
            <div>
              <dt>Started</dt>
              <dd>{formatDateTime(step.started_at)}</dd>
            </div>
            <div>
              <dt>Finished</dt>
              <dd>{formatDateTime(step.finished_at)}</dd>
            </div>
          </dl>

          {step.error_message ? (
            <p className="trace-error">Error: {step.error_message}</p>
          ) : null}
        </article>
      ))}
    </div>
  );
}
