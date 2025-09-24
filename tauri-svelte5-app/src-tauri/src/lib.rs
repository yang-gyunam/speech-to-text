pub mod error;
pub mod models;
pub mod utils;
pub mod cli;
pub mod settings;
pub mod system;
pub mod macos_integration;
pub mod updater;

/// Global batch processing manager
static BATCH_MANAGER: once_cell::sync::Lazy<Arc<Mutex<BatchProcessingManager>>> = 
    once_cell::sync::Lazy::new(|| Arc::new(Mutex::new(BatchProcessingManager::new())));

/// Batch processing manager for handling concurrent jobs
pub struct BatchProcessingManager {
    active_jobs: HashMap<String, ProcessingJob>,
    job_handles: HashMap<String, tokio::task::JoinHandle<()>>,
    cancellation_tokens: HashMap<String, tokio_util::sync::CancellationToken>,
}

impl BatchProcessingManager {
    pub fn new() -> Self {
        Self {
            active_jobs: HashMap::new(),
            job_handles: HashMap::new(),
            cancellation_tokens: HashMap::new(),
        }
    }

    pub fn add_job(&mut self, job: ProcessingJob) {
        self.active_jobs.insert(job.id.clone(), job);
    }

    pub fn get_job(&self, job_id: &str) -> Option<&ProcessingJob> {
        self.active_jobs.get(job_id)
    }

    pub fn update_job_progress(&mut self, job_id: &str, progress: ProcessingProgress) {
        if let Some(job) = self.active_jobs.get_mut(job_id) {
            job.progress = progress.progress;
            job.stage = progress.stage;
        }
    }

    pub fn remove_job(&mut self, job_id: &str) {
        self.active_jobs.remove(job_id);
        if let Some(handle) = self.job_handles.remove(job_id) {
            handle.abort();
        }
        if let Some(token) = self.cancellation_tokens.remove(job_id) {
            token.cancel();
        }
    }

    pub fn cancel_job(&mut self, job_id: &str) -> bool {
        if let Some(job) = self.active_jobs.get_mut(job_id) {
            job.is_cancelled = true;
        }
        if let Some(token) = self.cancellation_tokens.get(job_id) {
            token.cancel();
            true
        } else {
            false
        }
    }

    pub fn add_cancellation_token(&mut self, job_id: String, token: tokio_util::sync::CancellationToken) {
        self.cancellation_tokens.insert(job_id, token);
    }

    pub fn add_job_handle(&mut self, job_id: String, handle: tokio::task::JoinHandle<()>) {
        self.job_handles.insert(job_id, handle);
    }

    pub fn get_active_jobs(&self) -> Vec<&ProcessingJob> {
        self.active_jobs.values().collect()
    }
}

use error::AppResult;
use models::{AppSettings, TranscriptionResult, AudioFile, ProcessingJob, ProcessingProgress, ProcessingStage};
use cli::{CliManager, CliResult};
use settings::SettingsManager;
use system::{SystemIntegration, FormatInfo, SystemInfo, SystemDependencyCheck};
use macos_integration::{MacOSIntegration, NotificationOptions, DockBadgeInfo, FileAssociationStatus};
use std::sync::Arc;
use tokio::sync::Mutex;
use std::collections::HashMap;
use chrono::Utc;
use tauri::Emitter;

/// Create CLI manager based on environment
fn create_cli_manager() -> CliManager {
    // Check if we're in development mode
    if cfg!(debug_assertions) {
        // Development mode - use development CLI paths
        CliManager::new_dev()
    } else {
        // Production mode - use sidecar
        CliManager::new()
    }
}

// Basic Tauri commands for initial setup
#[tauri::command]
async fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[tauri::command]
async fn get_supported_formats() -> Vec<String> {
    SystemIntegration::get_supported_formats()
}

#[tauri::command]
async fn get_supported_formats_detailed() -> Vec<FormatInfo> {
    SystemIntegration::get_supported_formats_detailed()
}

#[tauri::command]
async fn validate_audio_file(file_path: String) -> AppResult<models::AudioFile> {
    utils::create_audio_file(&file_path)
}

#[tauri::command]
async fn get_default_settings() -> AppSettings {
    AppSettings::default()
}

// Settings Management Commands
#[tauri::command]
async fn load_settings() -> AppResult<AppSettings> {
    let manager = SettingsManager::new()?;
    manager.load_settings().await
}

#[tauri::command]
async fn save_settings(settings: AppSettings) -> AppResult<()> {
    let manager = SettingsManager::new()?;
    manager.save_settings(&settings).await
}

#[tauri::command]
async fn update_settings_field(field: String, value: serde_json::Value) -> AppResult<AppSettings> {
    let manager = SettingsManager::new()?;
    
    manager.update_settings(|settings| {
        match field.as_str() {
            "language" => {
                if let Some(lang) = value.as_str() {
                    settings.language = lang.to_string();
                }
            }
            "model_size" => {
                if let Ok(model_size) = serde_json::from_value(value) {
                    settings.model_size = model_size;
                }
            }
            "output_directory" => {
                if let Some(dir) = value.as_str() {
                    settings.output_directory = dir.to_string();
                }
            }
            "include_metadata" => {
                if let Some(include) = value.as_bool() {
                    settings.include_metadata = include;
                }
            }
            "auto_save" => {
                if let Some(auto_save) = value.as_bool() {
                    settings.auto_save = auto_save;
                }
            }
            "theme" => {
                if let Ok(theme) = serde_json::from_value(value) {
                    settings.theme = theme;
                }
            }
            _ => {} // Ignore unknown fields
        }
    }).await
}

#[tauri::command]
async fn reset_settings_to_defaults() -> AppResult<AppSettings> {
    let manager = SettingsManager::new()?;
    manager.reset_to_defaults().await
}

#[tauri::command]
async fn validate_settings(settings: AppSettings) -> AppResult<bool> {
    let manager = SettingsManager::new()?;
    manager.validate_settings(&settings)?;
    Ok(true)
}

#[tauri::command]
async fn get_settings_config_path() -> AppResult<String> {
    let manager = SettingsManager::new()?;
    Ok(manager.get_config_path().to_string_lossy().to_string())
}

#[tauri::command]
async fn settings_config_exists() -> AppResult<bool> {
    let manager = SettingsManager::new()?;
    Ok(manager.config_exists())
}

#[tauri::command]
async fn export_settings_to_file(export_path: String) -> AppResult<()> {
    let manager = SettingsManager::new()?;
    manager.export_settings(&export_path).await
}

#[tauri::command]
async fn import_settings_from_file(import_path: String) -> AppResult<AppSettings> {
    let manager = SettingsManager::new()?;
    manager.import_settings(&import_path).await
}

// System Integration Commands
#[tauri::command]
async fn select_directory() -> AppResult<Option<String>> {
    SystemIntegration::select_directory().await
}

#[tauri::command]
async fn select_files(multiple: bool) -> AppResult<Vec<String>> {
    SystemIntegration::select_files(multiple).await
}

#[tauri::command]
async fn reveal_file_in_explorer(file_path: String) -> AppResult<()> {
    SystemIntegration::reveal_file_in_explorer(&file_path).await
}

#[tauri::command]
async fn open_file_with_default_app(file_path: String) -> AppResult<()> {
    SystemIntegration::open_file_with_default_app(&file_path).await
}

#[tauri::command]
async fn check_file_format_support(file_path: String) -> AppResult<bool> {
    let path = std::path::Path::new(&file_path);
    if let Some(extension) = path.extension() {
        if let Some(ext_str) = extension.to_str() {
            return Ok(SystemIntegration::is_supported_format(ext_str));
        }
    }
    Ok(false)
}

#[tauri::command]
async fn get_system_info() -> SystemInfo {
    SystemIntegration::get_system_info()
}

#[tauri::command]
async fn check_system_dependencies() -> SystemDependencyCheck {
    SystemIntegration::check_system_dependencies().await
}

#[tauri::command]
async fn get_available_disk_space(directory: String) -> AppResult<u64> {
    SystemIntegration::get_available_disk_space(&directory)
}

// File System Commands
#[tauri::command]
async fn validate_multiple_files(file_paths: Vec<String>) -> AppResult<Vec<AudioFile>> {
    let mut validated_files = Vec::new();
    
    for path in file_paths {
        match utils::create_audio_file(&path) {
            Ok(audio_file) => validated_files.push(audio_file),
            Err(_) => continue, // Skip invalid files
        }
    }
    
    Ok(validated_files)
}

#[tauri::command]
async fn get_file_info(file_path: String) -> AppResult<AudioFile> {
    utils::create_audio_file(&file_path)
}

#[tauri::command]
async fn select_output_directory() -> AppResult<Option<String>> {
    SystemIntegration::select_directory().await
}

#[tauri::command]
async fn save_text_file(content: String, file_path: String) -> AppResult<()> {
    tokio::fs::write(&file_path, content).await?;
    Ok(())
}

#[tauri::command]
async fn save_binary_file(filename: String, content: String, is_base64: bool) -> AppResult<String> {

    
    // Use system file dialog to get save location
    let save_path = if let Some(path) = SystemIntegration::save_file_dialog(&filename).await? {
        path
    } else {
        return Err(error::AppError::FileNotFound("Save cancelled by user".to_string()));
    };
    
    if is_base64 {
        // Decode base64 content
        use base64::Engine;
        let decoded = base64::engine::general_purpose::STANDARD.decode(&content)
            .map_err(|e| error::AppError::ProcessingError(format!("Base64 decode error: {}", e)))?;
        tokio::fs::write(&save_path, decoded).await?;
    } else {
        tokio::fs::write(&save_path, content).await?;
    }
    
    Ok(save_path)
}

#[tauri::command]
async fn open_file_in_finder(file_path: String) -> AppResult<()> {
    SystemIntegration::reveal_file_in_explorer(&file_path).await
}

#[tauri::command]
async fn clear_output_cache() -> AppResult<()> {
    use std::path::PathBuf;

    // Get the app cache directory
    let cache_dir = dirs::cache_dir()
        .ok_or_else(|| error::AppError::ProcessingError("Could not find cache directory".to_string()))?
        .join("SpeechToText")
        .join("output");

    if !cache_dir.exists() {
        return Ok(()); // Directory doesn't exist, nothing to clear
    }

    // Read directory contents and remove transcription files
    let mut entries = tokio::fs::read_dir(&cache_dir).await?;

    while let Some(entry) = entries.next_entry().await? {
        let path = entry.path();
        if path.is_file() {
            // Remove transcription files (files containing "_transcription" and ending with .txt)
            if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
                if file_name.contains("_transcription") && file_name.ends_with(".txt") {
                    tokio::fs::remove_file(&path).await?;
                }
            }
        }
    }

    Ok(())
}

// CLI Integration Commands
#[tauri::command]
async fn check_cli_availability() -> AppResult<bool> {
    let manager = create_cli_manager();
    manager.check_cli_availability().await
}

#[tauri::command]
async fn get_cli_version() -> AppResult<String> {
    let manager = create_cli_manager();
    manager.get_cli_version().await
}

#[tauri::command]
async fn process_audio_file(
    file_path: String,
    settings: AppSettings,
    app_handle: tauri::AppHandle,
) -> AppResult<TranscriptionResult> {
    println!("🔥 process_audio_file called with: {}", file_path);
    println!("🔥 settings: {:?}", settings);

    let manager = create_cli_manager();
    println!("🔥 CliManager created, about to call process_file");

    // Create progress callback to emit events
    let app_handle_clone = app_handle.clone();
    let progress_callback: cli::ProgressCallback = Arc::new(move |progress| {
        println!("🔥 Single file progress: {:?}", progress);
        let _ = app_handle_clone.emit("file-progress", &progress);
    });

    let result = manager.process_file(&file_path, &settings, Some(progress_callback)).await;

    match &result {
        Ok(transcription) => println!("🔥 process_file completed successfully: {:?}", transcription),
        Err(e) => println!("🔥 process_file failed: {:?}", e),
    }

    result
}

#[tauri::command]
async fn process_batch_files(
    file_paths: Vec<String>,
    settings: AppSettings,
) -> AppResult<Vec<TranscriptionResult>> {
    let manager = create_cli_manager();
    manager.process_batch(&file_paths, &settings, None).await
}

// Enhanced Batch Processing Commands
#[tauri::command]
async fn start_batch_processing(
    app_handle: tauri::AppHandle,
    file_paths: Vec<String>,
    settings: AppSettings,
) -> AppResult<String> {
    // Validate all files first
    let mut audio_files = Vec::new();
    for path in &file_paths {
        let audio_file = utils::create_audio_file(path)?;
        audio_files.push(audio_file);
    }

    // Create processing job
    let job_id = utils::generate_id();
    let job = ProcessingJob {
        id: job_id.clone(),
        files: audio_files,
        current_file_index: 0,
        progress: 0.0,
        stage: ProcessingStage::Initializing,
        start_time: Utc::now(),
        estimated_completion: None,
        is_cancelled: false,
        can_cancel: true,
    };

    // Create cancellation token
    let cancellation_token = tokio_util::sync::CancellationToken::new();

    // Add job to manager
    {
        let mut manager = BATCH_MANAGER.lock().await;
        manager.add_job(job);
        manager.add_cancellation_token(job_id.clone(), cancellation_token.clone());
    }

    // Start processing in background
    let job_id_clone = job_id.clone();
    let file_paths_clone = file_paths.clone();
    let settings_clone = settings.clone();
    let app_handle_clone = app_handle.clone();

    let handle = tokio::spawn(async move {
        process_batch_with_events(app_handle_clone, job_id_clone, file_paths_clone, settings_clone, cancellation_token).await;
    });

    // Store the handle
    {
        let mut manager = BATCH_MANAGER.lock().await;
        manager.add_job_handle(job_id.clone(), handle);
    }

    Ok(job_id)
}

#[tauri::command]
async fn get_batch_progress(job_id: String) -> AppResult<Option<ProcessingJob>> {
    let manager = BATCH_MANAGER.lock().await;
    Ok(manager.get_job(&job_id).cloned())
}

#[tauri::command]
async fn cancel_batch_processing(job_id: String) -> AppResult<bool> {
    let mut manager = BATCH_MANAGER.lock().await;
    let cancelled = manager.cancel_job(&job_id);
    Ok(cancelled)
}

#[tauri::command]
async fn cancel_processing_job(job_id: String) -> AppResult<bool> {
    let mut manager = BATCH_MANAGER.lock().await;
    let cancelled = manager.cancel_job(&job_id);
    Ok(cancelled)
}

#[tauri::command]
async fn get_active_batch_jobs() -> AppResult<Vec<ProcessingJob>> {
    let manager = BATCH_MANAGER.lock().await;
    Ok(manager.get_active_jobs().into_iter().cloned().collect())
}

#[tauri::command]
async fn estimate_batch_processing_time(file_paths: Vec<String>) -> AppResult<f64> {
    // Simple estimation based on file count and average processing time
    // In a real implementation, this could consider file sizes and system performance
    let file_count = file_paths.len() as f64;
    let average_time_per_file = 30.0; // seconds, rough estimate
    Ok(file_count * average_time_per_file)
}

#[tauri::command]
async fn validate_batch_requirements(
    file_paths: Vec<String>,
    output_directory: String,
) -> AppResult<models::BatchValidationResult> {
    let mut validation_result = models::BatchValidationResult {
        valid_files: Vec::new(),
        invalid_files: Vec::new(),
        total_size: 0,
        estimated_output_size: 0,
        can_proceed: true,
        warnings: Vec::new(),
    };

    // Validate output directory
    if let Err(e) = utils::validate_output_directory(&output_directory) {
        validation_result.can_proceed = false;
        validation_result.warnings.push(format!("Output directory issue: {}", e));
    }

    // Validate each file
    for path in file_paths {
        match utils::create_audio_file(&path) {
            Ok(audio_file) => {
                validation_result.total_size += audio_file.size;
                validation_result.valid_files.push(audio_file);
            }
            Err(e) => {
                validation_result.invalid_files.push(models::FileValidationError {
                    file_path: path,
                    error_message: e.to_string(),
                });
            }
        }
    }

    // Estimate output size (rough estimate: 1KB per minute of audio)
    validation_result.estimated_output_size = validation_result.valid_files.len() as u64 * 1024;

    // Check if we have any valid files
    if validation_result.valid_files.is_empty() {
        validation_result.can_proceed = false;
        validation_result.warnings.push("No valid audio files found".to_string());
    }

    Ok(validation_result)
}

/// Process batch files with real-time progress events
async fn process_batch_with_events(
    app_handle: tauri::AppHandle,
    job_id: String,
    file_paths: Vec<String>,
    settings: AppSettings,
    cancellation_token: tokio_util::sync::CancellationToken,
) {
    let cli_manager = create_cli_manager();
    let total_files = file_paths.len();
    let mut results = Vec::new();

    for (index, file_path) in file_paths.iter().enumerate() {
        // Check for cancellation
        if cancellation_token.is_cancelled() {
            let _ = app_handle.emit("batch-cancelled", &job_id);
            return;
        }

        // Update current file progress
        let progress = ProcessingProgress {
            stage: ProcessingStage::Initializing,
            progress: (index as f64 / total_files as f64) * 100.0,
            current_file: Some(file_path.clone()),
            timestamp: Utc::now(),
            message: Some(format!("Processing file {} of {}", index + 1, total_files)),
            job_id: Some(job_id.clone()),
            file_index: Some(index),
            total_files: Some(total_files),
            can_cancel: true,
        };

        // Update job in manager
        {
            let mut manager = BATCH_MANAGER.lock().await;
            manager.update_job_progress(&job_id, progress.clone());
        }

        // Emit progress event
        let _ = app_handle.emit("batch-progress", &progress);

        // Create progress callback for individual file processing
        let app_handle_clone = app_handle.clone();
        let job_id_clone = job_id.clone();
        let progress_callback: cli::ProgressCallback = Arc::new(move |file_progress| {
            let _ = app_handle_clone.emit("file-progress", &file_progress);
            
            // Update job progress
            tokio::spawn({
                let job_id = job_id_clone.clone();
                let progress = file_progress.clone();
                async move {
                    let mut manager = BATCH_MANAGER.lock().await;
                    manager.update_job_progress(&job_id, progress);
                }
            });
        });

        // Process individual file with cancellation support
        match cli_manager.process_file_with_cancellation(
            file_path, 
            &settings, 
            Some(progress_callback),
            Some(cancellation_token.clone())
        ).await {
            Ok(result) => {
                results.push(result.clone());
                let _ = app_handle.emit("file-completed", &result);
            }
            Err(e) => {
                let error_event = serde_json::json!({
                    "file_path": file_path,
                    "error": e.to_string()
                });
                let _ = app_handle.emit("file-error", &error_event);
            }
        }

        // Check if job was cancelled
        {
            let manager = BATCH_MANAGER.lock().await;
            if manager.get_job(&job_id).is_none() {
                let _ = app_handle.emit("batch-cancelled", &job_id);
                return;
            }
        }
    }

    // Batch completed
    let completion_event = serde_json::json!({
        "job_id": job_id,
        "total_files": total_files,
        "successful": results.len(),
        "results": results
    });
    let _ = app_handle.emit("batch-completed", &completion_event);

    // Remove job from manager
    {
        let mut manager = BATCH_MANAGER.lock().await;
        manager.remove_job(&job_id);
    }
}

#[tauri::command]
async fn execute_cli_command(args: Vec<String>) -> AppResult<CliResult> {
    let manager = create_cli_manager();
    let args_refs: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
    manager.execute_raw_command(&args_refs).await
}

// macOS Integration Commands
#[tauri::command]
async fn set_dock_badge(badge_info: DockBadgeInfo) -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.set_dock_badge(badge_info)
}

#[tauri::command]
async fn clear_dock_badge() -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.clear_dock_badge()
}

#[tauri::command]
async fn show_notification(options: NotificationOptions) -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.show_notification(options)
}

#[tauri::command]
async fn set_dock_progress(progress: f64) -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.set_dock_progress(progress)
}

#[tauri::command]
async fn clear_dock_progress() -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.clear_dock_progress()
}

#[tauri::command]
async fn register_file_associations() -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.register_file_associations()
}

#[tauri::command]
async fn verify_file_associations() -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.verify_file_associations()
}

#[tauri::command]
async fn get_file_association_status() -> AppResult<Vec<FileAssociationStatus>> {
    let integration = MacOSIntegration::new();
    integration.get_file_association_status()
}

#[tauri::command]
async fn set_as_default_handler() -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.set_as_default_handler()
}

#[tauri::command]
async fn get_macos_version() -> AppResult<String> {
    let integration = MacOSIntegration::new();
    integration.get_macos_version()
}

#[tauri::command]
async fn is_macos() -> bool {
    MacOSIntegration::is_macos()
}

#[tauri::command]
async fn handle_file_opened_from_finder(file_path: String) -> AppResult<()> {
    let integration = MacOSIntegration::new();
    integration.handle_file_opened(file_path)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            get_app_version,
            get_supported_formats,
            get_supported_formats_detailed,
            validate_audio_file,
            validate_multiple_files,
            get_file_info,
            select_output_directory,
            select_directory,
            select_files,
            save_text_file,
            save_binary_file,
            open_file_in_finder,
            clear_output_cache,
            reveal_file_in_explorer,
            open_file_with_default_app,
            check_file_format_support,
            get_system_info,
            check_system_dependencies,
            get_available_disk_space,
            get_default_settings,
            load_settings,
            save_settings,
            update_settings_field,
            reset_settings_to_defaults,
            validate_settings,
            get_settings_config_path,
            settings_config_exists,
            export_settings_to_file,
            import_settings_from_file,
            check_cli_availability,
            get_cli_version,
            process_audio_file,
            process_batch_files,
            start_batch_processing,
            get_batch_progress,
            cancel_batch_processing,
            get_active_batch_jobs,
            estimate_batch_processing_time,
            validate_batch_requirements,
            execute_cli_command,
            cancel_processing_job,
            set_dock_badge,
            clear_dock_badge,
            show_notification,
            set_dock_progress,
            clear_dock_progress,
            register_file_associations,
            verify_file_associations,
            get_file_association_status,
            set_as_default_handler,
            get_macos_version,
            is_macos,
            handle_file_opened_from_finder,
            updater::check_for_updates,
            updater::get_updater_version,
            updater::get_build_info,
            updater::is_auto_update_enabled,
            updater::set_auto_update_enabled,
            updater::install_update,
            updater::get_update_check_frequency,
            updater::set_update_check_frequency
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
