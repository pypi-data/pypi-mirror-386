@echo off
REM E2Eテスト実行バッチファイル (Windows)
REM 使用方法: bin\run_e2e_tests.bat [オプション]

setlocal enabledelayedexpansion

REM デフォルト設定
set "RUN_ALL=false"
set "RUN_WORKFLOW=false"
set "RUN_QUALITY=false"
set "RUN_SMOKE=false"
set "INCLUDE_PERFORMANCE=false"
set "FAST_MODE=false"
set "VERBOSE=false"
set "DEBUG=false"
set "GENERATE_REPORT=false"
set "TIMEOUT=300"

REM カラー定義（Windows 10以降）
set "ESC="
set "RED=%ESC%[31m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "BLUE=%ESC%[34m"
set "NC=%ESC%[0m"

REM ログ関数
:log
echo %BLUE%[%date% %time%] %~1%NC%
goto :eof

:warn
echo %YELLOW%[WARNING] %~1%NC%
goto :eof

:error
echo %RED%[ERROR] %~1%NC%
exit /b 1

:success
echo %GREEN%[SUCCESS] %~1%NC%
goto :eof

REM ヘルプ表示
:show_help
echo E2Eテスト実行バッチファイル (Windows^)
echo.
echo 使用方法:
echo     bin\run_e2e_tests.bat [オプション]
echo.
echo オプション:
echo     -h, --help              このヘルプを表示
echo     -a, --all               全てのE2Eテストを実行
echo     -w, --workflow          ワークフロー統合テストのみ実行
echo     -q, --quality           品質保証ワークフローのみ実行
echo     -s, --smoke             スモークテスト（基本機能）のみ実行
echo     -p, --performance       パフォーマンステストを含む
echo     -f, --fast              高速実行（slow テストをスキップ）
echo     -v, --verbose           詳細出力
echo     -d, --debug             デバッグモード
echo     -r, --report            HTML レポート生成
echo.
echo 実行例:
echo     bin\run_e2e_tests.bat --smoke                    # スモークテストのみ
echo     bin\run_e2e_tests.bat --workflow --verbose       # ワークフロー統合テスト
echo     bin\run_e2e_tests.bat --all --report             # 全テスト + HTML レポート
echo.
goto :eof

REM 引数解析
:parse_args
if "%~1"=="" goto :args_done
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
if "%~1"=="-a" set "RUN_ALL=true"
if "%~1"=="--all" set "RUN_ALL=true"
if "%~1"=="-w" set "RUN_WORKFLOW=true"
if "%~1"=="--workflow" set "RUN_WORKFLOW=true"
if "%~1"=="-q" set "RUN_QUALITY=true"
if "%~1"=="--quality" set "RUN_QUALITY=true"
if "%~1"=="-s" set "RUN_SMOKE=true"
if "%~1"=="--smoke" set "RUN_SMOKE=true"
if "%~1"=="-p" set "INCLUDE_PERFORMANCE=true"
if "%~1"=="--performance" set "INCLUDE_PERFORMANCE=true"
if "%~1"=="-f" set "FAST_MODE=true"
if "%~1"=="--fast" set "FAST_MODE=true"
if "%~1"=="-v" set "VERBOSE=true"
if "%~1"=="--verbose" set "VERBOSE=true"
if "%~1"=="-d" set "DEBUG=true" & set "VERBOSE=true"
if "%~1"=="--debug" set "DEBUG=true" & set "VERBOSE=true"
if "%~1"=="-r" set "GENERATE_REPORT=true"
if "%~1"=="--report" set "GENERATE_REPORT=true"
shift
goto :parse_args

:args_done

REM プロジェクトルートに移動
cd /d "%~dp0\.."

REM 環境チェック
call :log "E2E テスト環境の確認"

REM Python仮想環境の確認
if not defined VIRTUAL_ENV (
    call :warn "仮想環境が有効化されていません"
    if exist "venv\Scripts\activate.bat" (
        call :log "venv を有効化中..."
        call venv\Scripts\activate.bat
    ) else if exist ".venv\Scripts\activate.bat" (
        call :log ".venv を有効化中..."
        call .venv\Scripts\activate.bat
    ) else (
        call :warn "仮想環境が見つかりません。グローバル環境で実行します"
    )
)

REM 必要なディレクトリ作成
if not exist "temp\cache\pytest_e2e" mkdir "temp\cache\pytest_e2e"
if not exist "temp\reports" mkdir "temp\reports"
if not exist "temp\logs" mkdir "temp\logs"

REM pytest の確認
pytest --version >nul 2>&1
if errorlevel 1 (
    call :error "pytest がインストールされていません"
    goto :eof
)

python --version
pytest --version

REM pytest引数の構築
set "PYTEST_ARGS=-c tests\e2e\pytest_e2e.ini"

REM マーカー設定
set "MARKERS="

if "%RUN_ALL%"=="true" (
    call :log "全E2Eテストを実行"
) else if "%RUN_SMOKE%"=="true" (
    call :log "スモークテストを実行"
    set "MARKERS=smoke"
) else (
    if "%RUN_WORKFLOW%"=="true" (
        call :log "ワークフロー統合テストを実行"
        set "MARKERS=workflow"
    )

    if "%RUN_QUALITY%"=="true" (
        call :log "品質保証ワークフローテストを実行"
        if defined MARKERS (
            set "MARKERS=!MARKERS! or quality"
        ) else (
            set "MARKERS=quality"
        )
    )

    REM デフォルト
    if not defined MARKERS (
        call :log "基本E2Eテストを実行"
        set "MARKERS=e2e"
    )
)

REM パフォーマンステスト
if "%INCLUDE_PERFORMANCE%"=="true" (
    call :log "パフォーマンステストを含む"
    if defined MARKERS (
        set "MARKERS=!MARKERS! or performance"
    ) else (
        set "MARKERS=performance"
    )
)

REM 高速モード
if "%FAST_MODE%"=="true" (
    call :log "高速モード: 時間のかかるテストをスキップ"
    set "PYTEST_ARGS=!PYTEST_ARGS! -m \"not slow\""
) else if defined MARKERS (
    set "PYTEST_ARGS=!PYTEST_ARGS! -m \"!MARKERS!\""
)

REM 詳細出力
if "%VERBOSE%"=="true" (
    set "PYTEST_ARGS=!PYTEST_ARGS! -vv"
    call :log "詳細出力モード"
)

REM デバッグモード
if "%DEBUG%"=="true" (
    set "PYTEST_ARGS=!PYTEST_ARGS! --tb=long --showlocals --capture=no"
    call :log "デバッグモード"
)

REM タイムアウト
set "PYTEST_ARGS=!PYTEST_ARGS! --timeout=!TIMEOUT!"

REM レポート生成
if "%GENERATE_REPORT%"=="true" (
    for /f "tokens=1-4 delims=/: " %%a in ("%date% %time%") do (
        set "TIMESTAMP=%%c%%a%%b_%%d"
    )
    set "TIMESTAMP=!TIMESTAMP: =!"
    set "REPORT_FILE=temp\reports\e2e_report_!TIMESTAMP!.html"
    set "PYTEST_ARGS=!PYTEST_ARGS! --html=!REPORT_FILE! --self-contained-html"
    call :log "HTMLレポート: !REPORT_FILE!"
)

REM ログファイル
for /f "tokens=1-4 delims=/: " %%a in ("%date% %time%") do (
    set "LOG_TIMESTAMP=%%c%%a%%b_%%d"
)
set "LOG_TIMESTAMP=!LOG_TIMESTAMP: =!"
set "LOG_FILE=temp\logs\e2e_test_!LOG_TIMESTAMP!.log"
set "PYTEST_ARGS=!PYTEST_ARGS! --log-file=!LOG_FILE!"

REM 実行開始
call :log "E2Eテスト実行開始"
call :log "実行コマンド: pytest !PYTEST_ARGS!"
call :log "ログファイル: !LOG_FILE!"

set "START_TIME=%time%"

REM pytest実行
pytest %PYTEST_ARGS%
if errorlevel 1 (
    call :error "E2Eテスト失敗"
    goto :eof
) else (
    call :success "E2Eテスト完了"
)

REM 結果サマリー
echo.
call :log "=== 実行結果サマリー ==="
if defined REPORT_FILE if exist "!REPORT_FILE!" (
    call :log "HTMLレポート: !REPORT_FILE!"
)
call :log "詳細ログ: !LOG_FILE!"

endlocal
goto :eof
