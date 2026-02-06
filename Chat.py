#!/usr/bin/env python3

import subprocess
import sys
import getpass
import time
import signal
import threading

PORT = "9000"
current_process = None


# -----------------------------
# Service helpers
# -----------------------------
def service_running(service):
    result = subprocess.run(
        ["systemctl", "is-active", service],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() == "active"


def ensure_service(service):
    if service_running(service):
        print(f"[OK] {service} running")
        return

    print(f"Starting {service}...")
    subprocess.run(["sudo", "systemctl", "start", service])
    time.sleep(2)


def ensure_ssh():
    # distro-safe SSH handling
    if service_running("ssh"):
        ensure_service("ssh")
    else:
        ensure_service("sshd")


def ensure_runtime():
    print("\n=== Checking runtime services ===\n")
    ensure_service("tor")
    ensure_ssh()


# -----------------------------
# Chat logic
# -----------------------------
def listen_background():
    global current_process
    current_process = subprocess.Popen(["ncat", "-l", PORT])
    current_process.wait()


def auto_chat(onion):
    global current_process

    ensure_runtime()

    print("\nPreparing peer connection...\n")

    # Start background listener
    listener_thread = threading.Thread(
        target=listen_background,
        daemon=True
    )
    listener_thread.start()

    time.sleep(2)

    user = getpass.getuser()

    print("Trying outbound connection...\n")

    ssh_command = [
        "ssh",
        "-o",
        "ProxyCommand=ncat --proxy 127.0.0.1:9050 --proxy-type socks5 %h %p",
        f"{user}@{onion}",
        "ncat",
        "127.0.0.1",
        PORT,
    ]

    current_process = subprocess.Popen(ssh_command)
    current_process.wait()


# -----------------------------
# Shutdown handling
# -----------------------------
def shutdown(signum, frame):
    global current_process

    print("\n\nClosing chat gracefully...\n")

    if current_process:
        current_process.terminate()

    sys.exit(0)


# -----------------------------
# CLI entry
# -----------------------------
def main():
    signal.signal(signal.SIGINT, shutdown)

    if len(sys.argv) < 2:
        print("Usage: chat.py <peer.onion>")
        sys.exit(1)

    onion = sys.argv[1]
    auto_chat(onion)


if __name__ == "__main__":
    main()
