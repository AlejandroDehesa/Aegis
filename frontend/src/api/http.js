import { API_BASE_URL } from "../constants/env";

let unauthorizedHandler = null;

export class ApiError extends Error {
  constructor(message, { status = 0, payload = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = typeof handler === "function" ? handler : null;
}

function extractErrorDetail(payload) {
  if (typeof payload === "string" && payload.trim()) {
    return payload.trim();
  }

  if (payload && typeof payload === "object") {
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail.trim();
    }

    if (Array.isArray(payload.detail)) {
      const validationMessage = payload.detail
        .map((item) => item?.msg)
        .filter(Boolean)
        .join(". ");

      if (validationMessage) {
        return validationMessage;
      }
    }
  }

  return "";
}

function buildErrorMessage(status, payload) {
  const detail = extractErrorDetail(payload);

  if (detail) {
    return detail;
  }

  if (status === 401) {
    return "Your session expired. Please log in again.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 404) {
    return "The requested resource was not found.";
  }

  if (status === 409) {
    return "The action cannot be completed in the current task state.";
  }

  if (status >= 500) {
    return "The server failed to process this request. Please try again.";
  }

  return "The request could not be completed.";
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

export async function apiRequest(path, options = {}) {
  const { ignoreUnauthorized = false, ...requestOptions } = options;
  const headers = new Headers(requestOptions.headers || {});
  const body = requestOptions.body;

  if (!(body instanceof FormData) && body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...requestOptions,
      credentials: "include",
      headers,
      body:
        body instanceof FormData || body === undefined || typeof body === "string"
          ? body
          : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("Unable to connect to the API server.", { status: 0 });
  }

  const payload = await parseResponse(response).catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      if (!ignoreUnauthorized && unauthorizedHandler) {
        unauthorizedHandler();
      }
    }

    const detail = buildErrorMessage(response.status, payload);
    throw new ApiError(detail, {
      status: response.status,
      payload,
    });
  }

  return payload;
}
