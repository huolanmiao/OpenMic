# Speech Module

## 1. Architectural Overview
The Speech Module is designed as a specialized rendering engine that transforms text scripts into stand-up comedy performances. Unlike generic TTS systems, it prioritizes **prosodic expressiveness**—incorporating laughter, pauses, and dynamic pacing to deliver punchlines effectively. The core implementation relies on a sequential pipeline architecture (`StandupSpeechPipeline`) that orchestrates text refinement, prosody control, and audio synthesis in a cohesive stream.

## 2. Implementation Pipeline
The processing flow begins with the **Text Refinement** stage. Here, the system leverages Large Language Models (LLMs) to normalize raw scripts and intelligently inject performance markers. This step converts written text into oral forms and inserts cues for laughter (`[laugh]`) or dramatic pauses (`[uv_break][lbreak]`) based on the semantic context of the jokes. Following this, a **Filler Injection** mechanism probabilistically inserts hesitation markers (like "uh", "you know") to mimic the spontaneity of live comedy, using a hybrid approach of statistical insertion and LLM-based syntax checking.

The refined text is then processed by the **Emotion & Rhythm Controller**. This component analyzes speech segments to assign specific prosodic parameters, such as slowing down for setups or pausing before punchlines. Finally, the **TTS Engine** (wrapping ChatTTS) synthesizes the audio segments. These distinct clips are stitched together and normalized by the **Audio Post-Processor**, ensuring a consistent and professional broadcast-quality output at 16kHz.

## 3. System Design & Robustness
A key engineering focus was **fail-safe robustness**. The system implements a **dual-mode operation**: while it defaults to high-quality LLM-based processing for text refinement and filler injection, it automatically degrades to a **Rule-Based Fallback Mode** if external APIs are unreachable. This ensures the pipeline remains functional even in offline environments, using Regex cleaners to maintain basic synthesis capabilities.

Furthermore, the module is designed for **flexibility and integration**. It shares the unified configuration system with the upstream agents and features a **hot-swappable voice banking mechanism**. To introduce a new comedian persona, developers simply place a speaker embedding file (`.pt`) into the `voices/` directory. The system automatically indexes these assets at runtime, allowing for instant switching between different character styles and tonal attributes without altering a single line of code.
