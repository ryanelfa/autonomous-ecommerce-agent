import { useEffect, useRef } from "react";

import type { IncidentView, TraceStep } from "../types";

function StepView({ step }: { step: TraceStep }) {
  switch (step.type) {
    case "thinking":
      return (
        <div className="anim-fade-in flex gap-2">
          <span aria-hidden>🧠</span>
          <p className="text-sm">{step.text}</p>
        </div>
      );
    case "tool_call": {
      const args = JSON.stringify(step.args);
      return (
        <div className="anim-fade-in flex gap-2">
          <span aria-hidden>🔧</span>
          <p className="font-mono-data text-xs text-[var(--accent)]">
            CALL {step.tool}{" "}
            <span className="text-[var(--muted)]">
              {args.length > 120 ? args.slice(0, 120) + "…" : args}
            </span>
          </p>
        </div>
      );
    }
    case "tool_result":
      return (
        <div className="anim-fade-in flex gap-2 pl-6">
          <p className="font-mono-data text-xs" style={{ color: step.ok ? "var(--success)" : "var(--danger)" }}>
            ↳ {step.ok ? "ok" : "ko"} <span className="text-[var(--muted)]">{step.resultSummary}</span>
          </p>
        </div>
      );
    case "customer_reply":
      return (
        <div className="anim-fade-in flex gap-2 rounded-lg bg-[var(--accent-soft)] p-2">
          <span aria-hidden>💬</span>
          <p className="text-sm italic">« {step.text} »</p>
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
    <section className="flex min-h-0 flex-col rounded-xl border border-[var(--accent-soft)] bg-[var(--surface)] p-3">
      <h2 className="pb-2 text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
        Agent — raisonnement en direct
        {incident && <span className="ml-2 normal-case text-[var(--accent)]">{incident.summary}</span>}
      </h2>
      <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto pr-1">
        {steps.length === 0 && (
          <p className="text-sm text-[var(--muted)]">
            L'agent est en veille. Injectez un incident ou laissez la simulation tourner.
          </p>
        )}
        {steps.map((step, index) => (
          <StepView key={index} step={step} />
        ))}
        <div ref={bottomRef} />
      </div>
    </section>
  );
}
