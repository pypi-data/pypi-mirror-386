"""Tests for configuration management."""

import sys
from unittest.mock import patch

import pytest

from miniflux_tui.config import Config, create_default_config, get_config_dir, get_config_file_path, load_config, validate_config


class TestValidateConfig:
    """Test configuration validation."""

    def test_valid_config(self, valid_config_dict):
        """Test validation of valid configuration."""
        is_valid, msg = validate_config(valid_config_dict)
        assert is_valid
        assert msg == "Configuration valid"

    def test_missing_server_url(self, valid_config_dict):
        """Test validation fails when server_url is missing."""
        del valid_config_dict["server_url"]
        is_valid, msg = validate_config(valid_config_dict)
        assert not is_valid
        assert "server_url" in msg

    def test_missing_api_key(self, valid_config_dict):
        """Test validation fails when api_key is missing."""
        del valid_config_dict["api_key"]
        is_valid, msg = validate_config(valid_config_dict)
        assert not is_valid
        assert "api_key" in msg

    def test_empty_server_url(self, valid_config_dict):
        """Test validation fails with empty server_url."""
        valid_config_dict["server_url"] = ""
        is_valid, msg = validate_config(valid_config_dict)
        assert not is_valid
        assert "non-empty" in msg.lower() or "empty" in msg.lower()

    def test_invalid_server_url_protocol(self, valid_config_dict):
        """Test validation fails with non-http(s) server_url."""
        valid_config_dict["server_url"] = "ftp://example.com"
        is_valid, msg = validate_config(valid_config_dict)
        assert not is_valid
        assert "http" in msg.lower()

    def test_server_url_with_http(self, valid_config_dict):
        """Test validation passes with http:// server_url."""
        valid_config_dict["server_url"] = "http://miniflux.local"
        is_valid, _ = validate_config(valid_config_dict)
        assert is_valid

    def test_empty_api_key(self, valid_config_dict):
        """Test validation fails with empty api_key."""
        valid_config_dict["api_key"] = ""
        is_valid, msg = validate_config(valid_config_dict)
        assert not is_valid
        assert "non-empty" in msg.lower() or "empty" in msg.lower()

    def test_short_api_key(self, valid_config_dict):
        """Test validation fails with api_key < 10 characters."""
        valid_config_dict["api_key"] = "short"
        is_valid, msg = validate_config(valid_config_dict)
        assert not is_valid
        assert "short" in msg.lower()

    def test_api_key_with_spaces(self, valid_config_dict):
        """Test validation fails when api_key is only whitespace."""
        valid_config_dict["api_key"] = "   "
        is_valid, _ = validate_config(valid_config_dict)
        assert not is_valid

    def test_invalid_sort_mode(self, valid_config_dict):
        """Test validation fails with invalid default_sort."""
        valid_config_dict["sorting"]["default_sort"] = "invalid"
        is_valid, msg = validate_config(valid_config_dict)
        assert not is_valid
        assert "default_sort" in msg

    def test_valid_sort_modes(self, valid_config_dict):
        """Test validation passes with all valid sort modes."""
        for sort_mode in ["date", "feed", "status"]:
            valid_config_dict["sorting"]["default_sort"] = sort_mode
            is_valid, _ = validate_config(valid_config_dict)
            assert is_valid, f"Failed for sort mode: {sort_mode}"

    def test_config_without_optional_fields(self):
        """Test validation of minimal valid config."""
        config = {
            "server_url": "https://miniflux.example.com",
            "api_key": "1234567890",
        }
        is_valid, _ = validate_config(config)
        assert is_valid


class TestConfigClass:
    """Test Config class initialization and methods."""

    def test_config_initialization(self):
        """Test Config class initialization with all parameters."""
        config = Config(
            server_url="https://miniflux.example.com",
            api_key="test-api-key-123456",
            allow_invalid_certs=True,
            unread_color="blue",
            read_color="white",
            default_sort="feed",
            default_group_by_feed=True,
            group_collapsed=True,
        )

        assert config.server_url == "https://miniflux.example.com"
        assert config.api_key == "test-api-key-123456"
        assert config.allow_invalid_certs is True
        assert config.unread_color == "blue"
        assert config.read_color == "white"
        assert config.default_sort == "feed"
        assert config.default_group_by_feed is True
        assert config.group_collapsed is True

    def test_config_initialization_defaults(self):
        """Test Config class initialization with default parameters."""
        config = Config(
            server_url="https://miniflux.example.com",
            api_key="test-api-key-123456",
        )

        assert config.server_url == "https://miniflux.example.com"
        assert config.api_key == "test-api-key-123456"
        assert config.allow_invalid_certs is False
        assert config.unread_color == "cyan"
        assert config.read_color == "gray"
        assert config.default_sort == "date"
        assert config.default_group_by_feed is False
        assert config.group_collapsed is False

    def test_config_from_file_valid(self, tmp_path):
        """Test Config.from_file() with valid config file."""
        config_file = tmp_path / "config.toml"
        config_content = """
server_url = "https://miniflux.example.com"
api_key = "test-api-key-1234567890"
allow_invalid_certs = true

[theme]
unread_color = "green"
read_color = "yellow"

[sorting]
default_sort = "feed"
default_group_by_feed = true
group_collapsed = false
"""
        config_file.write_text(config_content)

        config = Config.from_file(config_file)

        assert config.server_url == "https://miniflux.example.com"
        assert config.api_key == "test-api-key-1234567890"
        assert config.allow_invalid_certs is True
        assert config.unread_color == "green"
        assert config.read_color == "yellow"
        assert config.default_sort == "feed"
        assert config.default_group_by_feed is True
        assert config.group_collapsed is False

    def test_config_from_file_minimal(self, tmp_path):
        """Test Config.from_file() with minimal config file."""
        config_file = tmp_path / "config.toml"
        config_content = """
server_url = "https://miniflux.example.com"
api_key = "test-api-key-1234567890"
"""
        config_file.write_text(config_content)

        config = Config.from_file(config_file)

        assert config.server_url == "https://miniflux.example.com"
        assert config.api_key == "test-api-key-1234567890"
        assert config.allow_invalid_certs is False
        assert config.unread_color == "cyan"
        assert config.read_color == "gray"

    def test_config_from_file_not_found(self, tmp_path):
        """Test Config.from_file() raises FileNotFoundError when file doesn't exist."""
        config_file = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            Config.from_file(config_file)

    def test_config_from_file_invalid_content(self, tmp_path):
        """Test Config.from_file() raises ValueError for invalid config."""
        config_file = tmp_path / "config.toml"
        config_content = """
server_url = "https://miniflux.example.com"
api_key = "short"
"""
        config_file.write_text(config_content)

        with pytest.raises(ValueError, match="Invalid configuration"):
            Config.from_file(config_file)

    def test_config_from_file_missing_required_field(self, tmp_path):
        """Test Config.from_file() raises ValueError when required field missing."""
        config_file = tmp_path / "config.toml"
        config_content = """
server_url = "https://miniflux.example.com"
"""
        config_file.write_text(config_content)

        with pytest.raises(ValueError, match="Invalid configuration"):
            Config.from_file(config_file)


class TestConfigDirectory:
    """Test configuration directory path functions."""

    def test_get_config_dir_darwin(self):
        """Test get_config_dir() on macOS."""
        with patch.object(sys, "platform", "darwin"):
            config_dir = get_config_dir()
            assert "Library" in str(config_dir)
            assert "Application Support" in str(config_dir)
            assert "miniflux-tui" in str(config_dir)

    def test_get_config_dir_win32(self):
        """Test get_config_dir() on Windows."""
        with patch.object(sys, "platform", "win32"), patch.dict("os.environ", {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"}):
            config_dir = get_config_dir()
            assert "miniflux-tui" in str(config_dir)

    def test_get_config_dir_linux_with_xdg(self):
        """Test get_config_dir() on Linux with XDG_CONFIG_HOME."""
        with patch.object(sys, "platform", "linux"), patch.dict("os.environ", {"XDG_CONFIG_HOME": "/home/test/.config"}):
            config_dir = get_config_dir()
            assert "/home/test/.config" in str(config_dir)
            assert "miniflux-tui" in str(config_dir)

    def test_get_config_dir_linux_default(self):
        """Test get_config_dir() on Linux without XDG_CONFIG_HOME."""
        with patch.object(sys, "platform", "linux"), patch.dict("os.environ", {}, clear=True):
            config_dir = get_config_dir()
            assert ".config" in str(config_dir)
            assert "miniflux-tui" in str(config_dir)

    def test_get_config_file_path(self):
        """Test get_config_file_path() returns correct filename."""
        config_path = get_config_file_path()
        assert config_path.name == "config.toml"
        assert "miniflux-tui" in str(config_path)


class TestCreateDefaultConfig:
    """Test default configuration creation."""

    def test_create_default_config(self, tmp_path):
        """Test create_default_config() creates file with correct content."""
        config_dir = tmp_path / "miniflux-tui"

        with patch("miniflux_tui.config.get_config_dir") as mock_get_dir:
            mock_get_dir.return_value = config_dir
            config_path = create_default_config()

            assert config_path.exists()
            assert config_path.name == "config.toml"

            content = config_path.read_text()
            assert "server_url" in content
            assert "api_key" in content
            assert "allow_invalid_certs" in content
            assert "[theme]" in content
            assert "[sorting]" in content

    def test_create_default_config_creates_directory(self, tmp_path):
        """Test create_default_config() creates directory if it doesn't exist."""
        config_dir = tmp_path / "does" / "not" / "exist" / "miniflux-tui"

        with patch("miniflux_tui.config.get_config_dir") as mock_get_dir:
            mock_get_dir.return_value = config_dir
            config_path = create_default_config()

            assert config_dir.exists()
            assert config_path.exists()

    def test_create_default_config_overwrites_existing(self, tmp_path):
        """Test create_default_config() overwrites existing file."""
        config_dir = tmp_path / "miniflux-tui"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "config.toml"
        config_path.write_text("old content")

        with patch("miniflux_tui.config.get_config_dir") as mock_get_dir:
            mock_get_dir.return_value = config_dir
            returned_path = create_default_config()

            assert returned_path == config_path
            content = config_path.read_text()
            assert "server_url" in content
            assert "old content" not in content


class TestLoadConfig:
    """Test configuration loading."""

    def test_load_config_success(self, tmp_path):
        """Test load_config() successfully loads valid config."""
        config_dir = tmp_path / "miniflux-tui"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text("""
server_url = "https://miniflux.example.com"
api_key = "test-api-key-1234567890"
""")

        with patch("miniflux_tui.config.get_config_file_path") as mock_get_path:
            mock_get_path.return_value = config_file
            config = load_config()

            assert config is not None
            assert config.server_url == "https://miniflux.example.com"
            assert config.api_key == "test-api-key-1234567890"

    def test_load_config_not_found(self, tmp_path):
        """Test load_config() returns None when config doesn't exist."""
        config_path = tmp_path / "nonexistent.toml"

        with patch("miniflux_tui.config.get_config_file_path") as mock_get_path:
            mock_get_path.return_value = config_path
            config = load_config()

            assert config is None

    def test_load_config_with_all_options(self, tmp_path):
        """Test load_config() with all configuration options."""
        config_dir = tmp_path / "miniflux-tui"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text("""
server_url = "https://miniflux.example.com"
api_key = "test-api-key-1234567890"
allow_invalid_certs = true

[theme]
unread_color = "blue"
read_color = "red"

[sorting]
default_sort = "status"
default_group_by_feed = true
group_collapsed = true
""")

        with patch("miniflux_tui.config.get_config_file_path") as mock_get_path:
            mock_get_path.return_value = config_file
            config = load_config()

            assert config is not None
            assert config.server_url == "https://miniflux.example.com"
            assert config.allow_invalid_certs is True
            assert config.unread_color == "blue"
            assert config.read_color == "red"
            assert config.default_sort == "status"
            assert config.default_group_by_feed is True
            assert config.group_collapsed is True
