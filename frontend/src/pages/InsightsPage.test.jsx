import { screen, within } from "@testing-library/react";
import { vi } from "vitest";

import { InsightsPage } from "./InsightsPage";
import { renderWithProviders } from "../test/testUtils";

const mockGetInsightsOverview = vi.fn();
const mockListTasks = vi.fn();

vi.mock("../api/insightsApi", () => ({
  getInsightsOverview: (...args) => mockGetInsightsOverview(...args),
}));

vi.mock("../api/tasksApi", () => ({
  listTasks: (...args) => mockListTasks(...args),
}));

describe("InsightsPage", () => {
  test("renders metrics and empty quality queue", async () => {
    mockGetInsightsOverview.mockResolvedValueOnce({
      total_tasks: 3,
      failed_tasks: 0,
      low_rated_tasks: 0,
      unrated_tasks: 1,
      tasks_by_status: { completed: 3 },
      tasks_by_task_type: { comparison: 1, analysis: 1, planning: 1 },
      tasks_by_agent_name: { ComparisonAgent: 1, AnalysisAgent: 1, PlanningAgent: 1 },
      feedback_rating_distribution: { "4": 1, "5": 2 },
    });
    mockListTasks.mockResolvedValueOnce([]);

    renderWithProviders(<InsightsPage />);

    expect(await screen.findByText("Calidad de ejecucion y visibilidad operativa")).toBeInTheDocument();
    const totalTasksCard = screen.getByText("Tareas totales").closest("article");
    expect(totalTasksCard).not.toBeNull();
    expect(within(totalTasksCard).getByText("3")).toBeInTheDocument();
    expect(screen.getByText("No hay tareas fallidas o mal valoradas para este usuario.")).toBeInTheDocument();
  });
});
