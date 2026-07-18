"use client";
export default function DisclaimerBar() {
  return (
    <div
      className="w-full py-2 px-4 text-center text-xs"
      style={{
        background: "var(--veda-shila-deep)",
        color: "var(--veda-ink-soft)",
        borderTop: "1px solid var(--veda-fog)",
        fontFamily: "var(--font-ui)",
      }}
    >
      Educational decision support only — not a diagnosis or prescription.
      Clinical judgment of a qualified vaidya is required.
    </div>
  );
}
