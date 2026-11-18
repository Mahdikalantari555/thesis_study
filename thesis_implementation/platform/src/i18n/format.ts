/**
 * Locale-aware formatting helpers.
 *
 * Design decision (§5 of the change design): charts keep ISO-ish `YYYY-MM`
 * x-axis labels in both locales, because Recharts' default tick/category
 * handling plus bidirectional text make Persian month names unreliable on an
 * axis. Persian *digits* are, however, applied to prose and stat values in
 * `fa`, and month names are used in tooltips/labels where a text string is
 * expected rather than a chart category.
 */

import type { Locale } from "./types";

export const FA_DIGITS = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

/**
 * Convert every ASCII digit in `input` to the Persian-Indic equivalents.
 * Non-digit characters (including `-`, `.`, `%`, `e`) pass through untouched,
 * so ISO dates stay machine-parseable while reading naturally in Persian.
 */
export function toPersianDigits(input: string | number): string {
  return String(input).replace(/[0-9]/g, d => FA_DIGITS[Number(d)]);
}

/** Convert Persian-Indic digits back to ASCII (for parsing user input). */
export function toAsciiDigits(input: string): string {
  return input.replace(/[۰-۹]/g, d => String(FA_DIGITS.indexOf(d)));
}

/**
 * Format a score/statistic for display in the active locale.
 * Persian: fixed decimals + Persian digits. English: the same number, ASCII.
 */
export function formatNumber(value: number, decimals: number, locale: Locale): string {
  if (!Number.isFinite(value)) return locale === "fa" ? "—" : "—";
  const fixed = value.toFixed(decimals);
  return locale === "fa" ? toPersianDigits(fixed) : fixed;
}

/** Thousands-separated integer, localized. */
export function formatInteger(value: number, locale: Locale): string {
  const rounded = Math.round(value);
  return locale === "fa"
    ? toPersianDigits(rounded.toLocaleString("en-US"))
    : rounded.toLocaleString("en-US");
}

const FA_MONTHS = [
  "ژانویه",
  "فوریه",
  "مارس",
  "آوریل",
  "مه",
  "ژوئن",
  "ژوئیه",
  "اوت",
  "سپتامبر",
  "اکتبر",
  "نوامبر",
  "دسامبر",
];

const EN_MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

/**
 * Render an ISO date (`YYYY-MM-DD` or `YYYY-MM`) for prose/tooltips.
 * English → `Mar 2022`; Persian → `مارس ۲۰۲۲`.
 * Charts intentionally keep using `YYYY-MM` (see module docstring).
 */
export function formatMonthYear(iso: string, locale: Locale): string {
  const [y, m] = iso.split("-");
  const monthIdx = Number(m) - 1;
  if (!Number.isFinite(monthIdx) || monthIdx < 0 || monthIdx > 11) return iso;
  if (locale === "fa") return `${FA_MONTHS[monthIdx]} ${toPersianDigits(y)}`;
  return `${EN_MONTHS[monthIdx].slice(0, 3)} ${y}`;
}

/** ISO `YYYY-MM` slice used consistently by the charts in both locales. */
export function isoMonth(iso: string): string {
  return iso.slice(0, 7);
}

/**
 * Locale-specific font stack applied to `<html>` (`index.css` defines the
 * `--font-fa` custom property). Kept here so the context stays free of magic
 * strings.
 */
export const FA_FONT_STACK = "'Vazirmatn', 'Inter', ui-sans-serif, system-ui, sans-serif";
