import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listAgents } from "../api/agentsApi";
import { listDocuments } from "../api/documentsApi";
import { listTasks } from "../api/tasksApi";
import { AsyncContent } from "../components/AsyncContent";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { ROUTES } from "../constants/routes";
import { useI18n } from "../hooks/useI18n";
import { getErrorMessage } from "../utils/errors";
import { formatDateTime, formatTaskTypeLabel } from "../utils/formatters";

const DASHBOARD_PAGE_LIMIT = 50;

export function DashboardPage() {
  const { t, language, locale } = useI18n();
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
          listTasks({ limit: DASHBOARD_PAGE_LIMIT, offset: 0 }),
          listDocuments({ limit: DASHBOARD_PAGE_LIMIT, offset: 0 }),
          listAgents(),
        ]);
        setSummary({ tasks, documents, agents });
      } catch (loadError) {
        setError(getErrorMessage(loadError, t("dashboard.loading")));
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, [t]);

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
          <p className="eyebrow">{t("dashboard.eyebrow")}</p>
          <h2>{t("dashboard.title")}</h2>
        </div>
      </header>

      <div className="stats-grid">
        <StatCard label={t("dashboard.stats.tasks")} value={summary.tasks.length} />
        <StatCard label={t("dashboard.stats.documents")} value={summary.documents.length} />
        <StatCard label={t("dashboard.stats.agents")} value={summary.agents.length} />
        <StatCard label={t("dashboard.stats.ratedTasks")} value={ratedTasks.length} />
        <StatCard label={t("dashboard.stats.avgRating")} value={averageRating} />
      </div>

      <SectionCard
        title={t("dashboard.demoFlowTitle")}
        subtitle={t("dashboard.demoFlowSubtitle")}
        actions={
          <div className="quick-link-row">
            <Link className="button button-secondary" to={ROUTES.INSIGHTS}>
              {t("dashboard.openInsights")}
            </Link>
            <Link className="button button-secondary" to={ROUTES.TASKS}>
              {t("dashboard.openTasks")}
            </Link>
            <Link className="button button-secondary" to={ROUTES.DOCUMENTS}>
              {t("dashboard.openDocuments")}
            </Link>
          </div>
        }
      >
        <div className="demo-flow-grid">
          <Link className="list-item" to={ROUTES.TASKS}>
            <div>
              <strong>{t("dashboard.step1Title")}</strong>
              <p className="list-item-subtitle">{t("dashboard.step1Desc")}</p>
            </div>
          </Link>
          <Link className="list-item" to={ROUTES.TASKS}>
            <div>
              <strong>{t("dashboard.step2Title")}</strong>
              <p className="list-item-subtitle">{t("dashboard.step2Desc")}</p>
            </div>
          </Link>
          <Link className="list-item" to={ROUTES.DOCUMENTS}>
            <div>
              <strong>{t("dashboard.step3Title")}</strong>
              <p className="list-item-subtitle">{t("dashboard.step3Desc")}</p>
            </div>
          </Link>
          <Link className="list-item" to={ROUTES.TASKS}>
            <div>
              <strong>{t("dashboard.step4Title")}</strong>
              <p className="list-item-subtitle">{t("dashboard.step4Desc")}</p>
            </div>
          </Link>
          <Link className="list-item" to={ROUTES.INSIGHTS}>
            <div>
              <strong>{t("dashboard.step5Title")}</strong>
              <p className="list-item-subtitle">{t("dashboard.step5Desc")}</p>
            </div>
          </Link>
        </div>
      </SectionCard>

      <SectionCard
        title={t("dashboard.recentTasksTitle")}
        subtitle={t("dashboard.recentTasksSubtitle")}
      >
        <AsyncContent
          loading={loading}
          error={error}
          isEmpty={!recentTasks.length}
          loadingText={t("dashboard.loading")}
          emptyTitle={t("dashboard.emptyTitle")}
          emptyDescription={t("dashboard.emptyDescription")}
        >
          <div className="list-stack">
            {recentTasks.map((task) => (
              <Link className="list-item" key={task.id} to={`/tasks/${task.id}`}>
                <div>
                  <strong>{task.title}</strong>
                  <p className="list-item-subtitle">{formatTaskTypeLabel(task.task_type, language)}</p>
                </div>
                <div className="list-item-meta">
                  <StatusBadge status={task.status} />
                  <span className="meta-pill">
                    {task.feedback_rating ? `${task.feedback_rating}/5` : t("dashboard.notRated")}
                  </span>
                  <span>{formatDateTime(task.created_at, locale, t("common.notAvailable"))}</span>
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
