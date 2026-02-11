import { useState } from 'react'
import clsx from 'clsx'
import type { ChatMessage } from '../../types/imageChat'

interface MessageBubbleProps {
  message: ChatMessage
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const [showFullscreen, setShowFullscreen] = useState(false)

  const handleDownload = () => {
    if (!message.image_url) return

    // Base64 data URL을 다운로드
    const link = document.createElement('a')
    link.href = message.image_url
    link.download = `trdst-image-${Date.now()}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <>
      <div
        className={clsx('flex', {
          'justify-end': isUser,
          'justify-start': !isUser,
        })}
      >
        <div
          className={clsx('max-w-[80%] rounded-2xl px-4 py-3', {
            'bg-blue-600 text-white': isUser,
            'bg-gray-700 text-gray-100': !isUser,
          })}
        >
          {/* 텍스트 콘텐츠 */}
          {message.text_content && (
            <p className="whitespace-pre-wrap">{message.text_content}</p>
          )}

          {/* 이미지 콘텐츠 */}
          {message.image_url && (
            <div className="mt-2">
              <img
                src={message.image_url}
                alt="Generated"
                className="rounded-lg max-w-full cursor-pointer hover:opacity-90 transition-opacity"
                onClick={() => setShowFullscreen(true)}
              />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => setShowFullscreen(true)}
                  className="text-xs px-2 py-1 bg-gray-600 hover:bg-gray-500 rounded transition-colors"
                >
                  🔍 크게 보기
                </button>
                <button
                  onClick={handleDownload}
                  className="text-xs px-2 py-1 bg-blue-500 hover:bg-blue-400 rounded transition-colors"
                >
                  ⬇ 다운로드
                </button>
              </div>
            </div>
          )}

          {/* 메타데이터 */}
          {message.generation_time_ms && (
            <p className="text-xs opacity-60 mt-2">
              생성 시간: {(message.generation_time_ms / 1000).toFixed(1)}초
            </p>
          )}
        </div>
      </div>

      {/* 풀스크린 모달 */}
      {showFullscreen && message.image_url && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setShowFullscreen(false)}
        >
          <div className="relative max-w-full max-h-full">
            <img
              src={message.image_url}
              alt="Generated Full"
              className="max-w-full max-h-[90vh] object-contain rounded-lg"
              onClick={(e) => e.stopPropagation()}
            />
            <div className="absolute top-4 right-4 flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleDownload()
                }}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-400 text-white rounded-lg transition-colors"
              >
                ⬇ 다운로드
              </button>
              <button
                onClick={() => setShowFullscreen(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                ✕ 닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
