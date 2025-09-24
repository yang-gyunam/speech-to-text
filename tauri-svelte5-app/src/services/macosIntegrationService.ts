import { invoke } from '@tauri-apps/api/core';

export interface NotificationOptions {
  title: string;
  body: string;
  sound?: string;
  identifier?: string;
}

export interface DockBadgeInfo {
  count?: number;
  text?: string;
  progress?: number;
}

export interface FileAssociationStatus {
  extension: string;
  is_associated: boolean;
  current_handler?: string;
}

export class MacOSIntegrationService {
  /**
   * Check if running on macOS
   */
  static async isMacOS(): Promise<boolean> {
    try {
      return await invoke('is_macos');
    } catch (error) {
      console.error('Failed to check macOS status:', error);
      return false;
    }
  }

  /**
   * Get macOS version
   */
  static async getMacOSVersion(): Promise<string | null> {
    try {
      return await invoke('get_macos_version');
    } catch (error) {
      console.error('Failed to get macOS version:', error);
      return null;
    }
  }

  /**
   * Set dock badge with count or text
   */
  static async setDockBadge(badgeInfo: DockBadgeInfo): Promise<void> {
    try {
      await invoke('set_dock_badge', { badgeInfo });
    } catch (error) {
      console.error('Failed to set dock badge:', error);
      throw error;
    }
  }

  /**
   * Clear dock badge
   */
  static async clearDockBadge(): Promise<void> {
    try {
      await invoke('clear_dock_badge');
    } catch (error) {
      console.error('Failed to clear dock badge:', error);
      throw error;
    }
  }

  /**
   * Show system notification
   */
  static async showNotification(options: NotificationOptions): Promise<void> {
    try {
      await invoke('show_notification', { options });
    } catch (error) {
      console.error('Failed to show notification:', error);
      throw error;
    }
  }

  /**
   * Set dock progress indicator (0.0 to 1.0)
   */
  static async setDockProgress(progress: number): Promise<void> {
    try {
      await invoke('set_dock_progress', { progress });
    } catch (error) {
      console.error('Failed to set dock progress:', error);
      throw error;
    }
  }

  /**
   * Clear dock progress indicator
   */
  static async clearDockProgress(): Promise<void> {
    try {
      await invoke('clear_dock_progress');
    } catch (error) {
      console.error('Failed to clear dock progress:', error);
      throw error;
    }
  }

  /**
   * Register file associations for supported audio formats
   */
  static async registerFileAssociations(): Promise<void> {
    try {
      await invoke('register_file_associations');
    } catch (error) {
      console.error('Failed to register file associations:', error);
      throw error;
    }
  }

  /**
   * Verify file associations are properly registered
   */
  static async verifyFileAssociations(): Promise<void> {
    try {
      await invoke('verify_file_associations');
    } catch (error) {
      console.error('Failed to verify file associations:', error);
      throw error;
    }
  }

  /**
   * Get current file association status
   */
  static async getFileAssociationStatus(): Promise<FileAssociationStatus[]> {
    try {
      return await invoke('get_file_association_status');
    } catch (error) {
      console.error('Failed to get file association status:', error);
      return [];
    }
  }

  /**
   * Set this app as default handler for supported audio formats
   */
  static async setAsDefaultHandler(): Promise<void> {
    try {
      await invoke('set_as_default_handler');
    } catch (error) {
      console.error('Failed to set as default handler:', error);
      throw error;
    }
  }

  /**
   * Handle file opened from Finder (via file association)
   */
  static async handleFileOpenedFromFinder(filePath: string): Promise<void> {
    try {
      await invoke('handle_file_opened_from_finder', { filePath });
    } catch (error) {
      console.error('Failed to handle file opened from Finder:', error);
      throw error;
    }
  }

  /**
   * Show processing started notification
   */
  static async showProcessingStartedNotification(fileName: string): Promise<void> {
    if (await this.isMacOS()) {
      await this.showNotification({
        title: 'Speech to Text',
        body: `Started processing ${fileName}`,
        sound: 'default',
        identifier: 'processing-started'
      });
    }
  }

  /**
   * Show processing completed notification
   */
  static async showProcessingCompletedNotification(fileName: string, success: boolean): Promise<void> {
    if (await this.isMacOS()) {
      await this.showNotification({
        title: 'Speech to Text',
        body: success 
          ? `Successfully processed ${fileName}` 
          : `Failed to process ${fileName}`,
        sound: success ? 'default' : 'Basso',
        identifier: 'processing-completed'
      });
    }
  }

  /**
   * Show batch processing completed notification
   */
  static async showBatchCompletedNotification(totalFiles: number, successCount: number): Promise<void> {
    if (await this.isMacOS()) {
      const failedCount = totalFiles - successCount;
      const body = failedCount > 0 
        ? `Completed ${successCount}/${totalFiles} files (${failedCount} failed)`
        : `Successfully processed all ${totalFiles} files`;

      await this.showNotification({
        title: 'Batch Processing Complete',
        body,
        sound: failedCount > 0 ? 'Basso' : 'default',
        identifier: 'batch-completed'
      });
    }
  }

  /**
   * Update dock badge with processing count
   */
  static async updateProcessingBadge(count: number): Promise<void> {
    if (await this.isMacOS()) {
      if (count > 0) {
        await this.setDockBadge({ count });
      } else {
        await this.clearDockBadge();
      }
    }
  }

  /**
   * Update dock progress for current processing
   */
  static async updateProcessingProgress(progress: number): Promise<void> {
    if (await this.isMacOS()) {
      if (progress >= 0 && progress <= 1) {
        await this.setDockProgress(progress);
      } else {
        await this.clearDockProgress();
      }
    }
  }

  /**
   * Initialize macOS integration features
   */
  static async initialize(): Promise<void> {
    if (await this.isMacOS()) {
      try {
        // Verify file associations on startup
        await this.verifyFileAssociations();
        
        // Clear any existing dock badge/progress
        await this.clearDockBadge();
        await this.clearDockProgress();
        
        console.log('macOS integration initialized');
      } catch (error) {
        console.error('Failed to initialize macOS integration:', error);
      }
    }
  }

  /**
   * Cleanup macOS integration features
   */
  static async cleanup(): Promise<void> {
    if (await this.isMacOS()) {
      try {
        await this.clearDockBadge();
        await this.clearDockProgress();
        console.log('macOS integration cleaned up');
      } catch (error) {
        console.error('Failed to cleanup macOS integration:', error);
      }
    }
  }
}