import type { IncidentView } from "../types";
import { KIND_LABEL } from "../types";

function severityStyle(severity: IncidentView["severity"]): { bg: string; color: string } {
  if (severity === "high") return { bg: "var(--danger-soft)", color: "var(--danger)" };
  if (severity === "medium") return { bg: "var(--warning-soft)", color: "#b65c02" };
  return { bg: "var(--accent-soft)", color: "var(--muted)" };
}

function statusBadge(incident: IncidentView): { label: string; bg: string; color: string } {
  switch (incident.status) {
    case "in_progress":
      return { label: "Agent en cours", bg: "var(--accent-soft)", color: "var(--accent)" };
    case "resolved":
      return { label: "Résolu", bg: "var(--success-soft)", color: "var(--success)" };
    case "escalated":
      return { label: "Escaladé", bg: "var(--danger-soft)", color: "var(--danger)" };
    default:
      return { label: "En attente", bg: "#f3f3f3", color: "var(--muted)" };
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
  const severity = severityStyle(incident.severity);
  return (
    <article
      className={`anim-slide-in sfx-case-card p-3 ${active ? "sfx-case-card-active anim-pulse-soft" : ""}`}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span
            className="sfx-status-badge"
            style={{ backgroundColor: severity.bg, color: severity.color }}
          >
            {KIND_LABEL[incident.kind]}
          </span>
          <span className="font-mono-data text-[0.625rem] text-[var(--muted)]">
            #{incident.id.slice(0, 8)}
          </span>
        </div>
        <span className="font-mono-data text-[0.625rem] text-[var(--muted)]">{age(incident.createdAt)}</span>
      </div>
      <p className="mt-2 text-sm font-semibold leading-snug text-[var(--accent-strong)]">
        {incident.summary}
      </p>
      <p className="mt-1 line-clamp-2 text-xs italic text-[var(--muted)]">
        « {incident.customerMessage} »
      </p>
      <div className="mt-2.5 flex items-center justify-between border-t border-[var(--border)] pt-2 text-xs">
        <span className="text-[var(--muted)]">
          {incident.customerName}
          {incident.customerTier === "vip" && (
            <span className="ml-1 font-semibold text-[var(--accent)]">★ VIP</span>
          )}
          {" · "}
          <span className="font-mono-data font-medium text-[var(--accent-strong)]">
            {incident.orderAmount.toFixed(0)} €
          </span>
        </span>
        <span
          className="sfx-status-badge"
          style={{ backgroundColor: badge.bg, color: badge.color }}
        >
          {badge.label}
        </span>
      </div>
    </article>
  );
}

export function IncidentFeed({ incidents, activeId }: { incidents: IncidentView[]; activeId: string | null }) {
  return (
    <section className="sfx-console-panel flex min-h-0 flex-col overflow-hidden">
      <h2 className="sfx-panel-header">
        <span className="inline-block h-3.5 w-3.5 rounded-sm bg-[var(--accent)] opacity-80" aria-hidden />
        File d&apos;incidents
        <span className="ml-auto rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[0.625rem] font-bold text-[var(--accent)]">
          {incidents.length}
        </span>
      </h2>
      <div className="sfx-panel-body flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto">
        {incidents.length === 0 && (
          <p className="py-4 text-center text-sm text-[var(--muted)]">
            En attente du prochain incident…
          </p>
        )}
        {incidents.map((incident) => (
          <IncidentCard key={incident.id} incident={incident} active={incident.id === activeId} />
        ))}
      </div>
    </section>
  );
}
