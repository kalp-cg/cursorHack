"use client";

import { LOCALES, Locale } from "@/lib/i18n";
import { useApp } from "@/lib/app-context";

export default function LanguageSwitcher() {
  const { locale, setLocale, t } = useApp();

  return (
    <div className="veda-lang" role="group" aria-label={t("language")}>
      <span className="veda-lang-label">{t("language")}</span>
      <div className="veda-lang-seg">
        {LOCALES.map((l) => {
          const active = locale === l.code;
          return (
            <button
              key={l.code}
              type="button"
              className={`veda-lang-btn${active ? " is-active" : ""}`}
              aria-pressed={active}
              onClick={() => setLocale(l.code as Locale)}
              title={l.label}
            >
              <span className="veda-lang-code">{l.code.toUpperCase()}</span>
              <span className="veda-lang-native">{l.nativeShort}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
