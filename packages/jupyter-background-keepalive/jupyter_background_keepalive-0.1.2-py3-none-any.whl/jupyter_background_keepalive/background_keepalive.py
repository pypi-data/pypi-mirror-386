import os
import requests
import threading

_keepalive_thread = None
_stop_event = threading.Event()


def _send_hub_activity_ping():
    """Sends a single ping to the JupyterHub activity endpoint."""
    hub_api_url = os.environ.get("JUPYTERHUB_API_URL")
    hub_user = os.environ.get("JUPYTERHUB_USER")
    api_token = os.environ.get("JUPYTERHUB_API_TOKEN")

    if not all([hub_api_url, hub_user, api_token]):
        print("Keepalive Warning: JupyterHub environment variables not found.")
        return False  # Indicate failure

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
