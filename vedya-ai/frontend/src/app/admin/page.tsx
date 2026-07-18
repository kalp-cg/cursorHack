"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, AdminStats, AdminTrace, AdminUserRow } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import PrimaryButton from "@/components/PrimaryButton";

const STAT_LABELS: Record<string, string> = {
  formulations: "Formulations",
  herbs: "Herbs (Dravyas)",
  concepts: "Concepts",
  synonym_terms: "Synonym terms",
  constraint_rules: "Safety rules",
  sense_rules: "Sense rules",
  references: "Classical references",
  users: "Users",
  conversations: "Conversations",
  cases_run: "Cases run",
  cases_last_24h: "Cases (24h)",
};

export default function AdminPage() {
  const router = useRouter();
  const { user, t } = useApp();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [traces, setTraces] = useState<AdminTrace[]>([]);
  const [unresolved, setUnresolved] = useState<Array<{ term: string; count: number }>>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [s, u, tr, un] = await Promise.all([
        api.adminStats(),
        api.adminUsers(),
        api.adminTraces(25),
        api.adminUnresolvedTerms(),
      ]);
      setStats(s);
      setUsers(u.users);
      setTraces(tr.traces);
      setUnresolved(un.unresolved_terms);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // Give app-context a tick to hydrate the stored session
    const timer = setTimeout(() => void loadAll(), 150);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function toggleActive(row: AdminUserRow) {
    setBusy(row.user_id);
    try {
      await api.adminUpdateUser(row.user_id, { is_active: !row.is_active });
      await loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  async function toggleRole(row: AdminUserRow) {
    setBusy(row.user_id);
    try {
      await api.adminUpdateUser(row.user_id, { role: row.role === "admin" ? "user" : "admin" });
      await loadAll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  }

  if (loading) {
    return (
      <div className="veda-admin-center">
        <div className="veda-spinner" aria-hidden />
        <p>{t("pleaseWait")}</p>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="veda-admin-center">
        <p style={{ color: "var(--veda-agni)" }}>{error.includes("403") || error.includes("401") ? t("adminOnly") : error}</p>
        <PrimaryButton className="mt-4" onClick={() => router.push("/login")}>
          {t("login")}
        </PrimaryButton>
      </div>
    );
  }

  return (
    <div className="veda-admin">
      <header className="veda-admin-head">
        <div>
          <h1>{t("adminTitle")}</h1>
          <p>{t("adminSub")}</p>
        </div>
        <span className="veda-chip-meta">
          {user?.email} · {t("adminBadge")}
        </span>
      </header>

      {error && <p className="veda-admin-error">{error}</p>}

      {/* Corpus + usage stats */}
      {stats && (
        <>
          <h2 className="veda-admin-section">{t("adminCorpusHealth")}</h2>
          <div className="veda-admin-stats">
            {Object.entries(stats.counts).map(([key, value]) => (
              <div key={key} className="veda-admin-stat">
                <div className="veda-admin-stat-value tabular-nums">{value.toLocaleString()}</div>
                <div className="veda-admin-stat-label">{STAT_LABELS[key] || key}</div>
              </div>
            ))}
          </div>

          {stats.top_recommended.length > 0 && (
            <div className="veda-admin-panel">
              <h3>{t("adminTopYogas")}</h3>
              <ul className="veda-admin-toplist">
                {stats.top_recommended.map((y) => (
                  <li key={y.name}>
                    <span>{y.name}</span>
                    <strong className="tabular-nums">{y.count}</strong>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {/* Vocabulary gaps — the curator's to-do list */}
      <h2 className="veda-admin-section">{t("adminGapsTitle")}</h2>
      <div className="veda-admin-panel">
        <p className="veda-admin-hint">{t("adminGapsHint")}</p>
        {unresolved.length === 0 ? (
          <p className="veda-admin-empty">{t("adminGapsEmpty")}</p>
        ) : (
          <ul className="veda-admin-toplist">
            {unresolved.map((u) => (
              <li key={u.term}>
                <span>{u.term}</span>
                <strong className="tabular-nums">×{u.count}</strong>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Users */}
      <h2 className="veda-admin-section">{t("adminUsersTitle")}</h2>
      <div className="veda-admin-panel veda-admin-table-wrap">
        <table className="veda-admin-table">
          <thead>
            <tr>
              <th>{t("email")}</th>
              <th>{t("adminRole")}</th>
              <th>{t("adminActive")}</th>
              <th>{t("adminCases")}</th>
              <th>{t("adminActions")}</th>
            </tr>
          </thead>
          <tbody>
            {users.map((row) => (
              <tr key={row.user_id} className={row.is_active ? "" : "is-inactive"}>
                <td>
                  <span className="veda-admin-email">{row.email}</span>
                  {row.display_name && <span className="veda-admin-name">{row.display_name}</span>}
                </td>
                <td>
                  <span className={`veda-role-badge ${row.role === "admin" ? "is-admin" : ""}`}>{row.role}</span>
                </td>
                <td>{row.is_active ? "✓" : "—"}</td>
                <td className="tabular-nums">{row.cases_run}</td>
                <td>
                  <div className="veda-admin-actions">
                    <button
                      type="button"
                      className="veda-nav-link"
                      disabled={busy === row.user_id || row.user_id === user?.user_id}
                      onClick={() => toggleRole(row)}
                    >
                      {row.role === "admin" ? t("adminMakeUser") : t("adminMakeAdmin")}
                    </button>
                    <button
                      type="button"
                      className="veda-nav-link"
                      disabled={busy === row.user_id || row.user_id === user?.user_id}
                      onClick={() => toggleActive(row)}
                    >
                      {row.is_active ? t("adminDeactivate") : t("adminActivate")}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recent activity */}
      <h2 className="veda-admin-section">{t("adminTracesTitle")}</h2>
      <div className="veda-admin-panel">
        {traces.length === 0 ? (
          <p className="veda-admin-empty">{t("noResults")}</p>
        ) : (
          <ul className="veda-admin-traces">
            {traces.map((tr) => (
              <li key={tr.trace_id}>
                <div className="veda-trace-top">
                  <strong>{tr.top_yoga || "—"}</strong>
                  <span className="veda-trace-time">
                    {tr.created_at ? new Date(tr.created_at).toLocaleString() : ""}
                  </span>
                </div>
                <div className="veda-trace-summary">{tr.vignette_summary || "—"}</div>
                <div className="veda-trace-meta">
                  {tr.user_email || t("adminGuest")}
                  {tr.safety_hits.length > 0 && (
                    <span className="veda-trace-safety"> · {tr.safety_hits.length} {t("adminSafetyHits")}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
