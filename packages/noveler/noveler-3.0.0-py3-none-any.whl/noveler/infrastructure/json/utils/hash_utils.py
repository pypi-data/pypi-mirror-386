#!/usr/bin/env python3
"""ハッシュユーティリティ"""

import hashlib
import re
from pathlib import Path


def calculate_sha256(file_path: str | Path) -> str:
    """SHA256ハッシュ計算（最適化版）"""
    file_path = Path(file_path)

    if not file_path.exists():
        msg = f"ファイルが存在しません: {file_path}"
        raise FileNotFoundError(msg)

    sha256_hash = hashlib.sha256()
    chunk_size = 65536  # 64KB

    try:
        with file_path.open("rb") as f:
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)
    except OSError as e:
        msg = f"ファイル読み込みエラー: {file_path}"
        raise OSError(msg) from e

    return sha256_hash.hexdigest()


def calculate_sha256_from_content(content: str, encoding: str = "utf-8") -> str:
    """コンテンツ文字列からSHA256ハッシュ計算"""
    content_bytes = content.encode(encoding)
    return hashlib.sha256(content_bytes).hexdigest()


def verify_hash_format(hash_value: str) -> bool:
    """SHA256ハッシュ形式検証"""
    return bool(re.match(r"^[a-f0-9]{64}$", hash_value.lower()))
