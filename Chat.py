#!/usr/bin/env python3

import subprocess
import sys
import time
import signal
import os

PORT = "9000"
processes = []


# -----------------------------
# DEBUG HELPERS
# -----------------------------
def run_debug(cmd):
    print(f"\n[DEBUG] Running: {' '.join(cmd)}")
    subprocess.run(cmd)


def debug_state(stage):
    print(f"\n========== DEBUG STATE: {stage} ==========")

    print("\nTor status:")
    run_debug(["systemctl", "is-active", "tor"])

    print("\nSSH status:")
    run_debug(["systemctl", "is-active", "ssh"])
    run_debug(["systemctl", "is-active", "sshd"])

    print("\nPort listeners:")
    run_debug(["ss", "-lntp"])

    print("\nNcat processes:")
    run_debug(["pgrep", "-a", "ncat"])

    print("\nSSH processes:")
    run_debug(["pgrep", "-a", "ssh"])

    print("\nTor SOCKS port:")
    run_debug(["ss", "-lntp", "|", "grep", "9050"])

    print("\n===========================================")


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
    subprocess.run(["sudo", "systemctl", "start", service])
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
    debug_state("runtime-ready")


# -----------------------------
# Cleanup helpers
# -----------------------------
def cleanup_port():
    subprocess.run(
        ["sudo", "pkill", "-9", "-f", "ncat"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def cleanup_processes():
    print("\n[DEBUG] Cleaning up processes...")

    for p in processes:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        except Exception:
            pass

    cleanup_port()
    time.sleep(1)


# -----------------------------
# Chat logic
# -----------------------------
def listen_mode():
    ensure_runtime()

    cleanup_port()

    print("\n=== Listener Mode ===")
    print("Waiting for peer...\n")

    debug_state("before-listen")

    p = subprocess.Popen(
        ["ncat", "-l", "127.0.0.1", PORT],
        preexec_fn=os.setsid
    )
    processes.append(p)
    p.wait()

    debug_state("listener-exit")


def host_mode():
    ensure_runtime()

    onion = input("Enter peer onion address: ").strip()
    user = input("Enter Remote Username :   ")

    print("\nWaiting for peer...")
    input("Press ENTER when peer ready...")

    debug_state("before-connect")

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

    p = subprocess.Popen(
        ssh_command,
        preexec_fn=os.setsid
    )
    processes.append(p)
    p.wait()

    debug_state("after-connect")


# -----------------------------
# Shutdown
# -----------------------------
def shutdown(signum=None, frame=None):
    print("\nClosing chat gracefully...\n")
    cleanup_processes()
    sys.exit(0)


# -----------------------------
# Menu
# -----------------------------
def menu():
    print("\nSelect mode:")
    print("1) Host")
    print("2) Listener")

    choice = input("> ").strip()

    if choice == "1":
        host_mode()
    elif choice == "2":
        listen_mode()
    else:
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
