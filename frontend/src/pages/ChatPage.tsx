import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchSession } from '../api/imageChat'
import { useImageChatWebSocket } from '../hooks/useImageChatWebSocket'
import MessageBubble from '../components/image-chat/MessageBubble'
import ChatInput from '../components/image-chat/ChatInput'
import PurposeSelector from '../components/image-chat/PurposeSelector'
import StyleSelector from '../components/image-chat/StyleSelector'
import type { ChatMessage, ImagePurpose, StylePreset, WebSocketResponse } from '../types/imageChat'

export default function ChatPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [purpose, setPurpose] = useState<ImagePurpose>('sns_instagram_square')
  const [style, setStyle] = useState<StylePreset | undefined>()
  const [statusMessage, setStatusMessage] = useState<string>('')

  // 세션 데이터 조회
  const { data: session, isLoading } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => fetchSession(sessionId!),
    enabled: !!sessionId,
  })

  // 세션 데이터로 초기화
  useEffect(() => {
    if (session) {
      setMessages(session.messages)
      setPurpose(session.image_purpose as ImagePurpose)
      if (session.style_preset) {
        setStyle(session.style_preset as StylePreset)
      }
    }
  }, [session])

  // WebSocket 메시지 핸들러
  const handleMessage = useCallback((response: WebSocketResponse) => {
    if (response.type === 'status') {
      setStatusMessage(response.content || '')
      return
    }

    setStatusMessage('')

    // 새 메시지 추가
    const newMessage: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId!,
      role: 'assistant',
      content_type: response.image_url ? 'image' : 'text',
      text_content: response.content,
      image_url: response.image_url,
      tokens_used: 0,
      generation_time_ms: response.data?.generation_time_ms as number,
      created_at: response.timestamp,
    }

    setMessages((prev) => [...prev, newMessage])
  }, [sessionId])

  // WebSocket 연결
  const { isConnected, isLoading: wsLoading, sendChat, sendGenerate, sendRefine } =
    useImageChatWebSocket({
      sessionId: sessionId!,
      onMessage: handleMessage,
    })

  // 스크롤 자동 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, statusMessage])

  // 채팅 전송
  const handleSendChat = useCallback(
    (content: string) => {
      // 사용자 메시지 추가
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: sessionId!,
        role: 'user',
        content_type: 'text',
        text_content: content,
        tokens_used: 0,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])

      sendChat(content, purpose, style)
    },
    [sessionId, purpose, style, sendChat]
  )

  // 이미지 생성
  const handleGenerate = useCallback(
    (prompt: string) => {
      // 사용자 메시지 추가
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: sessionId!,
        role: 'user',
        content_type: 'text',
        text_content: `[이미지 생성] ${prompt}`,
        tokens_used: 0,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])

      sendGenerate(prompt, purpose, style)
    },
    [sessionId, purpose, style, sendGenerate]
  )

  // 이미지 개선
  const handleRefine = useCallback(
    (feedback: string) => {
      // 사용자 메시지 추가
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: sessionId!,
        role: 'user',
        content_type: 'text',
        text_content: `[이미지 개선] ${feedback}`,
        tokens_used: 0,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, userMessage])

      sendRefine(feedback, purpose)
    },
    [sessionId, purpose, sendRefine]
  )

  const hasGeneratedImage = messages.some((m) => m.image_url)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-400">로딩 중...</div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-120px)]">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <button
            onClick={() => navigate('/')}
            className="text-gray-400 hover:text-white transition-colors mr-4"
          >
            ← 뒤로
          </button>
          <span className="text-xl font-bold">
            {session?.title || '이미지 채팅'}
          </span>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-400">
          <span
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-yellow-500'
            }`}
          />
          <span>{isConnected ? '연결됨' : '연결 중'}</span>
        </div>
      </div>

      {/* 설정 패널 */}
      <div className="bg-gray-800 rounded-xl p-4 mb-4">
        <div className="mb-3">
          <label className="block text-sm text-gray-400 mb-2">이미지 용도</label>
          <PurposeSelector value={purpose} onChange={setPurpose} />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-2">스타일</label>
          <StyleSelector value={style} onChange={setStyle} />
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto bg-gray-800 rounded-xl">
        <div className="p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <p className="text-4xl mb-4">🎨</p>
              <p>이미지 생성을 시작해보세요!</p>
              <p className="text-sm mt-2">
                원하는 이미지를 설명하면 AI가 생성해드립니다.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}

          {/* 상태 메시지 */}
          {statusMessage && (
            <div className="flex justify-start">
              <div className="bg-gray-700 rounded-2xl px-4 py-3 text-gray-300 animate-pulse">
                {statusMessage}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 입력 영역 */}
      <div className="bg-gray-800 rounded-xl mt-4">
        <ChatInput
          onSendChat={handleSendChat}
          onGenerate={handleGenerate}
          onRefine={handleRefine}
          isLoading={wsLoading}
          isConnected={isConnected}
          hasGeneratedImage={hasGeneratedImage}
        />
      </div>
    </div>
  )
}
