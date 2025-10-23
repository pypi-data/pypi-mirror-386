#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python標準のlen()関数による日本語文字数カウントの検証
"""

def test_len_function():
    """len()関数の動作確認テスト"""
    test_cases = [
        # (テキスト, 期待される文字数, 説明)
        ("こんにちは", 5, "ひらがな5文字"),
        ("日本語", 3, "漢字3文字"),
        ("Hello", 5, "英字5文字"),
        ("😀😃😄", 3, "絵文字3文字"),
        ("日本語ABC", 6, "日本語と英字の混在6文字"),
        ("改行\nあり", 5, "改行を含む5文字"),
        ("タブ\tあり", 5, "タブを含む5文字"),
        ("　全角スペース　", 7, "全角スペース含む7文字"),
        (" 半角スペース ", 7, "半角スペース含む7文字"),
        ("「鍵括弧」", 5, "記号を含む5文字"),
        ("……", 2, "三点リーダー2文字"),
        ("――", 2, "ダッシュ2文字"),
        ("", 0, "空文字列"),
    ]

    print("=" * 60)
    print("Python len()関数による文字数カウントテスト")
    print("=" * 60)

    all_passed = True
    for text, expected, description in test_cases:
        actual = len(text)
        passed = actual == expected
        status = "✅ OK" if passed else f"❌ NG (期待値: {expected})"

        # 見やすく表示
        display_text = repr(text) if text else "''"
        print(f"\n{description}:")
        print(f"  テキスト: {display_text}")
        print(f"  len()結果: {actual} 文字")
        print(f"  判定: {status}")

        if not passed:
            all_passed = False
            # バイト数も参考表示
            byte_count = len(text.encode('utf-8'))
            print(f"  参考: UTF-8バイト数 = {byte_count}")

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ すべてのテストが成功しました！")
        print("→ Python標準のlen()関数は日本語文字を正しくカウントしています。")
    else:
        print("❌ 一部のテストが失敗しました。")
    print("=" * 60)

    return all_passed


def compare_with_bytes():
    """文字数とバイト数の比較"""
    print("\n" + "=" * 60)
    print("文字数 vs バイト数の比較")
    print("=" * 60)

    samples = [
        "Hello",      # ASCII文字のみ
        "こんにちは",  # 日本語のみ
        "日本語ABC",   # 混在
        "😀😃😄",     # 絵文字
    ]

    for text in samples:
        char_count = len(text)
        byte_count_utf8 = len(text.encode('utf-8'))
        byte_count_sjis = len(text.encode('shift_jis', errors='ignore'))

        print(f"\nテキスト: '{text}'")
        print(f"  文字数 (len): {char_count}")
        print(f"  UTF-8バイト数: {byte_count_utf8}")
        print(f"  Shift-JISバイト数: {byte_count_sjis}")
        print(f"  → 比率 (UTF-8/文字数): {byte_count_utf8/char_count:.1f}")


if __name__ == "__main__":
    # メインテスト実行
    test_passed = test_len_function()

    # 追加の比較情報
    compare_with_bytes()

    # 結論
    print("\n" + "=" * 60)
    print("【結論】")
    print("Python 3のlen()関数は、Unicode文字列の")
    print("「文字数」を正しくカウントします。")
    print("これは日本語、絵文字、その他のマルチバイト文字でも")
    print("正しく動作します。")
    print("\nもし文字数カウントに問題がある場合は、")
    print("len()関数以外の箇所に原因がある可能性が高いです。")
    print("=" * 60)
