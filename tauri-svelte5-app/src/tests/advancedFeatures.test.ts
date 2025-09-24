/**
 * Tests for advanced processing features
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { QueueManager, type QueueItem } from '../services/queueManager';
import { historyService, type HistoryItem } from '../services/historyService';
import { profilesService, type ProcessingProfile } from '../services/profilesService';

let queueManager: QueueManager;

describe('Advanced Processing Features', () => {
  beforeEach(() => {
    // Create fresh queue manager instance for each test
    QueueManager.resetInstance();
    queueManager = QueueManager.getInstance({ autoStart: false });
    
    // Clear any existing data
    historyService.clearHistory();
    historyService.clearRecentFiles();
  });

  afterEach(() => {
    queueManager.cleanup();
  });

  describe('Queue Manager', () => {
    it('should add items to queue with priority', () => {
      const file1 = new File(['content1'], 'file1.txt');
      const file2 = new File(['content2'], 'file2.txt');
      const file3 = new File(['content3'], 'file3.txt');

      // Add with different priorities
      const id1 = queueManager.addToQueue(file1, {}, { priority: 1 });
      const id2 = queueManager.addToQueue(file2, {}, { priority: 10 });
      const id3 = queueManager.addToQueue(file3, {}, { priority: 5 });

      const pendingItems = queueManager.getItemsByStatus('pending');
      
      expect(pendingItems).toHaveLength(3);
      // Should be ordered by priority (highest first)
      expect(pendingItems[0].priority).toBe(10);
      expect(pendingItems[1].priority).toBe(5);
      expect(pendingItems[2].priority).toBe(1);
    });

    it('should get queue statistics', () => {
      const file = new File(['content'], 'test.txt');
      queueManager.addToQueue(file, {});

      const stats = queueManager.getStats();
      
      expect(stats.total).toBe(1);
      expect(stats.pending).toBe(1);
      expect(stats.processing).toBe(0);
      expect(stats.completed).toBe(0);
      expect(stats.failed).toBe(0);
    });

    it('should cancel queue items', () => {
      const file = new File(['content'], 'test.txt');
      const id = queueManager.addToQueue(file, {});

      const cancelled = queueManager.cancelItem(id);
      expect(cancelled).toBe(true);

      const item = queueManager.getItem(id);
      expect(item).toBeNull();
    });

    it('should clear entire queue', () => {
      const file1 = new File(['content1'], 'file1.txt');
      const file2 = new File(['content2'], 'file2.txt');

      queueManager.addToQueue(file1, {});
      queueManager.addToQueue(file2, {});

      queueManager.clearQueue();

      const stats = queueManager.getStats();
      expect(stats.pending).toBe(0);
    });

    it('should handle queue processing lifecycle', async () => {
      const file = new File(['content'], 'test.txt');
      
      let progressCalled = false;
      let completeCalled = false;
      
      const id = queueManager.addToQueue(file, {}, {
        estimatedDuration: 100, // Short duration for test
        onProgress: () => { progressCalled = true; },
        onComplete: () => { completeCalled = true; }
      });

      queueManager.start();

      // Wait for processing to complete
      await new Promise(resolve => setTimeout(resolve, 200));

      expect(progressCalled).toBe(true);
      expect(completeCalled).toBe(true);

      const completedItems = queueManager.getItemsByStatus('completed');
      expect(completedItems).toHaveLength(1);
      expect(completedItems[0].id).toBe(id);
    });
  });

  describe('History Service', () => {
    it('should add items to history', () => {
      const id = historyService.addToHistory(
        'test.txt',
        '/path/to/test.txt',
        1024,
        5000,
        { language: 'en', model: 'base' },
        { transcribedText: 'Test transcription' },
        'completed'
      );

      expect(id).toBeDefined();
      
      const history = historyService.getHistory();
      expect(history).toHaveLength(1);
      expect(history[0].fileName).toBe('test.txt');
      expect(history[0].status).toBe('completed');
    });

    it('should filter history by date range', () => {
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);

      historyService.addToHistory(
        'test1.txt',
        '/path/to/test1.txt',
        1024,
        5000,
        {},
        { transcribedText: 'Test 1' }
      );

      const filtered = historyService.getHistory({
        dateFrom: yesterday,
        dateTo: tomorrow
      });

      expect(filtered).toHaveLength(1);
    });

    it('should search history by filename and content', () => {
      historyService.addToHistory(
        'meeting.txt',
        '/path/to/meeting.txt',
        1024,
        5000,
        {},
        { transcribedText: 'Important business meeting discussion' }
      );

      historyService.addToHistory(
        'personal.txt',
        '/path/to/personal.txt',
        1024,
        5000,
        {},
        { transcribedText: 'Personal notes and thoughts' }
      );

      const searchResults = historyService.searchHistory('meeting');
      expect(searchResults).toHaveLength(1);
      expect(searchResults[0].fileName).toBe('meeting.txt');

      const contentSearch = historyService.searchHistory('business');
      expect(contentSearch).toHaveLength(1);
    });

    it('should manage recent files', () => {
      historyService.addToHistory(
        'recent.txt',
        '/path/to/recent.txt',
        1024,
        5000,
        {},
        { transcribedText: 'Recent file' }
      );

      const recentFiles = historyService.getRecentFiles();
      expect(recentFiles).toHaveLength(1);
      expect(recentFiles[0].fileName).toBe('recent.txt');
    });

    it('should toggle favorite files', () => {
      historyService.addToHistory(
        'favorite.txt',
        '/path/to/favorite.txt',
        1024,
        5000,
        {},
        { transcribedText: 'Favorite file' }
      );

      const isFavorite = historyService.toggleFavorite('/path/to/favorite.txt');
      expect(isFavorite).toBe(true);

      const favorites = historyService.getFavoriteFiles();
      expect(favorites).toHaveLength(1);
      expect(favorites[0].fileName).toBe('favorite.txt');
    });

    it('should calculate statistics', () => {
      historyService.addToHistory(
        'test1.txt',
        '/path/to/test1.txt',
        1024,
        3000,
        { language: 'en' },
        { transcribedText: 'Test 1' },
        'completed'
      );

      historyService.addToHistory(
        'test2.txt',
        '/path/to/test2.txt',
        2048,
        7000,
        { language: 'en' },
        { transcribedText: 'Test 2' },
        'completed'
      );

      const stats = historyService.getStats();
      expect(stats.totalProcessed).toBe(2);
      expect(stats.averageProcessingTime).toBe(5000);
      expect(stats.successRate).toBe(100);
    });

    it('should export and import history', () => {
      historyService.addToHistory(
        'export.txt',
        '/path/to/export.txt',
        1024,
        5000,
        {},
        { transcribedText: 'Export test' }
      );

      const exported = historyService.exportHistory();
      expect(exported).toContain('export.txt');

      historyService.clearHistory();
      expect(historyService.getHistory()).toHaveLength(0);

      const imported = historyService.importHistory(exported);
      expect(imported).toBe(true);
      expect(historyService.getHistory()).toHaveLength(1);
    });
  });

  describe('Profiles Service', () => {
    it('should have built-in profiles', () => {
      const profiles = profilesService.getAllProfiles();
      expect(profiles.length).toBeGreaterThan(0);
      
      const builtInProfiles = profiles.filter(p => p.isBuiltIn);
      expect(builtInProfiles.length).toBeGreaterThan(0);
      
      const defaultProfile = profilesService.getDefaultProfile();
      expect(defaultProfile).toBeDefined();
      expect(defaultProfile?.isDefault).toBe(true);
    });

    it('should create custom profiles', () => {
      const id = profilesService.createProfile(
        'Custom Profile',
        {
          language: 'ko',
          modelSize: 'large',
          includeMetadata: true,
          autoSave: true,
          outputFormat: 'docx'
        },
        {
          description: 'My custom profile',
          tags: ['custom', 'korean']
        }
      );

      expect(id).toBeDefined();
      
      const profile = profilesService.getProfile(id);
      expect(profile).toBeDefined();
      expect(profile?.name).toBe('Custom Profile');
      expect(profile?.settings.language).toBe('ko');
      expect(profile?.isBuiltIn).toBe(false);
    });

    it('should prevent duplicate profile names', () => {
      profilesService.createProfile('Test Profile', {
        language: 'en',
        modelSize: 'base',
        includeMetadata: false,
        autoSave: true,
        outputFormat: 'txt'
      });

      expect(() => {
        profilesService.createProfile('Test Profile', {
          language: 'ko',
          modelSize: 'medium',
          includeMetadata: true,
          autoSave: true,
          outputFormat: 'docx'
        });
      }).toThrow('Profile with name "Test Profile" already exists');
    });

    it('should update profiles', () => {
      const id = profilesService.createProfile('Update Test', {
        language: 'en',
        modelSize: 'base',
        includeMetadata: false,
        autoSave: true,
        outputFormat: 'txt'
      });

      const updated = profilesService.updateProfile(id, {
        name: 'Updated Profile',
        settings: {
          language: 'ko',
          modelSize: 'large',
          includeMetadata: true,
          autoSave: true,
          outputFormat: 'docx'
        }
      });

      expect(updated).toBe(true);
      
      const profile = profilesService.getProfile(id);
      expect(profile?.name).toBe('Updated Profile');
      expect(profile?.settings.language).toBe('ko');
    });

    it('should delete custom profiles but not built-in ones', () => {
      const customId = profilesService.createProfile('Delete Test', {
        language: 'en',
        modelSize: 'base',
        includeMetadata: false,
        autoSave: true,
        outputFormat: 'txt'
      });

      const deleted = profilesService.deleteProfile(customId);
      expect(deleted).toBe(true);
      expect(profilesService.getProfile(customId)).toBeNull();

      // Try to delete built-in profile
      const builtInProfile = profilesService.getAllProfiles().find(p => p.isBuiltIn);
      if (builtInProfile) {
        const deletedBuiltIn = profilesService.deleteProfile(builtInProfile.id);
        expect(deletedBuiltIn).toBe(false);
      }
    });

    it('should duplicate profiles', () => {
      const originalId = profilesService.createProfile('Original', {
        language: 'en',
        modelSize: 'base',
        includeMetadata: false,
        autoSave: true,
        outputFormat: 'txt'
      });

      const duplicateId = profilesService.duplicateProfile(originalId, 'Duplicate');
      expect(duplicateId).toBeDefined();
      
      const duplicate = profilesService.getProfile(duplicateId!);
      expect(duplicate?.name).toBe('Duplicate');
      expect(duplicate?.settings.language).toBe('en');
      expect(duplicate?.isBuiltIn).toBe(false);
    });

    it('should track profile usage', () => {
      const id = profilesService.createProfile('Usage Test', {
        language: 'en',
        modelSize: 'base',
        includeMetadata: false,
        autoSave: true,
        outputFormat: 'txt'
      });

      const profile = profilesService.useProfile(id);
      expect(profile?.useCount).toBe(1);
      expect(profile?.lastUsed).toBeDefined();

      profilesService.useProfile(id);
      const updatedProfile = profilesService.getProfile(id);
      expect(updatedProfile?.useCount).toBe(2);
    });

    it('should search profiles by name and tags', () => {
      profilesService.createProfile('Korean Meeting', {
        language: 'ko',
        modelSize: 'medium',
        includeMetadata: true,
        autoSave: true,
        outputFormat: 'docx'
      }, {
        tags: ['korean', 'meeting', 'business']
      });

      const searchResults = profilesService.searchProfiles('korean');
      expect(searchResults.length).toBeGreaterThan(0);
      
      const tagResults = profilesService.getProfilesByTag('meeting');
      expect(tagResults.length).toBeGreaterThan(0);
    });

    it('should manage default profile', () => {
      const id = profilesService.createProfile('New Default', {
        language: 'en',
        modelSize: 'base',
        includeMetadata: false,
        autoSave: true,
        outputFormat: 'txt'
      });

      const setDefault = profilesService.setDefaultProfile(id);
      expect(setDefault).toBe(true);
      
      const defaultProfile = profilesService.getDefaultProfile();
      expect(defaultProfile?.id).toBe(id);
    });

    it('should calculate profile statistics', () => {
      profilesService.createProfile('Stats Test 1', {
        language: 'en',
        modelSize: 'base',
        includeMetadata: false,
        autoSave: true,
        outputFormat: 'txt'
      });

      profilesService.createProfile('Stats Test 2', {
        language: 'ko',
        modelSize: 'medium',
        includeMetadata: true,
        autoSave: true,
        outputFormat: 'docx'
      });

      const stats = profilesService.getStats();
      expect(stats.totalProfiles).toBeGreaterThanOrEqual(2);
      expect(stats.customProfiles).toBeGreaterThanOrEqual(2);
      expect(stats.builtInProfiles).toBeGreaterThan(0);
    });
  });

  describe('Integration Tests', () => {
    it('should integrate queue manager with history service', async () => {
      // Create a fresh queue manager for this test
      const testQueueManager = QueueManager.getInstance({ autoStart: false });
      
      const file = new File(['content'], 'integration.txt');
      
      let completedResult: any = null;
      
      const id = testQueueManager.addToQueue(file, { language: 'en' }, {
        estimatedDuration: 100,
        onComplete: (result) => {
          completedResult = result;
          
          // Add to history when processing completes
          historyService.addToHistory(
            file.name,
            '/path/to/' + file.name,
            file.size,
            100,
            { language: 'en' },
            { transcribedText: result.transcribedText },
            'completed'
          );
        }
      });

      testQueueManager.start();
      
      // Wait for processing
      await new Promise(resolve => setTimeout(resolve, 200));

      expect(completedResult).toBeDefined();
      
      const history = historyService.getHistory();
      expect(history).toHaveLength(1);
      expect(history[0].fileName).toBe('integration.txt');
      
      testQueueManager.cleanup();
    });

    it('should use profiles with queue manager', () => {
      const profileId = profilesService.createProfile('Queue Test Profile', {
        language: 'ko',
        modelSize: 'large',
        includeMetadata: true,
        autoSave: true,
        outputFormat: 'docx'
      });

      const profile = profilesService.useProfile(profileId);
      expect(profile).toBeDefined();

      const file = new File(['content'], 'profile-test.txt');
      const queueId = queueManager.addToQueue(file, profile?.settings);

      const queueItem = queueManager.getItem(queueId);
      expect(queueItem?.settings.language).toBe('ko');
      expect(queueItem?.settings.modelSize).toBe('large');
    });
  });
});