#!/usr/bin/env python3
"""
Safe Test Runner for FlowProcessor
Runs system health checks and implements segfault prevention measures.
"""

import os
import sys
import subprocess
import signal
import time
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from flowproc.infrastructure.monitoring.health import HealthChecker


class SafeTestRunner:
    """Safe test runner with segfault prevention."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.health_checker = HealthChecker()
        self.test_timeout = 300  # 5 minutes per test file
        self.max_failures = 3
        self.cleanup_temp_files = True
        
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
        report = self.health_checker.check_system_health()
        success = self._print_health_report(report)
        
        if not success:
            print("\n❌ Health check failed. Fix critical issues before running tests.")
            return False
        
        print("\n✅ Health check passed. Proceeding with tests.")
        return True

    def _print_health_report(self, report: dict) -> bool:
        """Print a compact health report summary; return True unless critical."""
        try:
            status = report.get('status', 'unknown')
            print(f"Status: {status}")
            for check in report.get('checks', []):
                print(f"- {check.get('name')}: {check.get('status')} - {check.get('message')}")
            return status != 'critical'
        except Exception:
            return True
    
    def run_tests_with_timeout(self, test_args: List[str]) -> subprocess.CompletedProcess:
        """Run tests with timeout and segfault protection."""
        # Build pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            '--maxfail', str(self.max_failures),
            '--disable-warnings',
            '--tb=short',
            '--timeout', str(self.test_timeout),
            '--timeout-method', 'thread'
        ] + test_args
        
        print(f"🧪 Running tests: {' '.join(cmd)}")
        
        # Run with timeout and signal handling
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                timeout=self.test_timeout * 2,  # Double timeout for safety
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"⏰ Tests timed out after {self.test_timeout * 2} seconds")
            return subprocess.CompletedProcess(
                cmd, 124, stdout="", stderr="Tests timed out"
            )
        except KeyboardInterrupt:
            print("\n⏹️  Tests interrupted by user")
            return subprocess.CompletedProcess(
                cmd, 130, stdout="", stderr="Tests interrupted"
            )
    
    def run_specific_tests(self, test_paths: List[str]) -> bool:
        """Run specific test files with safety measures."""
        if not self.run_health_check():
            return False
        
        temp_dir = self.setup_environment()
        
        try:
            # Run tests
            result = self.run_tests_with_timeout(test_paths)
            
            # Print results
            if result.stdout:
                print("\n📋 Test Output:")
                print(result.stdout)
            
            if result.stderr:
                print("\n⚠️  Test Errors/Warnings:")
                print(result.stderr)
            
            # Check exit code
            if result.returncode == 0:
                print(f"\n✅ Tests completed successfully")
                return True
            elif result.returncode == 124:
                print(f"\n⏰ Tests timed out")
                return False
            elif result.returncode == 130:
                print(f"\n⏹️  Tests interrupted")
                return False
            else:
                print(f"\n❌ Tests failed with exit code {result.returncode}")
                return False
                
        finally:
            self.cleanup_environment(temp_dir)
    
    def run_all_tests(self) -> bool:
        """Run all tests with safety measures."""
        return self.run_specific_tests(['tests/'])
    
    def run_integration_tests(self) -> bool:
        """Run integration tests with safety measures."""
        return self.run_specific_tests(['tests/integration/'])
    
    def run_unit_tests(self) -> bool:
        """Run unit tests with safety measures."""
        return self.run_specific_tests(['tests/unit/'])


def main():
    """Main entry point for safe test runner."""
    if len(sys.argv) < 2:
        print("Usage: python safe_test_runner.py <test_type> [test_paths...]")
        print("Test types:")
        print("  all          - Run all tests")
        print("  integration  - Run integration tests only")
        print("  unit         - Run unit tests only")
        print("  specific     - Run specific test files")
        print("\nExamples:")
        print("  python safe_test_runner.py all")
        print("  python safe_test_runner.py integration")
        print("  python safe_test_runner.py specific tests/integration/test_flowproc.py")
        sys.exit(1)
    
    test_type = sys.argv[1]
    test_paths = sys.argv[2:] if len(sys.argv) > 2 else []
    
    runner = SafeTestRunner(project_root)
    
    try:
        if test_type == 'all':
            success = runner.run_all_tests()
        elif test_type == 'integration':
            success = runner.run_integration_tests()
        elif test_type == 'unit':
            success = runner.run_unit_tests()
        elif test_type == 'specific':
            if not test_paths:
                print("Error: No test paths specified for 'specific' mode")
                sys.exit(1)
            success = runner.run_specific_tests(test_paths)
        else:
            print(f"Error: Unknown test type '{test_type}'")
            sys.exit(1)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test runner interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 