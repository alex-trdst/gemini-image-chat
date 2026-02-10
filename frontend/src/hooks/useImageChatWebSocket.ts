import { useCallback, useEffect, useRef, useState } from 'react'
import type { ImagePurpose, StylePreset, WebSocketResponse } from '../types/imageChat'

interface UseImageChatWebSocketOptions {
  sessionId: string
  onMessage?: (response: WebSocketResponse) => void
  onError?: (error: Event) => void
  onOpen?: () => void
  onClose?: () => void
}

export function useImageChatWebSocket({
  sessionId,
  onMessage,
  onError,
  onOpen,
  onClose,
}: UseImageChatWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)

  // WebSocket 연결
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const ws = new WebSocket(`${protocol}//${host}/ws/image-chat/${sessionId}`)

    ws.onopen = () => {
      setIsConnected(true)
      onOpen?.()
    }

    ws.onclose = () => {
      setIsConnected(false)
      setIsLoading(false)
      onClose?.()

      // 3초 후 재연결 시도
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connect()
      }, 3000)
    }

    ws.onerror = (event) => {
      onError?.(event)
    }

    ws.onmessage = (event) => {
      try {
        const response: WebSocketResponse = JSON.parse(event.data)

        // 상태 업데이트
        if (response.type === 'status') {
          if (response.content?.includes('생성 중') || response.content?.includes('개선 중')) {
            setIsLoading(true)
          }
        } else {
          setIsLoading(false)
        }

        onMessage?.(response)
      } catch (error) {
        console.error('WebSocket message parse error:', error)
      }
    }

    wsRef.current = ws
  }, [sessionId, onMessage, onError, onOpen, onClose])

  // 연결 해제
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    wsRef.current?.close()
    wsRef.current = null
    setIsConnected(false)
  }, [])

  // 채팅 메시지 전송
  const sendChat = useCallback(
    (content: string, purpose: ImagePurpose, style?: StylePreset) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

      wsRef.current.send(
        JSON.stringify({
          type: 'chat',
          content,
          data: { purpose, style },
        })
      )
    },
    []
  )

  // 이미지 생성 요청
  const sendGenerate = useCallback(
    (prompt: string, purpose: ImagePurpose, style?: StylePreset) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

      setIsLoading(true)
      wsRef.current.send(
        JSON.stringify({
          type: 'generate',
          content: prompt,
          data: { purpose, style },
        })
      )
    },
    []
  )

  // 이미지 개선 요청
  const sendRefine = useCallback(
    (feedback: string, purpose: ImagePurpose) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

      setIsLoading(true)
      wsRef.current.send(
        JSON.stringify({
          type: 'refine',
          content: feedback,
          data: { purpose },
        })
      )
    },
    []
  )

  // 컴포넌트 마운트 시 연결
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    isConnected,
    isLoading,
    sendChat,
    sendGenerate,
    sendRefine,
    connect,
    disconnect,
  }
}
