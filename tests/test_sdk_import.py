import subprocess
import sys
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_importing_sensor_client_does_not_create_uart():
    code = textwrap.dedent(
        """
        import sys
        import types

        calls = []

        class UART:
            def __init__(self, *args, **kwargs):
                calls.append((args, kwargs))

        class Pin:
            def __init__(self, number):
                self.number = number

        machine = types.ModuleType("machine")
        machine.UART = UART
        machine.Pin = Pin
        sys.modules["machine"] = machine

        from esp32api import SensorClient

        if calls:
            raise SystemExit("UART was created during import: %r" % (calls,))
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
