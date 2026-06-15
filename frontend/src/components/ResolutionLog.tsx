import type { Resolution } from "../types";
import { OUTCOME_LABEL } from "../types";

function outcomeColor(outcome: string): string {
  if (outcome === "human") return "var(--danger)";
  if (outcome === "refund") return "var(--muted)";
  return "var(--success)";
}

export function ResolutionLog({ resolutions }: { resolutions: Resolution[] }) {
  const done = resolutions.filter((r) => r.outcome !== "");
  return (
    <section className="flex min-h-0 flex-col rounded-xl bg-[var(--bg)]">
      <h2 className="px-1 pb-2 text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
        Résolutions
      </h2>
      <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1">
        {done.length === 0 && (
          <p className="px-1 text-sm text-[var(--muted)]">Aucune résolution pour l'instant.</p>
        )}
        {done.map((r) => (
          <article key={r.incidentId} className="anim-slide-in rounded-xl bg-[var(--surface)] p-3">
            <div className="flex items-center justify-between gap-2">
              <span
                className="rounded-full px-2 py-0.5 text-xs font-medium"
                style={{ backgroundColor: "var(--accent-soft)", color: outcomeColor(r.outcome) }}
              >
                {OUTCOME_LABEL[r.outcome] ?? r.outcome}
              </span>
              <span className="font-mono-data text-xs text-[var(--muted)]">
                {r.durationSeconds.toFixed(0)} s
              </span>
            </div>
            <p className="mt-2 text-sm">{r.summary}</p>
            {r.savedAmount > 0 && (
              <p className="font-mono-data mt-1 text-sm font-semibold text-[var(--accent)]">
                +{r.savedAmount.toLocaleString("fr-FR")} € sauvés
              </p>
            )}
            {r.customerReply && (
              <p className="mt-2 text-xs italic text-[var(--muted)]">« {r.customerReply} »</p>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
