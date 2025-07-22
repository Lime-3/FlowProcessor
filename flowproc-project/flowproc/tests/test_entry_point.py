import subprocess
import time
import pytest

@pytest.mark.integration  # Custom mark, registered in pyproject.toml
def test_flowproc_command():
    """Test that the flowproc command launches the GUI without immediate errors."""
    p = subprocess.Popen(["python", "-m", "flowproc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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