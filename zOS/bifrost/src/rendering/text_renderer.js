/**
 * ═══════════════════════════════════════════════════════════════
 * Text Renderer - Plain & Rich Text Display
 * ═══════════════════════════════════════════════════════════════
 *
 * Renders text events from zCLI backend, supporting both plain text
 * and rich text with markdown inline formatting.
 *
 * @module rendering/text_renderer
 * @layer 3
 * @pattern Strategy (single event type)
 *
 * Philosophy:
 * - "Terminal first" - text is the foundation of all zCLI output
 * - Pure rendering (no WebSocket, no state, no side effects)
 * - Uses Layer 2 utilities exclusively (no inline logic)
 *
 * Supported Events:
 * - 'text': Plain text with no formatting
 * - 'rich_text': Text with markdown inline syntax (NEW)
 *
 * Markdown Syntax Supported:
 * - `code` -> <code>
 * - **bold** -> <strong>
 * - *italic* -> <em>
 * - __underline__ -> <u>
 * - ~~strikethrough~~ -> <del>
 * - ==highlight== -> <mark>
 * - [text](url) -> <a href>
 * - \ (backslash + newline) -> <br> (recommended for YAML)
 * - (double-space + newline) -> <br>
 * - <br> literal tag (passes through)
 *
 * Dependencies:
 * - Layer 2: dom_utils.js, ztheme_utils.js, error_boundary.js
 *
 * Exports:
 * - TextRenderer: Class for rendering text and rich_text events
 *
 * Example:
 * ```javascript
 * import { TextRenderer } from './text_renderer.js';
 *
 * const renderer = new TextRenderer(logger);
 *
 * // Plain text (returns element, orchestrator handles appending)
 * const textEl = renderer.render({
 *   content: 'Hello, zCLI!',
 *   color: 'primary',
 *   indent: 1
 * }, 'zVaF');
 *
 * // Rich text with markdown (returns element)
 * const richTextEl = renderer.renderRichText({
 *   content: 'Use **bold** and `code` syntax',
 *   color: 'info'
 * });
 * ```
 */

// ─────────────────────────────────────────────────────────────────
// Imports
// ─────────────────────────────────────────────────────────────────
import { createElement, setAttributes } from '../utils/dom_utils.js';
import { getTextColorClass } from '../utils/ztheme_utils.js';
import { withErrorBoundary } from '../utils/error_boundary.js';
import emojiAccessibility from '../utils/emoji_accessibility.js';

// ─────────────────────────────────────────────────────────────────
// Text Renderer Class
// ─────────────────────────────────────────────────────────────────

/**
 * TextRenderer - Renders plain text events
 *
 * Handles the 'text' zDisplay event, which is the most basic
 * output primitive in zCLI. Renders a paragraph element with
 * optional color and indentation.
 */
export class TextRenderer {
  /**
   * Create a TextRenderer instance
   * @param {Object} logger - Logger instance for debugging
   */
  constructor(logger) {
    this.logger = logger || console;
    this.logger.log('[TextRenderer] ✅ Initialized');

    // Wrap render methods with error boundary
    const originalRender = this.render.bind(this);
    this.render = withErrorBoundary(originalRender, {
      component: 'TextRenderer.render',
      logger: this.logger
    });

    const originalRenderRichText = this.renderRichText.bind(this);
    this.renderRichText = withErrorBoundary(originalRenderRichText, {
      component: 'TextRenderer.renderRichText',
      logger: this.logger
    });
  }

  /**
   * Parse markdown inline syntax to HTML
   *
   * @param {string} text - Text with markdown syntax
   * @returns {string} HTML string with inline elements
   * @private
   *
   * Supported markdown:
   * - `code` -> <code>
   * - **bold** -> <strong>
   * - *italic* -> <em>
   * - __underline__ -> <u>
   * - ~~strikethrough~~ -> <del>
   * - ==highlight== -> <mark>
   * - [text](url) -> <a href="url">
   * - \ (backslash + newline) -> <br> (YAML-friendly)
   * - (double-space + newline) -> <br> (standard markdown, but YAML may strip spaces)
   * - <br> literal tag -> <br> (passes through)
   */
  _parseMarkdown(text) {
    // Trim trailing newlines to avoid extra <br> at the end
    let html = text.replace(/\n+$/, '');

    // Code blocks: ```language\ncode\n``` -> <pre><code>code</code></pre>
    // Must be processed BEFORE inline code to avoid conflicts
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (match, language, code) => {
      // Escape HTML in code
      const escapedCode = code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
      
      // Apply language class if specified
      const langClass = language ? ` language-${language}` : '';
      return `<pre class="zBg-dark zText-light zp-3 zRounded zOverflow-auto"><code class="zFont-mono${langClass}">${escapedCode}</code></pre>`;
    });

    // Links: [text](url) -> <a href="url">text</a>
    // Convert zPaths to URLs for proper navigation
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
      // Convert zPath (@.UI...) to URL path (/path/to/page)
      const href = this._convertZPathToURL(url);
      // Determine if link is internal or external
      const isInternal = url.startsWith('@') || url.startsWith('$') || url.startsWith('/') || url.startsWith('#');
      const target = isInternal ? '_self' : '_blank';
      const rel = target === '_blank' ? ' rel="noopener noreferrer"' : '';
      return `<a href="${href}" target="${target}"${rel}>${text}</a>`;
    });

    // Inline Code: `code` -> <code>code</code> (after code blocks to avoid conflicts)
    // Use placeholders to protect code content from further markdown processing
    const inlineCodeBlocks = [];
    html = html.replace(/`([^`]+)`/g, (match, code) => {
      const placeholder = `___INLINE_CODE_${inlineCodeBlocks.length}___`;
      inlineCodeBlocks.push(`<code>${code}</code>`);
      return placeholder;
    });

    // Unordered Lists: * item or - item -> <ul><li>item</li></ul>
    // Process lists before bold/italic to avoid conflicts with * markers
    html = html.replace(/(?:^|\n)((?:[*-] .+(?:\n|$))+)/g, (match, listBlock) => {
      const items = listBlock
        .split(/\n/)
        .filter(line => line.trim())
        .map(line => line.replace(/^[*-] /, '').trim())
        .map(item => `<li style="margin-bottom: 0.25rem;">${item}</li>`)
        .join('');
      return `\n<ul style="margin-top: 0.5rem; margin-bottom: 0.5rem;">${items}</ul>\n`;
    });

    // Bold: **text** -> <strong>text</strong>
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Italic: *text* -> <em>text</em> (but not ** from bold)
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Restore inline code blocks from placeholders BEFORE underline processing
    // (underline uses __ which would corrupt ___ placeholders)
    html = html.replace(/___INLINE_CODE_(\d+)___/g, (match, index) => {
      return inlineCodeBlocks[parseInt(index)];
    });

    // Underline: __text__ -> <u>text</u> (after inline code restoration)
    html = html.replace(/__([^_]+)__/g, '<u>$1</u>');

    // Strikethrough: ~~text~~ -> <del>text</del>
    html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>');

    // Highlight: ==text== -> <mark>text</mark>
    html = html.replace(/==([^=]+)==/g, '<mark>$1</mark>');

    // Line breaks: backslash + newline -> <br> (won't be stripped by YAML)
    html = html.replace(/\\\n/g, '<br>');

    // Line breaks: double-space + newline -> <br> (markdown standard, but YAML may strip)
    html = html.replace(/ {2}\n/g, '<br>');

    // Remove remaining single newlines (for text wrapping, but NOT within <pre> tags)
    // Strategy: Extract code blocks, remove newlines from text, then restore code blocks
    const codeBlocks = [];
    html = html.replace(/(<pre[\s\S]*?<\/pre>)/g, (match) => {
      const placeholder = `___CODE_BLOCK_${codeBlocks.length}___`;
      codeBlocks.push(match);
      return placeholder;
    });
    
    // NEW: Convert standalone newlines from zolo multi-line content to <br> tags
    // This preserves the natural line breaks from YAML/zolo files (e.g., multi-line content:)
    // Must happen BEFORE removing newlines
    html = html.replace(/\n/g, '<br>');
    
    // Restore code blocks with preserved newlines
    codeBlocks.forEach((block, index) => {
      html = html.replace(`___CODE_BLOCK_${index}___`, block);
    });

    // Remove leading and trailing <br> tags (caused by newlines around lists/blocks)
    html = html.replace(/^(<br>)+/, '');  // Remove leading <br>
    html = html.replace(/(<br>)+$/, '');  // Remove trailing <br>

    return html;
  }

  /**
   * Render a rich_text event with markdown parsing
   *
   * @param {Object} data - Rich text event data
   * @param {string} data.content - Text content with markdown syntax
   * @param {string} [data.color] - Text color (primary, secondary, info, success, warning, error)
   * @param {number} [data.indent=0] - Indentation level (0 = no indent)
   * @param {string} [data._zClass] - Custom CSS class (optional, from YAML)
   * @param {string} [data._id] - Custom element ID (optional)
   * @returns {HTMLElement|null} Created paragraph element or null if failed
   *
   * @example
   * renderer.renderRichText({ content: 'This is **bold** and *italic*' });
   * renderer.renderRichText({ content: 'Use `code` for commands', color: 'info' });
   */
  renderRichText(data) {
    const { content, color, indent = 0, _zClass, _id } = data;

    // Validate required parameters
    if (!content) {
      this.logger.error('[TextRenderer] ❌ Missing required parameter: content');
      return null;
    }

    // Build CSS classes array
    const classes = [];

    // Add custom class if provided (from YAML)
    if (_zClass) {
      // Split space-separated classes (e.g., "zText-center zmt-3 zmb-4")
      const customClasses = _zClass.split(/\s+/).filter(c => c);
      classes.push(...customClasses);
    }

    // Add color class if provided (uses Layer 2 utility)
    if (color) {
      const colorClass = getTextColorClass(color);
      if (colorClass) {
        classes.push(colorClass);
      }
    }

    // Create paragraph element (using Layer 2 utility)
    const p = createElement('p', classes);

    // Decode Unicode escapes first, then parse markdown, then enhance emojis for accessibility
    const decodedContent = this._decodeUnicodeEscapes(content);
    const parsedMarkdown = this._parseMarkdown(decodedContent);
    const accessibleHTML = emojiAccessibility.enhanceText(parsedMarkdown);
    p.innerHTML = accessibleHTML;
    
    // Apply syntax highlighting to code blocks (Prism.js)
    if (window.Prism) {
      const codeBlocks = p.querySelectorAll('pre code[class*="language-"]');
      console.log('[TextRenderer] 🎨 Found code blocks for highlighting:', codeBlocks.length, codeBlocks);
      codeBlocks.forEach((codeBlock) => {
        console.log('[TextRenderer] 🎨 Highlighting code block with classes:', codeBlock.className);
        Prism.highlightElement(codeBlock);
      });
    } else {
      console.warn('[TextRenderer] ⚠️  Prism not available for syntax highlighting');
    }

    // Apply attributes
    const attributes = {};

    // Apply ID if provided
    if (_id) {
      attributes.id = _id;
    }

    // Apply indent as inline style
    if (indent > 0) {
      attributes.style = `margin-left: ${indent}rem;`;
    }

    if (Object.keys(attributes).length > 0) {
      setAttributes(p, attributes);
    }

    // Log success
    this.logger.log(`[TextRenderer] ✅ Rendered rich_text (${content.length} chars, indent: ${indent})`);

    return p;
  }

  /**
   * Render a text event
   *
   * @param {Object} data - Text event data
   * @param {string} data.content - Text content to display
   * @param {string} [data.color] - Text color (primary, secondary, info, success, warning, error)
   * @param {number} [data.indent=0] - Indentation level (0 = no indent)
   * @param {string} [data.class] - Custom CSS class (optional)
   * @param {string} zone - Target DOM element ID
   * @returns {HTMLElement|null} Created paragraph element or null if failed
   *
   * @example
   * renderer.render({ content: 'Hello!' }, 'zVaF');
   * renderer.render({ content: 'Success!', color: 'success' }, 'zVaF');
   * renderer.render({ content: 'Indented', indent: 2 }, 'zVaF');
   */
  render(data, zone) {
    const { content, color, indent = 0, class: customClass } = data;

    // Validate required parameters
    if (!content) {
      this.logger.error('[TextRenderer] ❌ Missing required parameter: content');
      return null;
    }

    // Get target container
    const container = document.getElementById(zone);
    if (!container) {
      this.logger.error(`[TextRenderer] ❌ Zone not found: ${zone}`);
      return null;
    }

    // Build CSS classes array
    const classes = [];

    // Add custom class if provided (from YAML)
    if (customClass) {
      // Split space-separated classes (e.g., "zText-center zmt-3 zmb-4")
      const customClasses = customClass.split(/\s+/).filter(c => c);
      classes.push(...customClasses);
    }

    // Add color class if provided (uses Layer 2 utility)
    if (color) {
      const colorClass = getTextColorClass(color);
      if (colorClass) {
        classes.push(colorClass);
      }
    }

    // Create paragraph element (using Layer 2 utility)
    const p = createElement('p', classes);
    p.textContent = content; // Use textContent for XSS safety

    // Apply attributes
    const attributes = {};

    // Apply indent as inline style (zTheme doesn't have indent utilities)
    // Each indent level = 1rem left margin
    if (indent > 0) {
      attributes.style = `margin-left: ${indent}rem;`;
    }

    if (Object.keys(attributes).length > 0) {
      setAttributes(p, attributes);
    }

    // Append to container
    container.appendChild(p);

    // Log success
    this.logger.log(`[TextRenderer] ✅ Rendered text (${content.length} chars, indent: ${indent})`);

    return p;
  }

  /**
   * Decode Unicode escape sequences to actual characters
   * Supports: \uXXXX (standard) and \UXXXXXXXX (extended) formats
   * 
   * Note: Basic escape sequences (\n, \t, etc.) are handled by JSON.parse()
   * automatically when receiving data from backend. We only need to decode
   * custom Unicode formats that JSON doesn't handle.
   * 
   * @param {string} text - Text containing Unicode escapes
   * @returns {string} - Decoded text
   * @private
   */
  _decodeUnicodeEscapes(text) {
    if (!text || typeof text !== 'string') return text;
    
    // Replace \uXXXX format (standard 4-digit Unicode escape)
    text = text.replace(/\\u([0-9A-Fa-f]{4})/g, (match, hexCode) => {
      return String.fromCodePoint(parseInt(hexCode, 16));
    });
    
    // Replace \UXXXXXXXX format (extended 4-8 digit for supplementary characters & emojis)
    text = text.replace(/\\U([0-9A-Fa-f]{4,8})/g, (match, hexCode) => {
      return String.fromCodePoint(parseInt(hexCode, 16));
    });
    
    return text;
  }

  /**
   * Convert zPath to URL path for markdown links.
   * 
   * Example conversions:
   * - @.UI.zProducts.zTheme.zUI.zGrid.zGrid_Details → /zProducts/zTheme/zGrid
   * - @.UI.zAbout.zAbout_Details → /zAbout
   * - $zBlock → $zBlock (delta links pass through)
   * - /regular/path → /regular/path (web paths pass through)
   * 
   * @param {string} href - zPath or regular path
   * @returns {string} URL path for navigation
   * @private
   */
  _convertZPathToURL(href) {
    // Pass through delta links ($), web paths (/), and anchor links (#)
    if (!href.startsWith('@')) {
      return href;
    }
    
    // Parse zPath: @.UI.zProducts.zTheme.zUI.zGrid.zGrid_Details
    let path = href.replace(/^@\.UI\./, ''); // Remove @.UI.
    const parts = path.split('.');
    
    // Filter out zUI markers and block names
    const pathParts = parts.filter((part, index) => {
      if (part === 'zUI') return false;
      if (index === parts.length - 1 && (part.includes('_') || part.endsWith('Details') || part.endsWith('Section'))) {
        return false;
      }
      return true;
    });
    
    // Convert to /path format
    return '/' + pathParts.join('/');
  }
}

// ─────────────────────────────────────────────────────────────────
// Default Export
// ─────────────────────────────────────────────────────────────────
export default TextRenderer;

