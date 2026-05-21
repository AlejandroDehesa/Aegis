import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { TaskDetailPage } from "./TaskDetailPage";
import { renderWithProviders } from "../test/testUtils";

const mockGetTask = vi.fn();
const mockGetTaskTrace = vi.fn();

vi.mock("../api/tasksApi", () => ({
  getTask: (...args) => mockGetTask(...args),
  getTaskTrace: (...args) => mockGetTaskTrace(...args),
  executeTask: vi.fn(),
  submitTaskFeedback: vi.fn(),
}));

describe("TaskDetailPage", () => {
  test("shows completed result and execution trace data", async () => {
    mockGetTask.mockResolvedValueOnce({
      id: "task-completed",
      title: "FastAPI vs Django comparison",
      description: "Need architecture recommendation",
      status: "completed",
      task_type: "comparison",
      agent_name: "ComparisonAgent",
      result_text: "FastAPI and Django comparison with recommendation.",
      execution_trace: [],
      created_at: "2026-05-16T20:00:00Z",
      started_at: "2026-05-16T20:00:01Z",
      finished_at: "2026-05-16T20:00:02Z",
      duration_ms: 1000,
      feedback_rating: null,
      feedback_comment: null,
      feedback_submitted_at: null,
      error_message: null,
    });
    mockGetTaskTrace.mockResolvedValueOnce({
      task_id: "task-completed",
      status: "completed",
      started_at: "2026-05-16T20:00:01Z",
      finished_at: "2026-05-16T20:00:02Z",
      duration_ms: 1000,
      execution_trace: [
        {
          step_index: 1,
          step_name: "classification",
          agent_name: "TaskClassifier",
          status: "completed",
          short_summary: "Task classified as comparison.",
          started_at: "2026-05-16T20:00:01Z",
          finished_at: "2026-05-16T20:00:01Z",
        },
      ],
    });

    renderWithProviders(<TaskDetailPage />, {
      route: "/tasks/task-completed",
      path: "/tasks/:taskId",
      useRoutes: true,
    });

    expect(await screen.findByText("FastAPI vs Django comparison")).toBeInTheDocument();
    expect(screen.getByText("FastAPI and Django comparison with recommendation.")).toBeInTheDocument();
    expect(screen.getByText("TaskClassifier")).toBeInTheDocument();
    expect(screen.queryByText(/future expansion/i)).not.toBeInTheDocument();
  });

  test("shows processing status and no-result fallback", async () => {
    mockGetTask.mockResolvedValueOnce({
      id: "task-processing",
      title: "Plan platform rollout",
      description: "Create a staged plan",
      status: "processing",
      task_type: "planning",
      agent_name: "PlanningAgent",
      result_text: null,
      execution_trace: [],
      created_at: "2026-05-16T20:00:00Z",
      started_at: "2026-05-16T20:00:01Z",
      finished_at: null,
      duration_ms: null,
      feedback_rating: null,
      feedback_comment: null,
      feedback_submitted_at: null,
      error_message: null,
    });
    mockGetTaskTrace.mockResolvedValueOnce({
      task_id: "task-processing",
      status: "processing",
      started_at: "2026-05-16T20:00:01Z",
      finished_at: null,
      duration_ms: null,
      execution_trace: [],
    });

    renderWithProviders(<TaskDetailPage />, {
      route: "/tasks/task-processing",
      path: "/tasks/:taskId",
      useRoutes: true,
    });

    expect(await screen.findByText("Plan platform rollout")).toBeInTheDocument();
    expect(screen.getByText("No result available yet.")).toBeInTheDocument();
    expect(screen.getByText("Task is still running. Aegis is refreshing this page automatically.")).toBeInTheDocument();
  });

  test("renders rag and llm metadata in execution trace", async () => {
    mockGetTask.mockResolvedValueOnce({
      id: "task-rag-meta",
      title: "RAG evidence audit",
      description: "Use document evidence",
      status: "completed",
      task_type: "analysis",
      agent_name: "AnalysisAgent",
      result_text: "Structured response with evidence used.",
      execution_trace: [],
      created_at: "2026-05-16T20:00:00Z",
      started_at: "2026-05-16T20:00:01Z",
      finished_at: "2026-05-16T20:00:04Z",
      duration_ms: 3000,
      feedback_rating: null,
      feedback_comment: null,
      feedback_submitted_at: null,
      error_message: null,
    });
    mockGetTaskTrace.mockResolvedValueOnce({
      task_id: "task-rag-meta",
      status: "completed",
      started_at: "2026-05-16T20:00:01Z",
      finished_at: "2026-05-16T20:00:04Z",
      duration_ms: 3000,
      execution_trace: [
        {
          step_index: 3,
          step_name: "execution",
          agent_name: "AnalysisAgent",
          status: "completed",
          short_summary: "Analysis completed with RAG support.",
          llm_provider: "openrouter",
          llm_model: "openai/gpt-4o-mini",
          llm_prompt_tokens: 200,
          llm_completion_tokens: 150,
          llm_total_tokens: 350,
          llm_fallback_used: false,
          rag_enabled: true,
          rag_vector_backend: "pgvector",
          rag_retrieved_chunks_count: 2,
          rag_documents_used: ["aegis_report.md", "railway_notes.md"],
          rag_snippets: ["Snippet one", "Snippet two"],
          rag_scores: [0.91, 0.84],
          started_at: "2026-05-16T20:00:02Z",
          finished_at: "2026-05-16T20:00:04Z",
        },
      ],
    });

    renderWithProviders(<TaskDetailPage />, {
      route: "/tasks/task-rag-meta",
      path: "/tasks/:taskId",
      useRoutes: true,
    });

    expect(await screen.findByText("RAG evidence audit")).toBeInTheDocument();
    expect(screen.getByText("backend=pgvector, chunks=2")).toBeInTheDocument();
    expect(screen.getByText("aegis_report.md, railway_notes.md")).toBeInTheDocument();
    expect(screen.getByText("RAG snippets")).toBeInTheDocument();
    expect(screen.getByText("Snippet one (score: 0.91)")).toBeInTheDocument();
  });
});
