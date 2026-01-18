/**
 * SpinnerRenderer - Render loading spinners
 *
 * Terminal-first implementation matching backend zDisplay.spinner()
 *
 * Backend Events (from display_event_timebased.py):
 * - spinner_start: { event, spinnerId, label, style, container }
 * - spinner_stop: { event, spinnerId }
 *
 * Spinner Styles (matching terminal):
 * - dots: ⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
 * - line: - \ | /
 * - arc: ◜ ◠ ◝ ◞ ◡ ◟
 * - bouncingBall: ( ●    ) (  ●   ) (   ●  ) (    ● )
 * - simple: . .. ...
 *
 * Terminal Paradigm:
 * - Context manager: with display.spinner("Loading"): do_work()
 * - Background thread animates frames
 * - Auto-cleanup with checkmark on completion
 *
 * Bifrost Paradigm:
 * - WebSocket events trigger start/stop
 * - CSS animations handle visual feedback
 * - Multiple spinners can be active simultaneously
 *
 * Features:
 * - Size variants (sm, md, lg)
 * - Color variants (primary, secondary, success, danger, warning, info)
 * - CSS animations (no JavaScript required after rendering)
 * - Auto-cleanup on stop
 *
 * @see https://github.com/ZoloAi/zTheme/blob/main/Manual/ztheme-spinners.html
 */

import { createDiv } from './primitives/generic_containers.js';
import { createSpan } from './primitives/generic_containers.js';
import { applySpinnerSize } from '../utils/size_utils.js';

export default class SpinnerRenderer {
  /**
   * @param {Object} logger - Logger instance
   */
  constructor(logger) {
    this.logger = logger;
    this._activeSpinners = new Map(); // Track active spinners by spinnerId
  }

  /**
   * Start a spinner (spinner_start event)
   * @param {Object} event - Spinner start event
   * @param {string} event.spinnerId - Unique spinner ID
   * @param {string} event.label - Spinner label text
   * @param {string} event.style - Spinner style (dots, line, arc, etc.)
   * @param {string} event.container - Target container selector
   * @param {string} [event.size='md'] - Spinner size (sm, md, lg)
   * @param {string} [event.color='primary'] - Spinner color
   * @returns {HTMLElement} Spinner container element
   */
  start(event) {
    const {
      spinnerId,
      label = 'Loading...',
      style = 'dots',
      container = '#app',
      size = 'md',
      color = 'primary'
    } = event;

    this.logger.log('[SpinnerRenderer] Starting spinner:', { spinnerId, label, style });

    // Create spinner structure using primitives
    const spinnerContainer = this._createSpinnerContainer(spinnerId, label, size, color);

    // Find target container
    const targetElement = document.querySelector(container) || document.body;
    targetElement.appendChild(spinnerContainer);

    // Track active spinner
    this._activeSpinners.set(spinnerId, {
      element: spinnerContainer,
      label,
      startTime: Date.now()
    });

    this.logger.log('[SpinnerRenderer] Spinner started successfully');
    return spinnerContainer;
  }

  /**
   * Stop a spinner (spinner_stop event)
   * @param {Object} event - Spinner stop event
   * @param {string} event.spinnerId - Unique spinner ID
   * @param {boolean} [event.success=true] - Whether operation succeeded
   * @param {string} [event.message] - Optional completion message
   */
  stop(event) {
    const { spinnerId, success = true, message } = event;

    this.logger.log('[SpinnerRenderer] Stopping spinner:', { spinnerId, success });

    const spinnerData = this._activeSpinners.get(spinnerId);
    if (!spinnerData) {
      this.logger.warn('[SpinnerRenderer] Spinner not found:', spinnerId);
      return;
    }

    const { element, label, startTime } = spinnerData;
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);

    // Replace spinner with completion message
    this._replaceWithCompletion(element, label, success, message, duration);

    // Remove from active spinners
    this._activeSpinners.delete(spinnerId);

    this.logger.log('[SpinnerRenderer] Spinner stopped successfully');
  }

  /**
   * Create spinner container using primitives
   * @private
   */
  _createSpinnerContainer(spinnerId, label, size, color) {
    // Main container (using primitive)
    const container = createDiv({
      id: spinnerId,
      class: 'zSpinner-container zD-flex zFlex-items-center zGap-2 zMy-2'
    });

    // Determine spinner classes
    // zTheme has .zSpinner-border-sm for small, but no -md or -lg
    // TODO: Add .zSpinner-border-md and .zSpinner-border-lg to zTheme
    // See: https://github.com/ZoloAi/zTheme/blob/main/Manual/ztheme-spinners.html
    let spinnerClass = 'zSpinner-border';
    if (size === 'sm') {
      spinnerClass = 'zSpinner-border-sm'; // Use zTheme's built-in small size
    }

    // Spinner element (using primitive + zTheme classes)
    const spinner = createDiv({
      class: `${spinnerClass} zText-${color}`,
      role: 'status'
    });

    // For md/lg sizes, apply inline styles using size_utils
    // TODO: Remove this once zTheme has full size scale (.zSpinner-border-md, .zSpinner-border-lg)
    if (size === 'md' || size === 'lg') {
      applySpinnerSize(spinner, size);
    }

    // Accessibility label (using primitive)
    const srOnly = createSpan({
      class: 'zVisually-hidden'
    });
    srOnly.textContent = 'Loading...';
    spinner.appendChild(srOnly);

    // Label text (using primitive)
    const labelSpan = createSpan({
      class: 'zSpinner-label zText-muted'
    });
    labelSpan.textContent = label;

    // Assemble spinner
    container.appendChild(spinner);
    container.appendChild(labelSpan);

    return container;
  }

  /**
   * Replace spinner with completion message
   * @private
   */
  _replaceWithCompletion(element, label, success, message, duration) {
    // Clear spinner content
    element.innerHTML = '';

    // Create completion icon (checkmark or X)
    const icon = document.createElement('i');
    icon.className = success
      ? 'bi bi-check-circle-fill zText-success'
      : 'bi bi-x-circle-fill zText-danger';
    icon.style.fontSize = '1.2rem';

    // Create completion message (using primitive)
    const messageSpan = createSpan({
      class: success ? 'zText-success' : 'zText-danger'
    });
    messageSpan.textContent = message || `${label} ${success ? '✓' : '✗'}`;

    // Create duration badge (using primitive)
    const durationBadge = createSpan({
      class: 'zBadge zBadge-secondary zMs-2'
    });
    durationBadge.textContent = `${duration}s`;

    // Assemble completion message
    element.appendChild(icon);
    element.appendChild(document.createTextNode(' '));
    element.appendChild(messageSpan);
    element.appendChild(durationBadge);

    // Remove classes
    element.className = 'zSpinner-complete zD-flex zFlex-items-center zGap-2 zMy-2';

    // Auto-remove after 3 seconds (optional)
    setTimeout(() => {
      if (element.parentNode) {
        element.style.transition = 'opacity 0.3s';
        element.style.opacity = '0';
        setTimeout(() => {
          if (element.parentNode) {
            element.parentNode.removeChild(element);
          }
        }, 300);
      }
    }, 3000);
  }

  /**
   * Stop all active spinners (cleanup utility)
   * @param {boolean} [success=true] - Whether operations succeeded
   */
  stopAll(success = true) {
    this.logger.log('[SpinnerRenderer] Stopping all spinners');

    for (const [spinnerId, _data] of this._activeSpinners) {
      this.stop({ spinnerId, success });
    }
  }

  /**
   * Get active spinner count
   * @returns {number} Number of active spinners
   */
  getActiveCount() {
    return this._activeSpinners.size;
  }
}
