#!/usr/bin/env python3

import subprocess
import shutil
import sys

REQUIRED_TOOLS = {
    "tor": ["tor"],
    "ssh": ["openssh-server", "openssh"],
    "sshd": ["openssh-server"],
    "ncat": ["ncat", "nmap-ncat"]
}

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

    if not missing_packages:
        print("\nAll dependencies are installed.")
        sys.exit(0)

    print("\nMissing dependencies detected.")
    install
