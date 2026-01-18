/**
 * ═══════════════════════════════════════════════════════════════
 * Hooks Module - Event Hook Management
 * ═══════════════════════════════════════════════════════════════
 */

import { DarkModeToggle } from '../widgets/dark_mode_toggle.js';

export class HookManager {
  constructor(hooks = {}, logger = null) {
    this.hooks = hooks;
    this.logger = logger;
    this.errorHandler = null; // Can be set to display errors in UI
  }

  /**
   * Initialize built-in hooks (e.g., dark mode)
   */
  initBuiltInHooks() {
    // Initialize dark mode from localStorage
    const savedTheme = localStorage.getItem('zTheme-mode');
    if (savedTheme === 'dark') {
      this._applyDarkMode(true);
    }
  }

  /**
   * Apply dark mode to the page
   * @private
   */
  _applyDarkMode(isDark) {
    const body = document.body;
    const navbars = document.querySelectorAll('.zNavbar');
    const togglers = document.querySelectorAll('.zNavbar-toggler');

    if (isDark) {
      // Apply dark background to body
      body.classList.add('zBg-dark');
      body.style.backgroundColor = 'var(--color-dark)';
      // DON'T set body text color - let it cascade properly

      // Apply white text ONLY to elements outside cards
      const contentArea = document.getElementById('zVaF-content');
      if (contentArea) {
        // Apply white text to headers/titles outside cards
        contentArea.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(header => {
          if (!header.closest('.zCard')) {
            header.classList.add('zText-light');
          }
        });
        // Apply white text to paragraphs outside cards
        contentArea.querySelectorAll('p').forEach(p => {
          if (!p.closest('.zCard')) {
            p.classList.add('zText-light');
          }
        });
      }

      navbars.forEach(nav => {
        nav.classList.remove('zNavbar-light');
        nav.classList.add('zNavbar-dark');
      });
      // Apply dark mode to hamburger icon (makes it white)
      togglers.forEach(toggler => {
        toggler.classList.add('zNavbar-toggler-dark');
        // Bootstrap Icons inherit color from parent, set explicitly to white
        const icon = toggler.querySelector('i.bi');
        if (icon) {
          icon.style.color = '#ffffff';  // Direct color value instead of CSS var
        }
      });

      // Apply dark mode to theme toggle button icon (sun icon should be white)
      const themeToggleBtn = document.querySelector('.zTheme-toggle');
      if (themeToggleBtn) {
        const icon = themeToggleBtn.querySelector('i.bi');
        if (icon) {
          icon.style.color = '#ffffff';  // Direct color value instead of CSS var
        }
      }
    } else {
      // Remove dark background from body
      body.classList.remove('zBg-dark');
      body.style.backgroundColor = '';

      // Remove white text from all elements
      const contentArea = document.getElementById('zVaF-content');
      if (contentArea) {
        contentArea.querySelectorAll('.zText-light').forEach(el => {
          el.classList.remove('zText-light');
        });
      }

      navbars.forEach(nav => {
        nav.classList.remove('zNavbar-dark');
        nav.classList.add('zNavbar-light');
      });
      // Remove dark mode from hamburger icon
      togglers.forEach(toggler => {
        toggler.classList.remove('zNavbar-toggler-dark');
        // Clear inline styles to restore default color
        const icon = toggler.querySelector('i.bi');
        if (icon) {
          icon.style.color = '';
        }
      });

      // Clear theme toggle button icon color
      const themeToggleBtn = document.querySelector('.zTheme-toggle');
      if (themeToggleBtn) {
        const icon = themeToggleBtn.querySelector('i.bi');
        if (icon) {
          icon.style.color = '';
        }
      }
    }
  }

  /**
   * Set error handler for displaying errors in UI
   */
  setErrorHandler(handler) {
    this.errorHandler = handler;
  }

  /**
   * Call a hook if it exists
   */
  call(hookName, ...args) {
    const hook = this.hooks[hookName];
    if (typeof hook === 'function') {
      try {
        return hook(...args);
      } catch (error) {
        // Log to console
        this.logger.error(`[BifrostClient] Error in ${hookName} hook:`, error);

        // Log via logger if available
        if (this.logger) {
          this.logger.error(`Error in ${hookName} hook:`, error);
        }

        // Display in UI if error handler is set
        if (this.errorHandler) {
          try {
            this.errorHandler({
              type: 'hook_error',
              hookName,
              error,
              message: error.message,
              stack: error.stack
            });
          } catch (displayError) {
            this.logger.error('[BifrostClient] Error handler itself failed:', displayError);
          }
        }

        // Call onError hook if it exists and isn't the one that failed
        if (hookName !== 'onError' && this.hooks.onError) {
          try {
            this.hooks.onError(error);
          } catch (onErrorError) {
            this.logger.error('[BifrostClient] onError hook failed:', onErrorError);
          }
        }
      }
    }
  }

  /**
   * Check if a hook is registered
   */
  has(hookName) {
    return typeof this.hooks[hookName] === 'function';
  }

  /**
   * Register a new hook
   */
  register(hookName, fn) {
    if (typeof fn === 'function') {
      this.hooks[hookName] = fn;
    }
  }

  /**
   * Unregister a hook
   */
  unregister(hookName) {
    delete this.hooks[hookName];
  }

  /**
   * Get all registered hooks
   */
  list() {
    return Object.keys(this.hooks);
  }

  /**
   * Add dark mode toggle to navbar
   * This is a utility hook that can be called after navbar is rendered
   * @param {HTMLElement} navElement - The navbar element
   */
  addDarkModeToggle(navElement) {
    // Use DarkModeToggle widget (extracted for modularity)
    const darkModeWidget = new DarkModeToggle(this.logger);

    // Create toggle with theme change callback
    darkModeWidget.create(navElement, (newTheme) => {
      // Apply theme
      this._applyDarkMode(newTheme === 'dark');

      // Call onThemeChange hook if registered
      this.call('onThemeChange', newTheme);
    });
  }
}

