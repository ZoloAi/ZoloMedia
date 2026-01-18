/**
 * ═══════════════════════════════════════════════════════════════
 * Card Renderer - zTheme Card Components
 * ═══════════════════════════════════════════════════════════════
 *
 * Renders card/panel components aligned with zTheme card system:
 * - zCard (basic cards with proper body wrapper)
 * - zCard-header/footer (optional sections)
 * - zCard-title/subtitle/text (typography)
 * - Color variants (zCard-primary, zCard-success, etc.)
 *
 * ✨ REFACTORED: Uses Layer 0 primitives + Layer 2 utilities
 *
 * @module rendering/card_renderer
 * @layer 3
 * @pattern Strategy (card components)
 *
 * @see https://github.com/ZoloAi/zTheme/blob/main/src/css/zCards.css
 */

// ─────────────────────────────────────────────────────────────────
// Imports
// ─────────────────────────────────────────────────────────────────
import { createDiv } from './primitives/generic_containers.js';
import { createHeading, createParagraph } from './primitives/typography_primitives.js';

export default class CardRenderer {
  /**
   * Create a CardRenderer instance
   * @param {Object} logger - Logger instance for debugging
   */
  constructor(logger) {
    this.logger = logger || console;
    this.logger.log('[CardRenderer] Initialized');
  }

  /**
   * Enhance a container with proper zCard structure
   *
   * Transforms:
   *   <div class="zCard">
   *     <h2>Title</h2>
   *     <p>Content</p>
   *   </div>
   *
   * Into:
   *   <div class="zCard">
   *     <div class="zCard-body">
   *       <h2 class="zCard-title">Title</h2>
   *       <p class="zCard-text">Content</p>
   *     </div>
   *   </div>
   *
   * @param {HTMLElement} container - Container element with zCard class
   * @returns {HTMLElement} Enhanced card element
   */
  enhanceCard(container) {
    if (!container || !container.classList.contains('zCard')) {
      return container;
    }

    // Check if zCard-body already exists
    const existingBody = container.querySelector(':scope > .zCard-body');
    if (existingBody) {
      this.logger.log('[CardRenderer] Card already has zCard-body, skipping enhancement');
      return container;
    }

    // Create zCard-body wrapper (using primitive)
    const cardBody = createDiv({ class: 'zCard-body' });

    // Move all direct children into the card body
    while (container.firstChild) {
      const child = container.firstChild;

      // Apply zCard typography classes based on element type
      if (child.nodeType === Node.ELEMENT_NODE) {
        this._applyCardTypography(child);
      }

      cardBody.appendChild(child);
    }

    // Append the card body back to the container
    container.appendChild(cardBody);

    this.logger.log('[CardRenderer] Enhanced card with zCard-body wrapper');
    return container;
  }

  /**
   * Apply zCard typography classes to elements
   * @private
   * @param {HTMLElement} element - Element to enhance
   */
  _applyCardTypography(element) {
    const tagName = element.tagName.toLowerCase();

    // Apply zCard-title to first heading (h1-h6)
    if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
      // Check if this is the first heading in the card
      const parentCard = element.closest('.zCard');
      if (parentCard) {
        const existingTitle = parentCard.querySelector('.zCard-title');
        if (!existingTitle) {
          element.classList.add('zCard-title');
          this.logger.log(`[CardRenderer] Applied zCard-title to ${tagName}`);
        } else {
          // Subsequent headings could be subtitles
          element.classList.add('zCard-subtitle');
          this.logger.log(`[CardRenderer] Applied zCard-subtitle to ${tagName}`);
        }
      }
    } else if (tagName === 'p') {
      // Apply zCard-text to paragraphs
      element.classList.add('zCard-text');
      this.logger.log('[CardRenderer] Applied zCard-text to paragraph');
    }
  }

  /**
   * Create a complete card from scratch
   *
   * @param {Object} options - Card configuration
   * @param {string} [options.title] - Card title
   * @param {string} [options.subtitle] - Card subtitle
   * @param {string} [options.text] - Card text content
   * @param {string} [options.variant] - Color variant (primary, success, info, etc.)
   * @param {string} [options.header] - Header text
   * @param {string} [options.footer] - Footer text
   * @param {string} [options.classes] - Additional CSS classes
   * @returns {HTMLElement} Complete card element
   */
  createCard(options = {}) {
    const {
      title = '',
      subtitle = '',
      text = '',
      variant = null,
      header = null,
      footer = null,
      classes = ''
    } = options;

    // Create card container (using primitive)
    const card = createDiv({ class: 'zCard' });

    // Apply variant class
    if (variant) {
      card.classList.add(`zCard-${variant}`);
    }

    // Apply additional classes
    if (classes) {
      const classList = classes.split(' ').filter(c => c.trim());
      card.classList.add(...classList);
    }

    // Add header if provided (using primitive)
    if (header) {
      const headerEl = createDiv({ class: 'zCard-header' });
      headerEl.textContent = header;
      card.appendChild(headerEl);
    }

    // Create card body (using primitive)
    const cardBody = createDiv({ class: 'zCard-body' });

    // Add title (using primitive)
    if (title) {
      const titleEl = createHeading(2, { class: 'zCard-title' });
      titleEl.textContent = title;
      cardBody.appendChild(titleEl);
    }

    // Add subtitle (using primitive)
    if (subtitle) {
      const subtitleEl = createHeading(6, { class: 'zCard-subtitle zmb-2 zText-muted' });
      subtitleEl.textContent = subtitle;
      cardBody.appendChild(subtitleEl);
    }

    // Add text content (using primitive)
    if (text) {
      const textEl = createParagraph({ class: 'zCard-text' });
      textEl.textContent = text;
      cardBody.appendChild(textEl);
    }

    card.appendChild(cardBody);

    // Add footer if provided (using primitive)
    if (footer) {
      const footerEl = createDiv({ class: 'zCard-footer zText-muted' });
      footerEl.textContent = footer;
      card.appendChild(footerEl);
    }

    this.logger.log('[CardRenderer] Created card:', {title, variant, hasHeader: !!header, hasFooter: !!footer});

    return card;
  }

  /**
   * Extract card variant from color code
   * @param {string} color - Color code (PRIMARY, SUCCESS, etc.)
   * @returns {string|null} Card variant class or null
   */
  getCardVariant(color) {
    if (!color) {
      return null;
    }

    const variantMap = {
      'PRIMARY': 'primary',
      'SECONDARY': 'secondary',
      'SUCCESS': 'success',
      'INFO': 'info',
      'WARNING': 'warning',
      'DANGER': 'danger',
      'LIGHT': 'light',
      'DARK': 'dark'
    };

    return variantMap[color.toUpperCase()] || null;
  }
}
