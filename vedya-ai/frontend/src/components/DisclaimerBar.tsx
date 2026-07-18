"use client";

import { useApp } from "@/lib/app-context";

export default function DisclaimerBar() {
  const { t } = useApp();
  return (
    <div
      style={{
        width: "100%",
        padding: "0.55rem 1rem",
        textAlign: "center",
        fontSize: "0.75rem",
        background: "var(--veda-shila-deep)",
        color: "var(--veda-ink-soft)",
        borderTop: "1px solid var(--veda-fog)",
        fontFamily: "var(--font-ui)",
      }}
    >
      {t("disclaimer")}
    </div>
  );
}
