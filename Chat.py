#!/usr/bin/env python3

import subprocess
import sys
import getpass
import time
import signal

current_process = None

PORT = "9000"


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
    # Works across distros
    if service_running("ssh"):
        ensure_service("ssh")
    else:
        ensure_service("sshd")


def ensure_runtime():
    print("\n=== Checking runtime services ===\n")
    ensure_service("tor")
    ensure_ssh()


# -----------------------------
# Chat functions
# -----------------------------
def listen():
    ensure_runtime()

    print("\n=== Chat Listener ===")
    print(f"Listening on port {PORT}...\n")
    print("Waiting for peer...\n")

    global current_process
    current_process = subprocess.Popen(["ncat", "-l", PORT])
    current_process.wait()


def connect(onion):
    ensure_runtime()

    user = getpass.getuser()

    print("\n=== Connecting ===")
    print(f"User: {user}")
    print(f"Target: {onion}\n")

    ssh_command = [
        "ssh",
        "-o",
        "ProxyCommand=ncat --proxy 127.0.0.1:9050 --proxy-type socks5 %h %p",
        f"{user}@{onion}",
        "ncat",
        "127.0.0.1",
        PORT,
    ]

    global current_process
    current_process = subprocess.Popen(ssh_command)
    current_process.wait()

def shutdown(signum, frame):
    global current_process
    print("\n \nClosing chat... ")
    
    if current_process:
        current_process.terminate
    sys.exit(0)


# -----------------------------
# CLI
# -----------------------------
def usage():
    print("\nUsage:")
    print("  chat.py listen")
    print("  chat.py connect <onion>\n")


def main():
    signal.signal(signal.SIGINT, shutdown)
    
    
    if len(sys.argv) < 2:
        listen()
        return

    command = sys.argv[1]

    if command == "listen":
        listen()

    elif command == "connect":
        if len(sys.argv) < 3:
            usage()
            sys.exit(1)

        onion = sys.argv[2]
        connect(onion)

    else:
        usage()


if __name__ == "__main__":
    main()
