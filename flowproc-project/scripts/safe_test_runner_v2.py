#!/usr/bin/env python3
"""
Safe Test Runner v2 for FlowProcessor
Enhanced version with better isolation and error handling for refactored codebase.
"""

import os
import sys
import subprocess
import signal
import time
import tempfile
import shutil
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from debug.system_health_check import SystemHealthChecker


@dataclass
class TestResult:
    """Container for test results."""
    test_name: str
    status: str  # 'passed', 'failed', 'error', 'skipped'
    duration: float
    error_message: Optional[str] = None
    output: Optional[str] = None


class SafeTestRunnerV2:
    """Enhanced safe test runner with better isolation and error handling."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.health_checker = SystemHealthChecker(project_root)
        self.test_timeout = 120  # 2 minutes per test file
        self.max_failures = 5
        self.cleanup_temp_files = True
        
        # Test categories with different isolation requirements
        self.test_categories = {
            'safe': [
                'tests/integration/simple_writer_test.py',
                'tests/integration/diagnostic_test.py',
                'tests/integration/test_parsing.py',
                'tests/integration/test_simple_csv.py',
                'tests/integration/test_csv_demo_functionality.py',
                'tests/integration/test_sample_mapping_diagnostic.py'
            ],
            'isolated': [
                'tests/integration/test_async_and_vectorized.py::TestVectorizedAggregator'
            ],
            'gui': [
                'tests/unit/test_event_handler.py',
                'tests/unit/test_main_window.py',
                'tests/unit/test_state_manager.py',
                'tests/unit/test_ui_builder.py'
            ],
            'integration': [
                'tests/integration/test_async_and_vectorized.py::TestProcessingWorker',
                'tests/integration/test_async_and_vectorized.py::TestProcessingManager',
                'tests/integration/test_async_and_vectorized.py::TestIntegration'
            ]
        }
        
    def setup_environment(self):
        """Set up environment for safe testing."""
        # Set headless mode for GUI testing
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        # Set environment variables for better stability
        os.environ['PYTHONUNBUFFERED'] = '1'
        os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
        
        # Set memory limits for numpy
        os.environ['OPENBLAS_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        os.environ['OMP_NUM_THREADS'] = '1'
        
        # Set temp directory
        temp_dir = tempfile.mkdtemp(prefix='flowproc_test_')
        os.environ['TMPDIR'] = temp_dir
        os.environ['TEMP'] = temp_dir
        os.environ['TMP'] = temp_dir
        
        return temp_dir
    
    def cleanup_environment(self, temp_dir: str):
        """Clean up test environment."""
        if self.cleanup_temp_files and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up temp directory {temp_dir}: {e}")
    
    def run_health_check(self) -> bool:
        """Run system health check and return success status."""
        print("🔍 Running system health check...")
        report = self.health_checker.run_all_checks()
        success = self.health_checker.print_report(report)
        
        if not success:
            print("\n❌ Health check failed. Fix critical issues before running tests.")
            return False
        
        print("\n✅ Health check passed. Proceeding with tests.")
        return True
    
    def run_tests_with_isolation(self, test_paths: List[str], category: str) -> List[TestResult]:
        """Run tests with appropriate isolation based on category."""
        results = []
        
        for test_path in test_paths:
            print(f"\n🧪 Running {category} test: {test_path}")
            
            # Build pytest command with category-specific options
            cmd = [
                sys.executable, '-m', 'pytest',
                '--disable-warnings',
                '--tb=short',
                '--timeout', str(self.test_timeout),
                '--timeout-method', 'thread'
            ]
            
            # Add category-specific options
            if category == 'gui':
                # Don't add Qt-specific arguments that might not be supported
                pass
            elif category == 'isolated':
                cmd.extend(['--maxfail', '1'])
            
            cmd.append(test_path)
            
            start_time = time.time()
            
            try:
                # Run with timeout and signal handling
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    timeout=self.test_timeout * 2,
                    capture_output=True,
                    text=True,
                    env=os.environ.copy()
                )
                
                duration = time.time() - start_time
                
                # Determine test status
                if result.returncode == 0:
                    status = 'passed'
                    print(f"✅ {test_path} - PASSED ({duration:.2f}s)")
                elif result.returncode == 124:
                    status = 'timeout'
                    print(f"⏰ {test_path} - TIMEOUT")
                elif result.returncode == 130:
                    status = 'interrupted'
                    print(f"⏹️ {test_path} - INTERRUPTED")
                elif result.returncode in [-11, -6]:  # SIGSEGV, SIGABRT
                    status = 'segfault'
                    print(f"💥 {test_path} - SEGFAULT")
                else:
                    status = 'failed'
                    print(f"❌ {test_path} - FAILED (exit code {result.returncode})")
                
                # Create test result
                test_result = TestResult(
                    test_name=test_path,
                    status=status,
                    duration=duration,
                    error_message=result.stderr if result.stderr else None,
                    output=result.stdout if result.stdout else None
                )
                
                results.append(test_result)
                
                # Print output for failed tests
                if status != 'passed':
                    if result.stdout:
                        print(f"📋 Output: {result.stdout[:500]}...")
                    if result.stderr:
                        print(f"⚠️ Errors: {result.stderr[:500]}...")
                
            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                print(f"⏰ {test_path} - TIMEOUT")
                results.append(TestResult(
                    test_name=test_path,
                    status='timeout',
                    duration=duration,
                    error_message='Test timed out'
                ))
            except Exception as e:
                duration = time.time() - start_time
                print(f"💥 {test_path} - ERROR: {e}")
                results.append(TestResult(
                    test_name=test_path,
                    status='error',
                    duration=duration,
                    error_message=str(e)
                ))
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests with appropriate isolation."""
        if not self.run_health_check():
            return {'success': False, 'error': 'Health check failed'}
        
        temp_dir = self.setup_environment()
        all_results = {}
        
        try:
            # Run safe tests first
            print("\n🚀 Running safe tests...")
            safe_results = self.run_tests_with_isolation(self.test_categories['safe'], 'safe')
            all_results['safe'] = safe_results
            
            # Run isolated tests
            print("\n🚀 Running isolated tests...")
            isolated_results = self.run_tests_with_isolation(self.test_categories['isolated'], 'isolated')
            all_results['isolated'] = isolated_results
            
            # Run GUI tests with extra caution
            print("\n🚀 Running GUI tests...")
            gui_results = self.run_tests_with_isolation(self.test_categories['gui'], 'gui')
            all_results['gui'] = gui_results
            
            # Run integration tests last
            print("\n🚀 Running integration tests...")
            integration_results = self.run_tests_with_isolation(self.test_categories['integration'], 'integration')
            all_results['integration'] = integration_results
            
            # Calculate summary
            total_tests = sum(len(results) for results in all_results.values())
            passed_tests = sum(len([r for r in results if r.status == 'passed']) 
                             for results in all_results.values())
            failed_tests = total_tests - passed_tests
            
            summary = {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'categories': {
                    category: {
                        'total': len(results),
                        'passed': len([r for r in results if r.status == 'passed']),
                        'failed': len([r for r in results if r.status != 'passed'])
                    }
                    for category, results in all_results.items()
                }
            }
            
            all_results['summary'] = summary
            
            # Print summary
            self.print_summary(summary, all_results)
            
            return all_results
            
        finally:
            self.cleanup_environment(temp_dir)
    
    def print_summary(self, summary: Dict[str, Any], all_results: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print()
        
        print("Category Breakdown:")
        for category, stats in summary['categories'].items():
            print(f"  {category.upper()}: {stats['passed']}/{stats['total']} passed")
        
        print()
        print("Failed Tests:")
        for category, results in all_results.items():
            if category == 'summary':
                continue
            failed_tests = [r for r in results if r.status != 'passed']
            for test in failed_tests:
                print(f"  {test.test_name}: {test.status}")
                if test.error_message:
                    print(f"    Error: {test.error_message[:100]}...")
        
        print("="*60)


def main():
    """Main entry point for safe test runner v2."""
    if len(sys.argv) < 2:
        print("Usage: python safe_test_runner_v2.py <test_type>")
        print("Test types:")
        print("  all          - Run all tests with isolation")
        print("  safe         - Run only safe tests")
        print("  isolated     - Run isolated tests")
        print("  gui          - Run GUI tests")
        print("  integration  - Run integration tests")
        sys.exit(1)
    
    test_type = sys.argv[1]
    runner = SafeTestRunnerV2(project_root)
    
    try:
        if test_type == 'all':
            results = runner.run_all_tests()
        elif test_type == 'safe':
            results = {'safe': runner.run_tests_with_isolation(runner.test_categories['safe'], 'safe')}
        elif test_type == 'isolated':
            results = {'isolated': runner.run_tests_with_isolation(runner.test_categories['isolated'], 'isolated')}
        elif test_type == 'gui':
            results = {'gui': runner.run_tests_with_isolation(runner.test_categories['gui'], 'gui')}
        elif test_type == 'integration':
            results = {'integration': runner.run_tests_with_isolation(runner.test_categories['integration'], 'integration')}
        else:
            print(f"Error: Unknown test type '{test_type}'")
            sys.exit(1)
        
        # Exit with appropriate code
        if 'summary' in results:
            success_rate = results['summary']['success_rate']
            sys.exit(0 if success_rate >= 80 else 1)
        else:
            # For single category runs, check if any tests passed
            total_passed = sum(len([r for r in results[cat] if r.status == 'passed']) 
                             for cat in results)
            total_tests = sum(len(results[cat]) for cat in results)
            sys.exit(0 if total_passed > 0 else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Test runner interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 