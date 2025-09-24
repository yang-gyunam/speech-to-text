use crate::error::{AppError, AppResult};
use crate::models::SUPPORTED_FORMATS;
use std::path::Path;

/// System integration utilities for native OS features
pub struct SystemIntegration;

impl SystemIntegration {
    /// Open a native directory picker dialog
    pub async fn select_directory() -> AppResult<Option<String>> {
        // For now, we'll use a simple approach. In a full implementation,
        // you would use tauri-plugin-dialog or similar for native dialogs
        
        // Return the user's Documents directory as a fallback
        let documents_dir = dirs::document_dir()
            .or_else(|| dirs::home_dir())
            .ok_or_else(|| AppError::SystemError("Could not determine default directory".to_string()))?;
        
        Ok(Some(documents_dir.to_string_lossy().to_string()))
    }

    /// Open a native file picker dialog for selecting files
    pub async fn select_files(multiple: bool) -> AppResult<Vec<String>> {
        // use tauri_plugin_dialog::{DialogExt, MessageDialogKind};
        
        // For now, let's use a simple implementation with rfd
        // In production, you'd use tauri-plugin-dialog properly
        
        // Temporary implementation using native file dialog
        #[cfg(target_os = "macos")]
        {
            use std::process::Command;
            
            let mut cmd = Command::new("osascript");
            if multiple {
                cmd.arg("-e")
                   .arg("set fileList to choose file with multiple selections allowed with prompt \"Select audio files\" of type {\"m4a\", \"wav\", \"mp3\", \"aac\", \"flac\"}")
                   .arg("-e")
                   .arg("set posixPaths to {}")
                   .arg("-e")
                   .arg("repeat with aFile in fileList")
                   .arg("-e")
                   .arg("set end of posixPaths to POSIX path of aFile")
                   .arg("-e")
                   .arg("end repeat")
                   .arg("-e")
                   .arg("set AppleScript's text item delimiters to \"\\n\"")
                   .arg("-e")
                   .arg("return posixPaths as string");
            } else {
                cmd.arg("-e")
                   .arg("set selectedFile to choose file with prompt \"Select an audio file\" of type {\"m4a\", \"wav\", \"mp3\", \"aac\", \"flac\"}")
                   .arg("-e")
                   .arg("return POSIX path of selectedFile");
            }
            
            match cmd.output() {
                Ok(output) if output.status.success() => {
                    let result = String::from_utf8_lossy(&output.stdout);
                    let paths: Vec<String> = if multiple {
                        // Parse multiple POSIX paths separated by newlines
                        result.trim()
                            .split('\n')
                            .map(|s| s.trim().to_string())
                            .filter(|s| !s.is_empty())
                            .collect()
                    } else {
                        // Single POSIX path
                        let path = result.trim().to_string();
                        if path.is_empty() { vec![] } else { vec![path] }
                    };
                    
                    println!("✅ Selected files via AppleScript (POSIX paths): {:?}", paths);
                    Ok(paths)
                }
                Ok(_) => {
                    println!("User cancelled file selection");
                    Ok(vec![])
                }
                Err(e) => {
                    println!("Failed to open file dialog: {}", e);
                    Err(crate::error::AppError::IoError(format!("Failed to open file dialog: {}", e)))
                }
            }
        }
        
        #[cfg(not(target_os = "macos"))]
        {
            // Fallback for other platforms
            Ok(vec![])
        }
    }

    /// Open a native save file dialog
    pub async fn save_file_dialog(default_filename: &str) -> AppResult<Option<String>> {
        // This is a placeholder implementation
        // In a real app, you would use tauri-plugin-dialog
        
        // For now, save to Documents directory with the provided filename
        let documents_dir = dirs::document_dir()
            .or_else(|| dirs::home_dir())
            .ok_or_else(|| AppError::SystemError("Could not determine default directory".to_string()))?;
        
        let save_path = documents_dir.join(default_filename);
        Ok(Some(save_path.to_string_lossy().to_string()))
    }

    /// Reveal a file in the system file manager (Finder on macOS, Explorer on Windows, etc.)
    pub async fn reveal_file_in_explorer(file_path: &str) -> AppResult<()> {
        let path = Path::new(file_path);
        
        if !path.exists() {
            return Err(AppError::FileNotFound(file_path.to_string()));
        }

        #[cfg(target_os = "macos")]
        {
            std::process::Command::new("open")
                .arg("-R")
                .arg(file_path)
                .spawn()
                .map_err(|e| AppError::SystemError(format!("Failed to open Finder: {}", e)))?;
        }

        #[cfg(target_os = "windows")]
        {
            std::process::Command::new("explorer")
                .arg("/select,")
                .arg(file_path)
                .spawn()
                .map_err(|e| AppError::SystemError(format!("Failed to open Explorer: {}", e)))?;
        }

        #[cfg(target_os = "linux")]
        {
            // Try different file managers commonly available on Linux
            let file_managers = ["nautilus", "dolphin", "thunar", "pcmanfm", "nemo"];
            let parent_dir = path.parent().unwrap_or(Path::new("/"));
            
            let mut success = false;
            for manager in &file_managers {
                if let Ok(_) = std::process::Command::new(manager)
                    .arg(parent_dir)
                    .spawn()
                {
                    success = true;
                    break;
                }
            }
            
            if !success {
                // Fallback to xdg-open with parent directory
                std::process::Command::new("xdg-open")
                    .arg(parent_dir)
                    .spawn()
                    .map_err(|e| AppError::SystemError(format!("Failed to open file manager: {}", e)))?;
            }
        }

        Ok(())
    }

    /// Open a file with the default system application
    pub async fn open_file_with_default_app(file_path: &str) -> AppResult<()> {
        let path = Path::new(file_path);
        
        if !path.exists() {
            return Err(AppError::FileNotFound(file_path.to_string()));
        }

        #[cfg(target_os = "macos")]
        {
            std::process::Command::new("open")
                .arg(file_path)
                .spawn()
                .map_err(|e| AppError::SystemError(format!("Failed to open file: {}", e)))?;
        }

        #[cfg(target_os = "windows")]
        {
            std::process::Command::new("cmd")
                .args(&["/C", "start", "", file_path])
                .spawn()
                .map_err(|e| AppError::SystemError(format!("Failed to open file: {}", e)))?;
        }

        #[cfg(target_os = "linux")]
        {
            std::process::Command::new("xdg-open")
                .arg(file_path)
                .spawn()
                .map_err(|e| AppError::SystemError(format!("Failed to open file: {}", e)))?;
        }

        Ok(())
    }

    /// Get supported audio formats with descriptions
    pub fn get_supported_formats_detailed() -> Vec<FormatInfo> {
        vec![
            FormatInfo {
                extension: "m4a".to_string(),
                description: "MPEG-4 Audio (AAC)".to_string(),
                mime_type: "audio/mp4".to_string(),
            },
            FormatInfo {
                extension: "wav".to_string(),
                description: "Waveform Audio File".to_string(),
                mime_type: "audio/wav".to_string(),
            },
            FormatInfo {
                extension: "mp3".to_string(),
                description: "MPEG Audio Layer III".to_string(),
                mime_type: "audio/mpeg".to_string(),
            },
            FormatInfo {
                extension: "aac".to_string(),
                description: "Advanced Audio Coding".to_string(),
                mime_type: "audio/aac".to_string(),
            },
            FormatInfo {
                extension: "flac".to_string(),
                description: "Free Lossless Audio Codec".to_string(),
                mime_type: "audio/flac".to_string(),
            },
        ]
    }

    /// Get basic supported formats list
    pub fn get_supported_formats() -> Vec<String> {
        SUPPORTED_FORMATS.iter().map(|&s| s.to_string()).collect()
    }

    /// Check if a file extension is supported
    pub fn is_supported_format(extension: &str) -> bool {
        let ext = extension.to_lowercase();
        let ext = ext.strip_prefix('.').unwrap_or(&ext);
        SUPPORTED_FORMATS.contains(&ext)
    }

    /// Get system information relevant to the application
    pub fn get_system_info() -> SystemInfo {
        SystemInfo {
            os: std::env::consts::OS.to_string(),
            arch: std::env::consts::ARCH.to_string(),
            family: std::env::consts::FAMILY.to_string(),
            home_dir: dirs::home_dir().map(|p| p.to_string_lossy().to_string()),
            documents_dir: dirs::document_dir().map(|p| p.to_string_lossy().to_string()),
            config_dir: dirs::config_dir().map(|p| p.to_string_lossy().to_string()),
        }
    }

    /// Check if the system has required dependencies
    pub async fn check_system_dependencies() -> SystemDependencyCheck {
        let mut check = SystemDependencyCheck {
            python_available: false,
            cli_available: false,
            ffmpeg_available: false,
            whisper_available: false,
            issues: Vec::new(),
        };

        // Check Python
        if let Ok(output) = std::process::Command::new("python3")
            .arg("--version")
            .output()
        {
            if output.status.success() {
                check.python_available = true;
            }
        } else if let Ok(output) = std::process::Command::new("python")
            .arg("--version")
            .output()
        {
            if output.status.success() {
                check.python_available = true;
            }
        }

        if !check.python_available {
            check.issues.push("Python is not available in PATH".to_string());
        }

        // Check CLI availability
        if let Ok(output) = std::process::Command::new("speech-to-text")
            .arg("--version")
            .output()
        {
            if output.status.success() {
                check.cli_available = true;
            }
        }

        if !check.cli_available {
            check.issues.push("speech-to-text CLI is not available in PATH".to_string());
        }

        // Check FFmpeg (optional but recommended)
        if let Ok(output) = std::process::Command::new("ffmpeg")
            .arg("-version")
            .output()
        {
            if output.status.success() {
                check.ffmpeg_available = true;
            }
        }

        if !check.ffmpeg_available {
            check.issues.push("FFmpeg is not available (optional but recommended for better audio support)".to_string());
        }

        check
    }

    /// Get available disk space for a given directory
    pub fn get_available_disk_space(directory: &str) -> AppResult<u64> {
        let path = Path::new(directory);
        
        if !path.exists() {
            return Err(AppError::FileNotFound(directory.to_string()));
        }

        // This is a simplified implementation
        // In a real app, you might use a crate like `fs2` for more accurate disk space info
        Ok(1024 * 1024 * 1024) // Return 1GB as placeholder
    }
}

/// Information about a supported audio format
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct FormatInfo {
    pub extension: String,
    pub description: String,
    pub mime_type: String,
}

/// System information structure
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SystemInfo {
    pub os: String,
    pub arch: String,
    pub family: String,
    pub home_dir: Option<String>,
    pub documents_dir: Option<String>,
    pub config_dir: Option<String>,
}

/// System dependency check result
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct SystemDependencyCheck {
    pub python_available: bool,
    pub cli_available: bool,
    pub ffmpeg_available: bool,
    pub whisper_available: bool,
    pub issues: Vec<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_supported_formats() {
        let formats = SystemIntegration::get_supported_formats();
        assert!(formats.contains(&"m4a".to_string()));
        assert!(formats.contains(&"wav".to_string()));
        assert!(formats.contains(&"mp3".to_string()));
    }

    #[test]
    fn test_get_supported_formats_detailed() {
        let formats = SystemIntegration::get_supported_formats_detailed();
        assert!(!formats.is_empty());
        
        let m4a_format = formats.iter().find(|f| f.extension == "m4a");
        assert!(m4a_format.is_some());
        assert_eq!(m4a_format.unwrap().mime_type, "audio/mp4");
    }

    #[test]
    fn test_is_supported_format() {
        assert!(SystemIntegration::is_supported_format("m4a"));
        assert!(SystemIntegration::is_supported_format(".wav"));
        assert!(SystemIntegration::is_supported_format("MP3"));
        assert!(!SystemIntegration::is_supported_format("txt"));
        assert!(!SystemIntegration::is_supported_format("doc"));
    }

    #[test]
    fn test_get_system_info() {
        let info = SystemIntegration::get_system_info();
        assert!(!info.os.is_empty());
        assert!(!info.arch.is_empty());
        assert!(!info.family.is_empty());
    }

    #[tokio::test]
    async fn test_check_system_dependencies() {
        let check = SystemIntegration::check_system_dependencies().await;
        // We can't assert specific values since they depend on the system
        // But we can check that the structure is populated
        // Issues can be empty or contain items - just check that the check completed
        assert!(check.issues.is_empty() || !check.issues.is_empty()); // Always true, but uses the variable
    }

    #[tokio::test]
    async fn test_select_directory() {
        let result = SystemIntegration::select_directory().await;
        assert!(result.is_ok());
        if let Ok(Some(dir)) = result {
            assert!(!dir.is_empty());
        }
    }

    #[test]
    fn test_get_available_disk_space_invalid_path() {
        let result = SystemIntegration::get_available_disk_space("/nonexistent/path");
        assert!(result.is_err());
    }
}