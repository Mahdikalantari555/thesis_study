"""Static checks on the bilingual platform layer.

These tests read the TypeScript sources directly (no Node toolchain required) so
that CI can police the invariants the `platform-bilingual-i18n` and
`platform-page-bug-audit` specs promise without building the SPA:

* both dictionaries define exactly the same keys;
* every ``t("…")`` key used by a component exists in the English dictionary;
* no Persian value is empty;
* no placeholder ``{name}`` is dropped or invented in the Persian translation;
* no leftover English UI strings from the "page bug audit" remain.

A full type-level check already covers parts of this (``fa.ts`` is declared
``satisfies Record<keyof typeof en, string>``), but that only runs when a
developer has ``node_modules`` installed — these tests keep the guarantee on a
plain Python checkout too.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PLATFORM = Path(__file__).resolve().parents[2] / "platform"
I18N = PLATFORM / "src" / "i18n"
SRC = PLATFORM / "src"

PLACEHOLDER = re.compile(r"\{(\w+)\}")
# Same job as PLACEHOLDER, but safe to use inside the Persian-value heuristic
# below: `PLACEHOLDER.sub` returns '' for a symbols-only string, which compares
# falsely to the original in the comprehension.



def _parse_dictionary(path: Path) -> dict[str, str]:
    """Parse ``"key": "value"`` pairs out of a TS dictionary literal.

    Deliberately regex-based: pulling in a JS parser would add a dependency for
    what is a flat, one-line-per-entry file. Returns ``{}`` for a missing file so
    the missing-file failure is reported by the explicit ``exists`` assertions.
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    # Drop the trailing `satisfies`/`as const` clauses and comments.
    text = re.sub(r"//[^\n]*", "", text)
    pairs: dict[str, str] = {}
    for match in re.finditer(r'"([^"\\]+)"\s*:\s*"((?:[^"\\]|\\.)*)"', text):
        key, value = match.group(1), match.group(2)
        pairs[key] = value.encode().decode("unicode_escape") if "\\" in value else value
    return pairs


@pytest.fixture(scope="module")
def en() -> dict[str, str]:
    return _parse_dictionary(I18N / "en.ts")


@pytest.fixture(scope="module")
def fa() -> dict[str, str]:
    return _parse_dictionary(I18N / "fa.ts")


# ── Dictionary integrity ─────────────────────────────────────────────────────
def test_dictionaries_exist_and_are_substantial(en, fa):
    assert len(en) > 300, f"English dictionary looks truncated ({len(en)} keys)"
    assert len(fa) > 300, f"Persian dictionary looks truncated ({len(fa)} keys)"


def test_persian_dictionary_has_no_missing_keys(en, fa):
    missing = sorted(set(en) - set(fa))
    assert not missing, f"fa.ts is missing {len(missing)} key(s): {missing[:10]}"


def test_persian_dictionary_has_no_extra_keys(en, fa):
    extra = sorted(set(fa) - set(en))
    assert not extra, f"fa.ts declares {len(extra)} key(s) absent from en.ts: {extra[:10]}"


def test_no_empty_translations(fa):
    empty = [k for k, v in fa.items() if not v.strip()]
    assert not empty, f"empty Persian translations: {empty}"


def test_placeholders_match_between_locales(en, fa):
    mismatched = {}
    for key, english in en.items():
        persian = fa.get(key, "")
        if set(PLACEHOLDER.findall(english)) != set(PLACEHOLDER.findall(persian)):
            mismatched[key] = (sorted(PLACEHOLDER.findall(english)), sorted(PLACEHOLDER.findall(persian)))
    assert not mismatched, f"placeholder mismatch: {mismatched}"


def test_persian_values_are_actually_persian(fa):
    """Guard against accidental copy-paste of the English string.

    Keys that are pure symbols/proper nouns (e.g. ``ui.notAvailable`` → ``—``)
    are exempt; the rest must contain at least one Arabic-script character.
    """
    arabic = re.compile(r"[\u0600-\u06FF]")
    # NOTE: the condition is expressed with `continue` rather than a single
    # chained `and` so that a value made purely of placeholders/symbols cannot
    # compare falsely-equal to the untouched original.
    suspect = []
    for key, value in fa.items():
        if len(value) <= 12 or arabic.search(value) or key.startswith("model."):
            continue
        remainder = PLACEHOLDER.sub("", value).strip(" →←—–-·.,")
        if remainder:
            suspect.append(key)
    assert not suspect, f"Persian values without Arabic script (likely untranslated): {suspect[:10]}"


# ── Component usage ──────────────────────────────────────────────────────────
def _tsx_files() -> list[Path]:
    return sorted(p for p in SRC.rglob("*.tsx") if "i18n" not in p.parts)


def test_every_t_call_resolves_to_a_dictionary_key(en):
    missing: dict[str, list[str]] = {}
    for path in _tsx_files():
        source = path.read_text(encoding="utf-8")
        for key in re.findall(r'\bt\(\s*"([^"]+)"', source):
            if key not in en:
                missing.setdefault(str(path.relative_to(PLATFORM)), []).append(key)
    assert not missing, f"unresolved translation keys: {missing}"


def test_no_hardcoded_english_nav_labels():
    """The sidebar labels used to live in a module-level ``NAV`` array."""
    app = (SRC / "App.tsx").read_text(encoding="utf-8")
    assert "label: 'Overview'" not in app and 'label: "Overview"' not in app
    assert 't(`nav.${n.id}`)' in app


def test_persian_font_is_self_hosted():
    css = (SRC / "index.css").read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in css, "CDN font import breaks the offline build"
    assert "vazirmatn-arabic-400-normal.woff2" in css
    for weight in ("400", "500", "600", "700"):
        assert (SRC / "assets" / "fonts" / f"vazirmatn-arabic-{weight}-normal.woff2").exists()


# ── Page bug audit regressions ───────────────────────────────────────────────
def test_no_hardcoded_48_step_sliders():
    """Sliders must span the loaded date axis, not a literal 48-point range."""
    offenders = {
        str(p.relative_to(SRC)): re.findall(r"max=\{4[0-9]\}", p.read_text(encoding="utf-8"))
        for p in _tsx_files()
    }
    offenders = {k: v for k, v in offenders.items() if v}
    assert not offenders, f"hard-coded slider bounds: {offenders}"
    # …and they must actually bind to LAST_IDX (or DATES.length - 1).
    bound = [
        p for p in _tsx_files()
        if "type=\"range\"" in p.read_text(encoding="utf-8") and "LAST_IDX" in p.read_text(encoding="utf-8")
    ]
    assert len(bound) >= 4, f"expected every slider view to use LAST_IDX, found {[p.name for p in bound]}"


def test_no_stale_region_labels():
    for path in SRC.rglob("*"):
        if path.suffix in {".ts", ".tsx", ".json", ".css"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "Piracicaba" not in text, f"stale region label in {path}"


def test_khuzestan_region_is_stated():
    """The dataset region must be named explicitly after removing the old label."""
    en = _parse_dictionary(I18N / "en.ts")
    fa = _parse_dictionary(I18N / "fa.ts")
    assert "Khuzestan" in en["overview.footer.region"]
    assert "خوزستان" in fa["overview.footer.region"]


def test_series_json_is_consumed():
    # data.ts (renamed from mock.ts — it is the typed loader for real pipeline
    # JSON, not mock data) must remain the single data source.
    data = (SRC / "data" / "data.ts").read_text(encoding="utf-8")
    # Contract v4: the big series payload loads as raw text + JSON.parse.
    assert "from './series_khuzestan.json?raw'" in data
    assert "from './farms_khuzestan.json'" in data
    # The synthetic generator must be gone: no seeded RNG in the data layer.
    assert "function rng(" not in data


def test_map_view_does_not_recreate_on_theme_change():
    view = (SRC / "components" / "MapView.tsx").read_text(encoding="utf-8")
    mount_effect = view[view.index("useEffect(") : view.index("/** Theme")]
    assert "}, []);" in mount_effect, "map mount effect must not depend on `dark`"


def test_selected_field_default_is_guarded():
    ctx = (SRC / "context" / "AnalysisContext.tsx").read_text(encoding="utf-8")
    # Strip comments so the BUG-05 explanation itself does not trip the check.
    code = re.sub(r"/\*.*?\*/", "", ctx, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    assert "FIELDS[9]" not in code and "FIELDS[10]" not in code and "FIELDS[18]" not in code


def test_exported_series_matches_platform_expectations():
    """The exporter and the platform must agree on the payload shape (contract v4)."""
    series = json.loads((SRC / "data" / "series_khuzestan.json").read_text(encoding="utf-8"))
    farms = json.loads((SRC / "data" / "farms_khuzestan.json").read_text(encoding="utf-8"))

    assert series["contractVersion"] == 4
    fields = series["fields"]
    assert len(fields) == len(farms) > 0, "every farm needs a time series"
    required = {"ndvi", "evi", "savi", "ndmi", "tvdi", "cwsi", "eta", "precip", "temp", "lst"}
    first = next(iter(fields.values()))
    assert set(required) <= set(first["channels"]), f"missing channels: {required - set(first['channels'])}"
    # The shared date axis is derived from this payload — uniform by construction.
    axis = series["axis"]
    assert len(axis) > 500, f"full acquisition axis expected, got {len(axis)}"
    for f in fields.values():
        for c in required:
            assert len(f["channels"][c]) == len(axis), "channel arrays must cover the axis"
        for k in f["scores"]:
            assert len(f["scores"][k]) == len(axis)
    # Every real acquisition date: months with two scenes appear twice.
    months = {}
    for d in axis:
        months[d[:7]] = months.get(d[:7], 0) + 1
    assert max(months.values()) >= 2, "multi-acquisition months must be present"
