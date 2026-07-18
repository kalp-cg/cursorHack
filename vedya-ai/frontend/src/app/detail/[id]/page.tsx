"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, FormulationDetail } from "@/lib/api";
import CitationCard from "@/components/CitationCard";
import PrimaryButton from "@/components/PrimaryButton";
import { useApp } from "@/lib/app-context";

function PropertyRow({
  label,
  value,
  emptyLabel,
}: {
  label: string;
  value?: string | string[] | null;
  emptyLabel: string;
}) {
  const display = !value || (Array.isArray(value) && value.length === 0) ? null : value;
  return (
    <div
      className="flex justify-between items-start py-2.5 text-sm"
      style={{ borderBottom: "1px solid var(--veda-shila-deep)" }}
    >
      <span className="font-medium w-32" style={{ color: "var(--veda-ink-soft)" }}>
        {label}
      </span>
      <span className="flex-1 text-right" style={{ color: display ? "var(--veda-ink)" : "var(--veda-fog)" }}>
        {display ? (Array.isArray(display) ? display.join(", ") : display) : emptyLabel}
      </span>
    </div>
  );
}

export default function DetailPage() {
  const router = useRouter();
  const params = useParams();
  const yogaId = String(params.id || "");
  const { t } = useApp();
  const [detail, setDetail] = useState<FormulationDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!yogaId) return;
    api
      .getFormulation(yogaId)
      .then(setDetail)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [yogaId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: "var(--veda-shila)" }}>
        <div
          className="w-8 h-8 border-2 border-t-transparent rounded-full animate-spin"
          style={{ borderColor: "var(--veda-harita)" }}
        />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen" style={{ background: "var(--veda-shila)" }}>
        <p style={{ color: "var(--veda-ink-soft)" }}>{t("notInCorpus")}</p>
        <PrimaryButton className="mt-4" onClick={() => router.back()}>
          {t("goBack")}
        </PrimaryButton>
      </div>
    );
  }

  const primary = detail.primary_indications || [];
  const secondary = detail.secondary_indications || [];

  return (
    <div style={{ background: "var(--veda-shila)", minHeight: "100vh", fontFamily: "var(--font-ui)" }}>
      <div className="sticky top-0 z-10 px-6 py-3 flex items-center gap-4" style={{ background: "var(--veda-ink)" }}>
        <button onClick={() => router.back()} className="text-sm" style={{ color: "rgba(247,249,248,0.6)" }}>
          ← {t("goBack")}
        </button>
        <span className="text-base font-semibold" style={{ fontFamily: "var(--font-display)", color: "#F7F9F8" }}>
          {t("detailTitle")}
        </span>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8">
        <h1 className="text-3xl font-medium mb-1" style={{ fontFamily: "var(--font-display)", color: "var(--veda-ink)" }}>
          {detail.name}
        </h1>
        <div className="flex items-center gap-2 mb-6 flex-wrap">
          {detail.kalpana && (
            <span
              className="text-sm px-3 py-1 rounded-full"
              style={{ background: "var(--veda-shila-deep)", color: "var(--veda-ink-soft)" }}
            >
              {detail.kalpana}
            </span>
          )}
          {detail.external_only && (
            <span
              className="text-xs px-3 py-1 rounded-full font-medium"
              style={{ background: "var(--veda-agni-soft)", color: "var(--veda-agni)" }}
            >
              {t("externalOnly")}
            </span>
          )}
          {detail.category && (
            <span className="text-sm" style={{ color: "var(--veda-ink-soft)" }}>
              {detail.category}
            </span>
          )}
        </div>

        {(primary.length > 0 || secondary.length > 0) && (
          <section className="mb-8">
            <h2 className="font-semibold text-base mb-3" style={{ color: "var(--veda-ink)" }}>
              {t("indicationsTitle")}
            </h2>
            <div
              className="rounded-xl p-4"
              style={{ background: "var(--veda-surface)", border: "1px solid var(--veda-shila-deep)" }}
            >
              {primary.length > 0 && (
                <p className="text-sm mb-2">
                  <strong>{t("primaryIndications")}:</strong> {primary.join(" · ")}
                </p>
              )}
              {secondary.length > 0 && (
                <p className="text-sm">
                  <strong>{t("secondaryIndications")}:</strong> {secondary.join(" · ")}
                </p>
              )}
            </div>
          </section>
        )}

        <section className="mb-8">
          <h2 className="font-semibold text-base mb-3" style={{ color: "var(--veda-ink)" }}>
            {t("propertiesTitle")}
          </h2>
          <div
            className="rounded-xl p-4"
            style={{ background: "var(--veda-surface)", border: "1px solid var(--veda-shila-deep)" }}
          >
            {detail.ingredients.length === 0 ? (
              <p className="text-sm" style={{ color: "var(--veda-fog)" }}>
                {t("notInCorpus")}
              </p>
            ) : (
              detail.ingredients.map((ing) => (
                <div key={ing.name} className="mb-4 last:mb-0">
                  <div className="font-medium text-sm mb-1" style={{ color: "var(--veda-ink)" }}>
                    {ing.name}
                    {ing.botanical_name && (
                      <span className="text-xs italic ml-2" style={{ color: "var(--veda-fog)" }}>
                        ({ing.botanical_name})
                      </span>
                    )}
                  </div>
                  <PropertyRow label="Rasa" value={ing.rasa} emptyLabel={t("notInCorpus")} />
                  <PropertyRow label="Guna" value={ing.guna} emptyLabel={t("notInCorpus")} />
                  <PropertyRow label="Virya" value={ing.virya} emptyLabel={t("notInCorpus")} />
                  <PropertyRow label="Vipaka" value={ing.vipaka} emptyLabel={t("notInCorpus")} />
                </div>
              ))
            )}
          </div>
        </section>

        {(detail.dosage || detail.anupana) && (
          <section className="mb-8">
            <h2 className="font-semibold text-base mb-3" style={{ color: "var(--veda-ink)" }}>
              {t("administrationTitle")}
            </h2>
            <div
              className="rounded-xl p-4"
              style={{ background: "var(--veda-surface)", border: "1px solid var(--veda-shila-deep)" }}
            >
              <PropertyRow label={t("dosageLabel")} value={detail.dosage} emptyLabel={t("notInCorpus")} />
              <PropertyRow label={t("anupanaLabel")} value={detail.anupana} emptyLabel={t("notInCorpus")} />
            </div>
          </section>
        )}

        {detail.ambiguity_notes && Object.keys(detail.ambiguity_notes).length > 0 && (
          <section className="mb-8">
            <h2 className="font-semibold text-base mb-3" style={{ color: "var(--veda-ink)" }}>
              {t("ambiguityTitle")}
            </h2>
            {Object.entries(detail.ambiguity_notes).map(([term, note]) => (
              <div
                key={term}
                className="rounded-xl p-4 mb-2"
                style={{ background: "var(--veda-tamra-soft)", border: "1px solid var(--veda-tamra)" }}
              >
                <div className="font-semibold text-sm mb-1" style={{ color: "var(--veda-tamra)" }}>
                  {term}
                </div>
                <p className="text-sm" style={{ color: "var(--veda-ink)" }}>
                  {note}
                </p>
              </div>
            ))}
          </section>
        )}

        <section className="mb-8">
          <h2 className="font-semibold text-base mb-3" style={{ color: "var(--veda-ink)" }}>
            {t("refsTitle")}
          </h2>
          {detail.references.length > 0 ? (
            <div className="space-y-2">
              {detail.references.map((r) => (
                <CitationCard key={r.ref_id} reference={r} />
              ))}
            </div>
          ) : (
            <p className="text-sm" style={{ color: "var(--veda-fog)" }}>
              {t("notInCorpus")}
            </p>
          )}
        </section>

        <PrimaryButton variant="outline" onClick={() => router.back()}>
          ← {t("goBack")}
        </PrimaryButton>
      </div>
    </div>
  );
}
