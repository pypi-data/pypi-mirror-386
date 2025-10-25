"""Pytest configuration and fixtures for quip tests."""
import pytest
import os
import tempfile
import shutil
import yaml
import json
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "defaults": {
            "template": "ue-task",
            "project_prefix": "test",
            "use_keyring": False,
            "code_type": "simple",
            "icon_font": "cour.ttf",
            "bootstrap": {
                "source": "/tmp/ue-baseline",
                "template_source": "/tmp/ut-baseline",
                "exclude": [".git", "dist", "build"],
                "template-exclude": [".git", "dist", "build"]
            }
        },
        "extension.yml": {
            "extension": {
                "name": "test-extension"
            },
            "owner": {
                "name": "Test Owner"
            }
        },
        "uip.yml": {
            "url": "http://localhost:8080/uc",
            "userid": "test.user",
            "template-name": "Test Template"
        },
        "external": {},
        "version_files": [
            {
                "file": "src/extension.yml",
                "format": "yml",
                "location": "extension.version"
            }
        ]
    }


@pytest.fixture
def mock_config_file(temp_dir, mock_config):
    """Create a mock config file."""
    config_path = os.path.join(temp_dir, ".uip_config.yml")
    with open(config_path, "w") as f:
        yaml.dump(mock_config, f)
    return config_path


@pytest.fixture
def mock_template_json():
    """Mock template.json for testing."""
    return {
        "name": "Test Template",
        "templateType": "Script",
        "sysId": "test123456",
        "extension": "ue-test",
        "variablePrefix": "test",
        "useCommonScript": True,
        "agentType": "Any",
        "fields": [
            {
                "name": "Test Field 1",
                "label": "Test Field 1",
                "fieldType": "Text",
                "sequence": 0,
                "fieldMapping": "Text Field 1",
                "sysId": "field123"
            }
        ],
        "events": [],
        "commands": []
    }


@pytest.fixture
def mock_project_structure(temp_dir, mock_template_json):
    """Create a mock project structure."""
    project_path = os.path.join(temp_dir, "ue-test-project")
    os.makedirs(project_path)
    
    # Create src/templates directory
    templates_dir = os.path.join(project_path, "src", "templates")
    os.makedirs(templates_dir)
    
    # Create template.json
    template_path = os.path.join(templates_dir, "template.json")
    with open(template_path, "w") as f:
        json.dump(mock_template_json, f, indent=4)
    
    # Create script file
    script_path = os.path.join(templates_dir, "script.py")
    with open(script_path, "w") as f:
        f.write("# Test script\nprint('Hello')\n")
    
    # Create extension.yml
    extension_yml = os.path.join(project_path, "src", "extension.yml")
    with open(extension_yml, "w") as f:
        yaml.dump({
            "extension": {
                "name": "ue-test-project",
                "version": "1.0.0"
            }
        }, f)
    
    # Create fields.yml
    fields_yml = os.path.join(project_path, "fields.yml")
    with open(fields_yml, "w") as f:
        yaml.dump({
            "fields": [
                {"Test Field": "text"}
            ]
        }, f)
    
    return project_path


@pytest.fixture
def mock_yes_input(monkeypatch):
    """Mock user input to always return 'yes'."""
    monkeypatch.setattr('builtins.input', lambda _: 'y')


@pytest.fixture
def mock_no_input(monkeypatch):
    """Mock user input to always return 'no'."""
    monkeypatch.setattr('builtins.input', lambda _: 'n')


@pytest.fixture
def mock_getpass(monkeypatch):
    """Mock getpass to return a test password."""
    monkeypatch.setattr('getpass.getpass', lambda _: 'test_password')
