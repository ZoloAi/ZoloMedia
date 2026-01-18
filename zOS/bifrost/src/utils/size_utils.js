/**
 * Size Utilities - Generate and apply zTheme size classes
 *
 * "Off-road" utility module created during Bifrost refactoring
 * Complements spacing_utils.js and color_utils.js
 *
 * zTheme doesn't have comprehensive size utilities built-in,
 * so we provide programmatic sizing for common patterns:
 * - Width/Height (responsive and fixed)
 * - Min/Max dimensions
 * - Aspect ratios
 * - Icon sizes
 * - Spinner sizes
 *
 * Layer: Utility (Layer 0.4)
 * Dependencies: None (pure utility functions)
 * Used by: All renderers that need programmatic sizing
 */

/**
 * Standard size scale (matches zTheme spacing scale)
 */
const SIZE_SCALE = {
  0: '0',
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  5: '1.25rem',  // 20px
  6: '1.5rem',   // 24px
  7: '1.75rem',  // 28px
  8: '2rem',     // 32px
  9: '2.25rem',  // 36px
  10: '2.5rem',  // 40px
  12: '3rem',    // 48px
  16: '4rem',    // 64px
  20: '5rem',    // 80px
  24: '6rem',    // 96px
  32: '8rem',    // 128px
  40: '10rem',   // 160px
  48: '12rem',   // 192px
  56: '14rem',   // 224px
  64: '16rem'    // 256px
};

/**
 * Percentage sizes for responsive layouts
 */
const PERCENT_SIZES = {
  '25': '25%',
  '33': '33.333333%',
  '50': '50%',
  '66': '66.666667%',
  '75': '75%',
  '100': '100%',
  auto: 'auto'
};

/**
 * Icon size presets (matching common icon libraries)
 */
const ICON_SIZES = {
  xs: '0.75rem',   // 12px
  sm: '1rem',      // 16px
  md: '1.5rem',    // 24px
  lg: '2rem',      // 32px
  xl: '3rem',      // 48px
  '2xl': '4rem'    // 64px
};

/**
 * Spinner size presets (matching Bootstrap/zTheme spinners)
 */
const SPINNER_SIZES = {
  sm: { width: '1rem', height: '1rem', borderWidth: '0.15em' },
  md: { width: '2rem', height: '2rem', borderWidth: '0.2em' },
  lg: { width: '3rem', height: '3rem', borderWidth: '0.25em' }
};

/**
 * Get width class
 * @param {string|number} size - Size value (scale number, percent, or 'auto')
 * @returns {string} Width class
 */
export function getWidthClass(size) {
  if (typeof size === 'number' || !isNaN(size)) {
    return `zW-${size}`;
  }
  return `zW-${size}`;
}

/**
 * Get height class
 * @param {string|number} size - Size value (scale number, percent, or 'auto')
 * @returns {string} Height class
 */
export function getHeightClass(size) {
  if (typeof size === 'number' || !isNaN(size)) {
    return `zH-${size}`;
  }
  return `zH-${size}`;
}

/**
 * Apply width to element
 * @param {HTMLElement} element - Target element
 * @param {string|number} size - Size value
 * @returns {HTMLElement} Element with width applied
 */
export function applyWidth(element, size) {
  const value = SIZE_SCALE[size] || PERCENT_SIZES[size] || size;
  element.style.width = value;
  return element;
}

/**
 * Apply height to element
 * @param {HTMLElement} element - Target element
 * @param {string|number} size - Size value
 * @returns {HTMLElement} Element with height applied
 */
export function applyHeight(element, size) {
  const value = SIZE_SCALE[size] || PERCENT_SIZES[size] || size;
  element.style.height = value;
  return element;
}

/**
 * Apply dimensions (width and height) to element
 * @param {HTMLElement} element - Target element
 * @param {string|number} width - Width value
 * @param {string|number} height - Height value (defaults to width for square)
 * @returns {HTMLElement} Element with dimensions applied
 */
export function applyDimensions(element, width, height = width) {
  applyWidth(element, width);
  applyHeight(element, height);
  return element;
}

/**
 * Apply min-width to element
 * @param {HTMLElement} element - Target element
 * @param {string|number} size - Size value
 * @returns {HTMLElement} Element with min-width applied
 */
export function applyMinWidth(element, size) {
  const value = SIZE_SCALE[size] || PERCENT_SIZES[size] || size;
  element.style.minWidth = value;
  return element;
}

/**
 * Apply max-width to element
 * @param {HTMLElement} element - Target element
 * @param {string|number} size - Size value
 * @returns {HTMLElement} Element with max-width applied
 */
export function applyMaxWidth(element, size) {
  const value = SIZE_SCALE[size] || PERCENT_SIZES[size] || size;
  element.style.maxWidth = value;
  return element;
}

/**
 * Apply icon size to element
 * @param {HTMLElement} element - Target element (icon)
 * @param {string} size - Icon size (xs, sm, md, lg, xl, 2xl)
 * @returns {HTMLElement} Element with icon size applied
 */
export function applyIconSize(element, size) {
  const value = ICON_SIZES[size] || ICON_SIZES.md;
  element.style.fontSize = value;
  element.style.width = value;
  element.style.height = value;
  return element;
}

/**
 * Apply spinner size to element
 * @param {HTMLElement} element - Target element (spinner)
 * @param {string} size - Spinner size (sm, md, lg)
 * @returns {HTMLElement} Element with spinner size applied
 */
export function applySpinnerSize(element, size) {
  const styles = SPINNER_SIZES[size] || SPINNER_SIZES.md;
  element.style.width = styles.width;
  element.style.height = styles.height;
  element.style.borderWidth = styles.borderWidth;
  return element;
}

/**
 * Apply aspect ratio to element
 * @param {HTMLElement} element - Target element
 * @param {string} ratio - Aspect ratio (e.g., '16/9', '4/3', '1/1')
 * @returns {HTMLElement} Element with aspect ratio applied
 */
export function applyAspectRatio(element, ratio) {
  element.style.aspectRatio = ratio;
  return element;
}

/**
 * Apply sizing configuration object to element
 * @param {HTMLElement} element - Target element
 * @param {Object} config - Sizing configuration
 * @param {string|number} [config.width] - Width
 * @param {string|number} [config.height] - Height
 * @param {string|number} [config.minWidth] - Min width
 * @param {string|number} [config.maxWidth] - Max width
 * @param {string|number} [config.minHeight] - Min height
 * @param {string|number} [config.maxHeight] - Max height
 * @param {string} [config.aspectRatio] - Aspect ratio
 * @returns {HTMLElement} Element with sizing applied
 */
export function applySizing(element, config) {
  if (config.width !== undefined) {
    applyWidth(element, config.width);
  }
  if (config.height !== undefined) {
    applyHeight(element, config.height);
  }
  if (config.minWidth !== undefined) {
    applyMinWidth(element, config.minWidth);
  }
  if (config.maxWidth !== undefined) {
    applyMaxWidth(element, config.maxWidth);
  }
  if (config.minHeight !== undefined) {
    const value = SIZE_SCALE[config.minHeight] || PERCENT_SIZES[config.minHeight] || config.minHeight;
    element.style.minHeight = value;
  }
  if (config.maxHeight !== undefined) {
    const value = SIZE_SCALE[config.maxHeight] || PERCENT_SIZES[config.maxHeight] || config.maxHeight;
    element.style.maxHeight = value;
  }
  if (config.aspectRatio !== undefined) {
    applyAspectRatio(element, config.aspectRatio);
  }

  return element;
}

/**
 * Get size value from scale or percent
 * @param {string|number} size - Size key
 * @returns {string} CSS size value
 */
export function getSizeValue(size) {
  return SIZE_SCALE[size] || PERCENT_SIZES[size] || size;
}

// Export constants for direct access
export { SIZE_SCALE, PERCENT_SIZES, ICON_SIZES, SPINNER_SIZES };

