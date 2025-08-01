#!/usr/bin/env python3
"""
System Health Check Script for FlowProcessor
Industry-standard diagnostics for segfault prevention and system health.
"""

import os
import sys
import platform
import subprocess
import psutil
import gc
import tempfile
import shutil
import threading
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

class SystemHealthChecker:
    """Comprehensive system health checker for segfault prevention."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {}
        self.critical_issues = []
        self.warnings = []
        self.recommendations = []
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def run_all_checks(self) -> Dict:
        """Run all health checks and return comprehensive report."""
        self.logger.info("Starting comprehensive system health check...")
        
        checks = [
            self.check_system_resources,
            self.check_python_environment,
            self.check_dependencies,
            self.check_file_system,
            self.check_memory_management,
            self.check_temp_file_handling,
            self.check_concurrency_safety,
            self.check_gui_environment,
            self.check_library_compatibility,
            self.check_test_environment
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.critical_issues.append(f"Check {check.__name__} failed: {e}")
        
        return self._generate_report()
    
    def check_system_resources(self):
        """Check system resource availability and limits."""
        self.logger.info("Checking system resources...")
        
        # Memory check
        memory = psutil.virtual_memory()
        if memory.available < 1_000_000_000:  # 1GB
            self.critical_issues.append(
                f"Low memory available: {memory.available / 1_000_000_000:.1f}GB"
            )
        
        # File descriptor limits
        try:
            import resource
            soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            if soft < 1024:
                self.warnings.append(
                    f"Low file descriptor limit: {soft} (recommend >1024)"
                )
        except ImportError:
            pass  # Windows doesn't have resource module
        
        # Disk space
        disk = psutil.disk_usage(self.project_root)
        if disk.free < 1_000_000_000:  # 1GB
            self.warnings.append(
                f"Low disk space: {disk.free / 1_000_000_000:.1f}GB free"
            )
    
    def check_python_environment(self):
        """Check Python environment and version compatibility."""
        self.logger.info("Checking Python environment...")
        
        # Python version
        version = sys.version_info
        if version < (3, 8):
            self.critical_issues.append(
                f"Python version {version.major}.{version.minor} is too old. "
                "Require Python 3.8+"
            )
        
        # Virtual environment
        if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.warnings.append("Not running in a virtual environment")
        
        # Python executable path
        self.results['python_path'] = sys.executable
        self.results['python_version'] = f"{version.major}.{version.minor}.{version.micro}"
    
    def check_dependencies(self):
        """Check critical dependencies for compatibility issues."""
        self.logger.info("Checking dependencies...")
        
        critical_packages = [
            'numpy', 'pandas', 'plotly', 'openpyxl', 'PySide6', 'scipy'
        ]
        
        for package in critical_packages:
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                self.results[f'{package}_version'] = version
                
                # Check for known problematic versions
                if package == 'numpy' and version.startswith('1.19'):
                    self.warnings.append(
                        f"NumPy {version} may have compatibility issues with some C extensions"
                    )
                elif package == 'openpyxl' and version < '3.0':
                    self.warnings.append(
                        f"OpenPyXL {version} is older version, may have memory issues"
                    )
                    
            except ImportError:
                self.critical_issues.append(f"Critical package {package} not found")
    
    def check_file_system(self):
        """Check file system permissions and temp directory access."""
        self.logger.info("Checking file system...")
        
        # Temp directory access
        try:
            with tempfile.NamedTemporaryFile(delete=True) as f:
                f.write(b'test')
                f.flush()
        except Exception as e:
            self.critical_issues.append(f"Cannot write to temp directory: {e}")
        
        # Project directory permissions
        if not os.access(self.project_root, os.W_OK):
            self.critical_issues.append("Cannot write to project directory")
        
        # Check for large files that might cause memory issues
        large_files = []
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                file_path = Path(root) / file
                try:
                    if file_path.stat().st_size > 100_000_000:  # 100MB
                        large_files.append(str(file_path))
                except OSError:
                    pass
        
        if large_files:
            self.warnings.append(f"Large files detected: {len(large_files)} files >100MB")
    
    def check_memory_management(self):
        """Check memory management and garbage collection."""
        self.logger.info("Checking memory management...")
        
        # Force garbage collection
        collected = gc.collect()
        if collected > 1000:
            self.warnings.append(f"Large number of objects collected: {collected}")
        
        # Check for memory leaks in test environment
        initial_memory = psutil.Process().memory_info().rss
        for _ in range(10):
            # Simulate some operations
            temp_data = [i for i in range(1000)]
            del temp_data
            gc.collect()
        
        final_memory = psutil.Process().memory_info().rss
        memory_diff = final_memory - initial_memory
        
        if memory_diff > 10_000_000:  # 10MB
            self.warnings.append(
                f"Potential memory leak detected: {memory_diff / 1_000_000:.1f}MB increase"
            )
    
    def check_temp_file_handling(self):
        """Check temporary file handling and cleanup."""
        self.logger.info("Checking temp file handling...")
        
        temp_files = []
        for _ in range(5):
            try:
                with tempfile.NamedTemporaryFile(delete=False) as f:
                    temp_files.append(f.name)
                    f.write(b'test data' * 1000)
            except Exception as e:
                self.warnings.append(f"Temp file creation failed: {e}")
                continue
            
            # Clean up
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
        
        # Check if temp files were properly cleaned up
        remaining_files = [f for f in temp_files if os.path.exists(f)]
        if remaining_files:
            self.warnings.append(f"Temp files not cleaned up: {len(remaining_files)}")
    
    def check_concurrency_safety(self):
        """Check for potential concurrency issues."""
        self.logger.info("Checking concurrency safety...")
        
        # Test basic threading
        try:
            result = []
            def worker():
                result.append(threading.current_thread().name)
            
            threads = [threading.Thread(target=worker) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            
            if len(result) != 3:
                self.warnings.append("Threading test failed")
                
        except Exception as e:
            self.warnings.append(f"Threading test error: {e}")
    
    def check_gui_environment(self):
        """Check GUI environment and display settings."""
        self.logger.info("Checking GUI environment...")
        
        # Check for display
        if platform.system() == 'Darwin':  # macOS
            if 'DISPLAY' not in os.environ and 'QT_QPA_PLATFORM' not in os.environ:
                # This is normal for macOS, but we should set headless mode
                self.recommendations.append(
                    "Set QT_QPA_PLATFORM=offscreen for headless testing"
                )
        elif platform.system() == 'Linux':
            if 'DISPLAY' not in os.environ:
                self.warnings.append("No DISPLAY environment variable set")
    
    def check_library_compatibility(self):
        """Check for library compatibility issues."""
        self.logger.info("Checking library compatibility...")
        
        # Check numpy and scipy compatibility
        try:
            import numpy as np
            import scipy
            test_array = np.random.random((1000, 1000))
            # Test basic operations
            result = np.linalg.svd(test_array)
            del test_array, result
            gc.collect()
        except Exception as e:
            self.critical_issues.append(f"NumPy/SciPy compatibility issue: {e}")
        
        # Check openpyxl memory usage
        try:
            import openpyxl
            from openpyxl import Workbook
            
            wb = Workbook()
            ws = wb.active
            
            # Test writing some data
            for i in range(100):
                for j in range(10):
                    ws.cell(row=i+1, column=j+1, value=f"test_{i}_{j}")
            
            # Test saving to temp file
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=True) as f:
                wb.save(f.name)
            
            wb.close()
            del wb, ws
            gc.collect()
            
        except Exception as e:
            self.critical_issues.append(f"OpenPyXL compatibility issue: {e}")
    
    def check_test_environment(self):
        """Check test environment configuration."""
        self.logger.info("Checking test environment...")
        
        # Check pytest configuration
        pytest_ini = self.project_root / 'pytest.ini'
        if pytest_ini.exists():
            try:
                import configparser
                config = configparser.ConfigParser()
                config.read(pytest_ini)
                
                # Check for timeout settings
                if 'pytest' in config:
                    timeout = config['pytest'].get('timeout', '')
                    if not timeout:
                        self.recommendations.append(
                            "Add timeout settings to pytest.ini to prevent hanging tests"
                        )
            except Exception:
                pass
        
        # Check for test isolation
        self.recommendations.append(
            "Use pytest-xdist with --maxfail=1 for better test isolation"
        )
    
    def _generate_report(self) -> Dict:
        """Generate comprehensive health report."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': {
                'platform': platform.platform(),
                'python_version': self.results.get('python_version', 'unknown'),
                'python_path': self.results.get('python_path', 'unknown'),
            },
            'package_versions': {
                k: v for k, v in self.results.items() 
                if k.endswith('_version')
            },
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'summary': {
                'total_checks': len(self.results),
                'critical_issues': len(self.critical_issues),
                'warnings': len(self.warnings),
                'recommendations': len(self.recommendations),
                'status': 'FAIL' if self.critical_issues else 'PASS'
            }
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted health report."""
        print("\n" + "="*60)
        print("FLOWPROCESSOR SYSTEM HEALTH CHECK REPORT")
        print("="*60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Platform: {report['system_info']['platform']}")
        print(f"Python: {report['system_info']['python_version']}")
        
        if report['package_versions']:
            print("\nPackage Versions:")
            for package, version in report['package_versions'].items():
                print(f"  {package.replace('_version', '')}: {version}")
        
        if report['critical_issues']:
            print(f"\n❌ CRITICAL ISSUES ({len(report['critical_issues'])}):")
            for issue in report['critical_issues']:
                print(f"  • {issue}")
        
        if report['warnings']:
            print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
            for warning in report['warnings']:
                print(f"  • {warning}")
        
        if report['recommendations']:
            print(f"\n💡 RECOMMENDATIONS ({len(report['recommendations'])}):")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        print(f"\n📊 SUMMARY:")
        print(f"  Status: {report['summary']['status']}")
        print(f"  Critical Issues: {report['summary']['critical_issues']}")
        print(f"  Warnings: {report['summary']['warnings']}")
        print(f"  Recommendations: {report['summary']['recommendations']}")
        
        if report['summary']['status'] == 'FAIL':
            print("\n🚨 SYSTEM HEALTH CHECK FAILED - Address critical issues before running tests")
            return False
        else:
            print("\n✅ SYSTEM HEALTH CHECK PASSED - Environment appears stable")
            return True


def main():
    """Main entry point for system health check."""
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    checker = SystemHealthChecker(project_root)
    report = checker.run_all_checks()
    
    success = checker.print_report(report)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 