import { useState } from 'react'

interface ChatInputProps {
  onSendChat: (content: string) => void
  onGenerate: (prompt: string) => void
  onRefine: (feedback: string) => void
  isLoading: boolean
  isConnected: boolean
  hasGeneratedImage: boolean
}

export default function ChatInput({
  onSendChat,
  onGenerate,
  onRefine,
  isLoading,
  isConnected,
  hasGeneratedImage,
}: ChatInputProps) {
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<'chat' | 'generate' | 'refine'>('generate')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading || !isConnected) return

    switch (mode) {
      case 'chat':
        onSendChat(input.trim())
        break
      case 'generate':
        onGenerate(input.trim())
        break
      case 'refine':
        onRefine(input.trim())
        break
    }

    setInput('')
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-gray-700 p-4">
      {/* 모드 선택 */}
      <div className="flex space-x-2 mb-3">
        <button
          type="button"
          onClick={() => setMode('generate')}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            mode === 'generate'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          🎨 이미지 생성
        </button>
        <button
          type="button"
          onClick={() => setMode('refine')}
          disabled={!hasGeneratedImage}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            mode === 'refine'
              ? 'bg-purple-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          } ${!hasGeneratedImage ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          ✨ 이미지 개선
        </button>
        <button
          type="button"
          onClick={() => setMode('chat')}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            mode === 'chat'
              ? 'bg-green-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          💬 대화
        </button>
      </div>

      {/* 입력 필드 */}
      <div className="flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            mode === 'generate'
              ? '생성할 이미지를 설명하세요...'
              : mode === 'refine'
              ? '개선 사항을 입력하세요...'
              : '메시지를 입력하세요...'
          }
          disabled={isLoading || !isConnected}
          className="flex-1 px-4 py-3 bg-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading || !isConnected}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="flex items-center">
              <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
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
              생성 중...
            </span>
          ) : (
            '전송'
          )}
        </button>
      </div>

      {/* 연결 상태 */}
      {!isConnected && (
        <p className="text-sm text-yellow-500 mt-2">연결 중...</p>
      )}
    </form>
  )
}
