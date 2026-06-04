---
name: site-builder
description: content/articles/*.md から静的 HTML サイト (site/) をフル再生成する手順。Python 標準ライブラリのみで動き、ビルドツール不要。
---

# サイトビルダー (静的 HTML)

## 実行

```bash
python3 .claude/skills/site-builder/scripts/build_site.py
```

これだけ。`lightin.config.json` と `content/` を読んで `site/` を**毎回フル再生成**する。

## 何が生成されるか

```
site/
├── index.html          # 記事カード一覧 (日付降順)
├── style.css           # トンマナ (accentColor) を反映した共通 CSS
├── articles/{slug}.html
└── images/             # content/images/ のコピー
```

- ブラウザで `open site/index.html` するだけで閲覧できる (サーバー不要、file:// で完結)
- アイキャッチ画像が無い記事は ⚡ 入りのグラデーションプレースホルダーになる

## 記事 Markdown の前提

- `content/articles/{slug}.md`、frontmatter に `title` / `date` / `description` (必須)、`eyecatch` / `tags` (任意)
- 本文画像のパスは `/images/{slug}/xxx.png` 形式 (ビルダーが相対パスに変換する)
- frontmatter が壊れている記事はスキップされ、警告が stdout に出る → writer に修正を依頼する

## トラブルシュート

- `config エラー`: `lightin.config.json` が無い → オンボーディング未完了。先にオンボーディングを実行
- 記事がスキップされた: 警告に出た frontmatter のキー欠落を直す
