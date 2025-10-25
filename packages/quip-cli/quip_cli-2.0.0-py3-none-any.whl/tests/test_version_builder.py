"""Unit tests for version_builder module."""
import pytest
import os
import yaml
from quip import version_builder as vb


class TestVersionParsing:
    """Tests for version parsing functions."""
    
    def test_safeget_existing_keys(self):
        """Test safeget with existing keys."""
        data = {"a": {"b": {"c": "value"}}}
        result = vb.safeget(data, "a", "b", "c")
        assert result == "value"
    
    def test_safeget_missing_key(self):
        """Test safeget with missing key."""
        data = {"a": {"b": "value"}}
        result = vb.safeget(data, "a", "c")
        assert result is None
    
    def test_safeset_existing_keys(self):
        """Test safeset with existing keys."""
        data = {"a": {"b": "old"}}
        result = vb.safeset(data, "new", "a", "b")
        assert result["a"]["b"] == "new"
    
    def test_safeset_missing_key(self):
        """Test safeset with missing key."""
        data = {"a": {}}
        result = vb.safeset(data, "value", "a", "b", "c")
        assert result is None


class TestVersionExtraction:
    """Tests for version extraction from files."""
    
    def test_get_version_from_yaml_file(self, temp_dir):
        """Test extracting version from YAML file."""
        yaml_file = os.path.join(temp_dir, "test.yml")
        data = {"extension": {"version": "1.2.3"}}
        with open(yaml_file, "w") as f:
            yaml.dump(data, f)
        
        versions = vb.get_version_from_file(yaml_file, "yml", "extension.version")
        assert len(versions) == 1
        assert versions[0] == "1.2.3"
    
    def test_get_version_from_python_file(self, temp_dir):
        """Test extracting version from Python file."""
        py_file = os.path.join(temp_dir, "test.py")
        with open(py_file, "w") as f:
            f.write('__version__ = "2.3.4"\n')
        
        pattern = r"^\s*(__version__)\s*=\s*[\"']+([^\"']+)[\"']+"
        versions = vb.get_version_from_file(py_file, "regex", pattern, group=2)
        assert len(versions) == 1
        assert versions[0] == "2.3.4"
    
    def test_get_version_from_nonexistent_file(self):
        """Test extracting version from non-existent file."""
        versions = vb.get_version_from_file("/nonexistent/file.yml", "yml", "version")
        assert len(versions) == 0


class TestVersionGeneration:
    """Tests for version number generation."""
    
    def test_get_new_version_minor(self):
        """Test generating minor version bump."""
        new_version = vb.get_new_version("minor", "1.2.3")
        assert new_version == "1.2.4"
    
    def test_get_new_version_major(self):
        """Test generating major version bump."""
        new_version = vb.get_new_version("major", "1.2.3")
        assert new_version == "1.3.0"
    
    def test_get_new_version_release(self):
        """Test generating release version."""
        new_version = vb.get_new_version("release", "1.2.3")
        assert new_version == "2.0.0"
    
    def test_get_new_version_beta(self):
        """Test generating beta version."""
        new_version = vb.get_new_version("beta", "1.2.3")
        assert new_version == "1.2.3-beta.1"
    
    def test_get_new_version_beta_increment(self):
        """Test incrementing beta version."""
        new_version = vb.get_new_version("beta", "1.2.3-beta.1")
        assert new_version == "1.2.3-beta.2"
    
    def test_get_new_version_rc(self):
        """Test generating release candidate version."""
        new_version = vb.get_new_version("rc", "1.2.3")
        assert new_version == "1.2.3-rc.1"
    
    def test_get_new_version_rc_increment(self):
        """Test incrementing rc version."""
        new_version = vb.get_new_version("rc", "1.2.3-rc.1")
        assert new_version == "1.2.3-rc.2"


class TestVersionUpdate:
    """Tests for version update in files."""
    
    def test_update_version_in_yaml(self, temp_dir):
        """Test updating version in YAML file."""
        yaml_file = os.path.join(temp_dir, "extension.yml")
        data = {"extension": {"version": "1.0.0"}}
        with open(yaml_file, "w") as f:
            yaml.dump(data, f)
        
        version_files = [{
            "file": yaml_file,
            "format": "yml",
            "location": "extension.version"
        }]
        
        vb.update_version("1.0.0", "2.0.0", version_files=version_files)
        
        with open(yaml_file) as f:
            updated = yaml.safe_load(f)
        
        assert updated["extension"]["version"] == "2.0.0"
    
    def test_update_version_in_python(self, temp_dir):
        """Test updating version in Python file."""
        py_file = os.path.join(temp_dir, "version.py")
        with open(py_file, "w") as f:
            f.write('__version__ = "1.0.0"\n')
        
        version_files = [{
            "file": py_file,
            "format": "regex",
            "location": r"^\s*(__version__)\s*=\s*[\"']+([^\"']+)[\"']+",
            "group": 2
        }]
        
        vb.update_version("1.0.0", "2.0.0", version_files=version_files)
        
        with open(py_file) as f:
            content = f.read()
        
        assert '__version__ = "2.0.0"' in content


class TestFindCurrentVersion:
    """Tests for finding current version across files."""
    
    def test_find_version_single_file(self, temp_dir):
        """Test finding version from a single file."""
        yaml_file = os.path.join(temp_dir, "extension.yml")
        data = {"extension": {"version": "1.5.0"}}
        with open(yaml_file, "w") as f:
            yaml.dump(data, f)
        
        version_files = [{
            "file": yaml_file,
            "format": "yml",
            "location": "extension.version"
        }]
        
        versions = vb.find_current_version(version_files)
        assert "1.5.0" in versions
    
    def test_find_version_multiple_files_same(self, temp_dir):
        """Test finding same version from multiple files."""
        yaml_file = os.path.join(temp_dir, "extension.yml")
        py_file = os.path.join(temp_dir, "version.py")
        
        with open(yaml_file, "w") as f:
            yaml.dump({"extension": {"version": "1.0.0"}}, f)
        
        with open(py_file, "w") as f:
            f.write('__version__ = "1.0.0"\n')
        
        version_files = [
            {
                "file": yaml_file,
                "format": "yml",
                "location": "extension.version"
            },
            {
                "file": py_file,
                "format": "regex",
                "location": r"^\s*(__version__)\s*=\s*[\"']+([^\"']+)[\"']+",
                "group": 2
            }
        ]
        
        versions = vb.find_current_version(version_files)
        assert len(versions) == 1
        assert versions[0] == "1.0.0"
