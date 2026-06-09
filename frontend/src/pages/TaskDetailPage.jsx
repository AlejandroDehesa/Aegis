import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { executeTask, getTask, getTaskTrace, submitTaskFeedback } from "../api/tasksApi";
import { AsyncContent } from "../components/AsyncContent";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { RagDebugPanel } from "../components/RagDebugPanel";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { TaskTraceList } from "../components/TaskTraceList";
import { ROUTES } from "../constants/routes";
import { useI18n } from "../hooks/useI18n";
import { usePolling } from "../hooks/usePolling";
import { getErrorMessage } from "../utils/errors";
import { formatDateTime, formatDuration, formatTaskTypeLabel } from "../utils/formatters";

function createFeedbackForm(task) {
  return {
    feedback_rating: task?.feedback_rating || 0,
    feedback_comment: task?.feedback_comment || "",
  };
}

export function TaskDetailPage() {
  const { t, language, locale } = useI18n();
  const { taskId } = useParams();
  const [task, setTask] = useState(null);
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [feedbackSaving, setFeedbackSaving] = useState(false);
  const [feedbackDirty, setFeedbackDirty] = useState(false);
  const [feedbackForm, setFeedbackForm] = useState(createFeedbackForm(null));
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [feedbackNotice, setFeedbackNotice] = useState("");

  useEffect(() => {
    setFeedbackDirty(false);
    setFeedbackForm(createFeedbackForm(null));
    void loadTaskDetail();
  }, [taskId]);

  usePolling(
    () => {
      void loadTaskDetail({ silent: true });
    },
    {
      enabled: Boolean(task && ["pending", "queued", "processing"].includes(task.status)),
      intervalMs: 2500,
    },
  );

  async function loadTaskDetail({ silent = false } = {}) {
    if (!silent) {
      setLoading(true);
      setLoadError("");
    }

    try {
      const [taskData, traceData] = await Promise.all([
        getTask(taskId),
        getTaskTrace(taskId),
      ]);
      setTask(taskData);
      setTrace(traceData);

      if (!feedbackDirty) {
        setFeedbackForm(createFeedbackForm(taskData));
      }

      if (!silent) {
        setLoadError("");
      }
    } catch (error) {
      const message = getErrorMessage(error, t("taskDetail.loading"));
      setLoadError(message);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }

  async function handleExecute() {
    setExecuting(true);
    setActionError("");
    setNotice("");

    try {
      const taskData = await executeTask(taskId, { debug: true });
      const traceData = await getTaskTrace(taskId);
      setTask(taskData);
      setTrace(traceData);

      if (!feedbackDirty) {
        setFeedbackForm(createFeedbackForm(taskData));
      }

      setNotice(
        ["queued", "processing"].includes(taskData.status)
          ? t("taskDetail.executeStarted")
          : t("taskDetail.executeCompleted"),
      );
    } catch (error) {
      setActionError(getErrorMessage(error, t("taskDetail.execute")));
    } finally {
      setExecuting(false);
    }
  }

  function updateFeedbackComment(event) {
    setFeedbackDirty(true);
    setFeedbackForm((current) => ({
      ...current,
      feedback_comment: event.target.value,
    }));
  }

  function updateFeedbackRating(value) {
    setFeedbackDirty(true);
    setFeedbackForm((current) => ({
      ...current,
      feedback_rating: value,
    }));
  }

  async function handleSubmitFeedback(event) {
    event.preventDefault();

    if (!feedbackForm.feedback_rating) {
      setActionError(t("taskDetail.missingRating"));
      return;
    }

    setFeedbackSaving(true);
    setActionError("");
    setFeedbackNotice("");

    try {
      const updatedTask = await submitTaskFeedback(taskId, {
        feedback_rating: feedbackForm.feedback_rating,
        feedback_comment: feedbackForm.feedback_comment,
      });

      setTask(updatedTask);
      setFeedbackForm(createFeedbackForm(updatedTask));
      setFeedbackDirty(false);
      setFeedbackNotice(t("taskDetail.feedbackSaved"));
    } catch (error) {
      setActionError(getErrorMessage(error, t("taskDetail.saveEvaluation")));
    } finally {
      setFeedbackSaving(false);
    }
  }

  if (!task) {
    return (
      <div className="page-grid">
        <AsyncContent
          loading={loading}
          error={loadError}
          isEmpty={!loading && !loadError}
          loadingText={t("taskDetail.loading")}
          emptyTitle={t("taskDetail.emptyTitle")}
          emptyDescription={t("taskDetail.emptyDescription")}
        >
          <div />
        </AsyncContent>
      </div>
    );
  }

  const canEvaluateTask = ["completed", "failed"].includes(task.status);

  return (
    <div className="page-grid">
      <header className="page-header page-header-inline">
        <div>
          <p className="eyebrow">{t("taskDetail.eyebrow")}</p>
          <h2>{task.title}</h2>
        </div>
        <div className="header-action-row">
          <Link className="button button-secondary" to={ROUTES.TASKS}>
            {t("taskDetail.backToTasks")}
          </Link>
          <button
            className="button button-primary"
            disabled={executing || ["queued", "processing"].includes(task.status)}
            onClick={handleExecute}
            type="button"
          >
            {executing
              ? t("taskDetail.executing")
              : ["queued", "processing"].includes(task.status)
                ? t("taskDetail.running")
                : t("taskDetail.execute")}
          </button>
        </div>
      </header>

      <FeedbackMessage tone="info">
        {["queued", "processing"].includes(task.status)
          ? t("taskDetail.runningNotice")
          : notice}
      </FeedbackMessage>
      <FeedbackMessage tone="success">{feedbackNotice}</FeedbackMessage>
      <FeedbackMessage tone="error">{loadError}</FeedbackMessage>
      <FeedbackMessage tone="error">{actionError}</FeedbackMessage>
      <FeedbackMessage tone="info">{t("taskDetail.demoChecklist")}</FeedbackMessage>

      <SectionCard
        title={t("taskDetail.overviewTitle")}
        subtitle={t("taskDetail.overviewSubtitle")}
      >
        <dl className="detail-grid">
          <div>
            <dt>{t("taskDetail.status")}</dt>
            <dd>
              <StatusBadge status={task.status} />
            </dd>
          </div>
          <div>
            <dt>{t("taskDetail.taskType")}</dt>
            <dd>{formatTaskTypeLabel(task.task_type, language)}</dd>
          </div>
          <div>
            <dt>{t("taskDetail.agent")}</dt>
            <dd>{task.agent_name}</dd>
          </div>
          <div>
            <dt>{t("taskDetail.created")}</dt>
            <dd>{formatDateTime(task.created_at, locale, t("common.notAvailable"))}</dd>
          </div>
          <div>
            <dt>{t("taskDetail.started")}</dt>
            <dd>{formatDateTime(task.started_at, locale, t("common.notAvailable"))}</dd>
          </div>
          <div>
            <dt>{t("taskDetail.finished")}</dt>
            <dd>{formatDateTime(task.finished_at, locale, t("common.notAvailable"))}</dd>
          </div>
          <div>
            <dt>{t("taskDetail.duration")}</dt>
            <dd>{formatDuration(task.duration_ms, t("common.notAvailable"))}</dd>
          </div>
          <div>
            <dt>{t("taskDetail.rating")}</dt>
            <dd>{task.feedback_rating ? `${task.feedback_rating}/5` : t("taskDetail.notRatedYet")}</dd>
          </div>
        </dl>

        <div className="content-block">
          <h3>{t("taskDetail.taskInput")}</h3>
          <pre>{task.description || t("taskDetail.noDescription")}</pre>
        </div>
      </SectionCard>

      <SectionCard
        title={t("taskDetail.resultTitle")}
        subtitle={t("taskDetail.resultSubtitle")}
      >
        <div className="content-block">
          <h3>{t("taskDetail.resultText")}</h3>
          <pre>{task.result_text || t("taskDetail.noResult")}</pre>
        </div>

        {task.error_message ? (
          <p className="trace-error">{t("taskDetail.errorPrefix", { message: task.error_message })}</p>
        ) : null}
      </SectionCard>

      <SectionCard
        title={t("taskDetail.evalTitle")}
        subtitle={t("taskDetail.evalSubtitle")}
      >
        {!canEvaluateTask ? (
          <FeedbackMessage tone="info">{t("taskDetail.evalLocked")}</FeedbackMessage>
        ) : null}

        <form className="form-grid" onSubmit={handleSubmitFeedback}>
          <div className="feedback-rating-group">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                aria-label={t("taskDetail.rateOption", { value })}
                aria-pressed={feedbackForm.feedback_rating === value}
                className={
                  feedbackForm.feedback_rating === value
                    ? "rating-button rating-button-active"
                    : "rating-button"
                }
                disabled={!canEvaluateTask || feedbackSaving}
                key={value}
                onClick={() => updateFeedbackRating(value)}
                type="button"
              >
                {value}
              </button>
            ))}
          </div>

          <label className="form-field">
            <span>{t("taskDetail.commentOptional")}</span>
            <textarea
              disabled={!canEvaluateTask || feedbackSaving}
              maxLength={1200}
              onChange={updateFeedbackComment}
              placeholder={t("taskDetail.commentPlaceholder")}
              rows="4"
              value={feedbackForm.feedback_comment}
            />
          </label>

          <div className="feedback-meta-row">
            <span className="meta-pill">
              {t("taskDetail.lastFeedback", {
                value: formatDateTime(task.feedback_submitted_at, locale, t("common.notAvailable")),
              })}
            </span>
          </div>

          <button
            className="button button-primary"
            disabled={!canEvaluateTask || feedbackSaving}
            type="submit"
          >
            {feedbackSaving ? t("taskDetail.savingFeedback") : t("taskDetail.saveEvaluation")}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title={t("taskDetail.traceTitle")}
        subtitle={t("taskDetail.traceSubtitle")}
      >
        <TaskTraceList trace={trace?.execution_trace || task.execution_trace} />
      </SectionCard>

      {task.rag_debug ? (
        <SectionCard
          title={t("taskDetail.debugTitle")}
          subtitle={t("taskDetail.debugSubtitle")}
        >
          <details className="debug-details">
            <summary className="debug-summary">{t("taskDetail.openDebug")}</summary>
            <RagDebugPanel debug={task.rag_debug} />
          </details>
        </SectionCard>
      ) : null}
    </div>
  );
}
