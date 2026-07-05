# Changelog

## 1.0.1 - 2026-07-04

### Changed
- Lean core install: `torch`/`transformers` and other heavy dependencies moved
  to opt-in extras (`[ml]`, `[nlp]`, `[api]`, `[voice-advanced]`, `[all]`).
  Without `[ml]`, emotion detection falls back to VADER-based analysis.
- Fixed placeholder repository URL in packaging metadata.
- Unified version across `setup.py` and `empathy_engine.__init__` (previously
  0.1.1 while the release was tagged 1.0.0).
- Updated author metadata.
- Moved reference docs into `docs/`; removed internal process docs from the repo.

### Fixed
- Stdlib logging fallback crashed (`TypeError`) on structlog-style calls like
  `logger.error("msg", error=...)` when structlog/loguru weren't installed —
  which turned any emotion-analysis error into a hard crash.
- `structlog.configure()` call was missing the required level argument, so the
  structlog path never activated even when installed.
- `analyze_emotions()` now falls back to VADER-based emotion inference on
  classifier failure instead of returning `None` fields.

### Added
- GitHub Actions CI running the test suite on Python 3.10 and 3.12.

## 1.0.0 - 2026-03-26

Initial public release.

### Changed
- Hardened timestamp parsing across core modules.
- Advanced API endpoints now accept both text-only analysis and fused analysis.
- `/analyze/multimodal` accepts multipart form text.
- Added request validation models for advanced endpoints.

### Added
- API and utility smoke tests.
- `pytest.ini` to limit test discovery to `tests/`.
- Time parsing helper (`empathy_engine/utils/time.py`).
- Empath category analysis in text results (`empath_json`).

### Removed
- Docker files and deployment scripts.
- Obsidian integration references.
