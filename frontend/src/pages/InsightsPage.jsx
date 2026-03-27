import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getInsightsOverview } from "../api/insightsApi";
import { listTasks } from "../api/tasksApi";
import { AsyncContent } from "../components/AsyncContent";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { getErrorMessage } from "../utils/errors";
import { formatDateTime, truncateText } from "../utils/formatters";

export function InsightsPage() {
  const [overview, setOverview] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadInsights() {
      setLoading(true);
      setError("");

      try {
        const [overviewResponse, tasksResponse] = await Promise.all([
          getInsightsOverview(),
          listTasks(),
        ]);
        setOverview(overviewResponse);
        setTasks(tasksResponse);
      } catch (loadError) {
        setError(getErrorMessage(loadError, "Unable to load operational insights."));
      } finally {
        setLoading(false);
      }
    }

    void loadInsights();
  }, []);

  const qualityReviewQueue = useMemo(
    () =>
      tasks
        .filter(
          (task) =>
            task.status === "failed" || (task.feedback_rating !== null && task.feedback_rating <= 2),
        )
        .slice(0, 8),
    [tasks],
  );

  const topRatedTasks = useMemo(
    () =>
      tasks
        .filter((task) => task.feedback_rating !== null && task.feedback_rating >= 4)
        .slice(0, 8),
    [tasks],
  );

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <p className="eyebrow">Insights</p>
          <h2>Operational visibility and quality review</h2>
        </div>
      </header>

      <FeedbackMessage tone="info">
        Use this view to identify failures, low-rated outputs, and strong task runs.
      </FeedbackMessage>

      <AsyncContent
        loading={loading}
        error={error}
        isEmpty={false}
        loadingText="Loading operational insights..."
      >
        <>
          <div className="stats-grid">
            <StatCard label="Total Tasks" value={overview?.total_tasks ?? 0} />
            <StatCard label="Failed Tasks" value={overview?.failed_tasks ?? 0} />
            <StatCard label="Low Rated" value={overview?.low_rated_tasks ?? 0} />
            <StatCard label="Unrated" value={overview?.unrated_tasks ?? 0} />
          </div>

          <SectionCard
            title="Distribution Snapshot"
            subtitle="Simple per-user distributions by status, type, agent and rating."
          >
            <div className="insights-grid">
              <DistributionList title="By status" items={overview?.tasks_by_status} />
              <DistributionList title="By task type" items={overview?.tasks_by_task_type} />
              <DistributionList title="By agent" items={overview?.tasks_by_agent_name} />
              <DistributionList title="By feedback rating" items={overview?.feedback_rating_distribution} />
            </div>
          </SectionCard>

          <SectionCard
            title="Quality Review Queue"
            subtitle="Failed or low-rated tasks that should be reviewed first."
          >
            {!qualityReviewQueue.length ? (
              <FeedbackMessage tone="success">
                No failed or low-rated tasks detected for this user.
              </FeedbackMessage>
            ) : (
              <div className="list-stack">
                {qualityReviewQueue.map((task) => (
                  <Link className="list-item" key={task.id} to={`/tasks/${task.id}`}>
                    <div>
                      <strong>{task.title}</strong>
                      <p className="list-item-subtitle">
                        {task.task_type} / {task.agent_name}
                      </p>
                      <p className="list-item-copy">
                        {truncateText(task.feedback_comment || task.result_text || task.description)}
                      </p>
                    </div>
                    <div className="list-item-meta">
                      <StatusBadge status={task.status} />
                      <span className="meta-pill">
                        Rating: {task.feedback_rating !== null ? `${task.feedback_rating}/5` : "not rated"}
                      </span>
                      <span>{formatDateTime(task.created_at)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard
            title="Strong Results"
            subtitle="Recent highly-rated outputs useful for demo storytelling."
          >
            {!topRatedTasks.length ? (
              <FeedbackMessage tone="info">
                No high-rated tasks yet. Complete and evaluate a few tasks to populate this section.
              </FeedbackMessage>
            ) : (
              <div className="list-stack">
                {topRatedTasks.map((task) => (
                  <Link className="list-item" key={task.id} to={`/tasks/${task.id}`}>
                    <div>
                      <strong>{task.title}</strong>
                      <p className="list-item-subtitle">
                        {task.task_type} / {task.agent_name}
                      </p>
                      <p className="list-item-copy">
                        {truncateText(task.feedback_comment || task.result_text || task.description)}
                      </p>
                    </div>
                    <div className="list-item-meta">
                      <StatusBadge status={task.status} />
                      <span className="meta-pill meta-pill-accent">{task.feedback_rating}/5</span>
                      <span>{formatDateTime(task.created_at)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </SectionCard>
        </>
      </AsyncContent>
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

function DistributionList({ title, items }) {
  const entries = Object.entries(items || {});

  return (
    <article className="insight-block">
      <p className="section-eyebrow">{title}</p>
      {!entries.length ? (
        <p className="list-item-subtitle">No data yet.</p>
      ) : (
        <div className="insight-list">
          {entries.map(([key, count]) => (
            <div className="insight-list-row" key={`${title}-${key}`}>
              <span>{key}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
