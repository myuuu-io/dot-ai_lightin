---
name: web-research
description: Jina Reader (s.jina.ai / r.jina.ai) で Web 検索と本文取得を行う手順。記事のリサーチ・ファクトチェックに使う。
---

# Web リサーチ (Jina Reader)

## API キーの読み込み

`.env.local` → `.env` → 環境変数の順で `JINA_API_KEY` を探す:

```bash
JINA_API_KEY=$(grep -s '^JINA_API_KEY=' .env.local .env | head -1 | cut -d= -f2)
```

**検索 (s.jina.ai) はキー必須** (未設定だと 401 が返る)。本文取得 (r.jina.ai) はキー無しでも動くがレート制限が厳しい。

キーが無い場合: 検索はスキップし、ユーザーに「https://jina.ai/api-dashboard/ で無料発行して `.env.local` に設定してください」と案内する。テーマに関する公式サイト等の既知 URL があれば、それを直接 r.jina.ai で読んでリサーチを続行してよい。

## 1. 検索 (s.jina.ai) — キー必須

```bash
curl -s "https://s.jina.ai/?q=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "検索クエリ")" \
  -H "Authorization: Bearer $JINA_API_KEY" \
  -H "Accept: application/json" \
  -H "X-Respond-With: no-content"
```

- JSON で `data[].title / url / description` が返る
- 1 テーマにつき検索は 2〜3 クエリまで (言い換え・絞り込みで質を上げる)

## 2. 本文取得 (r.jina.ai) — キー無しでも可

検索結果から読む価値のある URL を選び、本文を Markdown で取得:

```bash
curl -s "https://r.jina.ai/https://example.com/page" \
  -H "Authorization: Bearer $JINA_API_KEY"
```

- 出力が長い場合は一時ファイルに保存してから Read で必要部分だけ読む:
  `curl -s ... -o /tmp/jina-{n}.md`

## ソースの信頼度判定

| 信頼度 | 例 |
|---|---|
| 高 | 政府・自治体 (go.jp / lg.jp)、企業公式、学術機関、一次統計 |
| 中 | 大手メディア、業界専門メディア、公式ブログ |
| 低 | まとめサイト、アフィリエイト記事、個人ブログ、Q&A サイト |

- 信頼度: 低のソースは「話題の発見」にのみ使い、事実の根拠にしない
- 日付の古い情報 (制度・価格・統計) は必ず最新ソースで再確認する

## マナー

- 同一ドメインへの連続アクセスは避ける
- 取得した本文の丸写しは禁止。要点を自分の言葉でノート化する
