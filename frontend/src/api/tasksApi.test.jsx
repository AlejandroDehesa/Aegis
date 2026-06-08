import { createTask, executeTask, getTask, getTaskTrace, listTasks, submitTaskFeedback } from "./tasksApi";

const httpMocks = vi.hoisted(() => ({
  apiRequest: vi.fn(),
}));

vi.mock("./http", () => httpMocks);

describe("tasksApi", () => {
  beforeEach(() => {
    httpMocks.apiRequest.mockReset();
    httpMocks.apiRequest.mockResolvedValue({});
  });

  test("listTasks sends filters plus pagination params", async () => {
    await listTasks({
      status: "completed",
      taskType: "comparison",
      agentName: "ComparisonAgent",
      feedbackRating: 5,
      limit: 50,
      offset: 10,
    });

    expect(httpMocks.apiRequest).toHaveBeenCalledWith(
      "/tasks?status=completed&task_type=comparison&agent_name=ComparisonAgent&feedback_rating=5&limit=50&offset=10",
    );
  });

  test("getTask calls task detail endpoint", async () => {
    await getTask("task-1");
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/tasks/task-1");
  });

  test("createTask posts payload", async () => {
    await createTask({ title: "Test", description: "Desc" });
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/tasks", {
      method: "POST",
      body: { title: "Test", description: "Desc" },
    });
  });

  test("executeTask encodes debug/topK/minScore params", async () => {
    await executeTask("task-1", { debug: true, topK: 5, minScore: 0.25 });
    expect(httpMocks.apiRequest).toHaveBeenCalledWith(
      "/tasks/task-1/execute?debug=true&top_k=5&min_score=0.25",
      { method: "POST" },
    );
  });

  test("getTaskTrace calls trace endpoint", async () => {
    await getTaskTrace("task-1");
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/tasks/task-1/trace");
  });

  test("submitTaskFeedback posts feedback payload", async () => {
    await submitTaskFeedback("task-1", { feedback_rating: 4, feedback_comment: "Useful" });
    expect(httpMocks.apiRequest).toHaveBeenCalledWith("/tasks/task-1/feedback", {
      method: "POST",
      body: { feedback_rating: 4, feedback_comment: "Useful" },
    });
  });
});
