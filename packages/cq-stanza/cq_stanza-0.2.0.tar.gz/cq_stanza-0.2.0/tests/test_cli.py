"""Tests for Stanza CLI (stanza/cli.py)."""

import json
import re
from pathlib import Path

from click.testing import CliRunner

from stanza.cli import cli
from stanza.context import StanzaSession


class TestCLI:
    """Test suite for Stanza CLI commands."""

    def test_cli_help(self):
        """Test that CLI help command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Stanza" in result.output
        assert "Build tune up sequences" in result.output
        assert "init" in result.output
        assert "status" in result.output

    def test_cli_version(self):
        """Test that CLI version command works."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "(Stanza)" in result.output
        # Check for valid semantic version format (e.g., 0.1.0, 1.2.3)
        assert re.search(r"\d+\.\d+\.\d+", result.output) is not None


class TestInitCommand:
    """Test suite for 'stanza init' command."""

    def test_init_creates_session_with_default_name(self):
        """Test that init command creates session directory with default name."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init"])

            assert result.exit_code == 0
            assert "✓ Created session directory" in result.output
            assert "_untitled" in result.output
            assert "Session initialized successfully" in result.output

            sessions = list(Path.cwd().glob("*_untitled"))
            assert len(sessions) == 1
            assert sessions[0].exists()
            assert (sessions[0] / ".stanza" / "config.json").exists()

            notebooks = list(sessions[0].glob("*_untitled_notebook.ipynb"))
            assert len(notebooks) == 1
            assert notebooks[0].exists()

    def test_init_creates_session_with_custom_name(self):
        """Test that init command accepts custom name parameter."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--name", "my_experiment"])

            assert result.exit_code == 0
            assert "_my_experiment" in result.output

            sessions = list(Path.cwd().glob("*_my_experiment"))
            assert len(sessions) == 1
            assert sessions[0].exists()

            notebooks = list(sessions[0].glob("*_my_experiment.ipynb"))
            assert len(notebooks) == 1
            assert notebooks[0].exists()

    def test_init_creates_session_with_custom_path(self):
        """Test that init command accepts custom path parameter."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            custom_path = Path.cwd() / "custom_location"
            custom_path.mkdir()

            result = runner.invoke(cli, ["init", "--path", str(custom_path)])

            assert result.exit_code == 0
            assert "✓ Created session directory" in result.output

            sessions = list(custom_path.glob("*_untitled"))
            assert len(sessions) == 1

    def test_init_sets_active_session(self):
        """Test that init command sets the active session."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init"])

            assert result.exit_code == 0

            active_session = StanzaSession.get_active_session()
            assert active_session is not None
            assert active_session.exists()

    def test_init_fails_gracefully_on_error(self):
        """Test that init command handles errors gracefully."""
        runner = CliRunner()

        result = runner.invoke(cli, ["init", "--path", "/nonexistent/path/xyz"])

        assert result.exit_code != 0
        assert "Error" in result.output or "does not exist" in result.output

    def test_init_with_different_names_creates_multiple_directories(self):
        """Test that init with different names creates multiple directories."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result1 = runner.invoke(cli, ["init", "--name", "exp1"])
            assert result1.exit_code == 0

            result2 = runner.invoke(cli, ["init", "--name", "exp2"])
            assert result2.exit_code == 0

            exp1_sessions = list(Path.cwd().glob("*_exp1"))
            exp2_sessions = list(Path.cwd().glob("*_exp2"))
            assert len(exp1_sessions) == 1
            assert len(exp2_sessions) == 1

    def test_init_creates_valid_jupyter_notebook(self):
        """Test that init creates a valid Jupyter notebook with proper structure."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "--name", "test_notebook"])
            assert result.exit_code == 0

            sessions = list(Path.cwd().glob("*_test_notebook"))
            assert len(sessions) == 1

            notebooks = list(sessions[0].glob("*_test_notebook.ipynb"))
            assert len(notebooks) == 1

            with open(notebooks[0]) as f:
                notebook_data = json.load(f)

            assert "cells" in notebook_data
            assert "metadata" in notebook_data
            assert "nbformat" in notebook_data
            assert notebook_data["nbformat"] == 4

            cells = notebook_data["cells"]
            assert len(cells) >= 2

            assert cells[0]["cell_type"] == "markdown"
            assert "Test Notebook" in "".join(cells[0]["source"])

            assert cells[1]["cell_type"] == "code"
            source = "".join(cells[1]["source"])
            assert "from stanza.routines import RoutineRunner" in source
            assert "from stanza.utils import load_device_config" in source


class TestStatusCommand:
    """Test suite for 'stanza status' command."""

    def test_status_shows_no_session_when_not_initialized(self):
        """Test that status command shows helpful message when no session exists."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "No active session" in result.output
            assert "stanza init" in result.output

    def test_status_shows_active_session_info(self):
        """Test that status command displays active session information."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            init_result = runner.invoke(cli, ["init", "--name", "test"])
            assert init_result.exit_code == 0

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Active session:" in result.output
            assert "_test" in result.output
            assert "Location:" in result.output
            assert "Created:" in result.output

    def test_status_shows_creation_timestamp(self):
        """Test that status command displays creation timestamp."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            init_result = runner.invoke(cli, ["init"])
            assert init_result.exit_code == 0

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Created:" in result.output
            assert "202" in result.output

    def test_status_handles_deleted_session_directory(self):
        """Test that status handles case where session directory was deleted."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            init_result = runner.invoke(cli, ["init"])
            assert init_result.exit_code == 0

            active_session = StanzaSession.get_active_session()
            import shutil

            shutil.rmtree(active_session)

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "No active session" in result.output

    def test_status_handles_missing_metadata(self):
        """Test that status handles case where metadata file is missing."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            init_result = runner.invoke(cli, ["init"])
            assert init_result.exit_code == 0

            active_session = StanzaSession.get_active_session()
            metadata_file = active_session / ".stanza" / "config.json"
            metadata_file.unlink()

            result = runner.invoke(cli, ["status"])

            assert result.exit_code == 0
            assert "Active session:" in result.output
            assert "Location:" in result.output
            assert (
                "Created:" not in result.output or result.output.count("Created:") == 0
            )


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    def test_init_then_status_workflow(self):
        """Test complete workflow of init followed by status."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            init_result = runner.invoke(cli, ["init", "--name", "workflow_test"])
            assert init_result.exit_code == 0
            assert "_workflow_test" in init_result.output

            status_result = runner.invoke(cli, ["status"])
            assert status_result.exit_code == 0
            assert "_workflow_test" in status_result.output
            assert "Active session:" in status_result.output

    def test_multiple_init_commands_update_active_session(self):
        """Test that running init multiple times updates the active session."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            result1 = runner.invoke(cli, ["init", "--name", "first"])
            assert result1.exit_code == 0

            result2 = runner.invoke(cli, ["init", "--name", "second"])
            assert result2.exit_code == 0

            status_result = runner.invoke(cli, ["status"])
            assert status_result.exit_code == 0
            assert "_second" in status_result.output
            assert "_first" not in status_result.output
