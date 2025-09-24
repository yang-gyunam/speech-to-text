use crate::error::{AppError, AppResult};
use crate::models::{AppSettings, ModelSize, Theme};
use serde_json;
use std::path::PathBuf;
use tokio::fs;

/// Settings manager for handling configuration persistence and validation
pub struct SettingsManager {
    config_path: PathBuf,
}

impl SettingsManager {
    /// Create a new settings manager with the default config path
    pub fn new() -> AppResult<Self> {
        let config_dir = Self::get_config_directory()?;
        let config_path = config_dir.join("settings.json");
        
        Ok(Self { config_path })
    }

    /// Create a settings manager with a custom config path (useful for testing)
    pub fn with_config_path(config_path: PathBuf) -> Self {
        Self { config_path }
    }

    /// Get the application configuration directory
    fn get_config_directory() -> AppResult<PathBuf> {
        let config_dir = dirs::config_dir()
            .ok_or_else(|| AppError::ConfigError("Could not determine config directory".to_string()))?
            .join("speech-to-text-gui");
        
        Ok(config_dir)
    }

    /// Load settings from the configuration file
    pub async fn load_settings(&self) -> AppResult<AppSettings> {
        // If config file doesn't exist, return default settings
        if !self.config_path.exists() {
            let default_settings = AppSettings::default();
            // Create the config directory and save default settings
            self.save_settings(&default_settings).await?;
            return Ok(default_settings);
        }

        let content = fs::read_to_string(&self.config_path).await
            .map_err(|e| AppError::ConfigError(format!("Failed to read config file: {}", e)))?;

        let settings: AppSettings = serde_json::from_str(&content)
            .map_err(|e| AppError::ConfigError(format!("Failed to parse config file: {}", e)))?;

        // Validate the loaded settings
        self.validate_settings(&settings)?;

        Ok(settings)
    }

    /// Save settings to the configuration file
    pub async fn save_settings(&self, settings: &AppSettings) -> AppResult<()> {
        // Validate settings before saving
        self.validate_settings(settings)?;

        // Ensure the config directory exists
        if let Some(parent) = self.config_path.parent() {
            fs::create_dir_all(parent).await
                .map_err(|e| AppError::ConfigError(format!("Failed to create config directory: {}", e)))?;
        }

        let content = serde_json::to_string_pretty(settings)
            .map_err(|e| AppError::ConfigError(format!("Failed to serialize settings: {}", e)))?;

        fs::write(&self.config_path, content).await
            .map_err(|e| AppError::ConfigError(format!("Failed to write config file: {}", e)))?;

        Ok(())
    }

    /// Validate settings for correctness and consistency
    pub fn validate_settings(&self, settings: &AppSettings) -> AppResult<()> {
        // Validate language code (basic check for non-empty string)
        if settings.language.trim().is_empty() {
            return Err(AppError::ConfigError("Language cannot be empty".to_string()));
        }

        // Validate output directory exists or can be created
        self.validate_output_directory(&settings.output_directory)?;

        Ok(())
    }

    /// Validate that the output directory exists or can be created
    fn validate_output_directory(&self, output_dir: &str) -> AppResult<()> {
        let path = PathBuf::from(output_dir);
        
        if path.exists() {
            if !path.is_dir() {
                return Err(AppError::ConfigError(
                    format!("Output path '{}' exists but is not a directory", output_dir)
                ));
            }
        } else {
            // Try to create the directory
            if let Err(e) = std::fs::create_dir_all(&path) {
                return Err(AppError::ConfigError(
                    format!("Cannot create output directory '{}': {}", output_dir, e)
                ));
            }
        }

        Ok(())
    }

    /// Update specific settings fields and save
    pub async fn update_settings<F>(&self, updater: F) -> AppResult<AppSettings>
    where
        F: FnOnce(&mut AppSettings),
    {
        let mut settings = self.load_settings().await?;
        updater(&mut settings);
        self.save_settings(&settings).await?;
        Ok(settings)
    }

    /// Reset settings to default values
    pub async fn reset_to_defaults(&self) -> AppResult<AppSettings> {
        let default_settings = AppSettings::default();
        self.save_settings(&default_settings).await?;
        Ok(default_settings)
    }

    /// Get the path to the configuration file
    pub fn get_config_path(&self) -> &PathBuf {
        &self.config_path
    }

    /// Check if configuration file exists
    pub fn config_exists(&self) -> bool {
        self.config_path.exists()
    }

    /// Export settings to a specific file path
    pub async fn export_settings(&self, export_path: &str) -> AppResult<()> {
        let settings = self.load_settings().await?;
        let content = serde_json::to_string_pretty(&settings)
            .map_err(|e| AppError::ConfigError(format!("Failed to serialize settings: {}", e)))?;

        fs::write(export_path, content).await
            .map_err(|e| AppError::ConfigError(format!("Failed to export settings: {}", e)))?;

        Ok(())
    }

    /// Import settings from a specific file path
    pub async fn import_settings(&self, import_path: &str) -> AppResult<AppSettings> {
        let content = fs::read_to_string(import_path).await
            .map_err(|e| AppError::ConfigError(format!("Failed to read import file: {}", e)))?;

        let settings: AppSettings = serde_json::from_str(&content)
            .map_err(|e| AppError::ConfigError(format!("Failed to parse import file: {}", e)))?;

        // Validate imported settings
        self.validate_settings(&settings)?;

        // Save the imported settings
        self.save_settings(&settings).await?;

        Ok(settings)
    }
}

impl Default for SettingsManager {
    fn default() -> Self {
        Self::new().expect("Failed to create default settings manager")
    }
}

/// Settings validation utilities
pub struct SettingsValidator;

impl SettingsValidator {
    /// Validate language code format
    pub fn validate_language_code(language: &str) -> AppResult<()> {
        if language.trim().is_empty() {
            return Err(AppError::ConfigError("Language code cannot be empty".to_string()));
        }

        // Basic validation for common language codes (2-5 characters)
        if language.len() < 2 || language.len() > 5 {
            return Err(AppError::ConfigError(
                "Language code should be 2-5 characters long".to_string()
            ));
        }

        Ok(())
    }

    /// Validate model size
    pub fn validate_model_size(_model_size: &ModelSize) -> AppResult<()> {
        // All enum variants are valid, but we could add additional checks here
        // For example, checking if the model is available on the system
        Ok(())
    }

    /// Validate theme setting
    pub fn validate_theme(_theme: &Theme) -> AppResult<()> {
        // All enum variants are valid
        Ok(())
    }

    /// Validate directory path
    pub fn validate_directory_path(path: &str) -> AppResult<()> {
        if path.trim().is_empty() {
            return Err(AppError::ConfigError("Directory path cannot be empty".to_string()));
        }

        let path_buf = PathBuf::from(path);
        
        // Check if path is absolute (recommended for output directories)
        if !path_buf.is_absolute() {
            return Err(AppError::ConfigError(
                "Output directory should be an absolute path".to_string()
            ));
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn create_test_settings_manager() -> (SettingsManager, TempDir) {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("test_settings.json");
        let manager = SettingsManager::with_config_path(config_path);
        (manager, temp_dir)
    }

    #[tokio::test]
    async fn test_load_default_settings() {
        let (manager, _temp_dir) = create_test_settings_manager();
        
        let settings = manager.load_settings().await.unwrap();
        assert_eq!(settings.language, "ko");
        assert!(matches!(settings.model_size, ModelSize::Base));
    }

    #[tokio::test]
    async fn test_save_and_load_settings() {
        let (manager, _temp_dir) = create_test_settings_manager();
        
        let mut settings = AppSettings::default();
        settings.language = "en".to_string();
        settings.model_size = ModelSize::Large;
        
        manager.save_settings(&settings).await.unwrap();
        let loaded_settings = manager.load_settings().await.unwrap();
        
        assert_eq!(loaded_settings.language, "en");
        assert!(matches!(loaded_settings.model_size, ModelSize::Large));
    }

    #[tokio::test]
    async fn test_update_settings() {
        let (manager, _temp_dir) = create_test_settings_manager();
        
        let updated_settings = manager.update_settings(|settings| {
            settings.language = "ja".to_string();
            settings.auto_save = false;
        }).await.unwrap();
        
        assert_eq!(updated_settings.language, "ja");
        assert!(!updated_settings.auto_save);
    }

    #[tokio::test]
    async fn test_reset_to_defaults() {
        let (manager, _temp_dir) = create_test_settings_manager();
        
        // First, modify settings
        manager.update_settings(|settings| {
            settings.language = "fr".to_string();
        }).await.unwrap();
        
        // Then reset to defaults
        let reset_settings = manager.reset_to_defaults().await.unwrap();
        assert_eq!(reset_settings.language, "ko");
    }

    #[test]
    fn test_validate_language_code() {
        assert!(SettingsValidator::validate_language_code("en").is_ok());
        assert!(SettingsValidator::validate_language_code("ko").is_ok());
        assert!(SettingsValidator::validate_language_code("zh-CN").is_ok());
        
        assert!(SettingsValidator::validate_language_code("").is_err());
        assert!(SettingsValidator::validate_language_code("x").is_err());
        assert!(SettingsValidator::validate_language_code("toolong").is_err());
    }

    #[test]
    fn test_validate_directory_path() {
        // This test might need to be adjusted based on the OS
        #[cfg(unix)]
        {
            assert!(SettingsValidator::validate_directory_path("/tmp").is_ok());
            assert!(SettingsValidator::validate_directory_path("relative/path").is_err());
        }
        
        #[cfg(windows)]
        {
            assert!(SettingsValidator::validate_directory_path("C:\\temp").is_ok());
            assert!(SettingsValidator::validate_directory_path("relative\\path").is_err());
        }
        
        assert!(SettingsValidator::validate_directory_path("").is_err());
    }

    #[tokio::test]
    async fn test_export_import_settings() {
        let (manager, temp_dir) = create_test_settings_manager();
        
        // Create and save custom settings
        let mut settings = AppSettings::default();
        settings.language = "es".to_string();
        manager.save_settings(&settings).await.unwrap();
        
        // Export settings
        let export_path = temp_dir.path().join("exported_settings.json");
        manager.export_settings(export_path.to_str().unwrap()).await.unwrap();
        
        // Modify current settings
        manager.update_settings(|s| s.language = "de".to_string()).await.unwrap();
        
        // Import the exported settings
        let imported_settings = manager.import_settings(export_path.to_str().unwrap()).await.unwrap();
        assert_eq!(imported_settings.language, "es");
    }

    #[test]
    fn test_config_exists() {
        let (manager, _temp_dir) = create_test_settings_manager();
        assert!(!manager.config_exists());
    }
}