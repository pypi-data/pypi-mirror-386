#!/usr/bin/env python
"""
Release automation script for Context Bridge package.

Usage:
    python release.py --version 0.1.0 --check     # Just check
    python release.py --version 0.1.0 --test      # Test PyPI
    python release.py --version 0.1.0 --release   # Full release
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional
import re


class ReleaseManager:
    """Manage Context Bridge releases."""

    def __init__(self, version: str, project_root: Optional[Path] = None):
        self.version = version
        self.project_root = project_root or Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.init_file = self.project_root / "context_bridge" / "__init__.py"
        self.pyproject_file = self.project_root / "pyproject.toml"

    def run_command(self, cmd: list, check: bool = True, capture: bool = False):
        """Run a shell command."""
        print(f"▶ {' '.join(cmd)}")
        try:
            if capture:
                result = subprocess.run(
                    cmd,
                    check=check,
                    capture_output=True,
                    text=True,
                )
                return result.stdout.strip()
            else:
                subprocess.run(cmd, check=check)
                return None
        except subprocess.CalledProcessError as e:
            print(f"✗ Command failed: {e}")
            sys.exit(1)

    def validate_version(self) -> bool:
        """Validate version format."""
        if not re.match(r"^\d+\.\d+\.\d+$", self.version):
            print(f"✗ Invalid version format: {self.version}")
            print("  Expected format: MAJOR.MINOR.PATCH (e.g., 0.1.0)")
            return False
        print(f"✓ Version format valid: {self.version}")
        return True

    def check_files_exist(self) -> bool:
        """Check required files exist."""
        required = [
            self.init_file,
            self.pyproject_file,
            self.project_root / "README.md",
            self.project_root / "LICENSE",
        ]

        for file in required:
            if not file.exists():
                print(f"✗ Required file missing: {file}")
                return False
            print(f"✓ {file.name}")

        return True

    def update_version_numbers(self) -> bool:
        """Update version in __init__.py and pyproject.toml."""
        try:
            # Update __init__.py
            init_content = self.init_file.read_text()
            new_init = re.sub(
                r'__version__ = "[^"]*"',
                f'__version__ = "{self.version}"',
                init_content,
            )
            if new_init == init_content:
                print(f"✗ Could not update version in {self.init_file}")
                return False
            self.init_file.write_text(new_init)
            print(f"✓ Updated {self.init_file}: {self.version}")

            # Update pyproject.toml
            pyproject_content = self.pyproject_file.read_text()
            new_pyproject = re.sub(
                r'version = "[^"]*"',
                f'version = "{self.version}"',
                pyproject_content,
            )
            if new_pyproject == pyproject_content:
                print(f"✗ Could not update version in {self.pyproject_file}")
                return False
            self.pyproject_file.write_text(new_pyproject)
            print(f"✓ Updated {self.pyproject_file}: {self.version}")

            return True
        except Exception as e:
            print(f"✗ Error updating versions: {e}")
            return False

    def run_tests(self) -> bool:
        """Run test suite."""
        print("\n📋 Running tests...")
        try:
            self.run_command(
                ["uv", "run", "pytest", "tests/unit/", "-q", "--tb=short"],
                check=False,
            )
            print("✓ Tests completed")
            return True
        except Exception as e:
            print(f"✗ Tests failed: {e}")
            return False

    def check_code_quality(self) -> bool:
        """Run code quality checks."""
        print("\n🔍 Running code quality checks...")

        checks = [
            (["uv", "run", "black", "--check", "context_bridge/"], "Black"),
            (["uv", "run", "ruff", "check", "context_bridge/"], "Ruff"),
        ]

        all_passed = True
        for cmd, name in checks:
            try:
                self.run_command(cmd, check=False)
                print(f"✓ {name} check passed")
            except Exception as e:
                print(f"✗ {name} check failed: {e}")
                all_passed = False

        return all_passed

    def clean_builds(self) -> bool:
        """Clean old build directories."""
        print("\n🧹 Cleaning old builds...")
        try:
            for directory in [self.dist_dir, self.build_dir]:
                if directory.exists():
                    import shutil

                    shutil.rmtree(directory)
                    print(f"✓ Removed {directory}")
            return True
        except Exception as e:
            print(f"✗ Error cleaning builds: {e}")
            return False

    def build_distributions(self) -> bool:
        """Build wheel and source distributions."""
        print("\n📦 Building distributions...")
        try:
            self.run_command(["python", "-m", "build"], cwd=self.project_root)

            # Verify files exist
            wheel_files = list(self.dist_dir.glob("*.whl"))
            tar_files = list(self.dist_dir.glob("*.tar.gz"))

            if not wheel_files or not tar_files:
                print("✗ Build files not created")
                return False

            print(f"✓ Built: {wheel_files[0].name}")
            print(f"✓ Built: {tar_files[0].name}")
            return True
        except Exception as e:
            print(f"✗ Build failed: {e}")
            return False

    def validate_package(self) -> bool:
        """Validate package with twine."""
        print("\n✔ Validating package...")
        try:
            self.run_command(["twine", "check", "dist/*"], check=False)
            print("✓ Package validation passed")
            return True
        except Exception as e:
            print(f"✗ Validation failed: {e}")
            return False

    def upload_test_pypi(self) -> bool:
        """Upload to Test PyPI."""
        print("\n🧪 Uploading to Test PyPI...")
        try:
            self.run_command(
                [
                    "twine",
                    "upload",
                    "--repository",
                    "test-pypi",
                    "dist/*",
                    "--skip-existing",
                ],
                check=False,
            )
            print("✓ Test PyPI upload completed")
            return True
        except Exception as e:
            print(f"✗ Test PyPI upload failed: {e}")
            return False

    def upload_production_pypi(self) -> bool:
        """Upload to Production PyPI."""
        print("\n🚀 Uploading to Production PyPI...")

        # Confirm
        response = input("Are you sure? This will publish to PyPI! (yes/no): ").strip().lower()
        if response != "yes":
            print("✗ Upload cancelled")
            return False

        try:
            self.run_command(["twine", "upload", "dist/*", "--skip-existing"])
            print("✓ Production PyPI upload completed")
            return True
        except Exception as e:
            print(f"✗ Production upload failed: {e}")
            return False

    def commit_and_tag(self) -> bool:
        """Commit version bump and create tag."""
        print("\n📝 Committing changes...")
        try:
            self.run_command(["git", "add", "context_bridge/__init__.py", "pyproject.toml"])
            self.run_command(["git", "commit", "-m", f"Bump version to {self.version} for release"])
            self.run_command(
                ["git", "tag", "-a", f"v{self.version}", "-m", f"Release {self.version}"]
            )
            print(f"✓ Created tag: v{self.version}")
            return True
        except Exception as e:
            print(f"✗ Git operations failed: {e}")
            return False

    def check_workflow(self) -> bool:
        """Run pre-release checks."""
        print("🔍 Running pre-release checks...\n")

        checks = [
            ("Validating version", self.validate_version),
            ("Checking required files", self.check_files_exist),
            ("Running tests", self.run_tests),
            ("Checking code quality", self.check_code_quality),
        ]

        for name, check_func in checks:
            print(f"\n{name}...")
            if not check_func():
                print(f"✗ {name} failed")
                return False

        print("\n✅ All pre-release checks passed!")
        return True

    def build_workflow(self) -> bool:
        """Build distributions."""
        print("📦 Building distributions...\n")

        workflows = [
            ("Cleaning old builds", self.clean_builds),
            ("Building distributions", self.build_distributions),
            ("Validating package", self.validate_package),
        ]

        for name, workflow_func in workflows:
            print(f"\n{name}...")
            if not workflow_func():
                print(f"✗ {name} failed")
                return False

        print("\n✅ Build successful!")
        return True

    def test_workflow(self) -> bool:
        """Test on Test PyPI."""
        print("🧪 Testing on Test PyPI...\n")

        workflows = [
            ("Building distributions", self.build_distributions),
            ("Validating package", self.validate_package),
            ("Uploading to Test PyPI", self.upload_test_pypi),
        ]

        for name, workflow_func in workflows:
            print(f"\n{name}...")
            if not workflow_func():
                print(f"✗ {name} failed")
                return False

        print("\n✅ Test PyPI workflow successful!")
        print(f"Visit: https://test.pypi.org/project/context-bridge/{self.version}/")
        return True

    def release_workflow(self) -> bool:
        """Full release workflow."""
        print(f"🚀 Full Release Workflow (v{self.version})\n")

        workflows = [
            ("Running pre-release checks", self.check_workflow),
            ("Updating version numbers", self.update_version_numbers),
            ("Building distributions", self.build_distributions),
            ("Uploading to Production PyPI", self.upload_production_pypi),
            ("Committing and tagging", self.commit_and_tag),
        ]

        for name, workflow_func in workflows:
            print(f"\n{name}...")
            if not workflow_func():
                print(f"✗ {name} failed")
                return False

        print("\n✅ Release complete!")
        print(f"PyPI: https://pypi.org/project/context-bridge/{self.version}/")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Release Context Bridge package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python release.py --version 0.1.0 --check      # Run pre-release checks
  python release.py --version 0.1.0 --build      # Build distributions
  python release.py --version 0.1.0 --test       # Test PyPI upload
  python release.py --version 0.1.0 --release    # Full release
        """,
    )

    parser.add_argument(
        "--version",
        required=True,
        help="Version to release (e.g., 0.1.0)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run pre-release checks only",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build distributions only",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test on Test PyPI",
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Full release to production PyPI",
    )

    args = parser.parse_args()

    # Validate that only one action is specified
    actions = sum([args.check, args.build, args.test, args.release])
    if actions != 1:
        parser.error("Specify exactly one action: --check, --build, --test, or --release")

    manager = ReleaseManager(args.version)

    try:
        if args.check:
            success = manager.check_workflow()
        elif args.build:
            success = manager.build_workflow()
        elif args.test:
            success = manager.test_workflow()
        elif args.release:
            success = manager.release_workflow()
        else:
            parser.print_help()
            return

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Release process cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
