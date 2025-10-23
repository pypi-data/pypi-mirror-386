"""Tests.test_migration_sample
Where: Test module used during migration demonstrations.
What: Provides sample test cases illustrating migration workflows.
Why: Ensures migration tooling is validated with representative tests.
"""

from noveler.presentation.shared.shared_utilities import console
'テスト用ファイル'

def test_function():
    console.print('これはprint()のテストです')
    message = 'Hello World'
    console.print(message)
    console.print(f'Format: {message}')
    console.print('これはconsole_service.print_()のテストです')
    console.print(f'Format: {message}')
if __name__ == '__main__':
    test_function()
