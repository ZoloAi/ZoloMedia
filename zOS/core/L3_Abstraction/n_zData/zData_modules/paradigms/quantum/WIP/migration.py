# zCLI/subsystems/zData/zData_modules/paradigms/quantum/WIP/migration.py

# zCLI/subsystems/zMigrate.py - Schema Migration Subsystem
# --------------------------------------------------------------

"""
zMigrate - Minimal Schema Migration System

Version: 1.0 (ADD COLUMN only)

Handles:
- Schema introspection (read current database structure)
- Change detection (compare YAML schema vs database)
- Add missing columns (ALTER TABLE ADD COLUMN)

Future: DROP COLUMN, RENAME, TYPE changes, indexes, etc.
"""

# Logger will be passed as parameter to functions that need it

# ====================================================================
# Ghost Migration Table Schema for RGB Tracking
# ====================================================================
MIGRATION_TABLE_SCHEMA = {
    "id": {
        "type": "TEXT",
        "primary_key": True,
        "description": "Migration identifier"
    },
    "migration_type": {
        "type": "TEXT",
        "not_null": True,
        "description": "Type of migration (add_column, drop_column, etc.)"
    },
    "target_table": {
        "type": "TEXT",
        "not_null": True,
        "description": "Target table name"
    },
    "target_column": {
        "type": "TEXT",
        "description": "Target column name (null for table-level operations)"
    },
    "description": {
        "type": "TEXT",
        "description": "Human readable description"
    },
    "applied_at": {
        "type": "TEXT",
        "not_null": True,
        "description": "ISO timestamp when applied"
    },
    "status": {
        "type": "TEXT",
        "default": "success",
        "description": "Migration status (success, failed, rolled_back)"
    },
    # RGB Impact Tracking
    "rgb_impact_r": {
        "type": "int",
        "default": 0,
        "description": "Impact on Red component (time freshness)"
    },
    "rgb_impact_g": {
        "type": "int",
        "default": 0,
        "description": "Impact on Green component (access frequency)"
    },
    "rgb_impact_b": {
        "type": "int",
        "default": 10,
        "description": "Impact on Blue component (migration stability)"
    },
    "criticality_level": {
        "type": "int",
        "default": 1,
        "description": "1=low, 2=medium, 3=high, 4=critical"
    }
}


class ZMigrate:
    """
    Schema migration manager for zCLI.
    
    Minimal v1.0: Detects and adds missing columns only.
    """
    
    def __init__(self, walker=None, logger=None):
        """
        Initialize migration manager.
        
        Args:
            walker: Optional zCLI instance for context
            logger: Logger instance to use
        """
        self.walker = walker
        self.logger = logger or (walker.logger if walker else None)
    
    def _ensure_migrations_table(self, zData):
        """Create zMigrations table using zCLI's zTables function."""
        if zData["type"] == "sqlite":
            from zOS.L3_Abstraction.n_zData.zData_modules.infrastructure import zTables
            
            # Check if table exists first
            cur = zData["cursor"]
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='zMigrations'")
            if not cur.fetchone():
                # Create using zCLI's table creation system
                zTables("zMigrations", MIGRATION_TABLE_SCHEMA, zData["cursor"], zData["conn"])
                self.logger.info("[OK] Created zMigrations table using zCLI schema")
    
    def _update_rgb_on_access(self, table, row_id, zData):
        """Update RGB values when row is accessed."""
        cur = zData["cursor"]
        
        # R: Reset to 255 (fresh access) - will decay over time
        # G: Increment access frequency (with decay)
        cur.execute(f"""
            UPDATE {table} SET 
                weak_force_r = 255,  -- Reset to fresh (will decay over time)
                weak_force_g = MIN(255, weak_force_g + 5)  -- Increment access frequency
            WHERE id = ?
        """, (row_id,))
        
        zData["conn"].commit()
        self.logger.debug("[RGB] Updated RGB on access: %s.%s", table, row_id)
    
    def _update_rgb_on_migration(self, table, migration_type, success, zData):
        """Update B component based on migration results."""
        cur = zData["cursor"]
        
        if success:
            # Migration success = increase B (more stable)
            cur.execute(f"""
                UPDATE {table} SET 
                    weak_force_b = MIN(255, weak_force_b + 10)
            """)
            self.logger.info("[OK] Migration success - B increased for %s", table)
        else:
            # Migration failure = decrease B (less stable)
            cur.execute(f"""
                UPDATE {table} SET 
                    weak_force_b = MAX(0, weak_force_b - 20)
            """)
            self.logger.warning("[ERROR] Migration failed - B decreased for %s", table)
        
        zData["conn"].commit()
    
    def _apply_rgb_decay(self, zData):
        """Apply time-based decay to R and G components."""
        cur = zData["cursor"]
        
        # Get all user tables (exclude zCLI internal tables)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'z%'")
        user_tables = [row[0] for row in cur.fetchall()]
        
        total_rows_affected = 0
        
        for table in user_tables:
            # R: Natural decay (data gets "older" over time)
            # G: Access frequency decay (popularity fades)
            cur.execute(f"""
                UPDATE {table} SET 
                    weak_force_r = MAX(0, weak_force_r - 1),  -- Natural aging
                    weak_force_g = MAX(0, weak_force_g - 0.5) -- Access frequency fades
                WHERE weak_force_r > 0 OR weak_force_g > 0
            """)
            
            rows_affected = cur.rowcount
            total_rows_affected += rows_affected
            
            if rows_affected > 0:
                self.logger.debug("Applied RGB decay to %d rows in table '%s'", rows_affected, table)
        
        zData["conn"].commit()
        self.logger.info("[TIME] Applied RGB time decay to %d total rows across %d tables", total_rows_affected, len(user_tables))
        
        return total_rows_affected
    
    def get_rgb_health_report(self, zData):
        """Generate RGB health report using migration history."""
        cur = zData["cursor"]
        
        # Get all user tables (exclude zCLI internal tables)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'z%'")
        user_tables = [row[0] for row in cur.fetchall()]
        
        rgb_health = {}
        
        for table_name in user_tables:
            # Get current RGB state
            cur.execute(f"SELECT AVG(weak_force_r), AVG(weak_force_g), AVG(weak_force_b) FROM {table_name}")
            result = cur.fetchone()
            
            if result and result[0] is not None:  # Table has data
                avg_r, avg_g, avg_b = result
                health_score = self._calculate_health_score(avg_r, avg_g, avg_b)
                
                # Get migration history for this table
                cur.execute("""
                    SELECT COUNT(*), AVG(criticality_level), MAX(applied_at)
                    FROM zMigrations 
                    WHERE target_table = ?
                """, (table_name,))
                
                mig_result = cur.fetchone()
                migration_count = mig_result[0] if mig_result[0] else 0
                avg_criticality = mig_result[1] if mig_result[1] else 0
                last_migration = mig_result[2] if mig_result[2] else None
                
                rgb_health[table_name] = {
                    "avg_rgb": (round(avg_r, 2), round(avg_g, 2), round(avg_b, 2)),
                    "health_score": round(health_score, 3),
                    "migration_count": migration_count,
                    "avg_criticality": round(avg_criticality, 2) if avg_criticality else 0,
                    "last_migration": last_migration,
                    "status": self._get_table_status(health_score, avg_r, avg_g, avg_b)
                }
        
        return rgb_health
    
    def _calculate_health_score(self, r, g, b):
        """Calculate overall health score from RGB values."""
        # Normalize to 0-1 range, with higher values being better
        # White (255,255,255) = 1.0, Black (0,0,0) = 0.0
        return (r + g + b) / 765.0
    
    def _get_table_status(self, health_score, r, g, b):
        """Get human-readable status based on RGB values."""
        if health_score >= 0.8:
            return "EXCELLENT"
        elif health_score >= 0.6:
            return "GOOD"
        elif health_score >= 0.4:
            return "FAIR"
        elif health_score >= 0.2:
            return "POOR"
        else:
            return "CRITICAL"
    
    def suggest_migrations_for_rgb_health(self, zData, threshold=0.3):
        """Suggest migrations based on RGB health analysis."""
        cur = zData["cursor"]
        
        suggestions = []
        health_report = self.get_rgb_health_report(zData)
        
        for table_name, health_data in health_report.items():
            health_score = health_data["health_score"]
            avg_r, avg_g, avg_b = health_data["avg_rgb"]
            
            if health_score < threshold:
                # Low health score - suggest improvements
                suggestions.append({
                    "table": table_name,
                    "issue": f"Low health score ({health_score:.2f})",
                    "rgb_state": f"R={avg_r}, G={avg_g}, B={avg_b}",
                    "suggestions": self._generate_health_suggestions(avg_r, avg_g, avg_b),
                    "priority": "HIGH" if health_score < 0.2 else "MEDIUM"
                })
            
            elif avg_b < 100:  # Low migration stability
                suggestions.append({
                    "table": table_name,
                    "issue": f"Low migration stability (B={avg_b})",
                    "rgb_state": f"R={avg_r}, G={avg_g}, B={avg_b}",
                    "suggestions": ["Consider running schema migrations", "Check for missing migrations"],
                    "priority": "MEDIUM"
                })
            
            elif avg_g < 50:  # Low access frequency
                suggestions.append({
                    "table": table_name,
                    "issue": f"Low access frequency (G={avg_g})",
                    "rgb_state": f"R={avg_r}, G={avg_g}, B={avg_b}",
                    "suggestions": ["Data may be unused", "Consider archiving old data"],
                    "priority": "LOW"
                })
        
        return suggestions
    
    def _generate_health_suggestions(self, r, g, b):
        """Generate specific suggestions based on RGB values."""
        suggestions = []
        
        if r < 50:
            suggestions.append("Data is aging - consider refreshing or archiving")
        if g < 50:
            suggestions.append("Low usage - data may be stale or unused")
        if b < 100:
            suggestions.append("Migration issues - check schema consistency")
        
        if not suggestions:
            suggestions.append("RGB values are healthy")
        
        return suggestions
    
    def detect_changes(self, zForm, zData):
        """
        Detect schema changes between YAML and database.
        
        Args:
            zForm: Parsed YAML schema (dict)
            zData: Database connection object
        
        Returns:
            dict: Changes detected
                {
                    "new_columns": {
                        "table_name": [
                            {"name": "col", "type": "TEXT", "definition": {...}},
                            ...
                        ]
                    }
                }
        """
        self.logger.info("[Migration] Detecting schema changes...")
        
        # Get current database schema
        db_schema = self._introspect_database(zData)
        
        # Compare with YAML schema
        changes = {
            "new_columns": {},
            "new_indexes": {}
        }
        
        for table_name, table_fields in zForm.items():
            # Skip Meta and other non-table entries
            if table_name in ("Meta", "db_path") or not isinstance(table_fields, dict):
                continue
            
            # Check if table exists in database
            if table_name not in db_schema:
                self.logger.info("[Migration] Table '%s' doesn't exist in DB (will be created by zEnsureTables)", table_name)
                continue
            
            # Get columns currently in database
            db_columns = set(db_schema[table_name].keys())
            
            # Find new columns in YAML that don't exist in DB
            new_cols = []
            for field_name, field_def in table_fields.items():
                if not isinstance(field_def, dict):
                    continue
                
                if field_name not in db_columns:
                    # This column is in YAML but not in database
                    new_cols.append({
                        "name": field_name,
                        "definition": field_def
                    })
            
            if new_cols:
                changes["new_columns"][table_name] = new_cols
                self.logger.info("[Migration] Found %d new columns in table '%s'", len(new_cols), table_name)
            
            # Check for new indexes
            if "indexes" in table_fields:
                yaml_indexes = table_fields["indexes"]
                if isinstance(yaml_indexes, list):
                    # Get existing indexes from database
                    existing_indexes = self._get_table_indexes(table_name, zData)
                    existing_idx_names = {idx["name"] for idx in existing_indexes}
                    
                    # Find new indexes
                    new_indexes = []
                    for idx_def in yaml_indexes:
                        if isinstance(idx_def, dict):
                            idx_name = idx_def.get("name")
                            if idx_name and idx_name not in existing_idx_names:
                                new_indexes.append(idx_def)
                    
                    if new_indexes:
                        changes["new_indexes"][table_name] = new_indexes
                        self.logger.info("[Migration] Found %d new indexes for table '%s'", len(new_indexes), table_name)
        
        return changes
    
    def apply_migrations(self, changes, zForm, zData):
        """
        Apply detected schema changes to database.
        
        Args:
            changes: Changes dict from detect_changes()
            zForm: Parsed YAML schema
            zData: Database connection object
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not changes.get("new_columns") and not changes.get("new_indexes"):
            self.logger.info("[Migration] No changes to apply")
            return True
        
        self.logger.info("[Migration] Applying schema changes...")
        
        # Route to database-specific implementation
        if zData["type"] == "sqlite":
            return self._apply_sqlite_migrations(changes, zForm, zData)
        elif zData["type"] == "postgresql":
            return self._apply_postgres_migrations(changes, zForm, zData)
        else:
            self.logger.error("[Migration] Migrations not supported for database type: %s", zData["type"])
            return False
    
    def auto_migrate(self, zForm, zData):
        """
        Convenience method: detect and apply in one call.
        
        Args:
            zForm: Parsed YAML schema
            zData: Database connection object
        
        Returns:
            dict: Result with changes applied
        """
        changes = self.detect_changes(zForm, zData)
        
        if not changes.get("new_columns") and not changes.get("new_indexes"):
            return {"status": "no_changes", "message": "Schema is up to date"}
        
        success = self.apply_migrations(changes, zForm, zData)
        
        if success:
            total_cols = sum(len(cols) for cols in changes["new_columns"].values())
            total_idxs = sum(len(idxs) for idxs in changes["new_indexes"].values())
            message_parts = []
            if total_cols > 0:
                message_parts.append(f"{total_cols} new column(s)")
            if total_idxs > 0:
                message_parts.append(f"{total_idxs} new index(es)")
            
            return {
                "status": "success",
                "message": f"Added {', '.join(message_parts)}",
                "changes": changes
            }
        else:
            return {"status": "error", "message": "Migration failed"}
    
    # ============================================================
    # Database Introspection (Fork Pattern)
    # ============================================================
    
    def _introspect_database(self, zData):
        """
        Read current database schema structure.
        
        Forks based on database type.
        
        Returns:
            dict: {table_name: {column_name: {type, not_null, default, pk}}}
        """
        if zData["type"] == "sqlite":
            return self._introspect_sqlite(zData)
        elif zData["type"] == "postgresql":
            return self._introspect_postgres(zData)
        
        self.logger.warning("[Migration] Introspection not implemented for: %s", zData["type"])
        return {}
    
    def _introspect_sqlite(self, zData):
        """
        Read SQLite database schema using PRAGMA statements.
        
        Returns:
            dict: Schema structure
        """
        cur = zData["cursor"]
        schema = {}
        
        # Get all user tables (exclude sqlite internal tables)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cur.fetchall()]
        
        self.logger.info("[Migration] Found %d tables in database", len(tables))
        
        for table in tables:
            # Use PRAGMA table_info to get column details
            # Returns: (cid, name, type, notnull, dflt_value, pk)
            cur.execute(f"PRAGMA table_info({table})")
            columns = {}
            
            for row in cur.fetchall():
                cid, name, dtype, notnull, default, pk = row
                columns[name] = {
                    "type": dtype,
                    "not_null": bool(notnull),
                    "default": default,
                    "primary_key": bool(pk)
                }
            
            schema[table] = columns
            self.logger.debug("[Migration] Table '%s' has %d columns", table, len(columns))
        
        return schema
    
    def _get_table_indexes(self, table_name, zData):
        """
        Get list of indexes for a specific table.
        
        Args:
            table_name (str): Table name
            zData: Database connection object
        
        Returns:
            list: List of index info dicts
        """
        if zData["type"] == "sqlite":
            return self._get_sqlite_indexes(table_name, zData)
        elif zData["type"] == "postgresql":
            return self._get_postgres_indexes(table_name, zData)
        return []
    
    def _get_sqlite_indexes(self, table_name, zData):
        """Get indexes for a table in SQLite."""
        cur = zData["cursor"]
        indexes = []
        
        # Get index list for table
        cur.execute(f"PRAGMA index_list({table_name})")
        index_rows = cur.fetchall()
        
        for row in index_rows:
            # PRAGMA index_list returns: (seq, name, unique, origin, partial)
            seq, name, unique, origin, partial = row
            
            # Skip auto-created indexes for UNIQUE and PRIMARY KEY constraints
            if origin in ('u', 'pk'):
                continue
            
            # Get index columns
            cur.execute(f"PRAGMA index_info({name})")
            index_cols = [col_row[2] for col_row in cur.fetchall()]
            
            indexes.append({
                "name": name,
                "columns": index_cols,
                "unique": bool(unique),
                "partial": bool(partial)
            })
        
        return indexes
    
    def _get_postgres_indexes(self, table_name, zData):
        """Get indexes for a table in PostgreSQL."""
        cur = zData["cursor"]
        
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = %s
            AND schemaname = 'public'
        """, (table_name,))
        
        indexes = []
        for row in cur.fetchall():
            idx_name, idx_def = row
            # Skip primary key and unique constraint indexes
            if idx_name.endswith('_pkey') or 'UNIQUE' in idx_def.upper():
                continue
            
            indexes.append({
                "name": idx_name,
                "definition": idx_def
            })
        
        return indexes
    
    def _introspect_postgres(self, zData):
        """
        Read PostgreSQL database schema using information_schema.
        
        Returns:
            dict: Schema structure
        """
        cur = zData["cursor"]
        schema = {}
        
        # Query information_schema.columns
        cur.execute("""
            SELECT table_name, column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position
        """)
        
        for row in cur.fetchall():
            table, col_name, dtype, nullable, default = row
            
            if table not in schema:
                schema[table] = {}
            
            schema[table][col_name] = {
                "type": dtype,
                "not_null": nullable == 'NO',
                "default": default,
                "primary_key": False  # Would need separate query for PKs
            }
        
        return schema
    
    # ============================================================
    # Migration Application (Fork Pattern)
    # ============================================================
    
    def _apply_sqlite_migrations(self, changes, zForm, zData):
        """
        Apply migrations to SQLite database.
        
        Uses ALTER TABLE ADD COLUMN (supported in all SQLite versions).
        """
        cur = zData["cursor"]
        conn = zData["conn"]
        
        try:
            # Process each table with changes
            for table_name, new_columns in changes["new_columns"].items():
                for col_info in new_columns:
                    col_name = col_info["name"]
                    col_def = col_info["definition"]
                    
                    # Build SQL type from zCLI YAML definition
                    sql_type = self._get_sql_type(col_def)
                    
                    # Build ALTER TABLE statement
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {sql_type}"
                    
                    # Add DEFAULT if specified
                    if "default" in col_def and col_def["default"] is not None:
                        default_val = col_def["default"]
                        
                        # Handle special defaults
                        if isinstance(default_val, str) and default_val.lower() in ("now", "now()"):
                            sql += " DEFAULT CURRENT_TIMESTAMP"
                        elif isinstance(default_val, str):
                            sql += f" DEFAULT '{default_val}'"
                        else:
                            sql += f" DEFAULT {default_val}"
                    
                    # Execute migration
                    self.logger.info("[Migration] Executing: %s", sql)
                    cur.execute(sql)
                    self.logger.info("[Migration] [OK] Added column '%s' to table '%s'", col_name, table_name)
            
            # Commit all column changes
            conn.commit()
            self.logger.info("[Migration] All column migrations applied successfully")
            
            # Apply index changes
            if changes.get("new_indexes"):
                self.logger.info("[Migration] Creating new indexes...")
                for table_name, new_indexes in changes["new_indexes"].items():
                    # Import here to avoid circular dependency
                    from zOS.L3_Abstraction.n_zData.zData_modules.infrastructure import _create_indexes
                    _create_indexes(table_name, new_indexes, cur, conn)
                self.logger.info("[Migration] All index migrations applied successfully")
            
            return True
            
        except Exception as e:
            self.logger.error("[Migration] Migration failed: %s", e)
            conn.rollback()
            return False
    
    def _apply_postgres_migrations(self, changes, zForm, zData):
        """
        Apply migrations to PostgreSQL database.
        
        Same logic as SQLite (ALTER TABLE ADD COLUMN works the same way).
        """
        # PostgreSQL uses same ADD COLUMN syntax as SQLite!
        return self._apply_sqlite_migrations(changes, zForm, zData)
    
    # ============================================================
    # Helper Functions
    # ============================================================
    
    def _get_sql_type(self, field_def):
        """
        Convert zCLI YAML field definition to SQL type with constraints.
        
        Args:
            field_def: Field definition from YAML
        
        Returns:
            str: SQL type definition (e.g., "TEXT NOT NULL")
        """
        # Map zCLI types to SQL types
        raw_type = str(field_def.get("type", "str")).strip().lower()
        
        if raw_type.startswith("str") or raw_type == "enum":
            sql_type = "TEXT"
        elif raw_type.startswith("int"):
            sql_type = "INTEGER"
        elif raw_type.startswith("float"):
            sql_type = "REAL"
        elif raw_type.startswith("datetime"):
            sql_type = "TEXT"  # ISO8601 format
        elif raw_type == "blob":
            sql_type = "BLOB"
        elif raw_type == "numeric":
            sql_type = "NUMERIC"
        else:
            sql_type = "TEXT"  # Default fallback
        
        # Note: Cannot add NOT NULL or UNIQUE to existing tables in SQLite
        # These constraints require table recreation
        # For now, new columns are always nullable
        
        return sql_type


# ====================================================================
# Standalone Migration Functions
# ====================================================================

def auto_migrate_schema(zForm, zData, walker=None):
    """
    Convenience function: Auto-detect and apply schema changes.
    
    Can be called from zEnsureTables or manually.
    
    Args:
        zForm: Parsed YAML schema
        zData: Database connection object
        walker: Optional zCLI instance
    
    Returns:
        bool: True if migrations applied or no changes, False on error
    """
    migrator = ZMigrate(walker=walker)
    result = migrator.auto_migrate(zForm, zData)
    
    if result["status"] == "error":
        return False
    
    if result["status"] == "success":
        self.logger.info("[Migration] %s", result["message"])
    
    return True


def detect_schema_changes(zForm, zData, walker=None):
    """
    Detect changes without applying them.
    
    Args:
        zForm: Parsed YAML schema
        zData: Database connection object
        walker: Optional zCLI instance
    
    Returns:
        dict: Detected changes
    """
    migrator = ZMigrate(walker=walker)
    return migrator.detect_changes(zForm, zData)

