import { useEffect, useRef, useState } from "react";

import { deleteDocument, listDocuments, uploadDocument } from "../api/documentsApi";
import { AsyncContent } from "../components/AsyncContent";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { SectionCard } from "../components/SectionCard";
import { formatDateTime, truncateText } from "../utils/formatters";

export function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [form, setForm] = useState({
    title: "",
    content: "",
    file: null,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [listError, setListError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const fileInputRef = useRef(null);

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoading(true);
    setListError("");

    try {
      const items = await listDocuments();
      setDocuments(items);
    } catch (loadError) {
      setListError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  function updateField(event) {
    const { name, value, files } = event.target;
    setForm((current) => ({
      ...current,
      [name]: files ? files[0] || null : value,
    }));
  }

  async function handleUpload(event) {
    event.preventDefault();
    setSaving(true);
    setActionError("");
    setNotice("");

    if (!form.content && !form.file) {
      setSaving(false);
      setActionError("Provide text content or upload a file before submitting the document.");
      return;
    }

    try {
      const document = await uploadDocument(form);
      setForm({ title: "", content: "", file: null });
      event.currentTarget.reset();

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      setNotice(
        `Document "${document.title || "Untitled document"}" uploaded successfully.`,
      );
      await loadDocuments();
    } catch (uploadError) {
      setActionError(uploadError.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(documentId) {
    setDeletingId(documentId);
    setActionError("");
    setNotice("");

    try {
      const deletedDocument = documents.find((document) => document.id === documentId);
      await deleteDocument(documentId);
      setDocuments((current) =>
        current.filter((document) => document.id !== documentId),
      );
      setNotice(
        `Document "${deletedDocument?.title || "Untitled document"}" removed from the library.`,
      );
    } catch (deleteError) {
      setActionError(deleteError.message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <p className="eyebrow">Documents</p>
          <h2>Context ingestion for retrieval</h2>
        </div>
      </header>

      <FeedbackMessage tone="success">{notice}</FeedbackMessage>
      <FeedbackMessage tone="error">{actionError}</FeedbackMessage>

      <SectionCard title="Upload Document" subtitle="Provide raw text or a simple UTF-8 file.">
        <form className="form-grid" onSubmit={handleUpload}>
          <label className="form-field">
            <span>Title</span>
            <input
              name="title"
              onChange={updateField}
              placeholder="Architecture notes"
              value={form.title}
            />
          </label>

          <label className="form-field">
            <span>Text content</span>
            <textarea
              name="content"
              onChange={updateField}
              placeholder="Paste document text here when not uploading a file."
              rows="6"
              value={form.content}
            />
          </label>

          <label className="form-field">
            <span>File</span>
            <input
              accept=".txt,.md,.csv,.json"
              name="file"
              onChange={updateField}
              ref={fileInputRef}
              type="file"
            />
          </label>

          <button className="button button-primary" disabled={saving} type="submit">
            {saving ? "Uploading..." : "Upload document"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Document Library"
        subtitle="Stored documents available for retrieval augmentation."
        actions={
          <button
            className="button button-secondary"
            disabled={loading}
            onClick={() => {
              void loadDocuments();
            }}
            type="button"
          >
            Refresh
          </button>
        }
      >
        <AsyncContent
          loading={loading}
          error={listError}
          isEmpty={!documents.length}
          loadingText="Loading documents..."
          emptyTitle="No documents uploaded"
          emptyDescription="Upload a document to enrich retrieval and execution context."
        >
          <div className="list-stack">
            {documents.map((document) => (
              <article className="list-item" key={document.id}>
                <div>
                  <strong>{document.title || "Untitled document"}</strong>
                  <p className="list-item-subtitle">
                    {document.source_type} / {document.chunk_count} chunks
                  </p>
                  <p className="list-item-copy">{truncateText(document.content_preview)}</p>
                </div>
                <div className="list-item-meta">
                  <span>{formatDateTime(document.created_at)}</span>
                  <button
                    className="button button-danger"
                    disabled={deletingId === document.id}
                    onClick={() => handleDelete(document.id)}
                    type="button"
                  >
                    {deletingId === document.id ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </article>
            ))}
          </div>
        </AsyncContent>
      </SectionCard>
    </div>
  );
}
