use crate::error::{AppError, AppResult};
use crate::models::{AppSettings, ProcessingProgress, ProcessingStage, TranscriptionResult, TranscriptionMetadata, AudioInfo};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::process::Stdio;
use std::sync::Arc;
use tokio::time::{timeout, Duration};
use tokio_util::sync::CancellationToken;
use regex::Regex;

/// CLI execution result
#[derive(Debug, Serialize, Deserialize)]
pub struct CliResult {
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
    pub exit_code: i32,
}

/// Progress callback type
pub type ProgressCallback = Arc<dyn Fn(ProcessingProgress) + Send + Sync>;

/// CLI integration manager
pub struct CliManager {
    use_sidecar: bool,
    timeout_duration: Duration,
}

impl Default for CliManager {
    fn default() -> Self {
        Self {
            use_sidecar: true, // Always try sidecar first in production
            timeout_duration: Duration::from_secs(3600), // 1 hour timeout
        }
    }
}

impl CliManager {
    /// Create a new CLI manager
    pub fn new() -> Self {
        Self::default()
    }

    /// Create a new CLI manager for development (without sidecar)
    pub fn new_dev() -> Self {
        Self {
            use_sidecar: false,
            timeout_duration: Duration::from_secs(3600),
        }
    }

    /// Set timeout duration for CLI operations
    pub fn with_timeout(mut self, timeout: Duration) -> Self {
        self.timeout_duration = timeout;
        self
    }

    /// Check if the CLI is available and working
    pub async fn check_cli_availability(&self) -> AppResult<bool> {
        if self.use_sidecar {
            // Use bundled sidecar - find the correct path
            let cli_path = self.find_sidecar_path()?;
            let output = tokio::process::Command::new(&cli_path)
                .arg("--version")
                .output()
                .await
                .map_err(|e| AppError::CliError(format!("Failed to execute sidecar: {}", e)))?;

            Ok(output.status.success())
        } else {
            // Development fallback - try to find CLI in development paths
            self.check_cli_availability_dev().await
        }
    }

    /// Find the sidecar binary path
    fn find_sidecar_path(&self) -> AppResult<String> {
        // Create debug log file on Desktop for easy access
        let desktop_path = dirs::desktop_dir().unwrap_or_else(|| std::env::temp_dir());
        let log_path = desktop_path.join("speechtotext_debug.log");
        let mut debug_log = String::new();
        
        // In production, the sidecar should be in the same directory as the main executable
        if let Ok(exe_path) = std::env::current_exe() {
            let msg = format!("🔍 Current executable path: {:?}\n", exe_path);
            println!("{}", msg);
            debug_log.push_str(&msg);
            
            if let Some(parent) = exe_path.parent() {
                let msg = format!("🔍 Parent directory: {:?}\n", parent);
                println!("{}", msg);
                debug_log.push_str(&msg);
                
                // List all files in the parent directory for debugging
                if let Ok(entries) = std::fs::read_dir(parent) {
                    let msg = "🔍 Files in parent directory:\n";
                    println!("{}", msg);
                    debug_log.push_str(msg);
                    
                    for entry in entries {
                        if let Ok(entry) = entry {
                            let msg = format!("  - {:?}\n", entry.file_name());
                            println!("{}", msg);
                            debug_log.push_str(&msg);
                        }
                    }
                }
                
                let sidecar_path = parent.join("speech-to-text");
                let msg = format!("🔍 Looking for sidecar at: {:?}\n", sidecar_path);
                println!("{}", msg);
                debug_log.push_str(&msg);
                
                if sidecar_path.exists() {
                    if let Some(path_str) = sidecar_path.to_str() {
                        let msg = format!("🟢 Found sidecar at: {}\n", path_str);
                        println!("{}", msg);
                        debug_log.push_str(&msg);
                        
                        // Check if the file is executable
                        if let Ok(metadata) = std::fs::metadata(&sidecar_path) {
                            let msg = format!("🔍 Sidecar file permissions: {:?}\n", metadata.permissions());
                            println!("{}", msg);
                            debug_log.push_str(&msg);
                        }
                        
                        // Write debug log to file
                        let _ = std::fs::write(&log_path, &debug_log);
                        
                        return Ok(path_str.to_string());
                    }
                } else {
                    let msg = format!("❌ Sidecar not found at expected path: {:?}\n", sidecar_path);
                    println!("{}", msg);
                    debug_log.push_str(&msg);
                }
            }
        } else {
            let msg = "❌ Failed to get current executable path\n";
            println!("{}", msg);
            debug_log.push_str(msg);
        }
        
        // Write debug log to file
        let _ = std::fs::write(&log_path, &debug_log);
        
        Err(AppError::CliError("Sidecar binary not found".to_string()))
    }

    /// Development version of CLI availability check
    async fn check_cli_availability_dev(&self) -> AppResult<bool> {
        use tokio::process::Command as AsyncCommand;
        
        let cli_command = self.find_dev_cli_command();
        let output = timeout(
            Duration::from_secs(10),
            AsyncCommand::new(&cli_command)
                .arg("--version")
                .output()
        ).await
        .map_err(|_| AppError::CliError("CLI command timed out".to_string()))?
        .map_err(|e| AppError::CliError(format!("Failed to execute CLI: {}", e)))?;

        Ok(output.status.success())
    }

    /// Find CLI command for development
    fn find_dev_cli_command(&self) -> String {
        let current_dir = std::env::current_dir().unwrap_or_else(|_| std::path::PathBuf::from("."));

        // Check different possible paths for virtual environment
        let venv_paths = vec![
            current_dir.join("../venv/bin/speech-to-text"),  // From tauri-gui-app/
            current_dir.join("../../venv/bin/speech-to-text"), // From tauri-gui-app/src-tauri/
            current_dir.join("venv/bin/speech-to-text"),     // From project root
            current_dir.join("../../garbage/venv/bin/speech-to-text"), // From garbage venv
        ];

        for venv_path in venv_paths {
            if venv_path.exists() {
                if let Some(path_str) = venv_path.to_str() {
                    println!("🟢 Found speech-to-text at: {}", path_str);
                    return path_str.to_string();
                }
            }
        }

        // Fallback to system PATH
        println!("⚠️ Using fallback: speech-to-text from PATH");
        "speech-to-text".to_string()
    }

    /// Get CLI version information
    pub async fn get_cli_version(&self) -> AppResult<String> {
        if self.use_sidecar {
            let cli_path = self.find_sidecar_path()?;
            let output = tokio::process::Command::new(&cli_path)
                .arg("--version")
                .output()
                .await
                .map_err(|e| AppError::CliError(format!("Failed to get CLI version: {}", e)))?;

            if output.status.success() {
                Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
            } else {
                Err(AppError::CliError(
                    String::from_utf8_lossy(&output.stderr).to_string()
                ))
            }
        } else {
            self.get_cli_version_dev().await
        }
    }

    /// Development version of CLI version check
    async fn get_cli_version_dev(&self) -> AppResult<String> {
        use tokio::process::Command as AsyncCommand;
        
        let cli_command = self.find_dev_cli_command();
        let output = timeout(
            Duration::from_secs(10),
            AsyncCommand::new(&cli_command)
                .arg("--version")
                .output()
        ).await
        .map_err(|_| AppError::CliError("CLI version check timed out".to_string()))?
        .map_err(|e| AppError::CliError(format!("Failed to get CLI version: {}", e)))?;

        if output.status.success() {
            Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
        } else {
            Err(AppError::CliError(
                String::from_utf8_lossy(&output.stderr).to_string()
            ))
        }
    }

    /// Process a single audio file using the CLI
    pub async fn process_file(
        &self,
        file_path: &str,
        settings: &AppSettings,
        progress_callback: Option<ProgressCallback>,
    ) -> AppResult<TranscriptionResult> {
        self.process_file_with_cancellation(file_path, settings, progress_callback, None).await
    }

    /// Process a single audio file with cancellation support
    pub async fn process_file_with_cancellation(
        &self,
        file_path: &str,
        settings: &AppSettings,
        progress_callback: Option<ProgressCallback>,
        cancellation_token: Option<CancellationToken>,
    ) -> AppResult<TranscriptionResult> {
        println!("🔥 process_file_with_cancellation started with: {}", file_path);

        // Validate file exists
        if !std::path::Path::new(file_path).exists() {
            println!("🔥 File not found: {}", file_path);
            return Err(AppError::FileNotFound(file_path.to_string()));
        }
        println!("🔥 File exists, building CLI command");

        // Build CLI command arguments - back to original approach
        let mut args = vec![
            file_path.to_string(),
            "--language".to_string(), 
            settings.language.clone(),
            "--model-size".to_string(), 
            settings.model_size.to_string(),
        ];

        println!("🔥 CLI command args: {:?}", args);

        if settings.include_metadata {
            args.push("--include-metadata".to_string());
        }

        // Check for cancellation before starting
        if let Some(ref token) = cancellation_token {
            if token.is_cancelled() {
                return Err(AppError::ProcessingError("Processing was cancelled".to_string()));
            }
        }

        // Send initial progress
        if let Some(ref callback) = progress_callback {
            callback(ProcessingProgress {
                stage: ProcessingStage::Initializing,
                progress: 0.0,
                current_file: Some(file_path.to_string()),
                timestamp: Utc::now(),
                message: Some("Starting transcription...".to_string()),
                job_id: None,
                file_index: None,
                total_files: None,
                can_cancel: cancellation_token.is_some(),
            });
        }

        // Execute command with timeout
        let start_time = std::time::Instant::now();
        println!("🔥 About to spawn CLI process");

        if self.use_sidecar {
            // Use Tauri sidecar
            self.process_with_sidecar(args, file_path, settings, progress_callback, cancellation_token, start_time).await
        } else {
            // Use development CLI
            self.process_with_dev_cli(args, file_path, settings, progress_callback, cancellation_token, start_time).await
        }
    }

    /// Process file using Tauri sidecar
    async fn process_with_sidecar(
        &self,
        args: Vec<String>,
        file_path: &str,
        settings: &AppSettings,
        progress_callback: Option<ProgressCallback>,
        cancellation_token: Option<CancellationToken>,
        start_time: std::time::Instant,
    ) -> AppResult<TranscriptionResult> {
        use tokio::io::{AsyncBufReadExt, BufReader};
        
        let cli_path = self.find_sidecar_path()?;
        
        // Test CLI before processing
        println!("🔥 Testing CLI before processing...");
        let test_result = tokio::process::Command::new(&cli_path)
            .arg("--version")
            .output()
            .await;
            
        match test_result {
            Ok(output) => {
                println!("🔥 CLI test output: {}", String::from_utf8_lossy(&output.stdout));
                if !output.status.success() {
                    println!("🔥 CLI test stderr: {}", String::from_utf8_lossy(&output.stderr));
                    return Err(AppError::CliError(format!("CLI test failed with exit code: {:?}", output.status.code())));
                }
            }
            Err(e) => {
                println!("🔥 CLI test failed: {}", e);
                return Err(AppError::CliError(format!("CLI test failed: {}", e)));
            }
        }
        
        // Create a safe working directory for CLI execution
        let work_dir = dirs::cache_dir()
            .unwrap_or_else(|| std::env::temp_dir())
            .join("SpeechToText");
        
        // Ensure the directory exists
        let _ = std::fs::create_dir_all(&work_dir);
        
        let mut cmd = tokio::process::Command::new(&cli_path);
        
        // Build enhanced PATH with common ffmpeg locations
        let current_path = std::env::var("PATH").unwrap_or_else(|_| "/usr/bin:/bin:/usr/sbin:/sbin".to_string());
        let enhanced_path = format!(
            "{}:/usr/local/bin:/opt/homebrew/bin:/usr/local/Cellar/ffmpeg/*/bin:/opt/local/bin", 
            current_path
        );
        
        cmd.args(&args)
           .stdout(Stdio::piped())
           .stderr(Stdio::piped())
           .current_dir(&work_dir) // Set working directory outside app bundle
           .env("TMPDIR", work_dir.to_string_lossy().to_string()) // Set temp directory
           .env("HOME", dirs::home_dir().unwrap_or_else(|| std::env::temp_dir()).to_string_lossy().to_string()) // Ensure HOME is set
           .env("PATH", enhanced_path); // Enhanced PATH with ffmpeg locations

        println!("🔥 About to spawn sidecar with command: {} {:?}", cli_path, args);
        println!("🔥 Working directory: {:?}", work_dir);

        // Log to desktop for debugging with enhanced information
        let desktop_path = dirs::desktop_dir().unwrap_or_else(|| std::env::temp_dir());
        let cli_debug_log_path = desktop_path.join("speechtotext_cli_execution.log");
        
        // Check if CLI file exists and is executable
        let cli_file_info = if std::path::Path::new(&cli_path).exists() {
            match std::fs::metadata(&cli_path) {
                Ok(metadata) => format!("CLI file exists, size: {} bytes, permissions: {:?}", metadata.len(), metadata.permissions()),
                Err(e) => format!("CLI file exists but metadata error: {}", e),
            }
        } else {
            "CLI file does not exist!".to_string()
        };
        
        // Check if input file exists
        let input_file_info = if std::path::Path::new(file_path).exists() {
            match std::fs::metadata(file_path) {
                Ok(metadata) => format!("Input file exists, size: {} bytes", metadata.len()),
                Err(e) => format!("Input file exists but metadata error: {}", e),
            }
        } else {
            "Input file does not exist!".to_string()
        };
        
        let cli_debug_log = format!(
            "CLI Execution Debug - {}\n\
            Command: {}\n\
            CLI File Info: {}\n\
            Args: {:?}\n\
            Working Directory: {:?}\n\
            File Path: {}\n\
            Input File Info: {}\n\
            Settings: {:?}\n\
            Environment Variables:\n\
            - TMPDIR: {:?}\n\
            - HOME: {:?}\n\
            - PATH: {:?}\n\n",
            chrono::Utc::now().format("%Y-%m-%d %H:%M:%S"),
            cli_path, 
            cli_file_info,
            args, 
            work_dir, 
            file_path,
            input_file_info,
            settings,
            std::env::var("TMPDIR").unwrap_or_else(|_| "Not set".to_string()),
            std::env::var("HOME").unwrap_or_else(|_| "Not set".to_string()),
            std::env::var("PATH").unwrap_or_else(|_| "Not set".to_string())
        );
        let _ = std::fs::write(&cli_debug_log_path, &cli_debug_log);

        let mut child = cmd.spawn()
            .map_err(|e| {
                println!("🔥 Failed to spawn sidecar process: {}", e);
                AppError::CliError(format!("Failed to spawn sidecar process: {}", e))
            })?;

        println!("🔥 Sidecar process spawned successfully");

        // Monitor stdout and stderr for progress
        if let Some(callback) = progress_callback {
            let stdout = child.stdout.take().ok_or_else(|| AppError::CliError("Failed to capture stdout".to_string()))?;
            let stderr = child.stderr.take().ok_or_else(|| AppError::CliError("Failed to capture stderr".to_string()))?;
            
            let file_path_clone = file_path.to_string();
            let callback_clone = callback.clone();
            tokio::spawn(async move {
                let mut lines = BufReader::new(stdout).lines();
                while let Ok(Some(line)) = lines.next_line().await {
                    Self::parse_and_emit_progress(&line, &callback_clone, &file_path_clone);
                }
            });

            let file_path_clone_2 = file_path.to_string();
            let callback_clone_2 = callback.clone();
            tokio::spawn(async move {
                let mut lines = BufReader::new(stderr).lines();
                while let Ok(Some(line)) = lines.next_line().await {
                    Self::parse_and_emit_progress(&line, &callback_clone_2, &file_path_clone_2);
                }
            });

            // Send completion status
            let status = if let Some(ref token) = cancellation_token {
                tokio::select! {
                    result = timeout(self.timeout_duration, async {
                        // Check for cancellation before waiting
                        if token.is_cancelled() {
                            let _ = child.kill().await;
                            return Err(std::io::Error::new(std::io::ErrorKind::Interrupted, "Cancelled"));
                        }
                        println!("🔥 Calling child.wait()");
                        child.wait().await
                    }) => {
                        println!("🔥 Sidecar process completed, processing result");
                        result
                            .map_err(|e| {
                                println!("🔥 Sidecar process timed out: {}", e);
                                AppError::CliError("Sidecar process timed out".to_string())
                            })?
                            .map_err(|e| {
                                println!("🔥 Sidecar process failed: {}", e);
                                AppError::CliError(format!("Sidecar process failed: {}", e))
                            })?
                    }
                    _ = token.cancelled() => {
                        println!("🔥 Processing was cancelled");
                        return Err(AppError::ProcessingError("Processing was cancelled".to_string()));
                    }
                }
            } else {
                println!("🔥 Calling timeout with child.wait()");
                timeout(self.timeout_duration, child.wait()).await
                    .map_err(|e| {
                        println!("🔥 Sidecar process timed out: {}", e);
                        AppError::CliError("Sidecar process timed out".to_string())
                    })?
                    .map_err(|e| {
                        println!("🔥 Sidecar process failed: {}", e);
                        AppError::CliError(format!("Sidecar process failed: {}", e))
                    })?
            };

            println!("🔥 Sidecar process output received");

            let processing_time = start_time.elapsed().as_secs_f64();

            if status.success() {
                callback(ProcessingProgress {
                    stage: ProcessingStage::Saving,
                    progress: 100.0,
                    current_file: Some(file_path.to_string()),
                    timestamp: Utc::now(),
                    message: Some("Transcription completed!".to_string()),
                    job_id: None,
                    file_index: None,
                    total_files: None,
                    can_cancel: false,
                });

                // Read output files since CLI completed successfully
                self.parse_cli_completion(file_path, processing_time, settings).await
            } else {
                let mut error_log = String::new();
                
                let msg = format!("🔥 Sidecar execution failed!\n");
                println!("{}", msg);
                error_log.push_str(&msg);
                
                let msg = format!("🔥 Exit code: {:?}\n", status.code());
                println!("{}", msg);
                error_log.push_str(&msg);
                
                let msg = format!("🔥 Command used: {}\n", cli_path);
                println!("{}", msg);
                error_log.push_str(&msg);
                
                let msg = format!("🔥 File path: {}\n", file_path);
                println!("{}", msg);
                error_log.push_str(&msg);
                
                let msg = format!("🔥 Args: {:?}\n", args);
                println!("{}", msg);
                error_log.push_str(&msg);

                // Try to capture stderr for more details
                let stderr_output = tokio::process::Command::new(&cli_path)
                    .args(&args)
                    .output()
                    .await;
                    
                match stderr_output {
                    Ok(output) => {
                        let msg = format!("🔥 CLI stderr: {}\n", String::from_utf8_lossy(&output.stderr));
                        println!("{}", msg);
                        error_log.push_str(&msg);
                        
                        let msg = format!("🔥 CLI stdout: {}\n", String::from_utf8_lossy(&output.stdout));
                        println!("{}", msg);
                        error_log.push_str(&msg);
                    }
                    Err(e) => {
                        let msg = format!("🔥 Failed to capture CLI output: {}\n", e);
                        println!("{}", msg);
                        error_log.push_str(&msg);
                    }
                }

                // Write error log to file on Desktop for easy access
                let desktop_path = dirs::desktop_dir().unwrap_or_else(|| std::env::temp_dir());
                let error_log_path = desktop_path.join("speechtotext_error.log");
                let _ = std::fs::write(&error_log_path, &error_log);

                Err(AppError::CliError(format!("CLI execution failed with exit code: {:?}", status.code())))
            }
        } else {
            // No progress callback provided, just wait for the process to finish
            let status = child.wait().await.map_err(|e| AppError::CliError(format!("Sidecar process failed: {}", e)))?;
            let processing_time = start_time.elapsed().as_secs_f64();
            if status.success() {
                self.parse_cli_completion(file_path, processing_time, settings).await
            } else {
                Err(AppError::CliError(format!("CLI execution failed with exit code: {:?}", status.code())))
            }
        }
    }

    /// Process file using development CLI
    async fn process_with_dev_cli(
        &self,
        args: Vec<String>,
        file_path: &str,
        settings: &AppSettings,
        progress_callback: Option<ProgressCallback>,
        cancellation_token: Option<CancellationToken>,
        start_time: std::time::Instant,
    ) -> AppResult<TranscriptionResult> {
        use tokio::process::Command as AsyncCommand;
        use tokio::io::{AsyncBufReadExt, BufReader};

        let cli_command = self.find_dev_cli_command();
        
        // Create a safe working directory for CLI execution
        let work_dir = dirs::cache_dir()
            .unwrap_or_else(|| std::env::temp_dir())
            .join("SpeechToText");
        
        // Ensure the directory exists
        let _ = std::fs::create_dir_all(&work_dir);
        
        let mut cmd = AsyncCommand::new(&cli_command);
        cmd.args(&args)
           .stdout(Stdio::piped())
           .stderr(Stdio::piped())
           .current_dir(&work_dir) // Set working directory outside app bundle
           .env("TMPDIR", work_dir.to_string_lossy().to_string()) // Set temp directory
           .env("HOME", dirs::home_dir().unwrap_or_else(|| std::env::temp_dir()).to_string_lossy().to_string()); // Ensure HOME is set

        let mut child = cmd.spawn()
            .map_err(|e| {
                println!("🔥 Failed to spawn CLI process: {}", e);
                AppError::CliError(format!("Failed to spawn CLI process: {}", e))
            })?;

        println!("🔥 CLI process spawned successfully");

        // Monitor stdout and stderr for progress
        if let Some(callback) = progress_callback {
            let stdout = child.stdout.take().ok_or_else(|| AppError::CliError("Failed to capture stdout".to_string()))?;
            let stderr = child.stderr.take().ok_or_else(|| AppError::CliError("Failed to capture stderr".to_string()))?;
            
            let file_path_clone = file_path.to_string();
            let callback_clone = callback.clone();
            tokio::spawn(async move {
                let mut lines = BufReader::new(stdout).lines();
                while let Ok(Some(line)) = lines.next_line().await {
                    Self::parse_and_emit_progress(&line, &callback_clone, &file_path_clone);
                }
            });

            let file_path_clone_2 = file_path.to_string();
            let callback_clone_2 = callback.clone();
            tokio::spawn(async move {
                let mut lines = BufReader::new(stderr).lines();
                while let Ok(Some(line)) = lines.next_line().await {
                    Self::parse_and_emit_progress(&line, &callback_clone_2, &file_path_clone_2);
                }
            });

            // Send completion status
            let status = if let Some(ref token) = cancellation_token {
                tokio::select! {
                    result = timeout(self.timeout_duration, async {
                        // Check for cancellation before waiting
                        if token.is_cancelled() {
                            let _ = child.kill().await;
                            return Err(std::io::Error::new(std::io::ErrorKind::Interrupted, "Cancelled"));
                        }
                        println!("🔥 Calling child.wait()");
                        child.wait().await
                    }) => {
                        println!("🔥 CLI process completed, processing result");
                        result
                            .map_err(|e| {
                                println!("🔥 CLI process timed out: {}", e);
                                AppError::CliError("CLI process timed out".to_string())
                            })?
                            .map_err(|e| {
                                println!("🔥 CLI process failed: {}", e);
                                AppError::CliError(format!("CLI process failed: {}", e))
                            })?
                    }
                    _ = token.cancelled() => {
                        println!("🔥 Processing was cancelled");
                        return Err(AppError::ProcessingError("Processing was cancelled".to_string()));
                    }
                }
            } else {
                println!("🔥 Calling timeout with child.wait()");
                timeout(self.timeout_duration, child.wait()).await
                    .map_err(|e| {
                        println!("🔥 CLI process timed out: {}", e);
                        AppError::CliError("CLI process timed out".to_string())
                    })?
                    .map_err(|e| {
                        println!("🔥 CLI process failed: {}", e);
                        AppError::CliError(format!("CLI process failed: {}", e))
                    })?
            };

            println!("🔥 CLI process output received");

            let processing_time = start_time.elapsed().as_secs_f64();

            if status.success() {
                callback(ProcessingProgress {
                    stage: ProcessingStage::Saving,
                    progress: 100.0,
                    current_file: Some(file_path.to_string()),
                    timestamp: Utc::now(),
                    message: Some("Transcription completed!".to_string()),
                    job_id: None,
                    file_index: None,
                    total_files: None,
                    can_cancel: false,
                });

                // Read output files since CLI completed successfully
                self.parse_cli_completion(file_path, processing_time, settings).await
            } else {
                println!("🔥 CLI execution failed!");
                println!("🔥 Exit code: {:?}", status.code());
                println!("🔥 Command used: {}", cli_command);
                println!("🔥 File path: {}", file_path);

                // Try to run a simple test to see if CLI is accessible
                if let Ok(test_output) = std::process::Command::new(&cli_command)
                    .arg("--version")
                    .output() {
                    println!("🔥 CLI version test output: {}", String::from_utf8_lossy(&test_output.stdout));
                    println!("🔥 CLI version test stderr: {}", String::from_utf8_lossy(&test_output.stderr));
                    println!("🔥 CLI version test success: {}", test_output.status.success());
                } else {
                    println!("🔥 Failed to run CLI version test");
                }

                Err(AppError::CliError(format!("CLI execution failed with exit code: {:?}", status.code())))
            }
        } else {
            // No progress callback provided, just wait for the process to finish
            let status = child.wait().await.map_err(|e| AppError::CliError(format!("CLI process failed: {}", e)))?;
            let processing_time = start_time.elapsed().as_secs_f64();
            if status.success() {
                self.parse_cli_completion(file_path, processing_time, settings).await
            } else {
                Err(AppError::CliError(format!("CLI execution failed with exit code: {:?}", status.code())))
            }
        }
    }

    /// Process multiple files in batch
    pub async fn process_batch(
        &self,
        file_paths: &[String],
        settings: &AppSettings,
        progress_callback: Option<ProgressCallback>,
    ) -> AppResult<Vec<TranscriptionResult>> {
        let mut results = Vec::new();
        let total_files = file_paths.len();

        for (index, file_path) in file_paths.iter().enumerate() {
            // Update batch progress
            if let Some(ref callback) = progress_callback {
                let batch_progress = (index as f64 / total_files as f64) * 100.0;
                callback(ProcessingProgress {
                    stage: ProcessingStage::Initializing,
                    progress: batch_progress,
                    current_file: Some(file_path.clone()),
                    timestamp: Utc::now(),
                    message: Some(format!("Processing file {} of {}", index + 1, total_files)),
                    job_id: None,
                    file_index: Some(index),
                    total_files: Some(total_files),
                    can_cancel: true,
                });
            }

            // Process individual file
            match self.process_file(file_path, settings, progress_callback.clone()).await {
                Ok(result) => results.push(result),
                Err(e) => {
                    // Log error but continue with other files
                    eprintln!("Failed to process {}: {}", file_path, e);
                    // Could optionally collect errors and return them
                }
            }
        }

        Ok(results)
    }

    /// Monitor processing progress (simulated for now)
    pub async fn monitor_progress(&self, callback: ProgressCallback, file_path: &str) {
        self.monitor_progress_with_cancellation(callback, file_path.to_string(), None).await;
    }

    /// Monitor processing progress with cancellation support
    pub async fn monitor_progress_with_cancellation(
        &self, 
        callback: ProgressCallback, 
        file_path: String, 
        cancellation_token: Option<CancellationToken>
    ) {
        Self::monitor_progress_with_cancellation_static(callback, file_path, cancellation_token).await;
    }

    /// Static version of monitor_progress_with_cancellation for use in spawned tasks
    async fn monitor_progress_with_cancellation_static(
        callback: ProgressCallback, 
        file_path: String, 
        cancellation_token: Option<CancellationToken>
    ) {
        let stages = [
            (ProcessingStage::LoadingModel, "Loading Whisper model...", 15.0),
            (ProcessingStage::Preprocessing, "Preprocessing audio...", 25.0),
            (ProcessingStage::Transcribing, "Transcribing audio...", 80.0),
            (ProcessingStage::Postprocessing, "Processing results...", 95.0),
            (ProcessingStage::Saving, "Saving transcription...", 100.0),
        ];

        for (stage, message, progress) in stages.iter() {
            // Check for cancellation
            if let Some(ref token) = cancellation_token {
                if token.is_cancelled() {
                    return;
                }
            }

            callback(ProcessingProgress {
                stage: stage.clone(),
                progress: *progress,
                current_file: Some(file_path.clone()),
                timestamp: Utc::now(),
                message: Some(message.to_string()),
                job_id: None,
                file_index: None,
                total_files: None,
                can_cancel: cancellation_token.is_some(),
            });

            // Simulate processing time with cancellation checks
            for _ in 0..10 {
                if let Some(ref token) = cancellation_token {
                    if token.is_cancelled() {
                        return;
                    }
                }
                tokio::time::sleep(Duration::from_millis(100)).await;
            }
        }
    }

    /// Parse CLI output and create TranscriptionResult
    #[allow(dead_code)]
    async fn parse_cli_output(
        &self,
        file_path: &str,
        output: &[u8],
        processing_time: f64,
        settings: &AppSettings,
    ) -> AppResult<TranscriptionResult> {
        let output_str = String::from_utf8_lossy(output);
        
        // For now, we'll create a basic result structure
        // In a real implementation, this would parse the actual CLI output format
        let audio_file = crate::utils::create_audio_file(file_path)?;
        let output_path = crate::utils::get_output_filename(file_path, &settings.output_directory)?;
        
        // Try to read the transcribed text from the output file
        let transcribed_text = if std::path::Path::new(&output_path).exists() {
            tokio::fs::read_to_string(&output_path).await
                .unwrap_or_else(|_| "Transcription completed but text could not be read".to_string())
        } else {
            // Fallback: extract text from CLI output if available
            output_str.trim().to_string()
        };

        Ok(TranscriptionResult {
            id: crate::utils::generate_id(),
            original_file: audio_file,
            transcribed_text,
            metadata: TranscriptionMetadata {
                language: settings.language.clone(),
                model_size: settings.model_size.to_string(),
                timestamp: Utc::now(),
                audio_info: AudioInfo {
                    duration: 0.0, // Would be extracted from CLI output
                    sample_rate: None,
                    channels: None,
                },
            },
            output_path,
            processing_time,
            confidence: None, // Would be extracted from CLI output if available
        })
    }

    /// Parse CLI completion by reading output files (instead of relying on stdout)
    async fn parse_cli_completion(
        &self,
        file_path: &str,
        processing_time: f64,
        settings: &AppSettings,
    ) -> AppResult<TranscriptionResult> {
        // Create a basic result structure by reading output files
        let audio_file = crate::utils::create_audio_file(file_path)?;
        
        // Since we're not specifying output-dir, files will be in the CLI working directory
        let work_dir = dirs::cache_dir()
            .unwrap_or_else(|| std::env::temp_dir())
            .join("SpeechToText");
        
        let base_name = std::path::Path::new(&audio_file.name)
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("output");
        
        let expected_output_path = work_dir.join(format!("{}_transcription.txt", base_name)).to_string_lossy().to_string();

        // Try to read the transcribed text from the output file
        // First try the exact expected path
        println!("🔥 Looking for output file at: {}", expected_output_path);
        
        // Log to desktop for debugging
        let mut debug_log = format!("🔥 Looking for output file at: {}\n", expected_output_path);
        
        // Also check the working directory where CLI was executed
        let work_dir = dirs::cache_dir()
            .unwrap_or_else(|| std::env::temp_dir())
            .join("SpeechToText");
        debug_log.push_str(&format!("🔥 CLI working directory: {:?}\n", work_dir));
        
        // List files in working directory
        if let Ok(work_entries) = std::fs::read_dir(&work_dir) {
            debug_log.push_str("🔥 Files in CLI working directory:\n");
            for entry in work_entries {
                if let Ok(entry) = entry {
                    if let Some(filename) = entry.file_name().to_str() {
                        debug_log.push_str(&format!("  - {}\n", filename));
                        
                        // If it's the output directory, list its contents too
                        if filename == "output" && entry.path().is_dir() {
                            debug_log.push_str("🔥 Contents of output directory:\n");
                            if let Ok(output_entries) = std::fs::read_dir(entry.path()) {
                                for output_entry in output_entries {
                                    if let Ok(output_entry) = output_entry {
                                        if let Some(output_filename) = output_entry.file_name().to_str() {
                                            debug_log.push_str(&format!("    - {}\n", output_filename));
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        let (transcribed_text, actual_output_path) = if std::path::Path::new(&expected_output_path).exists() {
            println!("🔥 Found exact output file");
            debug_log.push_str("🔥 Found exact output file\n");
            let text = tokio::fs::read_to_string(&expected_output_path).await
                .unwrap_or_else(|_| "Transcription completed but text could not be read".to_string());
            (text, expected_output_path)
        } else {
            // If exact path doesn't exist, look for files with timestamp suffixes
            let audio_file = crate::utils::create_audio_file(file_path)?;
            let base_name = std::path::Path::new(&audio_file.name)
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("output");

            // Look in multiple directories for files matching the pattern
            let search_dirs = vec![
                work_dir.clone(),                    // CLI working directory
                work_dir.join("output"),             // CLI output subdirectory
                dirs::home_dir().unwrap_or_else(|| std::path::PathBuf::from("/tmp")), // User home directory
            ];
            
            let mut found_file = None;
            
            for search_dir in search_dirs {
                debug_log.push_str(&format!("🔥 Searching in directory: {:?}\n", search_dir));
                
                if !search_dir.exists() {
                    debug_log.push_str("  Directory doesn't exist, skipping\n");
                    continue;
                }
                
                if let Ok(_entries) = std::fs::read_dir(&search_dir) {
                    debug_log.push_str("  Successfully read directory\n");
                    
                    // List all files in directory for debugging
                    if let Ok(all_entries) = std::fs::read_dir(&search_dir) {
                        debug_log.push_str("🔥 All files in search directory:\n");
                        for entry in all_entries {
                            if let Ok(entry) = entry {
                                if let Some(filename) = entry.file_name().to_str() {
                                    debug_log.push_str(&format!("  - {}\n", filename));
                                }
                            }
                        }
                    }
                    
                    let mut matching_files: Vec<_> = std::fs::read_dir(&search_dir)
                        .unwrap()
                        .filter_map(|entry| entry.ok())
                        .filter(|entry| {
                            if let Some(filename) = entry.file_name().to_str() {
                                debug_log.push_str(&format!("  Checking file: {}\n", filename));
                                
                                // Look for files with multiple patterns:
                                // 1. {base_name}_transcription_YYYYMMDDHHMM.txt (timestamp format from CLI)
                                // 2. {base_name}_transcription.txt (exact format)
                                // 3. {base_name}.txt (CLI default format)
                                
                                // Pattern 1: timestamp format (most common from CLI)
                                let transcription_timestamp_pattern = format!("{}_transcription_", base_name);
                                let timestamp_match = filename.starts_with(&transcription_timestamp_pattern) && filename.ends_with(".txt");
                                
                                // Pattern 2: exact format
                                let exact_transcription_pattern = format!("{}_transcription.txt", base_name);
                                let exact_match = filename == exact_transcription_pattern;
                                
                                // Pattern 3: simple format
                                let simple_pattern = format!("{}.txt", base_name);
                                let simple_match = filename == simple_pattern;
                                
                                // Pattern 4: any file containing the base name and "transcription"
                                let contains_match = filename.contains(base_name) && 
                                                   filename.contains("transcription") && 
                                                   filename.ends_with(".txt");
                                
                                let matches = timestamp_match || exact_match || simple_match || contains_match;
                                
                                if matches {
                                    debug_log.push_str(&format!("    ✅ MATCH: {}\n", filename));
                                } else {
                                    debug_log.push_str(&format!("    ❌ No match: {}\n", filename));
                                }
                                
                                matches
                            } else {
                                false
                            }
                        })
                        .collect();

                    // Sort by modification time (newest first)
                    matching_files.sort_by(|a, b| {
                        let time_a = a.metadata().and_then(|m| m.modified()).unwrap_or(std::time::SystemTime::UNIX_EPOCH);
                        let time_b = b.metadata().and_then(|m| m.modified()).unwrap_or(std::time::SystemTime::UNIX_EPOCH);
                        time_b.cmp(&time_a)
                    });

                    if let Some(latest_file) = matching_files.first() {
                        let actual_path = latest_file.path().to_string_lossy().to_string();
                        debug_log.push_str(&format!("  ✅ Found file: {}\n", actual_path));
                        found_file = Some((actual_path, latest_file.path().to_path_buf()));
                        break; // Found file, stop searching
                    } else {
                        debug_log.push_str("  No matching files in this directory\n");
                    }
                } else {
                    debug_log.push_str("  Failed to read directory\n");
                }
            }
            
            if let Some((actual_path, file_path_buf)) = found_file {
                println!("🔥 Found actual output file: {}", actual_path);
                debug_log.push_str(&format!("🔥 Final result - Found actual output file: {}\n", actual_path));
                let text = tokio::fs::read_to_string(&file_path_buf).await
                    .unwrap_or_else(|_| "Transcription completed but text could not be read".to_string());
                (text, actual_path)
            } else {
                debug_log.push_str("❌ No matching files found in any directory\n");
                
                // Write debug log to desktop
                let desktop_path = dirs::desktop_dir().unwrap_or_else(|| std::env::temp_dir());
                let debug_log_path = desktop_path.join("speechtotext_file_search.log");
                let _ = std::fs::write(&debug_log_path, &debug_log);
                
                return Err(AppError::CliError("Transcription output file not found".to_string()));
            }
        };

        // Write successful debug log to desktop
        let desktop_path = dirs::desktop_dir().unwrap_or_else(|| std::env::temp_dir());
        let debug_log_path = desktop_path.join("speechtotext_file_search.log");
        let _ = std::fs::write(&debug_log_path, &debug_log);

        Ok(TranscriptionResult {
            id: crate::utils::generate_id(),
            original_file: audio_file,
            transcribed_text,
            metadata: TranscriptionMetadata {
                language: settings.language.clone(),
                model_size: settings.model_size.to_string(),
                timestamp: Utc::now(),
                audio_info: AudioInfo {
                    duration: 0.0, // Would be extracted from CLI output
                    sample_rate: None,
                    channels: None,
                },
            },
            output_path: actual_output_path,
            processing_time,
            confidence: None, // Would be extracted from CLI output if available
        })
    }

    /// Execute a raw CLI command for testing
    pub async fn execute_raw_command(&self, args: &[&str]) -> AppResult<CliResult> {
        if self.use_sidecar {
            let cli_path = self.find_sidecar_path()?;
            let output = timeout(
                Duration::from_secs(30),
                tokio::process::Command::new(&cli_path)
                    .args(args)
                    .output()
            ).await
            .map_err(|_| AppError::CliError("Command timed out".to_string()))?
            .map_err(|e| AppError::CliError(format!("Failed to execute command: {}", e)))?;

            Ok(CliResult {
                success: output.status.success(),
                output: String::from_utf8_lossy(&output.stdout).to_string(),
                error: if output.stderr.is_empty() {
                    None
                } else {
                    Some(String::from_utf8_lossy(&output.stderr).to_string())
                },
                exit_code: output.status.code().unwrap_or(-1),
            })
        } else {
            let cli_command = self.find_dev_cli_command();
            let output = timeout(
                Duration::from_secs(30),
                tokio::process::Command::new(&cli_command)
                    .args(args)
                    .output()
            ).await
            .map_err(|_| AppError::CliError("Command timed out".to_string()))?
            .map_err(|e| AppError::CliError(format!("Failed to execute command: {}", e)))?;

            Ok(CliResult {
                success: output.status.success(),
                output: String::from_utf8_lossy(&output.stdout).to_string(),
                error: if output.stderr.is_empty() {
                    None
                } else {
                    Some(String::from_utf8_lossy(&output.stderr).to_string())
                },
                exit_code: output.status.code().unwrap_or(-1),
            })
        }
    }

    /// Parses a line of CLI output and emits a progress event if progress information is found.
    fn parse_and_emit_progress(line: &str, callback: &ProgressCallback, file_path: &str) {
        println!("🔥 CLI Output: {}", line);
        
        // Log all CLI output to desktop for debugging
        let desktop_path = dirs::desktop_dir().unwrap_or_else(|| std::env::temp_dir());
        let cli_output_log_path = desktop_path.join("speechtotext_cli_output.log");
        let log_entry = format!("[{}] {}\n", chrono::Utc::now().format("%H:%M:%S%.3f"), line);
        let _ = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&cli_output_log_path)
            .and_then(|mut file| {
                use std::io::Write;
                file.write_all(log_entry.as_bytes())
            });

        // Skip sending basic CLI output as progress to avoid overriding real progress
        // Only send important messages, not every line of output

        // Pattern 1: Whisper segment progress (e.g., "[00:00.000 --> 00:30.000]")
        let segment_regex = Regex::new(r"\[(\d{2}):(\d{2})\.(\d{3}) --> (\d{2}):(\d{2})\.(\d{3})\]").unwrap();
        if let Some(caps) = segment_regex.captures(line) {
            // Calculate approximate progress based on timestamp
            if let (Ok(_start_min), Ok(_start_sec), Ok(end_min), Ok(end_sec)) = (
                caps[1].parse::<f64>(),
                caps[2].parse::<f64>(),
                caps[4].parse::<f64>(),
                caps[5].parse::<f64>(),
            ) {
                let current_time = end_min * 60.0 + end_sec;
                // Assume audio is roughly 5 minutes long for progress calculation
                // This is a rough estimate since we don't know total duration
                let estimated_progress = (current_time / 300.0) * 100.0;
                let progress = if estimated_progress > 90.0 { 90.0 } else { estimated_progress };

                callback(ProcessingProgress {
                    stage: ProcessingStage::Transcribing,
                    progress,
                    current_file: Some(file_path.to_string()),
                    timestamp: Utc::now(),
                    message: Some(format!("Transcribing: {:.1}% ({}:{:02})", progress, end_min as u8, end_sec as u8)),
                    job_id: None,
                    file_index: None,
                    total_files: None,
                    can_cancel: true,
                });
                return;
            }
        }

        // Pattern 2: tqdm progress bar (e.g., "96%|█████████▌| 213478/222478 [03:06<00:07, 1146.02frames/s]")
        let tqdm_regex = Regex::new(r"(\d+)%\|[^|]*\|\s*(\d+)/(\d+)\s*\[").unwrap();
        if let Some(caps) = tqdm_regex.captures(line) {
            if let (Ok(percent), Ok(current), Ok(total)) = (
                caps[1].parse::<f64>(),
                caps[2].parse::<f64>(),
                caps[3].parse::<f64>(),
            ) {
                callback(ProcessingProgress {
                    stage: ProcessingStage::Transcribing,
                    progress: percent,
                    current_file: Some(file_path.to_string()),
                    timestamp: Utc::now(),
                    message: Some(format!("Transcribing: {}% ({}/{})", percent as u8, current as u64, total as u64)),
                    job_id: None,
                    file_index: None,
                    total_files: None,
                    can_cancel: true,
                });
                return;
            }
        }

        // Pattern 3: CLI progress format from our CLI (e.g., "[1/1] (100.0%) Processing: test-file-1.m4a")
        let cli_progress_regex = Regex::new(r"\[(\d+)/(\d+)\]\s*\((\d+(?:\.\d+)?)%\)\s*Processing:").unwrap();
        if let Some(caps) = cli_progress_regex.captures(line) {
            if let (Ok(current), Ok(total), Ok(percent)) = (
                caps[1].parse::<f64>(),
                caps[2].parse::<f64>(),
                caps[3].parse::<f64>(),
            ) {
                callback(ProcessingProgress {
                    stage: ProcessingStage::Transcribing,
                    progress: percent,
                    current_file: Some(file_path.to_string()),
                    timestamp: Utc::now(),
                    message: Some(format!("Processing file: {}% ({}/{})", percent as u8, current as u64, total as u64)),
                    job_id: None,
                    file_index: None,
                    total_files: None,
                    can_cancel: true,
                });
                return;
            }
        }

        // Pattern 4: Simple percentage (e.g., "50%" or "Processing: 50%")
        let percent_regex = Regex::new(r"(\d+)%").unwrap();
        if let Some(caps) = percent_regex.captures(line) {
            if let Ok(percent) = caps[1].parse::<f64>() {
                callback(ProcessingProgress {
                    stage: ProcessingStage::Transcribing,
                    progress: percent,
                    current_file: Some(file_path.to_string()),
                    timestamp: Utc::now(),
                    message: Some(format!("Transcribing: {}%", percent as u8)),
                    job_id: None,
                    file_index: None,
                    total_files: None,
                    can_cancel: true,
                });
                return;
            }
        }

        // Pattern 5: Whisper loading model
        if line.contains("Loading Whisper model") {
            callback(ProcessingProgress {
                stage: ProcessingStage::Initializing,
                progress: 10.0,
                current_file: Some(file_path.to_string()),
                timestamp: Utc::now(),
                message: Some("Loading Whisper model...".to_string()),
                job_id: None,
                file_index: None,
                total_files: None,
                can_cancel: true,
            });
            return;
        }

        // Pattern 6: Whisper transcribing
        if line.contains("Transcribing") && !line.contains("Loading") {
            callback(ProcessingProgress {
                stage: ProcessingStage::Transcribing,
                progress: 25.0,
                current_file: Some(file_path.to_string()),
                timestamp: Utc::now(),
                message: Some("Transcribing audio...".to_string()),
                job_id: None,
                file_index: None,
                total_files: None,
                can_cancel: true,
            });
            return;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use std::fs::File;


    #[tokio::test]
    async fn test_cli_manager_creation() {
        let manager = CliManager::default();
        assert_eq!(manager.cli_command, "speech-to-text");
    }

    #[tokio::test]
    async fn test_cli_manager_with_custom_command() {
        let manager = CliManager::new("custom-cli".to_string());
        assert_eq!(manager.cli_command, "custom-cli");
    }

    #[tokio::test]
    async fn test_cli_manager_with_timeout() {
        let manager = CliManager::default().with_timeout(Duration::from_secs(30));
        assert_eq!(manager.timeout_duration, Duration::from_secs(30));
    }

    #[tokio::test]
    async fn test_execute_raw_command_with_echo() {
        // Use echo command which should be available on most systems
        let manager = CliManager::new("echo".to_string());
        let result = manager.execute_raw_command(&["hello", "world"]).await.unwrap();
        
        assert!(result.success);
        assert!(result.output.contains("hello world"));
        assert!(result.error.is_none());
        assert_eq!(result.exit_code, 0);
    }

    #[tokio::test]
    async fn test_execute_raw_command_failure() {
        // Use a command that should fail
        let manager = CliManager::new("nonexistent-command".to_string());
        let result = manager.execute_raw_command(&["test"]).await;
        
        assert!(result.is_err());
    }

    #[tokio::test]
    async fn test_parse_cli_output() {
        let manager = CliManager::default();
        let temp_dir = tempdir().unwrap();
        let file_path = temp_dir.path().join("test.m4a");
        File::create(&file_path).unwrap();
        
        let settings = AppSettings::default();
        let output = b"Test transcription output";
        
        let result = manager.parse_cli_output(
            file_path.to_str().unwrap(),
            output,
            10.5,
            &settings
        ).await.unwrap();
        
        assert_eq!(result.processing_time, 10.5);
        assert_eq!(result.metadata.language, "ko");
        assert!(!result.id.is_empty());
    }

    #[tokio::test]
    async fn test_monitor_progress() {
        use tokio::sync::mpsc;
        
        let manager = CliManager::default();
        let (tx, mut rx) = mpsc::unbounded_channel();
        
        let callback: ProgressCallback = Arc::new(move |progress| {
            let _ = tx.send(progress);
        });
        
        // Start monitoring in background
        let monitor_task = tokio::spawn(async move {
            manager.monitor_progress(callback, "test.m4a").await;
        });
        
        // Collect some progress updates
        let mut updates = Vec::new();
        for _ in 0..3 {
            if let Ok(progress) = timeout(Duration::from_secs(2), rx.recv()).await {
                if let Some(progress) = progress {
                    updates.push(progress);
                }
            }
        }
        
        monitor_task.abort();
        assert!(!updates.is_empty());
    }
}