import { useEffect, useRef } from 'react'
import { Sparkles } from 'lucide-react'
import { MessageBubble } from './MessageBubble'
import type { Message, Theme } from '../types'
import styles from './ChatWindow.module.css'

interface ChatWindowProps {
  messages: Message[]
  theme: Theme
  onSendSuggestion: (text: string) => void
  description?: string
  suggestions?: string[] | null
  isLoadingContext?: boolean
}

export function ChatWindow({ messages, theme, onSendSuggestion, description, suggestions, isLoadingContext }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Show empty state when no messages
  if (messages.length === 0) {
    return (
      <div className={styles.main}>
        <div className={styles.empty}>
          <h2 className={styles.emptyTitle}>Ask anything about your data</h2>
          <p className={styles.emptySubtitle}>
            {description ?? "I'll query your database and explain the results."}
          </p>

          {isLoadingContext ? (
            <div className={styles.loadingContainer}>
              <div className={styles.loadingPulse}>
                <Sparkles size={20} className={styles.sparkle} />
                <span>Generating suggestions from your schema…</span>
              </div>
              <div className={styles.skeletonGrid}>
                {[...Array(6)].map((_, i) => (
                  <div key={i} className={styles.skeletonPill} />
                ))}
              </div>
            </div>
          ) : suggestions && suggestions.length > 0 ? (
            <div className={styles.suggestions}>
              {suggestions.map((s) => (
                <button
                  key={s}
                  className={styles.suggestion}
                  onClick={() => onSendSuggestion(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    )
  }

  // Show active chat messages
  return (
    <div className={styles.main}>
      <div className={styles.messages}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} theme={theme} onSendSuggestion={onSendSuggestion} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
