import { useEffect, useRef } from "react";

import type { IncidentView, TraceStep } from "../types";

function StepView({ step }: { step: TraceStep }) {
  switch (step.type) {
    case "thinking":
      return (
        <div className="sfx-timeline-item anim-fade-in">
          <span className="sfx-timeline-marker sfx-timeline-marker-thinking" aria-hidden />
          <div className="sfx-timeline-content">
            <p className="sfx-timeline-label">Raisonnement</p>
            <p className="mt-0.5 text-sm leading-relaxed text-[var(--text)]">{step.text}</p>
          </div>
        </div>
      );
    case "tool_call": {
      const args = JSON.stringify(step.args);
      return (
        <div className="sfx-timeline-item anim-fade-in">
          <span className="sfx-timeline-marker sfx-timeline-marker-tool" aria-hidden />
          <div className="sfx-timeline-content">
            <p className="sfx-timeline-label">Action agent</p>
            <p className="font-mono-data mt-0.5 text-xs text-[var(--accent-strong)]">
              {step.tool}
            </p>
            <p className="font-mono-data mt-1 text-[0.6875rem] leading-relaxed text-[var(--muted)]">
              {args.length > 120 ? args.slice(0, 120) + "…" : args}
            </p>
          </div>
        </div>
      );
    }
    case "tool_result":
      return (
        <div className="sfx-timeline-item anim-fade-in pl-0">
          <span
            className={`sfx-timeline-marker ${step.ok ? "sfx-timeline-marker-result-ok" : "sfx-timeline-marker-result-ko"}`}
            aria-hidden
          />
          <div
            className="sfx-timeline-content"
            style={{
              borderColor: step.ok ? "var(--success-soft)" : "var(--danger-soft)",
              backgroundColor: step.ok ? "var(--success-soft)" : "var(--danger-soft)",
            }}
          >
            <p className="sfx-timeline-label">{step.ok ? "Résultat" : "Erreur"}</p>
            <p
              className="font-mono-data mt-0.5 text-xs font-medium"
              style={{ color: step.ok ? "var(--success)" : "var(--danger)" }}
            >
              {step.tool} — {step.ok ? "succès" : "échec"}
            </p>
            <p className="mt-0.5 text-xs text-[var(--muted)]">{step.resultSummary}</p>
          </div>
        </div>
      );
    case "customer_reply":
      return (
        <div className="sfx-timeline-item anim-fade-in">
          <span className="sfx-timeline-marker sfx-timeline-marker-reply" aria-hidden />
          <div className="sfx-timeline-content sfx-timeline-content-reply">
            <p className="sfx-timeline-label">Réponse client</p>
            <p className="mt-0.5 text-sm italic leading-relaxed text-[var(--accent-strong)]">
              « {step.text} »
            </p>
          </div>
        </div>
      );
  }
}

export function AgentTrace({ steps, incident }: { steps: TraceStep[]; incident: IncidentView | null }) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [steps.length]);

  return (
    <section className="sfx-console-panel flex min-h-0 flex-col overflow-hidden border-[var(--accent)]/20">
      <h2 className="sfx-panel-header">
        <span className="inline-block h-3.5 w-3.5 rounded-sm bg-[var(--accent)]" aria-hidden />
        Fil d&apos;activité agent
        {incident && (
          <span className="ml-1 truncate font-normal normal-case tracking-normal text-[var(--accent)]">
            — {incident.summary}
          </span>
        )}
        {incident && (
          <span className="ml-auto shrink-0 rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-[0.625rem] font-bold text-[var(--accent)]">
            En cours
          </span>
        )}
      </h2>
      <div className="sfx-panel-body flex min-h-0 flex-1 flex-col overflow-y-auto">
        {steps.length === 0 && (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 py-8 text-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-full border border-[var(--border)] bg-[var(--surface-alt)]">
              <span className="text-lg text-[var(--muted)]" aria-hidden>◎</span>
            </div>
            <p className="max-w-xs text-sm text-[var(--muted)]">
              L&apos;agent est en veille. Injectez un incident ou laissez la simulation tourner.
            </p>
          </div>
        )}
        {steps.length > 0 && (
          <div className="sfx-timeline">
            {steps.map((step, index) => (
              <StepView key={index} step={step} />
            ))}
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}
