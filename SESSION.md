# Gemini Image Chat - 세션 기록

## 현재 개발 목표
> Gemini API 기반 마케팅 이미지 생성 채팅 서비스

## 현재 상태
- **Phase**: 배포 준비 완료
- **마지막 업데이트**: 2026-02-10

## 작업 요청 로그
| 일시 | 요청 내용 | 상태 |
|------|----------|------|
| 2026-02-10 | Gemini API 연동 마케팅 이미지 채팅 서비스 개발 | ✅ 완료 |
| 2026-02-10 | 별도 GitHub 레포로 분리 | ✅ 완료 |
| 2026-02-10 | Fly.io 배포 설정 | ⚠️ 재시도 필요 |

## 완료된 작업 상세

### 2026-02-10: 프로젝트 생성 및 백엔드 구현
- **변경 파일**:
  - `src/config.py` - 설정 관리
  - `src/storage/models.py` - DB 모델 (Session, Message, GeneratedImage)
  - `src/schemas/image_chat.py` - Pydantic 스키마
  - `src/modules/gemini_image.py` - Gemini API 클라이언트
  - `src/services/image_chat_service.py` - 비즈니스 로직
  - `src/api/routes/image_chat.py` - REST API
  - `src/api/routes/websocket.py` - WebSocket 엔드포인트
  - `src/api/main.py` - FastAPI 앱

### 2026-02-10: 프론트엔드 구현
- **변경 파일**:
  - `frontend/src/pages/SessionsPage.tsx` - 세션 목록/생성
  - `frontend/src/pages/ChatPage.tsx` - 채팅 인터페이스
  - `frontend/src/hooks/useImageChatWebSocket.ts` - WebSocket 훅
  - `frontend/src/components/image-chat/*` - UI 컴포넌트
  - `frontend/src/api/imageChat.ts` - API 클라이언트
  - `frontend/src/types/imageChat.ts` - TypeScript 타입

### 2026-02-10: 배포 설정
- **변경 파일**:
  - `Dockerfile` - Docker 빌드 설정
  - `fly.toml` - Fly.io 앱 설정
  - `entrypoint.sh` - 서버 시작 스크립트

## 다음 작업 예정
1. Fly.io 배포 완료
2. GEMINI_API_KEY secret 설정
3. 실제 이미지 생성 테스트

## 배포 방법

### 1. Fly.io 앱 배포
```bash
cd gemini-image-chat
fly deploy
```

### 2. Gemini API 키 설정
```bash
fly secrets set GEMINI_API_KEY=your_api_key_here
```

### 3. 배포 확인
- URL: https://gemini-image-chat.fly.dev

## 프로젝트 구조

```
gemini-image-chat/
├── src/                      # 백엔드 소스
│   ├── api/                  # FastAPI 앱
│   │   ├── main.py
│   │   └── routes/
│   │       ├── image_chat.py
│   │       └── websocket.py
│   ├── modules/              # Gemini API 모듈
│   │   └── gemini_image.py
│   ├── schemas/              # Pydantic 스키마
│   │   └── image_chat.py
│   ├── services/             # 비즈니스 로직
│   │   └── image_chat_service.py
│   ├── storage/              # DB 모델
│   │   └── models.py
│   └── config.py
├── frontend/                 # React 프론트엔드
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── hooks/
│       ├── api/
│       └── types/
├── static/                   # 빌드된 프론트엔드
├── Dockerfile
├── fly.toml
├── entrypoint.sh
└── pyproject.toml
```

## 기능

### 이미지 용도 프리셋
- SNS (Instagram Square/Portrait, Facebook)
- 배너 (Web, Mobile)
- 제품 이미지
- 이메일 헤더

### 스타일 프리셋
- Modern, Minimal, Vibrant, Luxury
- Playful, Professional, Natural, Tech

### API 엔드포인트
- `POST /api/image-chat/sessions` - 세션 생성
- `GET /api/image-chat/sessions` - 세션 목록
- `GET /api/image-chat/sessions/{id}` - 세션 상세
- `DELETE /api/image-chat/sessions/{id}` - 세션 삭제
- `GET /api/image-chat/purposes` - 용도 목록
- `GET /api/image-chat/styles` - 스타일 목록
- `WS /ws/image-chat/{session_id}` - 실시간 채팅

## 환경변수
- `GEMINI_API_KEY` - Gemini API 키 (필수)
- `GEMINI_MODEL` - 모델명 (기본: gemini-2.0-flash-exp)
- `DATABASE_URL` - SQLite DB 경로 (기본: sqlite+aiosqlite:///./data/image_chat.db)

## 알려진 이슈
- entrypoint.sh Windows 줄바꿈 문제 수정됨 (2026-02-10)
