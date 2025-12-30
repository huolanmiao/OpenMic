# Speech Module Plan (ChatTTS-first)

## Goals
- Generate 16 kHz stand-up audio with professional delivery: controlled pacing, pauses (0.8s setup pause, 2s post-punch pause), emphasis, and filler words.
- Emotionally controllable output (speed, pitch/f0 bias, energy) despite ChatTTS lacking explicit emotion IDs.
- Streaming-friendly synthesis to improve UX.
- Quality evaluation (MOS-like proxy + performance metrics) to guide retries or diagnostics.

## Architecture Overview
- `SpeechSynthesizer`: public facade; selects backend (default ChatTTS), orchestrates parsing -> control -> TTS -> post-processing; supports `stream=True` to yield audio chunks.
- Backends: `ChatTTSBackend` (primary). `VALLExBackend` not included (per decision), but interface kept flexible.
- Processing pipeline: text/script -> marker parsing -> filler insertion -> emotion/tempo assignment -> prosody control tokens -> TTS -> post-processing -> evaluation report.

## Submodules

### 1) PerformanceMarkerParser
- Input: raw script with optional inline markers like (*pause*), (*stress:word*), (*tone:吐槽*).
- Output: structured markers (segments with roles: setup/punch, pauses, stress targets, tone hints, speed hints).
- Method: regex + punctuation heuristics; default pauses at commas/periods; ensure punchline pre-pause 0.8s and post-pause 2.0s; fallback markers when none provided.

### 2) FillerInjector
- Inserts fillers ("呃", "那个", "就是") around long pauses or clause starts with capped frequency.
- Rules: avoid adjacent to stressed keywords; probability tuned by style; deterministic option for tests.

### 3) EmotionProfile / EmotionController
- Profiles map comedic intent (吐槽/兴奋/无语/平稳) to parameters: speed scale, f0 shift, energy gain, sampling temperature.
- Controller assigns profiles per segment (setup calmer/slower, punch normal or slightly faster, outro relaxed) and exposes a compact control object consumed by prosody.

### 4) ProsodyController
- Converts markers + emotion profile into backend-ready directives:
  - Tempo per segment (speed scale)
  - Pauses as explicit silence tokens (0.8s, 2.0s)
  - Emphasis via duration/energy boost or repeated tokens
  - Pitch/f0 bias per segment
- Produces a backend-agnostic prosody plan consumed by ChatTTSBackend.

### 5) ChatTTSBackend
- Responsibilities: load/init ChatTTS, accept text + prosody plan, emit 16 kHz PCM.
- Controls: silence tokens for pauses, per-segment speed/energy/pitch adjustments, sampling temperature.
- Streaming: segment-wise synthesis; yield PCM chunks in order, or fallback to full buffer when stream=False.

### 6) AudioPostProcessor (lightweight)
- Ensure 16 kHz mono; normalize loudness; optional fade-in/out; concat segment chunks; output bytes or numpy/torch tensor.

### 7) SpeechEvaluator (proxy)
- Metrics: pause alignment (planned vs actual duration), stress hit rate (keyword proximity), tempo adherence, simple MOS proxy (rule/ML placeholder).
- Output: diagnostic report; hooks for future MOSNet/LLM rater.

## Public API Sketch
- `SpeechSynthesizer.synthesize(script: str, stream: bool=False) -> bytes | Iterator[bytes]`
- Optional params: `style`, `emotion_profile`, `seed`, `max_len_s`, `evaluate: bool` to return `(audio, report)`.

## Dependencies
- Core: `torch`, `torchaudio`, `numpy`, `chattts` package (to be added to requirements when implementing).
- Optional: `pydub` for fades; `fastapi`/`streamlit` already present for higher layers.

## Non-Goals (for now)
- VALL-E X backend.
- Multispeaker diarization.
- Advanced MOS model integration (placeholder hooks only).

## Milestones
1) Define interfaces/classes and stubs in `src/speech` (no heavy deps yet).
2) Implement rule-based parser, fillers, prosody controller; unit tests for deterministic paths.
3) Integrate ChatTTS backend with streaming and post-processing; add dependency.
4) Add evaluator hooks and simple rule-based scoring.
5) Wire into orchestrator/CLI (pending approval if outside `speech`).
