import subprocess
import time
import sys
import os
import signal

components = [
    ("Backend API", "python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload", "growda/backend"),
    ("FL Server", "python3 fl_server.py", "growda/backend"),
    # Wait for servers to start
    ("WAIT", 5, None),
    ("Hospital A Client", "python3 client.py", "growda/clients/hospital_A"),
    ("Hospital B Client", "python3 client.py", "growda/clients/hospital_B"),
    ("Frontend", "npm run dev", "growda/frontend"),
]

processes = []

def cleanup(signum, frame):
    print("\nStopping all services...")
    for p in processes:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

base_dir = os.path.dirname(os.path.abspath(__file__))

print("Starting Growda System...")

for name, cmd, rel_dir in components:
    if name == "WAIT":
        print(f"Waiting {cmd} seconds for servers to initialize...")
        time.sleep(cmd)
        continue

    print(f"Starting {name}...")
    cwd = os.path.join(base_dir, rel_dir)
    
    p = subprocess.Popen(cmd, shell=True, cwd=cwd, preexec_fn=os.setsid)
    processes.append(p)

print("All services started. Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup(None, None)
