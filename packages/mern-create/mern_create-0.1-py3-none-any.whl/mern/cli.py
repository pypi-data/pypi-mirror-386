import subprocess
import sys
import os

def main():
    if len(sys.argv) != 2:
        print("Usage: mern <app-name>")
        sys.exit(1)
    app_name = sys.argv[1]
    script_path = os.path.join(os.path.dirname(__file__), "mern.sh")
    subprocess.run(["bash", script_path, app_name], check=True)

