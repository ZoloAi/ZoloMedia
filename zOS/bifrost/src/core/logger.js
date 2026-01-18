/**
 * ═══════════════════════════════════════════════════════════════
 * Logger Module - Debug Logging
 * ═══════════════════════════════════════════════════════════════
 */

export class Logger {
  constructor(debug = false) {
    this.debug = debug;
  }

  /**
   * Log message if debug enabled
   */
  log(message, ...args) {
    if (this.debug) {
      console.log(`[BifrostClient] ${message}`, ...args);
    }
  }

  /**
   * Log error (always shown, regardless of debug mode)
   */
  error(message, ...args) {
    console.error(`[BifrostClient ERROR] ${message}`, ...args);
  }

  /**
   * Log warning if debug enabled
   */
  warn(message, ...args) {
    if (this.debug) {
      console.warn(`[BifrostClient WARN] ${message}`, ...args);
    }
  }

  /**
   * Enable debug logging
   */
  enable() {
    this.debug = true;
  }

  /**
   * Disable debug logging
   */
  disable() {
    this.debug = false;
  }

  /**
   * Check if debug is enabled
   */
  isEnabled() {
    return this.debug;
  }
}

