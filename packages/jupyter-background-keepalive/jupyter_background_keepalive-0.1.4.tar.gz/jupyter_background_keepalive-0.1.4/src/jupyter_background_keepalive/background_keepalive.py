import os
import json
import glob
import getpass
import requests
import threading

_keepalive_thread = None
_stop_event = threading.Event()


def _send_hub_activity_ping():
    """Sends a single ping to the JupyterHub activity endpoint."""
    jupyter_runtime_dir = os.environ.get("JUPYTER_RUNTIME_DIR")
    if not jupyter_runtime_dir:
        print("Keepalive Warning: JUPYTER_RUNTIME_DIR environment variable not found.")
        return False

    # Find the jpserver-XXXX.json file
    runtime_files = glob.glob(os.path.join(jupyter_runtime_dir, "jpserver-*.json"))
    if not runtime_files:
        print(f"Keepalive Warning: No jpserver-*.json found in {jupyter_runtime_dir}")
        return False

    # Sort by modification time and pick the newest
    runtime_files.sort(key=os.path.getmtime, reverse=True)
    runtime_file_path = runtime_files[0]

    try:
        with open(runtime_file_path, "r") as f:
            server_info = json.load(f)
        hub_api_url = server_info.get("url")
        api_token = server_info.get("token")
        hub_user = getpass.getuser() # Get username using getpass
    except Exception as e:
        print(f"Keepalive Error: Failed to read or parse {runtime_file_path}: {e}")
        return False

    if not all([hub_api_url, hub_user]) or not api_token:
        print("Keepalive Warning: Jupyter server info (url, token, or user) not found.")
        return False

    activity_url = f"{hub_api_url}/users/{hub_user}/activity"
    headers = {"Authorization": f"token {api_token}"}

    try:
        r = requests.post(activity_url, headers=headers, json={}, timeout=10)
        if r.status_code not in [200, 204]:
            print(f"Keepalive Error: Failed ping ({r.status_code})")
        # No need to print on success, keep it clean
    except Exception as e:
        print(f"Keepalive Error: Exception during ping: {e}")
    return True  # Indicate success or handled error


def _keepalive_loop(interval_seconds=180):
    """Periodically pings the hub until the stop event is set."""
    print(f"Keepalive: Starting activity pings every {interval_seconds} seconds.")
    if not _send_hub_activity_ping():  # Initial ping check
        print("Keepalive Error: Initial ping failed. Stopping keepalive.")
        return

    while not _stop_event.wait(interval_seconds):
        _send_hub_activity_ping()
    print("Keepalive: Stopped activity pings.")


def start(interval_seconds=30):
    """Starts the background keepalive ping thread."""
    global _keepalive_thread, _stop_event
    if _keepalive_thread is None or not _keepalive_thread.is_alive():
        _stop_event.clear()
        _keepalive_thread = threading.Thread(
            target=_keepalive_loop, args=(interval_seconds,), daemon=True
        )
        _keepalive_thread.start()
    else:
        print("Keepalive: Already running.")


def stop():
    """Stops the background keepalive ping thread."""
    global _keepalive_thread
    if _keepalive_thread and _keepalive_thread.is_alive():
        _stop_event.set()
        _keepalive_thread.join(timeout=5)  # Wait briefly for thread to exit
        _keepalive_thread = None
