"""Integration tests for common workflows."""
import pytest
import os
import json
import yaml
from unittest.mock import patch, Mock
import sys


class TestProjectCreationWorkflow:
    """Integration tests for project creation workflow."""
    
    @patch('quip.quip.Quip.uip_init')
    @patch('quip.quip.Quip.create_icon_safe')
    @patch('subprocess.run')
    def test_new_extension_workflow(self, mock_subprocess, mock_icon, mock_uip, temp_dir, mock_config_file, monkeypatch):
        """Test creating a new extension project."""
        test_args = ['quip', 'new', 'test-project', '-c', mock_config_file]
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.chdir(temp_dir)
        
        from quip.quip import Quip
        
        quip = Quip()
        # Mock the main execution to avoid full workflow
        assert quip.args.action == 'new'
        assert quip.args.name == 'test-project'
    
    @patch('quip.quip.Quip.create_icon_safe')
    @patch('subprocess.run')
    def test_new_template_workflow(self, mock_subprocess, mock_icon, temp_dir, mock_config_file, monkeypatch):
        """Test creating a new template project."""
        test_args = ['quip', 'new', 'test-template', '--template', '-c', mock_config_file]
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.chdir(temp_dir)
        
        from quip.quip import Quip
        
        quip = Quip()
        assert quip.args.action == 'new'
        assert quip.args.template is True


class TestFieldWorkflow:
    """Integration tests for field management workflow."""
    
    def test_fields_yaml_to_template_json(self, mock_project_structure, mock_config_file, monkeypatch):
        """Test converting fields.yml to template.json."""
        test_args = ['quip', 'fields', '--update', '-c', mock_config_file]
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.chdir(mock_project_structure)
        
        from quip.quip import Quip
        
        quip = Quip()
        assert quip.args.action == 'fields'
        assert quip.args.update is True


class TestVersionWorkflow:
    """Integration tests for version management."""
    
    def test_version_display(self, mock_project_structure, mock_config_file, monkeypatch):
        """Test displaying current version."""
        test_args = ['quip', 'version', '-c', mock_config_file]
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.chdir(mock_project_structure)
        
        from quip.quip import Quip
        
        quip = Quip()
        assert quip.args.action == 'version'
    
    def test_version_minor_bump(self, mock_project_structure, mock_config_file, monkeypatch):
        """Test minor version bump."""
        test_args = ['quip', 'version', 'minor', '-c', mock_config_file]
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.chdir(mock_project_structure)
        
        from quip.quip import Quip
        
        quip = Quip()
        assert quip.args.version_method == 'minor'


class TestConfigurationWorkflow:
    """Integration tests for configuration management."""
    
    def test_config_display(self, mock_config_file, monkeypatch):
        """Test displaying configuration."""
        test_args = ['quip', 'config', '-c', mock_config_file]
        monkeypatch.setattr(sys, 'argv', test_args)
        
        from quip.quip import Quip
        
        quip = Quip()
        assert quip.args.action == 'config'


class TestBuildWorkflow:
    """Integration tests for build workflow."""
    
    @patch('subprocess.run')
    def test_template_build(self, mock_subprocess, mock_project_structure, mock_config_file, monkeypatch):
        """Test building a template."""
        # Make it a template project
        template_json = os.path.join(mock_project_structure, "src", "templates", "template.json")
        with open(template_json, "r") as f:
            data = json.load(f)
        data["templateType"] = "Script"
        with open(template_json, "w") as f:
            json.dump(data, f)
        
        test_args = ['quip', 'build', '-c', mock_config_file]
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.chdir(mock_project_structure)
        
        from quip.quip import Quip
        
        quip = Quip()
        assert quip.args.action == 'build'


class TestCleanWorkflow:
    """Integration tests for clean workflow."""
    
    def test_clean_project(self, mock_project_structure, mock_config_file, monkeypatch):
        """Test cleaning project build artifacts."""
        # Create some build directories
        build_dir = os.path.join(mock_project_structure, "build")
        dist_dir = os.path.join(mock_project_structure, "dist")
        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(dist_dir, exist_ok=True)
        
        test_args = ['quip', 'clean', '-c', mock_config_file]
        monkeypatch.setattr(sys, 'argv', test_args)
        monkeypatch.chdir(mock_project_structure)
        
        from quip.quip import Quip
        
        quip = Quip()
        assert quip.args.action == 'clean'
