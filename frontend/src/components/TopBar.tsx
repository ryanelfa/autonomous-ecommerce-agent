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
    <header className="flex items-center justify-between rounded-xl bg-[var(--surface)] px-4 py-3">
      <div className="flex items-center gap-3">
        <span dangerouslySetInnerHTML={{ __html: brand.logoSvg }} aria-hidden />
        <div>
          <h1 className="font-display text-2xl font-semibold leading-none">{brand.name} Ops</h1>
          <p className="text-xs text-[var(--muted)]">{brand.tagline} — Agent War Room</p>
        </div>
        <select
          aria-label="Changer de marque"
          className="ml-4 rounded-lg border border-[var(--accent-soft)] bg-[var(--bg)] px-2 py-1 text-sm"
          value={brand.id}
          onChange={(e) => onBrandChange(e.target.value)}
        >
          {brands.map((b) => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-4 text-sm">
        {!wsConnected && (
          <span className="text-[var(--danger)]">⟳ reconnexion…</span>
        )}
        <span className="flex items-center gap-2 text-[var(--muted)]">
          <span
            className="inline-block h-2 w-2 rounded-full"
            style={{ backgroundColor: simRunning ? "var(--success)" : "var(--muted)" }}
          />
          Simulation {simRunning ? "ON" : "OFF"}
        </span>
        <button
          onClick={onToggleSim}
          className="rounded-lg border border-[var(--accent-soft)] px-3 py-1 hover:border-[var(--accent)]"
        >
          {simRunning ? "⏸ Pause" : "▶ Reprendre"}
        </button>
      </div>
    </header>
  );
}
