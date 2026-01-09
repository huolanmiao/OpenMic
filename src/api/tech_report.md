# Technical Report: Web API & Interaction Layer (Task 4)

## 1. Executive Summary

This module serves as the interface layer for the OpenMic system, bridging the gap between end-users and the underlying Multi-Agent System (MAS) and Text-to-Speech (TTS) engines. The primary objective was to transform the asynchronous, long-running nature of AI content generation into a responsive and interactive user experience.

We implemented a **FastAPI** backend to handle task orchestration and a **Streamlit** frontend to provide a "Script-Edit-Perform" workflow. A key technical achievement in this module is the implementation of a real-time event streaming mechanism that exposes the internal "thought process" of the AutoGen agents to the user interface, improving system transparency.

## 2. Architectural Design

### Asynchronous Client-Server Model
Generating a full comedy script involves multiple rounds of agent dialogue, and synthesizing audio is computationally expensive. A traditional synchronous HTTP request-response cycle would result in timeouts and a poor user experience.

To address this, we adopted an **Asynchronous Polling Architecture**:
1.  **Task Submission:** The client submits a request. The server immediately returns a unique `task_id` and spawns a background process.
2.  **State Management:** The server maintains a lightweight, in-memory state dictionary (`TASKS`) to track the lifecycle of every request (Pending $\to$ Processing $\to$ Completed/Failed).
3.  **Client Polling:** The frontend periodically polls the server to retrieve the current status, progress percentage, and granular stage descriptions.



## 3. Backend Implementation (FastAPI)

The backend logic resides in `src/api/backend_server.py` and focuses on orchestrating the AI components without blocking the main server loop.

### Real-Time Agent Monitoring via Event Streaming
One of the significant challenges was visualizing the Multi-Agent collaboration. Standard execution methods treated the agent group chat as a "black box," returning only the final result.

We refactored the execution logic to use **Event Streaming**. Instead of waiting for the full chat completion, the system now iterates through the `team.run_stream()` generator. This allows us to intercept every message sent by any agent (e.g., the *ComedyDirector* defining strategy or the *AudienceAnalyzer* refining jokes) in real-time. These events are immediately pushed to the global `TASKS` state, allowing the frontend to display exactly which agent is speaking and what they are doing.

### Optimized Audio Generation Pipeline
The Text-to-Speech (TTS) component, powered by the `StandupSpeechPipeline`, is resource-intensive. We implemented two specific optimizations to ensure server stability:

1.  **Singleton Pattern & Lazy Loading:** The TTS model is large and slow to initialize. We implemented a singleton pattern that loads the model only upon the first request to `/voices` or `/generate_audio`. This prevents unnecessary memory consumption during script-only workflows.
2.  **Non-Blocking Inference:** Since PyTorch inference is a synchronous, CPU/GPU-bound operation, it blocks the FastAPI event loop. We wrapped the inference calls using `asyncio.to_thread`. This offloads the computation to a separate thread pool, ensuring that the API remains responsive to health checks and status queries even while generating audio.

## 4. Frontend Implementation (Streamlit)

The frontend is a Single Page Application (SPA) designed to guide the user through the creative process.

### The "Generate-Edit-Perform" Workflow
We moved away from a "one-click" generation approach to a more human-in-the-loop workflow:
1.  **Generation:** The user inputs a topic, and the Multi-Agent system drafts a script.
2.  **Intervention:** The user can edit the generated script directly in the UI. This is crucial for fixing jokes that might not land or adding personal touches.
3.  **Performance:** The *revised* script is sent to the TTS engine.

### Session State Persistence
Streamlit reruns the entire script on every user interaction. To prevent data loss (e.g., losing the generated script when selecting a voice), we utilized `st.session_state` to persist the script text, audio binary data, and user configuration across re-renders.

## 5. Technical Challenges & Solutions

### Challenge 1: AutoGen Early Termination
**Issue:** Initially, we attempted to monitor agent progress by injecting a callback function into the `SelectorGroupChat`'s workflow selector. However, this side effect interfered with the internal state machine of AutoGen 0.10+, causing the conversation to terminate prematurely or behave unpredictably.
**Solution:** We decoupled the monitoring logic from the selection logic. We reverted the selector to a pure function and moved the progress tracking to the outer orchestration layer using the `run_stream` asynchronous iterator. This ensures the agents operate undisturbed while we passively observe their output.

### Challenge 2: Concurrency Blocking
**Issue:** When User A requested audio generation, the server's main thread would lock up during tensor calculation, causing User B's status polling requests to hang.
**Solution:** By implementing `asyncio.to_thread` for the TTS pipeline, we released the Global Interpreter Lock (GIL) for I/O operations, allowing the FastAPI server to handle concurrent status requests seamlessly while heavy computation occurs in the background.

## 6. Interface Specification

The system exposes the following RESTful endpoints:

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/generate` | POST | Initiates the Multi-Agent script generation workflow. |
| `/generate_audio` | POST | Initiates the TTS pipeline for a specific script text. |
| `/tasks/{task_id}` | GET | Returns the current status, progress (0-1.0), and active stage description. |
| `/tasks/{task_id}/result` | GET | Retrieves the final artifact (text script or audio URL). |
| `/voices` | GET | Returns available voice profiles with metadata (gender, style). |

## 7. Conclusion

The implemented module successfully wraps complex, long-running AI processes into a user-friendly web service. The architecture is resilient to high-latency tasks and provides high transparency into the AI's decision-making process, meeting the project's requirements for an interactive comedy creation tool.