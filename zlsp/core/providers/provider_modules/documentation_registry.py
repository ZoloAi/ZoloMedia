"""
Documentation Registry - Single Source of Truth

This is the ONLY place where documentation is defined.
All providers (hover, completion) use this registry.

Eliminates 249 lines of duplication between hover_provider.py and completion_provider.py!
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class DocumentationType(Enum):
    """Type of documentation entry."""
    TYPE_HINT = "type_hint"
    SPECIAL_KEY = "special_key"
    UI_ELEMENT = "ui_element"
    ZKERNEL_DATA = "zkernel_data"
    VALUE = "value"


@dataclass
class Documentation:
    """
    Unified documentation entry.
    
    Used for type hints, special keys, UI elements, etc.
    Supports both hover and completion generation.
    """
    label: str
    title: str
    description: str
    example: str
    doc_type: DocumentationType
    category: Optional[str] = None
    
    def to_hover_markdown(self) -> str:
        """Convert to Markdown for hover display."""
        return f"**{self.title}**\n\n{self.description}\n\nExample: `{self.example}`"
    
    def to_completion_detail(self) -> str:
        """Get short detail for completion item."""
        return self.title
    
    def to_completion_documentation(self) -> str:
        """Get full documentation for completion item."""
        return f"{self.description}\n\nExample: `{self.example}`"


class DocumentationRegistry:
    """
    Central registry for all documentation.
    
    Single Source of Truth (SSOT) - change once, affects all providers!
    """
    
    _registry: Dict[str, Documentation] = {}
    
    @classmethod
    def register(cls, key: str, doc: Documentation) -> None:
        """Register documentation entry."""
        cls._registry[key] = doc
    
    @classmethod
    def get(cls, key: str) -> Optional[Documentation]:
        """Get documentation by key."""
        return cls._registry.get(key)
    
    @classmethod
    def get_by_type(cls, doc_type: DocumentationType) -> List[Documentation]:
        """Get all documentation of a specific type."""
        return [
            doc for doc in cls._registry.values() 
            if doc.doc_type == doc_type
        ]
    
    @classmethod
    def get_by_category(cls, category: str) -> List[Documentation]:
        """Get all documentation for a specific category."""
        return [
            doc for doc in cls._registry.values()
            if doc.category == category
        ]
    
    @classmethod
    def all(cls) -> List[Documentation]:
        """Get all registered documentation."""
        return list(cls._registry.values())
    
    @classmethod
    def clear(cls) -> None:
        """Clear registry (for testing)."""
        cls._registry.clear()


# ============================================================================
# SSOT: Type Hint Documentation (12 entries)
# ============================================================================

TYPE_HINTS = [
    Documentation(
        label="int",
        title="Integer Number",
        description="Convert value to integer.",
        example="port(int): 8080",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="float",
        title="Floating Point Number",
        description="Convert value to float.",
        example="pi(float): 3.14159",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="bool",
        title="Boolean",
        description="Convert value to boolean (true/false).",
        example="enabled(bool): true",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="str",
        title="String",
        description="Explicitly mark value as string. Also enables multi-line YAML-style content collection.",
        example="description(str): My App",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="list",
        title="List/Array",
        description="Ensure value is a list.",
        example="items(list): [1, 2, 3]",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="dict",
        title="Dictionary/Object",
        description="Ensure value is a dictionary.",
        example="config(dict): {key: value}",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="null",
        title="Null Value",
        description="Set value to null/None.",
        example="optional(null):",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="raw",
        title="Raw String",
        description="String without escape sequence processing.",
        example="regex(raw): \\d+",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="date",
        title="Date String",
        description="Date value (semantic hint).",
        example="created(date): 2024-01-06",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="time",
        title="Time String",
        description="Time value (semantic hint).",
        example="starts(time): 14:30:00",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="url",
        title="URL String",
        description="URL value (semantic hint).",
        example="homepage(url): https://example.com",
        doc_type=DocumentationType.TYPE_HINT
    ),
    Documentation(
        label="path",
        title="Path String",
        description="File path (semantic hint).",
        example="config(path): /etc/app/config.zolo",
        doc_type=DocumentationType.TYPE_HINT
    ),
]

# ============================================================================
# SSOT: Common Value Documentation
# ============================================================================

COMMON_VALUES = [
    Documentation(
        label="true",
        title="Boolean true",
        description="Use with (bool) type hint for boolean values.",
        example="enabled(bool): true",
        doc_type=DocumentationType.VALUE
    ),
    Documentation(
        label="false",
        title="Boolean false",
        description="Use with (bool) type hint for boolean values.",
        example="disabled(bool): false",
        doc_type=DocumentationType.VALUE
    ),
    # Note: "null" is registered as TYPE_HINT, not VALUE
]

# ============================================================================
# SSOT: Special Key Documentation (zSpark, zEnv, zUI, zSchema)
# ============================================================================

SPECIAL_KEYS = [
    Documentation(
        label="zMode",
        title="zMode (Execution Mode)",
        description="Sets execution mode: Terminal or zBifrost.",
        example="zMode: Terminal",
        doc_type=DocumentationType.SPECIAL_KEY,
        category="zSpark"
    ),
    Documentation(
        label="deployment",
        title="Deployment Environment",
        description="Deployment mode: Production or Development.",
        example="deployment: Production",
        doc_type=DocumentationType.SPECIAL_KEY,
        category="zSpark"
    ),
    Documentation(
        label="logger",
        title="Logger Level",
        description="Logging level: DEBUG, SESSION, INFO, WARNING, ERROR, CRITICAL, PROD.",
        example="logger: INFO",
        doc_type=DocumentationType.SPECIAL_KEY,
        category="zSpark"
    ),
    Documentation(
        label="zMeta",
        title="zMeta (Metadata Block)",
        description="Metadata block for zUI and zSchema files.",
        example="zMeta:\n  Data_Type: User",
        doc_type=DocumentationType.SPECIAL_KEY,
        category="zKernel"
    ),
    Documentation(
        label="zRBAC",
        title="zRBAC (Access Control)",
        description="Role-based access control block.",
        example="zRBAC:\n  admin: full",
        doc_type=DocumentationType.SPECIAL_KEY,
        category="zEnv"
    ),
]

# ============================================================================
# Auto-Register All Documentation
# ============================================================================

for doc in TYPE_HINTS + COMMON_VALUES + SPECIAL_KEYS:
    DocumentationRegistry.register(doc.label, doc)
