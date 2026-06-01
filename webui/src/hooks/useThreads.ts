import { useState, useCallback, useRef, useEffect } from 'react'
import type { Message } from '../types'
import {
  streamMessage,
  fetchThreads,
  createThread as createThreadApi,
  updateThread as updateThreadApi,
  deleteThreadApi,
  generateThreadTitle,
  type ThreadMeta,
} from '../api/agentService'

export interface Thread {
  id: string        // UUID4 session ID (36 chars, meets AgentCore 33+ requirement)
  title: string
  summary: string
  messages: Message[]
  createdAt: Date
  messageCount: number
}

function threadMetaToThread(meta: ThreadMeta): Thread {
  return {
    id: meta.id,
    title: meta.title,
    summary: meta.summary || '',
    messages: [],
    createdAt: new Date(meta.created_at),
    messageCount: meta.message_count,
  }
}

export function useThreads() {
  const [threads, setThreads] = useState<Thread[]>([])
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const activeThread = threads.find(t => t.id === activeThreadId) ?? null

  // Load thread index from backend on mount
  useEffect(() => {
    fetchThreads().then(metas => {
      if (metas.length > 0) {
        setThreads(metas.map(threadMetaToThread))
      }
    })
  }, [])

  const createNewThread = useCallback(() => {
    abortRef.current?.abort()
    setIsLoading(false)

    // Create on backend first to get the UUID4 session ID
    createThreadApi('New Chat').then(meta => {
      if (meta) {
        const newThread: Thread = {
          id: meta.id,  // UUID4 from backend
          title: meta.title,
          messages: [],
          createdAt: new Date(meta.created_at),
          messageCount: 0,
        }
        setThreads(prev => [newThread, ...prev])
        setActiveThreadId(meta.id)
      }
    })
  }, [])

  const selectThread = useCallback((threadId: string) => {
    abortRef.current?.abort()
    setIsLoading(false)
    setActiveThreadId(threadId)

    // Load messages from backend if thread has no messages in local state
    const thread = threads.find(t => t.id === threadId)
    if (thread && thread.messages.length === 0) {
      fetch(`/api/threads/${threadId}`)
        .then(res => res.json())
        .then(data => {
          if (data.messages && data.messages.length > 0) {
            setThreads(prev =>
              prev.map(t =>
                t.id === threadId
                  ? {
                      ...t,
                      messages: data.messages.map((m: { id: string; role: string; content: string; timestamp: string }) => ({
                        id: m.id,
                        role: m.role as 'user' | 'assistant',
                        content: m.content,
                        timestamp: new Date(m.timestamp),
                        isStreaming: false,
                      })),
                      messageCount: data.messages.length,
                    }
                  : t
              )
            )
          }
        })
        .catch(() => { /* silent */ })
    }
  }, [threads])

  const sendMessage = useCallback((text: string) => {
    if (!text.trim() || isLoading) return

    let threadId = activeThreadId

    // If no active thread, we need to create one first
    if (!threadId || !threads.find(t => t.id === threadId)) {
      // Create synchronously in UI, then persist
      createThreadApi(text.trim().slice(0, 60)).then(meta => {
        if (meta) {
          const newThread: Thread = {
            id: meta.id,
            title: text.trim().slice(0, 60),
            messages: [],
            createdAt: new Date(meta.created_at),
            messageCount: 0,
          }
          setThreads(prev => [newThread, ...prev])
          setActiveThreadId(meta.id)
          // Now send the message with the real session ID
          _doSend(text.trim(), meta.id)
        }
      })
      return
    }

    _doSend(text.trim(), threadId)
  }, [isLoading, activeThreadId, threads])

  const _doSend = (text: string, threadId: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }

    const assistantId = crypto.randomUUID()
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      thinking: '',
      tools: [],
      timestamp: new Date(),
      isStreaming: true,
    }

    // Update local state
    setThreads(prev =>
      prev.map(t => {
        if (t.id !== threadId) return t
        const isFirst = t.messages.length === 0
        return {
          ...t,
          title: isFirst ? text.slice(0, 60) : t.title,
          messages: [...t.messages, userMsg, assistantMsg],
          messageCount: t.messageCount + 2,
        }
      })
    )

    // Update title on backend if first message
    const thread = threads.find(t => t.id === threadId)
    if (thread && thread.messages.length === 0) {
      updateThreadApi(threadId, { title: text.slice(0, 60) })
    }

    setIsLoading(true)

    // Pass threadId as session_id to the agent
    abortRef.current = streamMessage(text, {
      onToken: (token) => {
        setThreads(prev =>
          prev.map(t =>
            t.id === threadId
              ? { ...t, messages: t.messages.map(m => m.id === assistantId ? { ...m, content: m.content + token } : m) }
              : t
          )
        )
      },
      onThinking: (thinkText) => {
        setThreads(prev =>
          prev.map(t =>
            t.id === threadId
              ? { ...t, messages: t.messages.map(m => m.id === assistantId ? { ...m, thinking: (m.thinking ?? '') + thinkText } : m) }
              : t
          )
        )
      },
      onTool: (toolName) => {
        setThreads(prev =>
          prev.map(t =>
            t.id === threadId
              ? { ...t, messages: t.messages.map(m => m.id === assistantId && !(m.tools ?? []).includes(toolName) ? { ...m, tools: [...(m.tools ?? []), toolName] } : m) }
              : t
          )
        )
      },
      onMetrics: (metrics) => {
        setThreads(prev =>
          prev.map(t =>
            t.id === threadId
              ? { ...t, messages: t.messages.map(m => m.id === assistantId ? { ...m, metrics: metrics as Message['metrics'] } : m) }
              : t
          )
        )
      },
      onDone: () => {
        setThreads(prev => {
          const updated = prev.map(t =>
            t.id === threadId
              ? { ...t, messages: t.messages.map(m => m.id === assistantId ? { ...m, isStreaming: false } : m) }
              : t
          )

          // Generate/update title after every response
          const currentThread = updated.find(t => t.id === threadId)
          if (currentThread) {
            generateThreadTitle(threadId).then(result => {
              if (result) {
                setThreads(p => p.map(t =>
                  t.id === threadId ? { ...t, title: result.title, summary: result.summary } : t
                ))
                updateThreadApi(threadId, { title: result.title, summary: result.summary })
              }
            })
          }

          return updated
        })
        updateThreadApi(threadId, { message_count: (thread?.messageCount ?? 0) + 2 })
        setIsLoading(false)
      },
      onError: (error) => {
        setThreads(prev =>
          prev.map(t =>
            t.id === threadId
              ? { ...t, messages: t.messages.map(m => m.id === assistantId ? { ...m, content: `Error: ${error}`, isStreaming: false, isError: true } : m) }
              : t
          )
        )
        setIsLoading(false)
      },
    }, threadId)  // <-- session_id passed here
  }

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    if (activeThreadId) {
      setThreads(prev =>
        prev.map(t =>
          t.id === activeThreadId
            ? { ...t, messages: t.messages.map(m => m.isStreaming ? { ...m, isStreaming: false } : m) }
            : t
        )
      )
    }
    setIsLoading(false)
  }, [activeThreadId])

  const deleteThread = useCallback((threadId: string) => {
    setThreads(prev => prev.filter(t => t.id !== threadId))
    if (activeThreadId === threadId) {
      setActiveThreadId(null)
    }
    deleteThreadApi(threadId)
  }, [activeThreadId])

  return {
    threads,
    activeThread,
    activeThreadId,
    isLoading,
    createNewThread,
    selectThread,
    sendMessage,
    stopStreaming,
    deleteThread,
  }
}
