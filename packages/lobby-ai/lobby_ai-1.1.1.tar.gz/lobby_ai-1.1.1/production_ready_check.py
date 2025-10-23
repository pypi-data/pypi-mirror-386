#!/usr/bin/env python3
"""
Production Readiness Check for Doorman CLI
This script verifies that Doorman is production-ready by testing core functionality.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd
        )
        return result
    except Exception as e:
        print(f"❌ Exception running command '{cmd}': {e}")
        return None


def check_help_command():
    """Check that help command works."""
    print("🔍 Testing help command...")
    result = run_command("python3 -m doorman --help")
    if result is None or result.returncode != 0:
        print("❌ Help command failed")
        return False

    if "DOORMAN.EXE" not in result.stdout:
        print("❌ Help command doesn't show expected output")
        return False

    print("✅ Help command works correctly")
    return True


def check_config_doctor():
    """Check that config doctor works."""
    print("🔍 Testing config doctor...")
    result = run_command("python3 -m doorman config doctor")
    if result is None or result.returncode != 0:
        print("❌ Config doctor failed")
        return False

    if "All checks passed" not in result.stdout and "🎉" not in result.stdout:
        print("❌ Config doctor doesn't show expected output")
        return False

    print("✅ Config doctor works correctly")
    return True


def check_plan_generation():
    """Check that plan generation works."""
    print("🔍 Testing plan generation...")
    result = run_command(
        "python3 -m doorman plan 'create a simple file with hello world' --script-only"
    )
    if result is None or result.returncode != 0:
        print("❌ Plan generation failed")
        if result:
            print(f"STDERR: {result.stderr}")
        return False

    # Check that we got a shell script (allow for error messages at the beginning)
    lines = result.stdout.split("\n")
    script_lines = [
        line
        for line in lines
        if line.startswith("#!/bin/bash")
        or (line and not line.startswith("Failed to record"))
    ]

    if not script_lines or not script_lines[0].startswith("#!/bin/bash"):
        print("❌ Generated output is not a valid shell script")
        print(f"First few lines: {lines[:5]}")
        return False

    # Test that the script can be executed (basic syntax check)
    script_content = "\n".join(script_lines)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(script_content)
        script_path = f.name

    try:
        # Make script executable and test basic syntax
        os.chmod(script_path, 0o755)
        syntax_result = run_command(f"bash -n {script_path}")
        if syntax_result is None or syntax_result.returncode != 0:
            print("❌ Generated script has syntax errors")
            return False

        print("✅ Plan generation works correctly")
        return True
    finally:
        # Clean up
        if os.path.exists(script_path):
            os.unlink(script_path)


def check_provider_commands():
    """Check that provider commands work."""
    print("🔍 Testing provider commands...")

    # Test provider list
    result = run_command("python3 -m doorman providers list")
    if result is None or result.returncode != 0:
        print("❌ Provider list command failed")
        return False

    if "PROVIDER" not in result.stdout.upper():
        print("❌ Provider list doesn't show expected output")
        return False

    print("✅ Provider commands work correctly")
    return True


def check_fighters_command():
    """Check that fighters command works."""
    print("🔍 Testing fighters command...")
    result = run_command("python3 -m doorman fighters")
    if result is None or result.returncode != 0:
        print("❌ Fighters command failed")
        return False

    if "FIGHTER" not in result.stdout.upper():
        print("❌ Fighters command doesn't show expected output")
        return False

    print("✅ Fighters command works correctly")
    return True


def main():
    """Main function to run all checks."""
    print("🚀 Doorman Production Readiness Check")
    print("=" * 50)

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Run all checks
    checks = [
        check_help_command,
        check_config_doctor,
        check_plan_generation,
        check_provider_commands,
        check_fighters_command,
    ]

    passed = 0
    failed = 0

    for check in checks:
        try:
            if check():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Check {check.__name__} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All checks passed! Doorman is production-ready!")
        return 0
    else:
        print("⚠️  Some checks failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
