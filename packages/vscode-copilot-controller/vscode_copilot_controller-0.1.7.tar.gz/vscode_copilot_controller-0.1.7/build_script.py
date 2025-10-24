#!/usr/bin/env python3
"""Build script for vscode-copilot-controller package.

This script helps with building and uploading the package to PyPI.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str) -> bool:
    """Run a command and return success status."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def clean_build():
    """Clean previous build artifacts."""
    print("🧹 Cleaning build artifacts...")
    
    # Remove build directories
    for path in ["build", "dist", "*.egg-info"]:
        if Path(path).exists():
            if sys.platform == "win32":
                subprocess.run(f"rmdir /s /q {path}", shell=True, capture_output=True)
            else:
                subprocess.run(f"rm -rf {path}", shell=True, capture_output=True)
    
    print("✅ Build artifacts cleaned")


def run_tests():
    """Run the test suite."""
    print("🧪 Running tests...")
    
    if not run_command("python -m pytest tests/ -v"):
        print("❌ Tests failed!")
        return False
        
    print("✅ All tests passed")
    return True


def run_linting():
    """Run code quality checks."""
    print("🔍 Running code quality checks...")
    
    # Run black formatting check
    if not run_command("python -m black --check vscode_copilot_controller/"):
        print("❌ Code formatting check failed! Run: black vscode_copilot_controller/")
        return False
    
    # Run isort import sorting check  
    if not run_command("python -m isort --check-only vscode_copilot_controller/"):
        print("❌ Import sorting check failed! Run: isort vscode_copilot_controller/")
        return False
        
    # Run flake8 linting
    if not run_command("python -m flake8 vscode_copilot_controller/"):
        print("❌ Linting failed!")
        return False
        
    print("✅ Code quality checks passed")
    return True


def build_package():
    """Build the package."""
    print("📦 Building package...")
    
    if not run_command("python -m build"):
        print("❌ Package build failed!")
        return False
        
    print("✅ Package built successfully")
    return True


def upload_to_pypi(test: bool = False):
    """Upload package to PyPI."""
    repository = "--repository testpypi" if test else ""
    
    print(f"🚀 Uploading to {'Test ' if test else ''}PyPI...")
    
    if not run_command(f"python -m twine upload {repository} dist/*"):
        print("❌ Upload failed!")
        return False
        
    print("✅ Package uploaded successfully")
    return True


def main():
    """Main build process."""
    print("🔧 VSCode Copilot Controller - Build Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ pyproject.toml not found! Run this script from the project root.")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        action = sys.argv[1]
        
        if action == "clean":
            clean_build()
            return
        elif action == "test":
            if not run_tests():
                sys.exit(1)
            return
        elif action == "lint":
            if not run_linting():
                sys.exit(1)
            return
        elif action == "build":
            clean_build()
            if not build_package():
                sys.exit(1)
            return
        elif action == "upload-test":
            if not upload_to_pypi(test=True):
                sys.exit(1)
            return
        elif action == "upload":
            if not upload_to_pypi(test=False):
                sys.exit(1)
            return
        elif action == "full":
            pass  # Fall through to full build process
        else:
            print("Usage: python build.py [clean|test|lint|build|upload-test|upload|full]")
            sys.exit(1)
    
    # Full build process
    print("🚀 Starting full build process...")
    
    # Step 1: Clean
    clean_build()
    
    # Step 2: Run tests
    if not run_tests():
        print("❌ Build failed at testing stage")
        sys.exit(1)
    
    # Step 3: Run linting
    if not run_linting():
        print("❌ Build failed at linting stage")
        sys.exit(1)
    
    # Step 4: Build package
    if not build_package():
        print("❌ Build failed at packaging stage")
        sys.exit(1)
    
    print("🎉 Build completed successfully!")
    print("\nNext steps:")
    print("  • Test upload: python build.py upload-test")
    print("  • Production upload: python build.py upload")


if __name__ == "__main__":
    main()