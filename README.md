# 삼성전자 PSU 보상 계산기

삼성전자 PSU(성과연동 주식보상) 제도의 직급별 예상 보상 주식 수와
세전·세후 수령액을 확인하는 비공식 참고용 계산기입니다.
Yahoo Finance 시세를 매일 자동으로 받아 기준주가를 갱신합니다.

## 프로젝트 구조

```
.
├── index.html                     # 계산기 페이지 (정적)
├── data.json                      # 시세 데이터 (자동 갱신 대상)
├── scripts/
│   └── update_data.py             # 시세 수집·VWAP 계산 스크립트
└── .github/workflows/
    └── update-data.yml            # 매일 data.json 을 갱신하는 워크플로우
```

## 값의 분류

- **고정 상수** — `index.html` 의 `PSU` 객체. 최초 기준가(85,385원),
  약정 종료일(2028-10-13), 직급별 약정 주식(CL1·2 200주 / CL3·4 300주),
  지급 배수 6구간. 제도가 정한 값이므로 코드에서만 수정.
- **시장 데이터** — `data.json`. 현재가와 1주·1개월·2개월·3개월 VWAP.
  GitHub Actions 가 매일 자동 갱신.
- **사용자 입력** — 직급, 평가 주가(시나리오), 한계세율. UI에서 조작.

## 기준주가 산출식

```
기준주가 = (1주 VWAP + 1개월 VWAP + 2개월 VWAP) ÷ 3
```

PSU 평가식에는 1주·1개월·2개월 VWAP 이 쓰입니다. `data.json` 에는
차트 표시용으로 3개월 VWAP 도 함께 저장됩니다.

## 배포 방법 (GitHub Pages)

1. 이 폴더 전체를 새 GitHub 저장소에 푸시합니다.
2. 저장소 **Settings → Pages** 에서 Source 를 `main` 브랜치 루트로 지정합니다.
3. 잠시 후 `https://<사용자명>.github.io/<저장소명>/` 에서 접속됩니다.

## 시세 자동 갱신

- `.github/workflows/update-data.yml` 이 매일 평일 18:30(KST)에 실행되어
  `scripts/update_data.py` 로 `data.json` 을 갱신·커밋합니다.
- 배포 직후 실제 데이터를 채우려면 저장소 **Actions 탭 → Update stock data
  → Run workflow** 로 수동 실행하세요.
- 저장소 **Settings → Actions → General → Workflow permissions** 에서
  *Read and write permissions* 가 켜져 있어야 커밋이 됩니다.

## 알아둘 점

- `scripts/update_data.py` 는 표준 라이브러리만 사용합니다(설치 의존성 없음).
- Yahoo Finance 는 비공식 API 이며, 응답 형식이 바뀌면 스크립트 수정이
  필요할 수 있습니다.
- GitHub 의 예약 워크플로우는 저장소가 60일간 비활성이면 자동 중지되며,
  cron 실행 시각은 부하에 따라 지연될 수 있습니다.
- 로컬에서 `index.html` 을 `file://` 로 직접 열면 `data.json` fetch 가
  브라우저 보안정책에 막힙니다. 로컬 확인 시에는
  `python -m http.server` 로 간단한 웹 서버를 띄워 접속하세요.

## 면책

공개된 제도 정보 기반의 비공식 참고용 도구입니다. 실제 지급 주식 수,
지급 시점, 과세 방식은 회사 공식 안내 및 세무 신고 결과와 다를 수 있습니다.
세후 금액은 한계세율 + 지방소득세 10% 의 단순 추정치입니다.

제도 정보 출처: 서울신문 2025-10-14 보도.
한계세율: 국세청 소득세법 제55조.
