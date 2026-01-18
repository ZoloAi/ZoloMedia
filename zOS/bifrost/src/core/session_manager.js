/**
 * ════════════════════════════════════════════════════════════════════════════
 * zCLI - SessionManager (Layer 1 Primitive)
 * ════════════════════════════════════════════════════════════════════════════
 *
 * Manages public session data on the frontend, synced with backend zSession.
 *
 * Architecture:
 *   - Public data in localStorage (username, role, session_hash)
 *   - Private data in httpOnly cookies (session token) ← backend managed
 *   - session_hash for cache invalidation
 *
 * Security:
 *   - NO sensitive data in localStorage (XSS-safe)
 *   - Session token in httpOnly cookie (backend only)
 *   - Public data for UI decisions (navbar, RBAC display)
 *
 * Usage:
 *   const session = new SessionManager(storage);
 *   await session.init();
 *
 *   // After login (backend sends session_hash)
 *   session.setPublicData({
 *       username: 'Gal Nachshon',
 *       role: 'zAdmin',
 *       session_hash: 'abc123'
 *   });
 *
 *   // Check authentication
 *   if (session.isAuthenticated()) {
 *       console.log('User:', session.get('username'));
 *   }
 *
 * @version 1.6.0
 * @since 2025-12-16
 * ════════════════════════════════════════════════════════════════════════════
 */

(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.SessionManager = factory();
  }
}(typeof self !== 'undefined' ? self : this, () => {
  'use strict';

  // ════════════════════════════════════════════════════════════════════════
  // Constants
  // ════════════════════════════════════════════════════════════════════════

  const SESSION_KEY = 'public_session';
  const DEFAULT_SESSION = {
    authenticated: false,
    username: null,
    role: null,
    session_hash: null,
    app: null,
    timestamp: null
  };

  // ════════════════════════════════════════════════════════════════════════
  // SessionManager Class
  // ════════════════════════════════════════════════════════════════════════

  class SessionManager {
    /**
         * Create a new session manager instance
         *
         * @param {StorageManager} storage - StorageManager instance for persistence
         */
    constructor(storage) {
      if (!storage) {
        throw new Error('[SessionManager] StorageManager required');
      }

      this.storage = storage;
      this.session = { ...DEFAULT_SESSION };
      this.listeners = [];

      console.log('[SessionManager] Created');
    }

    /**
         * Initialize session manager
         *
         * Loads existing session from storage (if any).
         *
         * @returns {Promise<void>}
         */
    async init() {
      // Load from storage
      const stored = await this.storage.get(SESSION_KEY, 'session');

      if (stored && this._isValidSession(stored)) {
        this.session = stored;
        console.log('[SessionManager] ✅ Restored session:', this.session.username || 'anonymous');
      } else {
        this.session = { ...DEFAULT_SESSION };
        console.log('[SessionManager] ℹ️  No valid session found, starting anonymous');
      }
    }

    /**
         * Validate session data structure
         *
         * @private
         * @param {object} session - Session object to validate
         * @returns {boolean} True if valid
         */
    _isValidSession(session) {
      return session &&
                   typeof session === 'object' &&
                   typeof session.authenticated === 'boolean' &&
                   typeof session.session_hash === 'string';
    }

    /**
         * Set public session data (after login)
         *
         * Called by BifrostClient after successful login/auth.
         *
         * @param {object} data - Public session data from backend
         * @param {string} data.username - User's display name
         * @param {string} data.role - User's role (e.g., 'zAdmin')
         * @param {string} data.session_hash - Cache invalidation token
         * @param {string} data.app - Application name
         */
    async setPublicData(data) {
      const previousHash = this.session.session_hash;

      this.session = {
        authenticated: true,
        username: data.username || null,
        role: data.role || null,
        session_hash: data.session_hash || null,
        app: data.app || null,
        timestamp: Date.now()
      };

      // Persist to storage
      await this.storage.set(SESSION_KEY, this.session, 'session');

      console.log('[SessionManager] ✅ Session updated:', this.session.username);

      // Notify listeners (e.g., cache invalidation if hash changed)
      if (previousHash !== this.session.session_hash) {
        this._notifyListeners('session_changed', this.session);
      }
    }

    /**
         * Clear session (logout)
         *
         * Removes public session data. Backend handles cookie removal.
         */
    async clear() {
      const previousUsername = this.session.username;

      this.session = { ...DEFAULT_SESSION };
      await this.storage.remove(SESSION_KEY, 'session');

      console.log('[SessionManager] ✅ Session cleared:', previousUsername);

      // Notify listeners (e.g., clear caches)
      this._notifyListeners('session_cleared');
    }

    /**
         * Check if user is authenticated
         *
         * @returns {boolean} True if authenticated
         */
    isAuthenticated() {
      return this.session.authenticated === true;
    }

    /**
         * Check if user is a guest (not authenticated)
         *
         * @returns {boolean} True if guest
         */
    isGuest() {
      return !this.isAuthenticated();
    }

    /**
         * Get session property
         *
         * @param {string} key - Property key (e.g., 'username', 'role', 'session_hash')
         * @returns {any} Property value or null
         */
    get(key) {
      return this.session[key] || null;
    }

    /**
         * Get entire session object (read-only)
         *
         * @returns {object} Session data (shallow copy)
         */
    getAll() {
      return { ...this.session };
    }

    /**
         * Get session hash (for cache validation)
         *
         * @returns {string|null} Session hash or null
         */
    getHash() {
      return this.session.session_hash;
    }

    /**
         * Check if user has a specific role
         *
         * @param {string} role - Role name (e.g., 'zAdmin')
         * @returns {boolean} True if user has role
         */
    hasRole(role) {
      return this.session.role === role;
    }

    /**
         * Add listener for session changes
         *
         * @param {Function} callback - Callback function (event, data)
         */
    addListener(callback) {
      if (typeof callback === 'function') {
        this.listeners.push(callback);
      }
    }

    /**
         * Remove listener
         *
         * @param {Function} callback - Callback function to remove
         */
    removeListener(callback) {
      const index = this.listeners.indexOf(callback);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    }

    /**
         * Notify all listeners of an event
         *
         * @private
         * @param {string} event - Event name ('session_changed', 'session_cleared')
         * @param {any} data - Event data
         */
    _notifyListeners(event, data = null) {
      this.listeners.forEach(callback => {
        try {
          callback(event, data);
        } catch (error) {
          console.error('[SessionManager] Listener error:', error);
        }
      });
    }

    /**
         * Debug: Print session state
         */
    debug() {
      console.log('[SessionManager] Current session:', {
        authenticated: this.session.authenticated,
        username: this.session.username,
        role: this.session.role,
        hash: this.session.session_hash,
        app: this.session.app
      });
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // Export
  // ════════════════════════════════════════════════════════════════════════

  return SessionManager;
}));

