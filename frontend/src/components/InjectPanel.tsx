import { useState } from "react";

import type { IncidentKind } from "../types";
import { KIND_LABEL } from "../types";

const KINDS: IncidentKind[] = [
  "out_of_stock",
  "payment_failed",
  "lost_parcel",
  "vip_complaint",
  "return_request",
];

export function InjectPanel({ onInject }: { onInject: (kind: IncidentKind) => void }) {
  const [toast, setToast] = useState<string | null>(null);

  const handle = (kind: IncidentKind) => {
    onInject(kind);
    setToast(`Incident injecté : ${KIND_LABEL[kind]}`);
    setTimeout(() => setToast(null), 2500);
  };

  return (
    <footer className="relative rounded-xl bg-[var(--surface)] p-3">
      <p className="pb-2 text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
        Injecter un incident — cassez la prod, l'agent répare
      </p>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
        {KINDS.map((kind) => (
          <button
            key={kind}
            onClick={() => handle(kind)}
            className="rounded-lg border border-[var(--accent-soft)] px-3 py-2 text-sm font-medium transition-colors hover:border-[var(--accent)] hover:bg-[var(--accent-soft)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
          >
            {KIND_LABEL[kind]}
          </button>
        ))}
      </div>
      {toast && (
        <div className="anim-fade-in absolute -top-10 right-3 rounded-lg bg-[var(--accent-soft)] px-3 py-1.5 text-xs">
          {toast}
        </div>
      )}
    </footer>
  );
}
