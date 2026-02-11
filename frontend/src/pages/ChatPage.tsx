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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

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

    // 에러 처리
    if (response.type === 'error') {
      // 에러도 메시지로 표시
      const errorMessage: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: sessionId!,
        role: 'assistant',
        content_type: 'text',
        text_content: `⚠️ ${response.content}`,
        tokens_used: 0,
        created_at: response.timestamp,
      }
      setMessages((prev) => [...prev, errorMessage])
      return
    }

    // 새 메시지 추가 (텍스트, 이미지, 또는 혼합)
    const newMessage: ChatMessage = {
      id: crypto.randomUUID(),
      session_id: sessionId!,
      role: 'assistant',
      content_type: response.image_url ? (response.content ? 'mixed' : 'image') : 'text',
      text_content: response.content,
      image_url: response.image_url,
      tokens_used: 0,
      generation_time_ms: response.data?.generation_time_ms as number,
      created_at: response.timestamp,
    }

    setMessages((prev) => [...prev, newMessage])
  }, [sessionId])

  // WebSocket 연결
  const { isConnected, isLoading: wsLoading, sendConverse } =
    useImageChatWebSocket({
      sessionId: sessionId!,
      onMessage: handleMessage,
    })

  // 스크롤 자동 이동
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, statusMessage])

  // 통합 대화 전송
  const handleSend = useCallback(
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

      // 통합 대화 API 호출
      sendConverse(content, purpose, style)
    },
    [sessionId, purpose, style, sendConverse]
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-400">로딩 중...</div>
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-80px)]">
      {/* 왼쪽 사이드바 - 설정 패널 */}
      <div
        className={`flex-shrink-0 bg-gray-800 rounded-xl mr-4 transition-all duration-300 ${
          sidebarCollapsed ? 'w-12' : 'w-64'
        }`}
      >
        {/* 사이드바 헤더 */}
        <div className="flex items-center justify-between p-3 border-b border-gray-700">
          {!sidebarCollapsed && (
            <span className="text-sm font-medium text-gray-300">설정</span>
          )}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="p-1 hover:bg-gray-700 rounded transition-colors text-gray-400 hover:text-white"
            title={sidebarCollapsed ? '펼치기' : '접기'}
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>

        {/* 사이드바 내용 */}
        {!sidebarCollapsed && (
          <div className="p-4 space-y-6">
            {/* 이미지 용도 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                📐 이미지 용도
              </label>
              <PurposeSelector value={purpose} onChange={setPurpose} />
            </div>

            {/* 스타일 */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                🎨 스타일
              </label>
              <StyleSelector value={style} onChange={setStyle} />
            </div>

            {/* 현재 설정 요약 */}
            <div className="pt-4 border-t border-gray-700">
              <p className="text-xs text-gray-500 mb-2">현재 설정</p>
              <div className="space-y-1 text-sm">
                <p className="text-gray-400">
                  용도: <span className="text-blue-400">{purpose}</span>
                </p>
                <p className="text-gray-400">
                  스타일: <span className="text-purple-400">{style || '없음'}</span>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 접힌 상태 아이콘 */}
        {sidebarCollapsed && (
          <div className="flex flex-col items-center py-4 space-y-4">
            <span title="이미지 용도" className="text-lg">📐</span>
            <span title="스타일" className="text-lg">🎨</span>
          </div>
        )}
      </div>

      {/* 오른쪽 메인 영역 - 채팅 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-3 px-1">
          <div className="flex items-center">
            <button
              onClick={() => navigate('/')}
              className="text-gray-400 hover:text-white transition-colors mr-4 text-sm"
            >
              ← 뒤로
            </button>
            <span className="text-lg font-bold truncate">
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

        {/* 메시지 영역 */}
        <div className="flex-1 overflow-y-auto bg-gray-800 rounded-xl">
          <div className="p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center py-16 text-gray-400">
                <p className="text-5xl mb-4">🎨</p>
                <p className="text-lg font-medium mb-2">TRDST 이미지 생성</p>
                <p className="text-sm mb-4">
                  자연스럽게 대화하며 마케팅 이미지를 만들어보세요.
                </p>
                <div className="text-xs text-gray-500 space-y-1">
                  <p>💡 "인스타그램용 조명 이미지를 만들고 싶어"</p>
                  <p>💡 "고급스러운 소파 사진이 필요해"</p>
                  <p>💡 "페이스북 배너에 쓸 거실 이미지 만들어줘"</p>
                </div>
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
        <div className="bg-gray-800 rounded-xl mt-3">
          <ChatInput
            onSend={handleSend}
            isLoading={wsLoading}
            isConnected={isConnected}
          />
        </div>
      </div>
    </div>
  )
}
