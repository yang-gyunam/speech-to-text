#!/usr/bin/env node

/**
 * Build Validation Script
 * 
 * This script validates the build environment and requirements
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
  reset: '\x1b[0m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function checkNodeVersion() {
  const nodeVersion = process.version;
  const requiredVersion = '18.0.0';
  
  const current = nodeVersion.slice(1).split('.').map(Number);
  const required = requiredVersion.split('.').map(Number);
  
  for (let i = 0; i < 3; i++) {
    if (current[i] > required[i]) return true;
    if (current[i] < required[i]) return false;
  }
  return true;
}

function checkCommand(command, name) {
  try {
    execSync(`which ${command}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function checkFile(filePath, description) {
  if (fs.existsSync(filePath)) {
    return true;
  }
  return false;
}

function checkRustToolchain() {
  try {
    const rustVersion = execSync('rustc --version', { encoding: 'utf8' });
    const cargoVersion = execSync('cargo --version', { encoding: 'utf8' });
    return { rust: rustVersion.trim(), cargo: cargoVersion.trim() };
  } catch {
    return null;
  }
}

function checkTauriCLI() {
  try {
    const tauriVersion = execSync('npm list @tauri-apps/cli --depth=0', { encoding: 'utf8' });
    return tauriVersion.includes('@tauri-apps/cli');
  } catch {
    return false;
  }
}

function validateBuildEnvironment() {
  log('🔍 Validating build environment...', 'blue');
  
  const checks = [];
  
  // Node.js version check
  if (checkNodeVersion()) {
    log(`✅ Node.js version: ${process.version}`, 'green');
    checks.push({ name: 'Node.js', status: 'pass' });
  } else {
    log(`❌ Node.js version ${process.version} is too old. Required: 18.0.0+`, 'red');
    checks.push({ name: 'Node.js', status: 'fail' });
  }
  
  // npm check
  if (checkCommand('npm', 'npm')) {
    try {
      const npmVersion = execSync('npm --version', { encoding: 'utf8' }).trim();
      log(`✅ npm version: ${npmVersion}`, 'green');
      checks.push({ name: 'npm', status: 'pass' });
    } catch {
      log('❌ npm not working properly', 'red');
      checks.push({ name: 'npm', status: 'fail' });
    }
  } else {
    log('❌ npm not found', 'red');
    checks.push({ name: 'npm', status: 'fail' });
  }
  
  // Rust toolchain check
  const rustInfo = checkRustToolchain();
  if (rustInfo) {
    log(`✅ Rust: ${rustInfo.rust}`, 'green');
    log(`✅ Cargo: ${rustInfo.cargo}`, 'green');
    checks.push({ name: 'Rust', status: 'pass' });
  } else {
    log('❌ Rust toolchain not found', 'red');
    log('   Install from: https://rustup.rs/', 'yellow');
    checks.push({ name: 'Rust', status: 'fail' });
  }
  
  // Tauri CLI check
  if (checkTauriCLI()) {
    log('✅ Tauri CLI installed', 'green');
    checks.push({ name: 'Tauri CLI', status: 'pass' });
  } else {
    log('❌ Tauri CLI not found', 'red');
    log('   Install with: npm install @tauri-apps/cli', 'yellow');
    checks.push({ name: 'Tauri CLI', status: 'fail' });
  }
  
  // macOS specific checks
  if (process.platform === 'darwin') {
    log('\n🍎 macOS specific checks:', 'blue');
    
    // Xcode Command Line Tools
    if (checkCommand('xcrun', 'Xcode Command Line Tools')) {
      log('✅ Xcode Command Line Tools installed', 'green');
      checks.push({ name: 'Xcode CLI Tools', status: 'pass' });
    } else {
      log('❌ Xcode Command Line Tools not found', 'red');
      log('   Install with: xcode-select --install', 'yellow');
      checks.push({ name: 'Xcode CLI Tools', status: 'fail' });
    }
    
    // Check for code signing certificates
    try {
      const certs = execSync('security find-identity -v -p codesigning', { encoding: 'utf8' });
      if (certs.includes('Developer ID Application')) {
        log('✅ Code signing certificates found', 'green');
        checks.push({ name: 'Code Signing', status: 'pass' });
      } else {
        log('⚠️  No Developer ID Application certificates found', 'yellow');
        log('   Code signing will not be available', 'yellow');
        checks.push({ name: 'Code Signing', status: 'warning' });
      }
    } catch {
      log('⚠️  Could not check code signing certificates', 'yellow');
      checks.push({ name: 'Code Signing', status: 'warning' });
    }
  }
  
  // File structure checks
  log('\n📁 File structure checks:', 'blue');
  
  const requiredFiles = [
    { path: 'package.json', description: 'Package configuration' },
    { path: 'src-tauri/tauri.conf.json', description: 'Tauri configuration' },
    { path: 'src-tauri/Cargo.toml', description: 'Rust configuration' },
    { path: 'src-tauri/src/main.rs', description: 'Rust main file' },
    { path: 'src/main.ts', description: 'Svelte main file' },
    { path: 'tsconfig.json', description: 'TypeScript configuration' },
    { path: 'vite.config.ts', description: 'Vite configuration' }
  ];
  
  requiredFiles.forEach(file => {
    if (checkFile(file.path, file.description)) {
      log(`✅ ${file.description}: ${file.path}`, 'green');
      checks.push({ name: file.description, status: 'pass' });
    } else {
      log(`❌ Missing ${file.description}: ${file.path}`, 'red');
      checks.push({ name: file.description, status: 'fail' });
    }
  });
  
  // Dependencies check
  log('\n📦 Dependencies check:', 'blue');
  
  if (fs.existsSync('node_modules')) {
    log('✅ Node modules installed', 'green');
    checks.push({ name: 'Node modules', status: 'pass' });
  } else {
    log('❌ Node modules not found', 'red');
    log('   Run: npm install', 'yellow');
    checks.push({ name: 'Node modules', status: 'fail' });
  }
  
  // Summary
  log('\n📊 Validation Summary:', 'blue');
  
  const passed = checks.filter(c => c.status === 'pass').length;
  const failed = checks.filter(c => c.status === 'fail').length;
  const warnings = checks.filter(c => c.status === 'warning').length;
  
  log(`✅ Passed: ${passed}`, 'green');
  if (warnings > 0) log(`⚠️  Warnings: ${warnings}`, 'yellow');
  if (failed > 0) log(`❌ Failed: ${failed}`, 'red');
  
  if (failed > 0) {
    log('\n❌ Build validation failed. Please fix the issues above.', 'red');
    return false;
  } else if (warnings > 0) {
    log('\n⚠️  Build validation passed with warnings.', 'yellow');
    return true;
  } else {
    log('\n✅ Build validation passed successfully!', 'green');
    return true;
  }
}

function main() {
  log('🔧 Build Environment Validation', 'blue');
  log('================================\n', 'blue');
  
  const isValid = validateBuildEnvironment();
  
  if (!isValid) {
    process.exit(1);
  }
  
  log('\n🚀 Ready to build!', 'green');
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { validateBuildEnvironment };