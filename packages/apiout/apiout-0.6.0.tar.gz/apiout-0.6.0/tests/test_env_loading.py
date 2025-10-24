"""Tests for environment file loading functionality."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import typer

from apiout.cli import (
    _get_config_dir,
    _load_config_files,
    _resolve_config_path,
    _resolve_serializer_path,
)


class TestGetConfigDir:
    """Tests for _get_config_dir function."""

    def test_default_config_dir(self):
        """Test default config directory returns a valid path."""
        # Don't clear environment on Windows - need HOME/USERPROFILE
        if os.name == "nt":
            # On Windows, ensure LOCALAPPDATA is available or test will use fallback
            config_dir = _get_config_dir()
            # Just verify it's a Path and contains "apiout"
            assert isinstance(config_dir, Path)
            assert config_dir.name == "apiout"
        else:
            # On Unix, can safely clear environment
            with patch.dict(os.environ, {}, clear=True):
                config_dir = _get_config_dir()
                assert config_dir == Path.home() / ".config" / "apiout"

    def test_xdg_config_home_override(self):
        """Test XDG_CONFIG_HOME environment variable override."""
        custom_config = "/custom/config"
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": custom_config}):
            config_dir = _get_config_dir()
            assert config_dir == Path(custom_config) / "apiout"

    def test_xdg_config_home_with_tilde(self):
        """Test XDG_CONFIG_HOME with tilde expansion."""
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "~/custom_config"}):
            config_dir = _get_config_dir()
            expected = Path.home() / "custom_config" / "apiout"
            assert config_dir == expected

    def test_windows_localappdata(self):
        """Test Windows LOCALAPPDATA usage when available."""
        if os.name == "nt":
            # Test only on actual Windows
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                # Clear XDG_CONFIG_HOME to ensure LOCALAPPDATA is used
                env = {k: v for k, v in os.environ.items() if k != "XDG_CONFIG_HOME"}
                with patch.dict(os.environ, env, clear=True):
                    config_dir = _get_config_dir()
                    assert config_dir == Path(local_app_data) / "apiout"
        else:
            pytest.skip("Windows-specific test")


class TestResolveConfigPath:
    """Tests for _resolve_config_path function."""

    def test_resolve_config_name(self):
        """Test resolving a config name to config directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = Path(tmpdir)
            env_file = env_dir / "test_env.toml"
            env_file.write_text("""
[clients.test]
module = "test_module"

[[apis]]
name = "test_api"
""")

            with patch("apiout.cli._get_config_dir", return_value=env_dir):
                result = _resolve_config_path("test_env")
                assert result == env_file
                assert result.exists()

    def test_resolve_config_path_with_extension(self):
        """Test resolving a config path with .toml extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            config_file = tmpdir / "test.toml"
            config_file.write_text("""
[clients.test]
module = "test_module"

[[apis]]
name = "test_api"
""")

            result = _resolve_config_path(str(config_file))
            assert result == config_file.resolve()
            assert result.exists()

    def test_resolve_config_path_with_separators(self):
        """Test resolving a config path with separators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            config_file = tmpdir / "subdir" / "test.toml"
            config_file.parent.mkdir()
            config_file.write_text("""
[clients.test]
module = "test_module"

[[apis]]
name = "test_api"
""")

            result = _resolve_config_path(str(config_file))
            assert result == config_file.resolve()
            assert result.exists()

    def test_resolve_missing_config_name(self):
        """Test resolving a non-existent config name raises typer.Exit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_dir = Path(tmpdir)

            with patch("apiout.cli._get_config_dir", return_value=env_dir):
                with pytest.raises(typer.Exit):
                    _resolve_config_path("nonexistent")

    def test_resolve_missing_config_path(self):
        """Test resolving a non-existent config path raises typer.Exit."""
        with pytest.raises(typer.Exit):
            _resolve_config_path("/nonexistent/config.toml")


class TestLoadConfigFilesWithEnv:
    """Tests for _load_config_files with environment files."""

    def test_load_single_config(self):
        """Test loading a single config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.toml"
            config_file.write_text("""
[clients.client1]
module = "module1"

[[apis]]
name = "api1"
url = "http://example.com"
""")

            result = _load_config_files([config_file])

            assert "clients" in result
            assert "client1" in result["clients"]
            assert result["apis"][0]["name"] == "api1"

    def test_load_multiple_configs(self):
        """Test loading multiple config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            config1 = tmpdir / "config1.toml"
            config1.write_text("""
[clients.client1]
module = "module1"

[[apis]]
name = "api1"
url = "http://example1.com"
""")

            config2 = tmpdir / "config2.toml"
            config2.write_text("""
[clients.client2]
module = "module2"

[[apis]]
name = "api2"
url = "http://example2.com"
""")

            result = _load_config_files([config1, config2])

            assert "client1" in result["clients"]
            assert "client2" in result["clients"]
            assert len(result["apis"]) == 2
            assert result["apis"][0]["name"] == "api1"
            assert result["apis"][1]["name"] == "api2"

    def test_config_with_scoped_serializers(self):
        """Test config files with client-scoped serializers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.toml"
            config_file.write_text("""
[clients.test_client]
module = "test"

[serializers.test_client.ser1]
[serializers.test_client.ser1.fields]
field1 = "mapped1"

[[apis]]
name = "test_api"
client = "test_client"
url = "http://test.com"
serializer = "ser1"
""")

            result = _load_config_files([config_file])

            assert "test_client.ser1" in result["serializers"]
            assert (
                result["serializers"]["test_client.ser1"]["fields"]["field1"]
                == "mapped1"
            )

    def test_config_with_global_serializers(self):
        """Test config files with global (non-scoped) serializers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.toml"
            config_file.write_text("""
[clients.test_client]
module = "test"

[serializers.global_ser]
[serializers.global_ser.fields]
field1 = "mapped1"

[[apis]]
name = "test_api"
client = "test_client"
url = "http://test.com"
serializer = "global_ser"
""")

            result = _load_config_files([config_file])

            assert "global_ser" in result["serializers"]
            assert result["serializers"]["global_ser"]["fields"]["field1"] == "mapped1"

    def test_missing_config_file(self):
        """Test loading non-existent config file raises typer.Exit."""
        with pytest.raises(typer.Exit):
            _load_config_files([Path("/nonexistent/config.toml")])


class TestResolveSerializerPath:
    """Tests for _resolve_serializer_path function."""

    def test_resolve_serializer_name(self):
        """Test resolving a serializer name to config directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            serializer_file = config_dir / "test_serializer.toml"
            serializer_file.write_text("""
[serializers.test_serializer]
test_field = "test_value"
""")

            with patch("apiout.cli._get_config_dir", return_value=config_dir):
                result = _resolve_serializer_path("test_serializer")
                assert result == serializer_file
                assert result.exists()

    def test_resolve_serializer_path_with_extension(self):
        """Test resolving a serializer path with .toml extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            serializer_file = tmpdir / "test.toml"
            serializer_file.write_text("""
[serializers.test_serializer]
test_field = "test_value"
""")

            result = _resolve_serializer_path(str(serializer_file))
            assert result == serializer_file.resolve()
            assert result.exists()

    def test_resolve_serializer_path_with_separators(self):
        """Test resolving a serializer path with separators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            serializer_file = tmpdir / "subdir" / "test.toml"
            serializer_file.parent.mkdir()
            serializer_file.write_text("""
[serializers.test_serializer]
test_field = "test_value"
""")

            result = _resolve_serializer_path(str(serializer_file))
            assert result == serializer_file.resolve()
            assert result.exists()

    def test_resolve_missing_serializer_name(self):
        """Test resolving a non-existent serializer name raises typer.Exit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            with patch("apiout.cli._get_config_dir", return_value=config_dir):
                with pytest.raises(typer.Exit):
                    _resolve_serializer_path("nonexistent")

    def test_resolve_missing_serializer_path(self):
        """Test resolving a non-existent serializer path raises typer.Exit."""
        with pytest.raises(typer.Exit):
            _resolve_serializer_path("/nonexistent/serializer.toml")
