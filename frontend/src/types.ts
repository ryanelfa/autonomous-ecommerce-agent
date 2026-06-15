// Shared types: mirror of the WebSocket protocol and the GraphQL shapes the UI consumes.

export type IncidentKind =
  | "out_of_stock"
  | "payment_failed"
  | "lost_parcel"
  | "vip_complaint"
  | "return_request";

export type IncidentStatus = "open" | "in_progress" | "resolved" | "escalated";

export interface IncidentView {
  id: string;
  kind: IncidentKind;
  severity: "low" | "medium" | "high";
  summary: string;
  customerMessage: string;
  status: IncidentStatus;
  createdAt: string;
  resolutionKind: string | null;
  savedAmount: number;
  orderId: string;
  orderAmount: number;
  productName: string;
  customerName: string;
  customerTier: "standard" | "vip";
}

export interface Kpis {
  incidentsResolved: number;
  incidentsEscalated: number;
  savedRevenue: number;
  escalationRate: number;
  avgResolutionSeconds: number;
  openIncidents: number;
}

export interface BrandColors {
  background: string;
  surface: string;
  accent: string;
  accentSoft: string;
  text: string;
  muted: string;
  danger: string;
  success: string;
}

export interface Brand {
  id: string;
  name: string;
  tagline: string;
  logoSvg: string;
  colors: BrandColors;
  voice: string;
}

export type TraceStep =
  | { type: "thinking"; text: string }
  | { type: "tool_call"; tool: string; args: Record<string, unknown> }
  | { type: "tool_result"; tool: string; ok: boolean; resultSummary: string }
  | { type: "customer_reply"; text: string };

export interface Resolution {
  incidentId: string;
  summary: string;
  outcome: string; // refund | substitute | voucher | info | human
  savedAmount: number;
  durationSeconds: number;
  customerReply: string;
}

export interface WsMessage {
  type:
    | "order_created"
    | "incident_created"
    | "agent_started"
    | "agent_thinking"
    | "tool_call"
    | "tool_result"
    | "customer_reply"
    | "agent_finished"
    | "kpi_update"
    | "brand_changed"
    | "sim_state";
  ts: string;
  payload: Record<string, unknown>;
}

export const KIND_LABEL: Record<IncidentKind, string> = {
  out_of_stock: "Rupture de stock",
  payment_failed: "Paiement échoué",
  lost_parcel: "Colis perdu",
  vip_complaint: "VIP mécontente",
  return_request: "Demande de retour",
};

export const OUTCOME_LABEL: Record<string, string> = {
  refund: "Remboursée",
  substitute: "Substitution",
  voucher: "Bon d'achat",
  info: "Information",
  human: "Escaladée",
};
