import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { createTask, executeTask, listTasks } from "../api/tasksApi";
import { EmptyState } from "../components/EmptyState";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { formatDateTime, truncateText } from "../utils/formatters";


export function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [form, setForm] = useState({
    title: "",
    description: "",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [executingId, setExecutingId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    loadTasks();
  }, []);

  async function loadTasks() {
    setLoading(true);
    setError("");

    try {
      const taskList = await listTasks();
      setTasks(taskList);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
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
    setError("");

    try {
      await createTask(form);
      setForm({ title: "", description: "" });
      await loadTasks();
    } catch (saveError) {
      setError(saveError.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleExecuteTask(taskId) {
    setExecutingId(taskId);
    setError("");

    try {
      const updatedTask = await executeTask(taskId, { debug: true });
      setTasks((current) =>
        current.map((task) => (task.id === taskId ? updatedTask : task)),
      );
    } catch (executeError) {
      setError(executeError.message);
    } finally {
      setExecutingId(null);
    }
  }

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <p className="eyebrow">Tasks</p>
          <h2>Create, execute and inspect task runs</h2>
        </div>
      </header>

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

          {error ? <p className="form-error">{error}</p> : null}

          <button className="button button-primary" disabled={saving} type="submit">
            {saving ? "Creating..." : "Create task"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Task List"
        subtitle="Current tasks with status, summary and quick execution control."
      >
        {loading ? <p>Loading tasks...</p> : null}

        {!loading && !tasks.length ? (
          <EmptyState
            title="No tasks available"
            description="Create a task to start interacting with the execution system."
          />
        ) : null}

        {!loading && tasks.length ? (
          <div className="list-stack">
            {tasks.map((task) => (
              <article className="list-item" key={task.id}>
                <div>
                  <Link className="list-item-title" to={`/tasks/${task.id}`}>
                    {task.title}
                  </Link>
                  <p className="list-item-subtitle">
                    {task.task_type} · {task.agent_name}
                  </p>
                  <p className="list-item-copy">
                    {truncateText(task.result_text || task.description)}
                  </p>
                </div>

                <div className="list-item-meta">
                  <StatusBadge status={task.status} />
                  <span>{formatDateTime(task.created_at)}</span>
                  <button
                    className="button button-secondary"
                    disabled={executingId === task.id}
                    onClick={() => handleExecuteTask(task.id)}
                    type="button"
                  >
                    {executingId === task.id ? "Executing..." : "Execute"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </SectionCard>
    </div>
  );
}
