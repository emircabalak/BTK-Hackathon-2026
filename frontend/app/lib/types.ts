// Mirrors backend payloads from app/api/main.py + app/agents/orchestrator.py

export type AgentName =
  | "orchestrator"
  | "scout"
  | "critic"
  | "verifier"
  | "negotiator"
  | "decider";

export type Speaker = "negotiator" | "seller" | "system";

export type FinalistSummary = {
  product_id: string;
  title: string;
  price: number;
  rating: number;
  review_count: number;
  image_url?: string;
  seller_name: string;
  seller_rating: number;
  seller_sales: number;
};

export type AgentEvent = {
  type: "event";
  agent: AgentName;
  event: string;
  message?: string;
  product_id?: string;
  speaker?: Speaker;
  intent?: string;
  offered_price?: number | null;
  extras?: string[];
  internal_thought?: string;
  fake_ratio?: number;
  real_sentiment?: number;
  red_flags?: string[];
  authenticity?: number;
  flags?: string[];
  trust_score?: number;
  candidates?: string[];
  finalists?: FinalistSummary[];
  title?: string;
  status?: string;
  savings_tl?: number;
  savings_pct?: number;
  winner?: string;
  headline?: string;
  elapsed_ms?: number;
  ts?: number;
};

export type FinalistState = {
  summary: FinalistSummary;
  fake_ratio?: number;
  real_sentiment?: number;
  red_flags?: string[];
  authenticity?: number;
  flags?: string[];
  trust_score?: number;
  critic_done: boolean;
  verifier_done: boolean;
};

export type FinalMessage = {
  type: "final";
  result: PipelineResult;
};

export type DoneMessage = { type: "done" };
export type ErrorMessage = { type: "error"; message: string };

export type ServerMessage = AgentEvent | FinalMessage | DoneMessage | ErrorMessage;

// Backend Pydantic shapes (loose typing on purpose — we only access subset)

export type Seller = {
  seller_id: string;
  name: string;
  rating: number;
  total_sales: number;
  response_style?: string;
};

export type Product = {
  product_id: string;
  title: string;
  price: number;
  currency: string;
  marketplace?: string;
  url?: string;
  image_url?: string;
  description?: string;
  category?: string;
  rating: number;
  review_count: number;
  seller: Seller;
};

export type Turn = {
  speaker: Speaker;
  message: string;
  intent: string;
  offered_price?: number | null;
  internal_thought?: string;
  extras?: string[];
};

export type NegotiationOutcome = {
  status: "agreement" | "walk_away" | "no_movement" | "max_turns";
  original_price: number;
  final_price: number;
  savings_tl: number;
  savings_pct: number;
  extras: string[];
  turn_count: number;
  transcript: Turn[];
  summary: string;
};

export type CriticReport = {
  product_id: string;
  fake_ratio: number;
  real_sentiment: number;
  topics: { topic: string; score: number; sample?: string }[];
  red_flags: string[];
  representative_quote: string;
  confidence: number;
};

export type VerifierReport = {
  product_id: string;
  brand_consistency: number;
  spec_consistency: number;
  seller_score: number;
  overall_authenticity: number;
  flags: string[];
};

export type TrustBreakdown = {
  fake_ratio_contribution: number;
  authenticity_contribution: number;
  sentiment_contribution: number;
  seller_contribution: number;
};

export type FinalCard = {
  winner: Product;
  trust_score: number;
  trust_breakdown: TrustBreakdown;
  negotiation: NegotiationOutcome | null;
  headline: string;
  explanation: string;
  alternatives: Product[];
  buy_link: string;
};

export type PipelineResult = {
  query: string;
  scout: { parsed: { category: string; budget_max: number | null; persona: string }; candidates: Product[]; log: string[] };
  critic: Record<string, CriticReport>;
  verifier: Record<string, VerifierReport>;
  negotiation: NegotiationOutcome | null;
  final: FinalCard | null;
};

// Derived UI state per agent panel

export type AgentStatus = "pending" | "running" | "done";

export type AgentLogLine = {
  text: string;
  kind: "thinking" | "result" | "warn";
};

export type AgentState = {
  status: AgentStatus;
  logs: AgentLogLine[];
};

export type SceneState = "idle" | "running" | "done" | "error";

export type AppState = {
  scene: SceneState;
  query: string;
  agents: Record<AgentName, AgentState>;
  candidates: string[];
  finalists: Record<string, FinalistState>;
  finalistOrder: string[];
  winnerId: string | null;
  negotiationTurns: Turn[];
  negotiationStatus: NegotiationOutcome["status"] | null;
  final: FinalCard | null;
  errorMessage: string | null;
  startedAt: number | null;
  finishedAt: number | null;
};
