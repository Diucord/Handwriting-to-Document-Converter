# Modified Files Log

## 2026-03-02

### 1. `server/tools/tool_extract_html.py`
- Gemini 프롬프트에 bounding box 좌표 요청 추가 (`[IMAGE_PLACE_HOLDER_N|top,left,bottom,right]`)
- `_parse_placeholders()` 함수 추가: bbox 파싱 + PIL 크롭 + 폴백 처리
- 플레이스홀더 강제 추가 로직 제거 (Gemini가 없다고 판단하면 추가 안 함)
- 반환값에 `placeholder_images` dict 추가 (인덱스별 크롭된 base64)

### 2. `server/agents/orchestrator_agent.py`
- `_PLACEHOLDER_RE` regex 수정: `IMAGE_PLACEHOLDER` → `IMAGE_PLACE_HOLDER` (Gemini 출력과 일치시킴)
- `extract_pages_via_tool`에서 `placeholder_images`의 크롭 이미지를 `diagram_regions`에 전달하도록 변경

### 3. `server/tools/tool_assemble_pdf.py`
- `_PAGE_TEMPLATE.format(body=...)` → `.replace("{body}", ...)` 변경 (LaTeX `{}` 충돌 방지)
- 템플릿 내 `{{` 이스케이프를 `{`로 복원 (`.replace()` 방식이므로 불필요)

### 4. `server/tools/tool_classify_image.py`
- `illustration_redraw` 다시 활성화
- allowed_strategies에 `illustration_redraw` 복원
- 프롬프트에 illustration_redraw 예시 복원 (labeled schematic, atomic structures 등)

### 5. `server/tools/tool_classify_image.py` (모델 변경)
- 분류 모델: `gpt-4o-mini` → `gpt-4o` (정확도 향상)

### 6. `server/tools/tool_render_illustration.py` (파이프라인 확정)
- GPT-4o 분석 + gpt-image-1 재생성 파이프라인
- 분석 프롬프트: 모든 라벨 원본 언어 그대로 character-by-character 출력 강조
- 재생성 프롬프트: clean professional diagram, 원본 텍스트 정확 재현, flat style
- 반환값: `base64_png` (이미지)

### 7. `server/agents/orchestrator_agent.py` (단순화)
- HTML 다이어그램 로직 제거, 이미지 전용으로 통일
- `_replace_placeholders()`: 단일 `region_results` dict 사용
- `render_regions_via_tool()`: `region_results` 하나로 단순화

### 8. `client/src/StartPage.tsx` (공유 기능 추가)
- 공유 버튼 클릭 시 공유 시트(bottom sheet) 표시
- 링크 복사: `navigator.clipboard.writeText()` + fallback
- 카카오톡 공유: `sharer.kakao.com` URL 방식
- 메일 공유: `mailto:` 링크
- 복사 완료 토스트 메시지 (2초 자동 사라짐)

### 9. `client/src/StartPage.module.css` (공유 시트 스타일)
- `.shareOverlay`, `.shareSheet`, `.shareSheetVisible/Hidden` 추가
- `.shareOption`, `.shareIconCircle`, `.shareEmoji`, `.shareLabel` 추가
- `.toast` + `@keyframes toastFade` 애니메이션 추가

### 10. `server/tools/tool_render_math.py` (신규 - 수학 그래프 전용 렌더러)
- GPT-4o 분석 → matplotlib 코드 생성 → 실행 → PNG 출력 파이프라인
- 함수 그래프, 좌표계, 음영 영역, 접선 등 수학적 시각화 전용
- tempfile 기반 안전 실행, 실패 시 preserve_original 폴백

### 11. `server/tools/tool_classify_image.py` (math_graph 전략 추가)
- `primary_type`에 `math_graph` 추가
- `render_strategy`에 `math_graph` 추가 (최우선 판별)
- 프롬프트: 함수 곡선, 좌표계, 적분 음영, 접선 등 → math_graph로 분류
- `preserve_original`에서 함수 그래프 관련 항목 제거

### 12. `server/agents/orchestrator_agent.py` (math_graph 라우팅)
- `render_math` import 추가
- `_normalize_strategy()`에 `math_graph` 분기 추가
- `render_regions_via_tool()`에서 `math_graph` → `render_math.invoke()` 라우팅

### 13. `server/tools/tool_classify_image.py` (preserve_original 제거)
- 분류 단계에서 `preserve_original` 선택지 완전 제거
- LLM이 `preserve_original` 반환해도 `illustration_redraw`로 강제 변환
- confidence low → `illustration_redraw` 기본값 (기존: preserve_original)
- 분류 실패 시에도 `illustration_redraw` 시도 (기존: preserve_original)
- 모든 이미지 무조건 재생성 시도, preserve_original은 각 렌더러 내부 폴백으로만 사용
