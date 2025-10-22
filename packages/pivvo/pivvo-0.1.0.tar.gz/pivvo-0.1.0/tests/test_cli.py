import pytest
from pathlib import Path
import tempfile
import shutil
from pivvo.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_main_callback():
    """Test that the main callback displays the banner."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "____" in result.output


def test_init_command(tmp_path, monkeypatch):
    """Test the init command creates a project structure."""
    project_name = "test_project"
    project_path = tmp_path / project_name

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 0
    assert f"{project_name} initialized successfully" in result.output

    # Check that project structure was created
    assert project_path.exists()
    assert (project_path / "__init__.py").exists()
    assert (project_path / "README.md").exists()
    assert (project_path / ".gitignore").exists()
    assert (project_path / "venv").exists()


def test_init_existing_project(tmp_path, monkeypatch):
    """Test that init fails when project already exists."""
    project_name = "existing_project"
    project_path = tmp_path / project_name
    project_path.mkdir()

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", project_name])
    assert result.exit_code == 1
    assert f"{project_name} already exists" in result.output


def test_run_command_no_venv(tmp_path, monkeypatch):
    """Test that run command fails without virtual environment."""
    # Create a dummy script
    script_path = tmp_path / "test_script.py"
    script_path.write_text("print('Hello, World!')")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "test_script.py"])
    assert result.exit_code == 1
    assert "No virtual environment found" in result.output


def test_list_command_no_venv(tmp_path, monkeypatch):
    """Test that list command fails without virtual environment."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 1
    assert "No virtual environment found" in result.output


def test_freeze_command_no_venv(tmp_path, monkeypatch):
    """Test that freeze command fails without virtual environment."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["freeze"])
    assert result.exit_code == 1
    assert "No virtual environment found" in result.output


def test_upgrade_command_no_venv(tmp_path, monkeypatch):
    """Test that upgrade command fails without virtual environment."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["upgrade"])
    assert result.exit_code == 1
    assert "No virtual environment found" in result.output


def test_remove_command_no_venv(tmp_path, monkeypatch):
    """Test that remove command fails without virtual environment."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["remove", "some-package"])
    assert result.exit_code == 1
    assert "No virtual environment found" in result.output


def test_install_deps_no_venv(tmp_path, monkeypatch):
    """Test that install-deps command fails without virtual environment."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["install-deps", "pytest"])
    assert result.exit_code == 1
    assert "No virtual environment found" in result.output