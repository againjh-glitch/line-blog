# 라인 인테리어 저널 (blog.line-interior.co.kr)

라인 인테리어 웹블로그입니다. GitHub Pages로 무료 운영합니다.

## 폴더 구성
| 위치 | 내용 |
|---|---|
| `_src/posts/` | 글 원본 (마크다운) — 글은 여기에만 추가합니다 |
| `_src/images/` | 글에 쓰는 사진 원본 |
| `_src/config.json` | 매장 정보, 카테고리, 자주 묻는 질문 |
| `_src/style.css` | 디자인 |
| `_src/build.py` | 사이트를 만드는 프로그램 |
| 나머지 (`index.html`, `posts/`, `category/`, `img/` …) | build.py가 자동으로 만든 결과물 — 직접 고치지 않습니다 |

## 새 글 올리는 순서
1. `_src/posts/`에 `날짜-주소.md` 파일을 만들고, 맨 위에 아래 정보를 적습니다.
   ```
   ---
   title: "글 제목"
   slug: 영문-주소
   date: 2026-11-30
   category: cases        # cases / guide / space / material
   cover: 사진파일.jpg
   cover_alt: "사진 설명"
   description: "검색 결과에 보일 2~3문장 요약"
   summary: "글 맨 위 '한눈에 보기' 상자에 들어갈 요약"
   tags: [태그1, 태그2]
   faq:
     - q: "질문"
       a: "답변"
   ---
   ```
2. 사진은 `_src/images/`에 넣고, 본문에서는 `![설명](/img/파일이름.jpg)`로 씁니다.
3. `python3 _src/build.py` 실행 → 결과물 전체를 GitHub에 올립니다.

필요 패키지: `pip install markdown pyyaml pillow`

## 지우면 안 되는 파일
- `google….html` — 구글 서치콘솔 소유 확인 파일
- `naver….html` — 네이버 서치어드바이저 소유 확인 파일

build.py는 이 파일들을 건드리지 않습니다. 저장소에서 지우면 소유 확인이 풀리니 그대로 두세요.

## 검색엔진 등록 현황 (2026-11-23)
- 구글 서치콘솔: 소유 확인, sitemap.xml 제출
- 네이버 서치어드바이저: 소유 확인, sitemap.xml·rss.xml 제출
- RSS(`rss.xml`)에는 사진이 포함된 본문 전체가 들어갑니다 (네이버 권장 방식)
