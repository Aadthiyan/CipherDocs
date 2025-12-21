"""
Performance measurement utilities for benchmarking

Provides:
- Timer context managers for measuring execution time
- Memory tracking and reporting
- CPU monitoring
- Disk I/O measurement
- Performance report generation
"""

import time
import psutil
import os
import json
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import statistics


@dataclass
class TimingResult:
    """Timing measurement result"""
    name: str
    start_time: float
    end_time: float
    elapsed_seconds: float
    memory_start_mb: float
    memory_end_mb: float
    memory_delta_mb: float
    cpu_percent: float


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics"""
    operation: str
    count: int
    total_time_sec: float
    min_time_sec: float
    max_time_sec: float
    mean_time_sec: float
    median_time_sec: float
    p95_time_sec: float
    p99_time_sec: float
    throughput_per_sec: float
    total_memory_mb: float
    avg_cpu_percent: float


class PerformanceTracker:
    """Tracks performance metrics for benchmarking"""
    
    def __init__(self):
        self.measurements: List[TimingResult] = []
        self.process = psutil.Process(os.getpid())
        
    @contextmanager
    def track(self, name: str):
        """Context manager to track timing and resource usage"""
        # Get initial measurements
        start_time = time.time()
        memory_start = self.process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent_start = self.process.cpu_percent(interval=None)
        
        try:
            yield
        finally:
            # Get final measurements
            end_time = time.time()
            memory_end = self.process.memory_info().rss / 1024 / 1024  # MB
            cpu_percent = self.process.cpu_percent(interval=0.1)
            
            # Record measurement
            result = TimingResult(
                name=name,
                start_time=start_time,
                end_time=end_time,
                elapsed_seconds=end_time - start_time,
                memory_start_mb=memory_start,
                memory_end_mb=memory_end,
                memory_delta_mb=memory_end - memory_start,
                cpu_percent=cpu_percent
            )
            self.measurements.append(result)
    
    def get_metrics(self, operation: str) -> Optional[PerformanceMetrics]:
        """Get aggregated metrics for an operation"""
        matching = [m for m in self.measurements if m.name == operation]
        
        if not matching:
            return None
        
        times = [m.elapsed_seconds for m in matching]
        memories = [m.memory_delta_mb for m in matching]
        cpus = [m.cpu_percent for m in matching]
        
        # Sort times for percentile calculations
        sorted_times = sorted(times)
        
        return PerformanceMetrics(
            operation=operation,
            count=len(matching),
            total_time_sec=sum(times),
            min_time_sec=min(times),
            max_time_sec=max(times),
            mean_time_sec=statistics.mean(times),
            median_time_sec=statistics.median(times),
            p95_time_sec=sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0,
            p99_time_sec=sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0,
            throughput_per_sec=len(matching) / sum(times) if sum(times) > 0 else 0,
            total_memory_mb=sum(memories),
            avg_cpu_percent=statistics.mean(cpus) if cpus else 0
        )
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get metrics for all unique operations"""
        operations = set(m.name for m in self.measurements)
        return {op: self.get_metrics(op) for op in operations}
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a performance report"""
        metrics = self.get_all_metrics()
        
        report_lines = [
            "=" * 100,
            "PERFORMANCE BENCHMARK REPORT",
            "=" * 100,
            ""
        ]
        
        for op_name in sorted(metrics.keys()):
            m = metrics[op_name]
            report_lines.extend([
                f"Operation: {m.operation}",
                f"  Count: {m.count}",
                f"  Total Time: {m.total_time_sec:.2f}s",
                f"  Min Time: {m.min_time_sec*1000:.2f}ms",
                f"  Max Time: {m.max_time_sec*1000:.2f}ms",
                f"  Mean Time: {m.mean_time_sec*1000:.2f}ms",
                f"  Median Time: {m.median_time_sec*1000:.2f}ms",
                f"  P95 Time: {m.p95_time_sec*1000:.2f}ms",
                f"  P99 Time: {m.p99_time_sec*1000:.2f}ms",
                f"  Throughput: {m.throughput_per_sec:.2f} ops/sec",
                f"  Avg Memory Delta: {m.total_memory_mb/m.count:.2f}MB per operation",
                f"  Avg CPU: {m.avg_cpu_percent:.1f}%",
                ""
            ])
        
        report_lines.extend([
            "=" * 100,
            f"Total measurements collected: {len(self.measurements)}",
            "=" * 100,
        ])
        
        report = "\n".join(report_lines)
        
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(report)
        
        return report
    
    def export_json(self, output_file: str):
        """Export measurements as JSON"""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "measurements": [asdict(m) for m in self.measurements],
            "metrics": {op: asdict(m) for op, m in self.get_all_metrics().items()}
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)


class ResourceMonitor:
    """Monitor system resource usage"""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
        
    def get_memory_mb(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_memory_delta_mb(self) -> float:
        """Get memory delta from start in MB"""
        current = self.process.memory_info().rss
        return (current - self.start_memory) / 1024 / 1024
    
    def get_cpu_percent(self) -> float:
        """Get current CPU usage percentage"""
        return self.process.cpu_percent(interval=0.1)
    
    def get_elapsed_seconds(self) -> float:
        """Get elapsed time since start"""
        return time.time() - self.start_time
    
    def get_status(self) -> Dict[str, Any]:
        """Get current resource status"""
        return {
            "memory_mb": self.get_memory_mb(),
            "memory_delta_mb": self.get_memory_delta_mb(),
            "cpu_percent": self.get_cpu_percent(),
            "elapsed_seconds": self.get_elapsed_seconds()
        }


def measure_throughput(operation_fn, count: int, name: str) -> PerformanceMetrics:
    """
    Measure throughput of an operation
    
    Args:
        operation_fn: Function to execute repeatedly
        count: Number of times to execute
        name: Operation name for reporting
    
    Returns:
        PerformanceMetrics with throughput measurements
    """
    tracker = PerformanceTracker()
    
    for i in range(count):
        with tracker.track(name):
            operation_fn()
    
    return tracker.get_metrics(name)


def measure_latency(operation_fn, name: str) -> float:
    """
    Measure single-run latency of an operation
    
    Args:
        operation_fn: Function to execute
        name: Operation name for reporting
    
    Returns:
        Elapsed time in seconds
    """
    start = time.time()
    operation_fn()
    return time.time() - start
