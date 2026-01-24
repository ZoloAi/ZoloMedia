/**
 * ═══════════════════════════════════════════════════════════════
 * Container Utilities - Layout Primitives
 * ═══════════════════════════════════════════════════════════════
 *
 * Pure functions for creating and managing layout containers.
 * These are the TRUE primitives - before text, before headers, before anything.
 *
 * @module rendering/container_utils
 * @layer 0 (Foundation - below Layer 2 utilities)
 * @pattern Pure Functions (no state, no side effects)
 *
 * Philosophy:
 * - "Container first" - Everything needs a home
 * - Pure functions (input → output, no side effects)
 * - Uses zTheme exclusively (no custom CSS)
 * - Composable (containers can nest)
 *
 * Dependencies:
 * - Layer 2: dom_utils.js
 *
 * Exports:
 * - createContainer()
 * - createSection()
 * - createWrapper()
 * - applyContainerStyles()
 *
 * Example:
 * ```javascript
 * import { createContainer, createWrapper } from './container_utils.js';
 *
 * const container = createContainer(['zContainer', 'zMy-4']);
 * const flexWrapper = createWrapper(['zD-flex', 'zGap-3']);
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Imports
// ─────────────────────────────────────────────────────────────────
import { createElement, setAttributes } from '../utils/dom_utils.js';

// ─────────────────────────────────────────────────────────────────
// Container Creation Functions
// ─────────────────────────────────────────────────────────────────

/**
 * Create a main content container (zTheme: zContainer)
 *
 * A container is the primary layout element that provides:
 * - Max width constraints
 * - Horizontal centering
 * - Responsive padding
 *
 * @param {Array<string>} [classes=[]] - Additional CSS classes to apply
 * @param {Object} [attributes={}] - HTML attributes (id, data-*, etc.)
 * @returns {HTMLElement} Div element with zContainer class
 *
 * @example
 * // Basic centered container
 * const container = createContainer();
 *
 * @example
 * // Container with vertical margin
 * const container = createContainer(['zMy-4']);
 *
 * @example
 * // Fluid container (full width)
 * const fluidContainer = createContainer(['zContainer-fluid']);
 */
export function createContainer(classes = [], attributes = {}) {
  const containerClasses = ['zContainer', ...classes];
  const container = createElement('div', containerClasses);

  if (Object.keys(attributes).length > 0) {
    setAttributes(container, attributes);
  }

  return container;
}

/**
 * Create a semantic section element
 *
 * Sections are semantic HTML5 elements for content grouping.
 * Use for major page sections (hero, features, footer, etc.)
 *
 * @param {Array<string>} [classes=[]] - CSS classes to apply
 * @param {Object} [attributes={}] - HTML attributes
 * @returns {HTMLElement} Section element
 *
 * @example
 * // Hero section with background
 * const hero = createSection(['zBg-primary', 'zText-white', 'zPy-5']);
 *
 * @example
 * // Feature section with ID
 * const features = createSection(['zPy-4'], { id: 'features' });
 */
export function createSection(classes = [], attributes = {}) {
  const section = createElement('section', classes);

  if (Object.keys(attributes).length > 0) {
    setAttributes(section, attributes);
  }

  return section;
}

/**
 * Create a generic wrapper div (for grouping/layout)
 *
 * Wrappers are flexible divs for:
 * - Grouping related elements
 * - Applying flex/grid layouts
 * - Creating visual boundaries
 *
 * @param {Array<string>} [classes=[]] - CSS classes to apply
 * @param {Object} [attributes={}] - HTML attributes
 * @returns {HTMLElement} Div element (no default classes)
 *
 * @example
 * // Flex row wrapper
 * const row = createWrapper(['zD-flex', 'zGap-3', 'zFlex-items-center']);
 *
 * @example
 * // Grid wrapper
 * const grid = createWrapper(['zD-grid', 'zGap-4'], { style: 'grid-template-columns: repeat(3, 1fr);' });
 *
 * @example
 * // Card body wrapper
 * const cardBody = createWrapper(['zCard-body', 'zP-3']);
 */
export function createWrapper(classes = [], attributes = {}) {
  const wrapper = createElement('div', classes);

  if (Object.keys(attributes).length > 0) {
    setAttributes(wrapper, attributes);
  }

  return wrapper;
}

// ─────────────────────────────────────────────────────────────────
// Container Styling Functions
// ─────────────────────────────────────────────────────────────────

/**
 * Apply container-specific styles via config object
 *
 * This is a higher-level function for applying multiple style concerns at once.
 * Useful when you need to apply layout, display, and alignment in one call.
 *
 * @param {HTMLElement} element - Element to style
 * @param {Object} config - Style configuration
 * @param {string} [config.display] - Display mode (flex, grid, block, inline-block)
 * @param {string} [config.direction] - Flex direction (row, column)
 * @param {string} [config.align] - Alignment (start, center, end, stretch)
 * @param {string} [config.justify] - Justification (start, center, end, between, around)
 * @param {number} [config.gap] - Gap size (0-5)
 * @param {boolean} [config.wrap] - Enable flex wrap
 * @returns {HTMLElement} Element with styles applied
 *
 * @example
 * // Create a flex container with centering
 * const wrapper = createWrapper();
 * applyContainerStyles(wrapper, {
 *   display: 'flex',
 *   direction: 'row',
 *   align: 'center',
 *   justify: 'between',
 *   gap: 3
 * });
 *
 * @example
 * // Create a grid container
 * const grid = createWrapper();
 * applyContainerStyles(grid, {
 *   display: 'grid',
 *   gap: 4
 * });
 */
export function applyContainerStyles(element, config = {}) {
  const classes = [];

  // Display mode
  if (config.display) {
    const displayMap = {
      'flex': 'zD-flex',
      'grid': 'zD-grid',
      'block': 'zD-block',
      'inline-block': 'zD-inline-block',
      'none': 'zD-none'
    };
    const displayClass = displayMap[config.display];
    if (displayClass) {
      classes.push(displayClass);
    }
  }

  // Flex direction (only applies if display is flex)
  if (config.direction && config.display === 'flex') {
    const directionMap = {
      'row': 'zFlex-row',
      'column': 'zFlex-column',
      'row-reverse': 'zFlex-row-reverse',
      'column-reverse': 'zFlex-column-reverse'
    };
    const directionClass = directionMap[config.direction];
    if (directionClass) {
      classes.push(directionClass);
    }
  }

  // Alignment (align-items - vertical alignment in row, horizontal in column)
  if (config.align) {
    const alignMap = {
      'start': 'zFlex-items-start',
      'center': 'zFlex-items-center',
      'end': 'zFlex-items-end',
      'stretch': 'zFlex-items-stretch',
      'baseline': 'zFlex-items-baseline'
    };
    const alignClass = alignMap[config.align];
    if (alignClass) {
      classes.push(alignClass);
    }
  }

  // Justification (justify-content - horizontal alignment in row, vertical in column)
  if (config.justify) {
    const justifyMap = {
      'start': 'zFlex-start',
      'center': 'zFlex-center',
      'end': 'zFlex-end',
      'between': 'zFlex-between',
      'around': 'zFlex-around',
      'evenly': 'zFlex-evenly'
    };
    const justifyClass = justifyMap[config.justify];
    if (justifyClass) {
      classes.push(justifyClass);
    }
  }

  // Gap
  if (typeof config.gap === 'number' && config.gap >= 0 && config.gap <= 5) {
    classes.push(`zGap-${config.gap}`);
  }

  // Flex wrap
  if (config.wrap) {
    classes.push('zFlex-wrap');
  }

  // Apply all classes at once
  if (classes.length > 0) {
    element.classList.add(...classes);
  }

  return element;
}

// ─────────────────────────────────────────────────────────────────
// Flex Utility Functions (for programmatic class generation)
// ─────────────────────────────────────────────────────────────────

/**
 * Get zTheme flex justify-content class (horizontal alignment)
 * @param {string} justify - Justify: 'start', 'center', 'end', 'between', 'around', 'evenly'
 * @returns {string} zTheme justify class
 */
export function getFlexJustifyClass(justify = 'start') {
  const justifyMap = {
    start: 'zFlex-start',
    center: 'zFlex-center',
    end: 'zFlex-end',
    between: 'zFlex-between',
    around: 'zFlex-around',
    evenly: 'zFlex-evenly'
  };

  return justifyMap[justify] || 'zFlex-start';
}

/**
 * Get zTheme flex align-items class (vertical alignment)
 * @param {string} align - Align: 'start', 'center', 'end', 'stretch', 'baseline'
 * @returns {string} zTheme align class
 */
export function getFlexAlignClass(align = 'stretch') {
  const alignMap = {
    start: 'zFlex-items-start',
    center: 'zFlex-items-center',
    end: 'zFlex-items-end',
    stretch: 'zFlex-items-stretch',
    baseline: 'zFlex-items-baseline'
  };

  return alignMap[align] || 'zFlex-items-stretch';
}

/**
 * Get zTheme flex direction class
 * @param {string} direction - Direction: 'row', 'column', 'row-reverse', 'column-reverse'
 * @returns {string} zTheme flex direction class
 */
export function getFlexDirectionClass(direction = 'row') {
  const directionMap = {
    row: 'zFlex-row',
    column: 'zFlex-column',
    'row-reverse': 'zFlex-row-reverse',
    'column-reverse': 'zFlex-column-reverse'
  };

  return directionMap[direction] || 'zFlex-row';
}

/**
 * Create a container element for a zKey with metadata support
 * @param {string} zKey - The zKey identifier
 * @param {Object} metadata - Metadata object (may contain _zClass, _zHTML)
 * @returns {Promise<HTMLElement>} Container element (div by default, or semantic element if _zHTML is specified)
 */
export async function createZKeyContainer(zKey, metadata = {}) {
  // Check for custom HTML element type (_zHTML parameter)
  const elementType = metadata._zHTML || 'div';
  
  // Validate element type (security: only allow specific semantic elements)
  const validElements = ['div', 'section', 'article', 'aside', 'nav', 'header', 'footer', 'main'];
  const tagName = validElements.includes(elementType) ? elementType : 'div';
  
  // Create the container with the specified element type
  const container = document.createElement(tagName);

  // Check for custom classes in metadata
  if (metadata._zClass !== undefined) {
    if (metadata._zClass === '' || metadata._zClass === null) {
      // Empty string or null = no container classes (opt-out)
      container.className = '';
    } else {
      // Apply custom classes
      const classes = Array.isArray(metadata._zClass)
        ? metadata._zClass
        : metadata._zClass.split(',').map(c => c.trim());
      container.className = classes.join(' ');
    }
  } else {
    // Default: responsive zTheme container
    container.className = 'zContainer-fluid zp-2';
  }

  // Set data attribute for debugging
  container.setAttribute('data-zkey', zKey);
  // Set id for DevTools navigation and CSS targeting
  container.setAttribute('id', zKey);

  return container;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createContainer,
  createSection,
  createWrapper,
  applyContainerStyles,
  getFlexJustifyClass,
  getFlexAlignClass,
  getFlexDirectionClass,
  createZKeyContainer
};

