# Changelog

All notable changes to the Columbia Food Emission Dashboard are documented here.

---

## [Unreleased] — feature/staged-upload

### Added
- **Two-step staged upload workflow** — Uploaded files are now cleaned and categorized first, then shown in a preview before committing to the dashboard. Users can review category breakdowns, total weight, and item counts before confirming.
- **Data Management page** (`/data-management`) — New page for viewing upload history, managing pending and committed records, and deleting committed data with automatic emission recomputation.
- **`pipeline/staging.py`** — Core module implementing staging, commit, delete, and recompute operations. Makes `emissions_summary.json` a derived artifact rebuilt from committed records in `data/committed/`.
- **Lazy migration for legacy data** — Existing 2023/2024/2025 seeded emission values in `emissions_summary.json` are preserved when no committed records exist for those years.
- **Step indicator UI** — Visual two-step progress indicator on the Upload page showing current workflow state.
- **Preview cards** — Styled summary cards showing upload statistics before confirmation.
- **Navbar update** — Added "Data Management" link to the top navigation bar.
- **Cover page update** — Added Data Management navigation card to the Explore section.

### Changed
- **Upload page** (`pages/upload.py`) — Rewritten from single-step immediate processing to two-step staged workflow with preview → confirm/cancel flow.
- **`config.py`** — Added `STAGING_DIR` and `COMMITTED_DIR` path constants.
- **`assets/style.css`** — Added styles for `.step-indicator`, `.step`, `.step-number`, `.step-connector`, and `.preview-card`.

### Architecture
- **New data directories:** `data/staging/` (pending uploads) and `data/committed/` (confirmed uploads).
- **Source of truth shift:** Individual committed records in `data/committed/` are now the source of truth. `emissions_summary.json` is rebuilt from these records via `recompute_emissions()`.
- **Undo capability:** Deleting a committed record triggers recomputation of `emissions_summary.json` without that data, effectively undoing an upload.

---

## [1.0.0] — 2026-03-02

### Added
- Initial release of the Columbia Food Emission Dashboard.
- **Cover page** — Landing page with headline KPIs and navigation cards.
- **Background page** — Introduction to Cool Food Pledge, PPCC, and methodology.
- **Emission Dashboard** — Year-over-year emission charts, progress gauges toward 2030 targets, ruminant meat trends.
- **Demographics page** — Meals served data by dining hall, monthly trends, emissions per meal.
- **Upload page** — Drag-and-drop upload for raw monthly procurement Excel files.
- **Data pipeline** — Cleaning, 56-category food classification, and emission calculation replicating WRI Cool Food Calculator formulas.
- Emission factors extracted from Cool Food Calculator (`emission_factors.json`).
- Seeded baseline data for 2023, 2024, and 2025 from verified FINAL EMISSIONS source.
