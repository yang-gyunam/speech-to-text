# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### For Critical Security Issues

1. **DO NOT** create a public GitHub issue
2. Email us directly at: [security@yourproject.com] (replace with actual email)
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity (typically 30-90 days)

### What to Expect

1. We'll acknowledge receipt of your report
2. We'll investigate and validate the issue
3. We'll work on a fix and coordinate disclosure
4. We'll credit you in our security advisory (unless you prefer to remain anonymous)

## Security Best Practices

### For Users

- Always download releases from official sources
- Verify checksums when provided
- Keep the application updated to the latest version
- Report suspicious behavior immediately

### For Contributors

- Follow secure coding practices
- Never commit secrets, API keys, or credentials
- Use dependency scanning tools
- Perform security reviews for significant changes

## Known Security Considerations

- This application processes audio files locally - no data is sent to external servers
- File system access is limited to user-selected directories
- Network access is minimal and only for updates (if enabled)

## Security Features

- **Local Processing**: All audio transcription happens on your device
- **No Cloud Dependencies**: No external API calls for core functionality
- **Sandboxed Environment**: Runs in Tauri's security sandbox
- **Code Signing**: macOS releases are signed and notarized

## Vulnerability Disclosure Policy

We follow responsible disclosure practices:

1. Security researchers have 90 days to report vulnerabilities before public disclosure
2. We aim to fix critical vulnerabilities within 30 days
3. We'll coordinate with researchers on disclosure timing
4. We maintain a security advisory for all resolved issues

## Contact

For security-related questions or concerns:
- Email: [security@yourproject.com] (replace with actual email)
- For non-security issues, use GitHub Issues

Thank you for helping keep our project secure!