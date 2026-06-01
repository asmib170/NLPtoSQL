import { useEffect, useState, useCallback, useRef } from 'react'
import { Header } from './components/Header'
import { ChatWindow } from './components/ChatWindow'
import { ChatSidebar } from './components/ChatSidebar'
import { useThreads } from './hooks/useThreads'
import { useTheme } from './hooks/useTheme'
import { fetchDbContext, type DbContext } from './api/agentService'
import styles from './App.module.css'

const SIDEBAR_DEFAULT = 320
const SIDEBAR_MIN = 320
const SIDEBAR_MAX = 640

export default function App() {
  const { theme, toggle } = useTheme()
  const {
    threads,
    activeThread,
    activeThreadId,
    isLoading,
    createNewThread,
    selectThread,
    sendMessage,
    stopStreaming,
    deleteThread,
  } = useThreads()

  const [dbContext, setDbContext] = useState<DbContext | null>(null)
  const [isLoadingContext, setIsLoadingContext] = useState(true)
  const [sidebarWidth, setSidebarWidth] = useState(SIDEBAR_DEFAULT)
  const isDragging = useRef(false)

  useEffect(() => {
    setIsLoadingContext(true)
    fetchDbContext().then(ctx => {
      if (ctx) setDbContext(ctx)
      setIsLoadingContext(false)
    })
  }, [])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isDragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return
      const newWidth = window.innerWidth - e.clientX
      setSidebarWidth(Math.max(SIDEBAR_MIN, Math.min(SIDEBAR_MAX, newWidth)))
    }

    const handleMouseUp = () => {
      isDragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [])

  return (
    <div className={styles.app} data-theme={theme}>
      <Header
        theme={theme}
        onToggleTheme={toggle}
        activeThread={activeThread}
      />

      <div className={styles.body}>
        <ChatWindow
          messages={activeThread?.messages ?? []}
          theme={theme}
          onSendSuggestion={sendMessage}
          description={dbContext?.description}
          suggestions={dbContext?.sample_questions ?? null}
          isLoadingContext={isLoadingContext}
        />

        {/* Drag handle */}
        <div className={styles.resizeHandle} onMouseDown={handleMouseDown} />

        <div style={{ width: sidebarWidth, minWidth: sidebarWidth }}>
          <ChatSidebar
            threads={threads}
            activeThreadId={activeThreadId}
            isLoading={isLoading}
            onNewChat={createNewThread}
            onSelectThread={selectThread}
            onDeleteThread={deleteThread}
            onSend={sendMessage}
            onStop={stopStreaming}
          />
        </div>
      </div>
    </div>
  )
}
