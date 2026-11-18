/**
 * I18nProvider / useLocale / useT — the runtime half of the bilingual layer.
 *
 * Responsibilities (per `platform-bilingual-i18n` spec):
 *  1. Hold the single source of truth for the active locale (`en` | `fa`).
 *  2. Restore a persisted locale from `localStorage` synchronously on first
 *     render (no flash of English when Persian was chosen previously), and
 *     persist changes.
 *  3. Mirror the locale onto `<html lang dir>` and a `lang-fa` body class so
 *     CSS (font stack, RTL overrides) can react without React re-renders.
 *  4. Expose `t(key, params)` with `{placeholder}` interpolation, English
 *     fallback for unknown keys, and a one-time console warning per key.
 */

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { en } from "./en";
import { fa } from "./fa";
import { formatInteger, formatNumber, formatMonthYear, isoMonth } from "./format";
import { DEFAULT_LOCALE, isLocale, LOCALE_LABELS, LOCALE_NAMES, LOCALES, STORAGE_KEY, type Dictionary, type Locale } from "./types";

export type TParams = Record<string, string | number>;
export type TFn = (key: string, params?: TParams) => string;

interface I18nCtx {
  locale: Locale;
  setLocale: (l: Locale) => void;
  toggleLocale: () => void;
  t: TFn;
  dir: "ltr" | "rtl";
  isRtl: boolean;
  dictionary: Dictionary;
  locales: Locale[];
  labels: Record<Locale, string>;
  names: Record<Locale, string>;
  /** Locale-aware formatters, bound to the active locale. */
  fmt: {
    number: (value: number, decimals?: number) => string;
    integer: (value: number) => string;
    monthYear: (iso: string) => string;
    isoMonth: (iso: string) => string;
  };
}

const DICTIONARIES: Record<Locale, Dictionary> = { en: { ...en }, fa: { ...fa } };

const warned = new Set<string>();

function readStoredLocale(): Locale {
  // Guard for non-browser/test environments and blocked storage.
  try {
    const raw = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (isLocale(raw)) return raw;
    if (typeof window !== "undefined") {
      // Fall back to the browser preference the first time only.
      const nav = window.navigator?.language?.toLowerCase() ?? "";
      if (nav.startsWith("fa")) return "fa";
    }
  } catch {
    /* storage disabled — stay on the default */
  }
  return DEFAULT_LOCALE;
}

function interpolate(template: string, params?: TParams): string {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) => {
    const value = params[name];
    return value === undefined ? match : String(value);
  });
}

const I18nContext = createContext<I18nCtx>(null!);

export function useLocale() {
  return useContext(I18nContext);
}

/** Convenience hook: `const t = useT();` then `t("nav.overview")`. */
export function useT(): TFn {
  return useContext(I18nContext).t;
}

export function I18nProvider({ children, initialLocale }: { children: React.ReactNode; initialLocale?: Locale }) {
  const [locale, setLocaleState] = useState<Locale>(() => initialLocale ?? readStoredLocale());

  // Reflect the locale on the document root so CSS and a11y metadata agree.
  useEffect(() => {
    const root = document.documentElement;
    const dir = locale === "fa" ? "rtl" : "ltr";
    root.setAttribute("lang", locale);
    root.setAttribute("dir", dir);
    root.dataset.locale = locale;
    document.body.classList.toggle("lang-fa", locale === "fa");
    document.body.classList.toggle("lang-en", locale === "en");
    try {
      window.localStorage.setItem(STORAGE_KEY, locale);
    } catch {
      /* storage disabled — in-memory only */
    }
  }, [locale]);

  const t = useCallback<TFn>(
    (key, params) => {
      const dict = DICTIONARIES[locale];
      const enDict: Dictionary = en;
      const value = dict[key] ?? enDict[key];
      if (value === undefined) {
        if (!warned.has(key)) {
          warned.add(key);
          // eslint-disable-next-line no-console
          console.warn(`[i18n] missing translation key "${key}" (locale: ${locale})`);
        }
        return key;
      }
      return interpolate(value, params);
    },
    [locale]
  );

  const value = useMemo<I18nCtx>(() => {
    const dir = locale === "fa" ? "rtl" : "ltr";
    return {
      locale,
      setLocale: (l: Locale) => setLocaleState(isLocale(l) ? l : DEFAULT_LOCALE),
      toggleLocale: () => setLocaleState(prev => (prev === "en" ? "fa" : "en")),
      t,
      dir,
      isRtl: dir === "rtl",
      dictionary: DICTIONARIES[locale],
      locales: LOCALES,
      labels: LOCALE_LABELS,
      names: LOCALE_NAMES,
      fmt: {
        number: (v: number, decimals = 3) => formatNumber(v, decimals, locale),
        integer: (v: number) => formatInteger(v, locale),
        monthYear: (iso: string) => formatMonthYear(iso, locale),
        isoMonth,
      },
    };
  }, [locale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}
