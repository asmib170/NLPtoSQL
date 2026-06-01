import { Plus, MessageSquare, Trash2 } from 'lucide-react'
import { InputBar } from './InputBar'
import type { Thread } from '../hooks/useThreads'
import styles from './ChatSidebar.module.css'

interface ChatSidebarProps {
  threads: Thread[]
  activeThreadId: string | null
  isLoading: boolean
  onNewChat: () => void
  onSelectThread: (id: string) => void
  onDeleteThread: (id: string) => void
  onSend: (text: string) => void
  onStop: () => void
}

export function ChatSidebar({
  threads,
  activeThreadId,
  isLoading,
  onNewChat,
  onSelectThread,
  onDeleteThread,
  onSend,
  onStop,
}: ChatSidebarProps) {
  return (
    <aside className={styles.sidebar}>
      {/* New Chat button */}
      <button className={styles.newChatBtn} onClick={onNewChat}>
        <Plus size={16} />
        <span>New Chat</span>
      </button>

      {/* Section header */}
      <div className={styles.sectionHeader}>
        <MessageSquare size={14} />
        <span>Chat History</span>
      </div>

      {/* Thread list */}
      <div className={styles.threadList}>
        {threads.length === 0 ? (
          <div className={styles.emptyThreads}>
            <span>No conversations yet</span>
          </div>
        ) : (
          threads.map(thread => (
            <div
              key={thread.id}
              className={`${styles.threadItem} ${thread.id === activeThreadId ? styles.active : ''}`}
              onClick={() => onSelectThread(thread.id)}
            >
              <div className={styles.threadContent}>
                <span className={styles.threadTitle}>{thread.title}</span>
                <span className={styles.threadMeta}>
                  {thread.summary || `${thread.messageCount || thread.messages.length} messages`}
                </span>
              </div>
              <button
                className={styles.deleteBtn}
                onClick={(e) => { e.stopPropagation(); onDeleteThread(thread.id) }}
                title="Delete thread"
                aria-label="Delete thread"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))
        )}
      </div>

      {/* Input area at bottom */}
      <div className={styles.inputArea}>
        <InputBar onSend={onSend} onStop={onStop} isLoading={isLoading} />
      </div>
    </aside>
  )
}
