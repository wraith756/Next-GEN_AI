import { useRef, useCallback, useState } from 'react'

export function useVoice(onAudio: (data: ArrayBuffer) => void) {
  const recorder = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])
  const [listening, setListening] = useState(false)
  const onAudioRef = useRef(onAudio)
  onAudioRef.current = onAudio

  const startListening = useCallback(async () => {
    if (listening) return
    setListening(true)
    chunks.current = []

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    recorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' })

    recorder.current.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.current.push(e.data)
    }

    recorder.current.onstop = async () => {
      const blob = new Blob(chunks.current, { type: 'audio/webm' })
      const buffer = await blob.arrayBuffer()
      onAudioRef.current(buffer)
      stream.getTracks().forEach((t) => t.stop())
      setListening(false)
    }

    recorder.current.start()
    setTimeout(() => {
      if (recorder.current?.state === 'recording') {
        recorder.current.stop()
      }
    }, 8000)
  }, [listening])

  const stopListening = useCallback(() => {
    if (recorder.current?.state === 'recording') {
      recorder.current.stop()
    }
  }, [])

  return { listening, startListening, stopListening }
}
