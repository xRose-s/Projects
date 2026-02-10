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
        return True

    print(f"Starting {service}...")
    subprocess.run(
        ["sudo", "systemctl", "start", service],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)

    return service_running(service)


def ensure_ssh():
    if ensure_service("ssh"):
        return
    if ensure_service("sshd"):
        return

    print("[WARN] Could not start SSH service.")


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
def listen_mode():
    ensure_runtime()

    cleanup_port()

    print("\n=== Listener Mode ===")
    print("Waiting for peer...\n")
    print("Press Ctrl+C to exit\n")

    p = subprocess.Popen(
        ["ncat", "-l", "127.0.0.1", PORT],
        preexec_fn=os.setsid
    )
    processes.append(p)
    p.wait()


def host_mode():
    ensure_runtime()

    onion = input("Enter peer onion address: ").strip()

    user = getpass.getuser()

    print("\nWaiting for peer to start listener...")
    input("Press ENTER when peer is ready...")

    # ✅ SSH fix added here
    ssh_command = [
        "ssh",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o",
        "ProxyCommand=ncat --proxy 127.0.0.1:9050 --proxy-type socks5 %h %p",
        f"{user}@{onion}",
        "ncat",
        "127.0.0.1",
        PORT,
    ]

    p = subprocess.Popen(ssh_command)
    processes.append(p)
    p.wait()


# -----------------------------
# Shutdown handling
# -----------------------------
def shutdown(signum=None, frame=None):
    print("\n\nClosing chat gracefully...\n")
    cleanup_processes()
    sys.exit(0)


# -----------------------------
# Menu
# -----------------------------
def menu():
    print("\nSelect mode:")
    print("1) Host (connect)")
    print("2) Listener (wait)")
    choice = input("> ").strip()

    if choice == "1":
        host_mode()
    elif choice == "2":
        listen_mode()
    else:
        print("Invalid choice.")
        menu()


# -----------------------------
# Entry
# -----------------------------
def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    menu()


if __name__ == "__main__":
    main()
