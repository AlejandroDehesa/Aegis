import { useEffect, useState } from "react";

import { listAgents } from "../api/agentsApi";
import { AsyncContent } from "../components/AsyncContent";
import { SectionCard } from "../components/SectionCard";
import { useI18n } from "../hooks/useI18n";
import { getErrorMessage } from "../utils/errors";


export function AgentsPage() {
  const { t } = useI18n();
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAgents() {
      setLoading(true);
      setError("");

      try {
        const catalog = await listAgents();
        setAgents(catalog);
      } catch (loadError) {
        setError(getErrorMessage(loadError, t("agents.loading")));
      } finally {
        setLoading(false);
      }
    }

    loadAgents();
  }, []);

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <p className="eyebrow">{t("agents.eyebrow")}</p>
          <h2>{t("agents.title")}</h2>
        </div>
      </header>

      <SectionCard title={t("agents.catalogTitle")} subtitle={t("agents.catalogSubtitle")}>
        <AsyncContent
          loading={loading}
          error={error}
          isEmpty={!agents.length}
          loadingText={t("agents.loading")}
          emptyTitle={t("agents.emptyTitle")}
          emptyDescription={t("agents.emptyDescription")}
        >
          <div className="agent-grid">
            {agents.map((agent) => (
              <article className="agent-card" key={agent.name}>
                <p className="section-eyebrow">{agent.name}</p>
                <p>{agent.description}</p>
                <div className="tag-row">
                  {agent.supported_task_types.map((taskType) => (
                    <span className="tag" key={`${agent.name}-${taskType}`}>
                      {taskType}
                    </span>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </AsyncContent>
      </SectionCard>
    </div>
  );
}
