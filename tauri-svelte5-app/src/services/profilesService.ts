/**
 * Processing profiles and presets service
 */

interface ProcessingProfile {
  id: string;
  name: string;
  description?: string;
  settings: {
    language: string;
    modelSize: 'tiny' | 'base' | 'small' | 'medium' | 'large';
    outputDirectory?: string;
    includeMetadata: boolean;
    autoSave: boolean;
    outputFormat: 'txt' | 'docx' | 'pdf' | 'json';
    customOptions?: Record<string, any>;
  };
  isDefault: boolean;
  isBuiltIn: boolean;
  createdAt: Date;
  lastUsed?: Date;
  useCount: number;
  tags: string[];
}

interface ProfileStats {
  totalProfiles: number;
  customProfiles: number;
  builtInProfiles: number;
  mostUsedProfile: ProcessingProfile | null;
  recentlyUsed: ProcessingProfile[];
}

class ProfilesService {
  private static instance: ProfilesService;
  private profiles: ProcessingProfile[] = [];
  private storageKey = 'speech-to-text-profiles';

  private constructor() {
    this.initializeBuiltInProfiles();
    this.loadFromStorage();
  }

  static getInstance(): ProfilesService {
    if (!ProfilesService.instance) {
      ProfilesService.instance = new ProfilesService();
    }
    return ProfilesService.instance;
  }

  /**
   * Get all profiles
   */
  getAllProfiles(): ProcessingProfile[] {
    return [...this.profiles].sort((a, b) => {
      // Built-in profiles first, then by last used, then by name
      if (a.isBuiltIn && !b.isBuiltIn) return -1;
      if (!a.isBuiltIn && b.isBuiltIn) return 1;
      
      if (a.lastUsed && b.lastUsed) {
        return b.lastUsed.getTime() - a.lastUsed.getTime();
      }
      if (a.lastUsed && !b.lastUsed) return -1;
      if (!a.lastUsed && b.lastUsed) return 1;
      
      return a.name.localeCompare(b.name);
    });
  }

  /**
   * Get profile by ID
   */
  getProfile(id: string): ProcessingProfile | null {
    return this.profiles.find(profile => profile.id === id) || null;
  }

  /**
   * Get default profile
   */
  getDefaultProfile(): ProcessingProfile | null {
    return this.profiles.find(profile => profile.isDefault) || null;
  }

  /**
   * Create new profile
   */
  createProfile(
    name: string,
    settings: ProcessingProfile['settings'],
    options: {
      description?: string;
      isDefault?: boolean;
      tags?: string[];
    } = {}
  ): string {
    // Check if name already exists
    if (this.profiles.some(p => p.name === name)) {
      throw new Error(`Profile with name "${name}" already exists`);
    }

    const id = this.generateId();
    
    // If this is set as default, remove default from others
    if (options.isDefault) {
      this.profiles.forEach(profile => {
        profile.isDefault = false;
      });
    }

    const profile: ProcessingProfile = {
      id,
      name,
      description: options.description,
      settings: { ...settings },
      isDefault: options.isDefault || false,
      isBuiltIn: false,
      createdAt: new Date(),
      useCount: 0,
      tags: options.tags || []
    };

    this.profiles.push(profile);
    this.saveToStorage();

    return id;
  }

  /**
   * Update existing profile
   */
  updateProfile(
    id: string,
    updates: Partial<Omit<ProcessingProfile, 'id' | 'isBuiltIn' | 'createdAt'>>
  ): boolean {
    const profile = this.profiles.find(p => p.id === id);
    if (!profile || profile.isBuiltIn) {
      return false;
    }

    // Check if name change conflicts with existing profile
    if (updates.name && updates.name !== profile.name) {
      if (this.profiles.some(p => p.name === updates.name && p.id !== id)) {
        throw new Error(`Profile with name "${updates.name}" already exists`);
      }
    }

    // If setting as default, remove default from others
    if (updates.isDefault) {
      this.profiles.forEach(p => {
        if (p.id !== id) p.isDefault = false;
      });
    }

    // Apply updates
    Object.assign(profile, updates);
    this.saveToStorage();

    return true;
  }

  /**
   * Delete profile
   */
  deleteProfile(id: string): boolean {
    const index = this.profiles.findIndex(p => p.id === id);
    if (index === -1) return false;

    const profile = this.profiles[index];
    if (profile.isBuiltIn) return false;

    this.profiles.splice(index, 1);
    
    // If deleted profile was default, set first built-in as default
    if (profile.isDefault) {
      const firstBuiltIn = this.profiles.find(p => p.isBuiltIn);
      if (firstBuiltIn) {
        firstBuiltIn.isDefault = true;
      }
    }

    this.saveToStorage();
    return true;
  }

  /**
   * Duplicate profile
   */
  duplicateProfile(id: string, newName?: string): string | null {
    const originalProfile = this.profiles.find(p => p.id === id);
    if (!originalProfile) return null;

    const name = newName || `${originalProfile.name} (Copy)`;
    
    // Ensure unique name
    let finalName = name;
    let counter = 1;
    while (this.profiles.some(p => p.name === finalName)) {
      finalName = `${name} ${counter}`;
      counter++;
    }

    return this.createProfile(finalName, originalProfile.settings, {
      description: originalProfile.description,
      tags: [...originalProfile.tags]
    });
  }

  /**
   * Use profile (increment use count and update last used)
   */
  useProfile(id: string): ProcessingProfile | null {
    const profile = this.profiles.find(p => p.id === id);
    if (!profile) return null;

    profile.useCount++;
    profile.lastUsed = new Date();
    this.saveToStorage();

    return profile;
  }

  /**
   * Set default profile
   */
  setDefaultProfile(id: string): boolean {
    const profile = this.profiles.find(p => p.id === id);
    if (!profile) return false;

    // Remove default from all profiles
    this.profiles.forEach(p => {
      p.isDefault = false;
    });

    // Set new default
    profile.isDefault = true;
    this.saveToStorage();

    return true;
  }

  /**
   * Search profiles
   */
  searchProfiles(query: string): ProcessingProfile[] {
    const searchTerm = query.toLowerCase();
    return this.profiles.filter(profile =>
      profile.name.toLowerCase().includes(searchTerm) ||
      (profile.description && profile.description.toLowerCase().includes(searchTerm)) ||
      profile.tags.some(tag => tag.toLowerCase().includes(searchTerm))
    );
  }

  /**
   * Get profiles by tag
   */
  getProfilesByTag(tag: string): ProcessingProfile[] {
    return this.profiles.filter(profile =>
      profile.tags.includes(tag)
    );
  }

  /**
   * Get all tags
   */
  getAllTags(): string[] {
    const tags = new Set<string>();
    this.profiles.forEach(profile => {
      profile.tags.forEach(tag => tags.add(tag));
    });
    return Array.from(tags).sort();
  }

  /**
   * Get profile statistics
   */
  getStats(): ProfileStats {
    const totalProfiles = this.profiles.length;
    const customProfiles = this.profiles.filter(p => !p.isBuiltIn).length;
    const builtInProfiles = this.profiles.filter(p => p.isBuiltIn).length;
    
    const mostUsedProfile = this.profiles.reduce((max, profile) => 
      profile.useCount > (max?.useCount || 0) ? profile : max, 
      null as ProcessingProfile | null
    );

    const recentlyUsed = this.profiles
      .filter(p => p.lastUsed)
      .sort((a, b) => (b.lastUsed?.getTime() || 0) - (a.lastUsed?.getTime() || 0))
      .slice(0, 5);

    return {
      totalProfiles,
      customProfiles,
      builtInProfiles,
      mostUsedProfile,
      recentlyUsed
    };
  }

  /**
   * Export profiles to JSON
   */
  exportProfiles(): string {
    const customProfiles = this.profiles.filter(p => !p.isBuiltIn);
    return JSON.stringify({
      profiles: customProfiles,
      exportedAt: new Date().toISOString()
    }, null, 2);
  }

  /**
   * Import profiles from JSON
   */
  importProfiles(jsonData: string): boolean {
    try {
      const data = JSON.parse(jsonData);
      
      if (!data.profiles || !Array.isArray(data.profiles)) {
        throw new Error('Invalid profile data format');
      }

      let importedCount = 0;
      
      for (const profileData of data.profiles) {
        if (this.isValidProfile(profileData)) {
          // Ensure unique name
          let name = profileData.name;
          let counter = 1;
          while (this.profiles.some(p => p.name === name)) {
            name = `${profileData.name} (${counter})`;
            counter++;
          }

          const id = this.generateId();
          const profile: ProcessingProfile = {
            ...profileData,
            id,
            name,
            isBuiltIn: false,
            isDefault: false,
            createdAt: new Date(profileData.createdAt || Date.now()),
            lastUsed: profileData.lastUsed ? new Date(profileData.lastUsed) : undefined
          };

          this.profiles.push(profile);
          importedCount++;
        }
      }

      if (importedCount > 0) {
        this.saveToStorage();
      }

      return importedCount > 0;
    } catch (error) {
      console.error('Failed to import profiles:', error);
      return false;
    }
  }

  /**
   * Initialize built-in profiles
   */
  private initializeBuiltInProfiles(): void {
    const builtInProfiles: Omit<ProcessingProfile, 'id' | 'createdAt'>[] = [
      {
        name: 'Quick Transcription',
        description: 'Fast transcription with basic settings',
        settings: {
          language: 'auto',
          modelSize: 'base',
          includeMetadata: false,
          autoSave: true,
          outputFormat: 'txt'
        },
        isDefault: true,
        isBuiltIn: true,
        useCount: 0,
        tags: ['quick', 'basic']
      },
      {
        name: 'High Quality',
        description: 'Best quality transcription with large model',
        settings: {
          language: 'auto',
          modelSize: 'large',
          includeMetadata: true,
          autoSave: true,
          outputFormat: 'docx'
        },
        isDefault: false,
        isBuiltIn: true,
        useCount: 0,
        tags: ['quality', 'detailed']
      },
      {
        name: 'Korean Optimized',
        description: 'Optimized settings for Korean language',
        settings: {
          language: 'ko',
          modelSize: 'medium',
          includeMetadata: true,
          autoSave: true,
          outputFormat: 'txt'
        },
        isDefault: false,
        isBuiltIn: true,
        useCount: 0,
        tags: ['korean', 'language-specific']
      },
      {
        name: 'English Meetings',
        description: 'Optimized for English meeting recordings',
        settings: {
          language: 'en',
          modelSize: 'medium',
          includeMetadata: true,
          autoSave: true,
          outputFormat: 'docx'
        },
        isDefault: false,
        isBuiltIn: true,
        useCount: 0,
        tags: ['english', 'meetings', 'business']
      },
      {
        name: 'Fast Draft',
        description: 'Quick draft with minimal processing',
        settings: {
          language: 'auto',
          modelSize: 'tiny',
          includeMetadata: false,
          autoSave: false,
          outputFormat: 'txt'
        },
        isDefault: false,
        isBuiltIn: true,
        useCount: 0,
        tags: ['fast', 'draft', 'minimal']
      }
    ];

    builtInProfiles.forEach(profileData => {
      const profile: ProcessingProfile = {
        ...profileData,
        id: this.generateId(),
        createdAt: new Date()
      };
      this.profiles.push(profile);
    });
  }

  /**
   * Validate profile data
   */
  private isValidProfile(profile: any): boolean {
    return profile &&
           typeof profile.name === 'string' &&
           profile.settings &&
           typeof profile.settings.language === 'string' &&
           typeof profile.settings.modelSize === 'string' &&
           typeof profile.settings.includeMetadata === 'boolean' &&
           typeof profile.settings.autoSave === 'boolean' &&
           typeof profile.settings.outputFormat === 'string';
  }

  /**
   * Load profiles from localStorage
   */
  private loadFromStorage(): void {
    try {
      if (typeof localStorage !== 'undefined') {
        const data = localStorage.getItem(this.storageKey);
        if (data) {
          const parsed = JSON.parse(data);
          const customProfiles = parsed
            .filter((p: any) => !p.isBuiltIn && this.isValidProfile(p))
            .map((p: any) => ({
              ...p,
              createdAt: new Date(p.createdAt),
              lastUsed: p.lastUsed ? new Date(p.lastUsed) : undefined
            }));
          
          this.profiles.push(...customProfiles);
        }
      }
    } catch (error) {
      console.error('Failed to load profiles from storage:', error);
    }
  }

  /**
   * Save profiles to localStorage
   */
  private saveToStorage(): void {
    try {
      if (typeof localStorage !== 'undefined') {
        const customProfiles = this.profiles.filter(p => !p.isBuiltIn);
        localStorage.setItem(this.storageKey, JSON.stringify(customProfiles));
      }
    } catch (error) {
      console.error('Failed to save profiles to storage:', error);
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `profile_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export singleton instance
export const profilesService = ProfilesService.getInstance();

// Export types
export type { ProcessingProfile, ProfileStats };