import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "../theme/ThemeContext.jsx";

const OPTIONS = [
  { value: "light", label: "Clair", icon: Sun },
  { value: "dark", label: "Sombre", icon: Moon },
  { value: "system", label: "Système", icon: Monitor },
];

export function ThemeControl({ compact = false }) {
  const { mode, setMode } = useTheme();

  return (
    <div
      className={`theme-control${compact ? " theme-control--compact" : ""}`}
      role="group"
      aria-label="Apparence"
    >
      {OPTIONS.map((option) => {
        const Icon = option.icon;
        const active = mode === option.value;
        return (
          <button
            key={option.value}
            type="button"
            className={`theme-option${active ? " is-active" : ""}`}
            onClick={() => setMode(option.value)}
            aria-pressed={active}
            title={option.label}
          >
            <Icon size={compact ? 15 : 17} strokeWidth={1.9} />
            <span>{option.label}</span>
          </button>
        );
      })}
    </div>
  );
}
