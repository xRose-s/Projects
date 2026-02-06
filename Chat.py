#!/usr/bin/env python3

import subprocess
import sys
import getpass
import time
import signal
import threading
import os

PORT = "9000"
processes = []


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
    if service_running("ssh"):
        ensure_service("ssh")
    else:
        ensure_service("sshd")


def ensure_runtime():
    print("\n=== Checking runtime services ===\n")
    ensure_service("tor")
    ensure_ssh()


# -----------------------------
# Cleanup helpers
# -----------------------------
def cleanup_port():
    subprocess.run(
        ["sudo", "pkill", "-f", f"ncat.*{PORT}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def cleanup_processes():
    for p in processes:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            pass

    cleanup_port()


# -----------------------------
# Chat logic
# -----------------------------
def listen_background():
    p = subprocess.Popen(
        ["ncat", "-l", PORT],
        preexec_fn=os.setsid
    )
    processes.append(p)
    p.wait()


def auto_chat(onion):
    ensure_runtime()

    print("\nPreparing peer connection...\n")

    cleanup_port()

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

    for _ in range(3):
        try:
            p = subprocess.Popen(
                ssh_command,
                preexec_fn=os.setsid
            )
            processes.append(p)
            p.wait()
            return
        except Exception:
            print("Retrying connection...")
            time.sleep(3)

    print("Waiting for peer to join...")
    listener_thread.join()


# -----------------------------
# Shutdown handling
# -----------------------------
def shutdown(signum=None, frame=None):
    print("\n\nClosing chat gracefully...\n")
    cleanup_processes()
    sys.exit(0)


# -----------------------------
# CLI entry
# -----------------------------
def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    if len(sys.argv) < 2:
        print("Usage: chat.py <peer.onion>")
        sys.exit(1)

    onion = sys.argv[1]
    auto_chat(onion)


if __name__ == "__main__":
    main()
