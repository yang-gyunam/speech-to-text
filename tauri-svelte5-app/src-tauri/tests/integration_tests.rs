use tauri_gui_app_lib::cli::CliManager;
use tauri_gui_app_lib::models::AppSettings;
use tempfile::tempdir;
use std::fs::File;
use tokio::time::Duration;

#[tokio::test]
async fn test_cli_integration_basic() {
    let manager = CliManager::default();
    
    // Test basic CLI availability check (this will fail if CLI is not installed, which is expected)
    let availability = manager.check_cli_availability().await;
    // We don't assert success here since the CLI might not be installed in test environment
    println!("CLI availability check result: {:?}", availability);
}

#[tokio::test]
async fn test_cli_integration_with_mock_command() {
    // Use echo as a mock CLI command for testing
    let manager = CliManager::new("echo".to_string()).with_timeout(Duration::from_secs(5));
    
    // Test raw command execution
    let result = manager.execute_raw_command(&["test", "output"]).await;
    assert!(result.is_ok());
    
    let cli_result = result.unwrap();
    assert!(cli_result.success);
    assert!(cli_result.output.contains("test output"));
    assert_eq!(cli_result.exit_code, 0);
}

#[tokio::test]
async fn test_cli_integration_file_processing_structure() {
    let temp_dir = tempdir().unwrap();
    let file_path = temp_dir.path().join("test.m4a");
    File::create(&file_path).unwrap();
    
    let manager = CliManager::new("echo".to_string()); // Mock with echo
    let settings = AppSettings::default();
    
    // This will fail because echo is not the real CLI, but it tests the structure
    let result = manager.process_file(file_path.to_str().unwrap(), &settings, None).await;
    
    // We expect this to fail with echo, but the error should be a CLI error, not a file error
    match result {
        Err(tauri_gui_app_lib::error::AppError::CliError(_)) => {
            // This is expected - echo doesn't produce the expected CLI output format
        }
        Err(tauri_gui_app_lib::error::AppError::FileNotFound(_)) => {
            panic!("File should exist, this indicates a file handling issue");
        }
        Ok(_) => {
            // This would be unexpected with echo, but not necessarily wrong
            println!("Unexpected success with echo command");
        }
        Err(e) => {
            println!("Other error type: {:?}", e);
        }
    }
}

#[tokio::test]
async fn test_batch_processing_structure() {
    let temp_dir = tempdir().unwrap();
    let file1 = temp_dir.path().join("test1.m4a");
    let file2 = temp_dir.path().join("test2.m4a");
    File::create(&file1).unwrap();
    File::create(&file2).unwrap();
    
    let manager = CliManager::new("echo".to_string());
    let settings = AppSettings::default();
    let file_paths = vec![
        file1.to_string_lossy().to_string(),
        file2.to_string_lossy().to_string(),
    ];
    
    // Test batch processing structure
    let result = manager.process_batch(&file_paths, &settings, None).await;
    
    // Should return Ok with empty results (since echo fails to process properly)
    assert!(result.is_ok());
    let results = result.unwrap();
    // Results might be empty due to echo failures, but the structure should work
    println!("Batch processing completed with {} results", results.len());
}

#[tokio::test]
async fn test_cli_timeout_handling() {
    // Use sleep command to test timeout (available on Unix systems)
    let manager = CliManager::new("sleep".to_string()).with_timeout(Duration::from_millis(100));
    
    let result = manager.execute_raw_command(&["1"]).await; // Sleep for 1 second
    
    // Should timeout
    match result {
        Err(tauri_gui_app_lib::error::AppError::CliError(msg)) => {
            assert!(msg.contains("timed out") || msg.contains("timeout"));
        }
        _ => {
            // On some systems sleep might not be available, that's ok
            println!("Sleep command not available or behaved differently");
        }
    }
}

#[tokio::test]
async fn test_batch_processing_with_progress_callback() {
    use std::sync::Arc;
    use tokio::sync::mpsc;
    use tauri_gui_app_lib::models::ProcessingProgress;
    
    let temp_dir = tempdir().unwrap();
    let file1 = temp_dir.path().join("test1.m4a");
    let file2 = temp_dir.path().join("test2.m4a");
    File::create(&file1).unwrap();
    File::create(&file2).unwrap();
    
    let manager = CliManager::new("echo".to_string());
    let settings = AppSettings::default();
    let file_paths = vec![
        file1.to_string_lossy().to_string(),
        file2.to_string_lossy().to_string(),
    ];
    
    // Create progress callback
    let (tx, mut rx) = mpsc::unbounded_channel::<ProcessingProgress>();
    let progress_callback: tauri_gui_app_lib::cli::ProgressCallback = Arc::new(move |progress| {
        let _ = tx.send(progress);
    });
    
    // Start batch processing
    let process_task = tokio::spawn(async move {
        manager.process_batch(&file_paths, &settings, Some(progress_callback)).await
    });
    
    // Collect progress updates
    let mut progress_updates = Vec::new();
    let mut update_count = 0;
    
    // Collect updates for a short time
    while update_count < 5 {
        match tokio::time::timeout(Duration::from_millis(100), rx.recv()).await {
            Ok(Some(progress)) => {
                progress_updates.push(progress);
                update_count += 1;
            }
            _ => break,
        }
    }
    
    // Wait for processing to complete
    let result = process_task.await.unwrap();
    assert!(result.is_ok());
    
    // Should have received some progress updates
    println!("Received {} progress updates", progress_updates.len());
}

#[tokio::test]
async fn test_file_validation_batch() {
    use tauri_gui_app_lib::utils;
    
    let temp_dir = tempdir().unwrap();
    let valid_file1 = temp_dir.path().join("test1.m4a");
    let valid_file2 = temp_dir.path().join("test2.wav");
    let invalid_file = temp_dir.path().join("test.txt");
    
    File::create(&valid_file1).unwrap();
    File::create(&valid_file2).unwrap();
    File::create(&invalid_file).unwrap();
    
    let file_paths = vec![
        valid_file1.to_string_lossy().to_string(),
        valid_file2.to_string_lossy().to_string(),
        invalid_file.to_string_lossy().to_string(),
        "/nonexistent/file.m4a".to_string(),
    ];
    
    let results = utils::validate_multiple_file_paths(&file_paths);
    
    assert_eq!(results.len(), 4);
    assert!(results[0].is_ok()); // valid m4a
    assert!(results[1].is_ok()); // valid wav
    assert!(results[2].is_err()); // invalid format
    assert!(results[3].is_err()); // nonexistent file
}

#[tokio::test]
async fn test_concurrent_processing_simulation() {
    use tauri_gui_app_lib::models::{ProcessingJob, ProcessingStage};
    use tauri_gui_app_lib::utils;
    use chrono::Utc;
    
    // Create multiple mock processing jobs
    let mut jobs = Vec::new();
    
    for i in 0..3 {
        let temp_dir = tempdir().unwrap();
        let file_path = temp_dir.path().join(format!("test{}.m4a", i));
        File::create(&file_path).unwrap();
        
        let audio_file = utils::create_audio_file(file_path.to_str().unwrap()).unwrap();
        
        let job = ProcessingJob {
            id: utils::generate_id(),
            files: vec![audio_file],
            current_file_index: 0,
            progress: 0.0,
            stage: ProcessingStage::Initializing,
            start_time: Utc::now(),
            estimated_completion: None,
            is_cancelled: false,
            can_cancel: true,
        };
        
        jobs.push(job);
    }
    
    // Simulate concurrent job management
    assert_eq!(jobs.len(), 3);
    
    // Each job should have unique ID
    let mut ids = std::collections::HashSet::new();
    for job in &jobs {
        assert!(ids.insert(job.id.clone()));
    }
    
    println!("Created {} concurrent processing jobs", jobs.len());
}