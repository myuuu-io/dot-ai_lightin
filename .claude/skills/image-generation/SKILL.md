---
name: image-generation
description: gpt-image でアイキャッチ画像を生成する手順。参照画像を渡してメディア全体のトンマナを統一する。OPENAI_API_KEY 未設定なら静かにスキップ。
---

# 画像生成 (gpt-image)

## 前提チェック

```bash
grep -s '^OPENAI_API_KEY=.' .env.local .env || echo "NO_KEY"
```

`NO_KEY` なら**エラーにせず**「画像生成はスキップ (キー未設定)」と報告して終了する。
その場合、記事 frontmatter の `eyecatch:` 行は writer がそのまま残してよい (ビルダーがファイル不在を検知してプレースホルダーにする)。

## 生成コマンド

```bash
python3 .claude/skills/image-generation/scripts/generate_image.py \
  --output "content/images/{slug}/eyecatch.png" \
  --prompt "(下記プロンプト)" \
  --reference "content/images/{前回のslug}/eyecatch.png"   # 任意: トンマナ統一用
```

- `--reference` 無し → 通常生成 / 有り → 参照画像のスタイルを引き継いで生成
- サイズはデフォルト 1536x1024 (アイキャッチに最適)。変更不要

## プロンプトの組み立て

必ずこの 3 要素を含める:

1. **画風** — `settings/lightin.config.json` の `imageStyle` をそのまま使う
2. **主題** — 記事タイトルを視覚的メタファーに翻訳する (抽象語のままにしない)
   - 例: 「インボイス対応」→「請求書と電卓を前に整理整頓するフリーランスのデスク」
3. **制約** — `No text in the image.` を基本とする。文字を入れる場合は 10 字以内の日本語 1 フレーズだけ指定し、生成後に誤字がないか目視確認する

例:

```
フラットイラスト、やわらかい配色、アクセントカラー #2563eb。
請求書と電卓を前に作業するフリーランスのデスクを俯瞰で。
余白を活かした構図。No text in the image.
```

## トンマナ統一の運用

- `content/images/` に過去のアイキャッチがあれば、**最新の 1 枚**を `--reference` に渡す
- これにより 2 枚目以降は自動的に画風が揃っていく (1 枚目がメディアのスタイルアンカーになる)
