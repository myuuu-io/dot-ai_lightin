#!/usr/bin/env bash
# ⚡ Lightin インストーラー
# 使い方: curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/lightin/main/install.sh | bash
set -euo pipefail

# ===== 設定 =====
REPO="myuuu-io/dot-ai_lightin"
BRANCH="main"
TARGET_DIR="${1:-lightin}"
# ====================================================

YELLOW='\033[1;33m'
CYAN='\033[1;36m'
DIM='\033[2m'
BOLD='\033[1m'
RESET='\033[0m'

echo ""
echo -e "${YELLOW}"
cat <<'LOGO'
   __    ____  ___  _   _  ____  ____  _  _
  (  )  (_  _)/ __)( )_( )(_  _)(_  _)( \( )
   )(__  _)(_( (_-. ) _ (   )(   _)(_  )  (
  (____)(____)\___/(_) (_) (__) (____)(_)\_)
                                      ⚡⚡⚡
LOGO
echo -e "${RESET}"
sleep 0.3
echo -e "  ${BOLD}やあ、僕はライティン⚡${RESET}"
sleep 0.4
echo -e "  Web を調べて記事を書いて、君だけのオウンドメディアを作る専属ライターだよ。"
sleep 0.4
echo ""
echo -e "  ${DIM}インストールを始めるね...${RESET}"
echo ""

# ---- 前提チェック ----
fail() { echo -e "  ❌ $1" >&2; exit 1; }

command -v python3 >/dev/null 2>&1 || fail "Python 3 が必要です (macOS は標準搭載のはず)"
command -v curl    >/dev/null 2>&1 || fail "curl が必要です"
command -v tar     >/dev/null 2>&1 || fail "tar が必要です"
[ -e "$TARGET_DIR" ] && fail "「$TARGET_DIR」がすでに存在します。別の場所で実行するか、フォルダ名を指定してください: install.sh my-media"

if ! command -v claude >/dev/null 2>&1; then
  echo -e "  ⚠️  ${BOLD}Claude Code が見つかりません${RESET}"
  echo -e "     先にインストールしてね → ${CYAN}https://claude.com/claude-code${RESET}"
  echo -e "     (このまま続行はします)"
  echo ""
fi

# ---- ダウンロード & 展開 ----
echo -e "  📦 ダウンロード中..."
TMP_TAR="$(mktemp -t lightin.XXXXXX).tar.gz"
curl -fsSL "https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz" -o "$TMP_TAR" \
  || fail "ダウンロードに失敗しました (https://github.com/${REPO})"

mkdir -p "$TARGET_DIR"
tar -xzf "$TMP_TAR" -C "$TARGET_DIR" --strip-components=1
rm -f "$TMP_TAR"

# ---- 初期セットアップ ----
cd "$TARGET_DIR"
[ -f .env.local ] || cp .env.example .env.local
mkdir -p content/articles content/images content/research settings

echo -e "  ✅ ${BOLD}${TARGET_DIR}/${RESET} に展開したよ！"
echo ""
sleep 0.4

# ---- ようこそ ----
echo -e "${YELLOW}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "  ${BOLD}あとはこれをコピペするだけ:${RESET}"
echo ""
echo -e "  ${CYAN}cd ${TARGET_DIR} && claude \"よろしく！\"${RESET}"
echo ""
echo -e "  ${DIM}「よろしく！」が届いた瞬間に僕が挨拶して、ヒアリングを始めるよ。${RESET}"
echo -e "  ${DIM}(claude だけで起動した場合は、何か一言話しかけてくれれば始まるよ)${RESET}"
echo ""
echo -e "  ${DIM}アイキャッチ画像も自動生成したい場合だけ .env.local に OPENAI_API_KEY を設定してね${RESET}"
echo ""
echo -e "  メディア名・テーマ・僕の人格・トンマナを一緒に決めて、"
echo -e "  そのまま最初の 1 ページを作っちゃおう。"
echo ""
echo -e "  ${BOLD}それじゃ、待ってるね⚡${RESET}"
echo ""
