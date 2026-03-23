import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { executeTask, getTask, getTaskTrace } from "../api/tasksApi";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { RagDebugPanel } from "../components/RagDebugPanel";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { TaskTraceList } from "../components/TaskTraceList";
import { usePolling } from "../hooks/usePolling";
import { formatDateTime, formatDuration } from "../utils/formatters";

export function TaskDetailPage() {
  const { taskId } = useParams();
  const [task, setTask] = useState(null);
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
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
    }

    setError("");

    try {
      const [taskData, traceData] = await Promise.all([
        getTask(taskId),
        getTaskTrace(taskId),
      ]);
      setTask(taskData);
      setTrace(traceData);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }

  async function handleExecute() {
    setExecuting(true);
    setError("");
    setNotice("");

    try {
      const taskData = await executeTask(taskId, { debug: true });
      const traceData = await getTaskTrace(taskId);
      setTask(taskData);
      setTrace(traceData);
      setNotice(
        taskData.status === "processing"
          ? "Execution started. This view will refresh automatically until the task finishes."
          : "Execution completed. The latest task detail is now visible.",
      );
    } catch (executeError) {
      setError(executeError.message);
    } finally {
      setExecuting(false);
    }
  }

  if (loading) {
    return (
      <div className="page-grid">
        <p>Loading task detail...</p>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="page-grid">
        <FeedbackMessage tone="error">{error || "Task not found."}</FeedbackMessage>
      </div>
    );
  }

  return (
    <div className="page-grid">
      <header className="page-header page-header-inline">
        <div>
          <p className="eyebrow">Task Detail</p>
          <h2>{task.title}</h2>
        </div>
        <button
          className="button button-primary"
          disabled={executing || task.status === "processing"}
          onClick={handleExecute}
          type="button"
        >
          {executing
            ? "Executing..."
            : task.status === "processing"
              ? "Processing..."
              : "Execute with debug"}
        </button>
      </header>

      <FeedbackMessage tone="info">
        {task.status === "processing"
          ? "Task is still running. Aegis is refreshing this page automatically."
          : notice}
      </FeedbackMessage>
      <FeedbackMessage tone="error">{error}</FeedbackMessage>

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
