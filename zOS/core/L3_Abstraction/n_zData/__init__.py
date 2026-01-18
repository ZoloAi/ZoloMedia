# zCLI/subsystems/zData/__init__.py
"""
Unified data management subsystem for zCLI.

The zData subsystem provides comprehensive database operations with support for
multiple backends (SQLite, PostgreSQL, CSV), declarative schema definitions,
validation, hooks, and mode-agnostic display integration.

Features
--------
**CRUD Operations:**
- **INSERT**: Insert rows with validation and hooks (onBeforeInsert, onAfterInsert)
- **READ**: Select with JOINs, WHERE filtering, ORDER BY, LIMIT + OFFSET pagination
- **UPDATE**: Update rows with partial updates, WHERE conditions, hooks (onBeforeUpdate, onAfterUpdate)
- **DELETE**: Delete rows with WHERE safety (no hooks - irreversible by design)
- **UPSERT**: Insert-or-update with adapter-specific conflict resolution

**DDL Operations:**
- **CREATE TABLE**: Create tables from schema definitions (idempotent, bulk creation)
- **HEAD**: Display table schema (columns, types, nullable, defaults) via zDisplay
- **DROP TABLE**: Drop tables with critical safety warnings and cascade handling

**Transaction Control (TCL):**
- **BEGIN**: Start transaction
- **COMMIT**: Commit transaction
- **ROLLBACK**: Rollback transaction

**Data Control (DCL):**
- **GRANT**: Grant permissions (adapter-specific)
- **REVOKE**: Revoke permissions (adapter-specific)

**Validation:**
- 5-layer validation architecture: string → numeric → pattern → format → plugin
- Schema-driven field validation with type checking
- Custom business logic via plugin validators (zParser integration)

**Hooks:**
- onBeforeInsert, onAfterInsert: Execute custom logic around INSERT
- onBeforeUpdate, onAfterUpdate: Execute custom logic around UPDATE
- Hook execution via zFunc integration with zConv pattern

**Display Integration:**
- Mode-aware output via zDisplay (Terminal ASCII vs Bifrost JSON)
- Paginated table display with AdvancedData.zTable() for query results
- Interactive pagination in Terminal mode (press Enter to continue)

Supported Backends
-----------------
**SQLite:**
- File-based SQL database
- WAL mode for concurrency
- PRAGMA commands (foreign_keys, journal_mode, synchronous)
- DEFERRED isolation level
- INSERT OR REPLACE for UPSERT

**PostgreSQL:**
- Network-based SQL database
- psycopg2 driver
- Auto-database creation
- ON CONFLICT DO UPDATE for UPSERT
- SERIAL types for auto-increment primary keys

**CSV:**
- pandas DataFrame-based
- File-based persistence with in-memory caching
- Multi-table JOIN support with merge strategies
- Comprehensive WHERE clause filtering
- Schema-based type coercion

Architecture
-----------
zData uses a 2-tier architecture (simplified from 3-tier in Week 6.16 - Phase 3.1):

**Tier 1: zData.py (Main Facade)**
- Schema loading via zLoader
- Adapter initialization via AdapterFactory
- Request routing to operations

**Tier 2: Shared Infrastructure (zData_modules/shared/)**
- **Parsers**: WHERE clause and value type parsing
- **Validator**: 5-layer validation
- **Operations**: CRUD/DDL operation handlers
- **Backends**: Database adapters (SQLite, PostgreSQL, CSV)
- **DataOperations**: Central facade for operation routing

**Architectural History:**
Previously, zData had a 3-tier architecture with paradigm detection (classical vs quantum).
Quantum support was extracted as a separate Zolo app, and ClassicalData logic was merged
directly into zData.py, simplifying the architecture.

Usage Examples
-------------
**Basic Schema Loading and INSERT:**
    >>> from zOS import zOS
    >>> z = zCLI()
    >>> z.data.load_schema("@myapp.users.yaml")
    >>> z.data.insert("users", {"name": "Alice", "age": 30, "email": "alice@example.com"})

**READ with WHERE filtering and pagination:**
    >>> z.data.select("users", where="age >= 18", limit=20, offset=40, order_by="name")

**UPDATE with partial updates:**
    >>> z.data.update("users", {"status": "active"}, where="age >= 18")

**DELETE with WHERE safety:**
    >>> z.data.delete("users", where="status = inactive")

**UPSERT (conflict resolution):**
    >>> z.data.upsert("users", {"id": 1, "name": "Bob", "age": 25})

**DDL Operations:**
    >>> z.data.create_table(["users", "posts"])  # Bulk creation
    >>> z.data.head("users")  # Display schema
    >>> z.data.drop("temp_table", if_exists=True)  # Drop with safety

**Transaction Control:**
    >>> z.data.begin_transaction()
    >>> z.data.insert("users", {"name": "Charlie", "age": 35})
    >>> z.data.commit()  # or z.data.rollback()

**Wizard Mode (Schema Persistence):**
    >>> # In zWizard workflows, schema persists across steps
    >>> z.wizard.load("user_registration.yaml")
    >>> # Step 1: z.data operations work seamlessly
    >>> # Step 2: Same adapter/validator/operations persist
    >>> # Step 3: z.data.disconnect() called on wizard completion

**One-Shot Mode (Schema Loading):**
    >>> # In single commands, schema is loaded on demand
    >>> z.data.insert("users", {...})  # Schema loaded if not already
    >>> # Connection closed after command completes

Integration Points
-----------------
**zLoader**: Schema loading and 4-tier caching (system, pinned, schema, plugin)
**zParser**: zPath resolution (@., ~., zMachine.*), plugin validators (&PluginName.validator)
**zFunc**: Hook execution (onBeforeInsert, onAfterInsert, onBeforeUpdate, onAfterUpdate)
**zDisplay**: Mode-aware output (Terminal, Bifrost), paginated tables via AdvancedData
**zSession**: Active session state, zMode detection (Terminal, Walker, zBifrost)
**zWizard**: Multi-step data collection workflows with schema persistence
**zOpen**: Direct database file operations
**zComm**: Service management, WebSocket communication (Bifrost)

Schema Format
------------
zData uses declarative YAML schemas (zSchema files) with this structure:

**Meta Section:**
    Meta:
      Type: sqlite | postgresql | csv
      Connection:
        db_path: path/to/database.db  # SQLite
        host: localhost               # PostgreSQL
        port: 5432
        database: mydb
        user: postgres
        password: secret
        csv_dir: path/to/csv/          # CSV

**Tables Section:**
    Tables:
      users:
        Columns:
          id: {type: integer, primary_key: true, auto_increment: true}
          name: {type: string, required: true, maxLength: 100}
          age: {type: integer, min: 0, max: 150}
          email: {type: string, format: email}
        Hooks:
          onBeforeInsert: &MyPlugin.validate_user
          onAfterInsert: &MyPlugin.send_welcome_email

See Also
--------
- zData.py: Main facade with all operation methods
- zData_modules/: Internal implementation modules
- zLoader: Schema loading and caching
- zParser: Path resolution and plugin invocation
- zDisplay: Mode-aware output and AdvancedData tables
- zWizard: Multi-step workflows with data persistence
"""

from .zData import zData

__all__ = [
    "zData",
]