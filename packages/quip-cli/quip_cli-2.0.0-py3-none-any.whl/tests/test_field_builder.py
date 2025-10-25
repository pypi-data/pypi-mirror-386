"""Unit tests for field_builder module."""
import pytest
from quip import field_builder as fb


class TestFieldMapping:
    """Tests for field mapping functions."""
    
    def test_get_type_name(self):
        """Test get_type_name function."""
        assert fb.get_type_name("text") == "Text"
        assert fb.get_type_name("Text") == "Text"
        assert fb.get_type_name("large_text") == "Large Text"
        assert fb.get_type_name("boolean") == "Boolean"
        assert fb.get_type_name("choice") == "Choice"
    
    def test_labelize(self):
        """Test labelize function."""
        assert fb.labelize("test_field") == "Test Field"
        assert fb.labelize("testField") == "Test Field"
        assert fb.labelize("test-field") == "Test Field"
        assert fb.labelize("Test Field") == "Test Field"


class TestFieldCreation:
    """Tests for field creation functions."""
    
    def test_new_uuid_generation(self):
        """Test that new_uuid generates valid UUIDs."""
        uuid1 = fb.new_uuid()
        uuid2 = fb.new_uuid()
        
        assert len(uuid1) == 32
        assert len(uuid2) == 32
        assert uuid1 != uuid2
        assert '-' not in uuid1
    
    def test_create_text_field(self):
        """Test creating a text field."""
        field = fb.create_text_field("test_field", "Text Field 1", 0)
        
        assert field["name"] == "test_field"
        assert field["label"] == "Test Field"
        assert field["fieldType"] == "Text"
        assert field["fieldMapping"] == "Text Field 1"
        assert field["sequence"] == 0
        assert "sysId" in field
    
    def test_create_text_field_with_regex(self):
        """Test creating a text field with regex validation."""
        field = fb.create_text_field("email_field", "Text Field 2", 1, regex=r"^[a-z]+@[a-z]+\.[a-z]+$")
        
        assert field["name"] == "email_field"
        assert field["regex"] == r"^[a-z]+@[a-z]+\.[a-z]+$"
    
    def test_create_boolean_field(self):
        """Test creating a boolean field."""
        field = fb.create_boolean_field("enable_feature", "Boolean Field 1", 0)
        
        assert field["name"] == "enable_feature"
        assert field["label"] == "Enable Feature"
        assert field["fieldType"] == "Boolean"
        assert field["fieldMapping"] == "Boolean Field 1"
    
    def test_create_choice_field(self):
        """Test creating a choice field."""
        items = ["Option 1", "Option 2", "Option 3"]
        field = fb.create_choice_field("my_choice", "Choice Field 1", 0, items)
        
        assert field["name"] == "my_choice"
        assert field["fieldType"] == "Choice"
        assert len(field["items"]) == 3
        assert field["items"][0]["label"] == "Option 1"
    
    def test_create_credential_field(self):
        """Test creating a credential field."""
        field = fb.create_credential_field("my_credential", "Credential Field 1", 0)
        
        assert field["name"] == "my_credential"
        assert field["fieldType"] == "Credential"
        assert field["fieldMapping"] == "Credential Field 1"
    
    def test_create_credential_field_with_variable(self):
        """Test creating a credential field with variable support."""
        field = fb.create_credential_field("my_credential", "Credential Field 1", 0, allow_var=True)
        
        assert field["name"] == "my_credential"
        assert field["allowVariables"] is True


class TestFieldPreparation:
    """Tests for prepare_fields function."""
    
    def test_prepare_simple_fields(self):
        """Test preparing simple field list."""
        fields_config = [
            {"field1": "text"},
            {"field2": "boolean"}
        ]
        
        result = fb.prepare_fields(fields_config, code=False)
        
        assert len(result) == 2
        assert result[0]["name"] == "field1"
        assert result[0]["fieldType"] == "Text"
        assert result[1]["name"] == "field2"
        assert result[1]["fieldType"] == "Boolean"
    
    def test_prepare_fields_with_mapping(self):
        """Test preparing fields with explicit mapping."""
        fields_config = [
            {"field1": "text", "field_mapping": "Text Field 5"}
        ]
        
        result = fb.prepare_fields(fields_config, code=False)
        
        assert result[0]["fieldMapping"] == "Text Field 5"
    
    def test_prepare_choice_field_with_items(self):
        """Test preparing choice field with items."""
        fields_config = [
            {"my_choice": "choice", "items": ["A", "B", "C"]}
        ]
        
        result = fb.prepare_fields(fields_config, code=False)
        
        assert result[0]["fieldType"] == "Choice"
        assert len(result[0]["items"]) == 3


class TestFieldDumping:
    """Tests for field dumping functions."""
    
    def test_dump_fields(self):
        """Test dumping fields to YAML format."""
        fields = [
            {
                "name": "test_field",
                "label": "Test Field",
                "fieldType": "Text",
                "fieldMapping": "Text Field 1",
                "sequence": 0,
                "required": True
            }
        ]
        
        result = fb.dump_fields(fields)
        
        assert len(result) == 1
        assert "test_field" in result[0]
        assert result[0]["test_field"] == "text"
    
    def test_dump_choice_field(self):
        """Test dumping choice field."""
        fields = [
            {
                "name": "my_choice",
                "label": "My Choice",
                "fieldType": "Choice",
                "fieldMapping": "Choice Field 1",
                "items": [
                    {"label": "Option 1", "name": "opt1"},
                    {"label": "Option 2", "name": "opt2"}
                ]
            }
        ]
        
        result = fb.dump_fields(fields)
        
        assert "my_choice" in result[0]
        assert "items" in result[0]
        assert len(result[0]["items"]) == 2


class TestTemplateFields:
    """Tests for template field functions."""
    
    def test_prepare_template_fields(self):
        """Test preparing template-level fields."""
        config = {
            "name": "Test Template",
            "description": "Test Description",
            "icon": "test_icon.png"
        }
        
        result = fb.prepare_template_fields(config)
        
        assert "name" in result
        assert "description" in result
    
    def test_dump_template_fields(self):
        """Test dumping template-level fields."""
        template_json = {
            "name": "Test Template",
            "description": "Test Description",
            "templateType": "Script"
        }
        
        result = fb.dump_template_fields(template_json)
        
        assert result["name"] == "Test Template"
        assert result["description"] == "Test Description"


class TestEventFields:
    """Tests for event field functions."""
    
    def test_prepare_event_fields_empty(self):
        """Test preparing empty event list."""
        result = fb.prepare_event_fields([])
        assert result == []
    
    def test_dump_events_none(self):
        """Test dumping None events."""
        result = fb.dump_events(None)
        assert result == []
    
    def test_dump_events_empty(self):
        """Test dumping empty events list."""
        result = fb.dump_events([])
        assert result == []


class TestCommandFields:
    """Tests for command field functions."""
    
    def test_prepare_command_fields_empty(self):
        """Test preparing empty command list."""
        result = fb.prepare_command_fields([], {})
        assert result == []
    
    def test_dump_commands_none(self):
        """Test dumping None commands."""
        result = fb.dump_commands(None, [])
        assert result == []
    
    def test_dump_commands_empty(self):
        """Test dumping empty commands list."""
        result = fb.dump_commands([], [])
        assert result == []
