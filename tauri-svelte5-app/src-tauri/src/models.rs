use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

/// Application settings structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub language: String,
    pub model_size: ModelSize,
    pub output_directory: String,
    pub include_metadata: bool,
    pub auto_save: bool,
    pub theme: Theme,
    // Advanced performance options
    pub max_concurrent_jobs: u32,
    pub enable_gpu_acceleration: bool,
    pub memory_optimization: bool,
    // Advanced processing options
    pub enable_voice_activity_detection: bool,
    pub noise_reduction: bool,
    pub output_format: OutputFormat,
    // UI preferences
    pub compact_mode: bool,
    pub show_advanced_options: bool,
    pub enable_notifications: bool,
    pub auto_check_updates: bool,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            language: "ko".to_string(),
            model_size: ModelSize::Base,
            output_directory: dirs::home_dir()
                .unwrap_or_default()
                .join("Documents")
                .to_string_lossy()
                .to_string(),
            include_metadata: true,
            auto_save: true,
            theme: Theme::System,
            // Advanced performance options
            max_concurrent_jobs: 2,
            enable_gpu_acceleration: false,
            memory_optimization: true,
            // Advanced processing options
            enable_voice_activity_detection: true,
            noise_reduction: false,
            output_format: OutputFormat::Txt,
            // UI preferences
            compact_mode: false,
            show_advanced_options: false,
            enable_notifications: true,
            auto_check_updates: true,
        }
    }
}

/// Whisper model sizes
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ModelSize {
    Tiny,
    Base,
    Small,
    Medium,
    Large,
}

impl std::fmt::Display for ModelSize {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ModelSize::Tiny => write!(f, "tiny"),
            ModelSize::Base => write!(f, "base"),
            ModelSize::Small => write!(f, "small"),
            ModelSize::Medium => write!(f, "medium"),
            ModelSize::Large => write!(f, "large"),
        }
    }
}

/// UI theme options
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Theme {
    Light,
    Dark,
    System,
}

/// Output format options
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum OutputFormat {
    Txt,
    Srt,
    Vtt,
    Json,
}

/// Audio file information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioFile {
    pub id: String,
    pub name: String,
    pub path: String,
    pub size: u64,
    pub format: String,
    pub duration: Option<f64>,
    pub status: FileStatus,
}

/// File processing status
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum FileStatus {
    Pending,
    Processing,
    Completed,
    Error,
}

/// Transcription result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptionResult {
    pub id: String,
    pub original_file: AudioFile,
    pub transcribed_text: String,
    pub metadata: TranscriptionMetadata,
    pub output_path: String,
    pub processing_time: f64,
    pub confidence: Option<f64>,
}

/// Transcription metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptionMetadata {
    pub language: String,
    pub model_size: String,
    pub timestamp: DateTime<Utc>,
    pub audio_info: AudioInfo,
}

/// Audio file information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioInfo {
    pub duration: f64,
    pub sample_rate: Option<u32>,
    pub channels: Option<u32>,
}

/// Processing job information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingJob {
    pub id: String,
    pub files: Vec<AudioFile>,
    pub current_file_index: usize,
    pub progress: f64,
    pub stage: ProcessingStage,
    pub start_time: DateTime<Utc>,
    pub estimated_completion: Option<DateTime<Utc>>,
    pub is_cancelled: bool,
    pub can_cancel: bool,
}

/// Processing stages
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "snake_case")]
pub enum ProcessingStage {
    Initializing,
    LoadingModel,
    Preprocessing,
    Transcribing,
    Postprocessing,
    Finalizing,
    Saving,
}

impl std::fmt::Display for ProcessingStage {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ProcessingStage::Initializing => write!(f, "Initializing"),
            ProcessingStage::LoadingModel => write!(f, "Loading Model"),
            ProcessingStage::Preprocessing => write!(f, "Preprocessing"),
            ProcessingStage::Transcribing => write!(f, "Transcribing"),
            ProcessingStage::Postprocessing => write!(f, "Postprocessing"),
            ProcessingStage::Finalizing => write!(f, "Finalizing"),
            ProcessingStage::Saving => write!(f, "Saving"),
        }
    }
}

/// Processing progress information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingProgress {
    pub stage: ProcessingStage,
    pub progress: f64,
    pub current_file: Option<String>,
    pub timestamp: DateTime<Utc>,
    pub message: Option<String>,
    pub job_id: Option<String>,
    pub file_index: Option<usize>,
    pub total_files: Option<usize>,
    pub can_cancel: bool,
}

/// Batch processing statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchStatistics {
    pub total_files: usize,
    pub completed_files: usize,
    pub failed_files: usize,
    pub total_processing_time: f64,
    pub average_processing_time: f64,
}

/// Batch processing result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchResult {
    pub job_id: String,
    pub statistics: BatchStatistics,
    pub results: Vec<TranscriptionResult>,
    pub errors: Vec<ProcessingError>,
}

/// Processing error information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessingError {
    pub file_path: String,
    pub error_message: String,
    pub timestamp: DateTime<Utc>,
}

/// Batch validation result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BatchValidationResult {
    pub valid_files: Vec<AudioFile>,
    pub invalid_files: Vec<FileValidationError>,
    pub total_size: u64,
    pub estimated_output_size: u64,
    pub can_proceed: bool,
    pub warnings: Vec<String>,
}

/// File validation error
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileValidationError {
    pub file_path: String,
    pub error_message: String,
}

/// Supported audio formats
pub const SUPPORTED_FORMATS: &[&str] = &["m4a", "wav", "mp3", "aac", "flac"];

/// Check if a file extension is supported
pub fn is_supported_format(extension: &str) -> bool {
    SUPPORTED_FORMATS.contains(&extension.to_lowercase().as_str())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_settings() {
        let settings = AppSettings::default();
        assert_eq!(settings.language, "ko");
        assert!(matches!(settings.model_size, ModelSize::Base));
        assert!(settings.include_metadata);
        assert!(settings.auto_save);
    }

    #[test]
    fn test_model_size_display() {
        assert_eq!(ModelSize::Base.to_string(), "base");
        assert_eq!(ModelSize::Large.to_string(), "large");
    }

    #[test]
    fn test_supported_formats() {
        assert!(is_supported_format("m4a"));
        assert!(is_supported_format("M4A"));
        assert!(!is_supported_format("txt"));
    }

    #[test]
    fn test_processing_stage_display() {
        assert_eq!(ProcessingStage::LoadingModel.to_string(), "Loading Model");
        assert_eq!(ProcessingStage::Transcribing.to_string(), "Transcribing");
    }

    #[test]
    fn test_serialization() {
        let settings = AppSettings::default();
        let serialized = serde_json::to_string(&settings).unwrap();
        let deserialized: AppSettings = serde_json::from_str(&serialized).unwrap();
        assert_eq!(settings.language, deserialized.language);
    }
}