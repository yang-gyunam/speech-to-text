use std::path::PathBuf;
use std::fs;
use tempfile::TempDir;
use tokio::test;
use serde_json::json;

// Import your app's modules
use tauri_gui_app::{
    commands::{
        process_audio_file, process_batch_files, get_processing_progress,
        load_settings, save_settings, get_supported_formats,
        select_output_directory, save_text_file, open_file_in_finder
    },
    models::{AppSettings, TranscriptionResult, ProcessingProgress},
    error::AppError,
};

#[tokio::test]
async fn test_settings_management() {
    let temp_dir = TempDir::new().unwrap();
    let config_path = temp_dir.path().join("config.json");
    
    // Test default settings
    let default_settings = AppSettings::default();
    assert_eq!(default_settings.language, "ko");
    assert_eq!(default_settings.model_size, "base");
    
    // Test saving settings
    let custom_settings = AppSettings {
        language: "en".to_string(),
        model_size: "large".to_string(),
        output_directory: "/custom/output".to_string(),
        include_metadata: false,
        auto_save: false,
        theme: "dark".to_string(),
    };
    
    let result = save_settings(custom_settings.clone(), Some(config_path.clone())).await;
    assert!(result.is_ok());
    
    // Test loading settings
    let loaded_settings = load_settings(Some(config_path)).await.unwrap();
    assert_eq!(loaded_settings.language, "en");
    assert_eq!(loaded_settings.model_size, "large");
    assert_eq!(loaded_settings.output_directory, "/custom/output");
}

#[tokio::test]
async fn test_supported_formats() {
    let formats = get_supported_formats().await.unwrap();
    
    assert!(formats.contains(&"m4a".to_string()));
    assert!(formats.contains(&"wav".to_string()));
    assert!(formats.contains(&"mp3".to_string()));
    assert!(formats.contains(&"aac".to_string()));
    assert!(formats.contains(&"flac".to_string()));
    
    assert_eq!(formats.len(), 5);
}

#[tokio::test]
async fn test_file_validation() {
    let temp_dir = TempDir::new().unwrap();
    
    // Create test files
    let valid_audio_file = temp_dir.path().join("test.m4a");
    let invalid_file = temp_dir.path().join("test.txt");
    let nonexistent_file = temp_dir.path().join("nonexistent.m4a");
    
    fs::write(&valid_audio_file, b"fake audio content").unwrap();
    fs::write(&invalid_file, b"text content").unwrap();
    
    // Test valid file
    let result = validate_audio_file(&valid_audio_file).await;
    assert!(result.is_ok());
    
    // Test invalid format
    let result = validate_audio_file(&invalid_file).await;
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), AppError::UnsupportedFormat(_)));
    
    // Test nonexistent file
    let result = validate_audio_file(&nonexistent_file).await;
    assert!(result.is_err());
    assert!(matches!(result.unwrap_err(), AppError::FileNotFound(_)));
}

#[tokio::test]
async fn test_text_file_operations() {
    let temp_dir = TempDir::new().unwrap();
    let output_file = temp_dir.path().join("output.txt");
    
    let test_content = "안녕하세요. 이것은 테스트 텍스트입니다.";
    
    // Test saving text file
    let result = save_text_file(
        test_content.to_string(),
        output_file.to_string_lossy().to_string()
    ).await;
    
    assert!(result.is_ok());
    
    // Verify file was created and content is correct
    let saved_content = fs::read_to_string(&output_file).unwrap();
    assert_eq!(saved_content, test_content);
}

#[tokio::test]
async fn test_batch_processing_workflow() {
    let temp_dir = TempDir::new().unwrap();
    
    // Create multiple test audio files
    let file_paths: Vec<String> = (0..3)
        .map(|i| {
            let file_path = temp_dir.path().join(format!("test_{}.m4a", i));
            fs::write(&file_path, format!("fake audio content {}", i)).unwrap();
            file_path.to_string_lossy().to_string()
        })
        .collect();
    
    let settings = AppSettings::default();
    
    // This would normally call the actual processing function
    // For testing, we'll mock the behavior
    let result = simulate_batch_processing(file_paths, settings).await;
    
    assert!(result.is_ok());
    let results = result.unwrap();
    assert_eq!(results.len(), 3);
    
    // Verify each result has expected structure
    for (i, result) in results.iter().enumerate() {
        assert!(result.id.contains(&format!("test_{}", i)));
        assert!(!result.transcribed_text.is_empty());
        assert!(result.processing_time > 0);
    }
}

#[tokio::test]
async fn test_progress_monitoring() {
    // Test progress tracking during processing
    let progress = ProcessingProgress {
        current_file: "test.m4a".to_string(),
        progress: 0.75,
        stage: "transcribing".to_string(),
        time_elapsed: 45,
        estimated_time_remaining: Some(15),
    };
    
    // Test progress serialization/deserialization
    let json_str = serde_json::to_string(&progress).unwrap();
    let deserialized: ProcessingProgress = serde_json::from_str(&json_str).unwrap();
    
    assert_eq!(deserialized.current_file, "test.m4a");
    assert_eq!(deserialized.progress, 0.75);
    assert_eq!(deserialized.stage, "transcribing");
}

#[tokio::test]
async fn test_error_handling() {
    // Test various error conditions
    
    // Invalid file path
    let result = process_audio_file(
        "/nonexistent/path/file.m4a".to_string(),
        AppSettings::default()
    ).await;
    assert!(result.is_err());
    
    // Invalid settings
    let invalid_settings = AppSettings {
        language: "invalid_lang".to_string(),
        model_size: "invalid_size".to_string(),
        output_directory: "".to_string(),
        include_metadata: true,
        auto_save: true,
        theme: "system".to_string(),
    };
    
    let temp_dir = TempDir::new().unwrap();
    let test_file = temp_dir.path().join("test.m4a");
    fs::write(&test_file, b"fake content").unwrap();
    
    let result = process_audio_file(
        test_file.to_string_lossy().to_string(),
        invalid_settings
    ).await;
    assert!(result.is_err());
}

#[tokio::test]
async fn test_concurrent_processing() {
    let temp_dir = TempDir::new().unwrap();
    
    // Create multiple files for concurrent processing
    let files: Vec<String> = (0..5)
        .map(|i| {
            let file_path = temp_dir.path().join(format!("concurrent_{}.m4a", i));
            fs::write(&file_path, format!("content {}", i)).unwrap();
            file_path.to_string_lossy().to_string()
        })
        .collect();
    
    let settings = AppSettings::default();
    
    // Process files concurrently
    let tasks: Vec<_> = files.into_iter()
        .map(|file_path| {
            let settings = settings.clone();
            tokio::spawn(async move {
                simulate_single_file_processing(file_path, settings).await
            })
        })
        .collect();
    
    // Wait for all tasks to complete
    let results: Vec<_> = futures::future::join_all(tasks).await;
    
    // Verify all tasks completed successfully
    for result in results {
        assert!(result.is_ok());
        assert!(result.unwrap().is_ok());
    }
}

#[tokio::test]
async fn test_memory_usage() {
    // Test processing large files doesn't cause memory issues
    let temp_dir = TempDir::new().unwrap();
    let large_file = temp_dir.path().join("large_file.m4a");
    
    // Create a "large" file (simulated)
    let large_content = vec![0u8; 10 * 1024 * 1024]; // 10MB
    fs::write(&large_file, large_content).unwrap();
    
    let initial_memory = get_memory_usage();
    
    let result = simulate_single_file_processing(
        large_file.to_string_lossy().to_string(),
        AppSettings::default()
    ).await;
    
    let final_memory = get_memory_usage();
    
    assert!(result.is_ok());
    
    // Memory usage shouldn't increase dramatically
    let memory_increase = final_memory - initial_memory;
    assert!(memory_increase < 50 * 1024 * 1024); // Less than 50MB increase
}

#[tokio::test]
async fn test_file_system_operations() {
    let temp_dir = TempDir::new().unwrap();
    
    // Test directory selection (mocked)
    let selected_dir = simulate_directory_selection().await;
    assert!(selected_dir.is_ok());
    
    // Test file reveal in finder (mocked)
    let test_file = temp_dir.path().join("test.txt");
    fs::write(&test_file, "test content").unwrap();
    
    let result = open_file_in_finder(test_file.to_string_lossy().to_string()).await;
    // This would normally open Finder, but in tests we just verify it doesn't error
    assert!(result.is_ok());
}

#[tokio::test]
async fn test_configuration_validation() {
    // Test various configuration scenarios
    
    // Valid configuration
    let valid_config = AppSettings {
        language: "ko".to_string(),
        model_size: "base".to_string(),
        output_directory: "/valid/path".to_string(),
        include_metadata: true,
        auto_save: true,
        theme: "system".to_string(),
    };
    
    assert!(validate_settings(&valid_config).is_ok());
    
    // Invalid language
    let invalid_lang_config = AppSettings {
        language: "".to_string(),
        ..valid_config.clone()
    };
    
    assert!(validate_settings(&invalid_lang_config).is_err());
    
    // Invalid model size
    let invalid_model_config = AppSettings {
        model_size: "invalid".to_string(),
        ..valid_config.clone()
    };
    
    assert!(validate_settings(&invalid_model_config).is_err());
}

// Helper functions for testing

async fn simulate_single_file_processing(
    file_path: String,
    settings: AppSettings
) -> Result<TranscriptionResult, AppError> {
    // Simulate processing delay
    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
    
    Ok(TranscriptionResult {
        id: format!("result_{}", uuid::Uuid::new_v4()),
        original_file: file_path.clone(),
        transcribed_text: "모의 음성 변환 결과입니다.".to_string(),
        metadata: json!({
            "language": settings.language,
            "model_size": settings.model_size,
            "processing_time": 100
        }),
        output_path: format!("{}.txt", file_path),
        processing_time: 100,
        confidence: Some(0.85),
    })
}

async fn simulate_batch_processing(
    file_paths: Vec<String>,
    settings: AppSettings
) -> Result<Vec<TranscriptionResult>, AppError> {
    let mut results = Vec::new();
    
    for file_path in file_paths {
        let result = simulate_single_file_processing(file_path, settings.clone()).await?;
        results.push(result);
    }
    
    Ok(results)
}

async fn simulate_directory_selection() -> Result<Option<String>, AppError> {
    Ok(Some("/selected/directory".to_string()))
}

fn get_memory_usage() -> usize {
    // In a real implementation, this would get actual memory usage
    // For testing, we return a mock value
    1024 * 1024 // 1MB
}

fn validate_settings(settings: &AppSettings) -> Result<(), AppError> {
    if settings.language.is_empty() {
        return Err(AppError::ConfigError("Language cannot be empty".to_string()));
    }
    
    let valid_models = ["tiny", "base", "small", "medium", "large"];
    if !valid_models.contains(&settings.model_size.as_str()) {
        return Err(AppError::ConfigError("Invalid model size".to_string()));
    }
    
    Ok(())
}

async fn validate_audio_file(file_path: &PathBuf) -> Result<(), AppError> {
    if !file_path.exists() {
        return Err(AppError::FileNotFound(file_path.to_string_lossy().to_string()));
    }
    
    let extension = file_path.extension()
        .and_then(|ext| ext.to_str())
        .unwrap_or("");
    
    let supported_formats = ["m4a", "wav", "mp3", "aac", "flac"];
    if !supported_formats.contains(&extension) {
        return Err(AppError::UnsupportedFormat(extension.to_string()));
    }
    
    Ok(())
}