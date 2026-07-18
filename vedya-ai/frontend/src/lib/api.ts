const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface VignetteInput {
  free_text?: string;
  symptoms?: string[];
  rogas?: string[];
  comorbidities?: string[];
  age_band?: string;
  pregnancy?: boolean;
  prakriti?: string;
  kalpana_filter?: string;
  top_k?: number;
  conversation_id?: string;
  locale?: string;
  follow_up?: boolean;
}

export interface RankFeatures {
  primary_indication_match: number;
  secondary_indication_match: number;
  property_fit: number;
  citation_bonus: number;
  contraindication_penalty: number;
  medium_penalty: number;
  total_score: number;
}

export interface SafetyViolation {
  rule_id: string;
  severity: "HARD_EXCLUDE" | "WARN";
  message: string;
  classical_basis?: string;
}

export interface ReferenceCard {
  ref_id: string;
  work: string;
  sthana?: string;
  chapter?: string;
  verse_id?: string;
  excerpt_text?: string;
}

export interface ExplanationClaim {
  text: string;
  ref_ids: string[];
}

export interface Explanation {
  summary: string;
  claims: ExplanationClaim[];
  llm_used: boolean;
  template_fallback: boolean;
}

export interface ResolvedConcept {
  surface_form: string;
  canonical_name: string;
  concept_id: string;
  concept_type: string;
  synonyms_used?: string[];
}

export interface SenseDisambiguation {
  term: string;
  default_dravya: string;
  resolved_dravya: string;
  context_yoga: string;
  explanation: string;
}

export interface RecommendedFormulation {
  rank: number;
  yoga_id: string;
  yoga_name: string;
  kalpana?: string;
  category?: string;
  score: number;
  rank_features: RankFeatures;
  safety_violations: SafetyViolation[];
  hard_excluded: boolean;
  primary_indications: string[];
  secondary_indications: string[];
  references: ReferenceCard[];
  explanation?: Explanation;
  differentiation_note?: string;
  dosage?: string;
  anupana?: string;
  coverage_note?: string;
}

export interface RecommendationResponse {
  trace_id: string;
  vignette_summary: string;
  resolved_concepts: ResolvedConcept[];
  sense_disambiguations: SenseDisambiguation[];
  unresolved_terms: string[];
  safety_alerts: SafetyViolation[];
  results: RecommendedFormulation[];
  total_candidates: number;
  excluded_count: number;
  warned_count: number;
  corpus_version: string;
  llm_used: boolean;
  coverage_note?: string;
  conversation_id?: string | null;
  disclaimer: string;
}

export interface PresetVignette {
  id: string;
  label: string;
  description: string;
  vignette: VignetteInput;
}

export interface CompareResult {
  yoga_a: {
    yoga_id: string;
    yoga_name: string;
    kalpana?: string;
    primary_indications: string[];
    secondary_indications: string[];
    ingredients: string[];
    references: ReferenceCard[];
    safety_violations: SafetyViolation[];
    score: number;
    differentiation_note?: string;
  };
  yoga_b: {
    yoga_id: string;
    yoga_name: string;
    kalpana?: string;
    primary_indications: string[];
    secondary_indications: string[];
    ingredients: string[];
    references: ReferenceCard[];
    safety_violations: SafetyViolation[];
    score: number;
    differentiation_note?: string;
  };
  discrimination_explanation?: Explanation;
  winner_yoga_id?: string;
  winner_reason?: string;
}

export interface FormulationDetail {
  yoga_id: string;
  name: string;
  kalpana?: string;
  medium_class?: string;
  category?: string;
  dosage?: string;
  anupana?: string;
  reference_text?: string;
  differentiation_note?: string;
  ambiguity_notes?: Record<string, string>;
  external_only: boolean;
  ingredients: Array<{
    name: string;
    sense_override?: string;
    botanical_name?: string;
    english_name?: string;
    rasa?: string[];
    guna?: string[];
    virya?: string;
    vipaka?: string;
    prabhav?: string[];
    pacify?: string[];
    aggravate?: string[];
  }>;
  references: ReferenceCard[];
}

export interface AuthUser {
  user_id: string;
  email: string;
  display_name?: string | null;
  preferred_locale: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

function authHeaders(): HeadersInit {
  if (typeof window === "undefined") return { "Content-Type": "application/json" };
  const token = localStorage.getItem("vedya_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json();
}

export const api = {
  getPresets: () => apiFetch<PresetVignette[]>("/presets"),

  runPreset: (presetId: string) =>
    apiFetch<RecommendationResponse>(`/presets/${presetId}`),

  recommend: (inp: VignetteInput) =>
    apiFetch<RecommendationResponse>("/recommend", {
      method: "POST",
      body: JSON.stringify(inp),
    }),

  getFormulation: (yogaId: string) =>
    apiFetch<FormulationDetail>(`/formulation/${yogaId}`),

  compare: (yogaAId: string, yogaBId: string, inp?: VignetteInput) =>
    apiFetch<CompareResult>(
      `/compare?yoga_a_id=${yogaAId}&yoga_b_id=${yogaBId}`,
      inp ? { method: "POST", body: JSON.stringify(inp) } : { method: "POST", body: JSON.stringify({}) }
    ),

  synonymMap: (concept: string) =>
    apiFetch<{ concept_id: string; canonical_name: string; type: string; synonyms: string[] }>(
      `/synonym-map/${encodeURIComponent(concept)}`
    ),

  health: () =>
    apiFetch<{ status: string; db_connected: boolean; llm_enabled: boolean; corpus_version: string; formulation_count: number }>("/health"),

  signup: (body: { email: string; password: string; display_name?: string; preferred_locale?: string }) =>
    apiFetch<AuthResponse>("/auth/signup", { method: "POST", body: JSON.stringify(body) }),

  login: (body: { email: string; password: string }) =>
    apiFetch<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(body) }),

  me: () => apiFetch<AuthUser>("/auth/me"),

  listConversations: () =>
    apiFetch<Array<{ conversation_id: string; title: string; locale: string; updated_at?: string }>>(
      "/conversations"
    ),

  getConversation: (id: string) =>
    apiFetch<{
      conversation: { conversation_id: string; title: string };
      messages: Array<{ role: string; content_text: string; payload?: RecommendationResponse }>;
    }>(`/conversations/${id}`),
};
