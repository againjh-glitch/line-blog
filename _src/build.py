#!/usr/bin/env python3
"""라인 인테리어 저널 — 정적 블로그 생성기

사용법:  python3 _src/build.py
  _src/posts/*.md 의 글과 _src/config.json 설정을 읽어
  저장소 맨 위 폴더에 index.html, posts/, category/, img/, sitemap.xml, rss.xml 등을 만듭니다.
필요 패키지: markdown, pyyaml, pillow
"""
import json, re, shutil, html, datetime
from pathlib import Path

import markdown
import yaml
from PIL import Image

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
CFG = json.loads((SRC / "config.json").read_text(encoding="utf-8"))
B = CFG["business"]
SITE = CFG["site_url"].rstrip("/")
CATS = {c["slug"]: c for c in CFG["categories"]}
KST = datetime.timezone(datetime.timedelta(hours=9))
esc = lambda s: html.escape(str(s or ""), quote=True)

GENERATED = ["posts", "category", "img", "assets"]


# ---------- 이미지 ----------
def build_images():
    out = ROOT / "img"
    out.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for f in sorted((SRC / "images").glob("*")):
        if f.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        im = Image.open(f)
        im = im.convert("RGB")
        im.thumbnail((1600, 1600))
        name = f.stem + ".jpg"
        im.save(out / name, "JPEG", quality=82, optimize=True, progressive=True)
        sizes[f.name] = (name, im.size)
        sizes[name] = (name, im.size)
    return sizes


# ---------- 글 읽기 ----------
def load_posts():
    posts = []
    for f in sorted((SRC / "posts").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
        if not m:
            raise SystemExit(f"[오류] {f.name}: 맨 위에 --- 로 감싼 정보 블록이 필요합니다")
        meta = yaml.safe_load(m.group(1)) or {}
        if meta.get("draft"):
            continue
        body_md = m.group(2)
        md = markdown.Markdown(extensions=["extra", "toc", "sane_lists"],
                               extension_configs={"toc": {"toc_depth": "2"}})
        body = md.convert(body_md)
        toc = [(t["id"], t["name"]) for t in md.toc_tokens]
        d = meta["date"]
        if isinstance(d, str):
            d = datetime.date.fromisoformat(d)
        upd = meta.get("updated", d)
        if isinstance(upd, str):
            upd = datetime.date.fromisoformat(upd)
        cat = meta.get("category", "guide")
        if cat not in CATS:
            raise SystemExit(f"[오류] {f.name}: category '{cat}' 는 config.json 에 없습니다")
        text = re.sub(r"<[^>]+>", "", body)
        posts.append(dict(
            slug=meta["slug"], title=meta["title"], description=meta["description"],
            summary=meta.get("summary", meta["description"]), date=d, updated=upd,
            category=cat, tags=meta.get("tags", []), cover=meta.get("cover", CFG["hero_image"]),
            cover_alt=meta.get("cover_alt", meta["title"]), faq=meta.get("faq", []),
            body=body, toc=toc, minutes=max(1, round(len(text) / 500)),
        ))
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


# ---------- 공통 조각 ----------
FONTS = ('<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>'
         '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">'
         '<link rel="stylesheet" href="https://hangeul.pstatic.net/hangeul_static/css/maru-buri.css">')


def business_schema():
    return {
        "@type": "GeneralContractor",
        "@id": f"{SITE}/#business",
        "name": B["name"],
        "alternateName": B["name_en"],
        "url": B["homepage"],
        "telephone": B["phone_intl"],
        "email": B["email"],
        "image": f"{SITE}/img/{Path(CFG['hero_image']).stem}.jpg",
        "address": {"@type": "PostalAddress", "streetAddress": B["street"],
                    "addressLocality": B["locality"], "addressRegion": B["region"],
                    "addressCountry": "KR"},
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"],
             "opens": h["opens"], "closes": h["closes"]} for h in B["hours_schema"]],
        "knowsAbout": B["services"],
        "sameAs": [B["homepage"], B["naver_blog"], SITE + "/"],
    }


def jsonld(obj):
    return ('<script type="application/ld+json">'
            + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>")


def head(title, desc, path, image, og_type="website", extra=""):
    url = SITE + path
    img = f"{SITE}/img/{Path(image).stem}.jpg"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="keywords" content="{esc(CFG['keywords'])}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(CFG['site_name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="ko_KR">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" type="application/rss+xml" title="{esc(CFG['site_name'])}" href="{SITE}/rss.xml">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%232a2620'/%3E%3Cpath d='M10 8v16h12' stroke='%23d9bf8f' stroke-width='3' fill='none'/%3E%3C/svg%3E">
{FONTS}
<link rel="stylesheet" href="/assets/style.css">
{extra}
</head>
<body>
"""


def header(active=""):
    links = "".join(
        f'<a href="/category/{c["slug"]}/"{" aria-current=\"page\"" if active == c["slug"] else ""}>{esc(c["name"])}</a>'
        for c in CFG["categories"])
    return f"""<a class="skip" href="#main">본문 바로가기</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="brand" href="/" aria-label="{esc(CFG['site_name'])} 홈">
      <span class="brand-mark">LINE.</span><span class="brand-sub">JOURNAL</span>
    </a>
    <nav class="nav" aria-label="카테고리">{links}</nav>
    <div class="bar-actions">
      <a class="link-out" href="{B['homepage']}" target="_blank" rel="noopener">홈페이지</a>
      <a class="btn btn-small" href="tel:{B['phone'].replace('-', '')}">견적 문의</a>
    </div>
  </div>
  <nav class="nav-mobile wrap" aria-label="카테고리">{links}</nav>
</header>
<main id="main">
"""


def cta():
    return f"""<section class="cta">
  <div class="wrap cta-in">
    <div>
      <p class="eyebrow">CONTACT</p>
      <h2>우리 집 공사, 먼저 이야기 나눠 보세요</h2>
      <p>현장 위치와 원하시는 공간을 알려주시면<br class="br-pc"> 공사 범위와 일정을 함께 살펴봅니다.</p>
    </div>
    <div class="cta-actions">
      <a class="btn" href="tel:{B['phone'].replace('-', '')}">전화 {esc(B['phone'])}</a>
      <a class="btn btn-ghost" href="{B['homepage']}" target="_blank" rel="noopener">홈페이지에서 견적 문의</a>
    </div>
  </div>
</section>
"""


def footer():
    year = datetime.datetime.now(KST).year
    return f"""</main>
<footer class="site-footer">
  <div class="wrap foot">
    <div>
      <p class="foot-brand">LINE. INTERIOR</p>
      <p>{esc(B['name'])} · 대표 {esc(B['ceo'])} · 사업자등록번호 {esc(B['biz_no'])}</p>
      <p>{esc(B['address_full'])} · 대표번호 <a href="tel:{B['phone'].replace('-', '')}">{esc(B['phone'])}</a></p>
      <p>상담 {esc(' / '.join(B['hours']))}</p>
    </div>
    <div class="foot-links">
      <a href="{B['homepage']}" target="_blank" rel="noopener">라인 인테리어 홈페이지</a>
      <a href="{B['naver_blog']}" target="_blank" rel="noopener">네이버 블로그</a>
      <a href="/rss.xml">RSS</a>
    </div>
  </div>
  <p class="wrap copy">© {year} LINE INTERIOR. All rights reserved.</p>
</footer>
</body>
</html>
"""


def fmt_date(d):
    return f"{d.year}. {d.month:02d}. {d.day:02d}."


def card(p, imgs, eager=False):
    name, (w, h) = imgs.get(p["cover"], (Path(p["cover"]).stem + ".jpg", (1600, 1067)))
    c = CATS[p["category"]]
    return f"""<article class="card">
  <a class="card-img" href="/posts/{p['slug']}/" tabindex="-1" aria-hidden="true">
    <img src="/img/{name}" alt="" width="{w}" height="{h}" loading="{'eager' if eager else 'lazy'}">
  </a>
  <div class="card-body">
    <p class="meta"><a href="/category/{c['slug']}/">{esc(c['name'])}</a><time datetime="{p['date'].isoformat()}">{fmt_date(p['date'])}</time></p>
    <h3><a href="/posts/{p['slug']}/">{esc(p['title'])}</a></h3>
    <p class="excerpt">{esc(p['description'])}</p>
  </div>
</article>"""


# ---------- 페이지 ----------
def page_home(posts, imgs):
    hero_name, (hw, hh) = imgs[CFG["hero_image"]]
    chips = "".join(f'<a class="chip" href="/category/{c["slug"]}/">{esc(c["name"])}</a>' for c in CFG["categories"])
    cards = "\n".join(card(p, imgs, i < 3) for i, p in enumerate(posts)) or '<p class="empty">첫 글을 준비하고 있습니다.</p>'
    faq_html = "".join(f"<details><summary>{esc(f['q'])}</summary><p>{esc(f['a'])}</p></details>" for f in CFG["faq"])
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "@id": f"{SITE}/#website", "url": SITE + "/", "name": CFG["site_name"],
         "description": CFG["description"], "inLanguage": "ko-KR", "publisher": {"@id": f"{SITE}/#business"}},
        business_schema(),
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f["q"],
            "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in CFG["faq"]]},
    ]}
    title = f"{CFG['site_name']} | 부천 라인 인테리어 현장 이야기·공사 가이드"
    out = head(title, CFG["description"], "/", CFG["hero_image"], extra=jsonld(schema))
    out += header()
    hero_t = esc(CFG["hero_title"]).replace("\n", "<br>")
    hero_p = esc(CFG["hero_text"]).replace("\n", "<br>")
    out += f"""<section class="hero">
  <img class="hero-img" src="/img/{hero_name}" alt="라인 인테리어가 시공한 화이트톤 주방" width="{hw}" height="{hh}" fetchpriority="high">
  <div class="hero-shade"></div>
  <div class="wrap hero-copy">
    <p class="eyebrow light">LINE INTERIOR JOURNAL</p>
    <h1>{hero_t}</h1>
    <p>{hero_p}</p>
  </div>
</section>
<section class="section">
  <div class="wrap">
    <div class="chips" aria-label="카테고리">{chips}</div>
    <div class="sec-head"><div><p class="eyebrow">LATEST</p><h2>최근 이야기</h2></div></div>
    <div class="grid">{cards}</div>
  </div>
</section>
<section class="section tint">
  <div class="wrap two">
    <div><p class="eyebrow">ABOUT</p><h2>{esc(B['name'])}</h2>
      <p class="lead">{esc(', '.join(B['services']))} 공사를 직접 시공합니다.<br>이 저널에는 실제 현장의 기록과 공사 전에 알아두면 좋은 정보를 담습니다.</p>
      <ul class="facts">
        <li><span>주소</span>{esc(B['address_full'])}</li>
        <li><span>대표번호</span><a href="tel:{B['phone'].replace('-', '')}">{esc(B['phone'])}</a></li>
        <li><span>상담시간</span>{esc(' / '.join(B['hours']))}</li>
      </ul>
      <p class="maplinks"><a href="https://map.naver.com/p/search/{esc(B['address_full'])}" target="_blank" rel="noopener">네이버 지도</a><a href="https://map.kakao.com/link/search/{esc(B['address_full'])}" target="_blank" rel="noopener">카카오맵</a></p>
    </div>
    <div><p class="eyebrow">FAQ</p><h2>자주 묻는 질문</h2><div class="faq">{faq_html}</div></div>
  </div>
</section>
"""
    out += cta() + footer()
    return out


def page_category(cat, posts, imgs):
    lst = [p for p in posts if p["category"] == cat["slug"]]
    cards = "\n".join(card(p, imgs) for p in lst) or '<p class="empty">아직 이 카테고리에 올라온 글이 없습니다.</p>'
    path = f"/category/{cat['slug']}/"
    schema = {"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "url": SITE + path, "name": f"{cat['name']} | {CFG['site_name']}",
         "description": cat["desc"], "isPartOf": {"@id": f"{SITE}/#website"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": CFG["site_name"], "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": cat["name"], "item": SITE + path}]}]}
    out = head(f"{cat['name']} | {CFG['site_name']}", f"{cat['desc']} — {B['name']}", path,
               CFG["hero_image"], extra=jsonld(schema))
    out += header(cat["slug"])
    out += f"""<section class="page-head"><div class="wrap">
  <nav class="crumbs" aria-label="현재 위치"><a href="/">저널 홈</a><span>›</span><span>{esc(cat['name'])}</span></nav>
  <h1>{esc(cat['name'])}</h1><p>{esc(cat['desc'])}</p>
</div></section>
<section class="section"><div class="wrap"><div class="grid">{cards}</div></div></section>
"""
    return out + cta() + footer()


def page_post(p, posts, imgs):
    c = CATS[p["category"]]
    path = f"/posts/{p['slug']}/"
    name, (w, h) = imgs.get(p["cover"], (Path(p["cover"]).stem + ".jpg", (1600, 1067)))
    related = [q for q in posts if q["slug"] != p["slug"] and q["category"] == p["category"]][:3]
    if len(related) < 3:
        related += [q for q in posts if q["slug"] != p["slug"] and q not in related][:3 - len(related)]
    graph = [
        {"@type": "BlogPosting", "@id": SITE + path + "#article", "mainEntityOfPage": SITE + path,
         "headline": p["title"], "description": p["description"],
         "image": f"{SITE}/img/{name}", "datePublished": p["date"].isoformat(),
         "dateModified": p["updated"].isoformat(), "inLanguage": "ko-KR",
         "articleSection": c["name"], "keywords": ", ".join(p["tags"]),
         "author": {"@id": f"{SITE}/#business"}, "publisher": {"@id": f"{SITE}/#business"},
         "isPartOf": {"@id": f"{SITE}/#website"}},
        business_schema(),
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": CFG["site_name"], "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": c["name"], "item": f"{SITE}/category/{c['slug']}/"},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": SITE + path}]},
    ]
    if p["faq"]:
        graph.append({"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": f["q"],
            "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in p["faq"]]})
    extra = jsonld({"@context": "https://schema.org", "@graph": graph}) + \
        f'<meta property="article:published_time" content="{p["date"].isoformat()}">'
    out = head(f"{p['title']} | {CFG['site_name']}", p["description"], path, p["cover"], "article", extra)
    out += header(c["slug"])
    toc = ""
    if len(p["toc"]) >= 2:
        toc = '<nav class="toc" aria-label="목차"><p>목차</p><ol>' + "".join(
            f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in p["toc"]) + "</ol></nav>"
    faq = ""
    if p["faq"]:
        faq = '<section class="post-faq"><h2 id="faq">자주 묻는 질문</h2>' + "".join(
            f"<details><summary>{esc(f['q'])}</summary><p>{esc(f['a'])}</p></details>" for f in p["faq"]) + "</section>"
    tags = "".join(f"<span>#{esc(t)}</span>" for t in p["tags"])
    upd = f' · 수정 <time datetime="{p["updated"].isoformat()}">{fmt_date(p["updated"])}</time>' if p["updated"] != p["date"] else ""
    rel = ""
    if related:
        rel = '<section class="section tint"><div class="wrap"><div class="sec-head"><div><p class="eyebrow">MORE</p><h2>함께 읽으면 좋은 글</h2></div></div><div class="grid">' + \
            "\n".join(card(q, imgs) for q in related) + "</div></div></section>"
    out += f"""<article class="post">
  <header class="post-head wrap narrow">
    <nav class="crumbs" aria-label="현재 위치"><a href="/">저널 홈</a><span>›</span><a href="/category/{c['slug']}/">{esc(c['name'])}</a></nav>
    <h1>{esc(p['title'])}</h1>
    <p class="post-meta">{esc(B['name'])} · <time datetime="{p['date'].isoformat()}">{fmt_date(p['date'])}</time>{upd} · {p['minutes']}분 읽기</p>
  </header>
  <figure class="post-cover wrap"><img src="/img/{name}" alt="{esc(p['cover_alt'])}" width="{w}" height="{h}" fetchpriority="high"></figure>
  <div class="wrap narrow">
    <aside class="summary" aria-label="한눈에 보기"><p class="eyebrow">한눈에 보기</p><p>{esc(p['summary'])}</p></aside>
    {toc}
    <div class="prose">{p['body']}</div>
    {faq}
    <p class="tags">{tags}</p>
  </div>
</article>
{rel}
"""
    return out + cta() + footer()


def page_404():
    out = head(f"페이지를 찾을 수 없습니다 | {CFG['site_name']}", CFG["description"], "/404.html", CFG["hero_image"])
    out = out.replace('<link rel="canonical"', '<meta name="robots" content="noindex"><link rel="canonical"')
    out += header()
    out += '<section class="page-head"><div class="wrap"><h1>페이지를 찾을 수 없습니다</h1><p>주소가 바뀌었거나 삭제된 글입니다.</p><p><a class="btn" href="/">저널 홈으로</a></p></div></section>'
    return out + footer()


def sitemap(posts):
    urls = [(SITE + "/", posts[0]["updated"] if posts else datetime.date.today())]
    for c in CFG["categories"]:
        lst = [p for p in posts if p["category"] == c["slug"]]
        urls.append((f"{SITE}/category/{c['slug']}/", lst[0]["updated"] if lst else None))
    urls += [(f"{SITE}/posts/{p['slug']}/", p["updated"]) for p in posts]
    body = "".join(f"<url><loc>{u}</loc>" + (f"<lastmod>{d.isoformat()}</lastmod>" if d else "") + "</url>\n" for u, d in urls)
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + "</urlset>\n"


def rss(posts):
    def rfc(d):
        return datetime.datetime(d.year, d.month, d.day, 9, 0, tzinfo=KST).strftime("%a, %d %b %Y %H:%M:%S +0900")
    items = "".join(f"""<item><title>{esc(p['title'])}</title><link>{SITE}/posts/{p['slug']}/</link><guid>{SITE}/posts/{p['slug']}/</guid><pubDate>{rfc(p['date'])}</pubDate><category>{esc(CATS[p['category']]['name'])}</category><description>{esc(p['description'])}</description></item>
""" for p in posts[:30])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{esc(CFG['site_name'])}</title><link>{SITE}/</link><description>{esc(CFG['description'])}</description><language>ko</language>
{items}</channel></rss>
"""


def write(rel, text):
    f = ROOT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


def main():
    for d in GENERATED:
        if (ROOT / d).exists():
            shutil.rmtree(ROOT / d)
    imgs = build_images()
    posts = load_posts()
    (ROOT / "assets").mkdir()
    shutil.copy(SRC / "style.css", ROOT / "assets" / "style.css")
    write("index.html", page_home(posts, imgs))
    for c in CFG["categories"]:
        write(f"category/{c['slug']}/index.html", page_category(c, posts, imgs))
    for p in posts:
        write(f"posts/{p['slug']}/index.html", page_post(p, posts, imgs))
    write("404.html", page_404())
    write("sitemap.xml", sitemap(posts))
    write("rss.xml", rss(posts))
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    write("CNAME", SITE.split("://", 1)[1] + "\n")
    write(".nojekyll", "")
    print(f"완료: 글 {len(posts)}편, 카테고리 {len(CFG['categories'])}개, 이미지 {len({v[0] for v in imgs.values()})}장")


if __name__ == "__main__":
    main()
