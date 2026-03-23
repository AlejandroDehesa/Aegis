import { useEffect, useState } from "react";

import { listAgents } from "../api/agentsApi";
import { EmptyState } from "../components/EmptyState";
import { SectionCard } from "../components/SectionCard";


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
        setError(loadError.message);
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
          <h2>Catalog of execution capabilities</h2>
        </div>
      </header>

      <SectionCard title="Agent Catalog" subtitle="Static catalog exposed by the backend.">
        {loading ? <p>Loading agents...</p> : null}
        {error ? <p className="form-error">{error}</p> : null}

        {!loading && !error && !agents.length ? (
          <EmptyState
            title="No agents available"
            description="The backend did not return any configured agents."
          />
        ) : null}

        {!loading && !error && agents.length ? (
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
        ) : null}
      </SectionCard>
    </div>
  );
}
