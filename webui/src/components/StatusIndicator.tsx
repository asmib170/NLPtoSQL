import { useEffect, useState } from 'react'
import { checkHealth } from '../api/agentService'
import styles from './StatusIndicator.module.css'

export function StatusIndicator() {
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    const check = async () => setOnline(await checkHealth())
    check()
    const interval = setInterval(check, 15000)
    return () => clearInterval(interval)
  }, [])

  if (online === null) return null

  return (
    <div className={`${styles.indicator} ${online ? styles.online : styles.offline}`}>
      <span className={styles.dot} />
      <span className={styles.label}>
        {online ? 'Agent online' : 'Agent offline — start server.py'}
      </span>
    </div>
  )
}
