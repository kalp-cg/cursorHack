"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import type { Locale } from "@/lib/i18n";

const mem = new Map<string, string>();

function cacheKey(text: string, locale: Locale) {
  return `${locale}::${text}`;
}

/** Translate dynamic English prose into the active locale via Google-backed API. */
export function useTranslated(text: string | null | undefined): string {
  const { locale } = useApp();
  const source = text || "";
  const [out, setOut] = useState(source);

  useEffect(() => {
    let cancelled = false;
    if (!source.trim() || locale === "en") {
      setOut(source);
      return;
    }
    const key = cacheKey(source, locale);
    if (mem.has(key)) {
      setOut(mem.get(key)!);
      return;
    }
    setOut(source);
    api
      .translate([source], locale, "en")
      .then((res) => {
        if (cancelled) return;
        const translated = res.translations[0] || source;
        mem.set(key, translated);
        setOut(translated);
      })
      .catch(() => {
        if (!cancelled) setOut(source);
      });
    return () => {
      cancelled = true;
    };
  }, [source, locale]);

  return out;
}

export function TranslatedText({
  text,
  as: Tag = "span",
  className,
  style,
}: {
  text: string | null | undefined;
  as?: "span" | "p" | "div" | "li";
  className?: string;
  style?: React.CSSProperties;
}) {
  const translated = useTranslated(text);
  return (
    <Tag className={className} style={style}>
      {translated}
    </Tag>
  );
}

/** Batch-translate many strings when locale is not English. */
export function useTranslatedList(texts: string[]): string[] {
  const { locale } = useApp();
  const [out, setOut] = useState(texts);

  useEffect(() => {
    let cancelled = false;
    if (locale === "en" || texts.length === 0) {
      setOut(texts);
      return;
    }
    const missing: string[] = [];
    const resolved: (string | null)[] = texts.map((t) => {
      const key = cacheKey(t, locale);
      if (mem.has(key)) return mem.get(key)!;
      missing.push(t);
      return null;
    });
    if (missing.length === 0) {
      setOut(resolved as string[]);
      return;
    }
    api
      .translate(missing, locale, "en")
      .then((res) => {
        if (cancelled) return;
        let mi = 0;
        const next = texts.map((t, i) => {
          if (resolved[i] != null) return resolved[i] as string;
          const tr = res.translations[mi++] || t;
          mem.set(cacheKey(t, locale), tr);
          return tr;
        });
        setOut(next);
      })
      .catch(() => {
        if (!cancelled) setOut(texts);
      });
    return () => {
      cancelled = true;
    };
  }, [locale, texts.join("\u0001")]);

  return out;
}
