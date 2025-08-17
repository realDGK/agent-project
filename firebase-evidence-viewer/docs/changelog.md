## [2.1.0] - 2025-08-16
### Added
- Expand (Full View) feature for active tab with keyboard shortcuts (F to toggle, Esc to close).
- Deep link server routing: `/doc/{sha256}` and `/evidence-viewer` now serve the Evidence Viewer shell.
- Asset versioning with build timestamp and Cache-Control headers to prevent stale browser caching.
- Version constant logged to console and included in telemetry events for debugging.

### Changed
- Evidence chip behavior:
  - Click → In-pane routing (focuses tab, flashes highlight).
  - Shift+Click → Side-by-Side view (Conformed left, Source right).
  - Ctrl/Cmd+Click → Opens full UI in a new browser tab.
- Credits operand in calculation breakdown now displays as `+ $0.00` instead of `- $0.00`.

### Fixed
- Deep links now open correctly in new tabs instead of throwing server errors.
- Cache-busting applied to JavaScript/CSS assets to resolve stale code issues.

### Verified
- All acceptance criteria from v2.0 spec confirmed working in production:
  - Chip navigation and highlighting.
  - Side-by-Side comparison.
  - As-Of date resolution.
  - Formula breakdown with badges.
  - Telemetry event logging.

---
