import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { createSession, fetchSessions, deleteSession, fetchPurposes } from '../api/imageChat'
import type { ImagePurpose, StylePreset } from '../types/imageChat'
import PurposeSelector from '../components/image-chat/PurposeSelector'
import StyleSelector from '../components/image-chat/StyleSelector'

export default function SessionsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [selectedPurpose, setSelectedPurpose] = useState<ImagePurpose>('sns_instagram_square')
  const [selectedStyle, setSelectedStyle] = useState<StylePreset | undefined>()

  // 세션 목록 조회
  const { data, isLoading } = useQuery({
    queryKey: ['sessions'],
    queryFn: () => fetchSessions(),
  })

  // 세션 생성
  const createMutation = useMutation({
    mutationFn: createSession,
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
      navigate(`/chat/${session.id}`)
    },
  })

  // 세션 삭제
  const deleteMutation = useMutation({
    mutationFn: deleteSession,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    },
  })

  const handleCreate = () => {
    createMutation.mutate({
      title: newTitle || undefined,
      image_purpose: selectedPurpose,
      style_preset: selectedStyle,
    })
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">세션 목록</h1>
        <button
          onClick={() => setIsCreating(true)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
        >
          + 새 세션
        </button>
      </div>

      {/* 새 세션 생성 모달 */}
      {isCreating && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-xl p-6 w-full max-w-lg mx-4">
            <h2 className="text-xl font-bold mb-4">새 이미지 채팅 세션</h2>

            {/* 제목 */}
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">세션 제목 (선택)</label>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="예: SNS 캠페인 이미지"
                className="w-full px-4 py-2 bg-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* 용도 선택 */}
            <div className="mb-4">
              <label className="block text-sm text-gray-400 mb-2">이미지 용도</label>
              <PurposeSelector value={selectedPurpose} onChange={setSelectedPurpose} />
            </div>

            {/* 스타일 선택 */}
            <div className="mb-6">
              <label className="block text-sm text-gray-400 mb-2">스타일 프리셋</label>
              <StyleSelector value={selectedStyle} onChange={setSelectedStyle} />
            </div>

            {/* 버튼 */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setIsCreating(false)}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                취소
              </button>
              <button
                onClick={handleCreate}
                disabled={createMutation.isPending}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {createMutation.isPending ? '생성 중...' : '세션 시작'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 세션 목록 */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">로딩 중...</div>
      ) : data?.sessions.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <p className="text-6xl mb-4">🎨</p>
          <p>아직 세션이 없습니다.</p>
          <p className="text-sm mt-2">새 세션을 만들어 이미지를 생성해보세요!</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data?.sessions.map((session) => (
            <div
              key={session.id}
              className="bg-gray-800 rounded-xl p-4 hover:bg-gray-750 transition-colors cursor-pointer"
              onClick={() => navigate(`/chat/${session.id}`)}
            >
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-medium truncate">
                  {session.title || '제목 없음'}
                </h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    if (confirm('이 세션을 삭제하시겠습니까?')) {
                      deleteMutation.mutate(session.id)
                    }
                  }}
                  className="text-gray-500 hover:text-red-500 transition-colors"
                >
                  ✕
                </button>
              </div>

              {/* 미리보기 이미지 */}
              {session.final_image_url && (
                <div className="mb-3 aspect-square rounded-lg overflow-hidden bg-gray-700">
                  <img
                    src={session.final_image_url}
                    alt="Preview"
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              <div className="text-sm text-gray-400 space-y-1">
                <p>용도: {session.image_purpose}</p>
                <p>메시지: {session.messages_count}개</p>
                <p>생성된 이미지: {session.images_generated}개</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
