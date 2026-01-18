/**
 * ═══════════════════════════════════════════════════════════════
 * Dark Mode Toggle Widget
 * ═══════════════════════════════════════════════════════════════
 *
 * A reusable widget for creating theme switcher buttons.
 * Supports zTheme dark/light modes with localStorage persistence.
 *
 * @module widgets/dark_mode_toggle
 * @version 1.0.0
 * @author Gal Nachshon
 *
 * ───────────────────────────────────────────────────────────────
 * Architecture:
 * - Uses primitives for DOM creation (createButton, createDiv)
 * - Self-contained logic (no external dependencies except primitives)
 * - Follows zTheme navbar structure conventions
 * ───────────────────────────────────────────────────────────────
 */

import { createButton } from '../rendering/primitives/interactive_primitives.js';
import { createDiv } from '../rendering/primitives/generic_containers.js';

/**
 * Dark Mode Toggle Widget
 * Creates and manages a theme switcher button
 */
export class DarkModeToggle {
  /**
   * Create a new DarkModeToggle instance
   * @param {Object} logger - Logger instance for debugging (optional)
   */
  constructor(logger = null) {
    this.logger = logger;
  }

  /**
   * Create and attach dark mode toggle to navbar
   * @param {HTMLElement} navElement - Navbar element to attach toggle to
   * @param {Function} onThemeChange - Callback when theme changes (optional)
   * @returns {HTMLElement|null} The created toggle button, or null if already exists
   */
  create(navElement, onThemeChange = null) {
    // Validate input
    if (!navElement) {
      if (this.logger) {
        this.logger.error('[DarkModeToggle] navElement is required');
      }
      return null;
    }

    // Check if toggle already exists
    if (navElement.querySelector('.zTheme-toggle')) {
      if (this.logger) {
        this.logger.log('[DarkModeToggle] Toggle already exists, skipping');
      }
      return null;
    }

    // Create toggle button using primitive
    const toggleBtn = createButton('button', {
      class: 'zBtn zBtn-sm zBtn-outline-secondary zTheme-toggle',
      'aria-label': 'Toggle dark mode',
      style: 'margin-left: auto;' // Push to the right
    });

    // Get current theme and set icon
    const isDark = localStorage.getItem('zTheme-mode') === 'dark';
    this._updateIcon(toggleBtn, isDark);

    // Add click handler
    toggleBtn.addEventListener('click', () => {
      const currentTheme = localStorage.getItem('zTheme-mode');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

      // Save preference
      localStorage.setItem('zTheme-mode', newTheme);

      // Apply theme to document
      this._applyTheme(newTheme === 'dark');

      // Update icon
      this._updateIcon(toggleBtn, newTheme === 'dark');

      // Call callback
      if (onThemeChange) {
        onThemeChange(newTheme);
      }

      if (this.logger) {
        this.logger.log(`[DarkModeToggle] Theme switched to: ${newTheme}`);
      }
    });

    // Attach to navbar
    this._attachToNavbar(navElement, toggleBtn);

    if (this.logger) {
      this.logger.log('[DarkModeToggle] Added to navbar');
    }

    return toggleBtn;
  }

  /**
   * Update button icon based on theme
   * @private
   * @param {HTMLElement} button - The toggle button
   * @param {boolean} isDark - Whether dark mode is active
   */
  _updateIcon(button, isDark) {
    const iconColor = isDark ? 'color: #ffffff;' : '';  // White in dark mode
    button.innerHTML = isDark
      ? `<i class="bi bi-sun-fill" style="font-size: 1.2rem; ${iconColor}"></i>`
      : `<i class="bi bi-moon-fill" style="font-size: 1.2rem; ${iconColor}"></i>`;
  }

  /**
   * Apply theme to document
   * @private
   * @param {boolean} isDark - Whether to apply dark mode
   */
  _applyTheme(isDark) {
    if (isDark) {
      document.documentElement.setAttribute('data-bs-theme', 'dark');
      document.body.classList.add('zTheme-dark');
      document.body.classList.remove('zTheme-light');
    } else {
      document.documentElement.setAttribute('data-bs-theme', 'light');
      document.body.classList.add('zTheme-light');
      document.body.classList.remove('zTheme-dark');
    }
  }

  /**
   * Attach toggle to navbar structure
   * @private
   * @param {HTMLElement} navElement - Navbar element
   * @param {HTMLElement} toggleBtn - Toggle button to attach
   */
  _attachToNavbar(navElement, toggleBtn) {
    const navCollapse = navElement.querySelector('.zNavbar-collapse');
    if (navCollapse) {
      // Create container using primitive (follows zTheme navbar structure)
      const toggleContainer = createDiv({
        class: 'zNavbar-nav zms-auto'
      });
      toggleContainer.appendChild(toggleBtn);
      navCollapse.appendChild(toggleContainer);
    } else {
      // Fallback: just append to navbar
      navElement.appendChild(toggleBtn);
    }
  }
}

export default DarkModeToggle;

