import type { Resolution } from "../types";
import { OUTCOME_LABEL } from "../types";

function outcomeStyle(outcome: string): { bg: string; color: string } {
  if (outcome === "human") return { bg: "var(--danger-soft)", color: "var(--danger)" };
  if (outcome === "refund") return { bg: "#f3f3f3", color: "var(--muted)" };
  return { bg: "var(--success-soft)", color: "var(--success)" };
}

export function ResolutionLog({ resolutions }: { resolutions: Resolution[] }) {
  const done = resolutions.filter((r) => r.outcome !== "");
  return (
    <section className="sfx-console-panel flex min-h-0 flex-col overflow-hidden">
      <h2 className="sfx-panel-header">
        <span className="inline-block h-3.5 w-3.5 rounded-sm bg-[var(--success)] opacity-80" aria-hidden />
        Journal des résolutions
        <span className="ml-auto rounded-full bg-[var(--success-soft)] px-2 py-0.5 text-[0.625rem] font-bold text-[var(--success)]">
          {done.length}
        </span>
      </h2>
      <div className="sfx-panel-body flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto">
        {done.length === 0 && (
          <p className="py-4 text-center text-sm text-[var(--muted)]">
            Aucune résolution pour l&apos;instant.
          </p>
        )}
        {done.map((r) => {
          const style = outcomeStyle(r.outcome);
          return (
            <article key={r.incidentId} className="anim-slide-in sfx-case-card p-3">
              <div className="flex items-center justify-between gap-2">
                <span
                  className="sfx-status-badge"
                  style={{ backgroundColor: style.bg, color: style.color }}
                >
                  {OUTCOME_LABEL[r.outcome] ?? r.outcome}
                </span>
                <span className="font-mono-data text-[0.625rem] text-[var(--muted)]">
                  {r.durationSeconds.toFixed(0)} s
                </span>
              </div>
              <p className="mt-2 text-sm font-medium leading-snug text-[var(--accent-strong)]">
                {r.summary}
              </p>
              {r.savedAmount > 0 && (
                <p className="font-mono-data mt-1.5 inline-flex items-center rounded border border-[var(--accent-soft)] bg-[var(--accent-soft)] px-2 py-0.5 text-xs font-semibold text-[var(--accent)]">
                  +{r.savedAmount.toLocaleString("fr-FR")} € sauvés
                </p>
              )}
              {r.customerReply && (
                <p className="mt-2 border-l-2 border-[var(--border)] pl-2 text-xs italic text-[var(--muted)]">
                  « {r.customerReply} »
                </p>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
