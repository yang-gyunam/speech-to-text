/**
 * Build Configuration for Speech to Text Application
 * 
 * This file contains build-time configuration and utilities
 * for packaging and distributing the Tauri application.
 */

const fs = require('fs');
const path = require('path');

// Build configuration
const buildConfig = {
  // Application metadata
  app: {
    name: 'Speech to Text',
    version: '1.0.0',
    identifier: 'com.gnyang.speechtotext.app',
    description: 'Convert audio files to text using AI',
    author: 'Speech to Text Team',
    homepage: 'https://github.com/[YOUR_USERNAME]/speech-to-text-desktop',
    repository: 'https://github.com/[YOUR_USERNAME]/speech-to-text-desktop.git'
  },

  // Build targets
  targets: {
    macos: {
      enabled: true,
      arch: ['x86_64', 'aarch64'],
      minimumVersion: '12.0'
    },
    windows: {
      enabled: false, // Disable for now
      arch: ['x86_64']
    },
    linux: {
      enabled: false, // Disable for now
      arch: ['x86_64']
    }
  },

  // Code signing configuration
  signing: {
    macos: {
      identity: process.env.APPLE_SIGNING_IDENTITY || null,
      teamId: process.env.APPLE_TEAM_ID || null,
      provisioningProfile: process.env.APPLE_PROVISIONING_PROFILE || null
    }
  },

  // Notarization configuration
  notarization: {
    macos: {
      appleId: process.env.APPLE_ID || null,
      appleIdPassword: process.env.APPLE_ID_PASSWORD || null,
      teamId: process.env.APPLE_TEAM_ID || null
    }
  },

  // Distribution configuration
  distribution: {
    dmg: {
      background: 'dmg-background.png',
      iconSize: 80,
      windowSize: {
        width: 660,
        height: 400
      },
      contents: [
        { x: 180, y: 170, type: 'file', path: 'Speech to Text.app' },
        { x: 480, y: 170, type: 'link', path: '/Applications' }
      ]
    }
  },

  // Build optimization
  optimization: {
    minify: true,
    treeshake: true,
    bundleAnalyzer: false
  }
};

// Utility functions
const utils = {
  /**
   * Get the current build environment
   */
  getEnvironment() {
    return process.env.NODE_ENV || 'development';
  },

  /**
   * Check if we're building for production
   */
  isProduction() {
    return this.getEnvironment() === 'production';
  },

  /**
   * Get the build target platform
   */
  getTarget() {
    return process.env.BUILD_TARGET || 'macos';
  },

  /**
   * Validate build environment
   */
  validateEnvironment() {
    const errors = [];

    // Check Node.js version
    const nodeVersion = process.version;
    const requiredNodeVersion = '18.0.0';
    if (!this.compareVersions(nodeVersion.slice(1), requiredNodeVersion)) {
      errors.push(`Node.js ${requiredNodeVersion} or higher is required. Current: ${nodeVersion}`);
    }

    // Check for required environment variables in production
    if (this.isProduction()) {
      const requiredEnvVars = [
        'APPLE_SIGNING_IDENTITY',
        'APPLE_TEAM_ID'
      ];

      requiredEnvVars.forEach(envVar => {
        if (!process.env[envVar]) {
          console.warn(`Warning: ${envVar} environment variable is not set`);
        }
      });
    }

    return errors;
  },

  /**
   * Compare version strings
   */
  compareVersions(version1, version2) {
    const v1parts = version1.split('.').map(Number);
    const v2parts = version2.split('.').map(Number);

    for (let i = 0; i < Math.max(v1parts.length, v2parts.length); i++) {
      const v1part = v1parts[i] || 0;
      const v2part = v2parts[i] || 0;

      if (v1part > v2part) return true;
      if (v1part < v2part) return false;
    }
    return true; // Equal versions
  },

  /**
   * Generate build metadata
   */
  generateBuildMetadata() {
    return {
      buildTime: new Date().toISOString(),
      buildEnvironment: this.getEnvironment(),
      buildTarget: this.getTarget(),
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch
    };
  },

  /**
   * Create build info file
   */
  createBuildInfo() {
    const buildInfo = {
      ...buildConfig.app,
      build: this.generateBuildMetadata()
    };

    const buildInfoPath = path.join(__dirname, 'src', 'build-info.json');
    fs.writeFileSync(buildInfoPath, JSON.stringify(buildInfo, null, 2));
    console.log('Build info created:', buildInfoPath);
  }
};

// Pre-build validation
function preBuildValidation() {
  console.log('🔍 Validating build environment...');
  
  const errors = utils.validateEnvironment();
  if (errors.length > 0) {
    console.error('❌ Build validation failed:');
    errors.forEach(error => console.error(`  - ${error}`));
    process.exit(1);
  }

  console.log('✅ Build environment validation passed');
}

// Post-build tasks
function postBuildTasks() {
  console.log('🎉 Build completed successfully!');
  
  // Generate build metadata
  utils.createBuildInfo();
  
  // Log build information
  const metadata = utils.generateBuildMetadata();
  console.log('📦 Build Information:');
  console.log(`  - Environment: ${metadata.buildEnvironment}`);
  console.log(`  - Target: ${metadata.buildTarget}`);
  console.log(`  - Build Time: ${metadata.buildTime}`);
  console.log(`  - Node Version: ${metadata.nodeVersion}`);
}

module.exports = {
  buildConfig,
  utils,
  preBuildValidation,
  postBuildTasks
};