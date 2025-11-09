import os
import signal

PID = 38252

try:
    # SIGKILL más agresivo en Windows
    os.kill(PID, signal.SIGTERM)
    print(f"Sent SIGTERM to {PID}")

    # En Windows también podemos usar directamente el comando
    import subprocess
    result = subprocess.run(['taskkill', '/F', '/PID', str(PID)],
                          capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
except Exception as e:
    print(f"Error: {e}")
