/**
 * Shared i18n types.
 *
 * The platform ships an in-house, dependency-free i18n layer. Two flat
 * dictionaries (`en`, `fa`) map dotted keys (e.g. `"nav.overview"`) to
 * display strings. Flat keys keep dictionary diffs reviewable and avoid the
 * nested-object typing overhead described in the change design (§2).
 */

export type Locale = "en" | "fa";

/** A flat key → display-string map. */
export type Dictionary = Record<string, string>;

export const LOCALES: Locale[] = ["en", "fa"];

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "EN",
  fa: "FA",
};

/** Human-readable locale names (always shown in their own language). */
export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  fa: "فارسی",
};

export const DEFAULT_LOCALE: Locale = "en";

export const STORAGE_KEY = "agrianomaly.locale";

export function isLocale(value: unknown): value is Locale {
  return value === "en" || value === "fa";
}
