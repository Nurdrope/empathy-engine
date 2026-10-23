# Changelog

## Unreleased

### Changed
- Short texts (<20 words) now use the transformer emotion model whenever the
  `[ml]` extra is installed. Previously they always used quick mode, which only
  maps sentiment to joy/sadness and can never report fear, anger, disgust or
  surprise. On 8 short test sentences: model 7/8 correct, quick mode ~2/8
  (e.g. "I'm really anxious about the appointment tomorrow and I can't sleep"
  went from sadness to fear 99%). Without `[ml]`, behavior is unchanged.
- Text results include `analysis_mode`: `full`, `quick`, or `quick-fallback`
  (model requested but couldn't run), so callers know what they got.

### Security
- API keys required on every endpoint except `/`, `/health` and the docs
  (`EMPATHY_ENGINE_API_KEYS`; `Authorization: Bearer` or `X-API-Key`). New
  endpoints are protected by default. The server refuses to start without keys
  unless `EMPATHY_ENGINE_ALLOW_UNAUTHENTICATED=1` (local development).
- CORS is off by default (was `*`); allow specific origins with
  `EMPATHY_ENGINE_CORS_ORIGINS`.
- Request size limits: 25 MB audio uploads, 2 MB other bodies (configurable);
  streamed bodies without a Content-Length are rejected.
- Uploads restricted to known audio extensions; temp files always deleted.
- ffmpeg and the STT command now time out, and ffmpeg can only read local
  files (blocks URL-fetching tricks in crafted media files).
- 500 errors no longer return exception text; transcripts are never logged.
- Default bind address is now `127.0.0.1` (was `0.0.0.0`); the Docker image
  sets `HOST=0.0.0.0` itself, runs as a non-root user, and now installs the
  API dependencies it needs to start.

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
