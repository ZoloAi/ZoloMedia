"""
Tests for DocumentationRegistry - Single Source of Truth

Tests the unified documentation system that eliminates 249 lines of duplication!
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.providers.provider_modules.documentation_registry import (
    Documentation,
    DocumentationType,
    DocumentationRegistry
)


class TestDocumentation:
    """Test Documentation dataclass."""
    
    def test_documentation_creation(self):
        """Test creating a Documentation instance."""
        doc = Documentation(
            label="int",
            title="Integer Number",
            description="Convert value to integer.",
            example="port(int): 8080",
            doc_type=DocumentationType.TYPE_HINT
        )
        
        assert doc.label == "int"
        assert doc.title == "Integer Number"
        assert doc.description == "Convert value to integer."
        assert doc.example == "port(int): 8080"
        assert doc.doc_type == DocumentationType.TYPE_HINT
        assert doc.category is None
    
    def test_documentation_with_category(self):
        """Test creating Documentation with category."""
        doc = Documentation(
            label="zMode",
            title="Execution Mode",
            description="Sets mode.",
            example="zMode: Terminal",
            doc_type=DocumentationType.SPECIAL_KEY,
            category="zSpark"
        )
        
        assert doc.category == "zSpark"
    
    def test_to_hover_markdown(self):
        """Test converting to hover Markdown format."""
        doc = Documentation(
            label="int",
            title="Integer Number",
            description="Convert value to integer.",
            example="port(int): 8080",
            doc_type=DocumentationType.TYPE_HINT
        )
        
        markdown = doc.to_hover_markdown()
        
        assert "**Integer Number**" in markdown
        assert "Convert value to integer." in markdown
        assert "`port(int): 8080`" in markdown
    
    def test_to_completion_detail(self):
        """Test getting completion detail (short)."""
        doc = Documentation(
            label="int",
            title="Integer Number",
            description="Convert value to integer.",
            example="port(int): 8080",
            doc_type=DocumentationType.TYPE_HINT
        )
        
        detail = doc.to_completion_detail()
        assert detail == "Integer Number"
    
    def test_to_completion_documentation(self):
        """Test getting completion documentation (full)."""
        doc = Documentation(
            label="int",
            title="Integer Number",
            description="Convert value to integer.",
            example="port(int): 8080",
            doc_type=DocumentationType.TYPE_HINT
        )
        
        doc_text = doc.to_completion_documentation()
        
        assert "Convert value to integer." in doc_text
        assert "`port(int): 8080`" in doc_text


class TestDocumentationRegistry:
    """Test DocumentationRegistry - SSOT."""
    
    def setup_method(self):
        """Clear registry before each test."""
        # Note: The registry is pre-populated, so we test the existing data
        pass
    
    def test_registry_has_type_hints(self):
        """Test that all 12 type hints are registered."""
        type_hints = DocumentationRegistry.get_by_type(DocumentationType.TYPE_HINT)
        
        # Should have 12 type hints
        assert len(type_hints) == 12
        
        # Check specific type hints
        labels = [doc.label for doc in type_hints]
        assert "int" in labels
        assert "float" in labels
        assert "bool" in labels
        assert "str" in labels
        assert "list" in labels
        assert "dict" in labels
        assert "null" in labels
        assert "raw" in labels
        assert "date" in labels
        assert "time" in labels
        assert "url" in labels
        assert "path" in labels
    
    def test_registry_has_values(self):
        """Test that common values are registered."""
        values = DocumentationRegistry.get_by_type(DocumentationType.VALUE)
        
        # Should have true, false (null is a TYPE_HINT, not VALUE)
        assert len(values) == 2
        
        labels = [doc.label for doc in values]
        assert "true" in labels
        assert "false" in labels
    
    def test_registry_has_special_keys(self):
        """Test that special keys are registered."""
        special_keys = DocumentationRegistry.get_by_type(DocumentationType.SPECIAL_KEY)
        
        # Should have special keys
        assert len(special_keys) > 0
        
        labels = [doc.label for doc in special_keys]
        assert "zMode" in labels
        assert "deployment" in labels
        assert "logger" in labels
    
    def test_get_by_key(self):
        """Test retrieving documentation by key."""
        doc = DocumentationRegistry.get("int")
        
        assert doc is not None
        assert doc.label == "int"
        assert doc.title == "Integer Number"
        assert doc.doc_type == DocumentationType.TYPE_HINT
    
    def test_get_missing_key(self):
        """Test retrieving non-existent key."""
        doc = DocumentationRegistry.get("nonexistent")
        assert doc is None
    
    def test_get_by_category(self):
        """Test retrieving documentation by category."""
        zspark_docs = DocumentationRegistry.get_by_category("zSpark")
        
        assert len(zspark_docs) > 0
        labels = [doc.label for doc in zspark_docs]
        assert "zMode" in labels
        assert "deployment" in labels
        assert "logger" in labels
    
    def test_all(self):
        """Test retrieving all documentation."""
        all_docs = DocumentationRegistry.all()
        
        # Should have type hints + values + special keys
        assert len(all_docs) >= 15  # 12 type hints + 3 values + special keys
    
    def test_register_custom(self):
        """Test registering custom documentation."""
        custom_doc = Documentation(
            label="test_custom",  # Use unique name to avoid conflicts
            title="Custom Type",
            description="Custom description.",
            example="custom: value",
            doc_type=DocumentationType.TYPE_HINT
        )
        
        DocumentationRegistry.register("test_custom", custom_doc)
        
        retrieved = DocumentationRegistry.get("test_custom")
        assert retrieved is not None
        assert retrieved.label == "test_custom"
        assert retrieved.title == "Custom Type"
        
        # Clean up after test to avoid affecting other tests
        DocumentationRegistry._registry.pop("test_custom", None)


class TestDocumentationTypeEnum:
    """Test DocumentationType enum."""
    
    def test_enum_values(self):
        """Test that all expected enum values exist."""
        assert DocumentationType.TYPE_HINT.value == "type_hint"
        assert DocumentationType.SPECIAL_KEY.value == "special_key"
        assert DocumentationType.UI_ELEMENT.value == "ui_element"
        assert DocumentationType.ZKERNEL_DATA.value == "zkernel_data"
        assert DocumentationType.VALUE.value == "value"


class TestSingleSourceOfTruth:
    """Test that the registry eliminates duplication."""
    
    def test_no_duplication_needed(self):
        """Test that hover and completion can use the same data."""
        # Get type hint documentation
        doc = DocumentationRegistry.get("int")
        
        # Both hover and completion can use the same doc
        hover_text = doc.to_hover_markdown()
        completion_detail = doc.to_completion_detail()
        completion_doc = doc.to_completion_documentation()
        
        # All should contain the same information
        assert "integer" in hover_text.lower()
        assert "integer" in completion_detail.lower()
        assert "integer" in completion_doc.lower()
    
    def test_all_type_hints_accessible(self):
        """Test that all type hints are accessible for both use cases."""
        type_hints = DocumentationRegistry.get_by_type(DocumentationType.TYPE_HINT)
        
        # All type hints should support both formats
        for doc in type_hints:
            hover = doc.to_hover_markdown()
            detail = doc.to_completion_detail()
            doc_text = doc.to_completion_documentation()
            
            assert hover  # Not empty
            assert detail  # Not empty
            assert doc_text  # Not empty
