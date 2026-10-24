import { initials } from "../lib/labels.js";

export function Avatar({ user, name, email, size = "md" }) {
  const label = name || user?.display_name || user?.email || "";
  const address = email || user?.email || "";
  const tone = user?.role || "default";
  return (
    <span
      className={`avatar avatar--${size} avatar--${tone}`}
      title={label || address}
      aria-hidden="true"
    >
      {initials(label, address)}
    </span>
  );
}
