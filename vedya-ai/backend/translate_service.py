"""
Free translation for dynamic clinical prose — no paid API key required.

Provider chain (first success wins per batch):
1. MyMemory Translation API  — free, no key
2. LibreTranslate public API — free, no key (URL overridable)
3. Lingva Translate mirrors  — free, no key

Optional: set LIBRETRANSLATE_URL if you self-host LibreTranslate.
Results are cached in-process.
"""
from __future__ import annotations

import hashlib
import os
from typing import Optional
from urllib.parse import quote

import httpx

_CACHE: dict[str, str] = {}
_CACHE_MAX = 2000
_SUPPORTED = {"en", "gu"}
_LAST_PROVIDER = "none"

# Public LibreTranslate endpoints (tried in order)
_LIBRE_URLS = [
    os.getenv("LIBRETRANSLATE_URL", "").strip(),
    "https://libretranslate.com",
    "https://translate.argosopentech.com",
]

# Public Lingva instances
_LINGVA_HOSTS = [
    "lingva.ml",
    "lingva.thedaviddelta.com",
]


def last_provider() -> str:
    return _LAST_PROVIDER


def _cache_key(text: str, source: str, target: str) -> str:
    raw = f"{source}|{target}|{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _norm_lang(code: str | None) -> str:
    loc = (code or "en").lower().strip()
    return loc if loc in _SUPPORTED else "en"


def _chunk(text: str, limit: int = 450) -> list[str]:
    """MyMemory free tier prefers shorter queries."""
    t = text.strip()
    if len(t) <= limit:
        return [t]
    chunks: list[str] = []
    buf = ""
    for part in t.replace("\n", " ").split(". "):
        piece = part if part.endswith(".") or not part else part + "."
        if len(buf) + len(piece) + 1 <= limit:
            buf = f"{buf} {piece}".strip()
        else:
            if buf:
                chunks.append(buf)
            buf = piece[:limit]
    if buf:
        chunks.append(buf)
    return chunks or [t[:limit]]


async def _mymemory_one(client: httpx.AsyncClient, text: str, source: str, target: str) -> str:
    parts: list[str] = []
    for chunk in _chunk(text):
        resp = await client.get(
            "https://api.mymemory.translated.net/get",
            params={"q": chunk, "langpair": f"{source}|{target}"},
        )
        resp.raise_for_status()
        data = resp.json()
        translated = (data.get("responseData") or {}).get("translatedText") or ""
        # MyMemory returns the QUERY URL-encoded on quota / error sometimes
        if not translated or translated.upper().startswith("MYMEMORY WARNING"):
            raise RuntimeError(translated or "MyMemory empty")
        # Detect quota-style echo
        if "YOU USED ALL AVAILABLE" in translated.upper():
            raise RuntimeError("MyMemory quota exceeded")
        parts.append(translated)
    return " ".join(parts).strip()


async def _libre_one(client: httpx.AsyncClient, text: str, source: str, target: str) -> str:
    last_err: Exception | None = None
    for base in _LIBRE_URLS:
        if not base:
            continue
        try:
            resp = await client.post(
                f"{base.rstrip('/')}/translate",
                json={
                    "q": text,
                    "source": source,
                    "target": target,
                    "format": "text",
                },
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code >= 400:
                last_err = RuntimeError(f"LibreTranslate {resp.status_code}")
                continue
            data = resp.json()
            translated = data.get("translatedText") or ""
            if translated:
                return translated
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"LibreTranslate failed: {last_err}")


async def _lingva_one(client: httpx.AsyncClient, text: str, source: str, target: str) -> str:
    last_err: Exception | None = None
    encoded = quote(text, safe="")
    for host in _LINGVA_HOSTS:
        try:
            resp = await client.get(f"https://{host}/api/v1/{source}/{target}/{encoded}")
            if resp.status_code >= 400:
                last_err = RuntimeError(f"Lingva {resp.status_code}")
                continue
            data = resp.json()
            translated = data.get("translation") or ""
            if translated:
                return translated
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Lingva failed: {last_err}")


async def _translate_one(client: httpx.AsyncClient, text: str, source: str, target: str) -> tuple[str, str]:
    """Try free providers in order; return (translated, provider_name)."""
    errors: list[str] = []

    try:
        return await _mymemory_one(client, text, source, target), "mymemory"
    except Exception as e:
        errors.append(f"mymemory:{e}")

    try:
        return await _libre_one(client, text, source, target), "libretranslate"
    except Exception as e:
        errors.append(f"libre:{e}")

    try:
        return await _lingva_one(client, text, source, target), "lingva"
    except Exception as e:
        errors.append(f"lingva:{e}")

    print(f"✗ All free translators failed ({'; '.join(errors)}); keeping source")
    return text, "none"


async def translate_texts(
    texts: list[str],
    target_locale: str,
    source_locale: str = "en",
) -> list[str]:
    global _LAST_PROVIDER
    target = _norm_lang(target_locale)
    source = _norm_lang(source_locale)
    if target == source or not texts:
        _LAST_PROVIDER = "none"
        return list(texts)

    out: list[Optional[str]] = [None] * len(texts)
    missing_idx: list[int] = []
    missing_texts: list[str] = []

    for i, text in enumerate(texts):
        if not text or not str(text).strip():
            out[i] = text
            continue
        key = _cache_key(text, source, target)
        if key in _CACHE:
            out[i] = _CACHE[key]
        else:
            missing_idx.append(i)
            missing_texts.append(text)

    if not missing_texts:
        _LAST_PROVIDER = "cache"
        return [x if x is not None else "" for x in out]

    providers_used: list[str] = []
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for idx, orig_i in enumerate(missing_idx):
            src = missing_texts[idx]
            try:
                result, provider = await _translate_one(client, src, source, target)
            except Exception as e:
                print(f"✗ Translation failed ({e})")
                result, provider = src, "none"
            out[orig_i] = result
            key = _cache_key(src, source, target)
            if len(_CACHE) >= _CACHE_MAX and key not in _CACHE:
                _CACHE.pop(next(iter(_CACHE)))
            _CACHE[key] = result
            providers_used.append(provider)

    # Prefer reporting a real provider if any succeeded
    real = [p for p in providers_used if p != "none"]
    _LAST_PROVIDER = real[0] if real else "none"
    return [x if x is not None else "" for x in out]


async def translate_one(text: str, target_locale: str, source_locale: str = "en") -> str:
    results = await translate_texts([text], target_locale, source_locale)
    return results[0] if results else text
