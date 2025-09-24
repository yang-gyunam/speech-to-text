use crate::error::{AppError, AppResult};
use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MacOSIntegration {
    pub dock_badge_enabled: bool,
    pub menu_bar_enabled: bool,
    pub notifications_enabled: bool,
}

impl Default for MacOSIntegration {
    fn default() -> Self {
        Self {
            dock_badge_enabled: true,
            menu_bar_enabled: true,
            notifications_enabled: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationOptions {
    pub title: String,
    pub body: String,
    pub sound: Option<String>,
    pub identifier: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DockBadgeInfo {
    pub count: Option<u32>,
    pub text: Option<String>,
    pub progress: Option<f64>,
}

impl MacOSIntegration {
    pub fn new() -> Self {
        Self::default()
    }

    /// Set dock badge with count or text
    pub fn set_dock_badge(&self, badge_info: DockBadgeInfo) -> AppResult<()> {
        #[cfg(target_os = "macos")]
        {
            // For now, we'll use a simple approach without direct Cocoa calls
            // This can be enhanced later with proper macOS integration
            if let Some(count) = badge_info.count {
                println!("Setting dock badge count: {}", count);
            } else if let Some(text) = badge_info.text {
                println!("Setting dock badge text: {}", text);
            }
        }
        
        #[cfg(not(target_os = "macos"))]
        {
            // No-op on non-macOS platforms
            let _ = badge_info;
        }
        
        Ok(())
    }

    /// Clear dock badge
    pub fn clear_dock_badge(&self) -> AppResult<()> {
        self.set_dock_badge(DockBadgeInfo {
            count: None,
            text: None,
            progress: None,
        })
    }

    /// Show system notification
    pub fn show_notification(&self, options: NotificationOptions) -> AppResult<()> {
        // Use tauri-plugin-notification for cross-platform notifications
        println!("Notification: {} - {}", options.title, options.body);
        
        // This will be handled by the frontend using the tauri notification plugin
        Ok(())
    }

    /// Register file associations (requires app restart to take effect)
    pub fn register_file_associations(&self) -> AppResult<()> {
        #[cfg(target_os = "macos")]
        {
            // File associations are handled by the bundle configuration
            // This function can be used for runtime verification or updates
            self.verify_file_associations()
        }
        
        #[cfg(not(target_os = "macos"))]
        {
            Ok(())
        }
    }

    /// Verify that file associations are properly registered
    pub fn verify_file_associations(&self) -> AppResult<()> {
        #[cfg(target_os = "macos")]
        {
            let supported_extensions = vec!["m4a", "wav", "mp3", "aac", "flac"];
            let bundle_id = "com.yang-gyunam.speech-to-text";
            
            for ext in supported_extensions {
                let output = Command::new("duti")
                    .args(&["-x", ext])
                    .output();
                    
                match output {
                    Ok(result) => {
                        let output_str = String::from_utf8_lossy(&result.stdout);
                        if !output_str.contains(bundle_id) {
                            println!("Warning: File association for .{} may not be registered", ext);
                        }
                    }
                    Err(_) => {
                        // duti not available, skip verification
                        break;
                    }
                }
            }
        }
        
        Ok(())
    }

    /// Set application as default handler for supported audio formats
    pub fn set_as_default_handler(&self) -> AppResult<()> {
        #[cfg(target_os = "macos")]
        {
            let bundle_id = "com.yang-gyunam.speech-to-text";
            let supported_extensions = vec!["m4a", "wav", "mp3", "aac", "flac"];
            
            for ext in supported_extensions {
                let _output = Command::new("duti")
                    .args(&["-s", bundle_id, ext, "editor"])
                    .output();
                // Ignore errors as duti might not be available
            }
        }
        
        Ok(())
    }

    /// Get current file association status
    pub fn get_file_association_status(&self) -> AppResult<Vec<FileAssociationStatus>> {
        let mut status_list = Vec::new();
        let supported_extensions = vec!["m4a", "wav", "mp3", "aac", "flac"];
        
        #[cfg(target_os = "macos")]
        {
            let bundle_id = "com.yang-gyunam.speech-to-text";
            
            for ext in supported_extensions {
                let output = Command::new("duti")
                    .args(&["-x", ext])
                    .output();
                    
                let is_associated = match output {
                    Ok(result) => {
                        let output_str = String::from_utf8_lossy(&result.stdout);
                        output_str.contains(bundle_id)
                    }
                    Err(_) => false,
                };
                
                status_list.push(FileAssociationStatus {
                    extension: ext.to_string(),
                    is_associated,
                    current_handler: None,
                });
            }
        }
        
        #[cfg(not(target_os = "macos"))]
        {
            for ext in supported_extensions {
                status_list.push(FileAssociationStatus {
                    extension: ext.to_string(),
                    is_associated: false,
                    current_handler: None,
                });
            }
        }
        
        Ok(status_list)
    }

    /// Handle file opened from Finder (via file association)
    pub fn handle_file_opened(&self, file_path: String) -> AppResult<()> {
        // This will be called when a file is opened via file association
        // The actual handling should be done by the main application
        println!("File opened via association: {}", file_path);
        Ok(())
    }

    /// Set dock progress indicator
    pub fn set_dock_progress(&self, progress: f64) -> AppResult<()> {
        #[cfg(target_os = "macos")]
        {
            // For now, we'll use a simple approach without direct Cocoa calls
            if progress >= 0.0 && progress <= 1.0 {
                println!("Setting dock progress: {:.1}%", progress * 100.0);
            } else {
                println!("Clearing dock progress");
            }
        }
        
        #[cfg(not(target_os = "macos"))]
        {
            let _ = progress;
        }
        
        Ok(())
    }

    /// Clear dock progress indicator
    pub fn clear_dock_progress(&self) -> AppResult<()> {
        self.set_dock_progress(-1.0)
    }

    /// Check if running on macOS
    pub fn is_macos() -> bool {
        cfg!(target_os = "macos")
    }

    /// Get macOS version information
    pub fn get_macos_version(&self) -> AppResult<String> {
        #[cfg(target_os = "macos")]
        {
            let output = Command::new("sw_vers")
                .args(&["-productVersion"])
                .output()
                .map_err(|e| AppError::SystemError(format!("Failed to get macOS version: {}", e)))?;
                
            let version = String::from_utf8_lossy(&output.stdout).trim().to_string();
            Ok(version)
        }
        
        #[cfg(not(target_os = "macos"))]
        {
            Err(AppError::SystemError("Not running on macOS".to_string()))
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileAssociationStatus {
    pub extension: String,
    pub is_associated: bool,
    pub current_handler: Option<String>,
}

