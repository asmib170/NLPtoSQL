import { useState, useMemo } from 'react'
import { Download, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-react'
import styles from './SortableTable.module.css'

interface SortableTableProps {
  children: React.ReactNode
}

type SortDirection = 'asc' | 'desc' | null

/** Recursively extract text from React children */
function extractText(node: unknown): string {
  if (node == null) return ''
  if (typeof node === 'string' || typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(extractText).join('')
  if (typeof node === 'object' && 'props' in (node as object)) {
    const obj = node as { props?: { children?: unknown } }
    return extractText(obj.props?.children)
  }
  return String(node)
}

export function SortableTable({ children }: SortableTableProps) {
  const [sortCol, setSortCol] = useState<number | null>(null)
  const [sortDir, setSortDir] = useState<SortDirection>(null)

  // Parse table structure from children
  const { headers, rows } = useMemo(() => {
    const headers: string[] = []
    const rows: string[][] = []

    // Extract from React children tree
    const childArray = Array.isArray(children) ? children : [children]
    for (const child of childArray) {
      if (!child || typeof child !== 'object') continue
      const c = child as { type?: string; props?: { children?: unknown } }
      if (c.type === 'thead' && c.props?.children) {
        // Extract headers
        const headRow = c.props.children as { props?: { children?: unknown[] } }
        if (headRow?.props?.children) {
          const ths = Array.isArray(headRow.props.children) ? headRow.props.children : [headRow.props.children]
          for (const th of ths) {
            headers.push(extractText(th))
          }
        }
      }
      if (c.type === 'tbody' && c.props?.children) {
        // Extract rows
        const trs = Array.isArray(c.props.children) ? c.props.children : [c.props.children]
        for (const tr of trs) {
          const trObj = tr as { props?: { children?: unknown[] } }
          if (trObj?.props?.children) {
            const tds = Array.isArray(trObj.props.children) ? trObj.props.children : [trObj.props.children]
            const row: string[] = []
            for (const td of tds) {
              row.push(extractText(td))
            }
            rows.push(row)
          }
        }
      }
    }
    return { headers, rows }
  }, [children])

  // Sort rows
  const sortedRows = useMemo(() => {
    if (sortCol === null || sortDir === null) return rows
    return [...rows].sort((a, b) => {
      const aVal = a[sortCol] ?? ''
      const bVal = b[sortCol] ?? ''
      // Try numeric comparison
      const aNum = parseFloat(aVal.replace(/[$,%]/g, ''))
      const bNum = parseFloat(bVal.replace(/[$,%]/g, ''))
      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDir === 'asc' ? aNum - bNum : bNum - aNum
      }
      // String comparison
      return sortDir === 'asc'
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal)
    })
  }, [rows, sortCol, sortDir])

  const handleSort = (colIndex: number) => {
    if (sortCol === colIndex) {
      if (sortDir === 'asc') setSortDir('desc')
      else if (sortDir === 'desc') { setSortCol(null); setSortDir(null) }
      else setSortDir('asc')
    } else {
      setSortCol(colIndex)
      setSortDir('asc')
    }
  }

  const handleDownloadCsv = () => {
    const csvLines = [
      headers.join(','),
      ...sortedRows.map(row => row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(','))
    ]
    const csv = csvLines.join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'table_data.csv'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // If we couldn't parse the table, just render normally
  if (headers.length === 0) {
    return (
      <div className={styles.wrapper}>
        <table className={styles.table}>{children}</table>
      </div>
    )
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.toolbar}>
        <button className={styles.csvBtn} onClick={handleDownloadCsv} title="Download as CSV">
          <Download size={12} />
          <span>CSV</span>
        </button>
      </div>
      <table className={styles.table}>
        <thead>
          <tr>
            {headers.map((header, i) => (
              <th key={i} onClick={() => handleSort(i)} className={styles.sortableHeader}>
                <span>{header}</span>
                <span className={styles.sortIcon}>
                  {sortCol === i ? (
                    sortDir === 'asc' ? <ArrowUp size={12} /> : <ArrowDown size={12} />
                  ) : (
                    <ArrowUpDown size={11} />
                  )}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
