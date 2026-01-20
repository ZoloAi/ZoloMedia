# zOS/core/L2_Core/e_zDispatch/dispatch_modules/data_resolver.py

"""
Data Resolution Module for zDispatch Subsystem.

This module provides the DataResolver class, which handles block-level _data queries
defined in zUI files. It supports 3 query formats with session-based interpolation
and security filtering.

Extracted from dispatch_launcher.py as part of Phase 1 refactoring (Leaf Module).
This module has no internal dispatch dependencies - only depends on zData subsystem.

Supported Query Formats:
    1. Declarative dict: {model: "...", where: {...}, limit: 1}
    2. Shorthand string: "@.models.zSchema.contacts" (backward compatibility)
    3. Explicit zData: {zData: {action: "read", model: "..."}}

Features:
    - Session-based %session.* interpolation in WHERE clauses
    - Auto-filtering by authenticated user ID (shorthand format)
    - Silent query execution (no display output)
    - Limit=1 automatic unwrapping (returns dict instead of list)

Usage Example:
    resolver = DataResolver(zcli)
    
    # In dispatch flow
    if "_data" in zHorizontal:
        resolved_data = resolver.resolve_block_data(zHorizontal["_data"], context)
        context["_resolved_data"] = resolved_data

Integration:
    - zData: Query execution via zcli.data.handle_request()
    - zAuth: Session access via zcli.session
    - zLogger: Framework logging via zcli.logger

Thread Safety:
    - Read-only session access (no mutation)
    - Stateless query building (pure functions)
    - Safe for concurrent execution

Performance:
    - Single-pass query building
    - Lazy evaluation (only executes queries present in _data block)
    - Silent mode (no display overhead)
"""

from zOS import Any, Dict

class DataResolver:
    """
    Resolves block-level _data queries for zUI files.
    
    This class handles the execution of data queries defined in the _data block of
    zUI files, supporting multiple query formats and session-based interpolation.
    
    Attributes:
        zcli: Root zCLI instance (provides access to session, data, logger)
    
    Methods:
        resolve_block_data(): Main entry point - execute all queries in _data block
        
        Private query builders:
        _build_declarative_query(): Build from declarative dict format
        _build_shorthand_query(): Build from shorthand string format
        _interpolate_session_values(): Interpolate %session.* in WHERE clause
        _execute_data_query(): Execute query and extract result
    
    Example:
        resolver = DataResolver(zcli)
        
        # Declarative format
        data_block = {
            "user": {
                "model": "@.models.zSchema.users",
                "where": {"id": "%session.zAuth.applications.zCloud.id"},
                "limit": 1
            }
        }
        
        results = resolver.resolve_block_data(data_block, context)
        # Returns: {"user": {"id": 123, "name": "John", ...}}
    """
    
    def __init__(self, zcli: Any) -> None:
        """
        Initialize data resolver with zCLI instance.
        
        Args:
            zcli: Root zCLI instance (provides session, data, logger)
        
        Example:
            resolver = DataResolver(zcli)
        """
        self.zcli = zcli
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def resolve_block_data(
        self,
        data_block: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute data queries defined in block-level _data (ORCHESTRATOR).
        
        This method processes all queries in the _data block and returns a dictionary
        of results. Each query is executed independently, with errors isolated to
        individual queries.
        
        Supports 3 query formats:
        1. Declarative dict: {model: "...", where: {...}, limit: 1}
        2. Shorthand string: "@.models.zSchema.contacts"
        3. Explicit zData: {zData: {action: "read", model: "..."}}
        
        Args:
            data_block: _data section from zUI block
            context: Current execution context (passed to zData)
        
        Returns:
            Dictionary of query results: {"user": {...}, "stats": [...]}
        
        Examples:
            # Declarative format (recommended)
            _data:
              user:
                model: "@.models.zSchema.users"
                where: {id: "%session.zAuth.applications.zCloud.id"}
                limit: 1
            
            # Shorthand format (backward compatibility)
            _data:
              user: "@.models.zSchema.contacts"
            
            # Explicit zData format
            _data:
              stats:
                zData:
                  action: read
                  model: "@.models.zSchema.user_stats"
        
        Notes:
            - Each query executes in silent mode (no display output)
            - Session interpolation (%session.*) happens automatically
            - Errors are caught per-query (returns None for failed queries)
            - Results are logged at framework debug level
        """
        results = {}
        
        for key, query_def in data_block.items():
            try:
                # Format 1: Declarative dict
                if isinstance(query_def, dict) and "model" in query_def:
                    query_def = self._build_declarative_query(query_def)
                
                # Format 2: Shorthand string
                elif isinstance(query_def, str) and query_def.startswith('@.models.'):
                    query_def = self._build_shorthand_query(key, query_def)
                
                # Format 3: Explicit zData block
                if isinstance(query_def, dict) and "zData" in query_def:
                    results[key] = self._execute_data_query(key, query_def, context)
                else:
                    self.zcli.logger.framework.warning(f"[DataResolver] Invalid _data entry: {key}")
                    results[key] = None
                    
            except Exception as e:
                self.zcli.logger.framework.error(f"[DataResolver] Query '{key}' failed: {e}")
                results[key] = None
        
        return results
    
    # ========================================================================
    # PRIVATE QUERY BUILDERS
    # ========================================================================
    
    def _build_declarative_query(
        self,
        query_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build zData query from declarative dict format.
        
        Declarative format is the recommended approach for _data queries, providing
        explicit control over model, WHERE clause, and limit.
        
        Args:
            query_def: Declarative query (model + where + limit)
        
        Returns:
            zData query dict (ready for execution)
        
        Example:
            query = {"model": "@.models.zSchema.users", "where": {"id": 123}, "limit": 1}
            result = _build_declarative_query(query)
            # Returns: {"zData": {"action": "read", "model": "...", "options": {...}}}
        
        Notes:
            - Interpolates %session.* values in WHERE clause automatically
            - Defaults to limit=1 for single record queries
            - WHERE clause is optional (empty dict if not provided)
        """
        model = query_def.get("model")
        where_clause = query_def.get("where", {})
        
        # Interpolate %session.* values in WHERE clause
        interpolated_where = self._interpolate_session_values(where_clause)
        
        return {
            "zData": {
                "action": "read",
                "model": model,
                "options": {
                    "where": interpolated_where if interpolated_where else {},
                    "limit": query_def.get("limit", 1)
                }
            }
        }
    
    def _build_shorthand_query(
        self,
        key: str,
        model_path: str
    ) -> Dict[str, Any]:
        """
        Build zData query from shorthand string format.
        
        Shorthand format is backward compatible but less flexible. It auto-filters
        by authenticated user ID using hardcoded 'id' field.
        
        Format: user: "@.models.zSchema.contacts"
        Expands to: {action: "read", model: "...", where: {id: <user_id>}, limit: 1}
        
        Args:
            key: Query key (for logging/warnings)
            model_path: Model path string (@.models.*)
        
        Returns:
            zData query dict with auth filtering
        
        Notes:
            - Backward compatibility (hardcodes 'id' field)
            - Emits warning about hardcoded field
            - Auto-filters by authenticated user ID from session
            - Supports 3-layer auth architecture (app-specific → platform → fallback)
        """
        self.zcli.logger.framework.warning(
            f"[DataResolver] Shorthand syntax '{key}: \"{model_path}\"' uses hardcoded 'id' field. "
            f"Consider using declarative syntax with explicit WHERE clause."
        )
        
        # Get authenticated user ID from zAuth
        zauth = self.zcli.session.get('zAuth', {})
        active_app = zauth.get('active_app')
        
        # Try app-specific auth first
        if active_app:
            app_auth = zauth.get('applications', {}).get(active_app, {})
            user_id = app_auth.get('id')
        else:
            # Fallback to Zolo platform auth
            user_id = zauth.get('zSession', {}).get('id')
        
        return {
            "zData": {
                "action": "read",
                "model": model_path,
                "options": {
                    "where": {"id": user_id} if user_id else {"id": 0},
                    "limit": 1
                }
            }
        }
    
    def _interpolate_session_values(
        self,
        where_clause: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Interpolate %session.* values in WHERE clause.
        
        This enables dynamic filtering based on current session state without
        hardcoding user IDs or other session values in YAML files.
        
        Args:
            where_clause: WHERE clause dict (may contain %session.* values)
        
        Returns:
            WHERE clause with interpolated session values
        
        Example:
            where = {"id": "%session.zAuth.applications.zCloud.id"}
            result = _interpolate_session_values(where)
            # Returns: {"id": 123}  (actual user ID from session)
        
        Notes:
            - Navigates session dict using dot notation
            - Returns None if path doesn't exist (secure default)
            - Logs interpolation at framework debug level
            - Non-interpolated values pass through unchanged
        """
        interpolated = {}
        for field, value in where_clause.items():
            if isinstance(value, str) and value.startswith("%session."):
                # Extract session path: %session.zAuth.applications.zCloud.id
                session_path = value[9:]  # Remove "%session." prefix
                path_parts = session_path.split('.')
                
                # Navigate session dict
                session_value = self.zcli.session
                for part in path_parts:
                    if isinstance(session_value, dict):
                        session_value = session_value.get(part)
                    else:
                        session_value = None
                        break
                
                interpolated[field] = session_value
                self.zcli.logger.framework.debug(
                    f"[DataResolver] Interpolated {value} → {session_value}"
                )
            else:
                interpolated[field] = value
        
        return interpolated
    
    def _execute_data_query(
        self,
        key: str,
        query_def: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute zData query and extract result.
        
        This method executes the query in silent mode (no display output) and
        automatically unwraps single-record results for convenience.
        
        Args:
            key: Query key (for logging)
            query_def: zData query dict (ready for execution)
            context: Execution context (passed to zData)
        
        Returns:
            Query result:
            - Dict for single record (limit=1)
            - List for multiple records
            - None if query failed
        
        Notes:
            - Sets silent=True to suppress display output
            - Works in any zMode (Terminal, Bifrost)
            - Extracts first record for limit=1 queries (returns dict instead of list)
            - Logs result type and count at framework debug level
        """
        # Execute zData query in SILENT mode
        query_def["zData"]["silent"] = True
        result = self.zcli.data.handle_request(query_def["zData"], context)
        
        # Extract first record if limit=1
        limit = query_def["zData"].get("options", {}).get("limit")
        if isinstance(result, list) and limit == 1 and len(result) > 0:
            final_result = result[0]  # Return dict instead of list
        else:
            final_result = result
        
        # Log result
        result_type = type(final_result).__name__
        result_count = len(result) if isinstance(result, list) else 1
        self.zcli.logger.framework.debug(
            f"[DataResolver] Query '{key}' returned {result_type} ({result_count} records)"
        )
        
        return final_result
