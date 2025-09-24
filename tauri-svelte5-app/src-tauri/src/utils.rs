use crate::error::{AppError, AppResult};
use crate::models::{AudioFile, FileStatus, SUPPORTED_FORMATS};
use std::path::Path;
use uuid::Uuid;

/// Generate a unique ID for files and jobs
pub fn generate_id() -> String {
    Uuid::new_v4().to_string()
}

/// Validate if a file path exists and is accessible
pub fn validate_file_path(path: &str) -> AppResult<()> {
    // Handle potential Unicode normalization issues
    let normalized_path = path.trim();
    let file_path = Path::new(normalized_path);
    
    // Debug logging
    println!("🔍 Validating file path: '{}'", normalized_path);
    println!("📁 Path exists: {}", file_path.exists());
    println!("📄 Is file: {}", file_path.is_file());
    
    // Try to get canonical path for better error reporting
    match file_path.canonicalize() {
        Ok(canonical) => println!("✅ Canonical path: {:?}", canonical),
        Err(e) => println!("❌ Cannot get canonical path: {}", e),
    }
    
    if !file_path.exists() {
        let error_msg = format!("File not found: {}", normalized_path);
        println!("❌ {}", error_msg);
        return Err(AppError::FileNotFound(error_msg));
    }
    
    if !file_path.is_file() {
        let error_msg = format!("{} is not a file", normalized_path);
        println!("❌ {}", error_msg);
        return Err(AppError::IoError(error_msg));
    }
    
    println!("✅ File validation passed");
    Ok(())
}

/// Extract file extension from path
pub fn get_file_extension(path: &str) -> Option<String> {
    Path::new(path)
        .extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| ext.to_lowercase())
}

/// Validate if file format is supported
pub fn validate_audio_format(path: &str) -> AppResult<String> {
    println!("🎵 Validating audio format for: {}", path);
    
    let extension = get_file_extension(path)
        .ok_or_else(|| {
            let error_msg = "No file extension found".to_string();
            println!("❌ {}", error_msg);
            AppError::UnsupportedFormat(error_msg)
        })?;
    
    println!("📎 Extracted extension: '{}'", extension);
    println!("📋 Supported formats: {:?}", SUPPORTED_FORMATS);
    println!("✅ Extension supported: {}", SUPPORTED_FORMATS.contains(&extension.as_str()));
    
    if !SUPPORTED_FORMATS.contains(&extension.as_str()) {
        let error_msg = format!(
            "Format '{}' is not supported. Supported formats: {}",
            extension,
            SUPPORTED_FORMATS.join(", ")
        );
        println!("❌ {}", error_msg);
        return Err(AppError::UnsupportedFormat(error_msg));
    }
    
    println!("✅ Audio format validation passed");
    Ok(extension)
}

/// Create AudioFile struct from file path
pub fn create_audio_file(path: &str) -> AppResult<AudioFile> {
    let normalized_path = path.trim();
    
    validate_file_path(normalized_path)?;
    let format = validate_audio_format(normalized_path)?;
    
    let file_path = Path::new(normalized_path);
    let metadata = std::fs::metadata(normalized_path)?;
    
    // Handle Unicode file names safely
    let file_name = file_path
        .file_name()
        .and_then(|name| name.to_str())
        .map(|name| name.to_string())
        .unwrap_or_else(|| {
            // Fallback for non-UTF8 file names
            format!("file_{}", generate_id()[..8].to_string())
        });
    
    println!("Created AudioFile: name='{}', path='{}', size={}", file_name, normalized_path, metadata.len());
    
    Ok(AudioFile {
        id: generate_id(),
        name: file_name,
        path: normalized_path.to_string(),
        size: metadata.len(),
        format,
        duration: None, // Will be populated during processing
        status: FileStatus::Pending,
    })
}

/// Format file size in human-readable format
pub fn format_file_size(bytes: u64) -> String {
    const UNITS: &[&str] = &["B", "KB", "MB", "GB"];
    let mut size = bytes as f64;
    let mut unit_index = 0;
    
    while size >= 1024.0 && unit_index < UNITS.len() - 1 {
        size /= 1024.0;
        unit_index += 1;
    }
    
    if unit_index == 0 {
        format!("{} {}", bytes, UNITS[unit_index])
    } else {
        format!("{:.1} {}", size, UNITS[unit_index])
    }
}

/// Format duration in human-readable format (MM:SS)
pub fn format_duration(seconds: f64) -> String {
    let total_seconds = seconds as u64;
    let minutes = total_seconds / 60;
    let seconds = total_seconds % 60;
    format!("{:02}:{:02}", minutes, seconds)
}

/// Sanitize filename for safe file system operations
pub fn sanitize_filename(filename: &str) -> String {
    filename
        .chars()
        .map(|c| match c {
            '/' | '\\' | ':' | '*' | '?' | '"' | '<' | '>' | '|' => '_',
            c => c,
        })
        .collect()
}

/// Get output filename for transcription result
pub fn get_output_filename(input_path: &str, output_dir: &str) -> AppResult<String> {
    let input_path = Path::new(input_path);
    let stem = input_path
        .file_stem()
        .and_then(|s| s.to_str())
        .ok_or_else(|| AppError::IoError("Invalid input filename".to_string()))?;

    let sanitized_stem = sanitize_filename(stem);
    // Use transcription suffix (actual file will have timestamp added by Python CLI)
    let output_filename = format!("{}_transcription.txt", sanitized_stem);

    // Use same directory as input file if output_dir is empty (default behavior)
    let actual_output_dir = if output_dir.is_empty() {
        // Use the same directory as the input file
        input_path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .to_string_lossy()
            .to_string()
    } else {
        // Use user-specified output directory
        output_dir.to_string()
    };

    let output_path = Path::new(&actual_output_dir).join(output_filename);
    Ok(output_path.to_string_lossy().to_string())
}

/// Check if a directory exists and is writable
pub fn validate_output_directory(dir_path: &str) -> AppResult<()> {
    let path = Path::new(dir_path);
    
    if !path.exists() {
        return Err(AppError::IoError(format!("Directory does not exist: {}", dir_path)));
    }
    
    if !path.is_dir() {
        return Err(AppError::IoError(format!("{} is not a directory", dir_path)));
    }
    
    // Try to create a temporary file to check write permissions
    let temp_file = path.join(".write_test");
    match std::fs::File::create(&temp_file) {
        Ok(_) => {
            let _ = std::fs::remove_file(&temp_file);
            Ok(())
        }
        Err(_) => Err(AppError::IoError(format!("Directory is not writable: {}", dir_path)))
    }
}

/// Get audio file duration using basic file metadata (placeholder)
pub fn get_audio_duration(file_path: &str) -> AppResult<Option<f64>> {
    // This is a placeholder implementation
    // In a real implementation, you would use a library like ffprobe or similar
    // to extract actual audio duration
    validate_file_path(file_path)?;
    
    // For now, return None to indicate duration is not available
    // This would be populated by the CLI during processing
    Ok(None)
}

/// Batch validate multiple file paths
pub fn validate_multiple_file_paths(paths: &[String]) -> Vec<AppResult<AudioFile>> {
    paths.iter()
        .map(|path| create_audio_file(path))
        .collect()
}

/// Check available disk space in output directory
pub fn check_available_space(dir_path: &str) -> AppResult<u64> {
    let path = Path::new(dir_path);
    if !path.exists() {
        return Err(AppError::IoError(format!("Directory does not exist: {}", dir_path)));
    }
    
    // This is a simplified implementation
    // On Unix systems, you would use statvfs, on Windows GetDiskFreeSpaceEx
    // For now, return a large number as placeholder
    Ok(u64::MAX)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use tempfile::tempdir;

    #[test]
    fn test_generate_id() {
        let id1 = generate_id();
        let id2 = generate_id();
        assert_ne!(id1, id2);
        assert_eq!(id1.len(), 36); // UUID v4 length
    }

    #[test]
    fn test_get_file_extension() {
        assert_eq!(get_file_extension("test.m4a"), Some("m4a".to_string()));
        assert_eq!(get_file_extension("test.M4A"), Some("m4a".to_string()));
        assert_eq!(get_file_extension("test"), None);
    }

    #[test]
    fn test_validate_audio_format() {
        assert!(validate_audio_format("test.m4a").is_ok());
        assert!(validate_audio_format("test.wav").is_ok());
        assert!(validate_audio_format("test.txt").is_err());
    }

    #[test]
    fn test_format_file_size() {
        assert_eq!(format_file_size(512), "512 B");
        assert_eq!(format_file_size(1024), "1.0 KB");
        assert_eq!(format_file_size(1536), "1.5 KB");
        assert_eq!(format_file_size(1048576), "1.0 MB");
    }

    #[test]
    fn test_format_duration() {
        assert_eq!(format_duration(65.0), "01:05");
        assert_eq!(format_duration(3661.0), "61:01");
        assert_eq!(format_duration(30.5), "00:30");
    }

    #[test]
    fn test_sanitize_filename() {
        assert_eq!(sanitize_filename("test/file.txt"), "test_file.txt");
        assert_eq!(sanitize_filename("test:file"), "test_file");
        assert_eq!(sanitize_filename("normal_file"), "normal_file");
    }

    #[test]
    fn test_create_audio_file() {
        let temp_dir = tempdir().unwrap();
        let file_path = temp_dir.path().join("test.m4a");
        File::create(&file_path).unwrap();
        
        let audio_file = create_audio_file(file_path.to_str().unwrap()).unwrap();
        assert_eq!(audio_file.name, "test.m4a");
        assert_eq!(audio_file.format, "m4a");
        assert!(matches!(audio_file.status, FileStatus::Pending));
    }

    #[test]
    fn test_get_output_filename() {
        let result = get_output_filename("/path/to/audio.m4a", "/output").unwrap();
        assert!(result.ends_with("audio.txt"));
        assert!(result.starts_with("/output"));
    }

    #[test]
    fn test_validate_output_directory() {
        let temp_dir = tempdir().unwrap();
        let dir_path = temp_dir.path().to_str().unwrap();
        
        // Valid directory should pass
        assert!(validate_output_directory(dir_path).is_ok());
        
        // Non-existent directory should fail
        assert!(validate_output_directory("/nonexistent/path").is_err());
    }

    #[test]
    fn test_get_audio_duration() {
        let temp_dir = tempdir().unwrap();
        let file_path = temp_dir.path().join("test.m4a");
        File::create(&file_path).unwrap();
        
        let duration = get_audio_duration(file_path.to_str().unwrap()).unwrap();
        assert!(duration.is_none()); // Placeholder implementation returns None
    }

    #[test]
    fn test_validate_multiple_file_paths() {
        let temp_dir = tempdir().unwrap();
        let file1 = temp_dir.path().join("test1.m4a");
        let file2 = temp_dir.path().join("test2.wav");
        File::create(&file1).unwrap();
        File::create(&file2).unwrap();
        
        let paths = vec![
            file1.to_string_lossy().to_string(),
            file2.to_string_lossy().to_string(),
            "/nonexistent.mp3".to_string(),
        ];
        
        let results = validate_multiple_file_paths(&paths);
        assert_eq!(results.len(), 3);
        assert!(results[0].is_ok());
        assert!(results[1].is_ok());
        assert!(results[2].is_err());
    }

    #[test]
    fn test_check_available_space() {
        let temp_dir = tempdir().unwrap();
        let dir_path = temp_dir.path().to_str().unwrap();
        
        let space = check_available_space(dir_path).unwrap();
        assert!(space > 0);
        
        // Non-existent directory should fail
        assert!(check_available_space("/nonexistent/path").is_err());
    }
}