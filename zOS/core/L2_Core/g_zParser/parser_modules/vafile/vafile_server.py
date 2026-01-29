"""
Server File Parser - Parse zServer.*.yaml routing files (v1.5.4+)

This module parses declarative HTTP routing files for zServer, enabling
Flask blueprint-style route definitions with integrated RBAC.

Philosophy:
    "Routes are data, not code" - zServer follows zCLI's declarative approach

Structure:
    {
        "type": "server",
        "file_path": str,
        "meta": {
            "base_path": "./public",
            "default_route": "index.html",
            "error_pages": {403: "access_denied.html", 404: "404.html"}
        },
        "routes": {
            "/path": {
                "type": "static|dynamic|redirect",
                "file": "page.html",
                "description": "...",
                "zRBAC": {require_role: "admin"} or None
            }
        }
    }

Route Types:
    - static: Serve file from base_path
    - dynamic: Execute zFunc handler (future)
    - redirect: HTTP redirect (future)

RBAC Integration:
    Routes can have inline zRBAC metadata (same as zUI):
    - require_auth: true
    - require_role: "admin" or ["admin", "moderator"]
    - require_permission: "resource.action"

Examples:
    >>> data = {
    ...     "zMeta": {"base_path": "./public"},
    ...     "routes": {
    ...         "/": {"type": "static", "file": "index.html"},
    ...         "/admin": {
    ...             "type": "static",
    ...             "file": "admin.html",
    ...             "zRBAC": {"require_role": "admin"}
    ...         }
    ...     }
    ... }
    >>> result = parse_server_file(data, logger)
    >>> result["type"]
    "server"
    >>> result["routes"]["/admin"]["zRBAC"]
    {"require_role": "admin"}

Integration:
    - Called by parser_file.py when zServer.*.yaml detected
    - Used by zServer.py to load routing configuration
    - RBAC checked by router.py during request handling

Version: v1.5.4 Phase 2
"""

from zOS import Any, Dict, Optional

# =============================================================================
# MODULE CONSTANTS
# =============================================================================

# Import constants from centralized module (private - internal use only)
from ..parser_constants import (
    _FILE_TYPE_SERVER as FILE_TYPE_SERVER,
    _KEY_META as KEY_META,
    _KEY_ROUTES as KEY_ROUTES,
    _KEY_BASE_PATH as KEY_BASE_PATH,
    _KEY_DEFAULT_ROUTE as KEY_DEFAULT_ROUTE,
    _KEY_ERROR_PAGES as KEY_ERROR_PAGES,
    _KEY_TYPE as KEY_TYPE,
    _KEY_FILE as KEY_FILE,
    _KEY_CONTENT as KEY_CONTENT,
    _KEY_TEMPLATE as KEY_TEMPLATE,
    _KEY_CONTEXT as KEY_CONTEXT,
    _KEY_HANDLER as KEY_HANDLER,
    _KEY_TARGET as KEY_TARGET,
    _KEY_STATUS as KEY_STATUS,
    _KEY_DESCRIPTION as KEY_DESCRIPTION,
    _KEY_RBAC as KEY_RBAC,
    _KEY_ZVAFILE as KEY_ZVAFILE,
    _KEY_ZBLOCK as KEY_ZBLOCK,
    _ROUTE_TYPE_STATIC as ROUTE_TYPE_STATIC,
    _ROUTE_TYPE_CONTENT as ROUTE_TYPE_CONTENT,
    _ROUTE_TYPE_TEMPLATE as ROUTE_TYPE_TEMPLATE,
    _ROUTE_TYPE_DYNAMIC as ROUTE_TYPE_DYNAMIC,
    _ROUTE_TYPE_REDIRECT as ROUTE_TYPE_REDIRECT,
    _DEFAULT_BASE_PATH as DEFAULT_BASE_PATH,
    _DEFAULT_DEFAULT_ROUTE as DEFAULT_DEFAULT_ROUTE,
    _DEFAULT_ERROR_PAGES as DEFAULT_ERROR_PAGES,
    _LOG_MSG_PARSING_SERVER as LOG_MSG_PARSING_SERVER,
    _LOG_MSG_FOUND_ROUTES as LOG_MSG_FOUND_ROUTES,
    _LOG_MSG_ROUTE_WITH_RBAC as LOG_MSG_ROUTE_WITH_RBAC,
    _LOG_MSG_NO_ROUTES as LOG_MSG_NO_ROUTES,
)


# =============================================================================
# SERVER FILE PARSING
# =============================================================================

def parse_server_file(
    data: Dict[str, Any],
    logger: Any,
    file_path: Optional[str] = None,
    session: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parse server routing file with RBAC extraction.
    
    ⚠️ CRITICAL: This function is called by parser_file.py.
    Signature must remain stable.
    
    Args:
        data: Parsed YAML/JSON data from zServer file
        logger: Logger instance for diagnostic output
        file_path: Optional file path for logging
        session: Optional session dict (reserved for future use)
    
    Returns:
        Dict[str, Any]: Parsed server routing structure with format:
            {
                "type": "server",
                "file_path": str or None,
                "meta": {
                    "base_path": str,
                    "default_route": str,
                    "error_pages": {403: str, 404: str}
                },
                "routes": {
                    "/path": {
                        "type": str,
                        "file": str,
                        "description": str,
                        "zRBAC": dict or None
                    }
                }
            }
    
    Process Flow:
        1. Extract Meta section (base_path, default_route, error_pages)
        2. Extract routes section with RBAC metadata
        3. Return structured routing data
    
    Examples:
        >>> data = {
        ...     "zMeta": {"base_path": "./public"},
        ...     "routes": {
        ...         "/": {"type": "static", "file": "index.html"}
        ...     }
        ... }
        >>> result = parse_server_file(data, logger, "zServer.demo.yaml")
        >>> result["type"]
        "server"
        >>> result["meta"]["base_path"]
        "./public"
    
    Notes:
        - Missing Meta uses defaults
        - Routes without zRBAC are public
        - RBAC metadata is preserved for router.py
        - Session parameter reserved for future session-aware parsing
    """
    logger.info(LOG_MSG_PARSING_SERVER)
    
    # Extract Meta with defaults
    meta_raw = data.get(KEY_META, {})
    meta = {
        KEY_BASE_PATH: meta_raw.get(KEY_BASE_PATH, DEFAULT_BASE_PATH),
        KEY_DEFAULT_ROUTE: meta_raw.get(KEY_DEFAULT_ROUTE, DEFAULT_DEFAULT_ROUTE),
        KEY_ERROR_PAGES: meta_raw.get(KEY_ERROR_PAGES, DEFAULT_ERROR_PAGES.copy())
    }
    
    # Extract routes with RBAC
    routes_raw = data.get(KEY_ROUTES, {})
    routes = {}
    
    for route_path, route_data in routes_raw.items():
        if not isinstance(route_data, dict):
            logger.warning(f"[vafile_server] Skipping invalid route: {route_path}")
            continue
        
        # Extract RBAC metadata
        rbac = route_data.get(KEY_RBAC, None)
        
        # Build route entry
        route_entry = {
            KEY_TYPE: route_data.get(KEY_TYPE, ROUTE_TYPE_STATIC),
            KEY_RBAC: rbac
        }
        
        # Add type-specific fields
        if KEY_FILE in route_data:
            route_entry[KEY_FILE] = route_data[KEY_FILE]
        if KEY_CONTENT in route_data:
            route_entry[KEY_CONTENT] = route_data[KEY_CONTENT]
        if KEY_TEMPLATE in route_data:
            route_entry[KEY_TEMPLATE] = route_data[KEY_TEMPLATE]
        if KEY_CONTEXT in route_data:
            route_entry[KEY_CONTEXT] = route_data[KEY_CONTEXT]
        if KEY_HANDLER in route_data:
            route_entry[KEY_HANDLER] = route_data[KEY_HANDLER]
        if KEY_TARGET in route_data:
            route_entry[KEY_TARGET] = route_data[KEY_TARGET]
        if KEY_STATUS in route_data:
            route_entry[KEY_STATUS] = route_data[KEY_STATUS]
        if KEY_DESCRIPTION in route_data:
            route_entry[KEY_DESCRIPTION] = route_data[KEY_DESCRIPTION]
        if KEY_ZVAFILE in route_data:
            route_entry[KEY_ZVAFILE] = route_data[KEY_ZVAFILE]
        if "zVaFolder" in route_data:  # zWalker folder path
            route_entry["zVaFolder"] = route_data["zVaFolder"]
        if KEY_ZBLOCK in route_data:
            route_entry[KEY_ZBLOCK] = route_data[KEY_ZBLOCK]
        if "auto_discover_blocks" in route_data:  # Smart Walker Routes (auto-discovery)
            route_entry["auto_discover_blocks"] = route_data["auto_discover_blocks"]
        if "data" in route_data:  # JSON route data
            route_entry["data"] = route_data["data"]
        
        routes[route_path] = route_entry
        
        # Log RBAC routes
        if rbac:
            logger.debug(LOG_MSG_ROUTE_WITH_RBAC, route_path, rbac)
    
    # Log summary
    route_count = len(routes)
    if route_count > 0:
        logger.info(LOG_MSG_FOUND_ROUTES, route_count)
    else:
        logger.warning(LOG_MSG_NO_ROUTES)
    
    return {
        "type": FILE_TYPE_SERVER,
        "file_path": file_path,
        "meta": meta,
        "routes": routes
    }

