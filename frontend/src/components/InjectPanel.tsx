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
    <footer className="sfx-console-panel relative overflow-visible">
      <div className="sfx-panel-header">
        <span className="inline-block h-3.5 w-3.5 rounded-sm bg-[var(--warning)] opacity-80" aria-hidden />
        Injecter un incident — cassez la prod, l&apos;agent répare
      </div>
      <div className="sfx-panel-body">
        <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
          {KINDS.map((kind) => (
            <button
              key={kind}
              onClick={() => handle(kind)}
              className="sfx-button px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-1"
            >
              {KIND_LABEL[kind]}
            </button>
          ))}
        </div>
      </div>
      {toast && (
        <div className="anim-fade-in absolute -top-2 right-4 z-10 rounded border border-[var(--accent)] bg-[var(--accent)] px-3 py-1.5 text-xs font-medium text-white shadow-md">
          {toast}
        </div>
      )}
    </footer>
  );
}
