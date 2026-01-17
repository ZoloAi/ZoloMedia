# zOS/formatting/terminal.py
"""
Terminal output utilities for banners and formatted messages.

Note:
    These utilities are used BEFORE zDisplay is initialized (Layer 0 init),
    so they must be width-safe and not rely on zDisplay primitives.
"""

import os
import shutil
import subprocess
from typing import Optional

from .colors import Colors


def print_ready_message(
    label: str,
    color: str = "CONFIG",
    base_width: int = 60,
    char: str = "═",
    log_level: Optional[str] = None,
    is_production: bool = False,
    is_testing: bool = False
) -> None:
    """
    Print styled 'Ready' message for subsystems.
    
    Suppressed in Production and Testing modes (only shown in Development).
    
    Args:
        label: Message label
        color: Color code name from Colors class
        base_width: Total width of the message line (unused, kept for compatibility)
        char: Character to use for padding
        log_level: Optional log level (suppresses output if PROD) - deprecated
        is_production: If True, suppresses output (Production deployment)
        is_testing: If True, suppresses output (Testing deployment)
    
    Terminal Header / Banner Rules (pre-zDisplay):
        - Design for 80 columns, but never hardcode width
        - Detect width at print time (COLUMNS, get_terminal_size, tput cols)
        - Clamp width to [60–120]
        - Single-line only, ASCII separators only (= - _ *)
        - Truncate titles to fit
        - Center title if space allows, else left-align
        - Output must never wrap or exceed detected width (visual width)
    """
    # Check deployment mode first (highest priority)
    # Suppress in both Production AND Testing modes
    if is_production or is_testing:
        return
    
    # Fallback to old PROD log level check (for backward compatibility)
    # Import here to avoid circular dependency
    from zOS.logger.config import should_suppress_init_prints
    if should_suppress_init_prints(log_level):
        return

    # Detect width (print time)
    cols: Optional[int] = None
    try:
        env_cols = os.environ.get("COLUMNS", "").strip()
        if env_cols.isdigit():
            cols = int(env_cols)
    except Exception:
        cols = None

    if not cols:
        try:
            cols = int(shutil.get_terminal_size(fallback=(80, 24)).columns)
        except Exception:
            cols = None

    if not cols:
        try:
            result = subprocess.run(
                ["tput", "cols"],
                capture_output=True,
                text=True,
                check=False
            )
            out = (result.stdout or "").strip()
            if out.isdigit():
                cols = int(out)
        except Exception:
            cols = None

    if not cols or cols <= 0:
        cols = 80

    # Clamp to [60–120]
    if cols < 60:
        cols = 60
    elif cols > 120:
        cols = 120

    # ASCII-only separator selection
    allowed = {"=", "-", "_", "*"}
    sep = char if char in allowed else "="

    title = (label or "").strip()
    if not title:
        print(sep * cols)
        return

    # Build title that fits (plain version determines visual width)
    if cols >= 3:
        title_core_max = cols - 2
        title_core = title[:title_core_max]
        title_plain = f" {title_core} "
    else:
        title_core = title[:cols]
        title_plain = title_core

    remaining = cols - len(title_plain)

    # Optional ANSI color for the title core (must remain readable without color)
    title_out = title_plain
    if color and color != "RESET":
        try:
            color_code = getattr(Colors, color, Colors.RESET)
            reset_code = Colors.RESET
            if cols >= 3:
                title_out = f" {color_code}{title_core}{reset_code} "
            else:
                title_out = f"{color_code}{title_plain}{reset_code}"
        except Exception:
            title_out = title_plain

    # Center only if at least 1 separator fits on both sides; else left-align.
    if remaining >= 2:
        left = remaining // 2
        right = remaining - left
        line_out = (sep * left) + title_out + (sep * right)
    else:
        line_out = title_out + (sep * max(0, cols - len(title_plain)))

    print(line_out)

