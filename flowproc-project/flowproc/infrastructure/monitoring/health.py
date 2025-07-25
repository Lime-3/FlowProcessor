"""
Health checks for flow cytometry processing system.
"""

import os
import psutil
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import threading
import time

logger = logging.getLogger(__name__)


@dataclass
class HealthCheck:
    """Health check result."""
    name: str
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    timestamp: datetime
    details: Dict[str, Any]


class HealthChecker:
    """Performs health checks on the system."""
    
    def __init__(self):
        """Initialize the health checker."""
        self.checks: List[HealthCheck] = []
        self._lock = threading.Lock()
        
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check."""
        checks = []
        
        # Check CPU usage
        checks.append(self._check_cpu_usage())
        
        # Check memory usage
        checks.append(self._check_memory_usage())
        
        # Check disk usage
        checks.append(self._check_disk_usage())
        
        # Check disk space
        checks.append(self._check_disk_space())
        
        # Check Python environment
        checks.append(self._check_python_environment())
        
        # Check required packages
        checks.append(self._check_required_packages())
        
        # Store checks
        with self._lock:
            self.checks.extend(checks)
            # Keep only last 100 checks
            if len(self.checks) > 100:
                self.checks = self.checks[-100:]
        
        # Determine overall status
        overall_status = self._determine_overall_status(checks)
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': [self._check_to_dict(check) for check in checks],
            'summary': self._create_summary(checks)
        }
    
    def _check_cpu_usage(self) -> HealthCheck:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent < 80:
                status = 'healthy'
                message = f"CPU usage is normal: {cpu_percent:.1f}%"
            elif cpu_percent < 95:
                status = 'warning'
                message = f"CPU usage is high: {cpu_percent:.1f}%"
            else:
                status = 'critical'
                message = f"CPU usage is critical: {cpu_percent:.1f}%"
            
            return HealthCheck(
                name='cpu_usage',
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={'cpu_percent': cpu_percent}
            )
        except Exception as e:
            return HealthCheck(
                name='cpu_usage',
                status='critical',
                message=f"Failed to check CPU usage: {e}",
                timestamp=datetime.now(),
                details={'error': str(e)}
            )
    
    def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            if memory_percent < 80:
                status = 'healthy'
                message = f"Memory usage is normal: {memory_percent:.1f}%"
            elif memory_percent < 95:
                status = 'warning'
                message = f"Memory usage is high: {memory_percent:.1f}%"
            else:
                status = 'critical'
                message = f"Memory usage is critical: {memory_percent:.1f}%"
            
            return HealthCheck(
                name='memory_usage',
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    'memory_percent': memory_percent,
                    'memory_used_gb': memory.used / (1024**3),
                    'memory_total_gb': memory.total / (1024**3)
                }
            )
        except Exception as e:
            return HealthCheck(
                name='memory_usage',
                status='critical',
                message=f"Failed to check memory usage: {e}",
                timestamp=datetime.now(),
                details={'error': str(e)}
            )
    
    def _check_disk_usage(self) -> HealthCheck:
        """Check disk usage."""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            if disk_percent < 80:
                status = 'healthy'
                message = f"Disk usage is normal: {disk_percent:.1f}%"
            elif disk_percent < 95:
                status = 'warning'
                message = f"Disk usage is high: {disk_percent:.1f}%"
            else:
                status = 'critical'
                message = f"Disk usage is critical: {disk_percent:.1f}%"
            
            return HealthCheck(
                name='disk_usage',
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    'disk_percent': disk_percent,
                    'disk_used_gb': disk.used / (1024**3),
                    'disk_total_gb': disk.total / (1024**3)
                }
            )
        except Exception as e:
            return HealthCheck(
                name='disk_usage',
                status='critical',
                message=f"Failed to check disk usage: {e}",
                timestamp=datetime.now(),
                details={'error': str(e)}
            )
    
    def _check_disk_space(self) -> HealthCheck:
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024**3)
            
            if free_gb > 10:
                status = 'healthy'
                message = f"Sufficient disk space available: {free_gb:.1f} GB"
            elif free_gb > 1:
                status = 'warning'
                message = f"Low disk space: {free_gb:.1f} GB available"
            else:
                status = 'critical'
                message = f"Critical disk space: {free_gb:.1f} GB available"
            
            return HealthCheck(
                name='disk_space',
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={'free_gb': free_gb}
            )
        except Exception as e:
            return HealthCheck(
                name='disk_space',
                status='critical',
                message=f"Failed to check disk space: {e}",
                timestamp=datetime.now(),
                details={'error': str(e)}
            )
    
    def _check_python_environment(self) -> HealthCheck:
        """Check Python environment."""
        try:
            import sys
            python_version = sys.version
            python_path = sys.executable
            
            # Check if running in virtual environment
            in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            
            status = 'healthy'
            message = f"Python environment is healthy: {python_version}"
            
            return HealthCheck(
                name='python_environment',
                status=status,
                message=message,
                timestamp=datetime.now(),
                details={
                    'python_version': python_version,
                    'python_path': python_path,
                    'in_virtual_environment': in_venv
                }
            )
        except Exception as e:
            return HealthCheck(
                name='python_environment',
                status='critical',
                message=f"Failed to check Python environment: {e}",
                timestamp=datetime.now(),
                details={'error': str(e)}
            )
    
    def _check_required_packages(self) -> HealthCheck:
        """Check required packages."""
        required_packages = [
            'pandas', 'numpy', 'plotly', 'openpyxl', 'psutil'
        ]
        
        missing_packages = []
        package_versions = {}
        
        for package in required_packages:
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                package_versions[package] = version
            except ImportError:
                missing_packages.append(package)
        
        if not missing_packages:
            status = 'healthy'
            message = "All required packages are available"
        else:
            status = 'critical'
            message = f"Missing required packages: {', '.join(missing_packages)}"
        
        return HealthCheck(
            name='required_packages',
            status=status,
            message=message,
            timestamp=datetime.now(),
            details={
                'missing_packages': missing_packages,
                'package_versions': package_versions
            }
        )
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> str:
        """Determine overall health status."""
        if any(check.status == 'critical' for check in checks):
            return 'critical'
        elif any(check.status == 'warning' for check in checks):
            return 'warning'
        else:
            return 'healthy'
    
    def _check_to_dict(self, check: HealthCheck) -> Dict[str, Any]:
        """Convert health check to dictionary."""
        return {
            'name': check.name,
            'status': check.status,
            'message': check.message,
            'timestamp': check.timestamp.isoformat(),
            'details': check.details
        }
    
    def _create_summary(self, checks: List[HealthCheck]) -> Dict[str, Any]:
        """Create summary of health checks."""
        status_counts = {
            'healthy': len([c for c in checks if c.status == 'healthy']),
            'warning': len([c for c in checks if c.status == 'warning']),
            'critical': len([c for c in checks if c.status == 'critical'])
        }
        
        return {
            'total_checks': len(checks),
            'status_counts': status_counts,
            'overall_status': self._determine_overall_status(checks)
        }
    
    def get_health_history(self) -> List[Dict[str, Any]]:
        """Get health check history."""
        with self._lock:
            return [self._check_to_dict(check) for check in self.checks]
    
    def clear_history(self) -> None:
        """Clear health check history."""
        with self._lock:
            self.checks.clear()
            logger.info("Cleared health check history")


class HealthMonitor:
    """Continuous health monitoring."""
    
    def __init__(self, health_checker: HealthChecker):
        """Initialize the health monitor."""
        self.health_checker = health_checker
        self._monitoring = False
        self._monitor_thread = None
        self.health_history: List[Dict[str, Any]] = []
        
    def start_monitoring(self, interval: float = 60.0) -> None:
        """
        Start continuous health monitoring.
        
        Args:
            interval: Health check interval in seconds
        """
        if self._monitoring:
            logger.warning("Health monitoring already started")
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        logger.info("Started health monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
        logger.info("Stopped health monitoring")
    
    def _monitor_loop(self, interval: float) -> None:
        """Health monitoring loop."""
        while self._monitoring:
            try:
                health_status = self.health_checker.check_system_health()
                self.health_history.append(health_status)
                
                # Keep only last 100 entries
                if len(self.health_history) > 100:
                    self.health_history = self.health_history[-100:]
                
                # Log critical issues
                if health_status['status'] == 'critical':
                    logger.critical(f"Critical health issue detected: {health_status}")
                elif health_status['status'] == 'warning':
                    logger.warning(f"Health warning: {health_status}")
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(interval)
    
    def get_health_history(self) -> List[Dict[str, Any]]:
        """Get health monitoring history."""
        return self.health_history.copy()
    
    def get_current_health(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health_checker.check_system_health()


# Global instances
health_checker = HealthChecker()
health_monitor = HealthMonitor(health_checker) 