import type { ImagePurpose } from '../../types/imageChat'

interface PurposeSelectorProps {
  value: ImagePurpose
  onChange: (purpose: ImagePurpose) => void
}

const PURPOSES: { id: ImagePurpose; name: string; icon: string }[] = [
  { id: 'sns_instagram_square', name: 'Instagram 정사각형', icon: '📷' },
  { id: 'sns_instagram_portrait', name: 'Instagram 세로형', icon: '📱' },
  { id: 'sns_facebook', name: 'Facebook', icon: '👍' },
  { id: 'banner_web', name: '웹 배너', icon: '🖥️' },
  { id: 'banner_mobile', name: '모바일 배너', icon: '📲' },
  { id: 'product_showcase', name: '제품 쇼케이스', icon: '🛍️' },
  { id: 'email_header', name: '이메일 헤더', icon: '📧' },
]

export default function PurposeSelector({ value, onChange }: PurposeSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {PURPOSES.map((purpose) => (
        <button
          key={purpose.id}
          onClick={() => onChange(purpose.id)}
          className={`px-3 py-2 rounded-lg text-sm transition-colors ${
            value === purpose.id
              ? 'bg-blue-600 text-white'
              : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
          }`}
        >
          <span className="mr-1">{purpose.icon}</span>
          {purpose.name}
        </button>
      ))}
    </div>
  )
}
