# 7SH7.github.io

김승환의 인프라·클라우드 엔지니어 포트폴리오입니다. 기본 페이지는 한국어 정적 HTML이며, 일본어·영어 전환과 프로젝트 분야 필터만 브라우저 JavaScript를 사용합니다. 프로젝트 카드는 주제와 핵심 성과만 먼저 보여주고, 선택하면 상세 내용을 펼칩니다.

- 공개 주소: <https://7sh7.github.io/>
- 라이브 서비스: <https://m.micemore.com/>
- GitHub: <https://github.com/7SH7>

## 구조

```text
content.json                  공개 콘텐츠와 KR/JP/EN 번역
build.py                     GitHub API의 공개 저장소 수를 반영해 HTML 생성·검증
template.html                인라인 CSS/JS 템플릿
index.html                   생성된 단일 정적 페이지
.github/workflows/build.yml  main push 시 빌드·검증·Pages 배포
```

외부 런타임 의존성은 Google Fonts뿐이며, 빌드는 Python 표준 라이브러리만 사용합니다.

## 로컬 빌드

```bash
python build.py
python build.py --check
```

네트워크 없이 저장된 GitHub 저장소 수를 사용하려면 다음처럼 실행합니다.

```bash
python build.py --offline
python build.py --offline --check
```

콘텐츠 수정 후 `python build.py`로 `index.html`을 다시 생성해 함께 커밋합니다. 배포는 `main` 브랜치 push를 기준으로 GitHub Actions가 수행합니다.

## 추후 확인할 값

- RISE 창업경진대회 정식 명칭·주최·시기를 확인한 뒤 수상 항목 추가
- LLM for Science의 데이터 실행 결과를 입증하는 공개 산출물 URL이 생기면 프로젝트 링크에 추가

SSOBBI 저장소는 공개 조직 저장소 <https://github.com/LikeLionHGU/SSOBBI_Back>로 확인해 반영했습니다.

## 공개하지 않는 자료

`reference.txt`, 원본 이력서·포트폴리오 PDF와 MICEMore 구조도는 `.gitignore`로 제외합니다.

AWS 구조도는 리전·서브넷 구조, 탐지·알림 스택, 내부 식별자와 운영 자동화 경로가 드러나므로 공개하지 않습니다. 운영 구성은 `content.json`의 `live_service.evidence`에 결과 수준으로만 기술합니다. 상세본이 필요한 경우 NDA 체결 후 개별 전달합니다.
