import { STATUS_LABELS } from "../lib/format.js";

export function StatusBadge({ status, size = "md" }) {
  const label = STATUS_LABELS[status] || status || "Inconnu";
  return (
    <span className={`status-badge status-badge--${status || "unknown"} status-badge--${size}`}>
      <span className="status-dot" />
      {label}
    </span>
  );
}
