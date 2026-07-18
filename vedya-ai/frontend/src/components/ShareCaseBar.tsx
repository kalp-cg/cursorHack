"use client";
import { useState } from "react";
import { RecommendationResponse, VignetteInput } from "@/lib/api";
import PrimaryButton from "./PrimaryButton";
import { useApp } from "@/lib/app-context";

function toBase64Url(obj: unknown): string {
  const json = JSON.stringify(obj);
  const b64 =
    typeof window !== "undefined"
      ? btoa(unescape(encodeURIComponent(json)))
      : Buffer.from(json, "utf8").toString("base64");
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function decodeCaseParam(param: string): VignetteInput | null {
  try {
    const padded = param.replace(/-/g, "+").replace(/_/g, "/");
    const pad = padded.length % 4 === 0 ? "" : "=".repeat(4 - (padded.length % 4));
    const json =
      typeof window !== "undefined"
        ? decodeURIComponent(escape(atob(padded + pad)))
        : Buffer.from(padded + pad, "base64").toString("utf8");
    return JSON.parse(json) as VignetteInput;
  } catch {
    return null;
  }
}

function buildMarkdown(response: RecommendationResponse): string {
  const top = response.results.find((r) => !r.hard_excluded) || response.results[0];
  const lines: string[] = [
    `# VedyaAI case export`,
    ``,
    `> Educational decision support only — not a diagnosis or prescription.`,
    ``,
    `## Vignette`,
    ``,
    response.vignette_summary || "(no summary)",
    ``,
    `## Top recommendation`,
    ``,
  ];
  if (top) {
    lines.push(
      `**${top.yoga_name}** (${top.kalpana || "—"}) — fit score ${top.score.toFixed(1)}`,
      ``,
      top.explanation?.summary || "",
      ``,
      `### Citations`,
      ``
    );
    for (const ref of top.references.slice(0, 5)) {
      lines.push(
        `- **${ref.work}**${ref.chapter ? ` · ${ref.chapter}` : ""}${ref.verse_id ? ` · ${ref.verse_id}` : ""}`
      );
      if (ref.excerpt_text) lines.push(`  > ${ref.excerpt_text}`);
    }
  }
  lines.push(
    ``,
    `## Ranked list`,
    ``,
    ...response.results.slice(0, 8).map(
      (r) =>
        `${r.rank}. ${r.yoga_name} — ${r.score.toFixed(1)}${r.hard_excluded ? " (excluded)" : ""}`
    ),
    ``,
    `Trace: \`${response.trace_id}\` · Corpus ${response.corpus_version}`,
    ``
  );
  return lines.join("\n");
}

type Props = {
  response: RecommendationResponse;
};

export default function ShareCaseBar({ response }: Props) {
  const { t, locale } = useApp();
  const [copied, setCopied] = useState(false);

  function buildShareUrl(): string {
    let inp: VignetteInput = {
      free_text: response.vignette_summary,
      symptoms: [],
      rogas: [],
      comorbidities: [],
      top_k: 10,
      locale,
    };
    try {
      const raw = sessionStorage.getItem("vedya_input");
      if (raw) inp = { ...JSON.parse(raw), locale };
    } catch {
      /* ignore */
    }
    const encoded = toBase64Url(inp);
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    return `${origin}/results?case=${encoded}`;
  }

  async function share() {
    const url = buildShareUrl();
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      window.prompt(t("shareCase"), url);
    }
  }

  function exportMd() {
    const md = buildMarkdown(response);
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `vedya-case-${response.trace_id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="veda-share-bar">
      <PrimaryButton size="sm" variant="outline" onClick={share}>
        {copied ? t("shareCopied") : t("shareCase")}
      </PrimaryButton>
      <PrimaryButton size="sm" variant="outline" onClick={exportMd}>
        {t("exportMd")}
      </PrimaryButton>
    </div>
  );
}
