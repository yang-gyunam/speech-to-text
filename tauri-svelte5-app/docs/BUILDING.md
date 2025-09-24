# Building and Deployment Guide

This guide covers building, packaging, and deploying the Speech to Text application for macOS.

## Build Requirements

### System Requirements

#### macOS Development
- **macOS**: 12.0 (Monterey) or later
- **Xcode**: Latest version with Command Line Tools
- **Node.js**: 18.0.0 or later
- **Rust**: Latest stable version
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space for build artifacts

#### Development Tools
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Rust via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Install Node.js (via Homebrew)
brew install node

# Verify installations
node --version    # Should be 18.0.0+
rustc --version   # Should be latest stable
cargo --version   # Should be latest stable
```

### Project Dependencies

```bash
# Clone the repository
git clone https://github.com/speechtotext/tauri-gui-app.git
cd tauri-gui-app

# Install Node.js dependencies
npm install

# Install Rust dependencies (automatic with Tauri)
npm run tauri:deps

# Verify build environment
npm run build:check
```

## Build Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Development environment
NODE_ENV=development
TAURI_DEBUG=true
RUST_LOG=debug

# Build configuration
TAURI_PRIVATE_KEY=path/to/private.key
TAURI_KEY_PASSWORD=your_key_password

# Code signing (for release builds)
APPLE_CERTIFICATE_PASSWORD=cert_password
APPLE_ID=your@apple.id
APPLE_TEAM_ID=TEAM123456
APPLE_APP_SPECIFIC_PASSWORD=app_specific_password

# Notarization
APPLE_NOTARIZATION_APPLE_ID=your@apple.id
APPLE_NOTARIZATION_TEAM_ID=TEAM123456
APPLE_NOTARIZATION_PASSWORD=app_specific_password
```

### Build Scripts

The project includes several build scripts in `package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "tauri:dev": "tauri dev",
    "tauri:build": "tauri build",
    "tauri:build:debug": "tauri build --debug",
    "build:check": "npm run type-check && npm run lint && npm run test",
    "build:dev": "npm run build && npm run tauri:build:debug",
    "build:prod": "npm run build:check && npm run build && npm run tauri:build",
    "build:release": "npm run build:prod -- --config src-tauri/tauri.release.conf.json"
  }
}
```

## Development Builds

### Quick Development Build

```bash
# Start development server with hot reload
npm run tauri:dev

# This will:
# 1. Start Vite dev server for frontend
# 2. Compile Rust backend
# 3. Launch the application with hot reload
# 4. Enable debug logging and developer tools
```

### Debug Build

```bash
# Build debug version (faster compilation, includes debug symbols)
npm run build:dev

# Output location:
# src-tauri/target/debug/bundle/macos/Speech to Text.app
```

### Development Configuration

The development build uses `src-tauri/tauri.conf.json`:

```json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:1420",
    "distDir": "../dist"
  },
  "tauri": {
    "bundle": {
      "active": true,
      "targets": "all",
      "identifier": "com.gnyang.speechtotext.app.dev",
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/128x128@2x.png",
        "icons/icon.icns",
        "icons/icon.ico"
      ]
    }
  }
}
```

## Production Builds

### Release Build Process

```bash
# Full production build with all checks
npm run build:release

# This will:
# 1. Run type checking
# 2. Run linting
# 3. Run all tests
# 4. Build optimized frontend
# 5. Compile optimized Rust backend
# 6. Create signed and notarized app bundle
# 7. Generate DMG installer
```

### Build Targets

#### Intel (x86_64) Build
```bash
# Build for Intel Macs
rustup target add x86_64-apple-darwin
npm run build:prod -- --target x86_64-apple-darwin
```

#### Apple Silicon (aarch64) Build
```bash
# Build for Apple Silicon Macs
rustup target add aarch64-apple-darwin
npm run build:prod -- --target aarch64-apple-darwin
```

#### Universal Binary
```bash
# Build universal binary (both architectures)
npm run build:universal

# This creates a universal app that runs natively on both Intel and Apple Silicon
```

### Release Configuration

Production builds use `src-tauri/tauri.release.conf.json`:

```json
{
  "tauri": {
    "bundle": {
      "identifier": "com.gnyang.speechtotext.app",
      "category": "Productivity",
      "shortDescription": "Convert audio to text with AI",
      "longDescription": "A powerful desktop application that converts audio recordings to text using OpenAI's Whisper AI model.",
      "macOS": {
        "frameworks": [],
        "minimumSystemVersion": "12.0",
        "exceptionDomain": "",
        "signingIdentity": "Developer ID Application: Your Name (TEAM123456)",
        "providerShortName": "TEAM123456",
        "entitlements": "entitlements.plist"
      }
    },
    "updater": {
      "active": true,
      "endpoints": [
        "https://releases.speechtotext.app/{{target}}/{{arch}}/{{current_version}}"
      ],
      "dialog": true,
      "pubkey": "your_public_key_here"
    }
  }
}
```

## Code Signing and Notarization

### Prerequisites

1. **Apple Developer Account**: Required for distribution
2. **Developer ID Certificate**: For code signing
3. **App-Specific Password**: For notarization

### Certificate Setup

```bash
# Import certificate to keychain
security import DeveloperIDApplication.p12 -k ~/Library/Keychains/login.keychain

# Verify certificate
security find-identity -v -p codesigning

# Should show: "Developer ID Application: Your Name (TEAM123456)"
```

### Entitlements Configuration

Create `src-tauri/entitlements.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.files.downloads.read-write</key>
    <true/>
</dict>
</plist>
```

### Automated Signing Script

Create `scripts/sign-and-notarize.sh`:

```bash
#!/bin/bash
set -e

APP_PATH="$1"
BUNDLE_ID="com.gnyang.speechtotext.app"
SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM123456)"
APPLE_ID="your@apple.id"
TEAM_ID="TEAM123456"
APP_PASSWORD="app-specific-password"

echo "Signing application..."
codesign --deep --force --verify --verbose --sign "$SIGNING_IDENTITY" \
    --options runtime --entitlements src-tauri/entitlements.plist "$APP_PATH"

echo "Creating DMG..."
hdiutil create -volname "Speech to Text" -srcfolder "$APP_PATH" \
    -ov -format UDZO "Speech-to-Text-Installer.dmg"

echo "Signing DMG..."
codesign --sign "$SIGNING_IDENTITY" "Speech-to-Text-Installer.dmg"

echo "Notarizing DMG..."
xcrun notarytool submit "Speech-to-Text-Installer.dmg" \
    --apple-id "$APPLE_ID" \
    --team-id "$TEAM_ID" \
    --password "$APP_PASSWORD" \
    --wait

echo "Stapling notarization..."
xcrun stapler staple "Speech-to-Text-Installer.dmg"

echo "Verifying notarization..."
spctl -a -t open --context context:primary-signature "Speech-to-Text-Installer.dmg"

echo "Build complete!"
```

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/build.yml`:

```yaml
name: Build and Release

on:
  push:
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: 'npm'
          
      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: aarch64-apple-darwin,x86_64-apple-darwin
          
      - name: Install dependencies
        run: npm ci
        
      - name: Run tests
        run: npm run test:all
        
      - name: Type check
        run: npm run type-check
        
      - name: Lint
        run: npm run lint

  build:
    needs: test
    runs-on: macos-latest
    if: startsWith(github.ref, 'refs/tags/')
    
    strategy:
      matrix:
        target: [x86_64-apple-darwin, aarch64-apple-darwin]
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: 'npm'
          
      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: ${{ matrix.target }}
          
      - name: Install dependencies
        run: npm ci
        
      - name: Import Code-Signing Certificates
        uses: Apple-Actions/import-codesign-certs@v1
        with:
          p12-file-base64: ${{ secrets.APPLE_CERTIFICATE }}
          p12-password: ${{ secrets.APPLE_CERTIFICATE_PASSWORD }}
          
      - name: Build application
        run: npm run build:prod -- --target ${{ matrix.target }}
        env:
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
          APPLE_APP_SPECIFIC_PASSWORD: ${{ secrets.APPLE_APP_SPECIFIC_PASSWORD }}
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: speech-to-text-${{ matrix.target }}
          path: |
            src-tauri/target/${{ matrix.target }}/release/bundle/macos/*.app
            src-tauri/target/${{ matrix.target }}/release/bundle/dmg/*.dmg

  release:
    needs: build
    runs-on: macos-latest
    if: startsWith(github.ref, 'refs/tags/')
    
    steps:
      - name: Download artifacts
        uses: actions/download-artifact@v4
        
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            speech-to-text-x86_64-apple-darwin/**/*.dmg
            speech-to-text-aarch64-apple-darwin/**/*.dmg
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Build Optimization

### Frontend Optimization

#### Vite Configuration (`vite.config.ts`)
```typescript
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  
  // Build optimization
  build: {
    target: 'esnext',
    minify: 'esbuild',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['svelte'],
          ui: ['lucide-svelte'],
          tauri: ['@tauri-apps/api']
        }
      }
    }
  },
  
  // Development optimization
  server: {
    port: 1420,
    strictPort: true
  },
  
  // Environment variables
  envPrefix: ['VITE_', 'TAURI_']
});
```

#### Bundle Analysis
```bash
# Analyze bundle size
npm run build:analyze

# This generates a bundle analysis report
# Check dist/stats.html for detailed breakdown
```

### Rust Optimization

#### Cargo Configuration (`src-tauri/Cargo.toml`)
```toml
[profile.release]
panic = "abort"
codegen-units = 1
lto = true
opt-level = "s"
strip = true

[profile.dev]
debug = true
opt-level = 0

# Dependencies optimization
[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["rt-multi-thread", "macros"] }
tauri = { version = "1.5", features = ["api-all"] }
```

#### Build Features
```bash
# Build with specific features
cargo build --release --features "production,optimized"

# Build without default features
cargo build --release --no-default-features --features "minimal"
```

## Distribution

### DMG Creation

#### Custom DMG Script (`scripts/create-dmg.sh`)
```bash
#!/bin/bash
set -e

APP_NAME="Speech to Text"
APP_PATH="$1"
DMG_NAME="Speech-to-Text-Installer"
VOLUME_NAME="Speech to Text"

# Create temporary DMG
hdiutil create -size 200m -fs HFS+ -volname "$VOLUME_NAME" temp.dmg

# Mount DMG
hdiutil attach temp.dmg -mountpoint /Volumes/"$VOLUME_NAME"

# Copy app to DMG
cp -R "$APP_PATH" /Volumes/"$VOLUME_NAME"/

# Create Applications symlink
ln -s /Applications /Volumes/"$VOLUME_NAME"/Applications

# Copy background image and set up DMG appearance
mkdir /Volumes/"$VOLUME_NAME"/.background
cp dmg-background.png /Volumes/"$VOLUME_NAME"/.background/

# Set DMG properties with AppleScript
osascript scripts/setup-dmg.applescript "$VOLUME_NAME"

# Unmount DMG
hdiutil detach /Volumes/"$VOLUME_NAME"

# Convert to compressed DMG
hdiutil convert temp.dmg -format UDZO -o "$DMG_NAME.dmg"

# Clean up
rm temp.dmg

echo "DMG created: $DMG_NAME.dmg"
```

### Update System

#### Update Server Configuration
```json
{
  "version": "1.0.0",
  "notes": "Initial release with core transcription features",
  "pub_date": "2024-01-15T12:00:00Z",
  "platforms": {
    "darwin-x86_64": {
      "signature": "signature_here",
      "url": "https://releases.speechtotext.app/v1.0.0/Speech-to-Text-x86_64.dmg"
    },
    "darwin-aarch64": {
      "signature": "signature_here", 
      "url": "https://releases.speechtotext.app/v1.0.0/Speech-to-Text-aarch64.dmg"
    }
  }
}
```

#### Update Signature Generation
```bash
# Generate update signature
tauri signer sign -f "Speech-to-Text-Installer.dmg" -k private.key

# Verify signature
tauri signer verify -f "Speech-to-Text-Installer.dmg" -k public.key -s signature
```

## Troubleshooting

### Common Build Issues

#### Node.js Version Mismatch
```bash
# Error: Node.js version not supported
# Solution: Use Node Version Manager
nvm install 18
nvm use 18
```

#### Rust Compilation Errors
```bash
# Error: Rust compiler not found
# Solution: Reinstall Rust toolchain
rustup self update
rustup update stable
rustup default stable
```

#### Code Signing Failures
```bash
# Error: Code signing identity not found
# Solution: Check certificate installation
security find-identity -v -p codesigning

# Error: Entitlements not valid
# Solution: Verify entitlements.plist syntax
plutil -lint src-tauri/entitlements.plist
```

#### Notarization Issues
```bash
# Error: Notarization failed
# Solution: Check notarization status
xcrun notarytool log --apple-id your@apple.id --team-id TEAM123456 submission-id

# Error: App-specific password invalid
# Solution: Generate new app-specific password at appleid.apple.com
```

### Build Performance

#### Faster Development Builds
```bash
# Use debug profile for faster compilation
export CARGO_PROFILE_DEV_DEBUG=false
export CARGO_PROFILE_DEV_OPT_LEVEL=1

# Enable incremental compilation
export CARGO_INCREMENTAL=1

# Use faster linker (if available)
export RUSTFLAGS="-C link-arg=-fuse-ld=lld"
```

#### Parallel Builds
```bash
# Set number of parallel jobs
export CARGO_BUILD_JOBS=8

# Use all available cores
export CARGO_BUILD_JOBS=$(nproc)
```

### Debugging Build Issues

#### Verbose Output
```bash
# Enable verbose Cargo output
cargo build --verbose

# Enable Tauri debug output
TAURI_DEBUG=true npm run tauri:build

# Enable Rust logging
RUST_LOG=debug npm run tauri:build
```

#### Clean Builds
```bash
# Clean all build artifacts
npm run clean

# Clean Rust artifacts only
cargo clean

# Clean Node.js artifacts only
rm -rf node_modules dist
npm install
```

## Build Metrics

### Performance Benchmarks

| Build Type | Intel Mac | Apple Silicon | Universal |
|------------|-----------|---------------|-----------|
| Debug | 2-3 min | 1-2 min | 3-4 min |
| Release | 5-7 min | 3-5 min | 8-10 min |
| Full CI | 10-15 min | 8-12 min | 15-20 min |

### Size Metrics

| Component | Size | Compressed |
|-----------|------|------------|
| App Bundle | ~150MB | ~50MB |
| DMG Installer | ~60MB | ~45MB |
| Update Package | ~40MB | ~30MB |

This comprehensive build guide covers all aspects of building, signing, and distributing the Speech to Text application. Follow these procedures to ensure consistent, reliable builds for all deployment scenarios.