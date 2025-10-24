"""Tests for CLI functionality."""

import subprocess
import sys


def test_help_command():
    """Test that --help command works without errors."""
    result = subprocess.run(
        [sys.executable, "-m", "msconvert_cli.cli", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "ProteoWizard Docker wrapper" in result.stdout
    assert "--output-dir" in result.stdout
    assert "--workers" in result.stdout
    assert "--sage" in result.stdout
    assert "--casanovo" in result.stdout


def test_help_short_flag():
    """Test that -h works the same as --help."""
    result = subprocess.run(
        [sys.executable, "-m", "msconvert_cli.cli", "-h"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "ProteoWizard Docker wrapper" in result.stdout


def test_version_in_help():
    """Test that help shows all preset options."""
    result = subprocess.run(
        [sys.executable, "-m", "msconvert_cli.cli", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    # Check all presets are listed
    assert "--blitzff" in result.stdout
    assert "--biosaur" in result.stdout
    assert "--casanovo_mgf" in result.stdout


def test_missing_required_args():
    """Test that missing required arguments shows proper error."""
    result = subprocess.run(
        [sys.executable, "-m", "msconvert_cli.cli"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "required" in result.stderr.lower() or "error" in result.stderr.lower()
