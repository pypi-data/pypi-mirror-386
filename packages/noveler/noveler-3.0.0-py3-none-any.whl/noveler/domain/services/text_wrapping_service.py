"""Domain.services.text_wrapping_service
Where: Domain service module providing reusable business logic.
What: Houses service routines and helpers implemented in this module.
Why: Makes this service behaviour accessible to application workflows.
"""

from __future__ import annotations


def wrap_japanese_line(text: str, max_width: int) -> str:
    """日本語行の安全な位置での折り返し。

    - max_width を中心に直近の読点/句点/閉括弧などで改行
    - 近傍に適切な区切りが無い場合は固定長で分割
    - 前後の余分な空白は適度に調整
    """
    if len(text) <= max_width:
        return text
    result: list[str] = []
    rest = text
    break_chars = "、。，．？！）」』]〉》】＞」\n"
    while len(rest) > max_width:
        found = -1
        # 後方探索（max_widthの手前〜20文字）
        for i in range(min(max_width, len(rest)) - 1, max(-1, max_width - 20), -1):
            if rest[i] in break_chars:
                found = i + 1
                break
        # 前方探索（max_width〜+20文字）
        if found == -1:
            for i in range(max_width, min(len(rest), max_width + 20)):
                if rest[i] in break_chars:
                    found = i + 1
                    break
        if found == -1:
            found = max_width
        result.append(rest[:found].rstrip())
        rest = rest[found:].lstrip()
    if rest:
        result.append(rest)
    return "\n".join(result)
