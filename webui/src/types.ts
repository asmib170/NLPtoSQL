export type Role = 'user' | 'assistant'

export interface MessageMetrics {
  model?: string
  ttft_ms?: number | null
  latency_ms?: number
  input_tokens?: number
  output_tokens?: number
  total_tokens?: number
  cache_read_tokens?: number
  cache_write_tokens?: number
  estimated_cost_usd?: number
}

export interface Message {
  id: string
  role: Role
  content: string
  thinking?: string
  tools?: string[]
  metrics?: MessageMetrics
  timestamp: Date
  isStreaming?: boolean
  isError?: boolean
}

export type Theme = 'light' | 'dark'
