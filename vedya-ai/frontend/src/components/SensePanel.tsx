"use client";

import type { SenseDisambiguation } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import { TranslatedText } from "@/components/TranslatedText";

interface Props {
  items: SenseDisambiguation[];
}

export default function SensePanel({ items }: Props) {
  const { t } = useApp();
  if (!items.length) return null;

  return (
    <section className="veda-sense" aria-label={t("senseTitle")}>
      <h3 className="veda-sense-title">{t("senseTitle")}</h3>
      <p className="veda-sense-sub">{t("senseSub")}</p>
      <ul className="veda-sense-list">
        {items.map((s) => (
          <li key={`${s.term}-${s.context_yoga}`} className="veda-sense-card">
            <div className="veda-sense-term">{s.term}</div>
            <div className="veda-sense-map">
              <span className="veda-sense-from">{s.default_dravya}</span>
              <span className="veda-sense-arrow">→</span>
              <span className="veda-sense-to">{s.resolved_dravya}</span>
            </div>
            {s.context_yoga && (
              <div className="veda-sense-ctx">
                {t("senseInYoga")}: <strong>{s.context_yoga}</strong>
              </div>
            )}
            {s.explanation && (
              <TranslatedText as="p" text={s.explanation} className="veda-sense-expl" />
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
