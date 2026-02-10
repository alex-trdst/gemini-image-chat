import clsx from 'clsx'
import type { ChatMessage } from '../../types/imageChat'

interface MessageBubbleProps {
  message: ChatMessage
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'

  return (
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
              onClick={() => window.open(message.image_url, '_blank')}
            />
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
  )
}
