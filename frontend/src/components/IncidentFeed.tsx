import type { IncidentView } from "../types";
import { KIND_LABEL } from "../types";

function severityColor(severity: IncidentView["severity"]): string {
  if (severity === "high") return "var(--danger)";
  if (severity === "medium") return "var(--accent)";
  return "var(--muted)";
}

function statusBadge(incident: IncidentView): { label: string; color: string } {
  switch (incident.status) {
    case "in_progress":
      return { label: "Agent en cours", color: "var(--accent)" };
    case "resolved":
      return { label: "Résolu", color: "var(--success)" };
    case "escalated":
      return { label: "Escaladé", color: "var(--danger)" };
    default:
      return { label: "En attente", color: "var(--muted)" };
  }
}

function age(createdAt: string): string {
  const seconds = Math.max(0, Math.round((Date.now() - new Date(createdAt).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}min`;
  return `${Math.round(seconds / 3600)}h`;
}

export function IncidentCard({ incident, active }: { incident: IncidentView; active: boolean }) {
  const badge = statusBadge(incident);
  return (
    <article
      className={`anim-slide-in rounded-xl bg-[var(--surface)] p-3 ${active ? "anim-pulse-soft border border-[var(--accent)]" : "border border-transparent"}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className="rounded-full px-2 py-0.5 text-xs font-medium"
          style={{ backgroundColor: "var(--accent-soft)", color: severityColor(incident.severity) }}
        >
          {KIND_LABEL[incident.kind]}
        </span>
        <span className="font-mono-data text-xs text-[var(--muted)]">{age(incident.createdAt)}</span>
      </div>
      <p className="mt-2 text-sm font-medium">{incident.summary}</p>
      <p className="mt-1 line-clamp-2 text-xs italic text-[var(--muted)]">
        « {incident.customerMessage} »
      </p>
      <div className="mt-2 flex items-center justify-between text-xs">
        <span className="text-[var(--muted)]">
          {incident.customerName}
          {incident.customerTier === "vip" && (
            <span className="ml-1 text-[var(--accent)]">★ VIP</span>
          )}
          {" · "}
          <span className="font-mono-data">{incident.orderAmount.toFixed(0)} €</span>
        </span>
        <span style={{ color: badge.color }}>{badge.label}</span>
      </div>
    </article>
  );
}

export function IncidentFeed({ incidents, activeId }: { incidents: IncidentView[]; activeId: string | null }) {
  return (
    <section className="flex min-h-0 flex-col rounded-xl bg-[var(--bg)]">
      <h2 className="px-1 pb-2 text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
        Incidents
      </h2>
      <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1">
        {incidents.length === 0 && (
          <p className="px-1 text-sm text-[var(--muted)]">En attente du prochain incident…</p>
        )}
        {incidents.map((incident) => (
          <IncidentCard key={incident.id} incident={incident} active={incident.id === activeId} />
        ))}
      </div>
    </section>
  );
}
