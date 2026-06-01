/**
 * Export utilities — convert messages to HTML and Markdown for download.
 */

import type { Message } from '../types'

function formatTimestamp(date: Date): string {
  return date.toLocaleString()
}

/**
 * Export a single message or array of messages as Markdown.
 * Embeds chart images as base64 data URLs.
 */
export async function exportToMarkdown(messages: Message[], title?: string): Promise<string> {
  const lines: string[] = []
  if (title) lines.push(`# ${title}\n`)
  lines.push(`_Exported: ${new Date().toLocaleString()}_\n`)
  lines.push('---\n')

  for (const msg of messages) {
    const role = msg.role === 'user' ? '👤 **You**' : '🤖 **Assistant**'
    lines.push(`## ${role} — ${formatTimestamp(msg.timestamp)}\n`)

    let content = msg.content

    // Embed chart images as base64
    const imgMatches = content.matchAll(/!\[([^\]]*)\]\((\/api\/charts\/[^)]+)\)/g)
    for (const match of imgMatches) {
      const imgUrl = match[2]
      try {
        const response = await fetch(imgUrl)
        if (response.ok) {
          const blob = await response.blob()
          const base64 = await blobToBase64(blob)
          content = content.replace(match[0], `![${match[1]}](${base64})`)
        }
      } catch {
        // Leave original reference
      }
    }

    lines.push(content)
    lines.push('\n---\n')
  }

  return lines.join('\n')
}

/**
 * Export a single message or array of messages as HTML.
 * Converts markdown content to HTML and embeds chart images as base64.
 */
export async function exportToHtml(messages: Message[], title?: string): Promise<string> {
  const heading = title ?? 'Chat Export'
  const rows: string[] = []

  for (const msg of messages) {
    const role = msg.role === 'user' ? '👤 You' : '🤖 Assistant'
    const bgColor = msg.role === 'user' ? '#eef2ff' : '#f8f9fb'
    let htmlContent = markdownToHtml(msg.content)

    // Embed chart images as base64
    const imgMatches = htmlContent.matchAll(/<img src="(\/api\/charts\/[^"]+)"/g)
    for (const match of imgMatches) {
      const imgUrl = match[1]
      try {
        const response = await fetch(imgUrl)
        if (response.ok) {
          const blob = await response.blob()
          const base64 = await blobToBase64(blob)
          htmlContent = htmlContent.replace(match[0], `<img src="${base64}"`)
        }
      } catch {
        // Leave the broken image reference
      }
    }

    rows.push(`
      <div style="margin-bottom:1rem;padding:1rem;border-radius:12px;background:${bgColor};border:1px solid #e2e5eb;">
        <div style="font-size:0.8rem;color:#6b7280;margin-bottom:0.5rem;">
          <strong>${role}</strong> — ${formatTimestamp(msg.timestamp)}
        </div>
        <div style="font-size:0.9rem;line-height:1.6;">${htmlContent}</div>
      </div>`)
  }

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${heading}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; background: #fff; color: #1f2937; }
    h1 { font-size: 1.5rem; border-bottom: 2px solid #6366f1; padding-bottom: 0.5rem; }
    .meta { font-size: 0.8rem; color: #9ca3af; margin-bottom: 1.5rem; }
    table { border-collapse: collapse; width: 100%; margin: 0.5rem 0; }
    th, td { border: 1px solid #e2e5eb; padding: 0.4rem 0.7rem; text-align: left; font-size: 0.85rem; }
    th { background: #f1f3f7; font-weight: 600; }
    pre { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 8px; overflow-x: auto; font-size: 0.82rem; }
    code { font-family: 'JetBrains Mono', monospace; background: #f1f3f7; padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.85em; }
    pre code { background: none; padding: 0; }
    blockquote { border-left: 3px solid #6366f1; padding-left: 0.75rem; margin: 0.5rem 0; color: #6b7280; }
    img { max-width: 100%; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>${heading}</h1>
  <p class="meta">Exported: ${new Date().toLocaleString()}</p>
  ${rows.join('\n')}
</body>
</html>`
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

/**
 * Simple markdown to HTML converter.
 */
function markdownToHtml(md: string): string {
  let html = escapeHtml(md)

  // Code blocks (``` ... ```)
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, lang, code) => {
    return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`
  })

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // Headers
  html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>')
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')

  // Images
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" />')

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')

  // Tables
  html = html.replace(/^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)+)/gm, (_m, headerRow, _sep, bodyRows) => {
    const headers = headerRow.split('|').filter((c: string) => c.trim()).map((c: string) => `<th>${c.trim()}</th>`).join('')
    const rows = bodyRows.trim().split('\n').map((row: string) => {
      const cells = row.split('|').filter((c: string) => c.trim()).map((c: string) => `<td>${c.trim()}</td>`).join('')
      return `<tr>${cells}</tr>`
    }).join('')
    return `<table><thead><tr>${headers}</tr></thead><tbody>${rows}</tbody></table>`
  })

  // Unordered lists
  html = html.replace(/^[•\-\*] (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`)

  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')

  // Blockquotes
  html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>')

  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr />')

  // Paragraphs (double newline)
  html = html.replace(/\n\n/g, '</p><p>')
  html = `<p>${html}</p>`
  html = html.replace(/<p><\/p>/g, '')
  html = html.replace(/<p>(<h[1-4]>)/g, '$1')
  html = html.replace(/(<\/h[1-4]>)<\/p>/g, '$1')
  html = html.replace(/<p>(<pre>)/g, '$1')
  html = html.replace(/(<\/pre>)<\/p>/g, '$1')
  html = html.replace(/<p>(<table>)/g, '$1')
  html = html.replace(/(<\/table>)<\/p>/g, '$1')
  html = html.replace(/<p>(<ul>)/g, '$1')
  html = html.replace(/(<\/ul>)<\/p>/g, '$1')
  html = html.replace(/<p>(<hr \/>)/g, '$1')

  // Single newlines to <br>
  html = html.replace(/\n/g, '<br />')

  return html
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * Trigger a file download in the browser.
 */
export function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
