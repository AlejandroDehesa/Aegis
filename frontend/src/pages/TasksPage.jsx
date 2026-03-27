import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { createTask, executeTask, listTasks } from "../api/tasksApi";
import { AsyncContent } from "../components/AsyncContent";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { usePolling } from "../hooks/usePolling";
import { getErrorMessage } from "../utils/errors";
import {
  formatDateTime,
  formatDuration,
  getTaskActivityLabel,
  sortTasksByRecent,
  truncateText,
} from "../utils/formatters";

export function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [form, setForm] = useState({
    title: "",
    description: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [executingId, setExecutingId] = useState(null);
  const [listError, setListError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void loadTasks();
  }, []);

  usePolling(
    () => {
      void loadTasks({ silent: true });
    },
    {
      enabled: tasks.some((task) =>
        ["pending", "processing"].includes(task.status),
      ),
      intervalMs: 3000,
    },
  );

  async function loadTasks({ silent = false } = {}) {
    if (!silent) {
      setLoading(true);
    }

    setListError("");

    try {
      const taskList = await listTasks();
      setTasks(sortTasksByRecent(taskList));
    } catch (loadError) {
      setListError(getErrorMessage(loadError, "Unable to load tasks."));
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }

  function updateField(event) {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  async function handleCreateTask(event) {
    event.preventDefault();
    setSaving(true);
    setActionError("");
    setNotice("");

    try {
      await createTask(form);
      setForm({ title: "", description: "" });
      setNotice("Task created successfully. You can execute it from the list below.");
      await loadTasks();
    } catch (saveError) {
      setActionError(getErrorMessage(saveError, "Unable to create task."));
    } finally {
      setSaving(false);
    }
  }

  async function handleExecuteTask(taskId) {
    setExecutingId(taskId);
    setActionError("");
    setNotice("");

    try {
      const updatedTask = await executeTask(taskId, { debug: true });
      setTasks((current) =>
        sortTasksByRecent(
          current.map((task) => (task.id === taskId ? updatedTask : task)),
        ),
      );
      setNotice(
        updatedTask.status === "processing"
          ? "Execution started. The list will refresh automatically while the task is running."
          : "Task execution completed and the list has been updated.",
      );
      await loadTasks({ silent: true });
    } catch (executeError) {
      setActionError(getErrorMessage(executeError, "Unable to execute task."));
    } finally {
      setExecutingId(null);
    }
  }

  const runningCount = tasks.filter((task) =>
    ["pending", "processing"].includes(task.status),
  ).length;

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <p className="eyebrow">Tasks</p>
          <h2>Create, execute and inspect task runs</h2>
        </div>
      </header>

      <FeedbackMessage tone="success">{notice}</FeedbackMessage>
      <FeedbackMessage tone="error">{actionError}</FeedbackMessage>

      <SectionCard
        title="Create Task"
        subtitle="A compact form to push work into the backend orchestration flow."
      >
        <form className="form-grid" onSubmit={handleCreateTask}>
          <label className="form-field">
            <span>Title</span>
            <input
              name="title"
              onChange={updateField}
              placeholder="Compare FastAPI and Django for an internal AI platform"
              required
              value={form.title}
            />
          </label>

          <label className="form-field">
            <span>Description</span>
            <textarea
              name="description"
              onChange={updateField}
              placeholder="Describe the task, expected output or context."
              rows="5"
              value={form.description}
            />
          </label>

          <button className="button button-primary" disabled={saving} type="submit">
            {saving ? "Creating..." : "Create task"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Task List"
        subtitle="Current tasks with status, summary and quick execution control."
        actions={
          <>
            <span className="meta-pill">{tasks.length} total</span>
            <span className="meta-pill meta-pill-accent">{runningCount} active</span>
            <button
              className="button button-secondary"
              disabled={loading}
              onClick={() => {
                void loadTasks();
              }}
              type="button"
            >
              Refresh
            </button>
          </>
        }
      >
        <FeedbackMessage tone="info">
          {runningCount
            ? "Aegis refreshes active tasks automatically while they are pending or processing."
            : ""}
        </FeedbackMessage>

        <AsyncContent
          loading={loading}
          error={listError}
          isEmpty={!tasks.length}
          loadingText="Loading tasks..."
          emptyTitle="No tasks available"
          emptyDescription="Create a task to start interacting with the execution system."
        >
          <div className="list-stack">
            {tasks.map((task) => (
              <article className="list-item" key={task.id}>
                <div>
                  <Link className="list-item-title task-list-title" to={`/tasks/${task.id}`}>
                    {task.title}
                  </Link>
                  <p className="list-item-subtitle">
                    {task.task_type} / {task.agent_name}
                  </p>
                  <p className="list-item-copy task-list-copy">
                    {truncateText(task.result_text || task.description)}
                  </p>
                  <div className="task-kpi-row">
                    <span className="meta-pill">{getTaskActivityLabel(task)}</span>
                    <span className="meta-pill">
                      Duration: {formatDuration(task.duration_ms)}
                    </span>
                    <span className="meta-pill">
                      Rating: {task.feedback_rating ? `${task.feedback_rating}/5` : "not rated"}
                    </span>
                  </div>
                </div>

                <div className="list-item-meta">
                  <StatusBadge status={task.status} />
                  <span>{formatDateTime(task.created_at)}</span>
                  <div className="list-item-actions">
                    <Link className="button button-secondary" to={`/tasks/${task.id}`}>
                      View detail
                    </Link>
                    <button
                      className="button button-primary"
                      disabled={
                        executingId === task.id || task.status === "processing"
                      }
                      onClick={() => handleExecuteTask(task.id)}
                      type="button"
                    >
                      {executingId === task.id
                        ? "Executing..."
                        : task.status === "processing"
                          ? "Processing..."
                          : "Execute"}
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </AsyncContent>
      </SectionCard>
    </div>
  );
}
