import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { executeTask, getTask, getTaskTrace } from "../api/tasksApi";
import { RagDebugPanel } from "../components/RagDebugPanel";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { TaskTraceList } from "../components/TaskTraceList";
import { formatDateTime, formatDuration } from "../utils/formatters";


export function TaskDetailPage() {
  const { taskId } = useParams();
  const [task, setTask] = useState(null);
  const [trace, setTrace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadTaskDetail();
  }, [taskId]);

  async function loadTaskDetail() {
    setLoading(true);
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
      setLoading(false);
    }
  }

  async function handleExecute() {
    setExecuting(true);
    setError("");

    try {
      const taskData = await executeTask(taskId, { debug: true });
      const traceData = await getTaskTrace(taskId);
      setTask(taskData);
      setTrace(traceData);
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
        <p className="form-error">{error || "Task not found."}</p>
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
          disabled={executing}
          onClick={handleExecute}
          type="button"
        >
          {executing ? "Executing..." : "Execute with debug"}
        </button>
      </header>

      {error ? <p className="form-error">{error}</p> : null}

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
          <h3>Description</h3>
          <p>{task.description || "No description provided."}</p>
        </div>

        <div className="content-block">
          <h3>Result</h3>
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

      <SectionCard
        title="Debug Context"
        subtitle="RAG, memory and combined context visibility from the latest execution response."
      >
        <RagDebugPanel debug={task.rag_debug} />
      </SectionCard>
    </div>
  );
}
