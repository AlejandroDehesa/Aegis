export function StatusBadge({ status }) {
  const normalizedStatus = status || "unknown";

  return (
    <span className={`status-badge status-${normalizedStatus}`}>
      {normalizedStatus}
    </span>
  );
}
