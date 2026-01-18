# zCLI/subsystems/zConfig/zConfig_modules/config_zenv.py
"""
zEnv - Declarative Environment Configuration Loader

THE zCLI WAY: Replace traditional .env files with declarative config files.

This module provides a secure, declarative alternative to python-dotenv while
maintaining backward compatibility. It parses zEnv config files (.zolo, .yaml, .json)
and injects values into os.environ (just like dotenv), ensuring security and standard practices.

Key Features:
- Parse ZOLO/YAML/JSON declarative config files
- Auto-detect file format (.zolo preferred, .yaml fallback)
- Flatten nested structures to JSON strings for complex values
- Priority-based loading (base → environment-specific)
- Secure: Values injected into os.environ (process-isolated)
- Backward compatible: Falls back to dotenv if no config files found

File Format:
-----------
zEnv.base.zolo         - Base configuration (preferred - string-first, type hints)
zEnv.base.yaml         - Base configuration (fallback)
zEnv.development.zolo  - Development-specific overrides
zEnv.production.zolo   - Production-specific overrides
zEnv.testing.zolo      - Testing-specific overrides

Priority Order:
--------------
1. zEnv.{environment}.zolo (highest priority - environment-specific, preferred)
2. zEnv.{environment}.yaml (fallback if .zolo not found)
3. zEnv.base.zolo          (base configuration, preferred)
4. zEnv.base.yaml          (fallback if .zolo not found)
5. .zEnv.{environment}     (legacy dotenv fallback)
6. .zEnv                   (legacy dotenv base)

Example:
--------
# zEnv.base.zolo
ZNAVBAR:
  zVaF:
  zAccount:
    zRBAC:
      require_role: [zAdmin]

AWS_SECRET_KEY: secret123  # No quotes needed (string-first default)
DEBUG(bool): true          # Explicit type hint

After loading:
os.getenv("ZNAVBAR")  # '{"zVaF": null, "zAccount": {"zRBAC": {"require_role": ["zAdmin"]}}}'
os.getenv("AWS_SECRET_KEY")  # "secret123"
os.getenv("DEBUG")  # "true"

Security:
---------
- Values stored in os.environ (process-isolated, standard practice)
- No serialization risk (secrets not in Python objects)
- Works with Docker, K8s, systemd
- Audit trail via OS logging
"""

from zOS import os, sys, yaml, json, Path, Any, Dict, Optional, List, Union
from pathlib import Path

# Module constants
LOG_PREFIX = "[zEnv]"

# zEnv file extensions (priority order - consistent with zParser)
ZENV_EXT_ZOLO = ".zolo"
ZENV_EXT_YAML = ".yaml"
ZENV_EXTENSIONS = [
    ZENV_EXT_ZOLO,    # Try .zolo first (new DRY format)
    ZENV_EXT_YAML      # Fall back to .yaml
]

class zEnv:
    """
    Declarative environment configuration loader (THE zCLI WAY).
    
    Replaces python-dotenv with YAML/JSON declarative configs while
    maintaining security through os.environ injection.
    """
    
    def __init__(self, workspace_dir: str, environment: str = "development", logger=None):
        """
        Initialize zEnv loader.
        
        Args:
            workspace_dir: Path to workspace directory containing zEnv files
            environment: Current environment (development, production, testing)
            logger: Optional logger instance for debug output
        """
        self.workspace_dir = Path(workspace_dir)
        self.environment = environment.lower()
        self.logger = logger
        self._loaded_files: List[str] = []
        
    def load(self) -> bool:
        """
        Load environment configuration from config files into os.environ.
        
        Auto-detects file format (.zolo preferred, .yaml fallback).
        Priority order:
        1. zEnv.base.{zolo|yaml} (base configuration)
        2. zEnv.{environment}.{zolo|yaml} (environment-specific overrides)
        
        Returns:
            bool: True if any config files were loaded, False if no files found
            
        Note:
            Does NOT fall back to dotenv - that's handled by config_paths.load_dotenv()
            This ensures declarative files always take precedence when they exist.
        """
        # Find files with auto-detection
        base_file = self._find_file_with_extension("zEnv.base")
        env_file = self._find_file_with_extension(f"zEnv.{self.environment}")
        
        # Delegate to load_files()
        return self.load_files(base_file, env_file)
    
    def load_files(self, base_file: Optional[Path], env_file: Optional[Path]) -> bool:
        """
        Load specified config files into os.environ.
        
        This is the execution layer - it loads whatever files it's told to load.
        File detection happens in config_paths.py (the decision layer).
        
        Args:
            base_file: Path to base config file (or None)
            env_file: Path to environment config file (or None)
        
        Returns:
            bool: True if any files were loaded successfully
        """
        any_loaded = False
        
        # Load base configuration
        if base_file:
            base_config = self._load_file(base_file)
            if base_config:
                self._inject_to_environ(base_config)
                self._loaded_files.append(str(base_file))
                any_loaded = True
                self._log(f"✅ Loaded base config from {base_file.name}")
        
        # Load environment-specific configuration (overrides base)
        if env_file:
            env_config = self._load_file(env_file)
            if env_config:
                self._inject_to_environ(env_config)
                self._loaded_files.append(str(env_file))
                any_loaded = True
                self._log(f"✅ Loaded {self.environment} config from {env_file.name}")
        
        if not any_loaded:
            self._log("ℹ️  No zEnv config files found in workspace")
        
        return any_loaded
    
    def _find_file_with_extension(self, base_name: str) -> Optional[Path]:
        """
        Find a file by trying extensions in priority order.
        
        Args:
            base_name: Base filename without extension (e.g., "zEnv.base")
        
        Returns:
            Path to file if found, None otherwise
        """
        for ext in ZENV_EXTENSIONS:
            candidate = self.workspace_dir / f"{base_name}{ext}"
            if candidate.exists():
                return candidate
        return None
    
    def _load_file(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Load and parse a YAML, JSON, or ZOLO file.
        
        Args:
            file_path: Path to the file to load (string or Path object)
        
        Returns:
            Dict containing parsed data, or None if file doesn't exist or parse failed
        """
        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check file extension
            file_extension = file_path.suffix
            
            # For .zolo files, use the standalone zolo library (like PyYAML for .yaml)
            if file_extension == ZENV_EXT_ZOLO:
                try:
                    import zolo
                    data = zolo.loads(content, file_extension=file_extension)
                    if data is None:
                        self._log(f"⚠️  {file_path.name} is empty")
                        return None
                    return data
                except ImportError:
                    self._log(f"⚠️  zolo library not installed, falling back to YAML parser for {file_path.name}")
                    # Fallback to YAML if zolo not installed
                    try:
                        data = yaml.safe_load(content)
                        if data is None:
                            self._log(f"⚠️  {file_path.name} is empty")
                            return None
                        return data
                    except yaml.YAMLError as e:
                        self._log(f"❌ Failed to parse {file_path.name}: {e}")
                        return None
                except Exception as e:
                    self._log(f"❌ Failed to parse .zolo file {file_path.name}: {e}")
                    return None
            
            # For .yaml and .json files, try YAML first (supports both)
            try:
                data = yaml.safe_load(content)
                if data is None:
                    self._log(f"⚠️  {file_path.name} is empty")
                    return None
                return data
            except yaml.YAMLError as e:
                # Fallback to JSON
                try:
                    data = json.loads(content)
                    return data
                except json.JSONDecodeError as e2:
                    self._log(f"❌ Failed to parse {file_path.name}: YAML error: {e}, JSON error: {e2}")
                    return None
        
        except Exception as e:
            self._log(f"❌ Failed to read {file_path.name}: {e}")
            return None
    
    def _inject_to_environ(self, config: Dict[str, Any]) -> None:
        """
        Inject configuration values into os.environ.
        
        Nested structures (dicts, lists) are flattened to JSON strings.
        Simple values are converted to strings.
        
        Args:
            config: Dictionary of configuration values to inject
        """
        for key, value in config.items():
            if value is None:
                # Skip None values (don't set env var)
                continue
            
            if isinstance(value, (dict, list)):
                # Flatten complex structures to JSON strings
                os.environ[key] = json.dumps(value, ensure_ascii=False)
                self._log(f"  {key}: <complex> (JSON string)")
            elif isinstance(value, bool):
                # Convert boolean to lowercase string (true/false)
                os.environ[key] = str(value).lower()
                self._log(f"  {key}: {value}")
            else:
                # Simple values to strings
                os.environ[key] = str(value)
                self._log(f"  {key}: {value}")
    
    
    def _log(self, message: str) -> None:
        """
        Log a message (if logger is available).
        
        Args:
            message: Message to log
        """
        if self.logger:
            self.logger.framework.info(f"{LOG_PREFIX} {message}")
        # Silently skip if no logger (during bootstrap)


def load_zenv(workspace_dir: str, environment: str = "development", logger=None) -> bool:
    """
    Convenience function to load zEnv configuration.
    
    Args:
        workspace_dir: Path to workspace directory containing zEnv files
        environment: Current environment (development, production, testing)
        logger: Optional logger instance
    
    Returns:
        bool: True if YAML files were loaded, False if fell back to dotenv
    
    Example:
        >>> from zOS.L1_Foundation.a_zConfig.zConfig_modules.config_zenv import load_zenv
        >>> load_zenv("/path/to/workspace", "development")
        True
    """
    loader = zEnv(workspace_dir, environment, logger)
    return loader.load()

