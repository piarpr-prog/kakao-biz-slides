# Native CRM 2.0 — 슬라이드 덱

카카오 채널의 모든 접점을 CRM 트리거로 | 2026.06 카카오 비즈니스

---

## 파일 구조

| 파일 | 설명 | 수정 |
|---|---|---|
| `native_crm_v2.md` | **슬라이드 원본** — 여기를 수정하세요 | ✅ 편집 가능 |
| `build.py` | MD → HTML 빌드 스크립트 | ✅ 편집 가능 |
| `native_crm_build.html` | 빌드 결과물 (자동 생성) | ⚠ 직접 수정 금지 |
| `native_crm_dark_fixed.html` | 고정 기준본 (덮어쓰기 금지) | 🔒 읽기 전용 |
| `native_crm_dark.html` | 현재 다크테마 최신본 | 참고용 |
| `native_crm_v2.html` | 라이트테마 버전 | 참고용 |

---

## 협업 워크플로우

```
1. native_crm_v2.md 수정
       ↓
2. python3 build.py
       ↓
3. native_crm_build.html 브라우저에서 확인
       ↓
4. git add native_crm_v2.md native_crm_build.html
   git commit -m "슬라이드 수정: ..."
   git push
```

자동 감시 모드 (저장할 때마다 자동 재빌드):
```
python3 build.py --watch
```

커스텀 파일명:
```
python3 build.py --input my_slides.md --output my_slides.html
```

---

## MD 파일 작성 규칙

```markdown
# 문서 제목

## Slide 1 — COVER          ← 첫 슬라이드는 커버로 자동 렌더링

## Slide 2 — 슬라이드 제목   ← ## Slide N — 제목  형식 필수

### 섹션 제목               ← 카드 박스로 렌더링

| 컬럼1 | 컬럼2 | 컬럼3 |   ← 마크다운 표 → HTML 테이블
| --- | --- | --- |
| 값1 | 값2 | 값3 |

> 인사이트 텍스트            ← 노란 박스로 강조

- 항목 1                    ← 불릿 리스트
- 항목 2

**볼드**는 주황색으로 강조됩니다.
`코드`는 노란색 배경으로 표시됩니다.

---                         ← 슬라이드 구분선 (선택)
```

---

## 라이브 URL

| 버전 | URL |
|---|---|
| 빌드본 (최신) | https://piarpr-prog.github.io/kakao-biz-slides/native_crm_build.html |
| 다크 고정본 | https://piarpr-prog.github.io/kakao-biz-slides/native_crm_dark_fixed.html |
| 라이트 버전 | https://piarpr-prog.github.io/kakao-biz-slides/native_crm_v2.html |
