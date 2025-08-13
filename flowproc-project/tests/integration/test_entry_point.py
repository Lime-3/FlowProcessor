import subprocess
import sys
import time
import pytest

@pytest.mark.integration  # Custom mark, registered in pyproject.toml
def test_flowproc_command():
    """Test that the flowproc command launches the GUI without immediate errors."""
    # Skip test if PySide6 is not installed in the current interpreter or a child subprocess
    try:
        import PySide6  # noqa: F401
    except Exception:
        pytest.skip("PySide6 not installed; skipping GUI entry-point test")
    # Verify that the child process interpreter can import PySide6 as well
    check = subprocess.run([sys.executable, "-c", "import PySide6"], capture_output=True)
    if check.returncode != 0:
        pytest.skip("PySide6 not available in child interpreter; skipping GUI entry-point test")
    p = subprocess.Popen([sys.executable, "-m", "flowproc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    max_wait_time = 5  # Maximum wait time in seconds
    start_time = time.time()
    out, err = b"", b""
    while time.time() - start_time < max_wait_time:
        # Read initial 2KB of output
        new_out = p.stdout.read(2048)
        new_err = p.stderr.read(2048)
        out += new_out
        err += new_err
        if b"GUI application started" in out or b"GUI application started" in err:
            break
        time.sleep(0.1)  # Small sleep to prevent tight looping
    p.terminate()  # Gracefully terminate the process
    time.sleep(0.5)  # Wait for termination
    if p.poll() is None:  # If still running, force kill
        p.kill()
    assert "GUI application started" in out.decode('utf-8') or "GUI application started" in err.decode('utf-8')  # Verify GUI initialization
    assert "Error" not in err.decode('utf-8')  # No immediate errors
    print(f"Test completed in {time.time() - start_time:.2f} seconds")  # Debug runtime