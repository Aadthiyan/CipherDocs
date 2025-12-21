"""
Benchmark CLI - Easy execution of performance benchmarks

Usage:
  python benchmarks/run_benchmarks.py [--type=all|document|search|scalability] [--quick]
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from benchmarks.report_generator import BenchmarkReportGenerator, create_sample_report


def run_pytest_benchmarks(test_file=None, quick=False):
    """Run pytest benchmarks"""
    print("\n" + "=" * 70)
    print("RUNNING PERFORMANCE BENCHMARKS")
    print("=" * 70 + "\n")
    
    args = [
        "python", "-m", "pytest",
        test_file or "benchmarks/",
        "--ignore=benchmarks/load_testing.py",
        "-v", "-s",
        "--tb=short",
    ]
    
    if quick:
        args.extend(["--timeout=60"])
        print("Running in QUICK mode (60s timeout per test)\n")
    else:
        args.extend(["--timeout=600"])
        print("Running FULL benchmark suite (600s timeout per test)\n")
    
    result = subprocess.run(args, cwd="backend")
    return result.returncode


def run_document_benchmarks(quick=False):
    """Run document processing benchmarks"""
    print("\n📄 DOCUMENT PROCESSING BENCHMARKS")
    return run_pytest_benchmarks("benchmarks/test_document_processing.py", quick)


def run_search_benchmarks(quick=False):
    """Run search performance benchmarks"""
    print("\n🔍 SEARCH PERFORMANCE BENCHMARKS")
    return run_pytest_benchmarks("benchmarks/test_search_performance.py", quick)


def run_scalability_benchmarks(quick=False):
    """Run scalability benchmarks"""
    print("\n📈 SCALABILITY BENCHMARKS")
    return run_pytest_benchmarks("benchmarks/test_scalability.py", quick)


def run_all_benchmarks(quick=False):
    """Run all benchmarks"""
    results = {}
    
    # Document processing
    print("\n[1/3] Running document processing benchmarks...")
    results['document'] = run_document_benchmarks(quick)
    
    # Search performance
    print("\n[2/3] Running search performance benchmarks...")
    results['search'] = run_search_benchmarks(quick)
    
    # Scalability
    print("\n[3/3] Running scalability benchmarks...")
    results['scalability'] = run_scalability_benchmarks(quick)
    
    return results


def generate_sample_report():
    """Generate a sample benchmark report"""
    print("\n" + "=" * 70)
    print("GENERATING SAMPLE BENCHMARK REPORT")
    print("=" * 70 + "\n")
    
    gen = create_sample_report()
    
    txt_file = gen.save_text_report()
    html_file = gen.save_html_report()
    json_file = gen.save_json_report()
    
    print(f"\n✅ Reports generated:")
    print(f"  Text report:  {txt_file}")
    print(f"  HTML report:  {html_file}")
    print(f"  JSON report:  {json_file}")
    
    print(f"\n" + gen.generate_text_report())
    
    return [txt_file, html_file, json_file]


def print_usage():
    """Print usage information"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║           CIPHERDOCS PERFORMANCE BENCHMARKING SUITE                ║
╚════════════════════════════════════════════════════════════════════╝

USAGE:
  python benchmarks/run_benchmarks.py [OPTIONS]

OPTIONS:
  --type TYPE          Type of benchmarks to run:
                       - all:         All benchmarks (default)
                       - document:    Document processing benchmarks
                       - search:      Search performance benchmarks
                       - scalability: Scalability benchmarks
                       - report:      Generate sample report
  
  --quick              Quick mode (60s timeout per test)
  
  --help               Show this help message

EXAMPLES:
  # Run all benchmarks
  python benchmarks/run_benchmarks.py
  
  # Run quick benchmark suite
  python benchmarks/run_benchmarks.py --quick
  
  # Run only search benchmarks
  python benchmarks/run_benchmarks.py --type=search
  
  # Generate sample report
  python benchmarks/run_benchmarks.py --type=report

LOAD TESTING (requires separate terminal):
  1. Start application: python main.py (in backend/)
  2. Run load tests:
     locust -f benchmarks/load_testing.py --host=http://localhost:8000 \\
       -u 100 -r 10 -t 5m --headless

PERFORMANCE TARGETS:
  ✓ Document ingestion:    < 5 seconds for 10MB file
  ✓ Search latency:        < 500ms for single query
  ✓ Query throughput:      > 100 queries/second
  ✓ Upload throughput:     > 100 documents/hour
  ✓ Memory usage:          < 5GB at peak
  ✓ CPU usage:             < 95% at peak
  ✓ Encryption overhead:   < 20%
  ✓ Tenant isolation:      < 10% overhead with 10+ tenants

REPORT LOCATIONS:
  Text:  benchmark_reports/benchmark_report_*.txt
  HTML:  benchmark_reports/benchmark_report_*.html
  JSON:  benchmark_reports/benchmark_report_*.json

TROUBLESHOOTING:
  - Ensure pytest installed: pip install pytest
  - Ensure psutil installed: pip install psutil
  - Add backend to path: export PYTHONPATH=backend:$PYTHONPATH
  - Check database is running for integration tests
""")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="CipherDocs Performance Benchmarking Suite",
        add_help=False
    )
    
    parser.add_argument(
        "--type",
        choices=["all", "document", "search", "scalability", "report"],
        default="all",
        help="Type of benchmarks to run"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (60s timeout)"
    )
    
    parser.add_argument(
        "--help",
        action="store_true",
        help="Show help message"
    )
    
    args = parser.parse_args()
    
    if args.help:
        print_usage()
        return 0
    
    start_time = time.time()
    
    try:
        if args.type == "document":
            result = run_document_benchmarks(args.quick)
        elif args.type == "search":
            result = run_search_benchmarks(args.quick)
        elif args.type == "scalability":
            result = run_scalability_benchmarks(args.quick)
        elif args.type == "report":
            result = 0 if generate_sample_report() else 1
        else:  # all
            results = run_all_benchmarks(args.quick)
            result = 0 if all(r == 0 for r in results.values()) else 1
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        print(f"Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"Status: {'✅ PASSED' if result == 0 else '❌ FAILED'}")
        print("=" * 70 + "\n")
        
        return result
    
    except Exception as e:
        print(f"\n❌ Error running benchmarks: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
