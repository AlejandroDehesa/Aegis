import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { getInsightsOverview } from "../api/insightsApi";
import { listTasks } from "../api/tasksApi";
import { AsyncContent } from "../components/AsyncContent";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { useI18n } from "../hooks/useI18n";
import { getErrorMessage } from "../utils/errors";
import { formatDateTime, formatTaskTypeLabel, truncateText } from "../utils/formatters";

const INSIGHTS_PAGE_LIMIT = 50;

export function InsightsPage() {
  const { t, language, locale } = useI18n();
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
          listTasks({ limit: INSIGHTS_PAGE_LIMIT, offset: 0 }),
        ]);
        setOverview(overviewResponse);
        setTasks(tasksResponse);
      } catch (loadError) {
        setError(getErrorMessage(loadError, t("insights.loading")));
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
          <p className="eyebrow">{t("insights.eyebrow")}</p>
          <h2>{t("insights.title")}</h2>
        </div>
      </header>

      <FeedbackMessage tone="info">{t("insights.helper")}</FeedbackMessage>

      <AsyncContent
        loading={loading}
        error={error}
        isEmpty={false}
        loadingText={t("insights.loading")}
      >
        <>
          <div className="stats-grid">
            <StatCard label={t("insights.stats.total")} value={overview?.total_tasks ?? 0} />
            <StatCard label={t("insights.stats.failed")} value={overview?.failed_tasks ?? 0} />
            <StatCard label={t("insights.stats.lowRated")} value={overview?.low_rated_tasks ?? 0} />
            <StatCard label={t("insights.stats.unrated")} value={overview?.unrated_tasks ?? 0} />
          </div>

          <SectionCard
            title={t("insights.distributionTitle")}
            subtitle={t("insights.distributionSubtitle")}
          >
            <div className="insights-grid">
              <DistributionList title={t("insights.byStatus")} items={overview?.tasks_by_status} noDataLabel={t("insights.noData")} />
              <DistributionList title={t("insights.byTaskType")} items={overview?.tasks_by_task_type} noDataLabel={t("insights.noData")} formatKey={(key) => formatTaskTypeLabel(key, language)} />
              <DistributionList title={t("insights.byAgent")} items={overview?.tasks_by_agent_name} noDataLabel={t("insights.noData")} />
              <DistributionList title={t("insights.byRating")} items={overview?.feedback_rating_distribution} noDataLabel={t("insights.noData")} />
            </div>
          </SectionCard>

          <SectionCard
            title={t("insights.queueTitle")}
            subtitle={t("insights.queueSubtitle")}
          >
            {!qualityReviewQueue.length ? (
              <FeedbackMessage tone="success">{t("insights.queueEmpty")}</FeedbackMessage>
            ) : (
              <div className="list-stack">
                {qualityReviewQueue.map((task) => (
                  <Link className="list-item" key={task.id} to={`/tasks/${task.id}`}>
                    <div>
                      <strong>{task.title}</strong>
                      <p className="list-item-subtitle">
                        {formatTaskTypeLabel(task.task_type, language)} / {task.agent_name}
                      </p>
                      <p className="list-item-copy">
                        {truncateText(task.feedback_comment || task.result_text || task.description, 180, t("common.noData"))}
                      </p>
                    </div>
                    <div className="list-item-meta">
                      <StatusBadge status={task.status} />
                      <span className="meta-pill">
                        {t("tasks.rating", {
                          value:
                            task.feedback_rating !== null ? `${task.feedback_rating}/5` : t("tasks.notRated"),
                        })}
                      </span>
                      <span>{formatDateTime(task.created_at, locale, t("common.notAvailable"))}</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard
            title={t("insights.strongTitle")}
            subtitle={t("insights.strongSubtitle")}
          >
            {!topRatedTasks.length ? (
              <FeedbackMessage tone="info">{t("insights.strongEmpty")}</FeedbackMessage>
            ) : (
              <div className="list-stack">
                {topRatedTasks.map((task) => (
                  <Link className="list-item" key={task.id} to={`/tasks/${task.id}`}>
                    <div>
                      <strong>{task.title}</strong>
                      <p className="list-item-subtitle">
                        {formatTaskTypeLabel(task.task_type, language)} / {task.agent_name}
                      </p>
                      <p className="list-item-copy">
                        {truncateText(task.feedback_comment || task.result_text || task.description, 180, t("common.noData"))}
                      </p>
                    </div>
                    <div className="list-item-meta">
                      <StatusBadge status={task.status} />
                      <span className="meta-pill meta-pill-accent">{task.feedback_rating}/5</span>
                      <span>{formatDateTime(task.created_at, locale, t("common.notAvailable"))}</span>
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

function DistributionList({ title, items, noDataLabel, formatKey = (key) => key }) {
  const entries = Object.entries(items || {});

  return (
    <article className="insight-block">
      <p className="section-eyebrow">{title}</p>
      {!entries.length ? (
        <p className="list-item-subtitle">{noDataLabel}</p>
      ) : (
        <div className="insight-list">
          {entries.map(([key, count]) => (
            <div className="insight-list-row" key={`${title}-${key}`}>
              <span>{formatKey(key)}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
