/**
 * ═══════════════════════════════════════════════════════════════
 * Typography Primitives - Raw Text Content Elements
 * ═══════════════════════════════════════════════════════════════
 *
 * Core text content elements: headings and paragraphs.
 * These define document structure and readable text blocks.
 *
 * @module rendering/typography_primitives
 * @layer 0.0 (RAWEST - text primitives)
 * @pattern Pure Factory Functions
 *
 * Philosophy:
 * - Semantic hierarchy (h1-h6 for document structure)
 * - Block-level text (paragraphs)
 * - NO styling, NO classes (dress up later)
 * - zReboot.css provides baseline (margins, font-sizes, line-height)
 *
 * zReboot Defaults (from zTheme):
 * - Headings: margin-top: 0, margin-bottom: 0.5rem, font-weight: 500, line-height: 1.2
 * - Paragraph: margin-top: 0, margin-bottom: 1rem
 *
 * Dependencies:
 * - utils/dom_utils.js (createElement, setAttributes)
 *
 * Exports:
 * - createHeading(level, attributes) → HTMLHeadingElement (h1-h6)
 * - createParagraph(attributes) → HTMLParagraphElement
 *
 * Example:
 * ```javascript
 * import { createHeading, createParagraph } from './typography_primitives.js';
 *
 * // Raw elements
 * const title = createHeading(1, { id: 'page-title' });
 * title.textContent = 'Welcome';
 *
 * const text = createParagraph({ class: 'intro' });
 * text.textContent = 'This is the introduction.';
 * ```
 */

import { createElement, setAttributes } from '../../utils/dom_utils.js';

// ─────────────────────────────────────────────────────────────────
// Heading Elements (h1-h6)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a heading element (<h1> through <h6>)
 *
 * Used for document structure and content hierarchy.
 * Level is enforced: 1-6 only (defaults to 1, caps at 6).
 *
 * Semantic Meaning:
 * - h1: Page title (typically one per page)
 * - h2: Major sections
 * - h3: Subsections
 * - h4-h6: Further nested subsections
 *
 * zReboot Defaults:
 * - h1: 2.5rem (40px)
 * - h2: 2rem (32px)
 * - h3: 1.75rem (28px)
 * - h4: 1.5rem (24px)
 * - h5: 1.25rem (20px)
 * - h6: 1rem (16px)
 *
 * @param {number} [level=1] - Heading level (1-6), enforced and capped
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLHeadingElement} The created heading element (h1-h6)
 *
 * @example
 * // Page title (h1)
 * const title = createHeading(1, { id: 'page-title' });
 * title.textContent = 'My Application';
 *
 * // Section header (h2)
 * const sectionTitle = createHeading(2);
 * sectionTitle.textContent = 'Features';
 *
 * // Subsection (h3)
 * const subsection = createHeading(3, { class: 'subsection-header' });
 *
 * // Invalid level (caps at h6)
 * const invalid = createHeading(10);  // Creates h6 with console warning
 */
export function createHeading(level = 1, attributes = {}) {
  // Enforce level 1-6 (cap at h6 for invalid levels)
  const rawLevel = parseInt(level);

  if (isNaN(rawLevel) || rawLevel < 1) {
    console.warn(`[typography_primitives] createHeading: Invalid level "${level}", defaulting to 1`);
    level = 1;
  } else if (rawLevel > 6) {
    console.warn(`[typography_primitives] createHeading: Level ${rawLevel} exceeds h6, capping at 6`);
    level = 6;
  } else {
    level = rawLevel;
  }

  const tag = `h${level}`;
  const heading = createElement(tag);

  if (Object.keys(attributes).length > 0) {
    setAttributes(heading, attributes);
  }

  return heading;
}

// ─────────────────────────────────────────────────────────────────
// Paragraph Element
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <p> (paragraph) element
 *
 * Used for blocks of text content (body copy, descriptions, etc.).
 * The most common text container in web documents.
 *
 * zReboot Defaults:
 * - margin-top: 0
 * - margin-bottom: 1rem
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLParagraphElement} The created paragraph element
 *
 * @example
 * // Basic paragraph
 * const intro = createParagraph();
 * intro.textContent = 'Welcome to our application.';
 *
 * // Paragraph with class
 * const lead = createParagraph({ class: 'lead' });
 * lead.textContent = 'This is a lead paragraph.';
 *
 * // Paragraph with data attribute
 * const content = createParagraph({ 'data-section': 'intro', id: 'intro-text' });
 */
export function createParagraph(attributes = {}) {
  const p = createElement('p');

  if (Object.keys(attributes).length > 0) {
    setAttributes(p, attributes);
  }

  return p;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createHeading,
  createParagraph
};

