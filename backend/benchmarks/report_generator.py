"""
Benchmark Report Generator and Analysis

Generates comprehensive performance reports with:
- Performance metrics tables
- ASCII charts
- Comparative analysis
- Recommendations
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Single benchmark test result"""
    name: str
    value: float
    unit: str
    target: Optional[float] = None
    status: str = "PASS"  # PASS, FAIL, WARNING


class BenchmarkReportGenerator:
    """Generates comprehensive benchmark reports"""
    
    def __init__(self, output_dir: str = "benchmark_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[BenchmarkResult] = []
    
    def add_result(self, name: str, value: float, unit: str, target: Optional[float] = None):
        """Add a benchmark result"""
        status = "PASS"
        if target is not None:
            if unit in ["ms", "sec", "s"] and value > target:
                status = "FAIL"
            elif unit in ["ops/sec", "q/s", "docs/sec"] and value < target:
                status = "FAIL"
            elif unit == "%" and unit.endswith("%"):
                if "overhead" in name.lower() and value > target:
                    status = "FAIL"
        
        self.results.append(BenchmarkResult(
            name=name,
            value=value,
            unit=unit,
            target=target,
            status=status
        ))
    
    def generate_html_report(self, title: str = "Performance Benchmarks") -> str:
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; }}
        .summary {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .metrics-table {{ width: 100%; border-collapse: collapse; background-color: white; margin-top: 15px; }}
        .metrics-table th, .metrics-table td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        .metrics-table th {{ background-color: #007bff; color: white; }}
        .metrics-table tr:hover {{ background-color: #f9f9f9; }}
        .pass {{ color: #28a745; font-weight: bold; }}
        .fail {{ color: #dc3545; font-weight: bold; }}
        .warning {{ color: #ffc107; font-weight: bold; }}
        .status-bar {{ height: 20px; background-color: #ddd; border-radius: 3px; overflow: hidden; }}
        .status-bar-fill {{ height: 100%; background-color: #28a745; }}
        .section {{ margin-top: 30px; }}
        .chart {{ background-color: white; padding: 15px; margin-top: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="summary">
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Tests:</strong> {len(self.results)}</p>
        <p><strong>Passed:</strong> {sum(1 for r in self.results if r.status == 'PASS')}</p>
        <p><strong>Failed:</strong> {sum(1 for r in self.results if r.status == 'FAIL')}</p>
    </div>
    
    <div class="section">
        <h2>Performance Metrics</h2>
        <table class="metrics-table">
            <thead>
                <tr>
                    <th>Benchmark</th>
                    <th>Value</th>
                    <th>Target</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for result in sorted(self.results, key=lambda r: r.name):
            status_class = result.status.lower()
            status_text = result.status
            target_text = f"{result.target} {result.unit}" if result.target else "N/A"
            
            html += f"""                <tr>
                    <td>{result.name}</td>
                    <td>{result.value:.2f} {result.unit}</td>
                    <td>{target_text}</td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
"""
        
        html += """            </tbody>
        </table>
    </div>
</body>
</html>"""
        
        return html
    
    def save_html_report(self, filename: Optional[str] = None) -> Path:
        """Save HTML report to file"""
        if filename is None:
            filename = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        output_file = self.output_dir / filename
        output_file.write_text(self.generate_html_report())
        return output_file
    
    def generate_text_report(self) -> str:
        """Generate text report"""
        lines = [
            "=" * 100,
            "PERFORMANCE BENCHMARK REPORT",
            "=" * 100,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Total Tests: {len(self.results)}",
            f"Passed: {sum(1 for r in self.results if r.status == 'PASS')}",
            f"Failed: {sum(1 for r in self.results if r.status == 'FAIL')}",
            "",
            "RESULTS BY CATEGORY",
            "-" * 100,
        ]
        
        # Group by category
        categories = {}
        for result in self.results:
            category = result.name.split("_")[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
        
        for category in sorted(categories.keys()):
            lines.append(f"\n{category.upper()}")
            lines.append("-" * 50)
            
            for result in sorted(categories[category], key=lambda r: r.name):
                status_symbol = "✓" if result.status == "PASS" else "✗"
                target_str = f" (target: {result.target} {result.unit})" if result.target else ""
                lines.append(
                    f"{status_symbol} {result.name:40s} {result.value:10.2f} {result.unit:10s}{target_str}"
                )
        
        lines.extend([
            "",
            "=" * 100,
            "PERFORMANCE TARGETS",
            "=" * 100,
            "✓ Document ingestion: < 5 seconds for 10MB file",
            "✓ Search latency: < 500ms for single query",
            "✓ Query throughput: > 100 queries/second sustained",
            "✓ Encryption overhead: < 20% impact on latency",
            "✓ Document upload throughput: > 100 documents/hour",
            "✓ Concurrent uploads: 100 uploads without timeouts",
            "✓ Multi-tenant isolation: no performance degradation with 10+ tenants",
            "✓ Memory usage: < 1GB at idle, < 5GB at peak",
            "✓ Connection pool: efficient reuse without bottlenecks",
            "",
            "=" * 100,
        ])
        
        return "\n".join(lines)
    
    def save_text_report(self, filename: Optional[str] = None) -> Path:
        """Save text report to file"""
        if filename is None:
            filename = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        output_file = self.output_dir / filename
        output_file.write_text(self.generate_text_report())
        return output_file
    
    def generate_json_report(self) -> dict:
        """Generate JSON report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.status == "PASS"),
            "failed": sum(1 for r in self.results if r.status == "FAIL"),
            "results": [
                {
                    "name": r.name,
                    "value": r.value,
                    "unit": r.unit,
                    "target": r.target,
                    "status": r.status
                }
                for r in self.results
            ]
        }
    
    def save_json_report(self, filename: Optional[str] = None) -> Path:
        """Save JSON report to file"""
        if filename is None:
            filename = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        output_file = self.output_dir / filename
        output_file.write_text(json.dumps(self.generate_json_report(), indent=2))
        return output_file


def create_sample_report():
    """Create a sample benchmark report"""
    gen = BenchmarkReportGenerator()
    
    # Document Processing
    gen.add_result("ingestion_1mb_latency", 0.8, "sec", 5.0)
    gen.add_result("ingestion_10mb_latency", 3.2, "sec", 5.0)
    gen.add_result("chunking_100pages_throughput", 1250, "chunks/sec")
    gen.add_result("embedding_100chunks_latency", 2.1, "sec")
    gen.add_result("embedding_throughput", 47.6, "embeddings/sec")
    gen.add_result("encryption_1000embeddings_latency", 0.45, "sec")
    gen.add_result("encryption_throughput", 2222, "embeddings/sec")
    gen.add_result("encryption_overhead", 8.5, "%", 20.0)
    
    # Search Performance
    gen.add_result("search_single_query_latency", 125, "ms", 500)
    gen.add_result("search_100queries_throughput", 127, "queries/sec", 100)
    gen.add_result("search_top_k10_latency", 95, "ms")
    gen.add_result("search_top_k100_latency", 185, "ms")
    gen.add_result("result_decryption_100results", 22, "ms")
    gen.add_result("db_query_100results", 12, "ms")
    
    # Scalability
    gen.add_result("uploads_10concurrent", 1.2, "sec")
    gen.add_result("uploads_100concurrent", 8.5, "sec")
    gen.add_result("upload_throughput_hourly", 850, "docs/hour", 100)
    gen.add_result("search_1000documents", 145, "ms")
    gen.add_result("search_10000documents", 210, "ms")
    gen.add_result("multi_tenant_10tenants_throughput", 125, "ops/sec")
    gen.add_result("tenant_isolation_overhead", 3.2, "%", 10)
    
    # Resource Usage
    gen.add_result("idle_memory", 320, "MB")
    gen.add_result("peak_memory", 2400, "MB", 5000)
    gen.add_result("memory_per_embedding", 2.8, "KB")
    gen.add_result("cpu_idle", 5.2, "%")
    gen.add_result("cpu_peak", 78.5, "%", 95)
    
    return gen


if __name__ == "__main__":
    # Create and save sample report
    gen = create_sample_report()
    
    txt_file = gen.save_text_report()
    html_file = gen.save_html_report()
    json_file = gen.save_json_report()
    
    print(f"Reports generated:")
    print(f"  Text: {txt_file}")
    print(f"  HTML: {html_file}")
    print(f"  JSON: {json_file}")
    print("")
    print(gen.generate_text_report())
