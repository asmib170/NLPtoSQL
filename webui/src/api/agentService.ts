/**
 * agentService.ts — single integration point for the agent backend.
 *
 * Phase 1: FastAPI local server  (VITE_AGENT_URL=http://localhost:8000)
 * Phase 2: AWS AgentCore Runtime (VITE_AGENT_URL=https://your-agentcore-endpoint)
 *
 * To switch backends, only this file and .env need to change.
 */

const BASE_URL = import.meta.env.VITE_AGENT_URL ?? 'http://localhost:8000'

export interface StreamCallbacks {
  onToken: (token: string) => void
  onThinking: (text: string) => void
  onTool: (toolName: string) => void
  onMetrics: (metrics: Record<string, unknown>) => void
  onDone: () => void
  onError: (error: string) => void
}

/**
 * Send a message to the agent and stream the response via SSE.
 * Returns an AbortController so the caller can cancel mid-stream.
 */
export function streamMessage(message: string, callbacks: StreamCallbacks, threadId?: string): AbortController {
  const controller = new AbortController()

  const run = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, thread_id: threadId ?? '' }),
        signal: controller.signal,
      })

      if (!response.ok) {
        callbacks.onError(`Server error: ${response.status} ${response.statusText}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        callbacks.onError('No response body from server.')
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const payload = line.slice(6)

          if (payload === '[DONE]') {
            callbacks.onDone()
            return
          }

          if (payload.startsWith('[ERROR]')) {
            callbacks.onError(payload.slice(8))
            return
          }

          if (payload.startsWith('[THINKING] ')) {
            const text = payload.slice(11).replace(/\\n/g, '\n')
            callbacks.onThinking(text)
            continue
          }

          if (payload.startsWith('[TOOL] ')) {
            const toolName = payload.slice(7)
            callbacks.onTool(toolName)
            continue
          }

          if (payload.startsWith('[METRICS] ')) {
            try {
              const metrics = JSON.parse(payload.slice(10))
              callbacks.onMetrics(metrics)
            } catch { /* ignore parse errors */ }
            continue
          }

          // Regular text token
          const text = payload.replace(/\\n/g, '\n')
          callbacks.onToken(text)
        }
      }

      callbacks.onDone()
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      callbacks.onError((err as Error).message ?? 'Unknown error')
    }
  }

  run()
  return controller
}

/** Simple health check — resolves true if the backend is reachable. */
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/health`, { signal: AbortSignal.timeout(3000) })
    return res.ok
  } catch {
    return false
  }
}

/** Fetch DB context (name, description, sample questions) from the backend. */
export interface DbContext {
  db_name: string
  description: string
  tables: string[]
  sample_questions: string[]
}

export async function fetchDbContext(): Promise<DbContext | null> {
  try {
    const res = await fetch(`${BASE_URL}/api/context`, { signal: AbortSignal.timeout(30000) })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

// ------------------------------------------------------------------ //
// Thread persistence API (metadata only — messages handled by session manager)
// ------------------------------------------------------------------ //

export interface ThreadMeta {
  id: string          // UUID4 session ID (36 chars)
  title: string
  summary: string
  created_at: string
  updated_at: string
  message_count: number
}

/** Fetch all thread metadata from the backend. */
export async function fetchThreads(): Promise<ThreadMeta[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/threads`)
    if (!res.ok) return []
    return await res.json()
  } catch {
    return []
  }
}

/** Create a new thread on the backend. Returns metadata with UUID4 session ID. */
export async function createThread(title: string): Promise<ThreadMeta | null> {
  try {
    const res = await fetch(`${BASE_URL}/api/threads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

/** Update thread metadata (title, message_count). */
export async function updateThread(threadId: string, data: { title?: string; summary?: string; message_count?: number }): Promise<void> {
  try {
    await fetch(`${BASE_URL}/api/threads/${threadId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
  } catch {
    // silent fail
  }
}

/** Generate a short title and summary for a thread using the LLM. */
export async function generateThreadTitle(threadId: string): Promise<{ title: string; summary: string } | null> {
  try {
    const res = await fetch(`${BASE_URL}/api/threads/generate-title`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: threadId }),
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

/** Delete a thread from the backend. */
export async function deleteThreadApi(threadId: string): Promise<void> {
  try {
    await fetch(`${BASE_URL}/api/threads/${threadId}`, { method: 'DELETE' })
  } catch {
    // silent fail
  }
}
