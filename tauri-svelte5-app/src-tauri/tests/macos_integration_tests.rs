#[cfg(test)]
mod macos_integration_tests {
    use tauri_gui_app_lib::macos_integration::{MacOSIntegration, NotificationOptions, DockBadgeInfo};

    #[test]
    fn test_macos_integration_creation() {
        let integration = MacOSIntegration::new();
        assert!(integration.dock_badge_enabled);
        assert!(integration.menu_bar_enabled);
        assert!(integration.notifications_enabled);
    }

    #[test]
    fn test_is_macos_detection() {
        let is_macos = MacOSIntegration::is_macos();
        
        #[cfg(target_os = "macos")]
        assert!(is_macos);
        
        #[cfg(not(target_os = "macos"))]
        assert!(!is_macos);
    }

    #[test]
    fn test_dock_badge_info_creation() {
        let badge_info = DockBadgeInfo {
            count: Some(5),
            text: None,
            progress: None,
        };
        
        assert_eq!(badge_info.count, Some(5));
        assert_eq!(badge_info.text, None);
        assert_eq!(badge_info.progress, None);
    }

    #[test]
    fn test_notification_options_creation() {
        let options = NotificationOptions {
            title: "Test Title".to_string(),
            body: "Test Body".to_string(),
            sound: Some("default".to_string()),
            identifier: Some("test-id".to_string()),
        };
        
        assert_eq!(options.title, "Test Title");
        assert_eq!(options.body, "Test Body");
        assert_eq!(options.sound, Some("default".to_string()));
        assert_eq!(options.identifier, Some("test-id".to_string()));
    }

    #[tokio::test]
    async fn test_dock_badge_operations() {
        let integration = MacOSIntegration::new();
        
        // Test setting dock badge with count
        let badge_info = DockBadgeInfo {
            count: Some(3),
            text: None,
            progress: None,
        };
        
        let result = integration.set_dock_badge(badge_info);
        assert!(result.is_ok());
        
        // Test clearing dock badge
        let clear_result = integration.clear_dock_badge();
        assert!(clear_result.is_ok());
    }

    #[tokio::test]
    async fn test_dock_progress_operations() {
        let integration = MacOSIntegration::new();
        
        // Test setting dock progress
        let result = integration.set_dock_progress(0.5);
        assert!(result.is_ok());
        
        // Test clearing dock progress
        let clear_result = integration.clear_dock_progress();
        assert!(clear_result.is_ok());
    }

    #[tokio::test]
    async fn test_notification_display() {
        let integration = MacOSIntegration::new();
        
        let options = NotificationOptions {
            title: "Test Notification".to_string(),
            body: "This is a test notification".to_string(),
            sound: Some("default".to_string()),
            identifier: Some("test-notification".to_string()),
        };
        
        let result = integration.show_notification(options);
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_file_association_operations() {
        let integration = MacOSIntegration::new();
        
        // Test registering file associations
        let register_result = integration.register_file_associations();
        assert!(register_result.is_ok());
        
        // Test verifying file associations
        let verify_result = integration.verify_file_associations();
        assert!(verify_result.is_ok());
        
        // Test getting file association status
        let status_result = integration.get_file_association_status();
        assert!(status_result.is_ok());
        
        let status_list = status_result.unwrap();
        assert!(!status_list.is_empty());
        
        // Check that all expected extensions are present
        let extensions: Vec<String> = status_list.iter().map(|s| s.extension.clone()).collect();
        assert!(extensions.contains(&"m4a".to_string()));
        assert!(extensions.contains(&"wav".to_string()));
        assert!(extensions.contains(&"mp3".to_string()));
        assert!(extensions.contains(&"aac".to_string()));
        assert!(extensions.contains(&"flac".to_string()));
    }

    #[tokio::test]
    async fn test_file_opened_handler() {
        let integration = MacOSIntegration::new();
        
        let test_file_path = "/path/to/test/audio.m4a".to_string();
        let result = integration.handle_file_opened(test_file_path);
        assert!(result.is_ok());
    }

    #[cfg(target_os = "macos")]
    #[tokio::test]
    async fn test_macos_version_detection() {
        let integration = MacOSIntegration::new();
        
        let version_result = integration.get_macos_version();
        assert!(version_result.is_ok());
        
        let version = version_result.unwrap();
        assert!(!version.is_empty());
        
        // Version should be in format like "14.0" or "13.6.1"
        assert!(version.contains('.'));
    }

    #[cfg(not(target_os = "macos"))]
    #[tokio::test]
    async fn test_non_macos_version_detection() {
        let integration = MacOSIntegration::new();
        
        let version_result = integration.get_macos_version();
        assert!(version_result.is_err());
    }

    #[test]
    fn test_dock_badge_info_serialization() {
        let badge_info = DockBadgeInfo {
            count: Some(10),
            text: Some("Processing".to_string()),
            progress: Some(0.75),
        };
        
        let serialized = serde_json::to_string(&badge_info).unwrap();
        let deserialized: DockBadgeInfo = serde_json::from_str(&serialized).unwrap();
        
        assert_eq!(deserialized.count, Some(10));
        assert_eq!(deserialized.text, Some("Processing".to_string()));
        assert_eq!(deserialized.progress, Some(0.75));
    }

    #[test]
    fn test_notification_options_serialization() {
        let options = NotificationOptions {
            title: "Serialization Test".to_string(),
            body: "Testing notification serialization".to_string(),
            sound: Some("Basso".to_string()),
            identifier: Some("serialization-test".to_string()),
        };
        
        let serialized = serde_json::to_string(&options).unwrap();
        let deserialized: NotificationOptions = serde_json::from_str(&serialized).unwrap();
        
        assert_eq!(deserialized.title, "Serialization Test");
        assert_eq!(deserialized.body, "Testing notification serialization");
        assert_eq!(deserialized.sound, Some("Basso".to_string()));
        assert_eq!(deserialized.identifier, Some("serialization-test".to_string()));
    }

    #[tokio::test]
    async fn test_progress_boundary_values() {
        let integration = MacOSIntegration::new();
        
        // Test minimum progress (0.0)
        let min_result = integration.set_dock_progress(0.0);
        assert!(min_result.is_ok());
        
        // Test maximum progress (1.0)
        let max_result = integration.set_dock_progress(1.0);
        assert!(max_result.is_ok());
        
        // Test invalid progress (should still work but might be clamped)
        let invalid_result = integration.set_dock_progress(1.5);
        assert!(invalid_result.is_ok());
        
        // Test negative progress (should clear progress)
        let negative_result = integration.set_dock_progress(-1.0);
        assert!(negative_result.is_ok());
    }

    #[tokio::test]
    async fn test_empty_notification() {
        let integration = MacOSIntegration::new();
        
        let options = NotificationOptions {
            title: "".to_string(),
            body: "".to_string(),
            sound: None,
            identifier: None,
        };
        
        let result = integration.show_notification(options);
        assert!(result.is_ok());
    }

    #[tokio::test]
    async fn test_long_notification_text() {
        let integration = MacOSIntegration::new();
        
        let long_text = "A".repeat(1000);
        let options = NotificationOptions {
            title: long_text.clone(),
            body: long_text,
            sound: None,
            identifier: None,
        };
        
        let result = integration.show_notification(options);
        assert!(result.is_ok());
    }
}