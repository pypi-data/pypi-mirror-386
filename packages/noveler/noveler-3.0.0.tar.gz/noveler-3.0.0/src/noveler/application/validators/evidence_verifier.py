#!/usr/bin/env python3
"""エビデンス検証ユーティリティ（B20準拠）

LLMが返す evidence [{element, quote, start, end}] の妥当性を、
原稿本文に対する一致検証でチェックする軽量バリデータ。

設計方針:
- まず厳密一致（start/end範囲の一致→quote一致→全文検索）
- フォールバックとして軽い正規化（空白・改行除去）一致
- 重い外部依存（ベクトル・形態素）は使用しない（最小差分）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EvidenceItem:
    """LLMが返すevidence項目の内部表現。"""

    element: str | None
    quote: str
    start: int | None = None
    end: int | None = None


@dataclass
class EvidenceVerificationResult:
    """検証結果（合計・一致件数・詳細）。"""

    total: int
    verified: int
    details: list[dict[str, Any]]

    def ratio(self) -> float:
        if self.total <= 0:
            return 0.0
        return self.verified / self.total


class EvidenceVerifier:
    """エビデンス検証器。本文に対する位置/引用の一致を確認する。"""

    def verify(self, manuscript: str, evidence_list: list[dict[str, Any]]) -> EvidenceVerificationResult:
        items = [self._to_item(ev) for ev in (evidence_list or [])]
        verified = 0
        details: list[dict[str, Any]] = []

        for item in items:
            ok, method = self._verify_one(manuscript, item)
            if ok:
                verified += 1
            details.append(
                {
                    "element": item.element,
                    "quote": item.quote,
                    "start": item.start,
                    "end": item.end,
                    "verified": ok,
                    "method": method,
                }
            )

        return EvidenceVerificationResult(total=len(items), verified=verified, details=details)

    def _to_item(self, ev: dict[str, Any]) -> EvidenceItem:
        element = ev.get("element") if isinstance(ev, dict) else None
        quote = (ev.get("quote") or "") if isinstance(ev, dict) else ""
        try:
            start = int(ev.get("start")) if ev.get("start") is not None else None
        except Exception:
            start = None
        try:
            end = int(ev.get("end")) if ev.get("end") is not None else None
        except Exception:
            end = None
        return EvidenceItem(element=element, quote=str(quote), start=start, end=end)

    def _verify_one(self, manuscript: str, item: EvidenceItem) -> tuple[bool, str]:
        # 厳密: start/end 指定あり → 部分文字列一致
        if item.start is not None and item.end is not None:
            try:
                if 0 <= item.start <= item.end <= len(manuscript):
                    segment = manuscript[item.start : item.end]
                    if segment == item.quote and segment != "":
                        return True, "position_exact"
            except Exception:
                # 想定外の範囲・型エラーなどは一致なしとして継続
                return False, "range_error"

        # 厳密: quote の全文検索
        if item.quote and item.quote in manuscript:
            return True, "quote_exact"

        # フォールバック: ホワイトスペース正規化
        if item.quote:
            norm_quote = self._normalize(item.quote)
            norm_manuscript = self._normalize(manuscript)
            if norm_quote and norm_quote in norm_manuscript:
                return True, "quote_normalized"

        return False, "no_match"

    def _normalize(self, s: str) -> str:
        # 空白・改行・全角/半角スペースなどの簡易除去
        return "".join(ch for ch in s if not ch.isspace())
