# zCLI/subsystems/zLoader/loader_modules/__init__.py

"""
Public API aggregator for zLoader modules.

This module serves as Tier 4 (Package Aggregator) in the zLoader architecture,
exposing the public API from Tiers 1-3 (Foundation, Cache Implementations, Cache
Orchestrator). It provides a single import location for the zLoader facade to access
all necessary components for file loading and caching operations.

Purpose
-------
The loader_modules package aggregator provides a clean, organized public API for
zLoader's internal components. It exposes three levels of abstraction:
    - Primary API: CacheOrchestrator (unified cache interface)
    - Advanced API: Direct cache implementations (custom cache logic)
    - Foundation API: load_file_raw (bypass cache entirely)

Architecture
------------
**Tier 4 - Package Aggregator (Exposes Public APIs)**
    - Position: Aggregation tier between internal modules and facade
    - Aggregates: Tier 1-3 (Foundation, Cache Implementations, Cache Orchestrator)
    - Used By: zLoader.py facade (Tier 5)
    - Purpose: Single import location + public API exposure + multi-level access

**6-Tier Architecture**:
    - Tier 1: Foundation (loader_io.py - Raw file I/O)
    - Tier 2: Cache Implementations (SystemCache, PinnedCache, SchemaCache, PluginCache)
    - Tier 3: Cache Orchestrator (CacheOrchestrator - Unified cache router)
    - Tier 4: Package Aggregator ← THIS MODULE
    - Tier 5: Facade (zLoader.py - Public interface to zCLI)
    - Tier 6: Package Root (__init__.py - zLoader package entry point)

Public API Exports
------------------
This module exports 10 components organized by tier:

**Tier 6 - User Utilities**:
    - cache_utils: User-facing cache inspection and management utilities. Provides
      get_cached_files(), get_cached_files_count(), clear_system_cache(), and
      create_shortcut_from_cache() for interactive and programmatic cache control.

**Tier 3 - Cache Orchestrator**:
    - CacheOrchestrator: Unified cache router for all cache operations. Routes requests
      to appropriate cache tier (system, pinned, schema, plugin) based on cache_type
      parameter. Supports batch operations (clear all, get stats all).

**Tier 2 - Cache Implementations**:
    - SystemCache: UI/config file cache with LRU eviction (max_size=100). For frequently
      accessed YAML files (zUI, zSchema, zConfig).
    - PinnedCache: User alias cache with no eviction. For user-loaded aliases via zLoad
      command. Highest priority, never auto-evicts.
    - SchemaCache: DB connection cache with dual storage (in-memory connections + session
      metadata). For database connections and transaction management.
    - PluginCache: Plugin module cache with collision detection, session injection, mtime
      invalidation, LRU eviction (max_size=50). For dynamically loaded plugin modules.

**Tier 1 - Foundation I/O**:
    - load_file_raw: Raw file I/O function that bypasses all caching. Returns file
      contents as string. Used when cache bypass is needed or as fallback.

Usage Patterns
--------------
**Primary API (Recommended)**:
    Use CacheOrchestrator for most use cases. It provides a unified interface to all
    cache tiers and handles routing automatically:
        >>> from zOS.L2_Core.h_zLoader.loader_modules import CacheOrchestrator
        >>> cache = CacheOrchestrator(session, logger, zcli)
        >>> data = cache.get("zUI.users.yaml", cache_type="system")

**Advanced API (Custom Implementations)**:
    Import direct cache implementations for custom cache logic or when you need
    direct access to specific cache tier features:
        >>> from zOS.L2_Core.h_zLoader.loader_modules import SystemCache, PinnedCache
        >>> system_cache = SystemCache(session, logger, max_size=50)
        >>> pinned_cache = PinnedCache(session, logger)

**Foundation API (Bypass Cache)**:
    Use load_file_raw to bypass all caching and read files directly from disk:
        >>> from zOS.L2_Core.h_zLoader.loader_modules import load_file_raw
        >>> content = load_file_raw("/path/to/file.yaml")

**User Utilities API (Cache Management)**:
    Use cache_utils module for cache inspection and management:
        >>> from zOS.L2_Core.h_zLoader.loader_modules import cache_utils
        >>> files = cache_utils.get_cached_files(zcli)
        >>> stats = cache_utils.get_cached_files_count(zcli)
        >>> cache_utils.clear_system_cache(zcli)

External Usage
--------------
**Used By**:
    - zCLI/subsystems/zLoader/zLoader.py (Facade - Tier 5)
      Usage: Imports CacheOrchestrator and load_file_raw
      Purpose: Provides file loading and caching to zLoader facade

See Also
--------
- zLoader.py: Uses CacheOrchestrator and load_file_raw from this module
- cache_orchestrator.py: Tier 3 orchestrator (primary API)
- loader_cache_*.py: Tier 2 cache implementations (advanced API)
- loader_io.py: Tier 1 foundation I/O (foundation API)

Version History
---------------
- v1.5.9: Added cache_utils (Tier 6) for user-facing cache management utilities
- v1.5.4: Industry-grade upgrade (comprehensive docs, import organization,
          __all__ inline comments, usage guidance, architecture context)
- v1.5.3: Original implementation (6 exports: orchestrator + 4 caches + load_file_raw)
"""

# ============================================================================
# IMPORTS - Organized by Tier
# ============================================================================

# Tier 3: Cache Orchestrator
from .cache_orchestrator import CacheOrchestrator

# Tier 2: Cache Implementations
from .loader_cache_system import SystemCache
from .loader_cache_pinned import PinnedCache
from .loader_cache_schema import SchemaCache
from .loader_cache_plugin import PluginCache

# Tier 1: Foundation I/O
from .loader_io import load_file_raw

# Tier 6: User Utilities
from . import cache_utils

# ============================================================================
# PUBLIC API EXPORTS
# ============================================================================

__all__ = [
    "CacheOrchestrator",  # Tier 3: Unified cache router (PRIMARY API)
    "SystemCache",        # Tier 2: UI/config file cache (ADVANCED API)
    "PinnedCache",        # Tier 2: User alias cache (ADVANCED API)
    "SchemaCache",        # Tier 2: DB connection cache (ADVANCED API)
    "PluginCache",        # Tier 2: Plugin module cache (ADVANCED API)
    "load_file_raw",      # Tier 1: Raw file I/O (FOUNDATION API)
    "cache_utils",        # Tier 6: User-facing cache utilities (USER API)
]
