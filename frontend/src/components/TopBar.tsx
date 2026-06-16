import type { Brand } from "../types";

export function TopBar(props: {
  brand: Brand;
  brands: { id: string; name: string }[];
  simRunning: boolean;
  wsConnected: boolean;
  onBrandChange: (brandId: string) => void;
  onToggleSim: () => void;
}) {
  const { brand, brands, simRunning, wsConnected, onBrandChange, onToggleSim } = props;
  return (
    <header className="sfx-console-header flex items-center justify-between px-4 py-2.5">
      <div className="flex items-center gap-3">
        <span
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-[var(--border)] bg-[var(--surface-alt)] [&>svg]:h-7 [&>svg]:w-7"
          dangerouslySetInnerHTML={{ __html: brand.logoSvg }}
          aria-hidden
        />
        <div>
          <h1 className="font-display text-lg font-bold leading-tight text-[var(--accent-strong)]">
            {brand.name} Ops
          </h1>
          <p className="text-xs text-[var(--muted)]">
            {brand.tagline} — Console Agent Service
          </p>
        </div>
        <select
          aria-label="Changer de marque"
          className="sfx-select ml-2 px-2.5 py-1.5"
          value={brand.id}
          onChange={(e) => onBrandChange(e.target.value)}
        >
          {brands.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-3 text-sm">
        <span
          className="flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--surface-alt)] px-2.5 py-1 text-xs font-medium"
          title={wsConnected ? "WebSocket connecté" : "Reconnexion en cours"}
        >
          <span
            className={`inline-block h-2 w-2 rounded-full ${wsConnected ? "bg-[var(--success)]" : "bg-[var(--warning)] anim-pulse-soft"}`}
          />
          {wsConnected ? "En ligne" : "Reconnexion…"}
        </span>
        <span className="flex items-center gap-2 text-xs text-[var(--muted)]">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: simRunning ? "var(--success)" : "var(--muted)" }}
          />
          Simulation {simRunning ? "ON" : "OFF"}
        </span>
        <button
          onClick={onToggleSim}
          className="sfx-button px-3 py-1.5"
        >
          {simRunning ? "⏸ Pause" : "▶ Reprendre"}
        </button>
      </div>
    </header>
  );
}
