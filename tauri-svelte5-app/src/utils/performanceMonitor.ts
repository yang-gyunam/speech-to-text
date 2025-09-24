/**
 * Performance monitoring and benchmarking utilities
 */

interface PerformanceMetric {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, any>;
}

interface BenchmarkResult {
  name: string;
  duration: number;
  iterations: number;
  averageTime: number;
  minTime: number;
  maxTime: number;
  metadata?: Record<string, any>;
}

interface SystemMetrics {
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  timing: {
    navigationStart: number;
    loadEventEnd: number;
    domContentLoaded: number;
  };
  resources: {
    totalResources: number;
    loadedResources: number;
    failedResources: number;
  };
}

class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics = new Map<string, PerformanceMetric>();
  private benchmarks = new Map<string, BenchmarkResult>();
  private observers: PerformanceObserver[] = [];

  private constructor() {
    this.initializeObservers();
  }

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  /**
   * Start measuring performance for a named operation
   */
  startMeasure(name: string, metadata?: Record<string, any>): void {
    const metric: PerformanceMetric = {
      name,
      startTime: performance.now(),
      metadata
    };
    
    this.metrics.set(name, metric);
    
    // Also use Performance API mark
    performance.mark(`${name}-start`);
  }

  /**
   * End measurement and calculate duration
   */
  endMeasure(name: string): number | null {
    const metric = this.metrics.get(name);
    if (!metric) {
      console.warn(`No measurement started for: ${name}`);
      return null;
    }

    const endTime = performance.now();
    const duration = endTime - metric.startTime;
    
    metric.endTime = endTime;
    metric.duration = duration;
    
    // Use Performance API measure
    performance.mark(`${name}-end`);
    performance.measure(name, `${name}-start`, `${name}-end`);
    
    return duration;
  }

  /**
   * Get measurement result
   */
  getMeasurement(name: string): PerformanceMetric | null {
    return this.metrics.get(name) || null;
  }

  /**
   * Run benchmark for a function
   */
  async benchmark(
    name: string,
    fn: () => Promise<any> | any,
    iterations: number = 10,
    metadata?: Record<string, any>
  ): Promise<BenchmarkResult> {
    const times: number[] = [];
    
    for (let i = 0; i < iterations; i++) {
      const startTime = performance.now();
      
      try {
        await fn();
      } catch (error) {
        console.error(`Benchmark ${name} iteration ${i} failed:`, error);
      }
      
      const endTime = performance.now();
      times.push(endTime - startTime);
    }

    const duration = times.reduce((sum, time) => sum + time, 0);
    const averageTime = duration / iterations;
    const minTime = Math.min(...times);
    const maxTime = Math.max(...times);

    const result: BenchmarkResult = {
      name,
      duration,
      iterations,
      averageTime,
      minTime,
      maxTime,
      metadata
    };

    this.benchmarks.set(name, result);
    return result;
  }

  /**
   * Get system performance metrics
   */
  getSystemMetrics(): SystemMetrics {
    const memory = this.getMemoryMetrics();
    const timing = this.getTimingMetrics();
    const resources = this.getResourceMetrics();

    return { memory, timing, resources };
  }

  /**
   * Get memory usage metrics
   */
  private getMemoryMetrics() {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        percentage: (memory.usedJSHeapSize / memory.totalJSHeapSize) * 100
      };
    }
    
    return { used: 0, total: 0, percentage: 0 };
  }

  /**
   * Get navigation timing metrics
   */
  private getTimingMetrics() {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    
    return {
      navigationStart: navigation?.navigationStart || 0,
      loadEventEnd: navigation?.loadEventEnd || 0,
      domContentLoaded: navigation?.domContentLoadedEventEnd || 0
    };
  }

  /**
   * Get resource loading metrics
   */
  private getResourceMetrics() {
    const resources = performance.getEntriesByType('resource');
    const totalResources = resources.length;
    const failedResources = resources.filter(r => r.transferSize === 0).length;
    const loadedResources = totalResources - failedResources;

    return {
      totalResources,
      loadedResources,
      failedResources
    };
  }

  /**
   * Initialize performance observers
   */
  private initializeObservers(): void {
    if (typeof PerformanceObserver === 'undefined') return;

    // Observe long tasks
    try {
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          console.warn('Long task detected:', {
            name: entry.name,
            duration: entry.duration,
            startTime: entry.startTime
          });
        }
      });
      
      longTaskObserver.observe({ entryTypes: ['longtask'] });
      this.observers.push(longTaskObserver);
    } catch (error) {
      console.log('Long task observer not supported');
    }

    // Observe layout shifts
    try {
      const layoutShiftObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if ((entry as any).value > 0.1) {
            console.warn('Layout shift detected:', {
              value: (entry as any).value,
              startTime: entry.startTime
            });
          }
        }
      });
      
      layoutShiftObserver.observe({ entryTypes: ['layout-shift'] });
      this.observers.push(layoutShiftObserver);
    } catch (error) {
      console.log('Layout shift observer not supported');
    }
  }

  /**
   * Get all benchmark results
   */
  getAllBenchmarks(): BenchmarkResult[] {
    return Array.from(this.benchmarks.values());
  }

  /**
   * Get all measurements
   */
  getAllMeasurements(): PerformanceMetric[] {
    return Array.from(this.metrics.values());
  }

  /**
   * Clear all metrics and benchmarks
   */
  clear(): void {
    this.metrics.clear();
    this.benchmarks.clear();
    performance.clearMarks();
    performance.clearMeasures();
  }

  /**
   * Generate performance report
   */
  generateReport(): string {
    const systemMetrics = this.getSystemMetrics();
    const measurements = this.getAllMeasurements();
    const benchmarks = this.getAllBenchmarks();

    let report = '=== Performance Report ===\n\n';
    
    // System metrics
    report += 'System Metrics:\n';
    report += `Memory Usage: ${(systemMetrics.memory.percentage).toFixed(2)}% (${(systemMetrics.memory.used / 1024 / 1024).toFixed(2)} MB)\n`;
    report += `Load Time: ${systemMetrics.timing.loadEventEnd - systemMetrics.timing.navigationStart}ms\n`;
    report += `Resources: ${systemMetrics.resources.loadedResources}/${systemMetrics.resources.totalResources} loaded\n\n`;

    // Measurements
    if (measurements.length > 0) {
      report += 'Measurements:\n';
      measurements.forEach(metric => {
        if (metric.duration) {
          report += `${metric.name}: ${metric.duration.toFixed(2)}ms\n`;
        }
      });
      report += '\n';
    }

    // Benchmarks
    if (benchmarks.length > 0) {
      report += 'Benchmarks:\n';
      benchmarks.forEach(benchmark => {
        report += `${benchmark.name}: avg ${benchmark.averageTime.toFixed(2)}ms (${benchmark.iterations} iterations)\n`;
      });
    }

    return report;
  }

  /**
   * Cleanup observers
   */
  cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
    this.clear();
  }
}

// Export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();

// Export types
export type { PerformanceMetric, BenchmarkResult, SystemMetrics };

// Utility functions
export const measureAsync = async <T>(
  name: string,
  fn: () => Promise<T>,
  metadata?: Record<string, any>
): Promise<T> => {
  performanceMonitor.startMeasure(name, metadata);
  try {
    const result = await fn();
    return result;
  } finally {
    performanceMonitor.endMeasure(name);
  }
};

export const measureSync = <T>(
  name: string,
  fn: () => T,
  metadata?: Record<string, any>
): T => {
  performanceMonitor.startMeasure(name, metadata);
  try {
    const result = fn();
    return result;
  } finally {
    performanceMonitor.endMeasure(name);
  }
};