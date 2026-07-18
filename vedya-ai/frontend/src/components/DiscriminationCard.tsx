"use client";

import type { RecommendedFormulation } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import PrimaryButton from "@/components/PrimaryButton";
import { TranslatedText } from "@/components/TranslatedText";

interface Props {
  a: RecommendedFormulation;
  b: RecommendedFormulation;
  onCompare: () => void;
}

export default function DiscriminationCard({ a, b, onCompare }: Props) {
  const { t } = useApp();
  const delta = a.score - b.score;
  const aPrimary = a.primary_indications.slice(0, 3).join(" · ") || "—";
  const bPrimary = b.primary_indications.slice(0, 3).join(" · ") || "—";
  const aSecondary = a.secondary_indications.slice(0, 3).join(" · ") || "—";
  const bSecondary = b.secondary_indications.slice(0, 3).join(" · ") || "—";

  return (
    <section className="veda-disc">
      <div className="veda-disc-head">
        <h3>{t("whyOver", { a: a.yoga_name, b: b.yoga_name })}</h3>
        <span className="veda-disc-delta tabular-nums">
          {t("scoreDelta")}: {delta >= 0 ? "+" : ""}
          {delta.toFixed(1)}
        </span>
      </div>
      <p className="veda-disc-lead">{t("discLead")}</p>

      <div className="veda-disc-grid">
        <article className="veda-disc-col is-winner">
          <header>
            <span className="veda-disc-badge">{t("preferred")}</span>
            <h4>{a.yoga_name}</h4>
            <p>
              {a.kalpana || "—"} · {a.score.toFixed(1)}
            </p>
          </header>
          <dl>
            <div>
              <dt>{t("primaryIndications")}</dt>
              <dd>{aPrimary}</dd>
            </div>
            <div>
              <dt>{t("secondaryIndications")}</dt>
              <dd>{aSecondary}</dd>
            </div>
          </dl>
          {a.differentiation_note && (
            <TranslatedText as="p" text={a.differentiation_note} className="veda-disc-note" />
          )}
        </article>

        <article className="veda-disc-col">
          <header>
            <span className="veda-disc-badge is-alt">{t("alternate")}</span>
            <h4>{b.yoga_name}</h4>
            <p>
              {b.kalpana || "—"} · {b.score.toFixed(1)}
            </p>
          </header>
          <dl>
            <div>
              <dt>{t("primaryIndications")}</dt>
              <dd>{bPrimary}</dd>
            </div>
            <div>
              <dt>{t("secondaryIndications")}</dt>
              <dd>{bSecondary}</dd>
            </div>
          </dl>
          {b.differentiation_note && (
            <TranslatedText as="p" text={b.differentiation_note} className="veda-disc-note" />
          )}
        </article>
      </div>

      <div className="veda-disc-actions">
        <PrimaryButton onClick={onCompare}>{t("openFullCompare")}</PrimaryButton>
      </div>
    </section>
  );
}
