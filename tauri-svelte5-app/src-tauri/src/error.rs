use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Application-specific error types
#[derive(Debug, Error, Serialize, Deserialize)]
#[serde(tag = "type", content = "message")]
pub enum AppError {
    #[error("File not found: {0}")]
    FileNotFound(String),
    
    #[error("Unsupported file format: {0}")]
    UnsupportedFormat(String),
    
    #[error("Processing failed: {0}")]
    ProcessingError(String),
    
    #[error("CLI execution failed: {0}")]
    CliError(String),
    
    #[error("Configuration error: {0}")]
    ConfigError(String),
    
    #[error("System error: {0}")]
    SystemError(String),
    
    #[error("IO error: {0}")]
    IoError(String),
    
    #[error("Serialization error: {0}")]
    SerializationError(String),
}

impl From<std::io::Error> for AppError {
    fn from(error: std::io::Error) -> Self {
        AppError::IoError(error.to_string())
    }
}

impl From<serde_json::Error> for AppError {
    fn from(error: serde_json::Error) -> Self {
        AppError::SerializationError(error.to_string())
    }
}

/// Result type alias for convenience
pub type AppResult<T> = Result<T, AppError>;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_serialization() {
        let error = AppError::FileNotFound("test.txt".to_string());
        let serialized = serde_json::to_string(&error).unwrap();
        let deserialized: AppError = serde_json::from_str(&serialized).unwrap();
        
        match deserialized {
            AppError::FileNotFound(file) => assert_eq!(file, "test.txt"),
            _ => panic!("Wrong error type"),
        }
    }

    #[test]
    fn test_error_display() {
        let error = AppError::ProcessingError("Failed to process audio".to_string());
        assert_eq!(error.to_string(), "Processing failed: Failed to process audio");
    }

    #[test]
    fn test_io_error_conversion() {
        let io_error = std::io::Error::new(std::io::ErrorKind::NotFound, "File not found");
        let app_error: AppError = io_error.into();
        
        match app_error {
            AppError::IoError(_) => (),
            _ => panic!("Expected IoError"),
        }
    }
}