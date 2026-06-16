import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@apollo/client";

import { BOOTSTRAP_QUERY, INJECT_INCIDENT, SET_BRAND, SET_SIMULATION } from "./apollo";
import { applyBrandTheme } from "./theme";
import type {
  Brand, IncidentKind, IncidentView, Kpis, Resolution, TraceStep, WsMessage,
} from "./types";
import { useWarRoomSocket } from "./ws";
import { AgentTrace } from "./components/AgentTrace";
import { IncidentFeed } from "./components/IncidentFeed";
import { InjectPanel } from "./components/InjectPanel";
import { KpiStrip } from "./components/KpiStrip";
import { ResolutionLog } from "./components/ResolutionLog";
import { TopBar } from "./components/TopBar";

const MAX_FEED = 30;
const MAX_RESOLUTIONS = 20;
const MAX_TRACE = 60;

interface GqlIncident {
  id: string; kind: string; severity: string; summary: string; customerMessage: string;
  status: string; createdAt: string; resolutionKind: string | null; savedAmount: number;
  order: { id: string; amount: number; product: { name: string }; customer: { name: string; tier: string } };
}

interface WsIncidentPayload {
  id: string; kind: IncidentView["kind"]; severity: IncidentView["severity"];
  summary: string; customerMessage: string; status: IncidentView["status"];
  createdAt: string; resolutionKind: string | null; savedAmount: number;
  order: {
    id: string; amount: number; status: string;
    productName: string; customerName: string; customerTier: string;
  } | null;
}

function fromGql(i: GqlIncident): IncidentView {
  return {
    id: i.id,
    kind: i.kind.toLowerCase() as IncidentView["kind"],
    severity: i.severity as IncidentView["severity"],
    summary: i.summary,
    customerMessage: i.customerMessage,
    status: i.status.toLowerCase() as IncidentView["status"],
    createdAt: i.createdAt,
    resolutionKind: i.resolutionKind,
    savedAmount: i.savedAmount,
    orderId: i.order.id,
    orderAmount: i.order.amount,
    productName: i.order.product.name,
    customerName: i.order.customer.name,
    customerTier: i.order.customer.tier as IncidentView["customerTier"],
  };
}

function fromWs(p: WsIncidentPayload): IncidentView {
  return {
    id: p.id, kind: p.kind, severity: p.severity, summary: p.summary,
    customerMessage: p.customerMessage, status: p.status, createdAt: p.createdAt,
    resolutionKind: p.resolutionKind, savedAmount: p.savedAmount,
    orderId: p.order?.id ?? "?",
    orderAmount: p.order?.amount ?? 0,
    productName: p.order?.productName ?? "?",
    customerName: p.order?.customerName ?? "?",
    customerTier: (p.order?.customerTier ?? "standard") as IncidentView["customerTier"],
  };
}

export default function App() {
  const { data, loading } = useQuery(BOOTSTRAP_QUERY);
  const [injectIncident] = useMutation(INJECT_INCIDENT);
  const [setBrandMutation] = useMutation(SET_BRAND);
  const [setSimulation] = useMutation(SET_SIMULATION);

  const [incidents, setIncidents] = useState<IncidentView[]>([]);
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [brandList, setBrandList] = useState<{ id: string; name: string }[]>([]);
  const [simRunning, setSimRunning] = useState(true);
  const [activeIncidentId, setActiveIncidentId] = useState<string | null>(null);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [resolutions, setResolutions] = useState<Resolution[]>([]);
  const [savedFlash, setSavedFlash] = useState(0); // increments to retrigger the accent glow

  // Bootstrap from GraphQL
  useEffect(() => {
    if (!data) return;
    setIncidents((data.incidents as GqlIncident[]).map(fromGql));
    setKpis(data.kpis as Kpis);
    setBrand(data.activeBrand as Brand);
    setBrandList(data.brands as { id: string; name: string }[]);
    setSimRunning(data.simulationRunning as boolean);
    applyBrandTheme(data.activeBrand as Brand);
  }, [data]);

  const patchIncident = useCallback((id: string, patch: Partial<IncidentView>) => {
    setIncidents((prev) => prev.map((i) => (i.id === id ? { ...i, ...patch } : i)));
  }, []);

  const pushTrace = useCallback((step: TraceStep) => {
    setTrace((prev) => [...prev, step].slice(-MAX_TRACE));
  }, []);

  const onMessage = useCallback((msg: WsMessage) => {
    switch (msg.type) {
      case "incident_created": {
        const view = fromWs(msg.payload as unknown as WsIncidentPayload);
        setIncidents((prev) => [view, ...prev].slice(0, MAX_FEED));
        break;
      }
      case "agent_started": {
        const incidentId = msg.payload.incidentId as string;
        setActiveIncidentId(incidentId);
        setTrace([]);
        patchIncident(incidentId, { status: "in_progress" });
        break;
      }
      case "agent_thinking":
        pushTrace({ type: "thinking", text: msg.payload.text as string });
        break;
      case "tool_call":
        pushTrace({
          type: "tool_call",
          tool: msg.payload.tool as string,
          args: msg.payload.args as Record<string, unknown>,
        });
        break;
      case "tool_result":
        pushTrace({
          type: "tool_result",
          tool: msg.payload.tool as string,
          ok: msg.payload.ok as boolean,
          resultSummary: msg.payload.resultSummary as string,
        });
        break;
      case "customer_reply": {
        const incidentId = msg.payload.incidentId as string;
        const text = msg.payload.text as string;
        pushTrace({ type: "customer_reply", text });
        setResolutions((prev) => {
          const existing = prev.find((r) => r.incidentId === incidentId);
          if (existing) {
            return prev.map((r) => (r.incidentId === incidentId ? { ...r, customerReply: text } : r));
          }
          const placeholder: Resolution = {
            incidentId, summary: "", outcome: "", savedAmount: 0,
            durationSeconds: 0, customerReply: text,
          };
          return [placeholder, ...prev].slice(0, MAX_RESOLUTIONS);
        });
        break;
      }
      case "agent_finished": {
        const incidentId = msg.payload.incidentId as string;
        const outcome = msg.payload.outcome as string;
        const saved = msg.payload.savedAmount as number;
        const duration = msg.payload.durationSeconds as number;
        patchIncident(incidentId, {
          status: outcome === "human" ? "escalated" : "resolved",
          resolutionKind: outcome,
          savedAmount: saved,
        });
        setIncidents((current) => {
          const incident = current.find((i) => i.id === incidentId);
          setResolutions((prev) => {
            const base = prev.find((r) => r.incidentId === incidentId);
            const entry: Resolution = {
              incidentId,
              summary: incident?.summary ?? incidentId,
              outcome,
              savedAmount: saved,
              durationSeconds: duration,
              customerReply: base?.customerReply ?? "",
            };
            const rest = prev.filter((r) => r.incidentId !== incidentId);
            return [entry, ...rest].slice(0, MAX_RESOLUTIONS);
          });
          return current;
        });
        if (saved > 0) setSavedFlash((n) => n + 1);
        setActiveIncidentId(null);
        break;
      }
      case "kpi_update":
        setKpis(msg.payload as unknown as Kpis);
        break;
      case "brand_changed": {
        const next = msg.payload as unknown as Brand;
        setBrand(next);
        applyBrandTheme(next);
        break;
      }
      case "sim_state":
        setSimRunning(msg.payload.running as boolean);
        break;
      default:
        break;
    }
  }, [patchIncident, pushTrace]);

  const { connected } = useWarRoomSocket(onMessage);

  const activeIncident = useMemo(
    () => incidents.find((i) => i.id === activeIncidentId) ?? null,
    [incidents, activeIncidentId],
  );

  const handleInject = (kind: IncidentKind) => {
    void injectIncident({ variables: { kind: kind.toUpperCase() } });
  };
  const handleBrandChange = (brandId: string) => {
    void setBrandMutation({ variables: { brandId } });
  };
  const handleToggleSim = () => {
    void setSimulation({ variables: { running: !simRunning } });
    setSimRunning((s) => !s);
  };

  if (loading || !brand || !kpis) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 text-[var(--muted)]">
        <div
          className="anim-spin-slow h-8 w-8 rounded-full border-2 border-[var(--border)] border-t-[var(--accent)]"
          aria-hidden
        />
        <p className="text-sm font-medium text-[var(--accent-strong)]">Connexion à la War Room…</p>
      </div>
    );
  }

  return (
    <div className="mx-auto flex h-screen max-w-[1520px] flex-col gap-3 p-3 md:p-4">
      <TopBar
        brand={brand}
        brands={brandList}
        simRunning={simRunning}
        wsConnected={connected}
        onBrandChange={handleBrandChange}
        onToggleSim={handleToggleSim}
      />
      <KpiStrip kpis={kpis} savedFlash={savedFlash} />
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)_minmax(0,1fr)]">
        <IncidentFeed incidents={incidents} activeId={activeIncidentId} />
        <AgentTrace steps={trace} incident={activeIncident} />
        <ResolutionLog resolutions={resolutions} />
      </div>
      <InjectPanel onInject={handleInject} />
    </div>
  );
}
