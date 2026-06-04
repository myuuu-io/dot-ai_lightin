# ⚡ Lightin (ライティン)

**Web を検索して記事を書き、画像つきオウンドメディアとして公開してくれる Claude Code エージェント。**

```
　 ／＼
　＜ ⚡ ＞   やあ、僕はライティン！
　 ＼／　   君のメディアの専属ライターだよ
```

## インストール

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/lightin/main/install.sh | bash
```

その後:

```bash
cd lightin
cp .env.example .env.local   # キーを設定 (JINA_API_KEY 推奨 / OPENAI_API_KEY 任意)
claude
```

初回起動でライティンが挨拶し、ヒアリングが始まります。
メディア名・テーマ・読者像・人格・トンマナを答えると、君だけのメディアがセットアップされます。

## 使い方

セットアップ後、Claude Code でこう話しかけるだけ:

> フリーランスのインボイス対応について記事を書いて

ライティンが **検索 → 執筆 → アイキャッチ生成 → HTML 公開** まで一気にやって、ブラウザで記事を開いてくれます。

## 必要なもの

| もの | 必須 | 備考 |
|---|---|---|
| [Claude Code](https://claude.com/claude-code) | ✅ | |
| Python 3.9+ | ✅ | macOS は標準搭載 |
| `JINA_API_KEY` | 推奨 | [無料発行](https://jina.ai/api-dashboard/)。無くても動くがレート制限あり |
| `OPENAI_API_KEY` | 任意 | アイキャッチ生成用。無ければ画像なしで公開 |

## 仕組み

```
あなた「◯◯について記事書いて」
   │
   ├─ 1. lightin-researcher  … Jina Reader で Web 検索・ソース収集
   ├─ 2. lightin-writer      … 設定した人格で記事執筆
   ├─ 3. lightin-illustrator … gpt-image でアイキャッチ生成
   └─ 4. lightin-builder     … 静的 HTML サイト生成 → ブラウザで表示
```

- 記事は `content/articles/*.md`、サイトは `site/` に生成 (ビルドツール不要・依存ゼロ)
- サブエージェントは `.claude/agents/`、手順は `.claude/skills/` にすべて入っています
- DB・外部サービス通知なし。すべてローカル完結
