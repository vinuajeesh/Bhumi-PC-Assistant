import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Add repo root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.system_ctrl import SystemTools
from config import Config

# Mocking Config to simulate environments
@pytest.fixture
def mock_windows_config(monkeypatch):
    monkeypatch.setattr(Config, 'is_windows', lambda: True)
    monkeypatch.setattr(Config, 'is_macos', lambda: False)

@pytest.fixture
def mock_macos_config(monkeypatch):
    monkeypatch.setattr(Config, 'is_windows', lambda: False)
    monkeypatch.setattr(Config, 'is_macos', lambda: True)

def test_check_health():
    tools = SystemTools()
    status = tools.check_health()
    assert "CPU Load" in status
    assert "Memory Used" in status

@patch("subprocess.run")
def test_manage_packages_windows(mock_run, mock_windows_config):
    tools = SystemTools()
    # Force the instance to update its flags from the mocked config if it cached them
    tools.is_windows = True
    tools.is_macos = False

    # Mock return
    mock_run.return_value.stdout = "Success"

    tools.manage_packages("install", "firefox")

    # Verify winget was called
    args, _ = mock_run.call_args
    assert "winget install firefox" in args[0]

@patch("subprocess.run")
def test_manage_packages_macos(mock_run, mock_macos_config):
    tools = SystemTools()
    tools.is_windows = False
    tools.is_macos = True

    mock_run.return_value.stdout = "Success"

    tools.manage_packages("install", "wget")

    args, _ = mock_run.call_args
    assert "brew install wget" in args[0]

@patch("subprocess.Popen")
def test_compile_rom_script_not_found(mock_popen):
    tools = SystemTools()
    result = tools.compile_rom("non_existent_script.sh")
    assert "not found" in result

def test_compile_rom_found(tmpdir):
    # Create a dummy script
    p = tmpdir.mkdir("build_scripts").join("test_build.sh")
    p.write("#!/bin/bash\necho build")

    # Patch Config.BUILD_SCRIPTS_DIR
    with patch("config.Config.BUILD_SCRIPTS_DIR", str(p.dirname)):
        with patch("subprocess.Popen") as mock_popen:
            tools = SystemTools()
            result = tools.compile_rom("test_build.sh")

            assert "Started build script" in result
            mock_popen.assert_called_once()
