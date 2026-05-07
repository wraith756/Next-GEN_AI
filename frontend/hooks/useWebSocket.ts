import { useEffect, useRef, useCallback } from 'react'

export type WSMessage = {
  type: string
  text?: string
  session_id?: number
  success?: boolean
  data?: string   // base64 image data for image messages
  path?: string   // file path for screenshots
}

type Handler = (msg: WSMessage) => void

export function useWebSocket(onMessage: Handler) {
  const ws = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  const connect = useCallback(() => {
    ws.current = new WebSocket('ws://localhost:8000/ws')

    ws.current.onmessage = (e) => {
      try {
        const msg: WSMessage = JSON.parse(e.data)
        onMessageRef.current(msg)
      } catch {}
    }

    ws.current.onclose = () => {
      reconnectTimer.current = setTimeout(connect, 2000)
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      ws.current?.close()
    }
  }, [connect])

  const send = useCallback((msg: WSMessage) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(msg))
    }
  }, [])

  const sendBinary = useCallback((data: ArrayBuffer) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(data)
    }
  }, [])

  return { send, sendBinary }
}
