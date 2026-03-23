export function formatDateTime(value) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatDuration(durationMs) {
  if (durationMs === null || durationMs === undefined) {
    return "Not available";
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  return `${(durationMs / 1000).toFixed(2)} s`;
}

export function truncateText(value, maxLength = 180) {
  if (!value) {
    return "No data";
  }

  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength).trimEnd()}...`;
}

export function formatStatusLabel(status) {
  const normalizedStatus = status || "unknown";
  const labels = {
    pending: "Pending",
    processing: "Processing",
    completed: "Completed",
    failed: "Failed",
    unknown: "Unknown",
  };

  return labels[normalizedStatus] || normalizedStatus;
}

export function sortTasksByRecent(tasks) {
  return [...tasks].sort((left, right) => {
    return resolveTaskTimestamp(right) - resolveTaskTimestamp(left);
  });
}

export function getTaskActivityLabel(task) {
  if (task?.status === "processing" && task.started_at) {
    return `Started ${formatDateTime(task.started_at)}`;
  }

  if (task?.finished_at) {
    return `Finished ${formatDateTime(task.finished_at)}`;
  }

  if (task?.created_at) {
    return `Created ${formatDateTime(task.created_at)}`;
  }

  return "No recent activity";
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
