const DEFAULT_API_URL = "/api/v1";

function normalizeApiUrl(url) {
  if (!url) {
    return DEFAULT_API_URL;
  }

  return url.endsWith("/") ? url.slice(0, -1) : url;
}

export const API_BASE_URL = normalizeApiUrl(
  import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL,
);
