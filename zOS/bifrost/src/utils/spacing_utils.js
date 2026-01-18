/**
 * ═══════════════════════════════════════════════════════════════
 * Spacing Utilities - Layout Primitives
 * ═══════════════════════════════════════════════════════════════
 *
 * Pure functions for generating and applying spacing classes.
 * These are foundational primitives for consistent layout rhythm.
 *
 * @module rendering/spacing_utils
 * @layer 0 (Foundation - below Layer 2 utilities)
 * @pattern Pure Functions (no state, no side effects)
 *
 * Philosophy:
 * - "Spacing first" - Rhythm and breathing room for all layouts
 * - Pure functions (input → output, no side effects)
 * - Uses zTheme spacing scale exclusively (0-5, auto, negative)
 * - Generates class names programmatically (no hardcoded strings)
 *
 * zTheme Spacing Scale:
 * - 0: 0 (remove spacing)
 * - 1: 0.25rem (4px)
 * - 2: 0.5rem (8px)
 * - 3: 1rem (16px) ⭐ Base unit
 * - 4: 1.5rem (24px)
 * - 5: 3rem (48px)
 * - auto: Auto (for centering)
 * - n1-n5: Negative margins (pull elements closer)
 *
 * Dependencies:
 * - None (pure utility, no imports needed)
 *
 * Exports:
 * - getMarginClass()
 * - getPaddingClass()
 * - getGapClass()
 * - applySpacing()
 *
 * Example:
 * ```javascript
 * import { getMarginClass, getPaddingClass, applySpacing } from './spacing_utils.js';
 *
 * const mt = getMarginClass(4, 'top');      // 'zmt-4'
 * const px = getPaddingClass(3, 'x');       // 'zpx-3'
 * const gap = getGapClass(2);               // 'zGap-2'
 *
 * applySpacing(element, { margin: { top: 4 }, padding: { x: 3 } });
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Margin Class Generators
// ─────────────────────────────────────────────────────────────────

/**
 * Generate margin class name (zTheme: zm-, zmt-, zmb-, zms-, zme-, zmx-, zmy-)
 *
 * Supports all zTheme margin patterns:
 * - All sides: zm-{0-5|auto}
 * - Top: zmt-{0-5|auto}
 * - Bottom: zmb-{0-5} (no auto)
 * - Start (left in LTR): zms-{0-5} (no auto)
 * - End (right in LTR): zme-{0-5|auto}
 * - X-axis (left + right): zmx-{0-5|auto}
 * - Y-axis (top + bottom): zmy-{0-5|auto}
 * - Negative: zm-n{1-5}, zmt-n{1-5}, zmb-n{1-5}, zms-n{1-5}, zme-n{1-5}, zmx-n{1-5}, zmy-n{1-5}
 *
 * @param {number|string|null} size - Size (0-5) or 'auto' or negative (e.g., -2)
 * @param {string} [side=''] - Side ('top', 'bottom', 'start', 'end', 'x', 'y', or '' for all)
 * @returns {string|null} Class name or null if invalid
 *
 * @example
 * getMarginClass(3);              // 'zm-3' (all sides)
 * getMarginClass(4, 'top');       // 'zmt-4'
 * getMarginClass('auto');         // 'zm-auto'
 * getMarginClass('auto', 'x');    // 'zmx-auto' (horizontal centering)
 * getMarginClass(-2, 'top');      // 'zmt-n2' (negative margin, pull up)
 */
export function getMarginClass(size, side = '') {
  // Handle null/undefined
  if (size === null || size === undefined) {
    return null;
  }

  // Normalize side
  const sideMap = {
    'top': 't',
    'bottom': 'b',
    'start': 's',
    'end': 'e',
    'x': 'x',
    'y': 'y',
    '': ''
  };
  const sideSuffix = sideMap[side] || '';

  // Handle auto
  if (size === 'auto') {
    // Only these sides support auto in zTheme
    if (sideSuffix === '' || sideSuffix === 't' || sideSuffix === 'e' || sideSuffix === 'x' || sideSuffix === 'y') {
      return `zm${sideSuffix}-auto`;
    }
    return null; // zmb-auto and zms-auto don't exist
  }

  // Handle negative margins
  if (typeof size === 'number' && size < 0) {
    const absSize = Math.abs(size);
    if (absSize >= 1 && absSize <= 5) {
      return `zm${sideSuffix}-n${absSize}`;
    }
    return null;
  }

  // Handle positive sizes (0-5)
  const numSize = typeof size === 'number' ? size : parseInt(size);
  if (!isNaN(numSize) && numSize >= 0 && numSize <= 5) {
    return `zm${sideSuffix}-${numSize}`;
  }

  return null;
}

/**
 * Convenience functions for specific margin sides
 */
export const getMarginTopClass = (size) => getMarginClass(size, 'top');
export const getMarginBottomClass = (size) => getMarginClass(size, 'bottom');
export const getMarginStartClass = (size) => getMarginClass(size, 'start');
export const getMarginEndClass = (size) => getMarginClass(size, 'end');
export const getMarginXClass = (size) => getMarginClass(size, 'x');
export const getMarginYClass = (size) => getMarginClass(size, 'y');

// ─────────────────────────────────────────────────────────────────
// Padding Class Generators
// ─────────────────────────────────────────────────────────────────

/**
 * Generate padding class name (zTheme: zp-, zpt-, zpb-, zps-, zpe-, zpx-, zpy-)
 *
 * Supports all zTheme padding patterns:
 * - All sides: zp-{0-5}
 * - Top: zpt-{0-5}
 * - Bottom: zpb-{0-5}
 * - Start (left in LTR): zps-{0-5}
 * - End (right in LTR): zpe-{0-5}
 * - X-axis (left + right): zpx-{0-5}
 * - Y-axis (top + bottom): zpy-{0-5}
 *
 * Note: Padding does NOT support 'auto' or negative values in zTheme
 *
 * @param {number|string|null} size - Size (0-5)
 * @param {string} [side=''] - Side ('top', 'bottom', 'start', 'end', 'x', 'y', or '' for all)
 * @returns {string|null} Class name or null if invalid
 *
 * @example
 * getPaddingClass(3);           // 'zp-3' (all sides)
 * getPaddingClass(4, 'top');    // 'zpt-4'
 * getPaddingClass(2, 'x');      // 'zpx-2' (horizontal padding)
 * getPaddingClass(5, 'y');      // 'zpy-5' (vertical padding)
 */
export function getPaddingClass(size, side = '') {
  // Handle null/undefined
  if (size === null || size === undefined) {
    return null;
  }

  // Normalize side
  const sideMap = {
    'top': 't',
    'bottom': 'b',
    'start': 's',
    'end': 'e',
    'x': 'x',
    'y': 'y',
    '': ''
  };
  const sideSuffix = sideMap[side] || '';

  // Padding does NOT support auto or negative values
  const numSize = typeof size === 'number' ? size : parseInt(size);
  if (!isNaN(numSize) && numSize >= 0 && numSize <= 5) {
    return `zp${sideSuffix}-${numSize}`;
  }

  return null;
}

/**
 * Convenience functions for specific padding sides
 */
export const getPaddingTopClass = (size) => getPaddingClass(size, 'top');
export const getPaddingBottomClass = (size) => getPaddingClass(size, 'bottom');
export const getPaddingStartClass = (size) => getPaddingClass(size, 'start');
export const getPaddingEndClass = (size) => getPaddingClass(size, 'end');
export const getPaddingXClass = (size) => getPaddingClass(size, 'x');
export const getPaddingYClass = (size) => getPaddingClass(size, 'y');

// ─────────────────────────────────────────────────────────────────
// Gap Class Generator
// ─────────────────────────────────────────────────────────────────

/**
 * Generate gap class name (zTheme: zGap-)
 *
 * For flex/grid containers to add spacing between child elements.
 *
 * @param {number|string|null} size - Size (0-5)
 * @returns {string|null} Class name or null if invalid
 *
 * @example
 * getGapClass(3);  // 'zGap-3' (1rem gap between items)
 * getGapClass(2);  // 'zGap-2' (0.5rem gap between items)
 */
export function getGapClass(size) {
  // Handle null/undefined
  if (size === null || size === undefined) {
    return null;
  }

  const numSize = typeof size === 'number' ? size : parseInt(size);
  if (!isNaN(numSize) && numSize >= 0 && numSize <= 5) {
    return `zGap-${numSize}`;
  }

  return null;
}

// ─────────────────────────────────────────────────────────────────
// Apply Spacing Function
// ─────────────────────────────────────────────────────────────────

/**
 * Apply spacing configuration to an element via config object
 *
 * This is a higher-level function for applying multiple spacing concerns at once.
 *
 * @param {HTMLElement} element - Element to apply spacing to
 * @param {Object} config - Spacing configuration
 * @param {Object} [config.margin] - Margin config ({ all, top, bottom, start, end, x, y })
 * @param {Object} [config.padding] - Padding config ({ all, top, bottom, start, end, x, y })
 * @param {number} [config.gap] - Gap size (0-5) for flex/grid containers
 * @returns {HTMLElement} Element with spacing classes applied
 *
 * @example
 * // Apply multiple spacing values
 * applySpacing(element, {
 *   margin: { top: 4, bottom: 3, x: 'auto' },
 *   padding: { x: 2, y: 3 },
 *   gap: 2
 * });
 *
 * @example
 * // Apply simple spacing
 * applySpacing(element, {
 *   margin: { all: 3 },
 *   padding: { all: 2 }
 * });
 */
export function applySpacing(element, config = {}) {
  const classes = [];

  // Apply margins
  if (config.margin) {
    const m = config.margin;

    // All sides
    if (m.all !== undefined) {
      const cls = getMarginClass(m.all);
      if (cls) {
        classes.push(cls);
      }
    }

    // Individual sides
    if (m.top !== undefined) {
      const cls = getMarginClass(m.top, 'top');
      if (cls) {
        classes.push(cls);
      }
    }
    if (m.bottom !== undefined) {
      const cls = getMarginClass(m.bottom, 'bottom');
      if (cls) {
        classes.push(cls);
      }
    }
    if (m.start !== undefined) {
      const cls = getMarginClass(m.start, 'start');
      if (cls) {
        classes.push(cls);
      }
    }
    if (m.end !== undefined) {
      const cls = getMarginClass(m.end, 'end');
      if (cls) {
        classes.push(cls);
      }
    }

    // Axes
    if (m.x !== undefined) {
      const cls = getMarginClass(m.x, 'x');
      if (cls) {
        classes.push(cls);
      }
    }
    if (m.y !== undefined) {
      const cls = getMarginClass(m.y, 'y');
      if (cls) {
        classes.push(cls);
      }
    }
  }

  // Apply padding
  if (config.padding) {
    const p = config.padding;

    // All sides
    if (p.all !== undefined) {
      const cls = getPaddingClass(p.all);
      if (cls) {
        classes.push(cls);
      }
    }

    // Individual sides
    if (p.top !== undefined) {
      const cls = getPaddingClass(p.top, 'top');
      if (cls) {
        classes.push(cls);
      }
    }
    if (p.bottom !== undefined) {
      const cls = getPaddingClass(p.bottom, 'bottom');
      if (cls) {
        classes.push(cls);
      }
    }
    if (p.start !== undefined) {
      const cls = getPaddingClass(p.start, 'start');
      if (cls) {
        classes.push(cls);
      }
    }
    if (p.end !== undefined) {
      const cls = getPaddingClass(p.end, 'end');
      if (cls) {
        classes.push(cls);
      }
    }

    // Axes
    if (p.x !== undefined) {
      const cls = getPaddingClass(p.x, 'x');
      if (cls) {
        classes.push(cls);
      }
    }
    if (p.y !== undefined) {
      const cls = getPaddingClass(p.y, 'y');
      if (cls) {
        classes.push(cls);
      }
    }
  }

  // Apply gap
  if (config.gap !== undefined) {
    const cls = getGapClass(config.gap);
    if (cls) {
      classes.push(cls);
    }
  }

  // Apply all classes at once
  if (classes.length > 0) {
    element.classList.add(...classes);
  }

  return element;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  getMarginClass,
  getMarginTopClass,
  getMarginBottomClass,
  getMarginStartClass,
  getMarginEndClass,
  getMarginXClass,
  getMarginYClass,
  getPaddingClass,
  getPaddingTopClass,
  getPaddingBottomClass,
  getPaddingStartClass,
  getPaddingEndClass,
  getPaddingXClass,
  getPaddingYClass,
  getGapClass,
  applySpacing
};

