use tauri_gui_app_lib::system::SystemIntegration;
use tempfile::TempDir;
use std::fs;

#[tokio::test]
async fn test_system_integration_directory_selection() {
    let result = SystemIntegration::select_directory().await;
    assert!(result.is_ok());
    
    if let Ok(Some(dir)) = result {
        assert!(!dir.is_empty());
        // The directory should exist (it's typically Documents or Home)
        assert!(std::path::Path::new(&dir).exists());
    }
}

#[tokio::test]
async fn test_reveal_file_in_explorer_with_existing_file() {
    let temp_dir = TempDir::new().unwrap();
    let test_file = temp_dir.path().join("test.txt");
    fs::write(&test_file, "test content").unwrap();
    
    let result = SystemIntegration::reveal_file_in_explorer(
        &test_file.to_string_lossy()
    ).await;
    
    // This should succeed on most systems
    assert!(result.is_ok());
}

#[tokio::test]
async fn test_reveal_file_in_explorer_with_nonexistent_file() {
    let result = SystemIntegration::reveal_file_in_explorer("/nonexistent/file.txt").await;
    
    // This should fail because the file doesn't exist
    assert!(result.is_err());
}

#[tokio::test]
async fn test_open_file_with_default_app_nonexistent() {
    let result = SystemIntegration::open_file_with_default_app("/nonexistent/file.txt").await;
    
    // This should fail because the file doesn't exist
    assert!(result.is_err());
}

#[test]
fn test_supported_formats_consistency() {
    let basic_formats = SystemIntegration::get_supported_formats();
    let detailed_formats = SystemIntegration::get_supported_formats_detailed();
    
    // Both should have the same number of formats
    assert_eq!(basic_formats.len(), detailed_formats.len());
    
    // Each basic format should have a corresponding detailed format
    for basic_format in &basic_formats {
        let found = detailed_formats.iter().any(|detailed| &detailed.extension == basic_format);
        assert!(found, "Format {} not found in detailed formats", basic_format);
    }
}

#[test]
fn test_format_info_structure() {
    let formats = SystemIntegration::get_supported_formats_detailed();
    
    for format in formats {
        // Each format should have non-empty fields
        assert!(!format.extension.is_empty());
        assert!(!format.description.is_empty());
        assert!(!format.mime_type.is_empty());
        
        // MIME type should contain "audio/"
        assert!(format.mime_type.starts_with("audio/"));
    }
}

#[test]
fn test_format_support_detection() {
    // Test supported formats
    assert!(SystemIntegration::is_supported_format("m4a"));
    assert!(SystemIntegration::is_supported_format(".wav"));
    assert!(SystemIntegration::is_supported_format("MP3"));
    assert!(SystemIntegration::is_supported_format(".FLAC"));
    
    // Test unsupported formats
    assert!(!SystemIntegration::is_supported_format("txt"));
    assert!(!SystemIntegration::is_supported_format("doc"));
    assert!(!SystemIntegration::is_supported_format("pdf"));
    assert!(!SystemIntegration::is_supported_format(""));
}

#[test]
fn test_system_info_completeness() {
    let info = SystemIntegration::get_system_info();
    
    // Basic system info should be available
    assert!(!info.os.is_empty());
    assert!(!info.arch.is_empty());
    assert!(!info.family.is_empty());
    
    // At least one directory should be available
    assert!(info.home_dir.is_some() || info.documents_dir.is_some() || info.config_dir.is_some());
}

#[tokio::test]
async fn test_system_dependencies_check_structure() {
    let check = SystemIntegration::check_system_dependencies().await;
    
    // The check should complete and return a valid structure
    // We can't assert specific values since they depend on the system setup
    // But we can verify the structure is correct
    
    // If Python is not available, there should be an issue reported
    if !check.python_available {
        assert!(check.issues.iter().any(|issue| issue.contains("Python")));
    }
    
    // If CLI is not available, there should be an issue reported
    if !check.cli_available {
        assert!(check.issues.iter().any(|issue| issue.contains("speech-to-text")));
    }
}

#[test]
fn test_disk_space_check_with_valid_directory() {
    // Test with a directory that should exist on most systems
    let home_dir = dirs::home_dir().unwrap();
    let result = SystemIntegration::get_available_disk_space(
        &home_dir.to_string_lossy()
    );
    
    assert!(result.is_ok());
    if let Ok(space) = result {
        // Should return some positive amount of space
        assert!(space > 0);
    }
}

#[test]
fn test_disk_space_check_with_invalid_directory() {
    let result = SystemIntegration::get_available_disk_space("/nonexistent/directory");
    assert!(result.is_err());
}

#[tokio::test]
async fn test_file_selection_interface() {
    // Test single file selection
    let single_result = SystemIntegration::select_files(false).await;
    assert!(single_result.is_ok());
    
    // Test multiple file selection
    let multiple_result = SystemIntegration::select_files(true).await;
    assert!(multiple_result.is_ok());
    
    // Both should return empty vectors in our mock implementation
    assert_eq!(single_result.unwrap(), Vec::<String>::new());
    assert_eq!(multiple_result.unwrap(), Vec::<String>::new());
}