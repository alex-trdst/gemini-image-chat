import type {
  ChatMessage,
  ChatSessionDetail,
  GenerateImageRequest,
  PurposePreset,
  RefineImageRequest,
  SessionCreateRequest,
  SessionListResponse,
} from '../types/imageChat'

const API_BASE = '/api/image-chat'

// 세션 목록 조회
export async function fetchSessions(
  limit = 20,
  offset = 0
): Promise<SessionListResponse> {
  const res = await fetch(`${API_BASE}/sessions?limit=${limit}&offset=${offset}`)
  if (!res.ok) throw new Error('세션 목록을 불러올 수 없습니다.')
  return res.json()
}

// 세션 생성
export async function createSession(
  data: SessionCreateRequest
): Promise<ChatSessionDetail> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('세션을 생성할 수 없습니다.')
  return res.json()
}

// 세션 상세 조회
export async function fetchSession(sessionId: string): Promise<ChatSessionDetail> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`)
  if (!res.ok) throw new Error('세션을 불러올 수 없습니다.')
  return res.json()
}

// 세션 삭제
export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error('세션을 삭제할 수 없습니다.')
}

// 메시지 전송
export async function sendMessage(
  sessionId: string,
  content: string
): Promise<ChatMessage> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  })
  if (!res.ok) throw new Error('메시지를 전송할 수 없습니다.')
  return res.json()
}

// 이미지 생성
export async function generateImage(
  sessionId: string,
  data: GenerateImageRequest
): Promise<ChatMessage> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('이미지를 생성할 수 없습니다.')
  return res.json()
}

// 이미지 개선
export async function refineImage(
  sessionId: string,
  data: RefineImageRequest
): Promise<ChatMessage> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/refine`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('이미지를 개선할 수 없습니다.')
  return res.json()
}

// 용도 프리셋 조회
export async function fetchPurposes(): Promise<PurposePreset[]> {
  const res = await fetch(`${API_BASE}/purposes`)
  if (!res.ok) throw new Error('용도 목록을 불러올 수 없습니다.')
  return res.json()
}
