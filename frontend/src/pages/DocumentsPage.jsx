import { useEffect, useState } from "react";

import { deleteDocument, listDocuments, uploadDocument } from "../api/documentsApi";
import { EmptyState } from "../components/EmptyState";
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
  const [error, setError] = useState("");

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoading(true);
    setError("");

    try {
      const items = await listDocuments();
      setDocuments(items);
    } catch (loadError) {
      setError(loadError.message);
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
    setError("");

    try {
      await uploadDocument(form);
      setForm({ title: "", content: "", file: null });
      event.currentTarget.reset();
      await loadDocuments();
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(documentId) {
    setDeletingId(documentId);
    setError("");

    try {
      await deleteDocument(documentId);
      setDocuments((current) =>
        current.filter((document) => document.id !== documentId),
      );
    } catch (deleteError) {
      setError(deleteError.message);
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

      <SectionCard title="Upload Document" subtitle="Provide raw text or a simple UTF-8 file.">
        <form className="form-grid" onSubmit={handleUpload}>
          <label className="form-field">
            <span>Title</span>
            <input name="title" onChange={updateField} placeholder="Architecture notes" />
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
            <input accept=".txt,.md,.csv,.json" name="file" onChange={updateField} type="file" />
          </label>

          {error ? <p className="form-error">{error}</p> : null}

          <button className="button button-primary" disabled={saving} type="submit">
            {saving ? "Uploading..." : "Upload document"}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title="Document Library"
        subtitle="Stored documents available for retrieval augmentation."
      >
        {loading ? <p>Loading documents...</p> : null}

        {!loading && !documents.length ? (
          <EmptyState
            title="No documents uploaded"
            description="Upload a document to enrich retrieval and execution context."
          />
        ) : null}

        {!loading && documents.length ? (
          <div className="list-stack">
            {documents.map((document) => (
              <article className="list-item" key={document.id}>
                <div>
                  <strong>{document.title}</strong>
                  <p className="list-item-subtitle">
                    {document.source_type} · {document.chunk_count} chunks
                  </p>
                  <p className="list-item-copy">{truncateText(document.content_preview)}</p>
                </div>
                <div className="list-item-meta">
                  <span>{formatDateTime(document.created_at)}</span>
                  <button
                    className="button button-secondary"
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
        ) : null}
      </SectionCard>
    </div>
  );
}
