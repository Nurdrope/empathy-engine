"""
EmpathyEngine - FastAPI REST API Server
Provides HTTP endpoints for emotional analysis
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from ..core.engine import EmpathyEngine
from ..utils.logging import get_logger
from ..utils.settings import get_settings
from .security import (
    PUBLIC_PATHS,
    SecurityConfig,
    key_is_valid,
    presented_key,
    safe_audio_suffix,
)

# Initialize FastAPI app
settings = get_settings()
security_config = SecurityConfig.from_env()
logger = get_logger(__name__)
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version
)

BODY_METHODS = {"POST", "PUT", "PATCH"}
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
# Room for multipart boundaries and form fields around the audio itself.
MULTIPART_OVERHEAD = 64 * 1024


@app.middleware("http")
async def security_guard(request: Request, call_next):
    """
    Runs before every endpoint: API key check, then request size check.

    Read from the module-level `security_config` on each request so tests
    (and future reloads) can swap the config.
    """
    config = security_config

    if request.url.path not in PUBLIC_PATHS:
        if not config.auth_configured:
            # Fail closed: a server started without keys serves nothing.
            return JSONResponse(
                status_code=503,
                content={"detail": "API keys not configured on the server"},
            )
        if not config.allow_unauthenticated and not key_is_valid(config, presented_key(request.headers)):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid API key"},
                headers={"WWW-Authenticate": "Bearer"},
            )

    if request.method in BODY_METHODS:
        is_upload = request.headers.get("content-type", "").startswith("multipart/form-data")
        limit = config.max_upload_bytes + MULTIPART_OVERHEAD if is_upload else config.max_body_bytes
        length = request.headers.get("content-length")
        if length is None:
            # The size can't be checked up front for a streamed body; require
            # the length header (every normal HTTP client sends it).
            if "chunked" in request.headers.get("transfer-encoding", "").lower():
                return JSONResponse(status_code=411, content={"detail": "Content-Length required"})
        else:
            try:
                too_big = int(length) > limit
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})
            if too_big:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request too large (limit {limit // (1024 * 1024)} MB)"},
                )

    return await call_next(request)


# Added after the guard so it wraps it: browser preflight (OPTIONS) requests
# get CORS answers without needing a key. No origins configured = no CORS
# headers at all, so browsers on other sites can't call the API.
if security_config.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(security_config.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "X-API-Key", "Content-Type"],
    )


def _internal_error(exc: Exception) -> HTTPException:
    """
    Log the real error server-side; tell the client only that it failed.

    Exception text can contain file paths, library internals or fragments of
    the analyzed input, none of which should go back over the network.
    """
    logger.error("Request failed", error_type=type(exc).__name__, error=str(exc))
    return HTTPException(status_code=500, detail="Internal error while processing the request")


async def _save_upload(file: UploadFile, suffix: str) -> str:
    """Stream an upload to a temp file, enforcing the size limit; return its path."""
    limit = security_config.max_upload_bytes
    written = 0
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        try:
            while chunk := await file.read(1024 * 1024):
                written += len(chunk)
                if written > limit:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Audio file too large (limit {limit // (1024 * 1024)} MB)",
                    )
                tmp.write(chunk)
        except BaseException:
            tmp.close()
            _unlink_quietly(tmp.name)
            raise
        return tmp.name


def _unlink_quietly(path: Optional[str]) -> None:
    if path:
        try:
            os.unlink(path)
        except OSError:
            pass


# Initialize engine
engine = EmpathyEngine()


def _normalize_analysis_result(raw: dict) -> dict:
    """
    Normalize input into the fused analysis shape expected by advanced modules.

    Accepts either a fused analysis_result or a raw text analysis dict.
    """
    if not isinstance(raw, dict):
        return {}
    if isinstance(raw.get("result"), dict):
        raw = raw["result"]
    if raw.get("text_analysis") or raw.get("primary_emotion"):
        return raw
    if not raw:
        return raw
    text_analysis = raw
    fusion = engine.fusion.fuse(text_analysis=text_analysis, voice_analysis=None)
    fusion["text_analysis"] = text_analysis
    return fusion


def _wrap_response(result, **inputs) -> dict:
    """Return alpha-wide open response payloads with inputs."""
    payload = {"result": result}
    if inputs:
        payload["inputs"] = inputs
    return payload


def _run_stt(audio_path: str) -> Optional[str]:
    """
    Run speech-to-text if configured.

    Command can use {wav} and {outdir} placeholders.
    """
    command = settings.stt_command
    if not command:
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            rendered = command.format(wav=audio_path, outdir=tmpdir)
            rendered = " ".join(rendered.split())
        except Exception as exc:
            logger.error("STT command template failed", error=str(exc))
            return None

        # The command comes from the server's own config, never from a request,
        # and runs without a shell, so request data can't add commands. The
        # only request-influenced part is the {wav} path, whose suffix is
        # whitelisted by safe_audio_suffix().
        try:
            args = shlex.split(rendered)
            if len(args) >= 2 and os.path.isdir(args[0]):
                joined = os.path.join(args[0], args[1])
                if os.path.exists(joined):
                    args = [joined] + args[2:]
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=security_config.subprocess_timeout,
            )
        except subprocess.TimeoutExpired:
            logger.error("STT command timed out", timeout=security_config.subprocess_timeout)
            return None
        except Exception as exc:
            logger.error(
                f"STT command execution failed: {exc} | command={rendered}"
            )
            return None

        # stdout is deliberately never logged: it is the user's transcript.
        if result.returncode != 0:
            logger.error(
                "STT command failed: returncode={rc} | command={cmd} | stderr={err}".format(
                    rc=result.returncode,
                    cmd=rendered,
                    err=(result.stderr or "").strip()[-2000:]
                )
            )
            return None

        transcripts = sorted(Path(tmpdir).rglob("*.txt"))
        if transcripts:
            try:
                return transcripts[0].read_text().strip()
            except Exception as exc:
                logger.error("STT transcript read failed", error=str(exc))

        if result.stdout:
            return result.stdout.strip()

        try:
            entries = [p.name for p in Path(tmpdir).iterdir()]
        except Exception as exc:
            entries = [f"error_listing_dir: {exc}"]
        logger.error(
            "STT produced no transcript: returncode={rc} | command={cmd} | stderr={err} | dir_entries={entries}".format(
                rc=result.returncode,
                cmd=rendered,
                err=(result.stderr or "").strip()[-2000:],
                entries=entries
            )
        )

    return None


def _convert_to_wav(input_path: str) -> Optional[str]:
    """Convert audio to wav for whisper.cpp if needed."""
    if not shutil.which("ffmpeg"):
        logger.error("STT conversion failed: ffmpeg not found")
        return None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        wav_path = tmp.name

    # The input is an untrusted upload. "-protocol_whitelist file" stops a
    # crafted playlist-style file from making ffmpeg fetch URLs (SSRF);
    # -nostdin and the timeout stop it from hanging the worker.
    try:
        result = subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-y",
             "-protocol_whitelist", "file",
             "-i", input_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=security_config.subprocess_timeout,
        )
    except subprocess.TimeoutExpired:
        logger.error("STT conversion timed out", timeout=security_config.subprocess_timeout)
        _unlink_quietly(wav_path)
        return None
    if result.returncode != 0:
        logger.error(
            "STT conversion failed: returncode={rc} | stderr={err}".format(
                rc=result.returncode,
                err=(result.stderr or "").strip()[-2000:]
            )
        )
        _unlink_quietly(wav_path)
        return None

    return wav_path


# Request/Response models
class TextAnalysisRequest(BaseModel):
    text: str
    force_full: bool = False


class MultiModalRequest(BaseModel):
    text: Optional[str] = None
    force_full_text: bool = False


class ContextualAnalysisRequest(BaseModel):
    text: Optional[str] = None
    entries: Optional[List[dict]] = None
    pattern_days: int = 30
    force_full_text: bool = False


class PatternDetectionRequest(BaseModel):
    entries: List[dict]
    days: int = 30


class BatchAnalysisRequest(BaseModel):
    items: List[dict]
    include_patterns: bool = False


class SummaryRequest(BaseModel):
    entries: Optional[List[dict]] = None
    period: str = "daily"
    date: Optional[str] = None


class AnalysisResultRequest(BaseModel):
    analysis_result: dict


class CrisisAssessmentRequest(BaseModel):
    analysis_result: dict
    entries: Optional[List[dict]] = None
    days: int = 30


class BaselineBuildRequest(BaseModel):
    entries: Optional[List[dict]] = None
    days: Optional[int] = None
    user_id: Optional[str] = None


class BaselineCompareRequest(BaseModel):
    analysis_result: dict
    baseline: dict


class TransitionAnalyzeRequest(BaseModel):
    entries: List[dict]
    min_transition_count: int = 3


class TransitionTrackRequest(BaseModel):
    previous: dict
    current: dict
    transition_patterns: Optional[dict] = None


class ContextRequest(BaseModel):
    analysis_result: dict
    recent_entries: Optional[List[dict]] = None
    user_timezone: Optional[str] = None


class CongruenceRequest(BaseModel):
    analysis_result: dict
    intensity_result: Optional[dict] = None
    sarcasm_result: Optional[dict] = None
    context_result: Optional[dict] = None
    baseline: Optional[dict] = None


class PredictLearnRequest(BaseModel):
    entries: List[dict]
    baseline: Optional[dict] = None


class PredictNextRequest(BaseModel):
    current_analysis: dict
    timeframe: str = "short"


class TriggerIdentifyRequest(BaseModel):
    entries: List[dict]
    min_occurrences: int = 3


class TriggerCheckRequest(BaseModel):
    current_analysis: dict
    known_triggers: dict


class GroupAnalyzeRequest(BaseModel):
    individual_analyses: List[dict]
    group_metadata: Optional[dict] = None


class CulturalAdaptRequest(BaseModel):
    analysis_result: dict
    cultural_profile: Optional[dict] = None
    auto_detect: bool = True


class CoherenceScoreRequest(BaseModel):
    analysis_result: dict
    intensity_result: Optional[dict] = None
    sarcasm_result: Optional[dict] = None
    congruence_result: Optional[dict] = None
    context_result: Optional[dict] = None
    baseline_deviation: Optional[dict] = None
    cultural_adaptation: Optional[dict] = None


# API endpoints
@app.get("/")
async def root():
    """API root - health check."""
    return {
        "service": "EmpathyEngine API",
        "version": settings.api_version,
        "status": "operational"
    }


@app.post("/analyze/text")
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze text for emotional content.

    Request body:
    {
        "text": "I'm feeling stressed",
        "force_full": false
    }
    """
    try:
        result = engine.analyze_text(
            text=request.text,
            force_full=request.force_full
        )
        return JSONResponse(content=_wrap_response(
            result,
            text=request.text,
            force_full=request.force_full
        ))
    except Exception as e:
        logger.error("Text analysis failed", error=str(e))
        raise _internal_error(e)


@app.post("/analyze/voice")
async def analyze_voice(file: UploadFile = File(...)):
    """
    Analyze voice audio for prosodic emotion.

    Upload a WAV audio file.
    """
    suffix = safe_audio_suffix(file.filename)
    tmp_path = await _save_upload(file, suffix)
    try:
        result = engine.analyze_voice(tmp_path)
        return JSONResponse(content=_wrap_response(
            result,
            filename=file.filename
        ))
    except Exception as e:
        raise _internal_error(e)
    finally:
        _unlink_quietly(tmp_path)


@app.post("/analyze/multimodal")
async def analyze_multimodal(
    text: Optional[str] = Form(None),
    force_full_text: bool = Form(False),
    file: Optional[UploadFile] = File(None)
):
    """
    Multi-modal analysis with fusion.

    Accepts text and/or audio file.
    """
    tmp_path = None
    stt_path = None
    transcript = None

    # Validate and save audio before the try, so a 413/415 reaches the client
    # as-is instead of being turned into a 500.
    if file:
        suffix = safe_audio_suffix(file.filename)
        tmp_path = await _save_upload(file, suffix)

    try:
        if tmp_path:
            stt_path = tmp_path
            if suffix != ".wav":
                stt_path = _convert_to_wav(tmp_path)
            if stt_path:
                transcript = _run_stt(stt_path)
            if transcript and not text:
                text = transcript

        result = engine.analyze(
            text=text,
            audio_path=tmp_path,
            force_full_text=force_full_text
        )

        return JSONResponse(content=_wrap_response(
            result,
            text=text,
            force_full_text=force_full_text,
            file_provided=bool(file),
            transcript=transcript
        ))
    except Exception as e:
        raise _internal_error(e)
    finally:
        _unlink_quietly(tmp_path)
        if stt_path != tmp_path:
            _unlink_quietly(stt_path)


@app.post("/analyze/contextual")
async def analyze_contextual(request: ContextualAnalysisRequest):
    """
    Analysis with historical context and pattern detection.

    Request body:
    {
        "text": "I'm worried again",
        "entries": [...],  // historical entries
        "pattern_days": 30,
        "force_full_text": false
    }
    """
    try:
        result = engine.analyze_with_context(
            text=request.text,
            entries=request.entries,
            pattern_days=request.pattern_days,
            force_full_text=request.force_full_text
        )
        return JSONResponse(content=_wrap_response(
            result,
            text=request.text,
            entries=request.entries,
            pattern_days=request.pattern_days,
            force_full_text=request.force_full_text
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/patterns/detect")
async def detect_patterns(request: PatternDetectionRequest):
    """
    Detect emotional patterns from historical data.

    Request body:
    {
        "entries": [...],
        "days": 30
    }
    """
    try:
        patterns = engine.detect_patterns(
            entries=request.entries,
            days=request.days
        )
        return JSONResponse(content=_wrap_response(
            patterns,
            entries=request.entries,
            days=request.days
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/analyze/batch")
async def analyze_batch(request: BatchAnalysisRequest):
    """
    Batch analyze multiple items.

    Request body:
    {
        "items": [
            {"text": "...", "timestamp": "..."},
            {"text": "...", "timestamp": "..."}
        ],
        "include_patterns": false
    }
    """
    try:
        results = engine.batch_analyze(
            items=request.items,
            include_patterns=request.include_patterns
        )
        return JSONResponse(content=_wrap_response(
            {"results": results},
            items=request.items,
            include_patterns=request.include_patterns
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/summaries/generate")
async def generate_summary(request: SummaryRequest):
    """
    Generate emotional summary for a time period.

    Request body:
    {
        "entries": [...],  // list of entries with timestamp, emotion, sentiment
        "period": "daily",  // or "weekly", "monthly"
        "date": "2025-12-18"  // optional ISO date string
    }
    """
    try:
        entries = request.entries or []
        period = request.period
        date_str = request.date

        # Parse date if provided
        date = None
        if date_str:
            from datetime import datetime
            date = datetime.fromisoformat(date_str)

        summary = engine.generate_summary(entries, period=period, date=date)
        return JSONResponse(content=_wrap_response(
            summary,
            entries=entries,
            period=period,
            date=date_str
        ))
    except Exception as e:
        raise _internal_error(e)


# Advanced feature endpoints (December 2025 expansion)

@app.post("/advanced/intensity")
async def calibrate_intensity(request: AnalysisResultRequest):
    """
    Calibrate emotion intensity from analysis result.

    Request body:
    {
        "analysis_result": {...}  // output from /analyze/* endpoints
    }
    """
    try:
        analysis_result = _normalize_analysis_result(request.analysis_result)
        intensity = engine.intensity_calibrator.calibrate(analysis_result)
        return JSONResponse(content=_wrap_response(
            intensity,
            analysis_result=analysis_result
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/sarcasm")
async def detect_sarcasm(request: AnalysisResultRequest):
    """
    Detect sarcasm/irony in analysis result.

    Request body:
    {
        "analysis_result": {...}
    }
    """
    try:
        analysis_result = _normalize_analysis_result(request.analysis_result)
        sarcasm = engine.sarcasm_detector.detect(analysis_result)
        return JSONResponse(content=_wrap_response(
            sarcasm,
            analysis_result=analysis_result
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/crisis")
async def assess_crisis_risk(request: CrisisAssessmentRequest):
    """
    Assess crisis/risk level from analysis.

    Request body:
    {
        "analysis_result": {...},
        "entries": [...],  // optional historical entries
        "days": 30  // optional
    }
    """
    try:
        analysis_result = _normalize_analysis_result(request.analysis_result)
        entries = request.entries
        days = request.days

        assessment = engine.crisis_detector.assess_risk(
            analysis_result,
            entries=entries,
            days=days
        )
        schema = engine.crisis_detector.assess_risk_schema(
            analysis_result,
            entries=entries,
            days=days
        )
        return JSONResponse(content=_wrap_response(
            {"assessment": assessment, "schema": schema},
            analysis_result=analysis_result,
            entries=entries,
            days=days
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/baseline/build")
async def build_baseline(request: BaselineBuildRequest):
    """
    Build emotional baseline profile from historical data.

    Request body:
    {
        "entries": [...],
        "days": 30,  // optional
        "user_id": "user123"  // optional
    }
    """
    try:
        entries = request.entries or []
        days = request.days
        user_id = request.user_id

        baseline = engine.baseline_profiler.build_baseline(
            entries,
            days=days,
            user_id=user_id
        )
        return JSONResponse(content=_wrap_response(
            baseline,
            entries=entries,
            days=days,
            user_id=user_id
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/baseline/compare")
async def compare_to_baseline(request: BaselineCompareRequest):
    """
    Compare current state to baseline profile.

    Request body:
    {
        "analysis_result": {...},
        "baseline": {...}  // from /advanced/baseline/build
    }
    """
    try:
        analysis_result = _normalize_analysis_result(request.analysis_result)
        baseline = request.baseline

        deviation = engine.baseline_profiler.compare_to_baseline(
            analysis_result,
            baseline
        )
        return JSONResponse(content=_wrap_response(
            deviation,
            analysis_result=analysis_result,
            baseline=baseline
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/transitions/analyze")
async def analyze_transitions(request: TransitionAnalyzeRequest):
    """
    Analyze emotional transitions from historical data.

    Request body:
    {
        "entries": [...],
        "min_transition_count": 3  // optional
    }
    """
    try:
        entries = request.entries or []
        min_count = request.min_transition_count

        patterns = engine.transition_tracker.analyze_transitions(
            entries,
            min_transition_count=min_count
        )
        return JSONResponse(content=_wrap_response(
            patterns,
            entries=entries,
            min_transition_count=min_count
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/transitions/track")
async def track_transition(request: TransitionTrackRequest):
    """
    Track specific transition between two states.

    Request body:
    {
        "previous": {...},  // previous analysis result
        "current": {...},   // current analysis result
        "transition_patterns": {...}  // optional, from /advanced/transitions/analyze
    }
    """
    try:
        previous = _normalize_analysis_result(request.previous)
        current = _normalize_analysis_result(request.current)
        patterns = request.transition_patterns

        transition = engine.transition_tracker.track_transition(
            previous,
            current,
            transition_patterns=patterns
        )
        return JSONResponse(content=_wrap_response(
            transition,
            previous=previous,
            current=current,
            transition_patterns=patterns
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/context")
async def apply_context(request: ContextRequest):
    """
    Apply contextual modifications to emotion analysis.

    Request body:
    {
        "analysis_result": {...},
        "recent_entries": [...],  // optional
        "user_timezone": "America/New_York"  // optional
    }
    """
    try:
        analysis_result = _normalize_analysis_result(request.analysis_result)
        recent_entries = request.recent_entries
        user_timezone = request.user_timezone

        contextualized = engine.contextual_modifier.apply_context(
            analysis_result,
            recent_entries=recent_entries,
            user_timezone=user_timezone
        )
        return JSONResponse(content=_wrap_response(
            contextualized,
            analysis_result=analysis_result,
            recent_entries=recent_entries,
            user_timezone=user_timezone
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/congruence")
async def check_congruence(request: CongruenceRequest):
    """
    Check emotional congruence across dimensions.

    Request body:
    {
        "analysis_result": {...},
        "intensity_result": {...},  // optional
        "sarcasm_result": {...},     // optional
        "context_result": {...},     // optional
        "baseline": {...}             // optional
    }
    """
    try:
        analysis_result = _normalize_analysis_result(request.analysis_result)
        intensity_result = request.intensity_result
        sarcasm_result = request.sarcasm_result
        context_result = request.context_result
        baseline = request.baseline

        congruence = engine.congruence_checker.check_congruence(
            analysis_result,
            intensity_result=intensity_result,
            sarcasm_result=sarcasm_result,
            context_result=context_result,
            baseline=baseline
        )
        return JSONResponse(content=_wrap_response(
            congruence,
            analysis_result=analysis_result,
            intensity_result=intensity_result,
            sarcasm_result=sarcasm_result,
            context_result=context_result,
            baseline=baseline
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/predict/learn")
async def learn_prediction_patterns(request: PredictLearnRequest):
    """
    Learn emotional patterns for prediction.

    Request body:
    {
        "entries": [...],
        "baseline": {...}  // optional
    }
    """
    try:
        entries = request.entries or []
        baseline = request.baseline

        result = engine.emotion_predictor.learn_patterns(
            entries,
            baseline=baseline
        )
        return JSONResponse(content=_wrap_response(
            result,
            entries=entries,
            baseline=baseline
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/predict/next")
async def predict_next_emotion(request: PredictNextRequest):
    """
    Predict next likely emotional state.

    Request body:
    {
        "current_analysis": {...},
        "timeframe": "short"  // short/medium/long
    }

    Note: Must call /advanced/predict/learn first
    """
    try:
        current_analysis = _normalize_analysis_result(request.current_analysis)
        timeframe = request.timeframe

        prediction = engine.emotion_predictor.predict_next(
            current_analysis,
            timeframe=timeframe
        )
        return JSONResponse(content=_wrap_response(
            prediction,
            current_analysis=current_analysis,
            timeframe=timeframe
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/triggers/identify")
async def identify_triggers(request: TriggerIdentifyRequest):
    """
    Identify emotional triggers from historical data.

    Request body:
    {
        "entries": [...],
        "min_occurrences": 3  // optional
    }
    """
    try:
        entries = request.entries or []
        min_occ = request.min_occurrences

        triggers = engine.trigger_identifier.identify_triggers(
            entries,
            min_occurrences=min_occ
        )
        return JSONResponse(content=_wrap_response(
            triggers,
            entries=entries,
            min_occurrences=min_occ
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/triggers/check")
async def check_for_trigger(request: TriggerCheckRequest):
    """
    Check if current situation matches known triggers.

    Request body:
    {
        "current_analysis": {...},
        "known_triggers": {...}  // from /advanced/triggers/identify
    }
    """
    try:
        current_analysis = _normalize_analysis_result(request.current_analysis)
        known_triggers = request.known_triggers

        match = engine.trigger_identifier.check_for_trigger(
            current_analysis,
            known_triggers
        )
        return JSONResponse(content=_wrap_response(
            match,
            current_analysis=current_analysis,
            known_triggers=known_triggers
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/group/analyze")
async def analyze_group_emotion(request: GroupAnalyzeRequest):
    """
    Analyze collective emotional state of a group.

    Request body:
    {
        "individual_analyses": [...],  // list of analysis results
        "group_metadata": {...}  // optional
    }
    """
    try:
        individual_analyses = [
            _normalize_analysis_result(item)
            for item in request.individual_analyses
        ]
        group_metadata = request.group_metadata

        group_state = engine.group_analyzer.analyze_group(
            individual_analyses,
            group_metadata=group_metadata
        )
        return JSONResponse(content=_wrap_response(
            group_state,
            individual_analyses=individual_analyses,
            group_metadata=group_metadata
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/cultural/adapt")
async def adapt_for_culture(request: CulturalAdaptRequest):
    """
    Adapt emotion interpretation for cultural context.

    Request body:
    {
        "analysis_result": {...},
        "cultural_profile": {...},  // optional, or auto-detect
        "auto_detect": true  // optional
    }
    """
    try:
        analysis_result = _normalize_analysis_result(request.analysis_result)
        cultural_profile = request.cultural_profile
        auto_detect = request.auto_detect

        adapted = engine.cultural_adapter.adapt(
            analysis_result,
            cultural_profile=cultural_profile,
            auto_detect=auto_detect
        )
        return JSONResponse(content=_wrap_response(
            adapted,
            analysis_result=analysis_result,
            cultural_profile=cultural_profile,
            auto_detect=auto_detect
        ))
    except Exception as e:
        raise _internal_error(e)


@app.post("/advanced/coherence")
async def score_coherence(request: CoherenceScoreRequest):
    """
    Score overall coherence and reliability of analysis.

    Request body:
    {
        "analysis_result": {...},
        "intensity_result": {...},     // optional
        "sarcasm_result": {...},        // optional
        "congruence_result": {...},     // optional
        "context_result": {...},        // optional
        "baseline_deviation": {...},    // optional
        "cultural_adaptation": {...}    // optional
    }
    """
    try:
        analysis_result = _normalize_analysis_result(request.analysis_result)
        intensity_result = request.intensity_result
        sarcasm_result = request.sarcasm_result
        congruence_result = request.congruence_result
        context_result = request.context_result
        baseline_deviation = request.baseline_deviation
        cultural_adaptation = request.cultural_adaptation

        coherence = engine.coherence_scorer.score_coherence(
            analysis_result,
            intensity_result=intensity_result,
            sarcasm_result=sarcasm_result,
            congruence_result=congruence_result,
            context_result=context_result,
            baseline_deviation=baseline_deviation,
            cultural_adaptation=cultural_adaptation
        )
        return JSONResponse(content=_wrap_response(
            coherence,
            analysis_result=analysis_result,
            intensity_result=intensity_result,
            sarcasm_result=sarcasm_result,
            congruence_result=congruence_result,
            context_result=context_result,
            baseline_deviation=baseline_deviation,
            cultural_adaptation=cultural_adaptation
        ))
    except Exception as e:
        raise _internal_error(e)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "engine": "operational",
        "features": [
            "text", "voice", "fusion", "patterns", "summaries",
            "intensity", "sarcasm", "crisis", "baseline", "transitions",
            "context", "congruence", "prediction", "triggers", "group",
            "cultural", "coherence"
        ]
    }


class EmpathyAPI:
    """
    Convenience class for running the API server.

    Usage:
        api = EmpathyAPI()
        api.run(host="127.0.0.1", port=8000)
    """

    def __init__(self):
        self.app = app

    def run(self, host: str = "127.0.0.1", port: int = 8000, **kwargs):
        """
        Run the API server.

        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional uvicorn arguments
        """
        import uvicorn
        uvicorn.run(self.app, host=host, port=port, **kwargs)


def main() -> None:
    """
    Console-script entry point.

    Environment variables:
      - HOST (default: 127.0.0.1, this machine only; the Docker image sets 0.0.0.0)
      - PORT (default: 8000)
      - EMPATHY_ENGINE_* security settings, see api/security.py
    """
    if not security_config.auth_configured:
        sys.exit(
            "Refusing to start: no API keys configured.\n"
            "  Set EMPATHY_ENGINE_API_KEYS (generate one with:\n"
            "    python -c \"import secrets; print(secrets.token_urlsafe(32))\")\n"
            "  or, for local development only, EMPATHY_ENGINE_ALLOW_UNAUTHENTICATED=1"
        )
    host = os.getenv("HOST", "127.0.0.1")

    if security_config.allow_unauthenticated:
        if host not in LOOPBACK_HOSTS:
            sys.exit(
                f"Refusing to start: keys are disabled (EMPATHY_ENGINE_ALLOW_UNAUTHENTICATED) "
                f"but HOST={host} would expose the API beyond this machine.\n"
                "  Use HOST=127.0.0.1, or configure EMPATHY_ENGINE_API_KEYS."
            )
        logger.warning("API keys are DISABLED (local mode); reachable from this machine only")

    try:
        port = int(os.getenv("PORT", "8000"))
    except ValueError:
        port = 8000

    api = EmpathyAPI()
    api.run(host=host, port=port)


# CLI entry point
if __name__ == "__main__":
    main()
