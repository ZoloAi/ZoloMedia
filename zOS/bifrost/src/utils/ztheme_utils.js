/**
 * ═══════════════════════════════════════════════════════════════
 * zTheme Utilities - zCLI to zTheme Class Mappings
 * ═══════════════════════════════════════════════════════════════
 *
 * Pure functions for mapping zCLI color/style names to zTheme CSS classes.
 * Uses lookup tables for O(1) performance and consistency.
 *
 * @module utils/ztheme_utils
 * @layer 2
 * @pattern Pure Functions
 *
 * Dependencies:
 * - Layer 0: None (pure JavaScript)
 *
 * Exports:
 * - getButtonColorClass: Map zCLI color to zTheme button class
 * - getButtonSizeClass: Map size to zTheme button size class
 * - getButtonStyleClass: Map style variant to zTheme button style class
 * - getAlertColorClass: Map event type to zTheme alert class
 * - getBadgeColorClass: Map zCLI color to zTheme badge class
 * - getTextColorClass: Map zCLI color to zTheme text color class
 * - isValidZThemeClass: Validate if string is valid zTheme class
 * - indentToHeaderTag: Convert indent level to HTML header tag
 *
 * Example:
 * ```javascript
 * import { getButtonColorClass, getButtonSizeClass } from './ztheme_utils.js';
 *
 * const colorClass = getButtonColorClass('primary');  // 'zBtnPrimary'
 * const sizeClass = getButtonSizeClass('lg');          // 'zBtn-lg'
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Color Mappings (zCLI → zTheme)
// ─────────────────────────────────────────────────────────────────

/**
 * Button color mapping: zCLI color names → zTheme button classes
 * @const {Object<string, string>}
 */
const BUTTON_COLOR_MAP = {
  'primary': 'zBtn-primary',
  'secondary': 'zBtn-secondary',
  'success': 'zBtn-success',
  'danger': 'zBtn-danger',
  'warning': 'zBtn-warning',
  'info': 'zBtn-info',
  'light': 'zBtn-light',
  'dark': 'zBtn-dark',
  'link': 'zBtn-link'
};

/**
 * Alert color mapping: zCLI event types → zTheme zSignal classes
 * Returns ONLY the color-specific class (base zSignal class added by renderer)
 * @const {Object<string, string>}
 */
const ALERT_COLOR_MAP = {
  'error': 'zSignal-error',
  'warning': 'zSignal-warning',
  'success': 'zSignal-success',
  'info': 'zSignal-info',
  'danger': 'zSignal-error',      // danger → error (zTheme uses error)
  'primary': 'zSignal-primary',
  'secondary': 'zSignal-secondary',
  'light': 'zSignal-light',
  'dark': 'zSignal-dark'
};

/**
 * Badge color mapping: zCLI colors → zTheme badge classes
 * @const {Object<string, string>}
 */
const BADGE_COLOR_MAP = {
  'primary': 'zBadge zBgPrimary',
  'secondary': 'zBadge zBgSecondary',
  'success': 'zBadge zBgSuccess',
  'danger': 'zBadge zBgDanger',
  'warning': 'zBadge zBgWarning',
  'info': 'zBadge zBgInfo',
  'light': 'zBadge zBgLight',
  'dark': 'zBadge zBgDark'
};

/**
 * Text color mapping: zCLI colors → zTheme text color classes
 * @const {Object<string, string>}
 */
const TEXT_COLOR_MAP = {
  'primary': 'zText-primary',
  'secondary': 'zText-secondary',
  'success': 'zText-success',
  'danger': 'zText-danger',
  'warning': 'zText-warning',
  'info': 'zText-info',
  'light': 'zText-light',
  'dark': 'zText-dark',
  'muted': 'zText-muted',
  'white': 'zText-white'
};

// ─────────────────────────────────────────────────────────────────
// Button Utilities
// ─────────────────────────────────────────────────────────────────

/**
 * Get zTheme button color class from zCLI color name
 *
 * @param {string} zColor - zCLI color name (primary, danger, success, etc)
 * @returns {string} zTheme button class (zBtn-primary, zBtn-danger, etc)
 *
 * @example
 * getButtonColorClass('primary')   // 'zBtn-primary'
 * getButtonColorClass('DANGER')    // 'zBtn-danger' (case-insensitive)
 * getButtonColorClass('invalid')   // 'zBtn-primary' (fallback)
 * getButtonColorClass(null)        // 'zBtn-primary' (fallback)
 */
export function getButtonColorClass(zColor) {
  const normalized = zColor?.toLowerCase() || 'primary';
  return BUTTON_COLOR_MAP[normalized] || 'zBtn-primary';
}

/**
 * Get zTheme button size class
 *
 * @param {string} size - Size (sm, md, lg)
 * @returns {string} zTheme size class (zBtn-sm, zBtn-lg, or empty string for md)
 *
 * @example
 * getButtonSizeClass('sm')   // 'zBtn-sm'
 * getButtonSizeClass('md')   // '' (default, no class needed)
 * getButtonSizeClass('lg')   // 'zBtn-lg'
 * getButtonSizeClass(null)   // '' (default)
 */
export function getButtonSizeClass(size) {
  const normalized = size?.toLowerCase() || 'md';

  const SIZE_MAP = {
    'sm': 'zBtn-sm',
    'small': 'zBtn-sm',
    'md': '',
    'medium': '',
    'lg': 'zBtn-lg',
    'large': 'zBtn-lg'
  };

  return SIZE_MAP[normalized] || '';
}

/**
 * Get zTheme button style variant class
 *
 * NOTE: For outline buttons, use getButtonOutlineClass() instead.
 * This only handles non-color-specific styles.
 *
 * @param {string} style - Style variant (default, link)
 * @returns {string} zTheme style class or empty for default
 *
 * @example
 * getButtonStyleClass('default')   // '' (no class needed)
 * getButtonStyleClass('link')      // 'zBtn-link'
 */
export function getButtonStyleClass(style) {
  const normalized = style?.toLowerCase() || 'default';

  const STYLE_MAP = {
    'default': '',
    'solid': '',
    'link': 'zBtn-link'
  };

  return STYLE_MAP[normalized] || '';
}

/**
 * Get zTheme outline button class (color-specific)
 *
 * @param {string} zColor - zCLI color name
 * @returns {string} zTheme outline button class (e.g., 'zBtn-outline-primary')
 *
 * @example
 * getButtonOutlineClass('primary')  // 'zBtn-outline-primary'
 * getButtonOutlineClass('danger')   // 'zBtn-outline-danger'
 */
export function getButtonOutlineClass(zColor) {
  const normalized = zColor?.toLowerCase() || 'primary';
  return `zBtn-outline-${normalized}`;
}

// ─────────────────────────────────────────────────────────────────
// Alert Utilities
// ─────────────────────────────────────────────────────────────────

/**
 * Get zTheme signal color class from zCLI event type
 *
 * Returns ONLY the color-specific class (e.g., 'zSignal-success').
 * The base 'zSignal' class should be added separately by the renderer.
 *
 * @param {string} eventType - zCLI event type (error, warning, success, info)
 * @returns {string} zTheme signal color class (e.g., 'zSignal-success')
 *
 * @example
 * getAlertColorClass('error')    // 'zSignal-error'
 * getAlertColorClass('warning')  // 'zSignal-warning'
 * getAlertColorClass('success')  // 'zSignal-success'
 * getAlertColorClass('info')     // 'zSignal-info'
 */
export function getAlertColorClass(eventType) {
  const normalized = eventType?.toLowerCase() || 'info';
  return ALERT_COLOR_MAP[normalized] || 'zSignal-info';
}

// ─────────────────────────────────────────────────────────────────
// Badge Utilities
// ─────────────────────────────────────────────────────────────────

/**
 * Get zTheme badge color classes from zCLI color
 *
 * @param {string} zColor - zCLI color name
 * @returns {string} zTheme badge classes (e.g., 'zBadge zBgPrimary')
 *
 * @example
 * getBadgeColorClass('primary')  // 'zBadge zBgPrimary'
 * getBadgeColorClass('danger')   // 'zBadge zBgDanger'
 */
export function getBadgeColorClass(zColor) {
  const normalized = zColor?.toLowerCase() || 'primary';
  return BADGE_COLOR_MAP[normalized] || 'zBadge zBgPrimary';
}

// ─────────────────────────────────────────────────────────────────
// Text Utilities
// ─────────────────────────────────────────────────────────────────

/**
 * Get zTheme text color class from zCLI color
 *
 * @param {string} zColor - zCLI color name
 * @returns {string} zTheme text color class (e.g., 'zText-primary')
 *
 * @example
 * getTextColorClass('primary')  // 'zText-primary'
 * getTextColorClass('danger')   // 'zText-danger'
 * getTextColorClass('muted')    // 'zText-muted'
 */
export function getTextColorClass(zColor) {
  const normalized = zColor?.toLowerCase() || 'dark';
  return TEXT_COLOR_MAP[normalized] || 'zText-dark';
}

// ─────────────────────────────────────────────────────────────────
// Typography Utilities
// ─────────────────────────────────────────────────────────────────

/**
 * Convert indent level to HTML header tag
 *
 * NOTE: indent 0 is reserved for special cases (flush/hero layouts).
 * This function maps indent 1-6 directly to h1-h6 semantic HTML tags.
 *
 * @param {number} indent - Indent level (1-6, where 1=h1, 6=h6)
 * @returns {string} HTML tag name ('h1' through 'h6')
 *
 * @example
 * indentToHeaderTag(1)   // 'h1'
 * indentToHeaderTag(2)   // 'h2'
 * indentToHeaderTag(6)   // 'h6'
 * indentToHeaderTag(10)  // 'h6' (capped at h6)
 */
export function indentToHeaderTag(indent) {
  // Clamp indent between 1 and 6 (indent 0 reserved for special cases)
  const level = Math.max(1, Math.min(6, parseInt(indent) || 1));
  return `h${level}`;
}

// ─────────────────────────────────────────────────────────────────
// Validation Utilities
// ─────────────────────────────────────────────────────────────────

/**
 * Validate if a string is a valid zTheme class name
 *
 * @param {string} className - Class name to validate
 * @returns {boolean} True if valid zTheme class
 *
 * @example
 * isValidZThemeClass('zBtn')           // true
 * isValidZThemeClass('zBtnPrimary')    // true
 * isValidZThemeClass('zAlert')         // true
 * isValidZThemeClass('not-ztheme')     // false
 * isValidZThemeClass('btn-primary')    // false
 */
export function isValidZThemeClass(className) {
  if (!className || typeof className !== 'string') {
    return false;
  }

  // zTheme classes start with 'z' followed by uppercase letter
  return /^z[A-Z]/.test(className);
}

