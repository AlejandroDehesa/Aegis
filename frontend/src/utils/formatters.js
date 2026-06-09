export function formatDateTime(value, locale = "en-US", notAvailableLabel = "Not available") {
  if (!value) {
    return notAvailableLabel;
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatDuration(durationMs, notAvailableLabel = "Not available") {
  if (durationMs === null || durationMs === undefined) {
    return notAvailableLabel;
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  return `${(durationMs / 1000).toFixed(2)} s`;
}

export function truncateText(value, maxLength = 180, emptyLabel = "No data") {
  if (!value) {
    return emptyLabel;
  }

  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength).trimEnd()}...`;
}

export function formatStatusLabel(status, language = "en") {
  const normalizedStatus = status || "unknown";
  const labelsByLanguage = {
    en: {
      pending: "Pending",
      queued: "Queued",
      processing: "Processing",
      completed: "Completed",
      failed: "Failed",
      unknown: "Unknown",
    },
    es: {
      pending: "Pendiente",
      queued: "En cola",
      processing: "Procesando",
      completed: "Completada",
      failed: "Fallida",
      unknown: "Desconocido",
    },
  };
  const labels = labelsByLanguage[language] || labelsByLanguage.en;

  return labels[normalizedStatus] || normalizedStatus;
}

export function formatTaskTypeLabel(taskType, language = "en") {
  const normalizedTaskType = taskType || "general";
  const labelsByLanguage = {
    en: {
      general: "General",
      research: "Research",
      summary: "Summary",
      comparison: "Comparison",
      analysis: "Analysis",
      planning: "Planning",
    },
    es: {
      general: "General",
      research: "Investigacion",
      summary: "Resumen",
      comparison: "Comparacion",
      analysis: "Analisis",
      planning: "Planificacion",
    },
  };
  const labels = labelsByLanguage[language] || labelsByLanguage.en;

  return labels[normalizedTaskType] || normalizedTaskType;
}

export function sortTasksByRecent(tasks) {
  return [...tasks].sort((left, right) => {
    return resolveTaskTimestamp(right) - resolveTaskTimestamp(left);
  });
}

export function getTaskActivityLabel(task, language = "en", locale = "en-US") {
  const startedLabel = language === "es" ? "Iniciada" : "Started";
  const queuedLabel = language === "es" ? "En cola" : "Queued";
  const finishedLabel = language === "es" ? "Finalizada" : "Finished";
  const createdLabel = language === "es" ? "Creada" : "Created";
  const noneLabel = language === "es" ? "Sin actividad reciente" : "No recent activity";

  if (task?.status === "queued") {
    return queuedLabel;
  }

  if (task?.status === "processing" && task.started_at) {
    return `${startedLabel} ${formatDateTime(task.started_at, locale)}`;
  }

  if (task?.finished_at) {
    return `${finishedLabel} ${formatDateTime(task.finished_at, locale)}`;
  }

  if (task?.created_at) {
    return `${createdLabel} ${formatDateTime(task.created_at, locale)}`;
  }

  return noneLabel;
}

function resolveTaskTimestamp(task) {
  const rawValue =
    task?.finished_at ||
    task?.started_at ||
    task?.updated_at ||
    task?.created_at ||
    null;

  if (!rawValue) {
    return 0;
  }

  return new Date(rawValue).getTime();
}
