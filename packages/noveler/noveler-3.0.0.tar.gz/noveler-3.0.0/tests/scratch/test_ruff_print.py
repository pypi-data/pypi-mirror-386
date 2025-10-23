#!/usr/bin/env python3
"""print()テスト用ファイル"""

def bad_function():
    print("これはRuffで警告されるべきprint()です")
    message = "Bad practice"
    print(message)
    print(f"Format: {message}")

def good_function():
    from noveler.presentation.cli.shared_utilities import console
    console.print("これは適切なconsole.print()です")

if __name__ == "__main__":
    bad_function()
    good_function()
