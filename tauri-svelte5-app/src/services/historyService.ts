/**
 * Processing history and recent files service
 */

interface HistoryItem {
  id: string;
  fileName: string;
  filePath: string;
  fileSize: number;
  processedAt: Date;
  processingTime: number;
  settings: any;
  result: {
    transcribedText: string;
    outputPath?: string;
    confidence?: number;
    metadata?: any;
  };
  status: 'completed' | 'failed';
  error?: string;
}

interface RecentFile {
  id: string;
  fileName: string;
  filePath: string;
  fileSize: number;
  lastAccessed: Date;
  accessCount: number;
  isFavorite: boolean;
}

interface HistoryStats {
  totalProcessed: number;
  totalProcessingTime: number;
  averageProcessingTime: number;
  successRate: number;
  mostUsedSettings: any;
  favoriteFiles: RecentFile[];
}

interface HistoryFilter {
  dateFrom?: Date;
  dateTo?: Date;
  status?: 'completed' | 'failed';
  fileName?: string;
  minFileSize?: number;
  maxFileSize?: number;
}

class HistoryService {
  private static instance: HistoryService;
  private history: HistoryItem[] = [];
  private recentFiles: RecentFile[] = [];
  private maxHistoryItems = 1000;
  private maxRecentFiles = 50;
  private storageKey = 'speech-to-text-history';
  private recentFilesKey = 'speech-to-text-recent-files';

  private constructor() {
    this.loadFromStorage();
  }

  static getInstance(): HistoryService {
    if (!HistoryService.instance) {
      HistoryService.instance = new HistoryService();
    }
    return HistoryService.instance;
  }

  /**
   * Add processing result to history
   */
  addToHistory(
    fileName: string,
    filePath: string,
    fileSize: number,
    processingTime: number,
    settings: any,
    result: HistoryItem['result'],
    status: 'completed' | 'failed' = 'completed',
    error?: string
  ): string {
    const id = this.generateId();
    
    const historyItem: HistoryItem = {
      id,
      fileName,
      filePath,
      fileSize,
      processedAt: new Date(),
      processingTime,
      settings,
      result,
      status,
      error
    };

    // Add to beginning of history
    this.history.unshift(historyItem);

    // Limit history size
    if (this.history.length > this.maxHistoryItems) {
      this.history = this.history.slice(0, this.maxHistoryItems);
    }

    // Update recent files
    this.updateRecentFile(fileName, filePath, fileSize);

    // Save to storage
    this.saveToStorage();

    return id;
  }

  /**
   * Get history items with optional filtering
   */
  getHistory(filter?: HistoryFilter, limit?: number): HistoryItem[] {
    let filteredHistory = [...this.history];

    if (filter) {
      if (filter.dateFrom) {
        filteredHistory = filteredHistory.filter(item => 
          item.processedAt >= filter.dateFrom!
        );
      }

      if (filter.dateTo) {
        filteredHistory = filteredHistory.filter(item => 
          item.processedAt <= filter.dateTo!
        );
      }

      if (filter.status) {
        filteredHistory = filteredHistory.filter(item => 
          item.status === filter.status
        );
      }

      if (filter.fileName) {
        const searchTerm = filter.fileName.toLowerCase();
        filteredHistory = filteredHistory.filter(item => 
          item.fileName.toLowerCase().includes(searchTerm)
        );
      }

      if (filter.minFileSize) {
        filteredHistory = filteredHistory.filter(item => 
          item.fileSize >= filter.minFileSize!
        );
      }

      if (filter.maxFileSize) {
        filteredHistory = filteredHistory.filter(item => 
          item.fileSize <= filter.maxFileSize!
        );
      }
    }

    if (limit) {
      filteredHistory = filteredHistory.slice(0, limit);
    }

    return filteredHistory;
  }

  /**
   * Get recent files
   */
  getRecentFiles(limit?: number): RecentFile[] {
    const files = [...this.recentFiles].sort((a, b) => 
      b.lastAccessed.getTime() - a.lastAccessed.getTime()
    );

    return limit ? files.slice(0, limit) : files;
  }

  /**
   * Get favorite files
   */
  getFavoriteFiles(): RecentFile[] {
    return this.recentFiles.filter(file => file.isFavorite);
  }

  /**
   * Toggle favorite status of a file
   */
  toggleFavorite(filePath: string): boolean {
    const file = this.recentFiles.find(f => f.filePath === filePath);
    if (file) {
      file.isFavorite = !file.isFavorite;
      this.saveToStorage();
      return file.isFavorite;
    }
    return false;
  }

  /**
   * Remove file from recent files
   */
  removeFromRecent(filePath: string): boolean {
    const index = this.recentFiles.findIndex(f => f.filePath === filePath);
    if (index !== -1) {
      this.recentFiles.splice(index, 1);
      this.saveToStorage();
      return true;
    }
    return false;
  }

  /**
   * Clear recent files
   */
  clearRecentFiles(): void {
    this.recentFiles = [];
    this.saveToStorage();
  }

  /**
   * Get history statistics
   */
  getStats(): HistoryStats {
    const completedItems = this.history.filter(item => item.status === 'completed');
    const totalProcessed = this.history.length;
    const totalProcessingTime = this.history.reduce((sum, item) => sum + item.processingTime, 0);
    const averageProcessingTime = totalProcessed > 0 ? totalProcessingTime / totalProcessed : 0;
    const successRate = totalProcessed > 0 ? (completedItems.length / totalProcessed) * 100 : 0;

    // Find most used settings
    const settingsMap = new Map<string, number>();
    this.history.forEach(item => {
      const settingsKey = JSON.stringify(item.settings);
      settingsMap.set(settingsKey, (settingsMap.get(settingsKey) || 0) + 1);
    });

    let mostUsedSettings = {};
    let maxCount = 0;
    for (const [settingsStr, count] of settingsMap.entries()) {
      if (count > maxCount) {
        maxCount = count;
        mostUsedSettings = JSON.parse(settingsStr);
      }
    }

    const favoriteFiles = this.getFavoriteFiles();

    return {
      totalProcessed,
      totalProcessingTime,
      averageProcessingTime,
      successRate,
      mostUsedSettings,
      favoriteFiles
    };
  }

  /**
   * Search history
   */
  searchHistory(query: string): HistoryItem[] {
    const searchTerm = query.toLowerCase();
    return this.history.filter(item => 
      item.fileName.toLowerCase().includes(searchTerm) ||
      item.result.transcribedText.toLowerCase().includes(searchTerm)
    );
  }

  /**
   * Get history item by ID
   */
  getHistoryItem(id: string): HistoryItem | null {
    return this.history.find(item => item.id === id) || null;
  }

  /**
   * Delete history item
   */
  deleteHistoryItem(id: string): boolean {
    const index = this.history.findIndex(item => item.id === id);
    if (index !== -1) {
      this.history.splice(index, 1);
      this.saveToStorage();
      return true;
    }
    return false;
  }

  /**
   * Clear all history
   */
  clearHistory(): void {
    this.history = [];
    this.saveToStorage();
  }

  /**
   * Export history to JSON
   */
  exportHistory(): string {
    return JSON.stringify({
      history: this.history,
      recentFiles: this.recentFiles,
      exportedAt: new Date().toISOString()
    }, null, 2);
  }

  /**
   * Import history from JSON
   */
  importHistory(jsonData: string): boolean {
    try {
      const data = JSON.parse(jsonData);
      
      if (data.history && Array.isArray(data.history)) {
        // Validate and merge history
        const validHistory = data.history
          .filter(this.isValidHistoryItem)
          .map(item => ({
            ...item,
            processedAt: new Date(item.processedAt)
          }));
        this.history = [...validHistory, ...this.history];
        
        // Remove duplicates and limit size
        this.history = this.removeDuplicateHistory();
        if (this.history.length > this.maxHistoryItems) {
          this.history = this.history.slice(0, this.maxHistoryItems);
        }
      }

      if (data.recentFiles && Array.isArray(data.recentFiles)) {
        // Validate and merge recent files
        const validRecentFiles = data.recentFiles
          .filter(this.isValidRecentFile)
          .map(file => ({
            ...file,
            lastAccessed: new Date(file.lastAccessed)
          }));
        this.recentFiles = [...validRecentFiles, ...this.recentFiles];
        
        // Remove duplicates and limit size
        this.recentFiles = this.removeDuplicateRecentFiles();
        if (this.recentFiles.length > this.maxRecentFiles) {
          this.recentFiles = this.recentFiles.slice(0, this.maxRecentFiles);
        }
      }

      this.saveToStorage();
      return true;
    } catch (error) {
      console.error('Failed to import history:', error);
      return false;
    }
  }

  /**
   * Update recent file access
   */
  private updateRecentFile(fileName: string, filePath: string, fileSize: number): void {
    const existingIndex = this.recentFiles.findIndex(f => f.filePath === filePath);
    
    if (existingIndex !== -1) {
      // Update existing file
      const file = this.recentFiles[existingIndex];
      file.lastAccessed = new Date();
      file.accessCount++;
    } else {
      // Add new file
      const recentFile: RecentFile = {
        id: this.generateId(),
        fileName,
        filePath,
        fileSize,
        lastAccessed: new Date(),
        accessCount: 1,
        isFavorite: false
      };

      this.recentFiles.unshift(recentFile);

      // Limit recent files size
      if (this.recentFiles.length > this.maxRecentFiles) {
        this.recentFiles = this.recentFiles.slice(0, this.maxRecentFiles);
      }
    }
  }

  /**
   * Load data from localStorage
   */
  private loadFromStorage(): void {
    try {
      if (typeof localStorage !== 'undefined') {
        const historyData = localStorage.getItem(this.storageKey);
        if (historyData) {
          const parsed = JSON.parse(historyData);
          this.history = parsed.map(this.deserializeHistoryItem).filter(Boolean);
        }

        const recentFilesData = localStorage.getItem(this.recentFilesKey);
        if (recentFilesData) {
          const parsed = JSON.parse(recentFilesData);
          this.recentFiles = parsed.map(this.deserializeRecentFile).filter(Boolean);
        }
      }
    } catch (error) {
      console.error('Failed to load history from storage:', error);
    }
  }

  /**
   * Save data to localStorage
   */
  private saveToStorage(): void {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(this.storageKey, JSON.stringify(this.history));
        localStorage.setItem(this.recentFilesKey, JSON.stringify(this.recentFiles));
      }
    } catch (error) {
      console.error('Failed to save history to storage:', error);
    }
  }

  /**
   * Deserialize history item from storage
   */
  private deserializeHistoryItem(item: any): HistoryItem | null {
    try {
      return {
        ...item,
        processedAt: new Date(item.processedAt)
      };
    } catch {
      return null;
    }
  }

  /**
   * Deserialize recent file from storage
   */
  private deserializeRecentFile(file: any): RecentFile | null {
    try {
      return {
        ...file,
        lastAccessed: new Date(file.lastAccessed)
      };
    } catch {
      return null;
    }
  }

  /**
   * Validate history item
   */
  private isValidHistoryItem(item: any): boolean {
    return item && 
           typeof item.id === 'string' &&
           typeof item.fileName === 'string' &&
           typeof item.filePath === 'string' &&
           typeof item.fileSize === 'number' &&
           item.processedAt &&
           typeof item.processingTime === 'number' &&
           item.result;
  }

  /**
   * Validate recent file
   */
  private isValidRecentFile(file: any): boolean {
    return file &&
           typeof file.id === 'string' &&
           typeof file.fileName === 'string' &&
           typeof file.filePath === 'string' &&
           typeof file.fileSize === 'number' &&
           file.lastAccessed &&
           typeof file.accessCount === 'number';
  }

  /**
   * Remove duplicate history items
   */
  private removeDuplicateHistory(): HistoryItem[] {
    const seen = new Set<string>();
    return this.history.filter(item => {
      const key = `${item.filePath}-${item.processedAt.getTime()}`;
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
  }

  /**
   * Remove duplicate recent files
   */
  private removeDuplicateRecentFiles(): RecentFile[] {
    const seen = new Set<string>();
    return this.recentFiles.filter(file => {
      if (seen.has(file.filePath)) {
        return false;
      }
      seen.add(file.filePath);
      return true;
    });
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `history_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export singleton instance
export const historyService = HistoryService.getInstance();

// Export types
export type { HistoryItem, RecentFile, HistoryStats, HistoryFilter };