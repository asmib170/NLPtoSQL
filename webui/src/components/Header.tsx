import { Moon, Sun, Download } from 'lucide-react'
import { StatusIndicator } from './StatusIndicator'
import type { Theme, Message } from '../types'
import { exportToMarkdown, exportToHtml, downloadFile } from '../utils/exportUtils'
import styles from './Header.module.css'

interface HeaderProps {
  theme: Theme
  onToggleTheme: () => void
  activeThread?: { id: string; title: string; messages: Message[] } | null
}

export function Header({ theme, onToggleTheme, activeThread }: HeaderProps) {
  const handleExportMd = async () => {
    if (!activeThread || activeThread.messages.length === 0) return
    const md = await exportToMarkdown(activeThread.messages, activeThread.title)
    downloadFile(md, `${activeThread.title.replace(/\s+/g, '_')}.md`, 'text/markdown')
  }

  const handleExportHtml = async () => {
    if (!activeThread || activeThread.messages.length === 0) return
    const html = await exportToHtml(activeThread.messages, activeThread.title)
    downloadFile(html, `${activeThread.title.replace(/\s+/g, '_')}.html`, 'text/html')
  }

  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <img src="/favicon.svg" alt="NLP to SQL" className={styles.logo} />
        <div className={styles.title}>
          <span className={styles.titleMain}>NLP to SQL</span>
          <span className={styles.titleSub}>AI Data Assistant</span>
        </div>
      </div>

      <div className={styles.center}>
        <StatusIndicator />
      </div>

      <div className={styles.actions}>
        {activeThread && activeThread.messages.length > 0 && (
          <>
            <button className={styles.exportBtn} onClick={handleExportMd} title="Export thread as Markdown">
              <Download size={14} />
              <span>MD</span>
            </button>
            <button className={styles.exportBtn} onClick={handleExportHtml} title="Export thread as HTML">
              <Download size={14} />
              <span>HTML</span>
            </button>
          </>
        )}
        <button
          className={styles.iconBtn}
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          aria-label="Toggle theme"
        >
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>
      </div>
    </header>
  )
}
