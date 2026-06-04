#!/usr/bin/env python3
"""gpt-image で記事用画像を生成する。依存ゼロ (Python 標準ライブラリのみ)。

使い方:
  python3 generate_image.py --output content/images/slug/eyecatch.png --prompt "..."
  python3 generate_image.py --output ... --prompt "..." --reference 前回のeyecatch.png

参照画像なし → /v1/images/generations
参照画像あり → /v1/images/edits (スタイル引き継ぎ)
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "gpt-image-2"


def load_api_key() -> str:
    """OPENAI_API_KEY を取得。優先順位: 環境変数 → ./.env.local → ./.env → ~/.env.local → ~/.env"""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    candidates = [
        Path(".env.local"),
        Path(".env"),
        Path.home() / ".env.local",
        Path.home() / ".env",
    ]
    for env_path in candidates:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                if k.strip() == "OPENAI_API_KEY" and v.strip():
                    return v.strip().strip('"').strip("'")
    print(
        "SKIP: OPENAI_API_KEY が見つかりません (.env.local に設定すると画像が生成できます)",
        file=sys.stderr,
    )
    sys.exit(2)  # exit 2 = キー未設定 (エラーではなくスキップ扱い)


def build_multipart(fields: dict, files: list) -> tuple[bytes, str]:
    boundary = "----LightinBoundary" + base64.b64encode(os.urandom(16)).decode().rstrip("=")
    body = b""
    for name, value in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += f"{value}\r\n".encode()
    for name, filepath in files:
        filename = Path(filepath).name
        ctype = mimetypes.guess_type(filename)[0] or "image/png"
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {ctype}\r\n\r\n".encode()
        body += Path(filepath).read_bytes()
        body += b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def request_image(api_key: str, prompt: str, references: list, size: str, quality: str) -> dict:
    if references:
        # edits: 参照画像のスタイルを引き継ぐ
        fields = {"model": MODEL, "prompt": prompt, "size": size, "quality": quality, "n": "1"}
        files = [("image[]", r) for r in references]
        body, content_type = build_multipart(fields, files)
        url = "https://api.openai.com/v1/images/edits"
    else:
        body = json.dumps(
            {"model": MODEL, "prompt": prompt, "size": size, "quality": quality, "n": 1}
        ).encode()
        content_type = "application/json"
        url = "https://api.openai.com/v1/images/generations"

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": content_type},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt", "-p", required=True, help="画像生成プロンプト")
    p.add_argument("--output", "-o", required=True, help="出力 PNG パス")
    p.add_argument(
        "--reference", "-r", action="append", default=[],
        help="参照画像 (任意・複数可)。渡すとスタイルを引き継ぐ",
    )
    p.add_argument("--size", "-s", default="1536x1024", help="画像サイズ (デフォルト: 1536x1024)")
    p.add_argument("--quality", "-q", default="high", choices=["low", "medium", "high"])
    args = p.parse_args()

    api_key = load_api_key()
    references = [r for r in args.reference if Path(r).exists()]

    try:
        data = request_image(api_key, args.prompt, references, args.size, args.quality)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(1)

    item = data["data"][0]
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    if item.get("b64_json"):
        Path(args.output).write_bytes(base64.b64decode(item["b64_json"]))
    else:
        Path(args.output).write_bytes(urllib.request.urlopen(item["url"], timeout=120).read())
    print(f"画像を保存しました: {args.output}")


if __name__ == "__main__":
    main()
