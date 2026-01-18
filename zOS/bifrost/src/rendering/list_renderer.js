/**
 * ListRenderer - Renders list elements (ul/ol) with zTheme styling
 * Part of the modular bifrost rendering architecture
 */

import { withErrorBoundary } from '../utils/error_boundary.js';

export class ListRenderer {
  constructor(client) {
    this.client = client;
    this.logger = client.logger;

    // Wrap render method with error boundary
    const originalRender = this.render.bind(this);
    this.render = withErrorBoundary(originalRender, {
      component: 'ListRenderer',
      logger: this.logger
    });
  }

  /**
   * Render a list element (bulleted or numbered)
   * Supports both plain text items and nested zDisplay events
   * @param {Object} eventData - zDisplay event data with items array
   * @returns {Promise<HTMLElement>} - Rendered list element (ul or ol)
   */
  async render(eventData) {
    this.logger.log(`[ListRenderer] Rendering list with ${eventData.items?.length || 0} items`);

    // Check style: "number" → <ol>, "bullet" → <ul> (default)
    const style = eventData.style || 'bullet';
    const listElement = style === 'number'
      ? document.createElement('ol')
      : document.createElement('ul');

    // Apply base zTheme class
    listElement.className = 'zList';

    // Apply custom classes if provided (from YAML `_zClass` parameter - ignored by terminal)
    if (eventData._zClass) {
      listElement.className += ` ${eventData._zClass}`;
    }

    // Apply indent using zms (margin-start) classes
    if (eventData.indent && eventData.indent > 0) {
      listElement.className += ` zms-${eventData.indent}`;
    }

    // Apply custom id if provided (_id parameter - ignored by terminal)
    if (eventData._id) {
      listElement.setAttribute('id', eventData._id);
    }

    // Check if this is an inline list (for horizontal layout)
    const isInline = eventData._zClass && eventData._zClass.includes('zList-inline');

    // Render list items (async to support nested zDisplay events)
    const items = eventData.items || [];
    for (const item of items) {
      const li = document.createElement('li');

      // Apply zList-inline-item class if this is an inline list
      if (isInline) {
        li.className = 'zList-inline-item';
      }

      // Check if item contains a nested zDisplay event
      if (item && typeof item === 'object' && item.zDisplay) {
        this.logger.log('[ListRenderer] Rendering nested zDisplay event in list item');
        
        // Recursively render the nested zDisplay event
        try {
          const nestedElement = await this.client.zDisplayOrchestrator.renderZDisplayEvent(item.zDisplay);
          if (nestedElement) {
            li.appendChild(nestedElement);
          } else {
            this.logger.warn('[ListRenderer] Nested zDisplay returned null, using fallback');
            li.textContent = JSON.stringify(item);
          }
        } catch (error) {
          this.logger.error('[ListRenderer] Error rendering nested zDisplay:', error);
          li.textContent = `[Error: ${error.message}]`;
        }
      } else {
        // Plain text item (original behavior)
        const content = typeof item === 'string' ? item : (item.content || '');
        li.textContent = content;
      }

      listElement.appendChild(li);
    }

    this.logger.log(`[ListRenderer] ✅ Rendered ${style} list with ${items.length} items`);
    return listElement;
  }
}

export default ListRenderer;
