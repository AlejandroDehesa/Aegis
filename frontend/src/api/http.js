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
    return "Tu sesion expiro. Inicia sesion de nuevo.";
  }

  if (status === 403) {
    return "No tienes permisos para realizar esta accion.";
  }

  if (status === 404) {
    return "No se encontro el recurso solicitado.";
  }

  if (status === 409) {
    return "La accion no se puede completar en el estado actual de la tarea.";
  }

  if (status >= 500) {
    return "El servidor no pudo procesar esta solicitud. Intentalo de nuevo.";
  }

  return "No se pudo completar la solicitud.";
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
    throw new ApiError("No se pudo conectar con la API.", { status: 0 });
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
