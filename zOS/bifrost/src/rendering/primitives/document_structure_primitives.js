/**
 * ═══════════════════════════════════════════════════════════════
 * Document Structure Primitives - Semantic HTML5 Landmarks
 * ═══════════════════════════════════════════════════════════════
 *
 * Semantic HTML5 elements that define document structure and meaning.
 * These provide accessibility landmarks and improve SEO.
 *
 * @module rendering/document_structure_primitives
 * @layer 0.0 (RAWEST - semantic structure)
 * @pattern Pure Factory Functions
 *
 * Philosophy:
 * - Semantic structure over generic divs
 * - Accessibility landmarks (ARIA roles implicit)
 * - SEO and screen reader optimization
 * - NO styling, NO classes (dress up later)
 *
 * Semantic Meaning:
 * - <header>: Introductory content or navigation (implicit role="banner" at top-level)
 * - <footer>: Footer content, copyright (implicit role="contentinfo" at top-level)
 * - <main>: Primary content (implicit role="main", ONE per page)
 * - <nav>: Navigation links (implicit role="navigation")
 * - <section>: Thematic grouping with heading (implicit role="region" if labeled)
 * - <article>: Self-contained content (implicit role="article")
 * - <aside>: Tangentially related content (implicit role="complementary")
 *
 * zReboot Context:
 * - <main> has flex: 1 (for sticky footer layouts)
 *
 * Dependencies:
 * - utils/dom_utils.js (createElement, setAttributes)
 *
 * Exports:
 * - createHeader(attributes) → HTMLElement
 * - createFooter(attributes) → HTMLElement
 * - createMain(attributes) → HTMLElement
 * - createNav(attributes) → HTMLElement
 * - createSection(attributes) → HTMLElement
 * - createArticle(attributes) → HTMLElement
 * - createAside(attributes) → HTMLElement
 *
 * Example:
 * ```javascript
 * import { createHeader, createMain, createFooter } from './document_structure_primitives.js';
 *
 * const header = createHeader({ id: 'site-header' });
 * const main = createMain({ id: 'main-content' });
 * const footer = createFooter({ id: 'site-footer' });
 *
 * document.body.appendChild(header);
 * document.body.appendChild(main);
 * document.body.appendChild(footer);
 * ```
 */

import { createElement, setAttributes } from '../../utils/dom_utils.js';

// ─────────────────────────────────────────────────────────────────
// Top-Level Structural Elements
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <header> element
 *
 * Represents introductory content or navigational aids.
 * Typically contains logo, site title, navigation, search.
 * When used at top level (direct child of <body>), has implicit role="banner".
 *
 * Common Uses:
 * - Site-wide header (logo, nav, search)
 * - Article/section headers (title, metadata)
 * - Modal/dialog headers
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLElement} The created header element
 *
 * @example
 * // Site-wide header
 * const siteHeader = createHeader({ id: 'site-header', class: 'sticky-header' });
 *
 * // Article header
 * const articleHeader = createHeader({ class: 'article-header' });
 */
export function createHeader(attributes = {}) {
  const header = createElement('header');

  if (Object.keys(attributes).length > 0) {
    setAttributes(header, attributes);
  }

  return header;
}

/**
 * Create a <footer> element
 *
 * Represents footer content for its nearest sectioning content or root.
 * Typically contains copyright, links, contact info.
 * When used at top level (direct child of <body>), has implicit role="contentinfo".
 *
 * Common Uses:
 * - Site-wide footer (copyright, links, social)
 * - Article/section footers (author, tags, share)
 * - Modal/dialog footers (action buttons)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLElement} The created footer element
 *
 * @example
 * // Site-wide footer
 * const siteFooter = createFooter({ id: 'site-footer', class: 'sticky-footer' });
 *
 * // Article footer
 * const articleFooter = createFooter({ class: 'article-footer' });
 */
export function createFooter(attributes = {}) {
  const footer = createElement('footer');

  if (Object.keys(attributes).length > 0) {
    setAttributes(footer, attributes);
  }

  return footer;
}

/**
 * Create a <main> element
 *
 * Represents the dominant/primary content of the <body>.
 * Should be UNIQUE in the document (only ONE <main> per page).
 * Has implicit role="main" for accessibility.
 *
 * zReboot: Sets flex: 1 (allows main to grow in flexbox layouts for sticky footer).
 *
 * Best Practice:
 * - Use once per page
 * - Contains the primary content (skip nav, sidebars, ads)
 * - Helps screen readers jump to main content
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLElement} The created main element
 *
 * @example
 * // Primary content area
 * const mainContent = createMain({ id: 'main-content', role: 'main' });
 *
 * // In a SPA, might toggle aria-busy during loading
 * const main = createMain({ 'aria-busy': 'true' });
 */
export function createMain(attributes = {}) {
  const main = createElement('main');

  if (Object.keys(attributes).length > 0) {
    setAttributes(main, attributes);
  }

  return main;
}

/**
 * Create a <nav> element
 *
 * Represents a section with navigation links.
 * Has implicit role="navigation" for accessibility.
 * Can have multiple <nav> elements per page (site nav, TOC, breadcrumbs).
 *
 * Best Practice:
 * - Use for major navigation blocks
 * - Consider aria-label to distinguish multiple navs
 * - Not every link group needs <nav>, just primary navigation
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, aria-label, etc.)
 * @returns {HTMLElement} The created nav element
 *
 * @example
 * // Primary site navigation
 * const mainNav = createNav({ id: 'main-nav', 'aria-label': 'Main navigation' });
 *
 * // Table of contents
 * const tocNav = createNav({ id: 'toc', 'aria-label': 'Table of contents' });
 *
 * // Breadcrumb navigation
 * const breadcrumb = createNav({ 'aria-label': 'Breadcrumb' });
 */
export function createNav(attributes = {}) {
  const nav = createElement('nav');

  if (Object.keys(attributes).length > 0) {
    setAttributes(nav, attributes);
  }

  return nav;
}

// ─────────────────────────────────────────────────────────────────
// Content Sectioning Elements
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <section> element
 *
 * Represents a thematic grouping of content, typically with a heading.
 * Groups related content together (features, testimonials, chapters).
 * Has implicit role="region" if it has an accessible name (aria-label/aria-labelledby).
 *
 * Best Practice:
 * - Should have a heading (h1-h6) as a child
 * - Use when content doesn't fit <article>, <nav>, or <aside>
 * - Think: "Would this appear in a table of contents?"
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, aria-labelledby, etc.)
 * @returns {HTMLElement} The created section element
 *
 * @example
 * // Features section
 * const features = createSection({ id: 'features', 'aria-labelledby': 'features-heading' });
 *
 * // Chapter in a document
 * const chapter = createSection({ class: 'chapter', 'data-chapter': '1' });
 */
export function createSection(attributes = {}) {
  const section = createElement('section');

  if (Object.keys(attributes).length > 0) {
    setAttributes(section, attributes);
  }

  return section;
}

/**
 * Create an <article> element
 *
 * Represents self-contained, independently distributable content.
 * Think: blog post, news article, forum post, product card, comment.
 * Has implicit role="article" for accessibility.
 *
 * Best Practice:
 * - Should make sense on its own (syndication test)
 * - Typically has a heading
 * - Can be nested (e.g., blog post with comments)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, data-*, etc.)
 * @returns {HTMLElement} The created article element
 *
 * @example
 * // Blog post
 * const post = createArticle({ id: 'post-123', class: 'blog-post' });
 *
 * // Product card in e-commerce
 * const product = createArticle({ 'data-product-id': '456', class: 'product-card' });
 *
 * // Comment
 * const comment = createArticle({ id: 'comment-789', class: 'comment' });
 */
export function createArticle(attributes = {}) {
  const article = createElement('article');

  if (Object.keys(attributes).length > 0) {
    setAttributes(article, attributes);
  }

  return article;
}

/**
 * Create an <aside> element
 *
 * Represents content tangentially related to the main content.
 * Think: sidebars, callouts, pull quotes, related links.
 * Has implicit role="complementary" when not nested in <article> or <section>.
 *
 * Best Practice:
 * - Content is related but not essential
 * - Could be moved to a sidebar without breaking flow
 * - Not for unrelated content (use <div> or other semantics)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, aria-label, etc.)
 * @returns {HTMLElement} The created aside element
 *
 * @example
 * // Sidebar with related content
 * const sidebar = createAside({ id: 'sidebar', 'aria-label': 'Related articles' });
 *
 * // Pull quote in an article
 * const pullQuote = createAside({ class: 'pull-quote' });
 *
 * // Call-to-action box
 * const cta = createAside({ class: 'cta-box', 'data-cta': 'newsletter' });
 */
export function createAside(attributes = {}) {
  const aside = createElement('aside');

  if (Object.keys(attributes).length > 0) {
    setAttributes(aside, attributes);
  }

  return aside;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createHeader,
  createFooter,
  createMain,
  createNav,
  createSection,
  createArticle,
  createAside
};

