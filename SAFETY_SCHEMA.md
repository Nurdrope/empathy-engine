# Safety Schema (Draft)

This draft captures the v1.0 intent to separate clinician-grade payloads from
user-facing summaries. Alpha builds remain wide open.

## Response Shape (v1.0 target)

```json
{
  "risk_assessment": {
    "tier": "none|monitor|concern|high|critical",
    "confidence": 0.0,
    "signals": {
      "lexical_hits": [],
      "temporal_spike": false,
      "baseline_deviation": 0.0,
      "avoidance_detected": false,
      "negative_short_count": 0
    },
    "notes": "internal analyst notes"
  },
  "user_view": {
    "status": "neutral|watch|concern|urgent",
    "summary": "non-prescriptive tracking summary"
  },
  "clinical_view": {
    "signals": {},
    "scores": {},
    "timestamps": [],
    "inputs": {
      "text": "...",
      "audio_path": "..."
    }
  }
}
```

## Design Notes

- Alpha: return full payload in the main response.
- v1.0: default to `user_view`; `clinical_view` requires explicit opt-in.
- No advice/prescription; this is logging and tracking only.
- Redact sensitive strings in logs by default.
