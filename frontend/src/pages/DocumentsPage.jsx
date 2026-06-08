import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { deleteDocument, listDocuments, uploadDocument } from "../api/documentsApi";
import { AsyncContent } from "../components/AsyncContent";
import { FeedbackMessage } from "../components/FeedbackMessage";
import { SectionCard } from "../components/SectionCard";
import { ROUTES } from "../constants/routes";
import { useI18n } from "../hooks/useI18n";
import { getErrorMessage } from "../utils/errors";
import { formatDateTime, truncateText } from "../utils/formatters";

const PAGE_LIMIT = 50;

export function DocumentsPage() {
  const { t, locale } = useI18n();
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
      const items = await listDocuments({ limit: PAGE_LIMIT, offset: 0 });
      setDocuments(items);
    } catch (loadError) {
      setListError(getErrorMessage(loadError, t("documents.loading")));
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
      setActionError(t("documents.missingContent"));
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
        t("documents.uploadSuccess", {
          title: document.title || t("documents.untitled"),
        }),
      );
      await loadDocuments();
    } catch (uploadError) {
      setActionError(getErrorMessage(uploadError, t("documents.upload")));
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
        t("documents.deleteSuccess", {
          title: deletedDocument?.title || t("documents.untitled"),
        }),
      );
    } catch (deleteError) {
      setActionError(getErrorMessage(deleteError, t("documents.delete")));
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="page-grid">
      <header className="page-header">
        <div>
          <p className="eyebrow">{t("documents.eyebrow")}</p>
          <h2>{t("documents.title")}</h2>
        </div>
      </header>

      <FeedbackMessage tone="info">
        {t("documents.helper")}
        <Link className="inline-link" to={ROUTES.TASKS}>{t("documents.goToTasks")}</Link>
      </FeedbackMessage>

      <FeedbackMessage tone="success">{notice}</FeedbackMessage>
      <FeedbackMessage tone="error">{actionError}</FeedbackMessage>

      <SectionCard title={t("documents.uploadTitle")} subtitle={t("documents.uploadSubtitle")}>
        <form className="form-grid" onSubmit={handleUpload}>
          <label className="form-field">
            <span>{t("documents.fieldTitle")}</span>
            <input
              name="title"
              onChange={updateField}
              placeholder={t("documents.titlePlaceholder")}
              value={form.title}
            />
          </label>

          <label className="form-field">
            <span>{t("documents.fieldText")}</span>
            <textarea
              name="content"
              onChange={updateField}
              placeholder={t("documents.textPlaceholder")}
              rows="6"
              value={form.content}
            />
          </label>

          <label className="form-field">
            <span>{t("documents.fieldFile")}</span>
            <input
              accept=".txt,.md,.csv,.json"
              name="file"
              onChange={updateField}
              ref={fileInputRef}
              type="file"
            />
          </label>

          <button className="button button-primary" disabled={saving} type="submit">
            {saving ? t("documents.uploading") : t("documents.upload")}
          </button>
        </form>
      </SectionCard>

      <SectionCard
        title={t("documents.libraryTitle")}
        subtitle={t("documents.librarySubtitle")}
        actions={
          <button
            className="button button-secondary"
            disabled={loading}
            onClick={() => {
              void loadDocuments();
              }}
              type="button"
            >
              {t("common.refresh")}
            </button>
        }
      >
        <AsyncContent
          loading={loading}
          error={listError}
          isEmpty={!documents.length}
          loadingText={t("documents.loading")}
          emptyTitle={t("documents.emptyTitle")}
          emptyDescription={t("documents.emptyDescription")}
        >
          <div className="list-stack">
            {documents.map((document) => (
              <article className="list-item" key={document.id}>
                <div>
                  <strong>{document.title || t("documents.untitled")}</strong>
                  <p className="list-item-subtitle">
                    {t("documents.sourceChunks", {
                      source: document.source_type,
                      chunks: document.chunk_count,
                    })}
                  </p>
                  <p className="list-item-copy">
                    {truncateText(document.content_preview, 180, t("common.noData"))}
                  </p>
                </div>
                <div className="list-item-meta">
                  <span>{formatDateTime(document.created_at, locale, t("common.notAvailable"))}</span>
                  <button
                    className="button button-danger"
                    disabled={deletingId === document.id}
                    onClick={() => handleDelete(document.id)}
                    type="button"
                  >
                    {deletingId === document.id ? t("documents.deleting") : t("documents.delete")}
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
