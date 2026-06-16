import { useEffect, useRef, useState } from "react";

import type { Kpis } from "../types";

/** Animated number: eases toward the target over ~800ms. */
function useAnimatedNumber(target: number): number {
  const [value, setValue] = useState(target);
  const fromRef = useRef(target);
  useEffect(() => {
    const from = fromRef.current;
    if (from === target) return;
    const start = performance.now();
    const duration = 800;
    let raf = 0;
    const step = (now: number) => {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - (1 - t) ** 3; // ease-out cubic
      setValue(from + (target - from) * eased);
      if (t < 1) raf = requestAnimationFrame(step);
      else fromRef.current = target;
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target]);
  return value;
}

export function KpiStrip({ kpis, savedFlash }: { kpis: Kpis; savedFlash: number }) {
  const saved = useAnimatedNumber(kpis.savedRevenue);
  return (
    <section className="grid grid-cols-2 gap-2 md:grid-cols-5 md:gap-3">
      <div
        key={savedFlash /* retrigger glow on each save */}
        className="sfx-metric-tile sfx-metric-tile-highlight anim-glow col-span-2 px-4 py-3 md:col-span-1"
        title="Substitution = 100% du montant · Bon d'achat = 50% · Information = 30% · Remboursement/Escalade = 0"
      >
        <p className="text-[0.625rem] font-bold uppercase tracking-wider text-[var(--muted)]">
          CA sauvé
        </p>
        <p className="font-display tabular mt-0.5 text-3xl font-bold text-[var(--accent)]">
          {saved.toLocaleString("fr-FR", { maximumFractionDigits: 0 })} €
        </p>
      </div>
      <Kpi label="Incidents résolus" value={String(kpis.incidentsResolved)} />
      <Kpi label="Escaladés" value={String(kpis.incidentsEscalated)} />
      <Kpi label="Taux d'escalade" value={`${Math.round(kpis.escalationRate * 100)} %`} />
      <Kpi label="Résolution moy." value={`${kpis.avgResolutionSeconds.toFixed(0)} s`} />
    </section>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="sfx-metric-tile px-4 py-3">
      <p className="text-[0.625rem] font-bold uppercase tracking-wider text-[var(--muted)]">
        {label}
      </p>
      <p className="font-mono-data tabular mt-0.5 text-2xl font-semibold text-[var(--accent-strong)]">
        {value}
      </p>
    </div>
  );
}
