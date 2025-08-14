#!/usr/bin/env python3

from flowproc.infrastructure.monitoring.health import HealthChecker


def main() -> None:
    checker = HealthChecker()
    report = checker.check_system_health()

    status = report.get('status', 'unknown')
    print("System Health Report")
    print(f"Status: {status}")

    for check in report.get('checks', []):
        name = check.get('name', 'unknown')
        cstatus = check.get('status', 'unknown')
        message = check.get('message', '')
        print(f"- {name}: {cstatus} - {message}")

    raise SystemExit(0 if status != 'critical' else 1)


if __name__ == "__main__":
    main()