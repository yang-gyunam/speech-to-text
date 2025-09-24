#!/bin/bash

# Setup Code Signing for macOS
# This script helps set up code signing certificates and profiles

set -e

echo "🔐 Setting up macOS Code Signing..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script must be run on macOS"
    exit 1
fi

# Check for Xcode Command Line Tools
if ! command -v xcrun &> /dev/null; then
    print_error "Xcode Command Line Tools not found. Please install with: xcode-select --install"
    exit 1
fi

print_status "Xcode Command Line Tools found"

# Check for existing certificates
echo "🔍 Checking for existing certificates..."

DEVELOPER_CERTS=$(security find-identity -v -p codesigning | grep "Developer ID Application" | wc -l)
if [ "$DEVELOPER_CERTS" -gt 0 ]; then
    print_status "Found $DEVELOPER_CERTS Developer ID Application certificate(s)"
    security find-identity -v -p codesigning | grep "Developer ID Application"
else
    print_warning "No Developer ID Application certificates found"
    echo "To sign your app for distribution outside the Mac App Store, you need:"
    echo "1. A Developer ID Application certificate from Apple Developer Portal"
    echo "2. Import the certificate into your Keychain"
fi

# Check for installer certificates
INSTALLER_CERTS=$(security find-identity -v -p codesigning | grep "Developer ID Installer" | wc -l)
if [ "$INSTALLER_CERTS" -gt 0 ]; then
    print_status "Found $INSTALLER_CERTS Developer ID Installer certificate(s)"
else
    print_warning "No Developer ID Installer certificates found (needed for PKG installers)"
fi

# Check for notarization setup
echo ""
echo "🔍 Checking notarization setup..."

if [ -z "$APPLE_ID" ]; then
    print_warning "APPLE_ID environment variable not set"
    echo "Set it with: export APPLE_ID='your-apple-id@example.com'"
else
    print_status "APPLE_ID is set: $APPLE_ID"
fi

if [ -z "$APPLE_ID_PASSWORD" ]; then
    print_warning "APPLE_ID_PASSWORD environment variable not set"
    echo "Create an app-specific password at: https://appleid.apple.com/account/manage"
    echo "Then set it with: export APPLE_ID_PASSWORD='your-app-specific-password'"
else
    print_status "APPLE_ID_PASSWORD is set"
fi

if [ -z "$APPLE_TEAM_ID" ]; then
    print_warning "APPLE_TEAM_ID environment variable not set"
    echo "Find your Team ID at: https://developer.apple.com/account/#/membership"
    echo "Then set it with: export APPLE_TEAM_ID='YOUR_TEAM_ID'"
else
    print_status "APPLE_TEAM_ID is set: $APPLE_TEAM_ID"
fi

# Create environment template
echo ""
echo "📝 Creating environment template..."

cat > .env.signing.template << EOF
# Code Signing Environment Variables
# Copy this file to .env.signing and fill in your values

# Apple Developer Account
APPLE_ID=your-apple-id@example.com
APPLE_ID_PASSWORD=your-app-specific-password
APPLE_TEAM_ID=YOUR_TEAM_ID

# Code Signing Identity (from security find-identity -v -p codesigning)
APPLE_SIGNING_IDENTITY="Developer ID Application: Your Name (TEAM_ID)"

# Optional: Specific certificate SHA-1 hash
# APPLE_CERTIFICATE_HASH=your-certificate-hash

# Tauri Updater (if using auto-updates)
# TAURI_SIGNING_PRIVATE_KEY=path/to/private.key
# TAURI_SIGNING_PRIVATE_KEY_PASSWORD=your-key-password
EOF

print_status "Created .env.signing.template"

# Check if .env.signing exists
if [ -f ".env.signing" ]; then
    print_status ".env.signing file already exists"
else
    print_warning ".env.signing file not found"
    echo "Copy the template and fill in your values:"
    echo "cp .env.signing.template .env.signing"
fi

# Verify signing setup
echo ""
echo "🧪 Testing code signing setup..."

# Create a simple test file
TEST_FILE="test_signing.txt"
echo "Test file for code signing" > "$TEST_FILE"

# Try to sign the test file
if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
    SIGNING_IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed 's/.*) //' | sed 's/ ".*"//')
    
    if codesign --sign "$SIGNING_IDENTITY" --timestamp --options runtime "$TEST_FILE" 2>/dev/null; then
        print_status "Code signing test successful"
        
        # Verify the signature
        if codesign --verify --verbose "$TEST_FILE" 2>/dev/null; then
            print_status "Signature verification successful"
        else
            print_warning "Signature verification failed"
        fi
    else
        print_warning "Code signing test failed"
    fi
else
    print_warning "No signing identity available for testing"
fi

# Clean up test file
rm -f "$TEST_FILE"

echo ""
echo "📋 Summary:"
echo "1. Install certificates from Apple Developer Portal"
echo "2. Set up environment variables (use .env.signing.template)"
echo "3. Test with: npm run tauri build"
echo ""
echo "For more information, see:"
echo "- https://tauri.app/v1/guides/distribution/sign-macos"
echo "- https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"

print_status "Code signing setup complete!"