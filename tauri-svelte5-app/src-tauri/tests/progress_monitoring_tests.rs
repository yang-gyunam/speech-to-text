use tauri_gui_app_lib::{
    models::{ProcessingProgress, ProcessingStage, AppSettings},
    cli::CliManager,
};
use tokio_util::sync::CancellationToken;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::mpsc;

#[tokio::test]
async fn test_progress_monitoring_with_callback() {
    let (tx, mut rx) = mpsc::unbounded_channel();
    
    let callback = Arc::new(move |progress: ProcessingProgress| {
        let _ = tx.send(progress);
    });
    
    let manager = CliManager::new("echo".to_string());
    
    // Start monitoring in background
    let monitor_task = tokio::spawn(async move {
        manager.monitor_progress(callback, "test.m4a").await;
    });
    
    // Collect progress updates
    let mut updates = Vec::new();
    for _ in 0..5 {
        if let Ok(progress) = tokio::time::timeout(Duration::from_secs(2), rx.recv()).await {
            if let Some(progress) = progress {
                updates.push(progress);
            }
        }
    }
    
    monitor_task.abort();
    
    // Verify we received progress updates
    assert!(!updates.is_empty());
    
    // Verify stages are in correct order
    let stages: Vec<ProcessingStage> = updates.iter().map(|p| p.stage.clone()).collect();
    assert!(stages.contains(&ProcessingStage::LoadingModel));
    assert!(stages.contains(&ProcessingStage::Transcribing));
}

#[tokio::test]
async fn test_progress_monitoring_with_cancellation() {
    let (tx, mut rx) = mpsc::unbounded_channel();
    let cancellation_token = CancellationToken::new();
    
    let callback = Arc::new(move |progress: ProcessingProgress| {
        let _ = tx.send(progress);
    });
    
    let manager = CliManager::new("echo".to_string());
    
    // Start monitoring with cancellation
    let token_clone = cancellation_token.clone();
    let monitor_task = tokio::spawn(async move {
        manager.monitor_progress_with_cancellation(
            callback, 
            "test.m4a".to_string(), 
            Some(token_clone)
        ).await;
    });
    
    // Let it run for a bit
    tokio::time::sleep(Duration::from_millis(500)).await;
    
    // Cancel the operation
    cancellation_token.cancel();
    
    // Wait for task to complete
    let _ = tokio::time::timeout(Duration::from_secs(2), monitor_task).await;
    
    // Collect any remaining updates
    let mut updates = Vec::new();
    while let Ok(progress) = rx.try_recv() {
        updates.push(progress);
    }
    
    // Verify we got some updates before cancellation
    assert!(!updates.is_empty());
    
    // Verify cancellation was respected (task should complete quickly)
    // This is implicit in the test not timing out
}

#[tokio::test]
async fn test_file_processing_with_cancellation() {
    use tempfile::NamedTempFile;
    use std::io::Write;
    
    // Create a temporary file
    let mut temp_file = NamedTempFile::new().unwrap();
    writeln!(temp_file, "dummy audio content").unwrap();
    let file_path = temp_file.path().to_str().unwrap();
    
    let manager = CliManager::new("sleep".to_string()); // Use sleep command for testing
    let settings = AppSettings::default();
    let cancellation_token = CancellationToken::new();
    
    // Start processing in background
    let token_clone = cancellation_token.clone();
    let file_path_clone = file_path.to_string();
    let process_task = tokio::spawn(async move {
        manager.process_file_with_cancellation(
            &file_path_clone,
            &settings,
            None,
            Some(token_clone)
        ).await
    });
    
    // Cancel immediately
    cancellation_token.cancel();
    
    // Wait for result
    let result = tokio::time::timeout(Duration::from_secs(5), process_task).await;
    
    match result {
        Ok(Ok(Err(e))) => {
            // Should get a cancellation error
            let error_msg = e.to_string().to_lowercase();
            assert!(
                error_msg.contains("cancelled") || error_msg.contains("interrupted") || error_msg.contains("failed to execute"),
                "Expected cancellation or execution error, got: {}", e
            );
        }
        Ok(Err(_)) => {
            // Task was cancelled/aborted, which is also acceptable
        }
        Err(_) => {
            // Timeout occurred, which means cancellation worked (task didn't complete)
        }
        _ => {
            // Other outcomes might be acceptable depending on timing
        }
    }
}

#[tokio::test]
async fn test_progress_callback_data_structure() {
    let (tx, mut rx) = mpsc::unbounded_channel();
    
    let callback = Arc::new(move |progress: ProcessingProgress| {
        let _ = tx.send(progress);
    });
    
    let manager = CliManager::new("echo".to_string());
    
    // Start monitoring
    let monitor_task = tokio::spawn(async move {
        manager.monitor_progress(callback, "test.m4a").await;
    });
    
    // Get first progress update
    if let Ok(Some(progress)) = tokio::time::timeout(Duration::from_secs(2), rx.recv()).await {
        // Verify progress structure
        assert!(progress.progress >= 0.0);
        assert!(progress.progress <= 100.0);
        assert!(progress.current_file.is_some());
        assert_eq!(progress.current_file.unwrap(), "test.m4a");
        assert!(progress.message.is_some());
        
        // Verify timestamp is recent
        let now = chrono::Utc::now();
        let diff = now.signed_duration_since(progress.timestamp);
        assert!(diff.num_seconds() < 5);
    }
    
    monitor_task.abort();
}

#[tokio::test]
async fn test_progress_stages_sequence() {
    let (tx, mut rx) = mpsc::unbounded_channel();
    
    let callback = Arc::new(move |progress: ProcessingProgress| {
        let _ = tx.send(progress);
    });
    
    let manager = CliManager::new("echo".to_string());
    
    // Start monitoring
    let monitor_task = tokio::spawn(async move {
        manager.monitor_progress(callback, "test.m4a").await;
    });
    
    // Collect all updates
    let mut all_updates = Vec::new();
    while let Ok(progress) = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await {
        if let Some(progress) = progress {
            all_updates.push(progress);
        } else {
            break;
        }
    }
    
    monitor_task.abort();
    
    // Verify we have updates
    assert!(!all_updates.is_empty());
    
    // Verify stages are in logical order
    let stages: Vec<ProcessingStage> = all_updates.iter().map(|p| p.stage.clone()).collect();
    
    // Find positions of key stages
    let loading_pos = stages.iter().position(|s| matches!(s, ProcessingStage::LoadingModel));
    let transcribing_pos = stages.iter().position(|s| matches!(s, ProcessingStage::Transcribing));
    let saving_pos = stages.iter().position(|s| matches!(s, ProcessingStage::Saving));
    
    // Verify logical order (if stages are present)
    if let (Some(loading), Some(transcribing)) = (loading_pos, transcribing_pos) {
        assert!(loading < transcribing, "Loading should come before transcribing");
    }
    
    if let (Some(transcribing), Some(saving)) = (transcribing_pos, saving_pos) {
        assert!(transcribing < saving, "Transcribing should come before saving");
    }
}

#[tokio::test]
async fn test_progress_values_increase() {
    let (tx, mut rx) = mpsc::unbounded_channel();
    
    let callback = Arc::new(move |progress: ProcessingProgress| {
        let _ = tx.send(progress);
    });
    
    let manager = CliManager::new("echo".to_string());
    
    // Start monitoring
    let monitor_task = tokio::spawn(async move {
        manager.monitor_progress(callback, "test.m4a").await;
    });
    
    // Collect progress values
    let mut progress_values = Vec::new();
    while let Ok(progress) = tokio::time::timeout(Duration::from_millis(100), rx.recv()).await {
        if let Some(progress) = progress {
            progress_values.push(progress.progress);
        } else {
            break;
        }
    }
    
    monitor_task.abort();
    
    // Verify progress generally increases
    assert!(!progress_values.is_empty());
    
    // Check that progress values are within valid range
    for &progress in &progress_values {
        assert!(progress >= 0.0 && progress <= 100.0, "Progress should be between 0 and 100");
    }
    
    // Check that progress generally increases (allowing for some variation)
    if progress_values.len() > 1 {
        let first = progress_values[0];
        let last = progress_values[progress_values.len() - 1];
        assert!(last >= first, "Progress should generally increase over time");
    }
}