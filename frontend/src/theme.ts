import type { Brand } from "./types";

/** Converts a #RRGGBB hex to "r, g, b" for use in rgba(). */
function hexToRgb(hex: string): string {
  const h = hex.replace("#", "");
  const r = parseInt(h.substring(0, 2), 16);
  const g = parseInt(h.substring(2, 4), 16);
  const b = parseInt(h.substring(4, 6), 16);
  return `${r}, ${g}, ${b}`;
}

/** Darkens a #RRGGBB hex by a factor (0.8 = 20% darker) for hover/strong states. */
function darken(hex: string, factor = 0.8): string {
  const h = hex.replace("#", "");
  const r = Math.round(parseInt(h.substring(0, 2), 16) * factor);
  const g = Math.round(parseInt(h.substring(2, 4), 16) * factor);
  const b = Math.round(parseInt(h.substring(4, 6), 16) * factor);
  return `#${[r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

/** Injects the active brand palette as CSS variables. No hardcoded colors in components. */
export function applyBrandTheme(brand: Brand): void {
  const root = document.documentElement;
  const c = brand.colors;
  root.style.setProperty("--bg", c.background);
  root.style.setProperty("--surface", c.surface);
  root.style.setProperty("--accent", c.accent);
  root.style.setProperty("--accent-soft", c.accentSoft);
  root.style.setProperty("--accent-strong", darken(c.accent));
  root.style.setProperty("--accent-rgb", hexToRgb(c.accent));
  root.style.setProperty("--text", c.text);
  root.style.setProperty("--muted", c.muted);
  root.style.setProperty("--danger", c.danger);
  root.style.setProperty("--success", c.success);
  document.body.style.backgroundColor = c.background;
}