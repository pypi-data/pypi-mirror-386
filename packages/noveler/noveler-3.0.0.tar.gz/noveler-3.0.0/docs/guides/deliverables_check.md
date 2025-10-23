# 成果物チェック（DeliverableCheckService）

- 目的: 実ファイルとYAML記録の整合を確認し、進捗レポートを生成。
- パス解決: 固定パスではなく `IPathService` による動的解決へ移行。
  - plot_outline: `get_episode_plot_path()` → 無ければ `get_plots_dir()/第NNN話_*.yaml`
  - character_sheet: `get_character_settings_file()` → 無ければ `get_settings_dir()/キャラクター.yaml`
  - world_setting: `get_settings_dir()/世界観.yaml`
  - draft_manuscript: `get_manuscript_dir()/第NNN話_*.md`
  - quality_check: `get_quality_record_file()` → 無ければ管理直下の既定
  - access_analysis: `get_management_dir()/アクセス分析.yaml`
- 互換: 既存のキー名（plot_outline 等）は維持。
