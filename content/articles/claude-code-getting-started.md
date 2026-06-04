---
title: Claude Codeの使い方。最初の30分でやることを全部まとめた
date: 2026-06-04
description: インストール1行から、最初にやるべき設定3つまで。毎日Claude Codeで仕事をしている僕が、入門でつまずくポイントを順番に整理しました。
eyecatch: /images/claude-code-getting-started/eyecatch.png
tags: [ClaudeCode, AI活用, 開発効率化]
---

「AIにコードを書かせる」と聞くと、チャット画面にコードを貼り付けて、返ってきた答えをまたコピペする姿を想像しませんか。僕も最初はそうでした。でも Claude Code を使い始めてから、その往復がまるごと消えたんです。

この記事では、毎日 Claude Code で仕事をしている僕が、インストールから「最初にやっておくと快適になる設定」までを順番にまとめます。所要時間はだいたい 30 分。読み終わる頃には、ターミナルで AI と一緒に開発できる状態になっているはずです。

## Claude Codeとは何か

Claude Code は、Anthropic が開発した AI コーディングアシスタントです。チャット型の AI と決定的に違うのは、あなたのプロジェクトフォルダの中で動くこと。コードベース全体を読んで構造を理解した上で、複数のファイルをまたいで編集したり、コマンドを実行したりしてくれます。

例えるなら、チャット AI が「電話越しに相談できる先輩」だとしたら、Claude Code は「隣の席に座って、実際に手を動かしてくれる同僚」です。

動く場所はターミナルだけではありません。VS Code や JetBrains の拡張、デスクトップアプリ、ブラウザ版もあり、設定ファイル（CLAUDE.md）は全部の環境で共通で使えます。まずはターミナル版から入るのが一番シンプルなので、この記事もそれを前提にします。

## 料金: Freeプランでは使えない

ここ、最初に知っておいてほしいポイントです。Claude 自体には無料プランがありますが、**Claude Code を動かすには Pro 以上のサブスクリプションか、Anthropic Console のアカウントが必要**です（2026 年 6 月時点）。

個人で始めるなら月額 20 ドルの Pro プランが定番です。定額の利用枠の中で使う仕組みなので、意図しない追加課金が発生しないのが安心材料。逆に、API の従量課金で直接使う方法は、エージェントがコードを何度も読み込む性質上、初心者だと思ったよりコストが膨らみがちです。最初はサブスクリプションをおすすめします。

## インストールは1行で終わる

macOS / Linux / WSL なら、ターミナルでこれを実行するだけです。

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

これが公式推奨の「ネイティブインストール」で、自動更新も付いてきます。Homebrew 派なら `brew install --cask claude-code`、Windows なら PowerShell で `irm https://claude.ai/install.ps1 | iex` でも入ります。

インストールが終わったら、動作確認を兼ねてこれを打っておきましょう。

```bash
claude doctor
```

環境の問題をまとめて診断してくれるコマンドです。あとで何かつまずいたときも、まずこれを実行すると原因が見つかることが多いです。

## 最初の起動と /init

使い方は拍子抜けするほど簡単で、作業したいプロジェクトに移動して起動するだけです。

```bash
cd your-project
claude
```

初回はログインを求められるので、ブラウザで Claude のアカウントを連携します。続けて「このフォルダのファイルを信頼しますか？」という確認が出るので、自分のプロジェクトであれば Yes で進みます。

起動できたら、最初にやってほしいのがこれです。

```
/init
```

Claude がコードベースを読み取って、CLAUDE.md というルールファイルを自動生成してくれます。これはプロジェクトの「取扱説明書」のようなもので、以降の会話で Claude が前提として読んでくれます。技術スタックやコーディング規約をここに育てていくと、指示の精度が目に見えて上がります。

## 最初にやっておくと快適になる設定

デフォルトの Claude Code は安全側に倒してあって、いろいろな操作のたびに確認を求めてきます。安全なのは良いことなんですが、正直、毎回 Yes を押すのは疲れます。そこで設定ファイル（`~/.claude/settings.json`）を少しだけ調整します。

まずはパーミッションの最小構成から。

```json
{
  "permissions": {
    "allow": ["WebFetch", "WebSearch"],
    "deny": ["Read(./.env)", "Read(./.env.*)", "Edit(./.env)"]
  }
}
```

allow で Web 検索系の確認をスキップしつつ、deny で `.env`（API キーなどの機密ファイル）を読ませない、という構成です。パーミッションは deny → ask → allow の順で評価されるので、deny に書いたものは何があっても拒否されます。機密ファイルの deny は最初に入れておくのが鉄則です。

もうひとつのおすすめは完了通知です。長いタスクを任せて別の作業をしていると、終わったことに気づかないんですよね。Stop Hook を設定すると、処理が終わった瞬間に音で知らせてくれます。macOS ならこうです。

```json
{
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command", "command": "afplay /System/Library/Sounds/Glass.aiff" }] }]
  }
}
```

地味な設定ですが、僕はこれを入れてから「AI の作業待ちでぼーっとする時間」がなくなりました。

## まとめ

- Claude Code は「プロジェクトの中で手を動かしてくれる」AI アシスタント
- 利用には Pro プラン（月額 20 ドル〜）以上が必要。Free プランでは動かない
- インストールは `curl -fsSL https://claude.ai/install.sh | bash` の 1 行
- 起動したらまず `/init` で CLAUDE.md を作る
- パーミッション（特に `.env` の deny）と完了通知だけ先に設定しておくと快適

次にやることはひとつだけ。手元の小さなプロジェクトで `claude` と打って、「このコードを説明して」と話しかけてみてください。最初のひと往復で、たぶん想像が変わります。

## 参考にした情報

- [Overview - Claude Code Docs（Anthropic 公式）](https://docs.anthropic.com/en/docs/claude-code/overview)
- [Claude Code入門 #1: インストールから使える初期設定まで（Qiita）](https://qiita.com/dai_chi/items/6fec068d23caadea53df)
- [Claude Codeとは？料金と使い方、できること、注意点を整理（HP Tech&Device TV）](https://jp.ext.hp.com/techdevice/ai/ai_explained_60/)
- [私のシンプルなClaude Codeの使い方（note）](https://note.com/nike_cha_n/n/nee3503e7a617)
