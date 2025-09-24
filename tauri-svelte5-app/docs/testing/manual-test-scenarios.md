# Manual Testing Scenarios

This document outlines comprehensive manual testing scenarios for the Tauri GUI Speech-to-Text application.

## Test Environment Setup

### Prerequisites
- macOS 12.0 or later
- Node.js 18+ and npm
- Rust toolchain
- Test audio files in various formats (.m4a, .wav, .mp3, .aac, .flac)
- Different file sizes (small: <1MB, medium: 1-50MB, large: >50MB)

### Test Data Preparation
Create a test data folder with:
```
test-data/
├── audio/
│   ├── small/
│   │   ├── short-korean.m4a (30 seconds, Korean speech)
│   │   ├── short-english.wav (30 seconds, English speech)
│   │   └── short-silence.mp3 (30 seconds, mostly silence)
│   ├── medium/
│   │   ├── medium-korean.m4a (5 minutes, Korean speech)
│   │   ├── medium-english.wav (5 minutes, English speech)
│   │   └── medium-mixed.mp3 (5 minutes, Korean + English)
│   ├── large/
│   │   ├── large-lecture.m4a (30+ minutes, Korean lecture)
│   │   └── large-meeting.wav (60+ minutes, meeting recording)
│   └── invalid/
│       ├── corrupted.m4a (corrupted audio file)
│       ├── text-file.txt (text file with .m4a extension)
│       └── empty.wav (0 bytes file)
└── expected-results/
    ├── short-korean.txt (expected transcription)
    ├── short-english.txt (expected transcription)
    └── ... (other expected results)
```

## User Workflow Testing

### Scenario 1: First-Time User Experience

**Objective**: Test the onboarding and initial user experience

**Steps**:
1. Launch the application for the first time
2. Observe the initial interface
3. Check for any onboarding or help elements
4. Verify default settings are appropriate
5. Test the help/documentation access

**Expected Results**:
- Clean, intuitive interface loads quickly
- Default settings are sensible (Korean language, base model)
- Help information is easily accessible
- No errors or crashes on first launch

**Pass/Fail Criteria**:
- [ ] Application launches within 5 seconds
- [ ] Interface is responsive and well-organized
- [ ] Default settings match user expectations
- [ ] Help documentation is comprehensive and accessible

### Scenario 2: Single File Processing Workflow

**Objective**: Test the complete single file processing workflow

**Test Cases**:

#### 2.1 Drag and Drop Upload
**Steps**:
1. Open the application
2. Drag a small Korean audio file (.m4a) to the drop zone
3. Verify file is recognized and displayed
4. Check file information (name, size, format, duration)
5. Start processing
6. Monitor progress indicators
7. Review transcription results
8. Edit the transcription text
9. Save the results

**Expected Results**:
- File is immediately recognized and validated
- File information is accurate
- Progress is clearly indicated with time estimates
- Transcription quality is acceptable (>80% accuracy for clear speech)
- Text editing works smoothly
- Save operation completes successfully

**Pass/Fail Criteria**:
- [ ] Drag and drop works on first attempt
- [ ] File validation is immediate (<1 second)
- [ ] Progress updates are smooth and informative
- [ ] Transcription accuracy meets expectations
- [ ] Text editing is responsive
- [ ] Save operation succeeds without errors

#### 2.2 Browse and Select Upload
**Steps**:
1. Click "Browse Files" button
2. Navigate to test audio file
3. Select file and confirm
4. Proceed with processing workflow
5. Compare results with drag-and-drop method

**Expected Results**:
- File browser opens correctly
- File selection works as expected
- Processing results are identical to drag-and-drop method

#### 2.3 Different Audio Formats
**Repeat single file workflow with**:
- .wav file (medium size, English speech)
- .mp3 file (small size, mixed language)
- .aac file (medium size, Korean speech)
- .flac file (large size, high quality)

**Expected Results**:
- All supported formats process successfully
- Quality differences are minimal between formats
- Processing time scales appropriately with file size

### Scenario 3: Batch Processing Workflow

**Objective**: Test multiple file processing capabilities

**Steps**:
1. Select multiple audio files (3-5 files of different formats)
2. Drag all files to the drop zone simultaneously
3. Verify batch mode is activated
4. Review file list and individual file status
5. Start batch processing
6. Monitor overall progress and individual file progress
7. Handle any processing failures gracefully
8. Review batch results summary
9. Access individual transcription results

**Expected Results**:
- Batch mode activates automatically for multiple files
- Individual file status is clearly displayed
- Progress tracking works for both overall and individual files
- Failed files don't stop the entire batch
- Results are organized and easily accessible

**Pass/Fail Criteria**:
- [ ] Batch mode detection works reliably
- [ ] Progress tracking is accurate and informative
- [ ] Error handling doesn't crash the application
- [ ] Results organization is logical and user-friendly
- [ ] Performance remains acceptable with multiple files

### Scenario 4: Settings and Configuration

**Objective**: Test settings management and persistence

**Steps**:
1. Open settings panel
2. Change language setting (Korean ↔ English)
3. Change model size (base → large → small)
4. Change output directory
5. Toggle metadata inclusion
6. Toggle auto-save
7. Change theme (light/dark/system)
8. Save settings and restart application
9. Verify settings persistence
10. Test settings impact on processing

**Expected Results**:
- All settings are clearly labeled and functional
- Changes take effect immediately where appropriate
- Settings persist across application restarts
- Model size changes affect processing quality/speed appropriately

**Pass/Fail Criteria**:
- [ ] Settings interface is intuitive and complete
- [ ] All settings function as expected
- [ ] Settings persistence works reliably
- [ ] Performance impact of settings is reasonable

### Scenario 5: Error Handling and Recovery

**Objective**: Test application resilience and error recovery

**Test Cases**:

#### 5.1 Invalid File Handling
**Steps**:
1. Try to upload a text file with .m4a extension
2. Try to upload a corrupted audio file
3. Try to upload an extremely large file (>500MB)
4. Try to upload an empty file

**Expected Results**:
- Clear error messages for each invalid file type
- Application remains stable
- User can continue with valid files

#### 5.2 Processing Interruption
**Steps**:
1. Start processing a large file
2. Cancel processing mid-way
3. Try to start new processing immediately
4. Restart application during processing
5. Test network interruption (if applicable)

**Expected Results**:
- Cancellation works immediately
- Application state resets properly
- No corrupted files or partial results
- Graceful handling of interruptions

#### 5.3 System Resource Constraints
**Steps**:
1. Process multiple large files simultaneously
2. Monitor system resource usage
3. Test with low available disk space
4. Test with limited memory conditions

**Expected Results**:
- Application handles resource constraints gracefully
- Clear error messages for resource issues
- No system crashes or freezes

### Scenario 6: Export and Sharing Features

**Objective**: Test result export and sharing capabilities

**Steps**:
1. Complete a transcription
2. Test copy to clipboard functionality
3. Export to different formats (TXT, DOCX, PDF)
4. Test "Reveal in Finder" functionality
5. Test sharing options (if available)
6. Verify exported file quality and formatting

**Expected Results**:
- All export formats work correctly
- Exported files maintain proper formatting
- Metadata is included when requested
- File operations integrate well with macOS

## Performance Testing

### Scenario 7: Performance and Responsiveness

**Objective**: Verify application performance under various conditions

**Test Cases**:

#### 7.1 Startup Performance
**Steps**:
1. Measure application startup time (cold start)
2. Measure application startup time (warm start)
3. Test startup with various system loads

**Acceptance Criteria**:
- Cold start: < 10 seconds
- Warm start: < 5 seconds
- UI responsive within 2 seconds

#### 7.2 Processing Performance
**Steps**:
1. Process files of various sizes and measure times
2. Compare processing times with CLI version
3. Test concurrent processing limits
4. Monitor memory usage during processing

**Acceptance Criteria**:
- Processing speed within 20% of CLI version
- Memory usage < 2GB for typical files
- UI remains responsive during processing

#### 7.3 Large File Handling
**Steps**:
1. Process files > 100MB
2. Process files > 1 hour duration
3. Test batch processing with 10+ files
4. Monitor system impact

**Acceptance Criteria**:
- Large files process without crashes
- Progress reporting remains accurate
- System remains usable during processing

## Accessibility Testing

### Scenario 8: Accessibility and Usability

**Objective**: Ensure application is accessible to all users

**Test Cases**:

#### 8.1 Keyboard Navigation
**Steps**:
1. Navigate entire interface using only keyboard
2. Test Tab order and focus indicators
3. Test keyboard shortcuts
4. Verify screen reader compatibility

**Expected Results**:
- All functionality accessible via keyboard
- Logical tab order
- Clear focus indicators
- Proper ARIA labels and roles

#### 8.2 Visual Accessibility
**Steps**:
1. Test with high contrast mode
2. Test with different zoom levels (100%-200%)
3. Test color blind accessibility
4. Test in both light and dark themes

**Expected Results**:
- Interface remains usable at all zoom levels
- Color is not the only way to convey information
- Sufficient contrast ratios
- Both themes are fully functional

#### 8.3 Motor Accessibility
**Steps**:
1. Test with larger click targets
2. Test drag and drop alternatives
3. Test with reduced motion preferences

**Expected Results**:
- Click targets meet minimum size requirements
- Alternative input methods available
- Respects system motion preferences

## Stress Testing

### Scenario 9: Stress and Edge Cases

**Objective**: Test application limits and edge cases

**Test Cases**:

#### 9.1 File Limits
**Steps**:
1. Upload maximum number of files (100+)
2. Upload files with very long names
3. Upload files with special characters in names
4. Test with files in nested directories

#### 9.2 Content Edge Cases
**Steps**:
1. Process silent audio files
2. Process very noisy audio files
3. Process files with multiple languages
4. Process very short files (<5 seconds)
5. Process very long files (>2 hours)

#### 9.3 System Integration
**Steps**:
1. Test with multiple monitors
2. Test with different screen resolutions
3. Test with system sleep/wake cycles
4. Test with system updates/restarts

## User Acceptance Testing

### Scenario 10: Real-World Usage Scenarios

**Objective**: Test realistic user workflows

**Test Cases**:

#### 10.1 Student Use Case
**Scenario**: Student transcribing lecture recordings
**Steps**:
1. Process 1-hour lecture recording
2. Edit transcription for accuracy
3. Export to DOCX for note-taking
4. Save multiple lectures in organized folders

#### 10.2 Professional Use Case
**Scenario**: Professional transcribing meeting recordings
**Steps**:
1. Process multiple meeting recordings in batch
2. Include metadata for organization
3. Export to different formats for different stakeholders
4. Integrate with existing workflow

#### 10.3 Accessibility Use Case
**Scenario**: User with hearing impairment transcribing audio content
**Steps**:
1. Process various audio content types
2. Use keyboard-only navigation
3. Rely on visual progress indicators
4. Export for further processing

## Test Execution Guidelines

### Before Testing
1. Ensure clean test environment
2. Prepare all test data
3. Document system specifications
4. Clear any previous application data

### During Testing
1. Document all steps and observations
2. Take screenshots of any issues
3. Note performance metrics
4. Record any unexpected behavior

### After Testing
1. Compile test results
2. Categorize issues by severity
3. Verify all test scenarios completed
4. Prepare detailed test report

## Issue Reporting Template

### Bug Report Format
```
**Title**: Brief description of the issue

**Severity**: Critical/High/Medium/Low

**Environment**:
- OS Version: 
- App Version: 
- Hardware: 

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Result**: 

**Actual Result**: 

**Screenshots/Logs**: 

**Workaround**: (if any)
```

### Test Results Summary
```
**Test Scenario**: 
**Date**: 
**Tester**: 
**Overall Result**: Pass/Fail
**Issues Found**: 
**Notes**: 
```