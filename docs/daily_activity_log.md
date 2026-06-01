# Daily Activity Log — Continuation

## Thursday, 28/05/26

| Time Slot | Activity |
|-----------|----------|
| 9–10 AM | Building FastAPI streaming server (`server.py`) with SSE (Server-Sent Events) for real-time agent response streaming to the browser |
| 10–11 AM | Implementing CORS middleware, health endpoint, and `/api/chat` POST endpoint that accepts user messages and streams agent responses |
| 11–12 PM | Scaffolding React + Vite + TypeScript frontend — project setup, package.json, tsconfig, vite config with proxy to backend |
| 12–1 PM | **Lunch Break** |
| 1–2 PM | Building core React components: `Header` (with status indicator, theme toggle), `InputBar` (auto-resize textarea, send/stop buttons), `ChatWindow` (message list with auto-scroll) |
| 2–3 PM | Implementing `MessageBubble` component with full markdown rendering (react-markdown + remark-gfm), syntax-highlighted code blocks, and responsive table styling |
| 3–4 PM | Creating `agentService.ts` — single backend abstraction layer handling SSE stream parsing for `[THINKING]`, `[TOOL]`, `[METRICS]`, `[DONE]` event types. Designed for easy swap to AgentCore Runtime |
| 4–5 PM | Implementing dark/light mode with CSS variables, message slide-in animations, and `start.bat` script to launch both backend and frontend together |

---

## Friday, 29/05/26

| Time Slot | Activity |
|-----------|----------|
| 9–10 AM | Adding extended thinking to BedrockModel configuration (4096 token budget, temperature=1) and updating SSE generator to emit `[THINKING]` and `[TOOL]` events separately |
| 10–11 AM | Building collapsible sections in response bubbles — Thinking (auto-collapses after streaming), SQL Query (collapsed by default), and Suggested Follow-Up (clickable pills) |
| 11–12 PM | Implementing session management using Strands' built-in `FileSessionManager` — UUID4 session IDs (36 chars, AgentCore-compatible), conversation persistence per thread |
| 12–1 PM | **Lunch Break** |
| 1–2 PM | Building resizable right sidebar with chat history list, "New Chat" button, thread selection, and delete functionality. Created `useThreads` hook for multi-thread state management |
| 2–3 PM | Creating storage layer — abstract `ThreadIndexStorage` interface with `JsonFileThreadIndex` implementation for thread metadata. Added `/api/threads` CRUD endpoints and session message loading |
| 3–4 PM | Adding metrics popup (info icon) showing TTFT, total latency, input/output tokens, prompt cache reads/writes, and estimated cost. Wiring `event_loop_metrics` from Strands agent |
| 4–5 PM | Creating architecture documentation with Graphviz diagram (`docs/architecture.png`), detailed component explanations, data flow documentation, and AgentCore migration path |
