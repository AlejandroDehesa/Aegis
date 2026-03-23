import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listAgents } from "../api/agentsApi";
import { listDocuments } from "../api/documentsApi";
import { listTasks } from "../api/tasksApi";
import { EmptyState } from "../components/EmptyState";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
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
        setError(loadError.message);
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const recentTasks = summary.tasks.slice(0, 5);

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
      </div>

      <SectionCard
        title="Recent Tasks"
        subtitle="Latest task activity from the authenticated user."
      >
        {loading ? <p>Loading dashboard...</p> : null}
        {error ? <p className="form-error">{error}</p> : null}

        {!loading && !error && !recentTasks.length ? (
          <EmptyState
            title="No tasks yet"
            description="Create your first task from the Tasks view to start using Aegis."
          />
        ) : null}

        {!loading && !error && recentTasks.length ? (
          <div className="list-stack">
            {recentTasks.map((task) => (
              <Link className="list-item" key={task.id} to={`/tasks/${task.id}`}>
                <div>
                  <strong>{task.title}</strong>
                  <p className="list-item-subtitle">{task.task_type}</p>
                </div>
                <div className="list-item-meta">
                  <StatusBadge status={task.status} />
                  <span>{formatDateTime(task.created_at)}</span>
                </div>
              </Link>
            ))}
          </div>
        ) : null}
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
