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
   * Supports plain text items, nested arrays, and nested zDisplay events
   * NEW v1.7: Supports cascading styles for nested arrays!
   * @param {Object} eventData - zDisplay event data with items array
   * @param {number} level - Internal: current nesting level for cascading (default: 0)
   * @returns {Promise<HTMLElement>} - Rendered list element (ul or ol)
   */
  async render(eventData, level = 0) {
    this.logger.log(`[ListRenderer] Rendering list with ${eventData.items?.length || 0} items (level ${level})`);

    // Determine current style based on cascading
    let currentStyle;
    let cascadeStyles = null;
    
    if (Array.isArray(eventData.style)) {
      // Cascading styles: cycle through array based on nesting level
      cascadeStyles = eventData.style;
      currentStyle = eventData.style[level % eventData.style.length];
      this.logger.log(`[ListRenderer] Using cascading style: ${currentStyle} (level ${level})`);
    } else {
      // Single style: use for all levels
      currentStyle = eventData.style || 'bullet';
    }

    // Determine list element type and CSS list-style-type
    let listElement;
    let listStyleType = null;
    
    if (currentStyle === 'number') {
      listElement = document.createElement('ol');
    } else if (currentStyle === 'letter') {
      listElement = document.createElement('ol');
      listStyleType = 'lower-alpha';  // a, b, c
    } else if (currentStyle === 'roman') {
      listElement = document.createElement('ol');
      listStyleType = 'lower-roman';  // i, ii, iii
    } else if (currentStyle === 'circle') {
      listElement = document.createElement('ul');
      listStyleType = 'circle';  // ○
    } else if (currentStyle === 'square') {
      listElement = document.createElement('ul');
      listStyleType = 'square';  // ▪
    } else {
      // bullet (default) or any other style
      listElement = document.createElement('ul');
    }

    // Apply base zTheme class
    listElement.className = 'zList';

    // Apply list-style-type if specified
    if (listStyleType) {
      listElement.style.listStyleType = listStyleType;
    }

    // Apply custom classes if provided (from YAML `_zClass` parameter - ignored by terminal)
    // Only apply custom classes at top level (level 0)
    if (level === 0 && eventData._zClass) {
      listElement.className += ` ${eventData._zClass}`;
    }

    // Apply indent using zms (margin-start) classes
    if (eventData.indent && eventData.indent > 0) {
      listElement.className += ` zms-${eventData.indent}`;
    }

    // Apply custom id if provided (_id parameter - ignored by terminal)
    if (level === 0 && eventData._id) {
      listElement.setAttribute('id', eventData._id);
    }

    // Check if this is an inline list (for horizontal layout)
    const isInline = level === 0 && eventData._zClass && eventData._zClass.includes('zList-inline');

    // Render list items (async to support nested zDisplay events)
    const items = eventData.items || [];
    let lastLi = null;  // Track last created <li> for appending nested lists
    
    for (const item of items) {
      // NEW v1.7: Handle nested arrays naturally!
      if (Array.isArray(item)) {
        this.logger.log('[ListRenderer] Rendering nested array - appending to previous list item');
        
        // Nested array should be appended to the PREVIOUS list item
        if (lastLi) {
          try {
            const nestedEventData = {
              items: item,
              style: cascadeStyles || currentStyle,  // Pass cascading styles or current style
              indent: 0  // Nested lists use native HTML indentation
            };
            const nestedList = await this.render(nestedEventData, level + 1);
            lastLi.appendChild(nestedList);
          } catch (error) {
            this.logger.error('[ListRenderer] Error rendering nested array:', error);
            lastLi.textContent += ` [Error: ${error.message}]`;
          }
        } else {
          this.logger.warn('[ListRenderer] Nested array without previous list item - creating standalone');
          // Fallback: create a new <li> if no previous item exists
          const li = document.createElement('li');
          try {
            const nestedEventData = {
              items: item,
              style: cascadeStyles || currentStyle,
              indent: 0
            };
            const nestedList = await this.render(nestedEventData, level + 1);
            li.appendChild(nestedList);
            listElement.appendChild(li);
            lastLi = li;
          } catch (error) {
            this.logger.error('[ListRenderer] Error rendering nested array:', error);
            li.textContent = `[Error: ${error.message}]`;
            listElement.appendChild(li);
            lastLi = li;
          }
        }
        // Don't update lastLi - nested arrays attach to previous item
        continue;
      }

      // Create new <li> for non-array items
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
      lastLi = li;  // Track this as the last created <li>
    }

    this.logger.log(`[ListRenderer] ✅ Rendered ${currentStyle} list with ${items.length} items`);
    return listElement;
  }
}

export default ListRenderer;
