import { useState, useRef, useEffect } from 'react'

interface ChatInputProps {
  onSend: (content: string) => void
  isLoading: boolean
  isConnected: boolean
}

export default function ChatInput({
  onSend,
  isLoading,
  isConnected,
}: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // 자동 높이 조절
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [input])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading || !isConnected) return

    onSend(input.trim())
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // 빠른 제안 문구
  const suggestions = [
    '이미지를 만들어줘',
    '배경을 더 따뜻하게',
    '조명을 자연스럽게',
    '제품을 더 크게',
  ]

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-700 p-4">
      {/* 빠른 제안 - 입력이 비어있을 때만 표시 */}
      {!input.trim() && !isLoading && (
        <div className="flex flex-wrap gap-2 mb-3">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => setInput(suggestion)}
              className="text-xs px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-full transition-colors"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* 입력 필드 */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="자연스럽게 대화하세요. AI가 필요할 때 이미지를 생성합니다..."
            disabled={isLoading || !isConnected}
            rows={1}
            className="w-full px-4 py-3 bg-gray-700 rounded-xl text-white placeholder-gray-400
                       focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50
                       resize-none overflow-hidden"
          />
        </div>
        <button
          type="submit"
          disabled={!input.trim() || isLoading || !isConnected}
          className="px-5 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-medium
                     transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center justify-center min-w-[80px]"
        >
          {isLoading ? (
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ) : (
            <span>전송</span>
          )}
        </button>
      </div>

      {/* 도움말 */}
      <p className="text-xs text-gray-500 mt-2">
        Shift+Enter로 줄바꿈 • "이미지 만들어줘", "수정해줘" 등으로 자연스럽게 요청하세요
      </p>

      {/* 연결 상태 */}
      {!isConnected && (
        <p className="text-sm text-yellow-500 mt-2">연결 중...</p>
      )}
    </form>
  )
}
