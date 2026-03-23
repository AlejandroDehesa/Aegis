import { formatStatusLabel } from "../utils/formatters";

export function StatusBadge({ status }) {
  const normalizedStatus = status || "unknown";

  return (
    <span className={`status-badge status-${normalizedStatus}`}>
      <span aria-hidden="true" className="status-dot" />
      {formatStatusLabel(normalizedStatus)}
    </span>
  );
}
