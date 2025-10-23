#!/usr/bin/env python3
"""
Production Readiness Test for Doorman CLI
This script tests all core functionality to ensure the app is production-ready.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd
        )
        if check and result.returncode != 0:
            print(f"❌ Command failed: {cmd}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return None
        return result
    except Exception as e:
        print(f"❌ Exception running command: {cmd}")
        print(f"Error: {e}")
        return None


def test_basic_functionality():
    """Test basic Doorman CLI functionality."""
    print("🧪 Testing basic Doorman CLI functionality...")

    # Test help command
    result = run_command("python3 -m doorman --help")
    if result is None:
        return False

    if "DOORMAN.EXE" not in result.stdout:
        print("❌ Help command doesn't show expected output")
        return False

    print("✅ Help command works")
    return True


def test_config_commands():
    """Test configuration commands."""
    print("🔧 Testing configuration commands...")

    # Test config doctor
    result = run_command("python3 -m doorman config doctor")
    if result is None:
        return False

    if "All checks passed" not in result.stdout and "🎉" not in result.stdout:
        print("❌ Config doctor doesn't show expected output")
        print(f"Output: {result.stdout}")
        return False

    print("✅ Config doctor works")
    return True


def test_plan_generation():
    """Test plan generation functionality."""
    print("📝 Testing plan generation...")

    # Test simple plan with script-only output
    result = run_command(
        "python3 -m doorman plan 'create a simple python script that prints hello world' --script-only"
    )
    if result is None:
        return False

    if "#!/bin/bash" not in result.stdout:
        print("❌ Script generation doesn't produce expected output")
        print(f"Output: {result.stdout}")
        return False

    # Test that the generated script is valid
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(result.stdout)
        script_path = f.name

    try:
        # Make script executable
        os.chmod(script_path, 0o755)

        # Run the script
        script_result = run_command(f"bash {script_path}")
        if script_result is None:
            print("❌ Generated script failed to run")
            return False

        print("✅ Plan generation works")
        return True
    finally:
        # Clean up
        if os.path.exists(script_path):
            os.unlink(script_path)


def test_provider_status():
    """Test provider status functionality."""
    print("🔌 Testing provider status...")

    result = run_command("python3 -m doorman providers")
    if result is None:
        return False

    if "PROVIDER STATUS" not in result.stdout:
        print("❌ Provider status command doesn't show expected output")
        print(f"Output: {result.stdout}")
        return False

    print("✅ Provider status works")
    return True


def test_demo_command():
    """Test demo command."""
    print("🎮 Testing demo command...")

    result = run_command("python3 -m doorman demo")
    if result is None:
        return False

    if "Demo complete" not in result.stdout:
        print("❌ Demo command doesn't show expected output")
        print(f"Output: {result.stdout}")
        return False

    print("✅ Demo command works")
    return True


def main():
    """Main test function."""
    print("🚀 Starting Doorman Production Readiness Test")
    print("=" * 50)

    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Run all tests
    tests = [
        test_basic_functionality,
        test_config_commands,
        test_plan_generation,
        test_provider_status,
        test_demo_command,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Doorman is production-ready!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
