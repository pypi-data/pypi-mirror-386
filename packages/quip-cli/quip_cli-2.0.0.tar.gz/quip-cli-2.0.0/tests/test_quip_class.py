"""Unit tests for Quip class."""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from quip.quip import Quip, QuipGlobalConfig


class TestQuipInitialization:
    """Tests for Quip class initialization."""
    
    def test_init_basic(self, mock_config_file, monkeypatch):
        """Test basic initialization."""
        # Mock sys.argv to provide required arguments
        test_args = ['quip', 'version']
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.setattr('quip.quip.Quip.set_global_configs', lambda self, name, config: None)
        
        quip = Quip()
        assert quip is not None
    
    def test_parse_arguments_new(self, monkeypatch):
        """Test parsing 'new' command arguments."""
        test_args = ['quip', 'new', 'test-project']
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.setattr('quip.quip.Quip.set_global_configs', lambda self, name, config: None)
        
        quip = Quip()
        assert quip.args.action == 'new'
        assert quip.args.name == 'test-project'
    
    def test_parse_arguments_update(self, monkeypatch):
        """Test parsing 'update' command arguments."""
        test_args = ['quip', 'update', 'test-project', '--uuid']
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.setattr('quip.quip.Quip.set_global_configs', lambda self, name, config: None)
        
        quip = Quip()
        assert quip.args.action == 'update'
        assert quip.args.uuid is True
    
    def test_parse_arguments_build(self, monkeypatch):
        """Test parsing 'build' command arguments."""
        test_args = ['quip', 'build', 'test-project']
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.setattr('quip.quip.Quip.set_global_configs', lambda self, name, config: None)
        
        quip = Quip()
        assert quip.args.action == 'build'


class TestQuipUtilityMethods:
    """Tests for utility methods in Quip class."""
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_titleize(self, mock_parse, mock_config):
        """Test titleize method."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        assert quip.titleize("test-project") == "Test Project"
        assert quip.titleize("test_project") == "Test Project"
        assert quip.titleize("ue-test-project") == "Test Project"
        assert quip.titleize("ut-test-project") == "Test Project"
        assert quip.titleize("TestProject") == "TestProject"  # Already capitalized
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_format_ext_name(self, mock_parse, mock_config):
        """Test format_ext_name method."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        assert quip.format_ext_name("test_project") == "test-project"
        assert quip.format_ext_name("test project") == "test-project"
        assert quip.format_ext_name("test--project") == "test-project"
        assert quip.format_ext_name("test---project") == "test-project"
        assert quip.format_ext_name("TEST") == "test"
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_format_project_folder_name_extension(self, mock_parse, mock_config):
        """Test format_project_folder_name for extension."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        result = quip.format_project_folder_name("test-project", template=False, prefix=None)
        assert result == "ue-test-project"
        
        result = quip.format_project_folder_name("ue-test-project", template=False, prefix=None)
        assert result == "ue-test-project"
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_format_project_folder_name_template(self, mock_parse, mock_config):
        """Test format_project_folder_name for template."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        result = quip.format_project_folder_name("test-project", template=True, prefix=None)
        assert result == "ut-test-project"
        
        result = quip.format_project_folder_name("ut-test-project", template=True, prefix=None)
        assert result == "ut-test-project"
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_format_project_folder_name_with_prefix(self, mock_parse, mock_config):
        """Test format_project_folder_name with prefix."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        result = quip.format_project_folder_name("project", template=False, prefix="myprefix")
        assert result == "ue-myprefix-project"
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_get_new_uuid(self, mock_parse, mock_config):
        """Test get_new_uuid generates valid UUID."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        uuid = quip.get_new_uuid()
        assert len(uuid) == 32  # UUID without dashes
        assert '-' not in uuid
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_get_icon_message(self, mock_parse, mock_config):
        """Test get_icon_message generates appropriate icons."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        assert quip.get_icon_message("ue-aws-s3") == "AS"
        assert quip.get_icon_message("ut-test-template") == "TT"
        assert quip.get_icon_message("my-app") == "MA"
        assert len(quip.get_icon_message("very-long-name-here")) <= 3


class TestQuipFileOperations:
    """Tests for file operations in Quip class."""
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_read_file_content(self, mock_parse, mock_config, temp_dir):
        """Test reading file content."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        # Create a test file
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Test content")
        
        content = quip.read_file_content(test_file)
        assert content == "Test content"
    
    @patch('quip.quip.Quip.set_global_configs')
    @patch('quip.quip.Quip.parse_arguments')
    def test_format_json(self, mock_parse, mock_config):
        """Test JSON formatting."""
        mock_parse.return_value = Mock(name='test', action='version', debug=False)
        quip = Quip()
        
        test_obj = {"name": "test", "value": 123, "nested": {"key": "value"}}
        result = quip.format_json(test_obj)
        
        assert '"name"' in result
        assert '"value"' in result
        assert isinstance(result, str)


class TestQuipGlobalConfig:
    """Tests for QuipGlobalConfig class."""
    
    def test_init_with_existing_config(self, mock_config_file):
        """Test initialization with existing config file."""
        config = QuipGlobalConfig(config_file=mock_config_file)
        assert config.conf is not None
        assert "defaults" in config.conf
    
    def test_config_has_required_keys(self, mock_config_file):
        """Test that config has required keys."""
        config = QuipGlobalConfig(config_file=mock_config_file)
        assert "defaults" in config.conf
        assert "extension.yml" in config.conf
        assert "uip.yml" in config.conf
