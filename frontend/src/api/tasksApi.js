import { apiRequest } from "./http";

export function listTasks(filters = {}) {
  const params = new URLSearchParams();

  if (filters.status) {
    params.set("status", filters.status);
  }

  if (filters.taskType) {
    params.set("task_type", filters.taskType);
  }

  if (filters.agentName) {
    params.set("agent_name", filters.agentName);
  }

  if (filters.feedbackRating) {
    params.set("feedback_rating", String(filters.feedbackRating));
  }

  if (filters.limit !== undefined && filters.limit !== null && filters.limit !== "") {
    params.set("limit", String(filters.limit));
  }

  if (filters.offset !== undefined && filters.offset !== null && filters.offset !== "") {
    params.set("offset", String(filters.offset));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";

  return apiRequest(`/tasks${suffix}`);
}

export function getTask(taskId) {
  return apiRequest(`/tasks/${taskId}`);
}

export function createTask(payload) {
  return apiRequest("/tasks", {
    method: "POST",
    body: payload,
  });
}

export function executeTask(taskId, options = {}) {
  const params = new URLSearchParams();

  if (options.debug) {
    params.set("debug", "true");
  }

  if (options.topK) {
    params.set("top_k", String(options.topK));
  }

  if (options.minScore !== undefined && options.minScore !== null && options.minScore !== "") {
    params.set("min_score", String(options.minScore));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";

  return apiRequest(`/tasks/${taskId}/execute${suffix}`, {
    method: "POST",
  });
}

export function getTaskTrace(taskId) {
  return apiRequest(`/tasks/${taskId}/trace`);
}

export function submitTaskFeedback(taskId, payload) {
  return apiRequest(`/tasks/${taskId}/feedback`, {
    method: "POST",
    body: payload,
  });
}
