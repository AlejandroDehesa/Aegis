import { screen } from "@testing-library/react";
import { vi } from "vitest";

import { TasksPage } from "./TasksPage";
import { renderWithProviders } from "../test/testUtils";

const mockListTasks = vi.fn();

vi.mock("../api/tasksApi", () => ({
  listTasks: (...args) => mockListTasks(...args),
  createTask: vi.fn(),
  executeTask: vi.fn(),
}));

describe("TasksPage", () => {
  test("renders task list and execute action", async () => {
    mockListTasks.mockResolvedValueOnce([
      {
        id: "task-1",
        title: "Comparar FastAPI y Django",
        description: "Need recommendation",
        status: "completed",
        task_type: "comparison",
        agent_name: "ComparisonAgent",
        result_text: "Useful comparison output",
        duration_ms: 1200,
        feedback_rating: null,
        created_at: "2026-05-16T20:00:00Z",
      },
    ]);

    renderWithProviders(<TasksPage />);

    expect(await screen.findByText("Comparar FastAPI y Django")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ejecutar" })).toBeInTheDocument();
  });
});
