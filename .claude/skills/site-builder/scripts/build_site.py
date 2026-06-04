#!/usr/bin/env python3
"""content/articles/*.md → site/ 静的 HTML フル再生成。依存ゼロ (Python 標準ライブラリのみ)。

使い方: python3 .claude/skills/site-builder/scripts/build_site.py
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
  --ink: #1a1a1a;
  --muted: #6b7280;
  --bg: #fafaf9;
  --card: #ffffff;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Noto Sans JP", sans-serif;
  color: var(--ink); background: var(--bg); line-height: 1.9;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); }
.site-header { border-bottom: 1px solid #e7e5e4; background: var(--card); }
.site-header .inner { max-width: 960px; margin: 0 auto; padding: 28px 24px; }
.site-title { font-size: 24px; font-weight: 800; letter-spacing: 0.02em; }
.site-title a { color: var(--ink); text-decoration: none; }
.site-title .bolt { color: var(--accent); }
.site-tagline { color: var(--muted); font-size: 13px; margin-top: 4px; }
main { max-width: 960px; margin: 0 auto; padding: 40px 24px 80px; }
/* index */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }
.card {
  background: var(--card); border: 1px solid #e7e5e4; border-radius: 12px; overflow: hidden;
  text-decoration: none; color: var(--ink); display: flex; flex-direction: column;
  transition: transform .15s ease, box-shadow .15s ease;
}
.card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.08); }
.card-thumb { aspect-ratio: 3 / 2; object-fit: cover; width: 100%; display: block; }
.card-thumb-placeholder {
  aspect-ratio: 3 / 2; display: flex; align-items: center; justify-content: center;
  font-size: 42px; color: #fff;
  background: linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 55%, #1a1a1a));
}
.card-body { padding: 16px 18px 20px; display: flex; flex-direction: column; gap: 8px; }
.card-title { font-size: 16px; font-weight: 700; line-height: 1.5; }
.card-desc { font-size: 13px; color: var(--muted); line-height: 1.7; }
.card-meta { font-size: 12px; color: var(--muted); margin-top: auto; }
.empty-state { text-align: center; color: var(--muted); padding: 80px 0; }
/* article */
.article { background: var(--card); border: 1px solid #e7e5e4; border-radius: 12px; overflow: hidden; }
.article-eyecatch { width: 100%; display: block; }
.article-inner { max-width: 720px; margin: 0 auto; padding: 40px 28px 64px; }
.article h1 { font-size: 28px; line-height: 1.5; margin-bottom: 12px; }
.article-meta { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
.tag { display: inline-block; font-size: 11px; color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
  border-radius: 99px; padding: 1px 10px; margin-right: 6px; }
.article-body { margin-top: 32px; }
.article-body h2 {
  font-size: 21px; margin: 48px 0 16px; padding-left: 12px;
  border-left: 4px solid var(--accent); line-height: 1.5;
}
.article-body h3 { font-size: 17px; margin: 36px 0 12px; }
.article-body p { margin: 0 0 1.4em; }
.article-body ul, .article-body ol { margin: 0 0 1.4em; padding-left: 1.6em; }
.article-body li { margin-bottom: .4em; }
.article-body figure { margin: 28px 0; }
.article-body img { max-width: 100%; border-radius: 8px; }
.article-body blockquote {
  border-left: 3px solid #d6d3d1; color: var(--muted);
  padding: 4px 0 4px 16px; margin: 0 0 1.4em;
}
.article-body pre {
  background: #1c1917; color: #e7e5e4; border-radius: 8px;
  padding: 16px; overflow-x: auto; font-size: 13px; margin: 0 0 1.4em;
}
.article-body code { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: .9em; }
.article-body p code, .article-body li code { background: #f5f5f4; padding: 1px 6px; border-radius: 4px; }
.article-body hr { border: none; border-top: 1px solid #e7e5e4; margin: 40px 0; }
.back-link { display: inline-block; margin-bottom: 20px; font-size: 14px; text-decoration: none; }
.site-footer { text-align: center; color: var(--muted); font-size: 12px; padding: 32px 0 48px; }
@media (max-width: 600px) {
  .article h1 { font-size: 22px; }
  .article-inner { padding: 28px 20px 48px; }
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
    <div class="site-title"><a href="__HOME_PATH__"><span class="bolt">⚡</span> __MEDIA_NAME__</a></div>
    <div class="site-tagline">__TAGLINE__</div>
  </div>
</header>
<main>
__CONTENT__
</main>
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
        .replace("__TAGLINE__", htmlmod.escape(config.get("tagline", "")))
        .replace("__CONTENT__", content)
    )


# ---------------------------------------------------------------- build

def main() -> None:
    if not CONFIG_PATH.exists():
        print("config エラー: lightin.config.json がありません。先にオンボーディングを実行してください。")
        sys.exit(1)
    config = json.loads(CONFIG_PATH.read_text())
    accent = config.get("design", {}).get("accentColor", "#2563eb")

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
        tags_html = "".join(f'<span class="tag">{htmlmod.escape(t)}</span>' for t in tags)
        eyecatch_html = (
            f'<img class="article-eyecatch" src="../{a["eyecatch_rel"]}" alt="">'
            if a["eyecatch_rel"] else ""
        )
        content = f"""\
<article class="article">
{eyecatch_html}
<div class="article-inner">
<a class="back-link" href="../index.html">← 記事一覧へ</a>
<div class="article-meta">{htmlmod.escape(meta["date"])}</div>
<h1>{htmlmod.escape(meta["title"])}</h1>
<div>{tags_html}</div>
<div class="article-body">
{body_html}
</div>
</div>
</article>"""
        page = render_page(
            content, title=f'{meta["title"]} | {config["mediaName"]}',
            description=meta["description"], config=config, depth=1,
        )
        (SITE_DIR / "articles" / f"{a['slug']}.html").write_text(page)

    # index
    if articles:
        cards = []
        for a in articles:
            meta = a["meta"]
            thumb = (
                f'<img class="card-thumb" src="{a["eyecatch_rel"]}" alt="" loading="lazy">'
                if a["eyecatch_rel"]
                else '<div class="card-thumb-placeholder">⚡</div>'
            )
            cards.append(f"""\
<a class="card" href="articles/{a['slug']}.html">
{thumb}
<div class="card-body">
<div class="card-title">{htmlmod.escape(meta["title"])}</div>
<div class="card-desc">{htmlmod.escape(meta["description"])}</div>
<div class="card-meta">{htmlmod.escape(meta["date"])}</div>
</div>
</a>""")
        index_content = '<div class="card-grid">\n' + "\n".join(cards) + "\n</div>"
    else:
        index_content = '<div class="empty-state">まだ記事がありません。ライティンに「◯◯について記事書いて」と頼んでみよう ⚡</div>'

    index_page = render_page(
        index_content, title=config["mediaName"],
        description=config.get("tagline", ""), config=config, depth=0,
    )
    (SITE_DIR / "index.html").write_text(index_page)

    print(f"✅ ビルド完了: 記事 {len(articles)} 本 → site/index.html")
    for s in skipped:
        print(f"⚠️  スキップ: {s}")


if __name__ == "__main__":
    main()
