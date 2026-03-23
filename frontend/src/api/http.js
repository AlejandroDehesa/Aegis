import { clearStoredToken, getStoredToken } from "../utils/storage";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

export async function apiRequest(path, options = {}) {
  const token = getStoredToken();
  const headers = new Headers(options.headers || {});
  const body = options.body;

  if (!(body instanceof FormData) && body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body:
      body instanceof FormData || body === undefined || typeof body === "string"
        ? body
        : JSON.stringify(body),
  });

  const payload = await parseResponse(response);

  if (!response.ok) {
    if (response.status === 401) {
      clearStoredToken();
    }

    const detail =
      typeof payload === "string"
        ? payload
        : payload?.detail || "Request failed";
    throw new Error(detail);
  }

  return payload;
}
