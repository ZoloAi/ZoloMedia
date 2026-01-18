/**
 * ═══════════════════════════════════════════════════════════════
 * Image Renderer - Media Display Events
 * ═══════════════════════════════════════════════════════════════
 *
 * Terminal-First Design:
 * - Backend sends src, alt_text, caption (works with URLs and local paths)
 * - Terminal displays metadata + button to open
 * - Bifrost renders <img> element with zTheme styling
 *
 * Renders image display events from zCLI backend. Creates image
 * elements using primitives-first architecture.
 *
 * @module rendering/image_renderer
 * @layer 3
 * @pattern Primitives-First
 *
 * Dependencies:
 * - None (uses native DOM API)
 *
 * Exports:
 * - ImageRenderer: Class for rendering image events
 *
 * Example:
 * ```javascript
 * import ImageRenderer from './image_renderer.js';
 *
 * const renderer = new ImageRenderer(logger);
 * const element = renderer.render({
 *   src: 'https://picsum.photos/200/300',
 *   alt_text: 'Random Image',
 *   caption: 'A beautiful picture',
 *   _zClass: 'zRounded-circle',
 *   _id: 'profile-pic'
 * });
 * ```
 */

import { withErrorBoundary } from '../utils/error_boundary.js';

export class ImageRenderer {
  constructor(logger) {
    this.logger = logger;

    // Wrap render method with error boundary
    const originalRender = this.render.bind(this);
    this.render = withErrorBoundary(originalRender, {
      component: 'ImageRenderer',
      logger: this.logger
    });
  }

  /**
   * Render image element from primitives
   *
   * Terminal-First Design:
   * - src: Supports ANY URL (external) or path (local/relative)
   * - alt_text: Accessibility text (terminal shows this as header)
   * - caption: Optional caption (terminal shows below path)
   * - _zClass: Bifrost-only styling (e.g., zRounded-circle)
   * - _id: Bifrost-only DOM id for targeting
   *
   * @param {Object} eventData - Event data from backend
   * @param {string} eventData.src - Image source (URL or path)
   * @param {string} [eventData.alt_text] - Alternative text for accessibility
   * @param {string} [eventData.caption] - Optional caption text
   * @param {string} [eventData._zClass] - Custom classes for styling
   * @param {string} [eventData._id] - Custom id for targeting
   * @returns {HTMLElement} Image container element
   */
  render(eventData) {
    const { src, alt_text, caption, _zClass, _id } = eventData;

    if (!src) {
      this.logger.error('[ImageRenderer] Missing src parameter');
      return this._createErrorElement();
    }

    this.logger.log(`[ImageRenderer] Rendering image: ${src}`);

    // Create img element (THE primitive) - align with zTheme
    const img = document.createElement('img');
    img.src = src;  // Supports ANY URL (picsum, external, etc.) or local path

    // Apply _zClass and _id directly to img (zTheme pattern)
    if (_zClass) {
      img.className = _zClass;
    }
    if (_id) {
      img.setAttribute('id', _id);
    }

    // Add alt text for accessibility
    if (alt_text) {
      img.alt = alt_text;
    } else {
      img.alt = ''; // Empty alt for decorative images
    }

    // DON'T force inline styles - let zTheme/user control via classes
    // If user wants object-fit, they can add "zObject-fit-cover" to _zClass

    // Only wrap in <figure> if there's a caption (semantic HTML)
    if (caption) {
      const figure = document.createElement('figure');
      figure.appendChild(img);

      const figcaption = document.createElement('figcaption');
      figcaption.textContent = caption;
      figcaption.className = 'zText-muted zText-center zmt-2';
      figure.appendChild(figcaption);

      this.logger.log('[ImageRenderer] Image with caption rendered');
      return figure;
    }

    // No caption = return bare img (primitives-first + zTheme alignment!)
    this.logger.log('[ImageRenderer] Image rendered');
    return img;
  }

  /**
   * Create error element when src is missing
   * @private
   * @returns {HTMLElement}
   */
  _createErrorElement() {
    const error = document.createElement('div');
    error.className = 'zAlert zAlert-danger';
    error.textContent = '⚠️ Image source missing';
    return error;
  }
}

export default ImageRenderer;

