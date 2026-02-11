// 이미지 용도
export type ImagePurpose =
  | 'sns_instagram_square'
  | 'sns_instagram_portrait'
  | 'sns_facebook'
  | 'banner_web'
  | 'banner_mobile'
  | 'product_showcase'
  | 'email_header'
  | 'custom'

// 스타일 프리셋
export type StylePreset =
  | 'modern'
  | 'minimal'
  | 'vibrant'
  | 'luxury'
  | 'playful'
  | 'professional'
  | 'natural'
  | 'tech'

// 세션 상태
export type SessionStatus = 'active' | 'completed' | 'archived'

// 메시지 역할
export type MessageRole = 'user' | 'assistant'

// 콘텐츠 유형
export type ContentType = 'text' | 'image' | 'mixed'

// 세션 생성 요청
export interface SessionCreateRequest {
  title?: string
  image_purpose: ImagePurpose
  style_preset?: StylePreset
  brand_guidelines?: Record<string, unknown>
}

// 이미지 생성 요청
export interface GenerateImageRequest {
  prompt: string
  style_preset?: StylePreset
  reference_image_url?: string
}

// 이미지 개선 요청
export interface RefineImageRequest {
  feedback: string
  image_id: string
}

// 메시지 응답
export interface ChatMessage {
  id: string
  session_id: string
  role: MessageRole
  content_type: ContentType
  text_content?: string
  image_url?: string
  image_thumbnail_url?: string
  tokens_used: number
  generation_time_ms?: number
  created_at: string
}

// 세션 응답
export interface ChatSession {
  id: string
  title?: string
  image_purpose: string
  status: SessionStatus
  style_preset?: string
  final_image_url?: string
  messages_count: number
  images_generated: number
  total_tokens_used: number
  created_at: string
  updated_at?: string
}

// 세션 상세 응답
export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[]
}

// 용도 프리셋 응답
export interface PurposePreset {
  id: string
  name: string
  ratio: string
  width?: number
  height?: number
  description: string
}

// 세션 목록 응답
export interface SessionListResponse {
  sessions: ChatSession[]
  total: number
  limit: number
  offset: number
}

// WebSocket 메시지
export interface WebSocketMessage {
  type: 'chat' | 'generate' | 'refine' | 'converse'
  content: string
  data?: {
    purpose?: ImagePurpose
    style?: StylePreset
  }
}

// WebSocket 응답
export interface WebSocketResponse {
  type: 'message' | 'image' | 'mixed' | 'status' | 'error'
  content?: string
  image_url?: string
  data?: Record<string, unknown>
  timestamp: string
}
