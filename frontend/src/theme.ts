import type { Brand } from "./types";

/** Injects the active brand palette as CSS variables. No hardcoded colors in components. */
export function applyBrandTheme(brand: Brand): void {
  const root = document.documentElement;
  const c = brand.colors;
  root.style.setProperty("--bg", c.background);
  root.style.setProperty("--surface", c.surface);
  root.style.setProperty("--accent", c.accent);
  root.style.setProperty("--accent-soft", c.accentSoft);
  root.style.setProperty("--text", c.text);
  root.style.setProperty("--muted", c.muted);
  root.style.setProperty("--danger", c.danger);
  root.style.setProperty("--success", c.success);
  document.body.style.backgroundColor = c.background;
}
