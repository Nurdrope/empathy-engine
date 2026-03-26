# Changelog

## Unreleased

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
