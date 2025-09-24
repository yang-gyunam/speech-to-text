# Performance Testing Guide

This guide provides comprehensive performance testing procedures for the Tauri GUI Speech-to-Text application.

## Performance Testing Overview

### Objectives
- Ensure application meets performance requirements
- Identify performance bottlenecks
- Validate resource usage is within acceptable limits
- Compare performance with CLI version
- Test scalability with various workloads

### Key Performance Indicators (KPIs)
- **Startup Time**: Time from launch to fully functional UI
- **Processing Speed**: Audio processing time vs. audio duration ratio
- **Memory Usage**: Peak and average memory consumption
- **CPU Usage**: Peak and average CPU utilization
- **UI Responsiveness**: Time to respond to user interactions
- **File I/O Performance**: File read/write speeds
- **Concurrent Processing**: Performance with multiple simultaneous operations

## Test Environment Setup

### Hardware Requirements
**Minimum Test Configuration**:
- MacBook Air M1 (8GB RAM, 256GB SSD)
- macOS 12.0
- No other intensive applications running

**Recommended Test Configuration**:
- MacBook Pro M2 (16GB RAM, 512GB SSD)
- macOS 13.0+
- Controlled background processes

**High-End Test Configuration**:
- Mac Studio M2 Ultra (64GB RAM, 1TB SSD)
- macOS 14.0+
- Simulated high-load environment

### Software Tools
- **Activity Monitor**: Built-in macOS resource monitoring
- **Instruments**: Xcode profiling tools
- **htop**: Enhanced process monitoring
- **Custom Performance Scripts**: Automated measurement tools

### Test Data Sets
```
performance-test-data/
├── micro/          # < 1 minute files
│   ├── 10s-clear.m4a
│   ├── 30s-noisy.wav
│   └── 45s-mixed.mp3
├── small/          # 1-5 minute files
│   ├── 2min-lecture.m4a
│   ├── 3min-interview.wav
│   └── 5min-meeting.mp3
├── medium/         # 5-30 minute files
│   ├── 10min-presentation.m4a
│   ├── 20min-podcast.wav
│   └── 30min-conference.mp3
├── large/          # 30+ minute files
│   ├── 45min-lecture.m4a
│   ├── 60min-meeting.wav
│   └── 90min-seminar.mp3
└── stress/         # Stress test files
    ├── 3hour-conference.m4a
    ├── batch-20-files/
    └── concurrent-test-set/
```

## Performance Test Scenarios

### 1. Application Startup Performance

#### 1.1 Cold Start Performance
**Objective**: Measure startup time from system boot

**Procedure**:
1. Restart macOS
2. Wait for system to fully load (2 minutes)
3. Launch application
4. Measure time to fully functional UI

**Measurements**:
- Time to splash screen
- Time to main window
- Time to fully responsive UI
- Memory usage at startup
- CPU usage during startup

**Acceptance Criteria**:
- Cold start: ≤ 8 seconds
- Memory at startup: ≤ 150MB
- CPU usage peak: ≤ 80% for ≤ 3 seconds

#### 1.2 Warm Start Performance
**Objective**: Measure startup time with system cache

**Procedure**:
1. Launch application once and close
2. Wait 30 seconds
3. Launch application again
4. Measure startup metrics

**Acceptance Criteria**:
- Warm start: ≤ 3 seconds
- Memory at startup: ≤ 120MB

#### 1.3 Startup Under Load
**Objective**: Test startup performance under system load

**Procedure**:
1. Create system load (CPU/Memory intensive tasks)
2. Launch application
3. Measure startup performance
4. Compare with baseline

**Acceptance Criteria**:
- Startup time increase: ≤ 50% vs baseline
- Application remains functional

### 2. Processing Performance

#### 2.1 Single File Processing Speed
**Objective**: Measure processing speed for various file sizes

**Test Matrix**:
| File Duration | Expected Processing Time | Max Acceptable Time |
|---------------|-------------------------|-------------------|
| 10 seconds    | 5-15 seconds           | 30 seconds        |
| 1 minute      | 30-60 seconds          | 2 minutes         |
| 5 minutes     | 2-5 minutes            | 8 minutes         |
| 30 minutes    | 10-20 minutes          | 35 minutes        |
| 60 minutes    | 20-40 minutes          | 70 minutes        |

**Procedure**:
1. Process each test file individually
2. Record processing start and end times
3. Monitor resource usage throughout
4. Verify transcription quality
5. Compare with CLI version performance

**Measurements**:
- Processing time ratio (processing time / audio duration)
- Peak memory usage during processing
- Average CPU usage
- Disk I/O operations
- GPU usage (if applicable)

#### 2.2 Batch Processing Performance
**Objective**: Test performance with multiple files

**Test Cases**:
- 5 small files (1-2 minutes each)
- 10 medium files (5-10 minutes each)
- 3 large files (30+ minutes each)
- Mixed batch (various sizes)

**Procedure**:
1. Select batch of test files
2. Start batch processing
3. Monitor system resources
4. Record individual and total processing times
5. Verify all files processed successfully

**Measurements**:
- Total batch processing time
- Individual file processing times
- Resource usage patterns
- Memory growth over time
- Processing efficiency vs. sequential processing

#### 2.3 Concurrent Processing Limits
**Objective**: Determine optimal concurrent processing limits

**Procedure**:
1. Start with 1 concurrent job
2. Gradually increase concurrent jobs (2, 3, 4, 5+)
3. Monitor performance degradation
4. Identify optimal concurrent job count
5. Test system stability at limits

**Measurements**:
- Processing speed vs. concurrent jobs
- Memory usage scaling
- CPU utilization efficiency
- System responsiveness
- Error rates at high concurrency

### 3. Memory Performance

#### 3.1 Memory Usage Patterns
**Objective**: Analyze memory consumption patterns

**Test Scenarios**:
- Idle application memory usage
- Memory during file processing
- Memory growth with multiple files
- Memory cleanup after processing
- Memory leaks detection

**Procedure**:
1. Monitor baseline memory usage
2. Process files of increasing sizes
3. Record memory usage at key points
4. Force garbage collection
5. Check for memory leaks

**Measurements**:
- Baseline memory usage
- Peak memory during processing
- Memory per file in batch processing
- Memory cleanup efficiency
- Memory leak detection

**Acceptance Criteria**:
- Baseline usage: ≤ 100MB
- Peak usage: ≤ 2GB for typical files
- Memory cleanup: ≥ 90% after processing
- No detectable memory leaks

#### 3.2 Memory Stress Testing
**Objective**: Test memory limits and error handling

**Procedure**:
1. Process extremely large files (>500MB)
2. Process many files simultaneously
3. Simulate low memory conditions
4. Test memory pressure handling

**Acceptance Criteria**:
- Graceful handling of memory pressure
- Clear error messages for memory issues
- No system crashes or freezes

### 4. UI Responsiveness

#### 4.1 UI Response Times
**Objective**: Measure UI responsiveness during operations

**Test Cases**:
- Button click response time
- File drag and drop response
- Settings panel opening
- Progress updates frequency
- Text editing responsiveness

**Procedure**:
1. Perform UI actions during idle state
2. Perform UI actions during processing
3. Measure response times
4. Test UI during high system load

**Measurements**:
- Click-to-response time
- Drag-and-drop recognition time
- Progress update frequency
- Text input lag
- Animation smoothness

**Acceptance Criteria**:
- UI response time: ≤ 100ms (idle), ≤ 500ms (processing)
- Progress updates: ≥ 2 times per second
- Text input lag: ≤ 50ms
- Animations: ≥ 30 FPS

#### 4.2 UI Performance Under Load
**Objective**: Test UI responsiveness during intensive operations

**Procedure**:
1. Start large file processing
2. Interact with UI elements
3. Test all major UI functions
4. Monitor UI thread performance

**Acceptance Criteria**:
- UI remains responsive during processing
- No UI freezes or hangs
- All functions accessible during processing

### 5. File I/O Performance

#### 5.1 File Reading Performance
**Objective**: Measure file reading speeds

**Test Cases**:
- Small files (< 10MB)
- Medium files (10-100MB)
- Large files (> 100MB)
- Multiple files simultaneously

**Measurements**:
- File reading speed (MB/s)
- Time to file validation
- Memory usage during file reading
- Disk I/O patterns

#### 5.2 File Writing Performance
**Objective**: Measure transcription output writing

**Test Cases**:
- Small transcriptions (< 1KB)
- Medium transcriptions (1-100KB)
- Large transcriptions (> 100KB)
- Multiple simultaneous writes

**Measurements**:
- File writing speed
- Time to save completion
- Disk space usage
- Write operation reliability

### 6. Network Performance (if applicable)

#### 6.1 Model Download Performance
**Objective**: Test model downloading (if implemented)

**Measurements**:
- Download speed
- Progress reporting accuracy
- Resume capability
- Error handling

#### 6.2 Cloud Processing Performance
**Objective**: Test cloud processing (if implemented)

**Measurements**:
- Upload speed
- Processing latency
- Download speed
- Offline handling

## Performance Monitoring Tools

### Built-in Monitoring
```typescript
// Performance monitoring utility
class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map();
  
  startTimer(operation: string): string {
    const id = `${operation}-${Date.now()}`;
    performance.mark(`${id}-start`);
    return id;
  }
  
  endTimer(id: string): number {
    performance.mark(`${id}-end`);
    performance.measure(id, `${id}-start`, `${id}-end`);
    
    const measure = performance.getEntriesByName(id)[0];
    const duration = measure.duration;
    
    const operation = id.split('-')[0];
    if (!this.metrics.has(operation)) {
      this.metrics.set(operation, []);
    }
    this.metrics.get(operation)!.push(duration);
    
    return duration;
  }
  
  getStats(operation: string) {
    const times = this.metrics.get(operation) || [];
    return {
      count: times.length,
      average: times.reduce((a, b) => a + b, 0) / times.length,
      min: Math.min(...times),
      max: Math.max(...times),
      median: times.sort()[Math.floor(times.length / 2)]
    };
  }
}
```

### System Resource Monitoring
```bash
#!/bin/bash
# performance-monitor.sh

# Monitor system resources during testing
LOG_FILE="performance-test-$(date +%Y%m%d-%H%M%S).log"

echo "Starting performance monitoring..." | tee $LOG_FILE
echo "Timestamp,CPU%,Memory(MB),Disk_Read(MB/s),Disk_Write(MB/s)" | tee -a $LOG_FILE

while true; do
    TIMESTAMP=$(date +%H:%M:%S)
    CPU=$(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    MEMORY=$(ps -o pid,rss -p $(pgrep "tauri-gui-app") | tail -1 | awk '{print $2/1024}')
    
    echo "$TIMESTAMP,$CPU,$MEMORY,0,0" | tee -a $LOG_FILE
    sleep 1
done
```

## Performance Test Execution

### Pre-Test Setup
1. Close all unnecessary applications
2. Ensure stable system state
3. Clear application caches
4. Prepare test data
5. Set up monitoring tools

### Test Execution Process
1. **Baseline Measurement**: Record system performance without application
2. **Individual Tests**: Run each performance test scenario
3. **Data Collection**: Gather all performance metrics
4. **Analysis**: Compare results against acceptance criteria
5. **Reporting**: Document findings and recommendations

### Post-Test Analysis
1. **Statistical Analysis**: Calculate averages, percentiles, trends
2. **Bottleneck Identification**: Identify performance limiting factors
3. **Comparison Analysis**: Compare with previous versions and CLI
4. **Optimization Recommendations**: Suggest performance improvements

## Performance Benchmarking

### Baseline Performance Targets
Based on CLI version performance and user expectations:

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Startup Time | < 3s | < 8s | > 8s |
| Processing Ratio | < 0.5x | < 1.0x | > 1.0x |
| Memory Usage | < 500MB | < 2GB | > 2GB |
| UI Response | < 100ms | < 500ms | > 500ms |
| File I/O | > 50MB/s | > 10MB/s | < 10MB/s |

### Performance Regression Testing
1. **Automated Benchmarks**: Run performance tests on each build
2. **Trend Analysis**: Track performance over time
3. **Regression Detection**: Alert on performance degradation
4. **Performance Gates**: Block releases that don't meet criteria

## Troubleshooting Performance Issues

### Common Performance Problems
1. **Slow Startup**: Check for unnecessary initialization
2. **High Memory Usage**: Look for memory leaks or inefficient algorithms
3. **Poor Processing Speed**: Verify model loading and processing pipeline
4. **UI Lag**: Check for blocking operations on main thread
5. **File I/O Bottlenecks**: Optimize file reading/writing operations

### Performance Debugging Tools
1. **Xcode Instruments**: Detailed profiling and analysis
2. **Chrome DevTools**: For web-based components
3. **Activity Monitor**: Real-time system monitoring
4. **Console Logs**: Application-specific performance logs

### Performance Optimization Strategies
1. **Code Optimization**: Improve algorithm efficiency
2. **Memory Management**: Reduce memory footprint
3. **Async Operations**: Prevent UI blocking
4. **Caching**: Cache frequently used data
5. **Resource Management**: Optimize resource usage patterns

## Performance Test Report Template

```markdown
# Performance Test Report

**Date**: 
**Version**: 
**Tester**: 
**Environment**: 

## Executive Summary
- Overall performance rating: Pass/Fail
- Key findings
- Critical issues
- Recommendations

## Test Results Summary
| Test Category | Pass/Fail | Notes |
|---------------|-----------|-------|
| Startup Performance | | |
| Processing Performance | | |
| Memory Performance | | |
| UI Responsiveness | | |
| File I/O Performance | | |

## Detailed Results
[Include detailed metrics and analysis]

## Performance Trends
[Compare with previous versions]

## Recommendations
[List optimization suggestions]

## Appendix
[Raw data and detailed logs]
```