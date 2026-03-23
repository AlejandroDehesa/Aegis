import { apiRequest } from "./http";

export function listDocuments() {
  return apiRequest("/documents");
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
