#!/usr/bin/env python3
"""
Demo Script for Production-Ready Doorman CLI
This script demonstrates all core functionality in a simple, elegant way.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and display results elegantly."""
    print(f"\n🔍 {description}")
    print(f"   Command: {cmd}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Success")
            if result.stdout.strip():
                # Show first few lines of output
                lines = result.stdout.strip().split("\n")
                for line in lines[:3]:
                    print(f"      {line}")
                if len(lines) > 3:
                    print(f"      ... ({len(lines) - 3} more lines)")
            return True
        else:
            print("   ❌ Failed")
            if result.stderr.strip():
                print(f"      Error: {result.stderr.strip()[:100]}...")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def main():
    """Demonstrate production-ready functionality."""
    print("🚀 Doorman Production Demo")
    print("=" * 40)

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Demo sequence
    demos = [
        ("Check CLI help", "python3 -m doorman --help"),
        ("Run configuration check", "python3 -m doorman config doctor"),
        ("List AI providers", "python3 -m doorman providers list"),
        ("Show available agents", "python3 -m doorman fighters"),
        (
            "Generate simple plan",
            "python3 -m doorman plan 'create a hello world python script' --script-only",
        ),
    ]

    success_count = 0
    for description, command in demos:
        if run_command(command, description):
            success_count += 1

    print(f"\n🏁 Demo Complete: {success_count}/{len(demos)} demonstrations successful")

    if success_count == len(demos):
        print("🎉 All demonstrations passed! Doorman is production-ready!")
        return 0
    else:
        print("⚠️  Some demonstrations failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
