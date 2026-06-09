import { apiRequest } from "./http";

export function listDocuments(options = {}) {
  const params = new URLSearchParams();

  if (options.limit !== undefined && options.limit !== null && options.limit !== "") {
    params.set("limit", String(options.limit));
  }

  if (options.offset !== undefined && options.offset !== null && options.offset !== "") {
    params.set("offset", String(options.offset));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";

  return apiRequest(`/documents${suffix}`);
}

export function uploadDocument({ title, content, file }) {
  const formData = new FormData();

  if (title) {
    formData.append("title", title);
  }

  if (content) {
    formData.append("content", content);
  }

  if (file) {
    formData.append("file", file);
  }

  return apiRequest("/documents", {
    method: "POST",
    body: formData,
  });
}

export function deleteDocument(documentId) {
  return apiRequest(`/documents/${documentId}`, {
    method: "DELETE",
  });
}
