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
import { usePolling } from "../hooks/usePolling";
import { getErrorMessage } from "../utils/errors";
import { formatDateTime, formatDuration } from "../utils/formatters";

function createFeedbackForm(task) {
  return {
    feedback_rating: task?.feedback_rating || 0,
    feedback_comment: task?.feedback_comment || "",
  };
}

export function TaskDetailPage() {
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
      enabled: Boolean(task && ["pending", "processing"].includes(task.status)),
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
      const message = getErrorMessage(error, "Unable to load task detail.");
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
        taskData.status === "processing"
          ? "Execution started. This view will refresh automatically until the task finishes."
          : "Execution completed. The latest task detail is now visible.",
      );
    } catch (error) {
      setActionError(getErrorMessage(error, "Unable to execute this task."));
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
      setActionError("Select a rating before submitting feedback.");
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
      setFeedbackNotice("Task evaluation saved successfully.");
    } catch (error) {
      setActionError(getErrorMessage(error, "Unable to save task evaluation."));
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
          loadingText="Loading task detail..."
          emptyTitle="Task not found"
          emptyDescription="The requested task is not available for this user."
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
          <p className="eyebrow">Task Detail</p>
          <h2>{task.title}</h2>
        </div>
        <div className="header-action-row">
          <Link className="button button-secondary" to={ROUTES.TASKS}>
            Back to tasks
          </Link>
          <button
            className="button button-primary"
            disabled={executing || task.status === "processing"}
            onClick={handleExecute}
            type="button"
          >
            {executing
              ? "Executing task..."
              : task.status === "processing"
                ? "Task running..."
                : "Execute task"}
          </button>
        </div>
      </header>

      <FeedbackMessage tone="info">
        {task.status === "processing"
          ? "Task is still running. Aegis is refreshing this page automatically."
          : notice}
      </FeedbackMessage>
      <FeedbackMessage tone="success">{feedbackNotice}</FeedbackMessage>
      <FeedbackMessage tone="error">{loadError}</FeedbackMessage>
      <FeedbackMessage tone="error">{actionError}</FeedbackMessage>
      <FeedbackMessage tone="info">
        {"Demo checklist: execute -> inspect result and trace -> submit rating -> upload docs -> rerun task."}
      </FeedbackMessage>

      <SectionCard
        title="Task Overview"
        subtitle="Primary task metadata and current execution state."
      >
        <dl className="detail-grid">
          <div>
            <dt>Status</dt>
            <dd>
              <StatusBadge status={task.status} />
            </dd>
          </div>
          <div>
            <dt>Task type</dt>
            <dd>{task.task_type}</dd>
          </div>
          <div>
            <dt>Agent</dt>
            <dd>{task.agent_name}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{formatDateTime(task.created_at)}</dd>
          </div>
          <div>
            <dt>Started</dt>
            <dd>{formatDateTime(task.started_at)}</dd>
          </div>
          <div>
            <dt>Finished</dt>
            <dd>{formatDateTime(task.finished_at)}</dd>
          </div>
          <div>
            <dt>Duration</dt>
            <dd>{formatDuration(task.duration_ms)}</dd>
          </div>
          <div>
            <dt>Rating</dt>
            <dd>{task.feedback_rating ? `${task.feedback_rating}/5` : "Not rated yet"}</dd>
          </div>
        </dl>

        <div className="content-block">
          <h3>Task input</h3>
          <pre>{task.description || "No description provided."}</pre>
        </div>
      </SectionCard>

      <SectionCard
        title="Result"
        subtitle="Final consolidated output returned by the orchestration pipeline."
      >
        <div className="content-block">
          <h3>Result text</h3>
          <pre>{task.result_text || "No result available yet."}</pre>
        </div>

        {task.error_message ? (
          <p className="trace-error">Error: {task.error_message}</p>
        ) : null}
      </SectionCard>

      <SectionCard
        title="Result Evaluation"
        subtitle="Lightweight quality signal to rate the task output for demo and portfolio review."
      >
        {!canEvaluateTask ? (
          <FeedbackMessage tone="info">
            Run this task to completion first. Evaluation is enabled for completed or failed tasks.
          </FeedbackMessage>
        ) : null}

        <form className="form-grid" onSubmit={handleSubmitFeedback}>
          <div className="feedback-rating-group">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
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
            <span>Comment (optional)</span>
            <textarea
              disabled={!canEvaluateTask || feedbackSaving}
              maxLength={1200}
              onChange={updateFeedbackComment}
              placeholder="What worked well? What should improve?"
              rows="4"
              value={feedbackForm.feedback_comment}
            />
          </label>

          <div className="feedback-meta-row">
            <span className="meta-pill">
              Last feedback: {formatDateTime(task.feedback_submitted_at)}
            </span>
          </div>

          <button
            className="button button-primary"
            disabled={!canEvaluateTask || feedbackSaving}
            type="submit"
          >
            {feedbackSaving ? "Saving feedback..." : "Save evaluation"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Execution Trace"
        subtitle="Lifecycle by step across the orchestration pipeline."
      >
        <TaskTraceList trace={trace?.execution_trace || task.execution_trace} />
      </SectionCard>

      {task.rag_debug ? (
        <SectionCard
          title="Debug Context"
          subtitle="Collapsed by default to keep the main product view focused on outcomes."
        >
          <details className="debug-details">
            <summary className="debug-summary">Open RAG and memory debug context</summary>
            <RagDebugPanel debug={task.rag_debug} />
          </details>
        </SectionCard>
      ) : null}
    </div>
  );
}
