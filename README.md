# Gemini Image Chat

Gemini API 기반 마케팅 이미지 생성 채팅 서비스

## 기능

- 🎨 **AI 이미지 생성**: Gemini 2.0 Flash를 사용한 마케팅 이미지 생성
- 💬 **실시간 채팅**: WebSocket 기반 실시간 대화
- ✨ **이미지 개선**: Multi-turn 대화로 이미지 수정/개선
- 📐 **7가지 용도 프리셋**: Instagram, Facebook, 웹 배너, 모바일 배너, 제품 쇼케이스, 이메일 헤더
- 🎭 **8가지 스타일**: 모던, 미니멀, 비비드, 럭셔리, 플레이풀, 프로페셔널, 내추럴, 테크

## 기술 스택

### 백엔드
- FastAPI
- Google Gemini API (google-genai)
- SQLAlchemy + aiosqlite
- WebSocket

### 프론트엔드
- React 18
- TypeScript
- Tailwind CSS
- Vite

## 설치 및 실행

### 환경 변수 설정

```bash
cp .env.example .env
# .env 파일에서 GEMINI_API_KEY 설정
```

### 백엔드 실행

```bash
# 의존성 설치
uv pip install -e .

# 서버 실행
uvicorn src.api.main:app --reload --port 8000
```

### 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

## API 엔드포인트

### REST API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/image-chat/sessions` | 세션 생성 |
| GET | `/api/image-chat/sessions` | 세션 목록 |
| GET | `/api/image-chat/sessions/{id}` | 세션 상세 |
| DELETE | `/api/image-chat/sessions/{id}` | 세션 삭제 |
| POST | `/api/image-chat/sessions/{id}/generate` | 이미지 생성 |
| POST | `/api/image-chat/sessions/{id}/refine` | 이미지 개선 |
| GET | `/api/image-chat/purposes` | 용도 프리셋 목록 |

### WebSocket

```
WS /ws/image-chat/{session_id}
```

**메시지 타입:**
- `chat`: 텍스트 대화
- `generate`: 이미지 생성
- `refine`: 이미지 개선

## 배포 (Fly.io)

```bash
# 앱 생성
fly launch --name gemini-image-chat

# 시크릿 설정
fly secrets set GEMINI_API_KEY=your_api_key

# 배포
fly deploy
```

## 라이선스

MIT
