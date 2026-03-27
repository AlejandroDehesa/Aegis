import { useEffect, useState } from "react";

import { listAgents } from "../api/agentsApi";
import { AsyncContent } from "../components/AsyncContent";
import { SectionCard } from "../components/SectionCard";
import { getErrorMessage } from "../utils/errors";


export function AgentsPage() {
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
        setError(getErrorMessage(loadError, "Unable to load agents catalog."));
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
          <p className="eyebrow">Agents</p>
          <h2>Catalog of execution capabilities and routing targets</h2>
        </div>
      </header>

      <SectionCard title="Agent Catalog" subtitle="Static catalog exposed by the backend.">
        <AsyncContent
          loading={loading}
          error={error}
          isEmpty={!agents.length}
          loadingText="Loading agents..."
          emptyTitle="No agents available"
          emptyDescription="The backend did not return any configured agents."
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
