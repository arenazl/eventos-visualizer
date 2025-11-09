import os
import signal

PID = 38252

try:
    os.kill(PID, signal.SIGTERM)
    print(f"Killed process {PID}")
except Exception as e:
    print(f"Error: {e}")
