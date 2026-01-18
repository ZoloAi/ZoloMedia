# zCLI/subsystems/zConfig/zConfig_modules/helpers/config_helpers.py
"""Shared helper functions for configuration loading across zConfig subsystems."""

import logging
from zOS import yaml, Path, Dict, Any, Callable, Optional
import shutil

# Module-level logger
logger = logging.getLogger(__name__)

# Module constants
SOURCE_USER = "user"
LOG_PREFIX = "[ConfigHelpers]"
ZUI_CLI_SYS_FILENAME = "zUI.zcli_sys.yaml"
ZMIGRATION_SCHEMA_FILENAME = "zSchema.zMigration.yaml"

def ensure_user_directories(paths: Any) -> None:
    """
    Ensure user configuration directories exist (zConfigs, zUIs, zSchemas).
    
    Creates user_config_dir subdirectories if they don't already exist:
    - zConfigs: Configuration files (zConfig.machine.yaml, zConfig.environment.yaml)
    - zUIs: User-customized UI definition files
    - zSchemas: System schema templates (zSchema.zMigration.yaml)
    
    Args:
        paths: zConfigPaths instance
        
    Notes:
        - Called during zConfig initialization
        - Uses exist_ok=True for safe repeated calls
        - Silently handles errors (non-critical operation)
    """
    try:
        # Ensure zConfigs directory exists
        paths.user_zconfigs_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure zUIs directory exists
        paths.user_zuis_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure zSchemas directory exists
        paths.user_zschemas_dir.mkdir(parents=True, exist_ok=True)
        
    except Exception as e:
        logger.warning("%s Failed to create user directories: %s", LOG_PREFIX, e)

def ensure_app_directory(paths: Any, zSpark: Optional[Dict[str, Any]] = None) -> Optional[Path]:
    """
    Create app root directory if app_storage is enabled in zSpark.
    
    Simple opt-in: Creates Apps/{title}/ root folder.
    App creates subdirectories as needed.
    
    Args:
        paths: zConfigPaths instance
        zSpark: zSpark configuration dict
    
    Returns:
        Path: App root directory if created, None if not enabled
    
    Example:
        zSpark = {"title": "zCloud", "app_storage": True}
        → Creates ~/Library/Application Support/zolo-zcli/Apps/zCloud/
    
    Notes:
        - Only creates directory if app_storage is truthy in zSpark
        - Requires title key in zSpark to determine app name
        - Non-critical operation (silently handles errors)
    """
    if not zSpark:
        return None
    
    # Check if app storage is enabled
    app_storage = zSpark.get('app_storage')
    if not app_storage:
        return None
    
    # Get app name from title (required)
    app_name = zSpark.get('title')
    if not app_name:
        logger.warning("%s app_storage enabled but no title specified", LOG_PREFIX)
        return None
    
    try:
        # Create app root: Apps/{title}/
        app_root = paths.user_data_dir / "Apps" / app_name
        app_root.mkdir(parents=True, exist_ok=True)
        
        logger.info("%s App storage initialized: %s", LOG_PREFIX, app_root)
        return app_root
        
    except Exception as e:
        logger.warning("%s Failed to create app directory: %s", LOG_PREFIX, e)
        return None

def initialize_system_ui(paths: Any) -> None:
    """
    Copy system UI file (zUI.zcli_sys.yaml) from package to user zUIs directory.
    
    Copies the system UI file containing help menus, traceback UI, and uninstall
    walker definitions on first run. This ensures system UI features work from any
    directory. Users can customize this file after initial copy.
    
    Args:
        paths: zConfigPaths instance
        
    Notes:
        - Only copies if file doesn't exist (preserves user customizations)
        - Source: zCLI/UI/zUI.zcli_sys.yaml (from installed package)
        - Target: user_zuis_dir/zUI.zcli_sys.yaml
        - Non-critical operation (silently handles errors)
    """
    try:
        target_file = paths.user_zuis_dir / ZUI_CLI_SYS_FILENAME
        
        # Skip if file already exists (user may have customized)
        if target_file.exists():
            return
        
        # Get source file from package (zCLI/UI/)
        import zCLI
        zcli_package_dir = Path(zCLI.__file__).parent
        source_file = zcli_package_dir / "UI" / ZUI_CLI_SYS_FILENAME
        
        # Copy file if source exists
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            logger.debug("%s Initialized system UI: %s", LOG_PREFIX, ZUI_CLI_SYS_FILENAME)
            logger.debug("%s Location: %s", LOG_PREFIX, target_file)
        else:
            logger.warning("%s Source UI file not found: %s", LOG_PREFIX, source_file)
            
    except Exception as e:
        logger.warning("%s Failed to initialize system UI: %s", LOG_PREFIX, e)

def initialize_system_migration_schema(paths: Any) -> None:
    """
    Copy system migration schema (zSchema.zMigration.yaml) from package to user zSchemas directory.
    
    Copies the system migration schema template used for tracking schema evolution
    on first run. This template defines the structure for __zmigration_{table_name}
    tables that record version history, changes, and migration metadata.
    
    Args:
        paths: zConfigPaths instance
        
    Notes:
        - Only copies if file doesn't exist (preserves user customizations)
        - Source: zCLI/Schemas/zSchema.zMigration.yaml (from installed package)
        - Target: user_zschemas_dir/zSchema.zMigration.yaml
        - Used by: `zolo --zMigrate` command to create migration tracking tables
        - Non-critical operation (silently handles errors)
    """
    try:
        target_file = paths.user_zschemas_dir / ZMIGRATION_SCHEMA_FILENAME
        
        # Skip if file already exists (user may have customized)
        if target_file.exists():
            return
        
        # Get source file from package (zCLI/Schemas/)
        import zCLI
        zcli_package_dir = Path(zCLI.__file__).parent
        source_file = zcli_package_dir / "Schemas" / ZMIGRATION_SCHEMA_FILENAME
        
        # Copy file if source exists
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            logger.debug("%s Initialized migration schema: %s", LOG_PREFIX, ZMIGRATION_SCHEMA_FILENAME)
            logger.debug("%s Location: %s", LOG_PREFIX, target_file)
        else:
            logger.warning("%s Source migration schema not found: %s", LOG_PREFIX, source_file)
            
    except Exception as e:
        logger.warning("%s Failed to initialize migration schema: %s", LOG_PREFIX, e)

def load_config_with_override(
    paths: Any,  # zConfigPaths (avoid circular import)
    yaml_key: str,
    create_func: Callable[[Path, Dict[str, Any]], None],
    data_dict: Dict[str, Any],
    filename: str,
    subsystem_name: str,
    log_level: Optional[str] = None
) -> None:
    """Load config file from user directory, creating with defaults if missing."""
    user_config_path = paths.user_zconfigs_dir / filename
    is_production = paths._is_production

    if user_config_path.exists():
        _load_and_override(user_config_path, yaml_key, data_dict, subsystem_name, SOURCE_USER, log_level, is_production)
    else:
        create_func(user_config_path, data_dict)
        _load_and_override(user_config_path, yaml_key, data_dict, subsystem_name, SOURCE_USER, log_level, is_production)

def _load_and_override(
    path: Path,
    yaml_key: str,
    data_dict: Dict[str, Any],
    subsystem_name: str,
    source: str,
    log_level: Optional[str] = None,
    is_production: bool = False
) -> None:
    """Load YAML config file and merge its contents into data_dict (deployment-aware)."""
    try:
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f)

            if data and yaml_key in data:
                data_dict.update(data[yaml_key])
                if not is_production:
                    logger.info("[%s] Overriding with %s settings from: %s", subsystem_name, source, path)

    except Exception as e:
        if not is_production:
            logger.warning("[%s] Failed to load %s config: %s", subsystem_name, source, e)
