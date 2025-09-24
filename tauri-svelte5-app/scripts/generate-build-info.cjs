#!/usr/bin/env node

/**
 * Generate Build Information
 * 
 * This script generates build metadata that gets embedded into the application
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function getBuildInfo() {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  
  let gitCommit = 'unknown';
  let gitBranch = 'unknown';
  let gitTag = 'unknown';
  
  try {
    gitCommit = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
    gitBranch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf8' }).trim();
    
    // Try to get the current tag
    try {
      gitTag = execSync('git describe --tags --exact-match HEAD', { encoding: 'utf8' }).trim();
    } catch {
      // No tag on current commit
      gitTag = execSync('git describe --tags --abbrev=0', { encoding: 'utf8' }).trim() + '-dev';
    }
  } catch (error) {
    console.warn('Warning: Could not get git information:', error.message);
  }
  
  const buildInfo = {
    name: packageJson.name,
    version: packageJson.version,
    description: packageJson.description,
    build: {
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'development',
      target: process.env.BUILD_TARGET || 'development',
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch,
      git: {
        commit: gitCommit,
        branch: gitBranch,
        tag: gitTag
      }
    },
    features: {
      audioFormats: ['m4a', 'wav', 'mp3', 'aac', 'flac'],
      languages: ['ko', 'en'],
      models: ['tiny', 'base', 'small', 'medium', 'large'],
      exportFormats: ['txt', 'docx', 'pdf']
    }
  };
  
  return buildInfo;
}

function generateBuildInfo() {
  console.log('📦 Generating build information...');
  
  const buildInfo = getBuildInfo();
  
  // Write to src directory for frontend access
  const frontendPath = path.join('src', 'build-info.json');
  fs.writeFileSync(frontendPath, JSON.stringify(buildInfo, null, 2));
  console.log(`✅ Frontend build info written to: ${frontendPath}`);
  
  // Write to src-tauri for backend access
  const backendPath = path.join('src-tauri', 'build-info.json');
  fs.writeFileSync(backendPath, JSON.stringify(buildInfo, null, 2));
  console.log(`✅ Backend build info written to: ${backendPath}`);
  
  // Generate TypeScript definitions
  const tsDefinitions = `// Auto-generated build information types
export interface BuildInfo {
  name: string;
  version: string;
  description: string;
  build: {
    timestamp: string;
    environment: string;
    target: string;
    nodeVersion: string;
    platform: string;
    arch: string;
    git: {
      commit: string;
      branch: string;
      tag: string;
    };
  };
  features: {
    audioFormats: string[];
    languages: string[];
    models: string[];
    exportFormats: string[];
  };
}

export const buildInfo: BuildInfo = ${JSON.stringify(buildInfo, null, 2)};
`;
  
  const tsPath = path.join('src', 'build-info.ts');
  fs.writeFileSync(tsPath, tsDefinitions);
  console.log(`✅ TypeScript definitions written to: ${tsPath}`);
  
  // Log build information
  console.log('\n📋 Build Information:');
  console.log(`  Name: ${buildInfo.name}`);
  console.log(`  Version: ${buildInfo.version}`);
  console.log(`  Environment: ${buildInfo.build.environment}`);
  console.log(`  Target: ${buildInfo.build.target}`);
  console.log(`  Git Commit: ${buildInfo.build.git.commit.substring(0, 8)}`);
  console.log(`  Git Branch: ${buildInfo.build.git.branch}`);
  console.log(`  Git Tag: ${buildInfo.build.git.tag}`);
  console.log(`  Build Time: ${buildInfo.build.timestamp}`);
  
  return buildInfo;
}

// Run if called directly
if (require.main === module) {
  try {
    generateBuildInfo();
    console.log('\n🎉 Build information generated successfully!');
  } catch (error) {
    console.error('❌ Failed to generate build information:', error);
    process.exit(1);
  }
}

module.exports = { generateBuildInfo, getBuildInfo };