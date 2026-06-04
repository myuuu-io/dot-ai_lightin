#!/usr/bin/env python3
"""content/articles/*.md → site/ 静的 HTML フル再生成。依存ゼロ (Python 標準ライブラリのみ)。

使い方: python3 .claude/skills/site-builder/scripts/build_site.py
デザイン: note.com 風 (クリエイターページ風の一覧 + 余白広めの記事ページ)
"""

import html as htmlmod
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path.cwd()
CONFIG_PATH = ROOT / "lightin.config.json"
ARTICLES_DIR = ROOT / "content" / "articles"
IMAGES_DIR = ROOT / "content" / "images"
SITE_DIR = ROOT / "site"


# ---------------------------------------------------------------- frontmatter

def parse_frontmatter(text: str):
    """--- で囲まれた key: value を dict で返す。本文との tuple。"""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]
        meta[key.strip()] = value
    return meta, parts[2].lstrip("\n")


# ---------------------------------------------------------------- markdown

def inline(text: str) -> str:
    text = htmlmod.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" loading="lazy">', text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def md_to_html(md: str) -> str:
    out = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # コードフェンス
        if stripped.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            out.append(f"<pre><code>{htmlmod.escape(chr(10).join(code))}</code></pre>")
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        # 見出し
        m = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if m:
            # 本文の # は h2 扱いに揃える (h1 はタイトル専用)
            level = max(len(m.group(1)), 2)
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # 罫線
        if re.match(r"^(-{3,}|\*{3,})$", stripped):
            out.append("<hr>")
            i += 1
            continue

        # 引用
        if stripped.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(quote))}</p></blockquote>")
            continue

        # 箇条書き
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(f"<li>{inline(re.sub(r'^[-*]\s+', '', lines[i].strip()))}</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue

        # 番号リスト
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(f"<li>{inline(re.sub(r'^\d+\.\s+', '', lines[i].strip()))}</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue

        # 画像単独行は figure に
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if m:
            out.append(
                f'<figure><img src="{m.group(2)}" alt="{htmlmod.escape(m.group(1))}" loading="lazy"></figure>'
            )
            i += 1
            continue

        # 段落 (連続行をまとめる)
        para = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or re.match(r"^(#{1,4}\s|[-*]\s|\d+\.\s|>|```|!\[)", nxt) or re.match(r"^(-{3,}|\*{3,})$", nxt):
                break
            para.append(nxt)
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")

    return "\n".join(out)


# ---------------------------------------------------------------- templates

CSS_TEMPLATE = """\
:root {
  --accent: __ACCENT__;
  --ink: #08131a;
  --muted: #889199;
  --border: #efefef;
  --bg: #ffffff;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Noto Sans JP", sans-serif;
  color: var(--ink); background: var(--bg);
  -webkit-font-smoothing: antialiased;
}
a { color: var(--ink); }
img { max-width: 100%; }

/* ---- 共通ヘッダー (note 風の細い白バー) ---- */
.site-header {
  position: sticky; top: 0; z-index: 10;
  background: rgba(255,255,255,.97); backdrop-filter: blur(6px);
  border-bottom: 1px solid var(--border);
}
.site-header .inner {
  max-width: 856px; margin: 0 auto; padding: 10px 20px;
  display: flex; align-items: center; gap: 10px;
}
.logo-mark {
  width: 30px; height: 30px; border-radius: 50%;
  background: var(--accent); color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 15px;
  flex-shrink: 0;
}
.logo-name { font-weight: 700; font-size: 15px; text-decoration: none; color: var(--ink); }

/* ---- 一覧 (クリエイターページ風) ---- */
.creator-hero { text-align: center; padding: 52px 20px 8px; }
.creator-avatar {
  width: 84px; height: 84px; border-radius: 50%; margin: 0 auto;
  background: linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 60%, #08131a));
  color: #fff; font-size: 40px;
  display: flex; align-items: center; justify-content: center;
}
.creator-name { font-size: 22px; font-weight: 800; margin-top: 16px; letter-spacing: .01em; }
.creator-bio { font-size: 13px; color: var(--muted); margin-top: 8px; line-height: 1.8; }
.tab-bar {
  max-width: 680px; margin: 36px auto 0; padding: 0 20px;
  display: flex; gap: 28px; border-bottom: 1px solid var(--border);
}
.tab { font-size: 14px; font-weight: 600; color: var(--muted); padding: 10px 2px; }
.tab.active {
  color: var(--ink); border-bottom: 2px solid var(--ink); margin-bottom: -1px;
}
.tab .count { color: var(--muted); font-weight: 400; margin-left: 4px; font-size: 12px; }

.note-list { max-width: 680px; margin: 0 auto; padding: 4px 20px 96px; }
.note-item {
  display: flex; gap: 20px; align-items: flex-start;
  padding: 26px 0; border-bottom: 1px solid var(--border);
  text-decoration: none; color: inherit;
}
.note-item-text { flex: 1; min-width: 0; }
.note-item-title {
  font-size: 17px; font-weight: 700; line-height: 1.65;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.note-item:hover .note-item-title { color: color-mix(in srgb, var(--ink) 60%, var(--accent)); }
.note-item-desc {
  font-size: 13px; color: var(--muted); line-height: 1.8; margin-top: 6px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.note-item-meta {
  display: flex; align-items: center; gap: 8px; margin-top: 12px;
  font-size: 12px; color: var(--muted);
}
.mini-avatar {
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--accent); color: #fff; font-size: 10px;
  display: inline-flex; align-items: center; justify-content: center;
}
.note-item-thumb {
  width: 160px; height: 84px; border-radius: 4px; object-fit: cover; flex-shrink: 0;
}
.note-item-thumb-placeholder {
  width: 160px; height: 84px; border-radius: 4px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 55%, #08131a));
  color: #fff; font-size: 26px;
  display: flex; align-items: center; justify-content: center;
}
.empty-state { text-align: center; color: var(--muted); padding: 80px 0; font-size: 14px; }

/* ---- 記事ページ (note 風) ---- */
.article-container { max-width: 620px; margin: 0 auto; padding: 44px 20px 96px; }
.article-eyecatch { width: 100%; border-radius: 8px; display: block; margin-bottom: 36px; }
.article-title { font-size: 28px; font-weight: 800; line-height: 1.55; letter-spacing: .01em; }
.author-row {
  display: flex; align-items: center; gap: 10px;
  margin-top: 24px; padding-bottom: 24px; border-bottom: 1px solid var(--border);
}
.author-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--accent); color: #fff; font-size: 19px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.author-name { font-size: 14px; font-weight: 700; line-height: 1.4; }
.author-date { font-size: 12px; color: var(--muted); }

.article-body { margin-top: 40px; font-size: 16px; line-height: 2.05; }
.article-body p { margin-bottom: 2em; }
.article-body h2 { font-size: 23px; font-weight: 700; line-height: 1.6; margin: 64px 0 28px; }
.article-body h3 { font-size: 18px; font-weight: 700; line-height: 1.6; margin: 48px 0 20px; }
.article-body h4 { font-size: 16px; font-weight: 700; margin: 40px 0 16px; }
.article-body ul, .article-body ol { margin: 0 0 2em; padding-left: 1.5em; }
.article-body li { margin-bottom: .5em; }
.article-body a { color: #0f83fd; text-decoration: none; }
.article-body a:hover { text-decoration: underline; }
.article-body figure { margin: 40px 0; text-align: center; }
.article-body img { border-radius: 6px; }
.article-body blockquote {
  border-left: 2px solid #d6d6d6; color: #555;
  padding: 2px 0 2px 18px; margin: 0 0 2em;
}
.article-body blockquote p { margin-bottom: 0; }
.article-body pre {
  background: #f7f7f7; border: 1px solid var(--border); border-radius: 6px;
  padding: 18px; overflow-x: auto; font-size: 13px; line-height: 1.7; margin: 0 0 2em;
}
.article-body code { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: .88em; }
.article-body p code, .article-body li code {
  background: #f2f2f2; padding: 2px 6px; border-radius: 4px;
}
.article-body hr {
  border: none; text-align: center; margin: 56px 0;
}
.article-body hr::before { content: "* * *"; color: #b9b9b9; letter-spacing: .6em; font-size: 14px; }

.hashtags { margin-top: 56px; display: flex; flex-wrap: wrap; gap: 6px 14px; }
.hashtag { font-size: 13px; color: #0f83fd; text-decoration: none; }
.hashtag:hover { text-decoration: underline; }

/* スキ (♡) — JS なしの CSS チェックボックストグル */
.like-row {
  margin-top: 28px; padding: 24px 0;
  border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; gap: 14px;
}
.like-btn { position: relative; cursor: pointer; display: inline-flex; }
.like-btn input { position: absolute; opacity: 0; pointer-events: none; }
.like-btn .heart {
  width: 46px; height: 46px; border: 1px solid #d9d9d9; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: #b9b9b9; background: #fff;
  transition: transform .15s ease, color .15s ease, border-color .15s ease;
}
.like-btn:hover .heart { border-color: #ff2d55; color: #ff2d55; }
.like-btn input:checked + .heart {
  color: #fff; background: #ff2d55; border-color: #ff2d55; transform: scale(1.08);
}
.like-label { font-size: 13px; color: var(--muted); }

.author-footer {
  margin-top: 40px; display: flex; align-items: center; gap: 14px;
}
.author-footer .author-avatar { width: 56px; height: 56px; font-size: 26px; }
.author-footer-name { font-size: 15px; font-weight: 700; }
.author-footer-bio { font-size: 12px; color: var(--muted); margin-top: 3px; line-height: 1.7; }
.back-to-list {
  display: inline-block; margin-top: 48px; font-size: 14px;
  color: var(--muted); text-decoration: none;
}
.back-to-list:hover { color: var(--ink); }

.site-footer { text-align: center; color: #c2c2c2; font-size: 11px; padding: 0 0 48px; }

@media (max-width: 600px) {
  .article-title { font-size: 22px; }
  .note-item-thumb, .note-item-thumb-placeholder { width: 112px; height: 59px; }
  .note-item { gap: 14px; }
}
"""

PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<meta name="description" content="__DESCRIPTION__">
<link rel="stylesheet" href="__CSS_PATH__">
</head>
<body>
<header class="site-header">
  <div class="inner">
    <span class="logo-mark">⚡</span>
    <a class="logo-name" href="__HOME_PATH__">__MEDIA_NAME__</a>
  </div>
</header>
__CONTENT__
<footer class="site-footer">__MEDIA_NAME__ — Generated by Lightin ⚡</footer>
</body>
</html>
"""


def render_page(content: str, *, title: str, description: str, config: dict, depth: int = 0) -> str:
    prefix = "../" * depth
    return (
        PAGE_TEMPLATE
        .replace("__TITLE__", htmlmod.escape(title))
        .replace("__DESCRIPTION__", htmlmod.escape(description))
        .replace("__CSS_PATH__", prefix + "style.css")
        .replace("__HOME_PATH__", prefix + "index.html")
        .replace("__MEDIA_NAME__", htmlmod.escape(config["mediaName"]))
        .replace("__CONTENT__", content)
    )


# ---------------------------------------------------------------- build

def main() -> None:
    if not CONFIG_PATH.exists():
        print("config エラー: lightin.config.json がありません。先にオンボーディングを実行してください。")
        sys.exit(1)
    config = json.loads(CONFIG_PATH.read_text())
    accent = config.get("design", {}).get("accentColor", "#2cb696")
    media_name = config["mediaName"]
    tagline = config.get("tagline", "")

    # site/ をフル再生成
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    (SITE_DIR / "articles").mkdir(parents=True)
    if IMAGES_DIR.exists():
        shutil.copytree(IMAGES_DIR, SITE_DIR / "images", dirs_exist_ok=True)

    (SITE_DIR / "style.css").write_text(CSS_TEMPLATE.replace("__ACCENT__", accent))

    articles = []
    skipped = []
    for md_path in sorted(ARTICLES_DIR.glob("*.md")):
        meta, body = parse_frontmatter(md_path.read_text())
        missing = [k for k in ("title", "date", "description") if not meta.get(k)]
        if missing:
            skipped.append(f"{md_path.name} (frontmatter に {', '.join(missing)} がありません)")
            continue
        slug = md_path.stem
        eyecatch = meta.get("eyecatch", "")
        eyecatch_rel = eyecatch.lstrip("/") if eyecatch else ""
        has_eyecatch = bool(eyecatch_rel) and (SITE_DIR / eyecatch_rel).exists()
        articles.append({
            "slug": slug, "meta": meta, "body": body,
            "eyecatch_rel": eyecatch_rel if has_eyecatch else "",
        })

    articles.sort(key=lambda a: a["meta"]["date"], reverse=True)

    # 記事ページ
    for a in articles:
        meta = a["meta"]
        body_html = md_to_html(a["body"]).replace('src="/images/', 'src="../images/')
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [tags] if tags else []
        hashtags_html = (
            '<div class="hashtags">'
            + "".join(f'<a class="hashtag" href="../index.html">#{htmlmod.escape(t)}</a>' for t in tags)
            + "</div>"
        ) if tags else ""
        eyecatch_html = (
            f'<img class="article-eyecatch" src="../{a["eyecatch_rel"]}" alt="">'
            if a["eyecatch_rel"] else ""
        )
        content = f"""\
<main class="article-container">
{eyecatch_html}
<h1 class="article-title">{htmlmod.escape(meta["title"])}</h1>
<div class="author-row">
  <span class="author-avatar">⚡</span>
  <div>
    <div class="author-name">{htmlmod.escape(media_name)}</div>
    <div class="author-date">{htmlmod.escape(meta["date"])}</div>
  </div>
</div>
<div class="article-body">
{body_html}
</div>
{hashtags_html}
<div class="like-row">
  <label class="like-btn"><input type="checkbox"><span class="heart">♥</span></label>
  <span class="like-label">この記事にスキ⚡</span>
</div>
<div class="author-footer">
  <span class="author-avatar">⚡</span>
  <div>
    <div class="author-footer-name">{htmlmod.escape(media_name)}</div>
    <div class="author-footer-bio">{htmlmod.escape(tagline)}</div>
  </div>
</div>
<a class="back-to-list" href="../index.html">← 記事一覧へもどる</a>
</main>"""
        page = render_page(
            content, title=f'{meta["title"]}｜{media_name}',
            description=meta["description"], config=config, depth=1,
        )
        (SITE_DIR / "articles" / f"{a['slug']}.html").write_text(page)

    # index (クリエイターページ風)
    if articles:
        items = []
        for a in articles:
            meta = a["meta"]
            thumb = (
                f'<img class="note-item-thumb" src="{a["eyecatch_rel"]}" alt="" loading="lazy">'
                if a["eyecatch_rel"]
                else '<div class="note-item-thumb-placeholder">⚡</div>'
            )
            items.append(f"""\
<a class="note-item" href="articles/{a['slug']}.html">
<div class="note-item-text">
<div class="note-item-title">{htmlmod.escape(meta["title"])}</div>
<div class="note-item-desc">{htmlmod.escape(meta["description"])}</div>
<div class="note-item-meta"><span class="mini-avatar">⚡</span>{htmlmod.escape(media_name)}<span>{htmlmod.escape(meta["date"])}</span></div>
</div>
{thumb}
</a>""")
        list_html = "\n".join(items)
    else:
        list_html = '<div class="empty-state">まだ記事がありません。ライティンに「◯◯について記事書いて」と頼んでみよう ⚡</div>'

    index_content = f"""\
<div class="creator-hero">
  <div class="creator-avatar">⚡</div>
  <div class="creator-name">{htmlmod.escape(media_name)}</div>
  <div class="creator-bio">{htmlmod.escape(tagline)}</div>
</div>
<nav class="tab-bar">
  <span class="tab active">記事<span class="count">{len(articles)}</span></span>
</nav>
<main class="note-list">
{list_html}
</main>"""

    index_page = render_page(
        index_content, title=media_name,
        description=tagline, config=config, depth=0,
    )
    (SITE_DIR / "index.html").write_text(index_page)

    print(f"✅ ビルド完了: 記事 {len(articles)} 本 → site/index.html")
    for s in skipped:
        print(f"⚠️  スキップ: {s}")


if __name__ == "__main__":
    main()
