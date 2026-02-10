import type { StylePreset } from '../../types/imageChat'

interface StyleSelectorProps {
  value?: StylePreset
  onChange: (style: StylePreset | undefined) => void
}

const STYLES: { id: StylePreset; name: string }[] = [
  { id: 'modern', name: '모던' },
  { id: 'minimal', name: '미니멀' },
  { id: 'vibrant', name: '비비드' },
  { id: 'luxury', name: '럭셔리' },
  { id: 'playful', name: '플레이풀' },
  { id: 'professional', name: '프로페셔널' },
  { id: 'natural', name: '내추럴' },
  { id: 'tech', name: '테크' },
]

export default function StyleSelector({ value, onChange }: StyleSelectorProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={() => onChange(undefined)}
        className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
          !value
            ? 'bg-gray-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        }`}
      >
        기본
      </button>
      {STYLES.map((style) => (
        <button
          key={style.id}
          onClick={() => onChange(style.id)}
          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
            value === style.id
              ? 'bg-purple-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
        >
          {style.name}
        </button>
      ))}
    </div>
  )
}
