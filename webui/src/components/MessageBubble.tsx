import { useState, useEffect, useMemo, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { User, Bot, AlertCircle, ChevronDown, ChevronRight, Brain, Code2, Wrench, Info, Sparkles, CircleUser, Download } from 'lucide-react'
import type { Message } from '../types'
import { exportToMarkdown, exportToHtml, downloadFile } from '../utils/exportUtils'
import styles from './MessageBubble.module.css'

interface MessageBubbleProps {
  message: Message
  theme: 'light' | 'dark'
  onSendSuggestion?: (text: string) => void
}

function extractSql(content: string): { sql: string; rest: string } {
  const sqlBlocks: string[] = []
  let rest = content.replace(/```sql\n([\s\S]*?)```/g, (_match, code) => {
    sqlBlocks.push(code.trim())
    return ''
  })
  // Remove leftover "SQL Query" or "SQL Query Executed" headings
  rest = rest.replace(/^#{1,4}\s*SQL\s*Query\s*(Executed)?\s*$/gm, '')
  // Remove "**SQL Query**" or "**SQL Query:**" bold headings
  rest = rest.replace(/^\*\*SQL\s*Query\s*:?\*\*\s*$/gm, '')
  return { sql: sqlBlocks.join('\n\n'), rest: rest.trim() }
}

function extractSuggestions(content: string): { suggestions: string[]; contentWithout: string } {
  const suggestions: string[] = []
  const lines = content.split('\n')
  let inSuggestions = false
  const filteredLines: string[] = []

  for (const line of lines) {
    const lower = line.toLowerCase()
    if (
      lower.includes('follow-up question') ||
      lower.includes('suggested follow') ||
      lower.includes('you might also ask') ||
      lower.includes('questions you could ask')
    ) {
      inSuggestions = true
      continue
    }

    if (inSuggestions) {
      // Match numbered or bulleted list items
      const match = line.match(/^[\s]*(?:\d+[\.\)]\s*|[-•*]\s*)(.+)/)
      if (match) {
        const q = match[1].replace(/\*\*/g, '').replace(/[""]/g, '').trim()
        if (q.length > 10 && q.length < 200) {
          suggestions.push(q)
        }
      } else if (line.trim() === '') {
        // blank line might end the section
        if (suggestions.length > 0) inSuggestions = false
      } else {
        inSuggestions = false
        filteredLines.push(line)
      }
    } else {
      filteredLines.push(line)
    }
  }

  return { suggestions: suggestions.slice(0, 3), contentWithout: filteredLines.join('\n') }
}

function MetricsPopup({ metrics }: { metrics: NonNullable<Message['metrics']> }) {
  const [open, setOpen] = useState(false)

  return (
    <div className={styles.metricsWrapper}>
      <button
        className={styles.metricsBtn}
        onClick={() => setOpen(!open)}
        title="View metrics"
        aria-label="View response metrics"
      >
        <Info size={13} />
      </button>
      {open && (
        <div className={styles.metricsPopup}>
          <div className={styles.metricsGrid}>
            {metrics.model && (
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Model</span>
                <span className={styles.metricValue}>{metrics.model.split('.').pop()?.replace(/-v\d.*/, '') ?? metrics.model}</span>
              </div>
            )}
            {metrics.ttft_ms != null && (
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Time to First Token</span>
                <span className={styles.metricValue}>{(metrics.ttft_ms / 1000).toFixed(2)}s</span>
              </div>
            )}
            {metrics.latency_ms != null && (
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Total Latency</span>
                <span className={styles.metricValue}>{(metrics.latency_ms / 1000).toFixed(2)}s</span>
              </div>
            )}
            {metrics.input_tokens != null && (
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Input Tokens</span>
                <span className={styles.metricValue}>{metrics.input_tokens.toLocaleString()}</span>
              </div>
            )}
            {metrics.output_tokens != null && (
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Output Tokens</span>
                <span className={styles.metricValue}>{metrics.output_tokens.toLocaleString()}</span>
              </div>
            )}
            {metrics.cache_read_tokens != null && metrics.cache_read_tokens > 0 && (
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Cache Read</span>
                <span className={styles.metricValue}>{metrics.cache_read_tokens.toLocaleString()} tokens</span>
              </div>
            )}
            {metrics.cache_write_tokens != null && metrics.cache_write_tokens > 0 && (
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Cache Write</span>
                <span className={styles.metricValue}>{metrics.cache_write_tokens.toLocaleString()} tokens</span>
              </div>
            )}
            {metrics.estimated_cost_usd != null && (
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Est. Cost</span>
                <span className={styles.metricValue}>${metrics.estimated_cost_usd.toFixed(5)}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function MessageBubble({ message, theme, onSendSuggestion }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const codeStyle = theme === 'dark' ? oneDark : oneLight

  const [thinkingOpen, setThinkingOpen] = useState(true)
  const [sqlOpen, setSqlOpen] = useState(false)
  const thinkingRef = useRef<HTMLDivElement>(null)

  const { sql, mainContent, followUpSuggestions } = useMemo(
    () => {
      const { sql, rest } = extractSql(message.content)
      const { suggestions, contentWithout } = extractSuggestions(rest)
      return { sql, mainContent: contentWithout, followUpSuggestions: suggestions }
    },
    [message.content]
  )

  // Auto-collapse thinking when streaming finishes
  useEffect(() => {
    if (!message.isStreaming && (message.thinking || (message.tools && message.tools.length > 0))) {
      setThinkingOpen(false)
    }
  }, [message.isStreaming, message.thinking, message.tools])

  // Auto-scroll thinking section to bottom as new content arrives
  useEffect(() => {
    if (thinkingRef.current && message.isStreaming) {
      thinkingRef.current.scrollTop = thinkingRef.current.scrollHeight
    }
  }, [message.thinking, message.isStreaming])

  const markdownComponents = {
    code({ className, children, ...props }: Record<string, unknown>) {
      const match = /language-(\w+)/.exec((className as string) ?? '')
      const isBlock = !!match
      return isBlock ? (
        <SyntaxHighlighter
          style={codeStyle}
          language={match[1]}
          PreTag="div"
          customStyle={{
            borderRadius: '8px',
            fontSize: '0.82rem',
            margin: '0.5rem 0',
          }}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={styles.inlineCode} {...props}>
          {children as React.ReactNode}
        </code>
      )
    },
    table({ children }: Record<string, unknown>) {
      return (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>{children as React.ReactNode}</table>
        </div>
      )
    },
    img({ src, alt }: Record<string, unknown>) {
      const imgSrc = src as string
      const imgAlt = (alt as string) || 'Chart'
      return (
        <div className={styles.chartContainer}>
          <img src={imgSrc} alt={imgAlt} className={styles.chartImage} />
          <button
            className={styles.chartDownloadBtn}
            onClick={async () => {
              try {
                const response = await fetch(imgSrc)
                const blob = await response.blob()
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = imgSrc.split('/').pop() || 'chart.png'
                document.body.appendChild(a)
                a.click()
                document.body.removeChild(a)
                URL.revokeObjectURL(url)
              } catch { /* silent */ }
            }}
            title="Download chart"
          >
            <Download size={14} />
          </button>
        </div>
      )
    },
  }

  if (isUser) {
    return (
      <div className={`${styles.row} ${styles.userRow}`}>
        <div className={`${styles.avatar} ${styles.userAvatar}`}>
          <CircleUser size={16} strokeWidth={1.8} />
        </div>
        <div className={`${styles.bubble} ${styles.userBubble}`}>
          <p className={styles.userText}>{message.content}</p>
          <span className={styles.timestamp}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    )
  }

  const hasThinking = !!(message.thinking || (message.tools && message.tools.length > 0))

  return (
    <div className={`${styles.row} ${styles.assistantRow}`}>
      <div className={`${styles.avatar} ${message.isStreaming ? styles.botAvatarStreaming : styles.botAvatar}`}>
        <Sparkles size={14} strokeWidth={2} />
      </div>
      <div className={`${styles.bubble} ${styles.assistantBubble} ${message.isError ? styles.errorBubble : ''}`}>
        {message.isError && (
          <div className={styles.errorHeader}>
            <AlertCircle size={14} />
            <span>Error</span>
          </div>
        )}

        {/* Thinking section — collapsible */}
        {hasThinking && (
          <div className={styles.section}>
            <button
              className={styles.sectionToggle}
              onClick={() => setThinkingOpen(!thinkingOpen)}
            >
              {thinkingOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <Brain size={14} />
              <span>Thinking</span>
              {message.isStreaming && <span className={styles.streamingDot} />}
            </button>
            {thinkingOpen && (
              <div className={styles.sectionContent}>
                {/* Tools used */}
                {message.tools && message.tools.length > 0 && (
                  <div className={styles.toolsList}>
                    {message.tools.map((tool, i) => (
                      <span key={i} className={styles.toolPill}>
                        <Wrench size={11} />
                        {tool}
                      </span>
                    ))}
                  </div>
                )}
                {/* Reasoning text */}
                {message.thinking && (
                  <div className={styles.thinkingText} ref={thinkingRef}>
                    {message.thinking}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Results section — always visible */}
        {mainContent && (
          <div className={styles.resultsSection}>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents as never}>
              {mainContent}
            </ReactMarkdown>
            {message.isStreaming && <span className={styles.cursor} />}
          </div>
        )}

        {/* Show cursor if streaming but no content yet */}
        {!mainContent && message.isStreaming && (
          <div className={styles.resultsSection}>
            <span className={styles.cursor} />
          </div>
        )}

        {/* SQL section — collapsible */}
        {sql && (
          <div className={styles.section}>
            <button
              className={styles.sectionToggle}
              onClick={() => setSqlOpen(!sqlOpen)}
            >
              {sqlOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              <Code2 size={14} />
              <span>SQL Query</span>
            </button>
            {sqlOpen && (
              <div className={styles.sectionContent}>
                <SyntaxHighlighter
                  style={codeStyle}
                  language="sql"
                  PreTag="div"
                  customStyle={{
                    borderRadius: '8px',
                    fontSize: '0.82rem',
                    margin: '0.25rem 0',
                  }}
                >
                  {sql}
                </SyntaxHighlighter>
              </div>
            )}
          </div>
        )}

        {/* Follow-up suggestions as clickable pills */}
        {!message.isStreaming && followUpSuggestions.length > 0 && onSendSuggestion && (
          <div className={styles.followUpSection}>
            <span className={styles.followUpHeader}>Suggested Follow-Up</span>
            <div className={styles.followUpPills}>
              {followUpSuggestions.map((q, i) => (
                <button
                  key={i}
                  className={styles.followUpPill}
                  onClick={() => onSendSuggestion(q)}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className={styles.footer}>
          <span className={styles.timestamp}>
            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
          <div className={styles.footerActions}>
            {!message.isStreaming && (
              <div className={styles.exportMenu}>
                <button
                  className={styles.exportBtn}
                  onClick={async () => {
                    const md = await exportToMarkdown([message])
                    downloadFile(md, `response_${message.id}.md`, 'text/markdown')
                  }}
                  title="Export as Markdown"
                >
                  <Download size={12} />
                  <span>MD</span>
                </button>
                <button
                  className={styles.exportBtn}
                  onClick={async () => {
                    const html = await exportToHtml([message])
                    downloadFile(html, `response_${message.id}.html`, 'text/html')
                  }}
                  title="Export as HTML"
                >
                  <Download size={12} />
                  <span>HTML</span>
                </button>
              </div>
            )}
            {message.metrics && !message.isStreaming && (
              <MetricsPopup metrics={message.metrics} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
