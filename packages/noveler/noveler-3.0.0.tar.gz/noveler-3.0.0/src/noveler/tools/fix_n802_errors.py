#!/usr/bin/env python3
"""N802 (invalid-function-name) エラーを修正するスクリプト

このスクリプトは以下の修正を行います:
    1. CamelCase関数名をsnake_caseに変換
2. 日本語を含む関数名を英語に翻訳
3. テストファイルの関数名を優先的に修正
"""

import re
from pathlib import Path
from typing import Any

class N802Fixer:
    """N802エラー修正クラス"""

    def __init__(self, logger_service: Any | None = None, console_service: Any | None = None):
        self.japanese_translations = {
            # テスト関数名の翻訳マッピング
            "ドメインサービスerror_を適切にhandlingする": "handles_domain_service_errors_properly",
            "例外発生時のerror_ハンドリング": "handles_exceptions_on_error",
            "all_体構成creationの便利メソッド": "all_structure_creation_convenience_method",
            "章別プロットcreationの便利メソッド": "chapter_plot_creation_convenience_method",
            "episodes数別プロットcreationの便利メソッド": "episode_count_plot_creation_convenience_method",
            "前提条件ルールをcreationできる": "can_create_prerequisite_rules",
            "パラメータ付きpathを展開できる": "can_expand_parameterized_paths",
            "必須でない前提条件をcreationできる": "can_create_optional_prerequisites",
            "ワークフロー段階タイプをcreationできる": "can_create_workflow_stage_types",
            "all_ての段階タイプが定義されている": "all_stage_types_are_defined",
            "getOr": "get_or",
            "findBy": "find_by",
            "getAll": "get_all",
            "getValue": "get_value",
            "setValue": "set_value",
            "toString": "to_string",
            "fromString": "from_string",
            "isValid": "is_valid",
            "isEmpty": "is_empty",
            "hasValue": "has_value",
            "clearAll": "clear_all",
            "updateAll": "update_all",
            "deleteAll": "delete_all",
            "createNew": "create_new",
            "getDefault": "get_default",
            "setDefault": "set_default",
            "resetAll": "reset_all",
            "loadData": "load_data",
            "saveData": "save_data",
            "parseData": "parse_data",
            "formatData": "format_data",
            "validateData": "validate_data",
            "processData": "process_data",
            "convertData": "convert_data",
            "mergeData": "merge_data",
            "splitData": "split_data",
            "filterData": "filter_data",
            "sortData": "sort_data",
            "groupData": "group_data",
            "mapData": "map_data",
            "reduceData": "reduce_data",
            "calculateTotal": "calculate_total",
            "generateReport": "generate_report",
            "exportReport": "export_report",
            "importReport": "import_report",
            "analyzeResults": "analyze_results",
            "summarizeResults": "summarize_results",
            "displayResults": "display_results",
            "checkStatus": "check_status",
            "updateStatus": "update_status",
            "resetStatus": "reset_status",
            "getStatus": "get_status",
            "setStatus": "set_status",
            "handleError": "handle_error",
            "logError": "log_error",
            "raiseError": "raise_error",
            "catchError": "catch_error",
            "throwError": "throw_error",
            "initializeSystem": "initialize_system",
            "shutdownSystem": "shutdown_system",
            "restartSystem": "restart_system",
            "configureSystem": "configure_system",
            "startProcess": "start_process",
            "stopProcess": "stop_process",
            "pauseProcess": "pause_process",
            "resumeProcess": "resume_process",
            "executeCommand": "execute_command",
            "runCommand": "run_command",
            "callFunction": "call_function",
            "invokeMethod": "invoke_method",
            "dispatchEvent": "dispatch_event",
            "handleEvent": "handle_event",
            "listenEvent": "listen_event",
            "triggerEvent": "trigger_event",
            "emitEvent": "emit_event",
            "connectDatabase": "connect_database",
            "disconnectDatabase": "disconnect_database",
            "queryDatabase": "query_database",
            "updateDatabase": "update_database",
            "authenticateUser": "authenticate_user",
            "authorizeUser": "authorize_user",
            "validateUser": "validate_user",
            "createUser": "create_user",
            "updateUser": "update_user",
            "deleteUser": "delete_user",
            "getUserInfo": "get_user_info",
            "setUserInfo": "set_user_info",
            "sendMessage": "send_message",
            "receiveMessage": "receive_message",
            "processMessage": "process_message",
            "queueMessage": "queue_message",
            "broadcastMessage": "broadcast_message",
            "encryptData": "encrypt_data",
            "decryptData": "decrypt_data",
            "hashData": "hash_data",
            "verifyData": "verify_data",
            "signData": "sign_data",
            "openFile": "open_file",
            "closeFile": "close_file",
            "readFile": "read_file",
            "writeFile": "write_file",
            "deleteFile": "delete_file",
            "copyFile": "copy_file",
            "moveFile": "move_file",
            "renameFile": "rename_file",
            "createDirectory": "create_directory",
            "deleteDirectory": "delete_directory",
            "listDirectory": "list_directory",
            "watchDirectory": "watch_directory",
            "uploadFile": "upload_file",
            "downloadFile": "download_file",
            "compressFile": "compress_file",
            "extractFile": "extract_file",
            "searchText": "search_text",
            "replaceText": "replace_text",
            "matchPattern": "match_pattern",
            "validatePattern": "validate_pattern",
            "parseJSON": "parse_json",
            "stringifyJSON": "stringify_json",
            "validateJSON": "validate_json",
            "mergeJSON": "merge_json",
            "parseXML": "parse_xml",
            "validateXML": "validate_xml",
            "transformXML": "transform_xml",
            "parseYAML": "parse_yaml",
            "validateYAML": "validate_yaml",
            "mergeYAML": "merge_yaml",
            "parseCSV": "parse_csv",
            "writeCSV": "write_csv",
            "validateCSV": "validate_csv",
            "convertCSV": "convert_csv",
            "buildQuery": "build_query",
            "executeQuery": "execute_query",
            "prepareStatement": "prepare_statement",
            "bindParameters": "bind_parameters",
            "fetchResults": "fetch_results",
            "commitTransaction": "commit_transaction",
            "rollbackTransaction": "rollback_transaction",
            "beginTransaction": "begin_transaction",
            "lockResource": "lock_resource",
            "unlockResource": "unlock_resource",
            "allocateMemory": "allocate_memory",
            "freeMemory": "free_memory",
            "monitorPerformance": "monitor_performance",
            "optimizePerformance": "optimize_performance",
            "profileCode": "profile_code",
            "debugCode": "debug_code",
            "testCode": "test_code",
            "deployCode": "deploy_code",
            "buildProject": "build_project",
            "compileCode": "compile_code",
            "linkLibraries": "link_libraries",
            "packageApplication": "package_application",
            "publishPackage": "publish_package",
            "installDependencies": "install_dependencies",
            "updateDependencies": "update_dependencies",
            "checkDependencies": "check_dependencies",
            "resolveDependencies": "resolve_dependencies",
            "generateDocumentation": "generate_documentation",
            "updateDocumentation": "update_documentation",
            "publishDocumentation": "publish_documentation",
            "validateDocumentation": "validate_documentation",
            "scheduleTask": "schedule_task",
            "cancelTask": "cancel_task",
            "executeTask": "execute_task",
            "queueTask": "queue_task",
            "prioritizeTask": "prioritize_task",
            "createBackup": "create_backup",
            "restoreBackup": "restore_backup",
            "verifyBackup": "verify_backup",
            "scheduleBackup": "schedule_backup",
            "cleanupBackup": "cleanup_backup",
            "monitorHealth": "monitor_health",
            "checkHealth": "check_health",
            "reportHealth": "report_health",
            "alertHealth": "alert_health",
            "createMetrics": "create_metrics",
            "collectMetrics": "collect_metrics",
            "reportMetrics": "report_metrics",
            "analyzeMetrics": "analyze_metrics",
            "visualizeMetrics": "visualize_metrics",
            "exportMetrics": "export_metrics",
            "validateInput": "validate_input",
            "sanitizeInput": "sanitize_input",
            "escapeInput": "escape_input",
            "filterInput": "filter_input",
            "formatOutput": "format_output",
            "renderOutput": "render_output",
            "streamOutput": "stream_output",
            "bufferOutput": "buffer_output",
            "flushOutput": "flush_output",
            "closeOutput": "close_output",
            "createSession": "create_session",
            "destroySession": "destroy_session",
            "saveSession": "save_session",
            "loadSession": "load_session",
            "validateSession": "validate_session",
            "refreshSession": "refresh_session",
            "expireSession": "expire_session",
            "createCache": "create_cache",
            "clearCache": "clear_cache",
            "invalidateCache": "invalidate_cache",
            "warmCache": "warm_cache",
            "checkCache": "check_cache",
            "updateCache": "update_cache",
            "createToken": "create_token",
            "validateToken": "validate_token",
            "refreshToken": "refresh_token",
            "revokeToken": "revoke_token",
            "decodeToken": "decode_token",
            "encodeToken": "encode_token",
            "createWebhook": "create_webhook",
            "triggerWebhook": "trigger_webhook",
            "validateWebhook": "validate_webhook",
            "processWebhook": "process_webhook",
            "retryWebhook": "retry_webhook",
            "logWebhook": "log_webhook",
            "createNotification": "create_notification",
            "sendNotification": "send_notification",
            "queueNotification": "queue_notification",
            "retryNotification": "retry_notification",
            "dismissNotification": "dismiss_notification",
            "markAsRead": "mark_as_read",
            "markAsUnread": "mark_as_unread",
            "createAlert": "create_alert",
            "triggerAlert": "trigger_alert",
            "acknowledgeAlert": "acknowledge_alert",
            "escalateAlert": "escalate_alert",
            "resolveAlert": "resolve_alert",
            "suppressAlert": "suppress_alert",
            "createWorkflow": "create_workflow",
            "startWorkflow": "start_workflow",
            "pauseWorkflow": "pause_workflow",
            "resumeWorkflow": "resume_workflow",
            "cancelWorkflow": "cancel_workflow",
            "completeWorkflow": "complete_workflow",
            "validateWorkflow": "validate_workflow",
            "createPipeline": "create_pipeline",
            "executePipeline": "execute_pipeline",
            "validatePipeline": "validate_pipeline",
            "monitorPipeline": "monitor_pipeline",
            "optimizePipeline": "optimize_pipeline",
            "debugPipeline": "debug_pipeline",
            "createTemplate": "create_template",
            "renderTemplate": "render_template",
            "validateTemplate": "validate_template",
            "compileTemplate": "compile_template",
            "cacheTemplate": "cache_template",
            "loadTemplate": "load_template",
            "createSchema": "create_schema",
            "validateSchema": "validate_schema",
            "migrateSchema": "migrate_schema",
            "exportSchema": "export_schema",
            "importSchema": "import_schema",
            "compareSchema": "compare_schema",
            "createIndex": "create_index",
            "dropIndex": "drop_index",
            "rebuildIndex": "rebuild_index",
            "optimizeIndex": "optimize_index",
            "searchIndex": "search_index",
            "updateIndex": "update_index",
            "createRule": "create_rule",
            "evaluateRule": "evaluate_rule",
            "validateRule": "validate_rule",
            "executeRule": "execute_rule",
            "disableRule": "disable_rule",
            "enableRule": "enable_rule",
            "createPolicy": "create_policy",
            "enforcePolicy": "enforce_policy",
            "validatePolicy": "validate_policy",
            "updatePolicy": "update_policy",
            "deletePolicy": "delete_policy",
            "auditPolicy": "audit_policy",
            "createJob": "create_job",
            "scheduleJob": "schedule_job",
            "executeJob": "execute_job",
            "cancelJob": "cancel_job",
            "retryJob": "retry_job",
            "monitorJob": "monitor_job",
            "createQueue": "create_queue",
            "pushQueue": "push_queue",
            "popQueue": "pop_queue",
            "peekQueue": "peek_queue",
            "purgeQueue": "purge_queue",
            "monitorQueue": "monitor_queue",
            "createStream": "create_stream",
            "writeStream": "write_stream",
            "readStream": "read_stream",
            "closeStream": "close_stream",
            "flushStream": "flush_stream",
            "pipeStream": "pipe_stream",
            "createBuffer": "create_buffer",
            "writeBuffer": "write_buffer",
            "readBuffer": "read_buffer",
            "clearBuffer": "clear_buffer",
            "resizeBuffer": "resize_buffer",
            "copyBuffer": "copy_buffer",
            "createPool": "create_pool",
            "acquirePool": "acquire_pool",
            "releasePool": "release_pool",
            "drainPool": "drain_pool",
            "resizePool": "resize_pool",
            "monitorPool": "monitor_pool",
            "createCluster": "create_cluster",
            "joinCluster": "join_cluster",
            "leaveCluster": "leave_cluster",
            "monitorCluster": "monitor_cluster",
            "scaleCluster": "scale_cluster",
            "balanceCluster": "balance_cluster",
            "createBatch": "create_batch",
            "processBatch": "process_batch",
            "validateBatch": "validate_batch",
            "retryBatch": "retry_batch",
            "completeBatch": "complete_batch",
            "rollbackBatch": "rollback_batch",
            "createContext": "create_context",
            "enterContext": "enter_context",
            "exitContext": "exit_context",
            "switchContext": "switch_context",
            "saveContext": "save_context",
            "restoreContext": "restore_context",
            "createState": "create_state",
            "setState": "set_state",
            "getState": "get_state",
            "resetState": "reset_state",
            "saveState": "save_state",
            "loadState": "load_state",
            "createEvent": "create_event",
            "fireEvent": "fire_event",
            "handleEvent": "handle_event",
            "queueEvent": "queue_event",
            "cancelEvent": "cancel_event",
            "replayEvent": "replay_event",
            "createHandler": "create_handler",
            "registerHandler": "register_handler",
            "unregisterHandler": "unregister_handler",
            "invokeHandler": "invoke_handler",
            "wrapHandler": "wrap_handler",
            "chainHandler": "chain_handler",
            "createMiddleware": "create_middleware",
            "useMiddleware": "use_middleware",
            "applyMiddleware": "apply_middleware",
            "skipMiddleware": "skip_middleware",
            "composeMiddleware": "compose_middleware",
            "orderMiddleware": "order_middleware",
            "createFilter": "create_filter",
            "applyFilter": "apply_filter",
            "removeFilter": "remove_filter",
            "chainFilter": "chain_filter",
            "composeFilter": "compose_filter",
            "bypassFilter": "bypass_filter",
            "createValidator": "create_validator",
            "runValidator": "run_validator",
            "chainValidator": "chain_validator",
            "skipValidator": "skip_validator",
            "customValidator": "custom_validator",
            "asyncValidator": "async_validator",
            "createTransformer": "create_transformer",
            "applyTransformer": "apply_transformer",
            "chainTransformer": "chain_transformer",
            "reverseTransformer": "reverse_transformer",
            "composeTransformer": "compose_transformer",
            "cacheTransformer": "cache_transformer",
            "createSerializer": "create_serializer",
            "runSerializer": "run_serializer",
            "customSerializer": "custom_serializer",
            "binarySerializer": "binary_serializer",
            "jsonSerializer": "json_serializer",
            "xmlSerializer": "xml_serializer",
            "createDeserializer": "create_deserializer",
            "runDeserializer": "run_deserializer",
            "customDeserializer": "custom_deserializer",
            "safeDeserializer": "safe_deserializer",
            "strictDeserializer": "strict_deserializer",
            "lazyDeserializer": "lazy_deserializer",
            "createEncoder": "create_encoder",
            "runEncoder": "run_encoder",
            "base64Encoder": "base64_encoder",
            "urlEncoder": "url_encoder",
            "htmlEncoder": "html_encoder",
            "customEncoder": "custom_encoder",
            "createDecoder": "create_decoder",
            "runDecoder": "run_decoder",
            "base64Decoder": "base64_decoder",
            "urlDecoder": "url_decoder",
            "htmlDecoder": "html_decoder",
            "customDecoder": "custom_decoder",
            "createCompressor": "create_compressor",
            "runCompressor": "run_compressor",
            "gzipCompressor": "gzip_compressor",
            "zipCompressor": "zip_compressor",
            "customCompressor": "custom_compressor",
            "streamCompressor": "stream_compressor",
            "createDecompressor": "create_decompressor",
            "runDecompressor": "run_decompressor",
            "gzipDecompressor": "gzip_decompressor",
            "zipDecompressor": "zip_decompressor",
            "customDecompressor": "custom_decompressor",
            "streamDecompressor": "stream_decompressor",
            "createLogger": "create_logger",
            "getLogger": "get_logger",
            "configureLogger": "configure_logger",
            "rotateLogger": "rotate_logger",
            "flushLogger": "flush_logger",
            "closeLogger": "close_logger",
            "createFormatter": "create_formatter",
            "applyFormatter": "apply_formatter",
            "customFormatter": "custom_formatter",
            "dateFormatter": "date_formatter",
            "numberFormatter": "number_formatter",
            "stringFormatter": "string_formatter",
            "createParser": "create_parser",
            "runParser": "run_parser",
            "configParser": "config_parser",
            "argParser": "arg_parser",
            "jsonParser": "json_parser",
            "xmlParser": "xml_parser",
            "createBuilder": "create_builder",
            "runBuilder": "run_builder",
            "configBuilder": "config_builder",
            "queryBuilder": "query_builder",
            "formBuilder": "form_builder",
            "pageBuilder": "page_builder",
            "createFactory": "create_factory",
            "getFactory": "get_factory",
            "registerFactory": "register_factory",
            "abstractFactory": "abstract_factory",
            "singletonFactory": "singleton_factory",
            "prototypeFactory": "prototype_factory",
            "createAdapter": "create_adapter",
            "registerAdapter": "register_adapter",
            "getAdapter": "get_adapter",
            "chainAdapter": "chain_adapter",
            "fallbackAdapter": "fallback_adapter",
            "cacheAdapter": "cache_adapter",
            "createObserver": "create_observer",
            "attachObserver": "attach_observer",
            "detachObserver": "detach_observer",
            "notifyObserver": "notify_observer",
            "updateObserver": "update_observer",
            "clearObserver": "clear_observer",
            "createIterator": "create_iterator",
            "nextIterator": "next_iterator",
            "hasNextIterator": "has_next_iterator",
            "resetIterator": "reset_iterator",
            "currentIterator": "current_iterator",
            "countIterator": "count_iterator",
            "createDecorator": "create_decorator",
            "applyDecorator": "apply_decorator",
            "chainDecorator": "chain_decorator",
            "removeDecorator": "remove_decorator",
            "stackDecorator": "stack_decorator",
            "cacheDecorator": "cache_decorator",
            "createProxy": "create_proxy",
            "getProxy": "get_proxy",
            "invokeProxy": "invoke_proxy",
            "cacheProxy": "cache_proxy",
            "lazyProxy": "lazy_proxy",
            "protectionProxy": "protection_proxy",
            "createFacade": "create_facade",
            "getFacade": "get_facade",
            "registerFacade": "register_facade",
            "simplifyFacade": "simplify_facade",
            "wrapFacade": "wrap_facade",
            "exposeFacade": "expose_facade",
            "createCommand": "create_command",
            "executeCommand": "execute_command",
            "undoCommand": "undo_command",
            "redoCommand": "redo_command",
            "queueCommand": "queue_command",
            "macroCommand": "macro_command",
            "createStrategy": "create_strategy",
            "setStrategy": "set_strategy",
            "executeStrategy": "execute_strategy",
            "switchStrategy": "switch_strategy",
            "fallbackStrategy": "fallback_strategy",
            "chainStrategy": "chain_strategy",
            "createVisitor": "create_visitor",
            "acceptVisitor": "accept_visitor",
            "visitElement": "visit_element",
            "traverseTree": "traverse_tree",
            "walkStructure": "walk_structure",
            "processNodes": "process_nodes",
            "createMemento": "create_memento",
            "saveMemento": "save_memento",
            "restoreMemento": "restore_memento",
            "undoMemento": "undo_memento",
            "redoMemento": "redo_memento",
            "historyMemento": "history_memento",
            "createMediator": "create_mediator",
            "registerMediator": "register_mediator",
            "notifyMediator": "notify_mediator",
            "handleMediator": "handle_mediator",
            "routeMediator": "route_mediator",
            "unregisterMediator": "unregister_mediator",
            "createChain": "create_chain",
            "addChain": "add_chain",
            "removeChain": "remove_chain",
            "processChain": "process_chain",
            "breakChain": "break_chain",
            "continueChain": "continue_chain",
            "createInterpreter": "create_interpreter",
            "parseExpression": "parse_expression",
            "evaluateExpression": "evaluate_expression",
            "compileExpression": "compile_expression",
            "optimizeExpression": "optimize_expression",
            "cacheExpression": "cache_expression",
            "createPrototype": "create_prototype",
            "clonePrototype": "clone_prototype",
            "registerPrototype": "register_prototype",
            "getPrototype": "get_prototype",
            "removePrototype": "remove_prototype",
            "updatePrototype": "update_prototype",
            "createSingleton": "create_singleton",
            "getInstance": "get_instance",
            "resetInstance": "reset_instance",
            "hasInstance": "has_instance",
            "clearInstance": "clear_instance",
            "lockInstance": "lock_instance",
            "createFlyweight": "create_flyweight",
            "getFlyweight": "get_flyweight",
            "shareFlyweight": "share_flyweight",
            "unshareFlyweight": "unshare_flyweight",
            "countFlyweight": "count_flyweight",
            "clearFlyweight": "clear_flyweight",
            "createBridge": "create_bridge",
            "setBridge": "set_bridge",
            "crossBridge": "cross_bridge",
            "connectBridge": "connect_bridge",
            "disconnectBridge": "disconnect_bridge",
            "rebuildBridge": "rebuild_bridge",
            "createComposite": "create_composite",
            "addComposite": "add_composite",
            "removeComposite": "remove_composite",
            "getComposite": "get_composite",
            "countComposite": "count_composite",
            "traverseComposite": "traverse_composite",
            "createTemplate": "create_template",
            "defineTemplate": "define_template",
            "executeTemplate": "execute_template",
            "overrideTemplate": "override_template",
            "extendTemplate": "extend_template",
            "finalizeTemplate": "finalize_template"
        }
        self.fixed_count = 0
        self.total_errors = 0

        self.logger_service = logger_service
        self.console_service = console_service
    def camel_to_snake(self, name: str) -> str:
        """CamelCaseをsnake_caseに変換"""
        # 連続する大文字の前に_を挿入(最後の大文字の前)
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        # 小文字の後の大文字の前に_を挿入
        s2 = re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1)
        return s2.lower()

    def fix_function_name(self, name: str) -> str:
        """関数名を修正"""
        # 既に正しい形式の場合はそのまま返す
        if name.islower() or re.match(r"^[a-z_][a-z0-9_]*$", name):
            return name

        # まず日本語を含む場合は翻訳マッピングを使用
        original_name = name
        for jp_name, en_name in self.japanese_translations.items():
            if jp_name in name:
                name = name.replace(jp_name, en_name)

        # 日本語が残っている場合は一般的な置換を行う
        if re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", name):
            # よくあるパターンの置換
            name = name.replace("ドメインサービス", "domain_service")
            name = name.replace("ハンドリング", "handling")
            name = name.replace("エラー", "error")
            name = name.replace("例外発生時", "on_exception")
            name = name.replace("便利メソッド", "convenience_method")
            name = name.replace("章別プロット", "chapter_plot")
            name = name.replace("話数別プロット", "episode_plot")
            name = name.replace("体構成", "structure")
            name = name.replace("前提条件", "prerequisite")
            name = name.replace("ルール", "rules")
            name = name.replace("パラメータ付き", "parameterized")
            name = name.replace("を展開", "_expand")
            name = name.replace("必須でない", "optional")
            name = name.replace("ワークフロー", "workflow")
            name = name.replace("段階タイプ", "stage_types")
            name = name.replace("段階", "stage")
            name = name.replace("タイプ", "types")
            name = name.replace("の順序", "_order")
            name = name.replace("前提条件check", "prerequisite_check")
            name = name.replace("既に存在する", "already_exists")
            name = name.replace("を使った", "with")
            name = name.replace("プロット", "plot")
            name = name.replace("タスク", "task")
            name = name.replace("完all_な", "complete")
            name = name.replace("失敗state", "failure_state")
            name = name.replace("特定段階", "specific_stage")
            name = name.replace("前段階", "previous_stage")
            name = name.replace("未complete", "incomplete")
            name = name.replace("進捗", "progress")
            name = name.replace("前提条件不足時", "when_prerequisites_missing")
            name = name.replace("拒否する", "reject")
            name = name.replace("既存ファイル衝突時", "on_file_conflict")
            name = name.replace("verificationを求める", "requires_verification")
            name = name.replace("テンプレートを使って", "using_template")
            name = name.replace("カスタマイズされた", "customized")
            name = name.replace("完all_", "complete_")
            name = name.replace("all_", "all_")
            name = name.replace("をcreationできる", "_can_be_created")
            name = name.replace("をcreation", "_creation")
            name = name.replace("をgetできる", "_can_be_retrieved")
            name = name.replace("ができる", "_is_possible")
            name = name.replace("かcheckできる", "_can_be_checked")
            name = name.replace("をexecutionstartできる", "_can_start_execution")
            name = name.replace("をcompleteできる", "_can_be_completed")
            name = name.replace("にできる", "_can_be_set_to")
            name = name.replace("をgenerationできる", "_can_be_generated")
            name = name.replace("できる", "_possible")
            name = name.replace("する", "")
            name = name.replace("が定義されている", "_are_defined")
            name = name.replace("は", "_")
            name = name.replace("の場合", "_case")
            name = name.replace("できない", "_not_possible")
            name = name.replace("_を", "_")
            name = name.replace("を_", "_")
            name = name.replace("を", "_")
            name = name.replace("が", "_")
            name = name.replace("に", "_")
            name = name.replace("で", "_")
            name = name.replace("と", "_")
            name = name.replace("から", "_from_")
            name = name.replace("へ", "_to_")
            name = name.replace("より", "_than_")
            name = name.replace("ての", "_all_")

            # 残った日本語文字を削除
            name = re.sub(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+", "", name)

            # 連続するアンダースコアを1つに
            name = re.sub(r"_+", "_", name)

            # 先頭と末尾のアンダースコアを削除
            name = name.strip("_")

        # CamelCaseをsnake_caseに変換
        name = self.camel_to_snake(name)

        # 最終的なクリーンアップ
        name = re.sub(r"_+", "_", name)  # 連続するアンダースコアを1つに
        name = name.strip("_")  # 先頭と末尾のアンダースコアを削除

        # 空文字列になった場合はデフォルト名を返す
        if not name:
            return "unnamed_function"

        return name

    def process_file(self, file_path: Path) -> list[tuple[str, str]]:
        """ファイルを処理してN802エラーを修正"""
        changes = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines(keepends=True)

            # 関数定義を探して修正
            for i, line in enumerate(lines):
                # 関数定義のパターン(日本語文字も含む)
                # より広範なパターンでマッチ
                match = re.match(r"^(\s*)(async\s+)?def\s+([^\s(]+)\s*\(", line)
                if match:
                    indent = match.group(1)
                    async_keyword = match.group(2) or ""
                    old_name = match.group(3)
                    new_name = self.fix_function_name(old_name)

                    if old_name != new_name:
                        # 関数定義行を置換
                        new_line = line.replace(f"def {old_name}(", f"def {new_name}(")
                        if async_keyword:
                            new_line = new_line.replace(f"async def {old_name}(", f"async def {new_name}(")
                        lines[i] = new_line
                        changes.append((old_name, new_name))

                        # ファイル全体で関数呼び出しも置換
                        for j, other_line in enumerate(lines):
                            if i != j:  # 定義行以外:
                                # self.old_name( または old_name( のパターンを置換
                                # エスケープを適切に処理
                                try:
                                    escaped_old = re.escape(old_name)
                                    lines[j] = re.sub(
                                        rf"\b{escaped_old}\s*\(",
                                        f"{new_name}(",
                                        lines[j])

                                except re.error:
                                    # 正規表現エラーの場合は単純な文字列置換
                                    lines[j] = lines[j].replace(f"{old_name}(", f"{new_name}(")

            if changes:
                # ファイルを書き戻す
                file_path.write_text("".join(lines), encoding="utf-8")

        except Exception as e:
            self.console_service.print(f"Error processing {file_path}: {e}")

        return changes

    def run(self):
        """メイン処理を実行"""
        scripts_dir = Path("/mnt/c/Users/bamboocity/OneDrive/Documents/9_小説/00_ガイド/scripts")

        # まずN802エラーの総数をカウント
        self.console_service.print("N802エラーをスキャン中...")
        result = subprocess.run(
            ["ruff", "check", str(scripts_dir), "--select", "N802"],
            check=False, capture_output=True,
            text=True)

        # エラーを解析
        error_files = {}
        for line in result.stdout.strip().split("\n"):
            if line and "N802" in line:
                self.total_errors += 1
                file_path = line.split(":")[0]
                if file_path not in error_files:
                    error_files[file_path] = []
                error_files[file_path].append(line)

        self.console_service.print(f"検出されたN802エラー: {self.total_errors}件")
        self.console_service.print(f"影響を受けるファイル: {len(error_files)}個")
        self.console_service.print()

        # 各ファイルを処理
        for file_path in error_files:
            path = Path(file_path)
            if path.exists():
                self.console_service.print(f"処理中: {path}")
                changes = self.process_file(path)
                if changes:
                    self.fixed_count += len(changes)
                    for old_name, new_name in changes:
                        self.console_service.print(f"  修正: {old_name} → {new_name}")

        # 結果を表示
        self.console_service.print()
        self.console_service.print("=" * 60)
        self.console_service.print("修正完了!")
        self.console_service.print(f"総エラー数: {self.total_errors}")
        self.console_service.print(f"修正済み: {self.fixed_count}")
        self.console_service.print(f"修正率: {self.fixed_count / self.total_errors * 100:.1f}%" if self.total_errors > 0 else "N/A")

        # 残りのエラーを確認
        self.console_service.print("\n残りのエラーを確認中...")
        result = subprocess.run(
            ["ruff", "check", str(scripts_dir), "--select", "N802", "--statistics"],
            check=False, capture_output=True,
            text=True)

        remaining_count = 0
        for line in result.stdout.strip().split("\n"):
            if line and "N802" in line:
                parts = line.split()
                if parts and parts[0].isdigit():
                    remaining_count = int(parts[0])

        self.console_service.print(f"残りのN802エラー: {remaining_count}件")
        self.console_service.print(f"削減率: {(self.total_errors - remaining_count) / self.total_errors * 100:.1f}%" if self.total_errors > 0 else "N/A")

if __name__ == "__main__":
    import subprocess

    fixer = N802Fixer()
    fixer.run()
