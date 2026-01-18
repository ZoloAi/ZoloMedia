/**
 * ═══════════════════════════════════════════════════════════════
 * Color Utilities - Visual Identity Primitives
 * ═══════════════════════════════════════════════════════════════
 *
 * Pure functions for generating and applying color classes.
 * These are foundational primitives for consistent visual identity.
 *
 * @module rendering/color_utils
 * @layer 0 (Foundation - below Layer 2 utilities)
 * @pattern Pure Functions (no state, no side effects)
 *
 * Philosophy:
 * - "Color first" - Visual identity and semantics for all content
 * - Pure functions (input → output, no side effects)
 * - Uses zTheme color system exclusively (semantic colors)
 * - Generates class names programmatically (no hardcoded strings)
 *
 * zTheme Semantic Colors:
 * - primary: Brand color (green in zCLI)
 * - secondary: Supporting brand
 * - success: Green - positive actions/states
 * - danger/error: Red - errors/critical
 * - warning: Yellow - caution
 * - info: Blue - informational
 * - light: Light gray
 * - dark: Dark gray
 * - white: Pure white
 * - black: Pure black (text only)
 * - body: Default text color
 * - muted: Secondary/subdued text
 * - transparent: Transparent background
 *
 * Dependencies:
 * - None (pure utility, no imports needed)
 *
 * Exports:
 * - getBackgroundClass()
 * - getTextColorClass()
 * - getBorderColorClass()
 * - applyColorScheme()
 *
 * Example:
 * ```javascript
 * import { getBackgroundClass, getTextColorClass, applyColorScheme } from './color_utils.js';
 *
 * const bg = getBackgroundClass('primary');   // 'zBg-primary'
 * const text = getTextColorClass('white');    // 'zText-white'
 *
 * applyColorScheme(element, { background: 'light', text: 'dark', border: 'primary' });
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Color Constants (verified against zTheme CSS)
// ─────────────────────────────────────────────────────────────────

/**
 * Valid background colors in zTheme
 */
const VALID_BG_COLORS = [
  'primary', 'secondary', 'success', 'info', 'warning', 'danger', 'error',
  'light', 'dark', 'white', 'body', 'transparent'
];

/**
 * Valid text colors in zTheme
 */
const VALID_TEXT_COLORS = [
  'primary', 'secondary', 'success', 'info', 'warning', 'danger', 'error',
  'light', 'dark', 'body', 'muted', 'white', 'black',
  'black-50', 'white-50'  // Opacity variants
];

/**
 * Valid border colors in zTheme
 */
const VALID_BORDER_COLORS = [
  'primary', 'secondary', 'success', 'info', 'warning', 'danger',
  'light', 'dark', 'white'
];

// ─────────────────────────────────────────────────────────────────
// Background Color Functions
// ─────────────────────────────────────────────────────────────────

/**
 * Generate background color class (zTheme: zBg-)
 *
 * @param {string|null} color - Color name (semantic)
 * @returns {string|null} Class name or null if invalid
 *
 * @example
 * getBackgroundClass('primary');      // 'zBg-primary' (brand color)
 * getBackgroundClass('light');        // 'zBg-light' (light gray)
 * getBackgroundClass('transparent');  // 'zBg-transparent'
 */
export function getBackgroundClass(color) {
  if (!color) {
    return null;
  }

  const normalized = color.toLowerCase();

  if (VALID_BG_COLORS.includes(normalized)) {
    return `zBg-${normalized}`;
  }

  return null;
}

// ─────────────────────────────────────────────────────────────────
// Text Color Functions
// ─────────────────────────────────────────────────────────────────

/**
 * Generate text color class (zTheme: zText-)
 *
 * @param {string|null} color - Color name (semantic)
 * @returns {string|null} Class name or null if invalid
 *
 * @example
 * getTextColorClass('primary');    // 'zText-primary' (brand color)
 * getTextColorClass('muted');      // 'zText-muted' (subdued text)
 * getTextColorClass('white');      // 'zText-white'
 * getTextColorClass('black-50');   // 'zText-black-50' (50% opacity)
 */
export function getTextColorClass(color) {
  if (!color) {
    return null;
  }

  const normalized = color.toLowerCase();

  if (VALID_TEXT_COLORS.includes(normalized)) {
    return `zText-${normalized}`;
  }

  return null;
}

// ─────────────────────────────────────────────────────────────────
// Border Color Functions
// ─────────────────────────────────────────────────────────────────

/**
 * Generate border color class (zTheme: zBorder-)
 *
 * Note: This sets the border COLOR only, not the border itself.
 * You still need to add the `zBorder` class to show the border.
 *
 * @param {string|null} color - Color name (semantic)
 * @returns {string|null} Class name or null if invalid
 *
 * @example
 * // Must combine with zBorder to show border:
 * element.className = 'zBorder ' + getBorderColorClass('primary');
 * // Result: 'zBorder zBorder-primary'
 *
 * getBorderColorClass('primary');  // 'zBorder-primary'
 * getBorderColorClass('danger');   // 'zBorder-danger'
 */
export function getBorderColorClass(color) {
  if (!color) {
    return null;
  }

  const normalized = color.toLowerCase();

  if (VALID_BORDER_COLORS.includes(normalized)) {
    return `zBorder-${normalized}`;
  }

  return null;
}

// ─────────────────────────────────────────────────────────────────
// Apply Color Scheme Function
// ─────────────────────────────────────────────────────────────────

/**
 * Apply color scheme to an element via config object
 *
 * This is a higher-level function for applying multiple color concerns at once.
 *
 * @param {HTMLElement} element - Element to apply colors to
 * @param {Object} config - Color configuration
 * @param {string} [config.background] - Background color
 * @param {string} [config.text] - Text color
 * @param {string} [config.border] - Border color (requires zBorder class to be visible)
 * @returns {HTMLElement} Element with color classes applied
 *
 * @example
 * // Create a primary-colored card
 * applyColorScheme(element, {
 *   background: 'primary',
 *   text: 'white',
 *   border: 'primary'
 * });
 *
 * @example
 * // Create a light info box
 * applyColorScheme(element, {
 *   background: 'light',
 *   text: 'dark'
 * });
 */
export function applyColorScheme(element, config = {}) {
  const classes = [];

  // Apply background color
  if (config.background) {
    const bgClass = getBackgroundClass(config.background);
    if (bgClass) {
      classes.push(bgClass);
    }
  }

  // Apply text color
  if (config.text) {
    const textClass = getTextColorClass(config.text);
    if (textClass) {
      classes.push(textClass);
    }
  }

  // Apply border color
  if (config.border) {
    const borderClass = getBorderColorClass(config.border);
    if (borderClass) {
      classes.push(borderClass);
    }
  }

  // Apply all classes at once
  if (classes.length > 0) {
    element.classList.add(...classes);
  }

  return element;
}

// ─────────────────────────────────────────────────────────────────
// Helper: Get All Available Colors
// ─────────────────────────────────────────────────────────────────

/**
 * Get lists of all available colors (useful for debugging/documentation)
 *
 * @returns {Object} Object with arrays of valid colors for each category
 *
 * @example
 * const colors = getAvailableColors();
 * this.logger.log(colors.backgrounds);  // ['primary', 'secondary', ...]
 */
export function getAvailableColors() {
  return {
    backgrounds: [...VALID_BG_COLORS],
    text: [...VALID_TEXT_COLORS],
    borders: [...VALID_BORDER_COLORS]
  };
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  getBackgroundClass,
  getTextColorClass,
  getBorderColorClass,
  applyColorScheme,
  getAvailableColors
};

