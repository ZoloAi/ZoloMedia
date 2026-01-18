# zCLI/subsystems/zLoader/__init__.py

"""
zLoader subsystem - File loading and caching with zParser delegation.

This module serves as the package root (Tier 6) for the zLoader subsystem,
providing the entry point for file loading operations with intelligent caching.
zLoader handles zVaFiles (UI, Schema, Config) with delegation to zParser for
path resolution and content parsing.

Purpose
-------
The zLoader package root serves as Tier 6 (Package Root) in the zLoader architecture,
providing the main entry point for importing zLoader into zCLI. It exposes the zLoader
facade class which provides a unified interface for file loading and caching.

Architecture
------------
**Tier 6 - Package Root (Entry Point)**
    - Position: Top-level package entry point
    - Exposes: zLoader facade class (Tier 5)
    - Used By: zCLI.py (imports zLoader for zcli.loader attribute)
    - Purpose: Package initialization + public API exposure

**6-Tier Architecture**:
    - Tier 1: Foundation (loader_io.py - Raw file I/O)
    - Tier 2: Cache Implementations (SystemCache, PinnedCache, SchemaCache, PluginCache)
    - Tier 3: Cache Orchestrator (CacheOrchestrator - Unified cache router)
    - Tier 4: Package Aggregator (loader_modules/__init__.py - Public API exposure)
    - Tier 5: Facade (zLoader.py - Public interface to zCLI)
    - Tier 6: Package Root ← THIS MODULE

Public API
----------
**Exported Classes**:
    - zLoader: Main facade class for file loading and caching

Usage Patterns
--------------
**Standard Import (in zCLI.py)**:
    >>> from zOS.L2_Core.h_zLoader import zLoader
    >>> self.loader = zLoader(self)
    >>> # Used as: zcli.loader.handle(zPath)

**Direct Access (in subsystems)**:
    >>> # In zDispatch:
    >>> raw_zFile = self.zcli.loader.handle(zVaFile)
    >>>
    >>> # In zNavigation:
    >>> target_ui = walker.loader.handle(target_file)

Integration Points
------------------
**Week 6.6 (zDispatch)**:
    - dispatch_launcher.py: self.zcli.loader.handle(zVaFile)
    - dispatch_modifiers.py: self.zcli.loader.handle(zVaFile)

**Week 6.7 (zNavigation)**:
    - navigation_linking.py: walker.loader.handle()

**Week 6.8 (zParser)**:
    - Delegates to zParser for path resolution and parsing

Layer Position
--------------
Layer 1, Position 6 (zLoader - Tier 6 Package Root)
    - Tier 1-5: Internal components (I/O, caches, orchestrator, aggregator, facade)
    - Tier 6: Package Root ← THIS MODULE

See Also
--------
- zLoader.py: Main facade class (Tier 5)
- loader_modules/__init__.py: Package aggregator (Tier 4)
- cache_orchestrator.py: Cache orchestrator (Tier 3)

Version History
---------------
- v1.5.4: Industry-grade upgrade (comprehensive docs, architecture context,
          noqa explanation, integration points documentation)
- v1.5.3: Original implementation (basic package initialization)
"""

from .zLoader import zLoader  # noqa: F401  # Re-exported for public API

__all__ = ['zLoader']
