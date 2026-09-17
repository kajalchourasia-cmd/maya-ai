export type JourneyKind = "pregnant" | "postpartum";

export type JourneyPosition = {
  stage: "pregnancy" | "postpartum";
  unit: "week" | "day";
  exact: number | null;
  range_start: number | null;
  range_end: number | null;
};

export type JourneyOverview = {
  label: string; phase: string; progress_start: number; progress_end: number;
  range: boolean; start: number; end: number; progress_label: string;
};

export type GuidanceSection = {
  id: string; title: string; summary: string; bullets: string[];
  reference: string | null; basis: string | null; tone: string;
  food_options: Array<{ id: string; label: string; tags: string[] }>;
  source_links: Array<{ id: string; title: string; url: string; locator: string; jurisdiction: string }>;
};

export type DashboardGuidance = {
  overview_content: StaticOverview;
  version: string; kind: "source_linked_education"; source_checked_on: string;
  journey: JourneyOverview;
  nutrition_focus: string; nutrition_focus_detail: string;
  movement_focus: string; movement_focus_detail: string;
  nutrition: GuidanceSection[]; movement: GuidanceSection[]; this_week: GuidanceSection[];
  symptoms: GuidanceSection[]; wellbeing: GuidanceSection[];
  unmatched_allergies: string[]; food_note: string; reference_note: string;
};

export type StaticFact = {
  title: string; body: string; timing_label?: string;
  source_links: GuidanceSection["source_links"];
};
export type StaticOverview = {
  version: string; source_checked_on: string;
  nutrition: StaticFact; energy: StaticFact; movement: StaticFact;
  baby_fact: StaticFact | null; maternal_fact: StaticFact;
  faq_label: string; faq_month: number | null;
  faqs: Array<{id: string; question: string; answer: string; source_links: GuidanceSection["source_links"]}>;
};

export type OnboardingPayload = {
  session_id?: string;
  name: string;
  journey: JourneyKind;
  timeline_mode: "week" | "month" | "due" | "birth_date";
  timeline_value: string;
  diets: string[];
  allergies: string[];
  symptoms: string[];
  restrictions?: string[];
  use_fictional_sample_record: boolean;
};

export type SafetyCheck = {
  symptom: string;
  route: "urgent" | "needs_clarification" | "non_urgent";
  message: string;
  matched_rule_ids: string[];
  ordinary_generation_allowed: boolean;
  trace_id: string;
  stop_reason: string;
};

export type OnboardingResult = {
  session_id: string;
  name: string;
  journey: JourneyPosition;
  journey_label: string;
  timeline_source: string;
  limitations: string[];
  symptom_checks: SafetyCheck[];
  safety_blocked: boolean;
};

export type EvidenceCitation = {
  evidence_id: string;
  source_id: string;
  source_title: string;
  publisher: string;
  source_type: "public_fixture" | "personal_document_fixture" | "development_source" | "catalogue_education";
  url?: string;
  review_status: string;
  current_status: string;
  journey_applicability: string | null;
  locator: string;
  supporting_passage: string;
  supports_claim: boolean;
};

export type MayaDisplay = {
  schedule?: PlanResponse["schedule"];
  route: string;
  title: string;
  summary: string;
  provenance_sections: Record<string, string[]>;
  citations: EvidenceCitation[];
  uncertainties: string[];
  applied_constraints: string[];
  proposed_actions: string[];
  validation_display_allowed: boolean;
  ordinary_generation_calls: number;
  trace_id?: string | null;
};

export type GovernedCard = {
  card_id: string;
  domain: "health" | "nutrition" | "movement" | "symptoms" | "wellbeing" | "preparation" | "recovery" | "feeding" | "documents";
  title: string;
  summary: string;
  journey_scope: string;
  evidence_ids: string[];
  review_state: "released" | "product_preview" | "awaiting_specialist_review" | "unavailable";
  display_allowed: boolean;
  limitations: string[];
  source_links?: Array<{ title: string; url: string }>;
  suggested_action: string;
};

export type ComparisonPreview = {
  eligible_context: boolean;
  display_mode: "exact_week_editorial_preview" | "range_confirmation" | "postpartum_hidden" | "out_of_range";
  exact_week: number | null;
  range_start: number | null;
  range_end: number | null;
  approval_id: string;
  approval_reviewer: string;
  approval_capacity: string;
  approval_date: string;
  catalogue_version: string;
  catalogue_sha256: string;
  review_state: "editorial_product_preview_only";
  measurement_review_state: "pending";
  image_ownership_or_licence: "pending";
  limitations: string[];
};

export type HomeData = {
  dashboard_guidance: DashboardGuidance;
  name: string;
  journey: JourneyPosition;
  journey_label: string;
  confirmed_context: {
    diets: string[];
    allergies: string[];
    symptoms: string[];
    diets_status: "confirmed" | "not_provided";
    allergies_status: "confirmed" | "not_provided";
    symptoms_status: "reported" | "not_provided";
  };
  kpis: {
    care_records: number;
    upcoming_appointment: string | null;
    plan_state: "not_created" | "created";
  };
  content_cards: GovernedCard[];
  comparison_preview: ComparisonPreview;
  records: Array<{
    document_id: string;
    label: string;
    status: "fictional_sample" | "not_provided";
    summary: string;
    provenance: string;
  }>;
  mode: "demo" | "session";
  fictional: boolean;
  public_release_available: boolean;
};

export type PlanResponse = {
  focus?: "balanced" | "nutrition" | "movement" | "wellbeing";
  display: MayaDisplay;
  schedule: null | {
    save_eligible: boolean;
    items: Array<{
      schedule_item_id: string;
      day: string;
      start: string;
      slot?: string;
      origin?: string;
      end: string;
      domain: string;
      item: string;
      evidence_ids?: string[];
      constraint_notes?: string[];
      optional?: boolean;
    }>;
  };
  save_available: boolean;
  fictional: boolean;
};

export class MayaApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = "MayaApiError";
  }

  get isMissingSession() {
    return this.status === 404 && this.code === "session_not_found";
  }
}

const API_URL = (process.env.NEXT_PUBLIC_MAYA_API_URL || "/api/maya").replace(/\/$/, "");

function apiBaseUrl() {
  if (API_URL.startsWith("/")) return API_URL;
  const url = new URL(API_URL);
  if (typeof window !== "undefined" && ["localhost", "127.0.0.1"].includes(url.hostname)
    && ["localhost", "127.0.0.1"].includes(window.location.hostname)) {
    url.hostname = window.location.hostname;
  }
  return url.toString().replace(/\/$/, "");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, {
      ...init,
      credentials: "include",
      cache: "no-store",
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  } catch {
    throw new MayaApiError(
      "Maya could not reach the local service. Start the API and choose Retry.",
      0,
      "network_unavailable",
    );
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({
      detail: "The Maya service could not complete this request.",
      code: "request_failed",
    })) as { detail?: string | { message?: string; code?: string } | Array<{ msg?: string }>; code?: string };
    const detail = body.detail;
    const message = typeof detail === "string" ? detail
      : Array.isArray(detail) ? detail.map(item => item.msg || "Invalid input").join(". ")
      : detail?.message || `Request failed (${response.status})`;
    const detailCode = detail && typeof detail === "object" && !Array.isArray(detail) ? detail.code : undefined;
    throw new MayaApiError(
      message,
      response.status,
      body.code || detailCode || (response.status === 404 && message.startsWith("Session not found") ? "session_not_found" : "request_failed"),
    );
  }
  return response.json() as Promise<T>;
}

export const mayaApi = {
  createSession: () => request<{ session_id: string }>("/v1/session", { method: "POST" }),
  validateSession: (sessionId: string) =>
    request<{ session_id: string; valid: true; onboarding_complete: boolean }>(
      `/v1/session/${sessionId}`,
    ),
  previewTimeline: (payload: Pick<OnboardingPayload, "journey" | "timeline_mode" | "timeline_value">) => request<JourneyOverview>("/v1/timeline", { method: "POST", body: JSON.stringify(payload) }),
  onboard: (payload: OnboardingPayload) => request<OnboardingResult>("/v1/onboarding", {
    method: "POST", body: JSON.stringify(payload),
  }),
  home: (sessionId: string) => request<HomeData>(`/v1/home/${sessionId}`),
  chat: (sessionId: string, text: string) => request<{ display: MayaDisplay; schedule?: PlanResponse["schedule"]; focus?: PlanResponse["focus"] }>("/v1/chat", {
    method: "POST", body: JSON.stringify({ session_id: sessionId, text }),
  }),
  plan: (sessionId: string, focus: "balanced" | "nutrition" | "movement" | "wellbeing" = "balanced") =>
    request<PlanResponse>("/v1/plan", {
      method: "POST", body: JSON.stringify({ session_id: sessionId, horizon: "week", focus }),
    }),
  addSampleDocument: (sessionId: string) =>
    request<{ accepted: true; document_id: string; label: string; warning: string }>(
      `/v1/demo/document-sample/${sessionId}`,
      { method: "POST" },
    ),
};
