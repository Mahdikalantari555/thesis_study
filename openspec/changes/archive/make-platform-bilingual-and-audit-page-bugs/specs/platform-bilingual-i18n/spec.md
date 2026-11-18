# Spec Delta: platform-bilingual-i18n

## Purpose

Provides a bilingual (English/Persian) user interface layer for the React/Vite visualization platform, including locale state, translation dictionaries, a language switcher, RTL layout support, and Persian typography, so advisors and agronomists can use the dashboard in either language without code changes.

## ADDED Requirements

### Requirement: Locale state and provider
The platform SHALL maintain a single locale state (`en` or `fa`) provided via a React context to all views and components, defaulting to `en` when no prior choice exists.

#### Scenario: Default locale
- **WHEN** the platform is loaded for the first time in a browser with no saved preference
- **THEN** the active locale is `en` and all UI text renders in English

#### Scenario: Locale change propagates
- **WHEN** the user switches the locale via the language switcher
- **THEN** every view, panel title, tooltip, and label re-renders in the new locale without a page reload

### Requirement: Persistent language preference
The platform SHALL persist the selected locale in `localStorage` and restore it on subsequent loads.

#### Scenario: Restore saved preference
- **WHEN** the platform loads and `localStorage` contains a valid locale value
- **THEN** that locale becomes active immediately on first render

### Requirement: Translation dictionaries
The platform SHALL provide complete translation dictionaries for both `en` and `fa` covering every user-facing string in `App.tsx`, all 8 views, `ui.tsx`, and `MapView.tsx`.

#### Scenario: No missing keys
- **WHEN** any component calls `t(key)` for a key present in the English dictionary
- **THEN** the Persian dictionary contains the same key and returns a non-empty Persian string

#### Scenario: Fallback for unknown keys
- **WHEN** `t(key)` is called with a key not present in the active dictionary
- **THEN** the English value (or the key itself) is returned and a console warning is emitted

### Requirement: Language switcher
The platform SHALL display a language switcher in the topbar allowing toggling between English and Persian.

#### Scenario: Switcher visibility
- **WHEN** the platform renders the topbar
- **THEN** a control with labels "EN" and "FA" (or equivalent) is visible and clickable

#### Scenario: Switching updates document direction
- **WHEN** the user selects Persian
- **THEN** the `dir` attribute of the root element becomes `rtl` and the `lang` attribute becomes `fa`

### Requirement: RTL layout support
The platform SHALL apply right-to-left layout (mirrored sidebar, text alignment, flex row order) when the Persian locale is active.

#### Scenario: Sidebar position in RTL
- **WHEN** the locale is `fa`
- **THEN** the sidebar appears on the right side of the screen and text is right-aligned

#### Scenario: Charts render under RTL
- **WHEN** the locale is `fa`
- **THEN** all Recharts axes, legends, and tooltips remain fully visible and not clipped

### Requirement: Persian typography
The platform SHALL load and apply a Persian-capable font (Vazirmatn or equivalent) when the Persian locale is active.

#### Scenario: Font application
- **WHEN** the locale is `fa`
- **THEN** body text uses the Persian font stack and Persian digits render correctly

### Requirement: Locale-aware number and date formatting
The platform SHALL format numbers and dates according to the active locale.

#### Scenario: Persian digits
- **WHEN** the locale is `fa`
- **THEN** numeric stat values and counts may render with Persian digits where the dictionary specifies

#### Scenario: Date labels
- **WHEN** the locale is `fa`
- **THEN** month/year labels in charts use Persian month names or ISO dates consistently
