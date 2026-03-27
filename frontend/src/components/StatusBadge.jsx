import { formatStatusLabel } from "../utils/formatters";
import { useI18n } from "../hooks/useI18n";

export function StatusBadge({ status }) {
  const { language } = useI18n();
  const normalizedStatus = status || "unknown";

  return (
    <span className={`status-badge status-${normalizedStatus}`}>
      <span aria-hidden="true" className="status-dot" />
      {formatStatusLabel(normalizedStatus, language)}
    </span>
  );
}
