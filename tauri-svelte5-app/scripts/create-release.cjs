#!/usr/bin/env node

/**
 * Create Release Script
 * 
 * This script automates the release creation process
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for output
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  reset: '\x1b[0m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function execCommand(command, options = {}) {
  try {
    const result = execSync(command, { 
      encoding: 'utf8', 
      stdio: options.silent ? 'pipe' : 'inherit',
      ...options 
    });
    return result.trim();
  } catch (error) {
    throw new Error(`Command failed: ${command}\n${error.message}`);
  }
}

function validateVersion(version) {
  const versionRegex = /^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$/;
  return versionRegex.test(version);
}

function getCurrentVersion() {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  return packageJson.version;
}

function updateVersion(newVersion) {
  // Update package.json
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
  packageJson.version = newVersion;
  fs.writeFileSync('package.json', JSON.stringify(packageJson, null, 2) + '\n');
  
  // Update Cargo.toml
  const cargoToml = fs.readFileSync('src-tauri/Cargo.toml', 'utf8');
  const updatedCargoToml = cargoToml.replace(
    /^version = ".*"$/m,
    `version = "${newVersion}"`
  );
  fs.writeFileSync('src-tauri/Cargo.toml', updatedCargoToml);
  
  // Update tauri.conf.json
  const tauriConf = JSON.parse(fs.readFileSync('src-tauri/tauri.conf.json', 'utf8'));
  tauriConf.version = newVersion;
  fs.writeFileSync('src-tauri/tauri.conf.json', JSON.stringify(tauriConf, null, 2) + '\n');
  
  log(`✅ Updated version to ${newVersion}`, 'green');
}

function generateChangelog(version) {
  const changelogPath = 'CHANGELOG.md';
  const date = new Date().toISOString().split('T')[0];
  
  let changelog = '';
  if (fs.existsSync(changelogPath)) {
    changelog = fs.readFileSync(changelogPath, 'utf8');
  } else {
    changelog = '# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n';
  }
  
  const newEntry = `## [${version}] - ${date}

### Added
- New features and enhancements

### Changed
- Improvements and modifications

### Fixed
- Bug fixes and corrections

### Security
- Security improvements

`;
  
  // Insert new entry after the header
  const lines = changelog.split('\n');
  const headerEndIndex = lines.findIndex(line => line.startsWith('## '));
  
  if (headerEndIndex === -1) {
    changelog += newEntry;
  } else {
    lines.splice(headerEndIndex, 0, newEntry);
    changelog = lines.join('\n');
  }
  
  fs.writeFileSync(changelogPath, changelog);
  log(`✅ Generated changelog entry for ${version}`, 'green');
}

function createGitTag(version) {
  const tagName = `v${version}`;
  
  // Check if tag already exists
  try {
    execCommand(`git rev-parse ${tagName}`, { silent: true });
    log(`⚠️  Tag ${tagName} already exists`, 'yellow');
    return false;
  } catch {
    // Tag doesn't exist, we can create it
  }
  
  // Create and push tag
  execCommand(`git tag -a ${tagName} -m "Release ${version}"`);
  execCommand(`git push origin ${tagName}`);
  
  log(`✅ Created and pushed tag ${tagName}`, 'green');
  return true;
}

function buildRelease() {
  log('🔨 Building release...', 'blue');
  
  // Clean previous builds
  execCommand('npm run clean');
  
  // Generate build info
  execCommand('npm run generate-build-info');
  
  // Run tests
  log('🧪 Running tests...', 'blue');
  execCommand('npm run test:run');
  
  // Build the application
  log('📦 Building application...', 'blue');
  execCommand('npm run build:release');
  
  log('✅ Build completed successfully', 'green');
}

function createReleaseNotes(version) {
  const releaseNotesPath = `release-notes-${version}.md`;
  
  const template = `# Speech to Text v${version}

## What's New

### 🚀 New Features
- Feature 1: Description
- Feature 2: Description

### 🔧 Improvements
- Improvement 1: Description
- Improvement 2: Description

### 🐛 Bug Fixes
- Fix 1: Description
- Fix 2: Description

### 🔒 Security
- Security improvement 1
- Security improvement 2

## Installation

### macOS
1. Download the appropriate DMG file for your Mac:
   - Intel Macs: \`Speech-to-Text-x86_64.dmg\`
   - Apple Silicon Macs: \`Speech-to-Text-aarch64.dmg\`
2. Open the DMG file
3. Drag the app to your Applications folder
4. Launch from Applications

## System Requirements
- macOS 12.0 or later
- 4GB RAM minimum, 8GB recommended
- 1GB free disk space

## Support
Report issues at: https://github.com/speechtotext/tauri-gui-app/issues

---

**Full Changelog**: https://github.com/speechtotext/tauri-gui-app/compare/v${getPreviousVersion()}...v${version}
`;

  fs.writeFileSync(releaseNotesPath, template);
  log(`✅ Created release notes: ${releaseNotesPath}`, 'green');
  
  return releaseNotesPath;
}

function getPreviousVersion() {
  try {
    const tags = execCommand('git tag --sort=-version:refname', { silent: true });
    const tagList = tags.split('\n').filter(tag => tag.startsWith('v'));
    return tagList[0] || 'v0.0.0';
  } catch {
    return 'v0.0.0';
  }
}

function validateGitStatus() {
  try {
    const status = execCommand('git status --porcelain', { silent: true });
    if (status.length > 0) {
      log('⚠️  Working directory is not clean:', 'yellow');
      console.log(status);
      return false;
    }
    return true;
  } catch {
    log('❌ Failed to check git status', 'red');
    return false;
  }
}

function commitVersionChanges(version) {
  execCommand('git add package.json src-tauri/Cargo.toml src-tauri/tauri.conf.json CHANGELOG.md');
  execCommand(`git commit -m "chore: bump version to ${version}"`);
  execCommand('git push origin main');
  
  log('✅ Committed and pushed version changes', 'green');
}

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    log('❌ Please specify a version number', 'red');
    log('Usage: npm run create-release <version>', 'yellow');
    log('Example: npm run create-release 1.0.0', 'yellow');
    process.exit(1);
  }
  
  const newVersion = args[0];
  
  if (!validateVersion(newVersion)) {
    log('❌ Invalid version format. Use semantic versioning (e.g., 1.0.0)', 'red');
    process.exit(1);
  }
  
  const currentVersion = getCurrentVersion();
  
  log('🚀 Creating Release', 'magenta');
  log('==================', 'magenta');
  log(`Current version: ${currentVersion}`, 'cyan');
  log(`New version: ${newVersion}`, 'cyan');
  log('');
  
  // Validate git status
  if (!validateGitStatus()) {
    log('❌ Please commit or stash your changes before creating a release', 'red');
    process.exit(1);
  }
  
  try {
    // Update version numbers
    updateVersion(newVersion);
    
    // Generate changelog
    generateChangelog(newVersion);
    
    // Commit version changes
    commitVersionChanges(newVersion);
    
    // Build release
    buildRelease();
    
    // Create git tag
    const tagCreated = createGitTag(newVersion);
    
    if (tagCreated) {
      // Create release notes
      const releaseNotesPath = createReleaseNotes(newVersion);
      
      log('', 'reset');
      log('🎉 Release created successfully!', 'green');
      log('', 'reset');
      log('Next steps:', 'blue');
      log(`1. Edit release notes: ${releaseNotesPath}`, 'cyan');
      log('2. Wait for GitHub Actions to build artifacts', 'cyan');
      log('3. Create GitHub release with the generated tag', 'cyan');
      log('4. Upload build artifacts to the release', 'cyan');
      log('', 'reset');
      log(`GitHub Release URL: https://github.com/speechtotext/tauri-gui-app/releases/new?tag=v${newVersion}`, 'blue');
    } else {
      log('⚠️  Tag already exists, skipping GitHub release creation', 'yellow');
    }
    
  } catch (error) {
    log(`❌ Release creation failed: ${error.message}`, 'red');
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    log(`❌ Unexpected error: ${error.message}`, 'red');
    process.exit(1);
  });
}

module.exports = {
  validateVersion,
  getCurrentVersion,
  updateVersion,
  generateChangelog,
  createGitTag,
  buildRelease
};