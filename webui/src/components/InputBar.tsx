import { useState, useRef, useCallback, useEffect, type KeyboardEvent } from 'react'
import { Send, Square, Loader2, Mic, MicOff } from 'lucide-react'
import { AudioWaveform } from './AudioWaveform'
import { useSpeechToText } from '../hooks/useSpeechToText'
import styles from './InputBar.module.css'

interface InputBarProps {
  onSend: (message: string) => void
  onStop: () => void
  isLoading: boolean
}

export function InputBar({ onSend, onStop, isLoading }: InputBarProps) {
  const [value, setValue] = useState('')
  const [pendingVoiceSubmit, setPendingVoiceSubmit] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const {
    isListening,
    isLoading: isSpeechLoading,
    isModelLoading,
    modelProgress,
    transcript,
    error: speechError,
    recordingDuration,
    startListening,
    stopListening,
    resetTranscript,
    isSupported: isSpeechSupported,
  } = useSpeechToText({
    model: 'Xenova/whisper-tiny.en',
    silenceThreshold: 0.01,
    silenceTimeout: 2000,
    onSilenceDetected: () => {
      stopListening()
      setPendingVoiceSubmit(true)
    },
  })

  // Auto-submit voice transcript
  useEffect(() => {
    if (transcript && pendingVoiceSubmit && !isLoading) {
      setPendingVoiceSubmit(false)
      const text = transcript.trim()
      resetTranscript()
      // Don't send blank/empty transcriptions
      if (text && !text.startsWith('[') && text.length > 1) {
        onSend(text)
      }
    }
  }, [transcript, pendingVoiceSubmit, isLoading, resetTranscript, onSend])

  // Show transcript in textarea while recording (skip blank audio markers)
  useEffect(() => {
    if (transcript && isListening && !transcript.startsWith('[')) {
      setValue(transcript)
    }
  }, [transcript, isListening])

  const handleSend = useCallback(() => {
    const trimmed = value.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setValue('')
    resetTranscript()
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }, [value, isLoading, onSend, resetTranscript])

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  const handleMicClick = async () => {
    if (isListening) {
      stopListening()
      setPendingVoiceSubmit(true)
    } else {
      resetTranscript()
      setValue('')
      setPendingVoiceSubmit(false)
      await startListening()
    }
  }

  const formatDuration = (s: number) =>
    `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`

  return (
    <div className={styles.container}>
      {/* Model loading indicator */}
      {isModelLoading && (
        <div className={styles.modelLoading}>
          <Loader2 size={12} className={styles.spinner} />
          <span>Loading speech model… {modelProgress}%</span>
          <div className={styles.progressBar}>
            <div className={styles.progressFill} style={{ width: `${modelProgress}%` }} />
          </div>
        </div>
      )}

      <div className={styles.inner}>
        {/* Waveform when recording */}
        {isListening && (
          <div className={styles.waveformArea}>
            <AudioWaveform isActive={isListening} />
            <span className={styles.duration}>{formatDuration(recordingDuration)}</span>
          </div>
        )}

        <textarea
          ref={textareaRef}
          className={styles.textarea}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={isListening ? 'Listening…' : 'Ask a question about your data… (Enter to send, Shift+Enter for new line)'}
          rows={2}
          disabled={isListening}
          aria-label="Message input"
        />

        <div className={styles.buttonRow}>
          {/* Mic button */}
          {isSpeechSupported && (
            <button
              className={`${styles.micBtn} ${isListening ? styles.micActive : ''}`}
              onClick={handleMicClick}
              disabled={isModelLoading || isSpeechLoading}
              title={isListening ? 'Stop recording' : 'Voice input'}
              aria-label={isListening ? 'Stop recording' : 'Start voice input'}
            >
              {isListening ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
          )}

          {/* Send/Stop button */}
          <button
            className={`${styles.sendBtn} ${isLoading ? styles.stopBtn : ''}`}
            onClick={isLoading ? onStop : handleSend}
            disabled={!isLoading && !value.trim()}
            aria-label={isLoading ? 'Stop streaming' : 'Send message'}
            title={isLoading ? 'Stop' : 'Send'}
          >
            {isLoading ? (
              <Square size={16} fill="currentColor" />
            ) : (
              <Send size={16} />
            )}
          </button>
        </div>
      </div>

      {/* Speech error */}
      {speechError && (
        <div className={styles.speechError}>{speechError}</div>
      )}

      {isLoading && (
        <div className={styles.status}>
          <div className={styles.typingDots}>
            <span /><span /><span />
          </div>
          <span>Agent is thinking…</span>
        </div>
      )}

      <p className={styles.hint}>
        Powered by Strands Agents + Amazon Bedrock
      </p>
    </div>
  )
}
