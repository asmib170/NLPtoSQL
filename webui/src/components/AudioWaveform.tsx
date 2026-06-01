import { useEffect, useRef } from 'react'

interface AudioWaveformProps {
  isActive: boolean
  color?: string
}

export function AudioWaveform({ isActive, color = '#6366f1' }: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    if (!isActive || !canvasRef.current) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      return
    }

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const bars = 5
    const barWidth = 3
    const gap = 4
    const maxHeight = 24
    const minHeight = 4

    canvas.width = bars * (barWidth + gap) - gap
    canvas.height = maxHeight

    let phase = 0

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (let i = 0; i < bars; i++) {
        const amplitude = Math.sin(phase + i * 0.5) * 0.5 + 0.5
        const height = minHeight + (maxHeight - minHeight) * amplitude

        const x = i * (barWidth + gap)
        const y = (maxHeight - height) / 2

        ctx.fillStyle = color
        ctx.beginPath()
        ctx.roundRect(x, y, barWidth, height, barWidth / 2)
        ctx.fill()
      }

      phase += 0.1
      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isActive, color])

  if (!isActive) return null

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '24px' }}>
      <canvas ref={canvasRef} style={{ display: 'block' }} />
    </div>
  )
}
