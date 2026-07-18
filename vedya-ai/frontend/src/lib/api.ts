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
  primary_indications?: string[];
  secondary_indications?: string[];
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
  role?: string;
}

export interface AdminStats {
  corpus_version: string;
  llm_enabled: boolean;
  counts: Record<string, number>;
  top_recommended: Array<{ name: string; count: number }>;
}

export interface AdminUserRow {
  user_id: string;
  email: string;
  display_name?: string | null;
  role: string;
  is_active: boolean;
  created_at?: string | null;
  last_login_at?: string | null;
  conversations: number;
  cases_run: number;
}

export interface AdminTrace {
  trace_id: string;
  created_at?: string | null;
  vignette_summary?: string | null;
  top_yoga?: string | null;
  llm_used: boolean;
  safety_hits: string[];
  user_email?: string | null;
}

export interface AskPassage {
  ref_id: string;
  work: string;
  sthana?: string;
  chapter?: string;
  verse_id?: string;
  excerpt: string;
  score: number;
}

export interface AskConcept {
  canonical_name: string;
  surface_form: string;
  type: string;
  synonyms: string[];
}

export interface AskFormulation {
  yoga_id: string;
  name: string;
  kalpana?: string;
  primary_hits: number;
  total_hits: number;
  matched_conditions: string[];
}

export interface AskResponse {
  question: string;
  answer: string;
  llm_used: boolean;
  concepts: AskConcept[];
  passages: AskPassage[];
  formulations: AskFormulation[];
  coverage: "corpus" | "none";
  disclaimer: string;
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
  getPresets: (locale?: string) =>
    apiFetch<PresetVignette[]>(`/presets${locale ? `?locale=${locale}` : ""}`),

  runPreset: (presetId: string, locale?: string) =>
    apiFetch<RecommendationResponse>(
      `/presets/${presetId}${locale ? `?locale=${encodeURIComponent(locale)}` : ""}`
    ),

  translate: (texts: string[], target_locale: string, source_locale = "en") =>
    apiFetch<{
      translations: string[];
      target_locale: string;
      source_locale: string;
      provider: string;
    }>("/translate", {
      method: "POST",
      body: JSON.stringify({ texts, target_locale, source_locale }),
    }),

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

  voiceStatus: () =>
    apiFetch<{
      configured: boolean;
      tts_model: string;
      stt_model: string;
      default_voice_id: string;
      features: string[];
    }>("/voice/status"),

  voiceTts: async (text: string, locale = "en") => {
    const form = new FormData();
    form.append("text", text);
    form.append("locale", locale);
    const token = typeof window !== "undefined" ? localStorage.getItem("vedya_token") : null;
    const res = await fetch(`${API_BASE}/voice/tts`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) throw new Error(`TTS ${res.status}: ${await res.text()}`);
    return res.blob();
  },

  voiceListenRecommendation: async (opts: {
    yogaName: string;
    summary?: string;
    kalpana?: string;
    winnerReason?: string;
    locale?: string;
  }) => {
    const form = new FormData();
    form.append("yoga_name", opts.yogaName);
    form.append("summary", opts.summary || "");
    form.append("kalpana", opts.kalpana || "");
    form.append("winner_reason", opts.winnerReason || "");
    form.append("locale", opts.locale || "en");
    const token = typeof window !== "undefined" ? localStorage.getItem("vedya_token") : null;
    const res = await fetch(`${API_BASE}/voice/listen-recommendation`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) throw new Error(`Listen ${res.status}: ${await res.text()}`);
    return res.blob();
  },

  voiceStt: async (blob: Blob, locale = "en") => {
    const form = new FormData();
    form.append("file", blob, "vignette.webm");
    form.append("locale", locale);
    const token = typeof window !== "undefined" ? localStorage.getItem("vedya_token") : null;
    const res = await fetch(`${API_BASE}/voice/stt`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    if (!res.ok) throw new Error(`STT ${res.status}: ${await res.text()}`);
    return res.json() as Promise<{ text: string; language_code?: string }>;
  },

  ask: (question: string, locale = "en") =>
    apiFetch<AskResponse>("/ask", {
      method: "POST",
      body: JSON.stringify({ question, locale }),
    }),

  adminStats: () => apiFetch<AdminStats>("/admin/stats"),

  adminUsers: () => apiFetch<{ users: AdminUserRow[] }>("/admin/users"),

  adminTraces: (limit = 25) => apiFetch<{ traces: AdminTrace[] }>(`/admin/traces?limit=${limit}`),

  adminUnresolvedTerms: () =>
    apiFetch<{ unresolved_terms: Array<{ term: string; count: number; last_seen?: string }>; total_distinct: number }>(
      "/admin/unresolved-terms"
    ),

  adminUpdateUser: (userId: string, opts: { is_active?: boolean; role?: string }) => {
    const params = new URLSearchParams();
    if (opts.is_active !== undefined) params.set("is_active", String(opts.is_active));
    if (opts.role) params.set("role", opts.role);
    return apiFetch<{ updated: string }>(`/admin/users/${userId}?${params.toString()}`, {
      method: "PATCH",
    });
  },
};
