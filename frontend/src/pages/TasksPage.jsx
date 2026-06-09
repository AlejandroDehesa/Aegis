import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { createTask, executeTask, listTasks } from "../api/tasksApi";
import { AsyncContent } from "../components/AsyncContent";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { ROUTES } from "../constants/routes";
import { useI18n } from "../hooks/useI18n";
import { usePolling } from "../hooks/usePolling";
import { getErrorMessage } from "../utils/errors";
import {
  formatDateTime,
  formatDuration,
  formatTaskTypeLabel,
  getTaskActivityLabel,
  sortTasksByRecent,
  truncateText,
} from "../utils/formatters";

const EMPTY_FILTERS = {
  status: "",
  taskType: "",
  agentName: "",
  feedbackRating: "",
};
const PAGE_LIMIT = 50;

export function TasksPage() {
  const { t, language, locale } = useI18n();
  const demoTaskTemplate = {
    title: "Comparar FastAPI y Django para una plataforma interna de IA",
    description:
      "Haz una comparativa practica para un producto de orquestacion con IA: arquitectura, mantenibilidad, rendimiento y velocidad de implementacion.",
  };
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
  const [filters, setFilters] = useState(EMPTY_FILTERS);

  useEffect(() => {
    void loadTasks();
  }, []);

  usePolling(
    () => {
      void loadTasks({ silent: true });
    },
    {
      enabled: tasks.some((task) =>
        ["pending", "queued", "processing"].includes(task.status),
      ),
      intervalMs: 3000,
    },
  );

  async function loadTasks({ silent = false, activeFilters = filters } = {}) {
    if (!silent) {
      setLoading(true);
    }

    setListError("");

    try {
      const taskList = await listTasks({
        ...activeFilters,
        limit: PAGE_LIMIT,
        offset: 0,
      });
      setTasks(sortTasksByRecent(taskList));
    } catch (loadError) {
      setListError(getErrorMessage(loadError, t("tasks.loading")));
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

  function applyDemoTaskTemplate() {
    setForm(demoTaskTemplate);
    setNotice(t("tasks.demoTemplateLoaded"));
    setActionError("");
  }

  function updateFilterField(event) {
    const { name, value } = event.target;
    setFilters((current) => ({
      ...current,
      [name]: value,
    }));
  }

  function applyFilters() {
    void loadTasks({ activeFilters: filters });
  }

  function resetFilters() {
    setFilters(EMPTY_FILTERS);
    void loadTasks({ activeFilters: EMPTY_FILTERS });
  }

  async function handleCreateTask(event) {
    event.preventDefault();
    setSaving(true);
    setActionError("");
    setNotice("");

    try {
      await createTask(form);
      setForm({ title: "", description: "" });
      setNotice(t("tasks.createSuccess"));
      await loadTasks();
    } catch (saveError) {
      setActionError(getErrorMessage(saveError, t("tasks.create")));
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
        ["queued", "processing"].includes(updatedTask.status)
          ? t("tasks.executeStarted")
          : t("tasks.executeCompleted"),
      );
      await loadTasks({ silent: true });
    } catch (executeError) {
      setActionError(getErrorMessage(executeError, t("tasks.execute")));
    } finally {
      setExecutingId(null);
    }
  }

  const runningCount = tasks.filter((task) =>
    ["pending", "queued", "processing"].includes(task.status),
  ).length;

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <p className="eyebrow">{t("tasks.eyebrow")}</p>
          <h2>{t("tasks.title")}</h2>
        </div>
      </header>

      <FeedbackMessage tone="success">{notice}</FeedbackMessage>
      <FeedbackMessage tone="error">{actionError}</FeedbackMessage>

      <SectionCard
        title={t("tasks.createTitle")}
        subtitle={t("tasks.createSubtitle")}
        actions={
          <button
            className="button button-secondary"
            onClick={applyDemoTaskTemplate}
            type="button"
          >
            {t("tasks.useDemoTemplate")}
          </button>
        }
      >
        <form className="form-grid" onSubmit={handleCreateTask}>
          <label className="form-field">
            <span>{t("tasks.fieldTitle")}</span>
            <input
              name="title"
              onChange={updateField}
              placeholder={t("tasks.titlePlaceholder")}
              required
              value={form.title}
            />
          </label>

          <label className="form-field">
            <span>{t("tasks.fieldDescription")}</span>
            <textarea
              name="description"
              onChange={updateField}
              placeholder={t("tasks.descriptionPlaceholder")}
              rows="5"
              value={form.description}
            />
          </label>

          <button className="button button-primary" disabled={saving} type="submit">
            {saving ? t("tasks.creating") : t("tasks.create")}
          </button>
        </form>
        <p className="inline-helper">
          {t("tasks.demoPathHelper")}
          {" "}
          <Link className="inline-link" to={ROUTES.DOCUMENTS}>{t("tasks.addDocuments")}</Link>
          {t("tasks.addDocumentsSuffix")}
        </p>
      </SectionCard>

      <SectionCard
        title={t("tasks.listTitle")}
        subtitle={t("tasks.listSubtitle")}
        actions={
          <>
            <span className="meta-pill">{t("tasks.total", { count: tasks.length })}</span>
            <span className="meta-pill meta-pill-accent">{t("tasks.active", { count: runningCount })}</span>
            <button
              className="button button-secondary"
              disabled={loading}
              onClick={() => {
                void loadTasks();
              }}
              type="button"
            >
              {t("common.refresh")}
            </button>
          </>
        }
      >
        <FeedbackMessage tone="info">
          {runningCount
            ? t("tasks.autoRefreshNotice")
            : ""}
        </FeedbackMessage>
        <div className="filter-grid">
          <label className="form-field">
            <span>{t("tasks.filterStatus")}</span>
            <select name="status" onChange={updateFilterField} value={filters.status}>
              <option value="">{t("common.all")}</option>
              <option value="pending">{t("status.pending")}</option>
              <option value="queued">{t("status.queued")}</option>
              <option value="processing">{t("status.processing")}</option>
              <option value="completed">{t("status.completed")}</option>
              <option value="failed">{t("status.failed")}</option>
            </select>
          </label>

          <label className="form-field">
            <span>{t("tasks.filterTaskType")}</span>
            <select name="taskType" onChange={updateFilterField} value={filters.taskType}>
              <option value="">{t("common.all")}</option>
              <option value="general">{formatTaskTypeLabel("general", language)}</option>
              <option value="research">{formatTaskTypeLabel("research", language)}</option>
              <option value="summary">{formatTaskTypeLabel("summary", language)}</option>
              <option value="comparison">{formatTaskTypeLabel("comparison", language)}</option>
            </select>
          </label>

          <label className="form-field">
            <span>{t("tasks.filterAgent")}</span>
            <select name="agentName" onChange={updateFilterField} value={filters.agentName}>
              <option value="">{t("common.all")}</option>
              <option value="GeneralAssistantAgent">GeneralAssistantAgent</option>
              <option value="ResearchAgent">ResearchAgent</option>
              <option value="SummaryAgent">SummaryAgent</option>
              <option value="ComparisonAgent">ComparisonAgent</option>
            </select>
          </label>

          <label className="form-field">
            <span>{t("tasks.filterRating")}</span>
            <select
              name="feedbackRating"
              onChange={updateFilterField}
              value={filters.feedbackRating}
            >
              <option value="">{t("common.all")}</option>
              <option value="1">1</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
            </select>
          </label>
        </div>
        <div className="filter-actions">
          <button className="button button-secondary" onClick={applyFilters} type="button">
            {t("common.applyFilters")}
          </button>
          <button className="button button-secondary" onClick={resetFilters} type="button">
            {t("common.reset")}
          </button>
        </div>

        <AsyncContent
          loading={loading}
          error={listError}
          isEmpty={!tasks.length}
          loadingText={t("tasks.loading")}
          emptyTitle={t("tasks.emptyTitle")}
          emptyDescription={t("tasks.emptyDescription")}
        >
          <div className="list-stack">
            {tasks.map((task) => (
              <article className="list-item" key={task.id}>
                <div>
                  <Link className="list-item-title task-list-title" to={`/tasks/${task.id}`}>
                    {task.title}
                  </Link>
                  <p className="list-item-subtitle">
                    {formatTaskTypeLabel(task.task_type, language)} / {task.agent_name}
                  </p>
                  <p className="list-item-copy task-list-copy">
                    {truncateText(task.result_text || task.description, 180, t("common.noData"))}
                  </p>
                  <div className="task-kpi-row">
                    <span className="meta-pill">{getTaskActivityLabel(task, language, locale)}</span>
                    <span className="meta-pill">
                      {t("tasks.duration", {
                        value: formatDuration(task.duration_ms, t("common.notAvailable")),
                      })}
                    </span>
                    <span className="meta-pill">
                      {t("tasks.rating", {
                        value: task.feedback_rating ? `${task.feedback_rating}/5` : t("tasks.notRated"),
                      })}
                    </span>
                  </div>
                </div>

                <div className="list-item-meta">
                  <StatusBadge status={task.status} />
                  <span>{formatDateTime(task.created_at, locale, t("common.notAvailable"))}</span>
                  <div className="list-item-actions">
                    <Link className="button button-secondary" to={`/tasks/${task.id}`}>
                      {t("tasks.openDetail")}
                    </Link>
                    <button
                      className="button button-primary"
                      disabled={
                        executingId === task.id || ["queued", "processing"].includes(task.status)
                      }
                      onClick={() => handleExecuteTask(task.id)}
                      type="button"
                    >
                      {executingId === task.id
                        ? t("tasks.executing")
                        : ["queued", "processing"].includes(task.status)
                          ? t("tasks.processing")
                          : t("tasks.execute")}
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
