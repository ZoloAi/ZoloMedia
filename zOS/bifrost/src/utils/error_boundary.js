/**
 * ═══════════════════════════════════════════════════════════════
 * Error Boundary Utility - Standardized Error Handling for Renderers
 * ═══════════════════════════════════════════════════════════════
 *
 * Provides error boundary wrappers for renderer methods to ensure
 * graceful degradation when rendering fails.
 */

import { createElement } from './dom_utils.js';

/**
 * Create a fallback error UI element
 * @param {Object} errorInfo - Error information
 * @param {Error} errorInfo.error - The error that occurred
 * @param {string} errorInfo.component - Component name that failed
 * @param {Object} errorInfo.data - Data that was being rendered
 * @returns {HTMLElement} Error display element
 */
export function createErrorFallback(errorInfo) {
  const { error, component = 'Component', data: _data = {} } = errorInfo;

  const container = createElement('div');
  container.className = 'bifrost-render-error';
  container.style.cssText = `
    background: #fee;
    border-left: 4px solid #c33;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 4px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    font-size: 0.875rem;
  `;

  const title = createElement('div');
  title.style.cssText = 'font-weight: 600; color: #c33; margin-bottom: 0.5rem;';
  title.textContent = `⚠️ ${component} Render Error`;

  const message = createElement('div');
  message.style.cssText = 'color: #666; margin-bottom: 0.5rem;';
  message.textContent = error.message || 'An error occurred while rendering this component';

  const details = createElement('details');
  details.style.cssText = 'margin-top: 0.5rem;';

  const summary = createElement('summary');
  summary.style.cssText = 'cursor: pointer; color: #999; font-size: 0.75rem;';
  summary.textContent = 'Show technical details';

  const stack = createElement('pre');
  stack.style.cssText = `
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: #f9f9f9;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 0.75rem;
    color: #666;
  `;
  stack.textContent = error.stack || 'No stack trace available';

  details.appendChild(summary);
  details.appendChild(stack);

  container.appendChild(title);
  container.appendChild(message);
  container.appendChild(details);

  return container;
}

/**
 * Wrap a renderer method with error boundary
 * @param {Function} renderFn - The render function to wrap
 * @param {Object} options - Options for error handling
 * @param {string} options.component - Component name for error messages
 * @param {Function} options.logger - Logger instance
 * @param {Function} options.onError - Optional error handler callback
 * @param {boolean} options.throwOnError - Whether to re-throw errors (default: false)
 * @returns {Function} Wrapped render function
 */
export function withErrorBoundary(renderFn, options = {}) {
  const {
    component = 'Unknown',
    logger = console,
    onError = null,
    throwOnError = false
  } = options;

  return function wrappedRender(...args) {
    try {
      const result = renderFn.apply(this, args);

      // Handle async render functions
      if (result && typeof result.then === 'function') {
        return result.catch(error => {
          logger.error(`[${component}] Async render error:`, error);

          if (onError) {
            try {
              onError(error, args);
            } catch (handlerError) {
              logger.error(`[${component}] Error in error handler:`, handlerError);
            }
          }

          if (throwOnError) {
            throw error;
          }

          // Return fallback UI for async errors
          return createErrorFallback({
            error,
            component,
            data: args[0]
          });
        });
      }

      return result;

    } catch (error) {
      logger.error(`[${component}] Render error:`, error);

      if (onError) {
        try {
          onError(error, args);
        } catch (handlerError) {
          logger.error(`[${component}] Error in error handler:`, handlerError);
        }
      }

      if (throwOnError) {
        throw error;
      }

      // Return fallback UI for sync errors
      return createErrorFallback({
        error,
        component,
        data: args[0]
      });
    }
  };
}

/**
 * Create a safe wrapper for renderer classes
 * @param {Class} RendererClass - The renderer class to wrap
 * @param {Object} options - Options for error handling
 * @returns {Class} Wrapped renderer class
 */
export function createSafeRenderer(RendererClass, options = {}) {
  return class SafeRenderer extends RendererClass {
    constructor(...args) {
      super(...args);

      // Wrap render method if it exists
      if (typeof this.render === 'function') {
        const originalRender = this.render.bind(this);
        this.render = withErrorBoundary(originalRender, {
          component: RendererClass.name || 'Renderer',
          logger: this.logger || console,
          ...options
        });
      }

      // Wrap renderHTML method if it exists
      if (typeof this.renderHTML === 'function') {
        const originalRenderHTML = this.renderHTML.bind(this);
        this.renderHTML = withErrorBoundary(originalRenderHTML, {
          component: `${RendererClass.name || 'Renderer'}.renderHTML`,
          logger: this.logger || console,
          ...options
        });
      }
    }
  };
}

/**
 * Decorator for renderer methods (for future use with decorators proposal)
 * Usage: @errorBoundary({ component: 'MyRenderer' })
 */
export function errorBoundary(options = {}) {
  return function decorator(target, propertyKey, descriptor) {
    const originalMethod = descriptor.value;

    descriptor.value = withErrorBoundary(originalMethod, {
      component: `${target.constructor.name}.${propertyKey}`,
      ...options
    });

    return descriptor;
  };
}
