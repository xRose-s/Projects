#!/usr/bin/env python3

import subprocess
import shutil
import sys
import os
import time

REQUIRED_TOOLS = {
    "tor": ["tor"],
    "ssh": ["openssh-server", "openssh"],
    "sshd": ["openssh-server"],
    "ncat": ["ncat", "nmap-ncat"]
}

TORRC_PATH = "/etc/tor/torrc"
HIDDEN_SERVICE_DIR = "/var/lib/tor/ssh_p2p"

HIDDEN_SERVICE_CONFIG = """
# SSH + Chat P2P hidden service
HiddenServiceDir /var/lib/tor/ssh_p2p/
HiddenServicePort 22 127.0.0.1:22
HiddenServicePort 9000 127.0.0.1:9000
"""


# -----------------------------
# helpers
# -----------------------------
def run(cmd):
    return subprocess.run(cmd, shell=True)


def command_exists(cmd):
    return shutil.which(cmd) is not None


def detect_package_manager():
    if command_exists("apt"):
        return "apt"
    elif command_exists("dnf"):
        return "dnf"
    elif command_exists("pacman"):
        return "pacman"
    else:
        return None


# -----------------------------
# package installation
# -----------------------------
def install_packages(manager, packages):
    print(f"\nInstalling missing packages: {packages}\n")

    if manager == "apt":
        run("apt update")
        run(f"apt install -y {' '.join(packages)}")

    elif manager == "dnf":
        run(f"dnf install -y {' '.join(packages)}")

    elif manager == "pacman":
        run(f"pacman -Sy --noconfirm {' '.join(packages)}")

    else:
        print("Unsupported package manager.")
        sys.exit(1)


# -----------------------------
# tor configuration
# -----------------------------
def configure_tor():
    print("\n=== Configuring Tor hidden service ===\n")

    if not os.path.exists(TORRC_PATH):
        print("Tor config not found.")
        sys.exit(1)

    with open(TORRC_PATH, "r") as f:
        content = f.read()

    if HIDDEN_SERVICE_DIR in content:
        print("[OK] Hidden service already configured.")
        return False

    print("Adding hidden service config...")
    with open(TORRC_PATH, "a") as f:
        f.write("\n" + HIDDEN_SERVICE_CONFIG + "\n")

    return True


def restart_tor():
    print("\nRestarting Tor service...")
    run("systemctl restart tor")
    time.sleep(5)


def stop_tor():
    print("\nStopping Tor service...")
    run("systemctl stop tor")


def show_onion_address():
    hostname_file = f"{HIDDEN_SERVICE_DIR}/hostname"

    if not os.path.exists(hostname_file):
        print("Onion hostname not created yet.")
        return

    with open(hostname_file, "r") as f:
        onion = f.read().strip()

    print("\n=== NODE READY ===")
    print(f"Your onion address:\n{onion}\n")


# -----------------------------
# main
# -----------------------------
def main():
    print("\n=== Checking system dependencies ===\n")

    manager = detect_package_manager()
    if not manager:
        print("No supported package manager found.")
        sys.exit(1)

    print(f"Package manager detected: {manager}\n")

    missing_packages = []

    for tool, pkg_options in REQUIRED_TOOLS.items():
        if command_exists(tool):
            print(f"[OK] {tool} found")
        else:
            print(f"[MISSING] {tool}")
            missing_packages.append(pkg_options[0])

    if missing_packages:
        install_packages(manager, missing_packages)
        print("\nDependency installation complete.")
    else:
        print("\nAll dependencies installed.")

    changed = configure_tor()

    hostname_file = f"{HIDDEN_SERVICE_DIR}/hostname"
    if changed or not os.path.exists(hostname_file):
        restart_tor()

    show_onion_address()

    stop_tor()


if __name__ == "__main__":
    main()
