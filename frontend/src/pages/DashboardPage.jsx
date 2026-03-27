import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listAgents } from "../api/agentsApi";
import { listDocuments } from "../api/documentsApi";
import { listTasks } from "../api/tasksApi";
import { AsyncContent } from "../components/AsyncContent";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { ROUTES } from "../constants/routes";
import { getErrorMessage } from "../utils/errors";
import { formatDateTime } from "../utils/formatters";


export function DashboardPage() {
  const [summary, setSummary] = useState({
    tasks: [],
    documents: [],
    agents: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const [tasks, documents, agents] = await Promise.all([
          listTasks(),
          listDocuments(),
          listAgents(),
        ]);
        setSummary({ tasks, documents, agents });
      } catch (loadError) {
        setError(getErrorMessage(loadError, "Unable to load dashboard summary."));
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const recentTasks = summary.tasks.slice(0, 5);
  const ratedTasks = summary.tasks.filter((task) => task.feedback_rating !== null);
  const averageRating = ratedTasks.length
    ? (
      ratedTasks.reduce((total, task) => total + task.feedback_rating, 0) / ratedTasks.length
    ).toFixed(1)
    : "n/a";

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h2>Execution visibility at a glance</h2>
        </div>
      </header>

      <div className="stats-grid">
        <StatCard label="Tasks" value={summary.tasks.length} />
        <StatCard label="Documents" value={summary.documents.length} />
        <StatCard label="Agents" value={summary.agents.length} />
        <StatCard label="Rated Tasks" value={ratedTasks.length} />
        <StatCard label="Avg Rating" value={averageRating} />
      </div>

      <SectionCard
        title="Demo Flow"
        subtitle="Recommended walkthrough for interviews and portfolio demos."
      >
        <div className="demo-flow-grid">
          <Link className="list-item" to={ROUTES.TASKS}>
            <div>
              <strong>1) Create task</strong>
              <p className="list-item-subtitle">Open Tasks and create a realistic orchestration request.</p>
            </div>
          </Link>
          <Link className="list-item" to={ROUTES.TASKS}>
            <div>
              <strong>2) Execute task</strong>
              <p className="list-item-subtitle">Run it and watch status transitions with polling.</p>
            </div>
          </Link>
          <Link className="list-item" to={ROUTES.DOCUMENTS}>
            <div>
              <strong>3) Upload documents</strong>
              <p className="list-item-subtitle">Inject context to showcase retrieval-augmented execution.</p>
            </div>
          </Link>
          <Link className="list-item" to={ROUTES.TASKS}>
            <div>
              <strong>4) Review and rate output</strong>
              <p className="list-item-subtitle">Open task detail, inspect traces and submit quality feedback.</p>
            </div>
          </Link>
        </div>
      </SectionCard>

      <SectionCard
        title="Recent Tasks"
        subtitle="Latest task activity from the authenticated user."
      >
        <AsyncContent
          loading={loading}
          error={error}
          isEmpty={!recentTasks.length}
          loadingText="Loading dashboard..."
          emptyTitle="No tasks yet"
          emptyDescription="Create your first task from the Tasks view to start using Aegis."
        >
          <div className="list-stack">
            {recentTasks.map((task) => (
              <Link className="list-item" key={task.id} to={`/tasks/${task.id}`}>
                <div>
                  <strong>{task.title}</strong>
                  <p className="list-item-subtitle">{task.task_type}</p>
                </div>
                <div className="list-item-meta">
                  <StatusBadge status={task.status} />
                  <span className="meta-pill">
                    {task.feedback_rating ? `${task.feedback_rating}/5` : "Not rated"}
                  </span>
                  <span>{formatDateTime(task.created_at)}</span>
                </div>
              </Link>
            ))}
          </div>
        </AsyncContent>
      </SectionCard>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <article className="stat-card">
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}
