/**
 * ════════════════════════════════════════════════════════════════════════════
 * zCLI - StorageManager (Layer 0 Primitive)
 * ════════════════════════════════════════════════════════════════════════════
 *
 * Unified storage interface with progressive enhancement:
 * - Primary: IndexedDB (~50MB, async, modern browsers)
 * - Fallback: localStorage (~5-10MB, sync, universal)
 *
 * Mirrors zLoader's backend cache architecture for consistency.
 *
 * Usage:
 *   const storage = new StorageManager('zBifrost');
 *   await storage.init();
 *   await storage.set('key', {data: 'value'}, 'system');
 *   const data = await storage.get('key', 'system');
 *
 * Architecture:
 *   - Single unified interface (get/set/clear/remove)
 *   - Automatic fallback (IndexedDB → localStorage)
 *   - Namespace isolation (prevents key collisions)
 *   - Type-safe (validates JSON serialization)
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
    root.StorageManager = factory();
  }
}(typeof self !== 'undefined' ? self : this, () => {
  'use strict';

  // ════════════════════════════════════════════════════════════════════════
  // Constants
  // ════════════════════════════════════════════════════════════════════════

  const DB_VERSION = 1;
  const STORE_NAMES = ['system', 'pinned', 'plugin', 'rendered']; // session is in-memory only

  // ════════════════════════════════════════════════════════════════════════
  // StorageManager Class
  // ════════════════════════════════════════════════════════════════════════

  class StorageManager {
    /**
         * Create a new storage manager instance
         *
         * @param {string} namespace - Namespace for storage isolation (e.g., 'zBifrost')
         */
    constructor(namespace = 'zBifrost') {
      this.namespace = namespace;
      this.dbName = `${namespace}_cache`;
      this.db = null;
      this.useIndexedDB = false;
      this.useLocalStorage = false;
      this.initialized = false;

      // In-memory session cache (never persisted)
      this.sessionCache = new Map();

      console.log(`[StorageManager] Created with namespace: ${namespace}`);
    }

    /**
         * Initialize storage (must be called before use)
         *
         * Attempts IndexedDB first, falls back to localStorage if unavailable.
         *
         * @returns {Promise<boolean>} Success status
         */
    async init() {
      if (this.initialized) {
        console.log('[StorageManager] Already initialized');
        return true;
      }

      // Try IndexedDB first (modern, async, large capacity)
      try {
        await this._initIndexedDB();
        this.useIndexedDB = true;
        console.log('[StorageManager] ✅ Initialized with IndexedDB');
        this.initialized = true;
        return true;
      } catch (error) {
        console.warn('[StorageManager] ⚠️  IndexedDB unavailable, falling back to localStorage:', error.message);
      }

      // Fallback to localStorage (universal, sync, limited capacity)
      try {
        this._initLocalStorage();
        this.useLocalStorage = true;
        console.log('[StorageManager] ✅ Initialized with localStorage (fallback)');
        this.initialized = true;
        return true;
      } catch (error) {
        console.error('[StorageManager] ❌ Both IndexedDB and localStorage unavailable:', error);
        this.initialized = false;
        return false;
      }
    }

    /**
         * Initialize IndexedDB
         *
         * Creates object stores for each cache tier (system, pinned, plugin, rendered).
         * Session cache is in-memory only and not persisted.
         *
         * @private
         * @returns {Promise<void>}
         */
    _initIndexedDB() {
      return new Promise((resolve, reject) => {
        if (!window.indexedDB) {
          reject(new Error('IndexedDB not supported'));
          return;
        }

        const request = indexedDB.open(this.dbName, DB_VERSION);

        request.onerror = () => {
          reject(new Error(`IndexedDB open failed: ${request.error}`));
        };

        request.onsuccess = () => {
          this.db = request.result;
          console.log(`[StorageManager] IndexedDB opened: ${this.dbName}`);
          resolve();
        };

        request.onupgradeneeded = (event) => {
          const db = event.target.result;

          // Create object stores for each cache tier
          STORE_NAMES.forEach(storeName => {
            if (!db.objectStoreNames.contains(storeName)) {
              const store = db.createObjectStore(storeName, { keyPath: 'key' });
              store.createIndex('timestamp', 'timestamp', { unique: false });
              console.log(`[StorageManager] Created object store: ${storeName}`);
            }
          });
        };
      });
    }

    /**
         * Initialize localStorage (fallback)
         *
         * Validates localStorage is available and writable.
         *
         * @private
         */
    _initLocalStorage() {
      if (typeof localStorage === 'undefined') {
        throw new Error('localStorage not supported');
      }

      // Test write/read
      const testKey = `${this.namespace}_test`;
      try {
        localStorage.setItem(testKey, 'test');
        localStorage.removeItem(testKey);
      } catch (error) {
        throw new Error(`localStorage not writable: ${error.message}`);
      }
    }

    /**
         * Get value from storage
         *
         * @param {string} key - Storage key
         * @param {string} tier - Cache tier ('system', 'pinned', 'plugin', 'session', 'rendered')
         * @returns {Promise<any|null>} Stored value or null if not found
         */
    async get(key, tier = 'system') {
      if (!this.initialized) {
        console.warn('[StorageManager] Not initialized, call init() first');
        return null;
      }

      // Session cache is in-memory only
      if (tier === 'session') {
        return this.sessionCache.get(key) || null;
      }

      // Try persistent storage
      if (this.useIndexedDB) {
        return await this._getFromIndexedDB(key, tier);
      } else if (this.useLocalStorage) {
        return this._getFromLocalStorage(key, tier);
      }

      return null;
    }

    /**
         * Set value in storage
         *
         * @param {string} key - Storage key
         * @param {any} value - Value to store (must be JSON-serializable)
         * @param {string} tier - Cache tier ('system', 'pinned', 'plugin', 'session', 'rendered')
         * @param {number} ttl - Time-to-live in milliseconds (optional, for cache validation)
         * @returns {Promise<boolean>} Success status
         */
    async set(key, value, tier = 'system', ttl = null) {
      if (!this.initialized) {
        console.warn('[StorageManager] Not initialized, call init() first');
        return false;
      }

      // Validate JSON serialization
      try {
        JSON.stringify(value);
      } catch (error) {
        console.error('[StorageManager] Value not JSON-serializable:', error);
        return false;
      }

      // Session cache is in-memory only
      if (tier === 'session') {
        this.sessionCache.set(key, value);
        return true;
      }

      // Add metadata
      const entry = {
        key: key,
        value: value,
        timestamp: Date.now(),
        ttl: ttl
      };

      // Store persistently
      if (this.useIndexedDB) {
        return await this._setInIndexedDB(entry, tier);
      } else if (this.useLocalStorage) {
        return this._setInLocalStorage(entry, tier);
      }

      return false;
    }

    /**
         * Remove value from storage
         *
         * @param {string} key - Storage key
         * @param {string} tier - Cache tier
         * @returns {Promise<boolean>} Success status
         */
    async remove(key, tier = 'system') {
      if (!this.initialized) {
        console.warn('[StorageManager] Not initialized, call init() first');
        return false;
      }

      if (tier === 'session') {
        return this.sessionCache.delete(key);
      }

      if (this.useIndexedDB) {
        return await this._removeFromIndexedDB(key, tier);
      } else if (this.useLocalStorage) {
        return this._removeFromLocalStorage(key, tier);
      }

      return false;
    }

    /**
         * Clear entire cache tier
         *
         * @param {string} tier - Cache tier to clear (or 'all' to clear everything)
         * @returns {Promise<boolean>} Success status
         */
    async clear(tier = 'all') {
      if (!this.initialized) {
        console.warn('[StorageManager] Not initialized, call init() first');
        return false;
      }

      const tiersToClean = tier === 'all' ? ['system', 'pinned', 'plugin', 'session', 'rendered'] : [tier];

      for (const t of tiersToClean) {
        if (t === 'session') {
          this.sessionCache.clear();
        } else if (this.useIndexedDB) {
          await this._clearIndexedDBStore(t);
        } else if (this.useLocalStorage) {
          this._clearLocalStorageTier(t);
        }
      }

      console.log(`[StorageManager] Cleared tier(s): ${tier}`);
      return true;
    }

    /**
         * Get all keys in a tier
         *
         * @param {string} tier - Cache tier
         * @returns {Promise<string[]>} Array of keys
         */
    async keys(tier = 'system') {
      if (!this.initialized) {
        return [];
      }

      if (tier === 'session') {
        return Array.from(this.sessionCache.keys());
      }

      if (this.useIndexedDB) {
        return await this._getIndexedDBKeys(tier);
      } else if (this.useLocalStorage) {
        return this._getLocalStorageKeys(tier);
      }

      return [];
    }

    // ════════════════════════════════════════════════════════════════════
    // IndexedDB Private Methods
    // ════════════════════════════════════════════════════════════════════

    _getFromIndexedDB(key, tier) {
      return new Promise((resolve, _reject) => {
        try {
          const transaction = this.db.transaction([tier], 'readonly');
          const store = transaction.objectStore(tier);
          const request = store.get(key);

          request.onsuccess = () => {
            const entry = request.result;
            resolve(entry ? entry.value : null);
          };

          request.onerror = () => {
            console.error('[StorageManager] IndexedDB get error:', request.error);
            resolve(null);
          };
        } catch (error) {
          console.error('[StorageManager] IndexedDB get exception:', error);
          resolve(null);
        }
      });
    }

    _setInIndexedDB(entry, tier) {
      return new Promise((resolve, _reject) => {
        try {
          const transaction = this.db.transaction([tier], 'readwrite');
          const store = transaction.objectStore(tier);
          const request = store.put(entry);

          request.onsuccess = () => resolve(true);
          request.onerror = () => {
            console.error('[StorageManager] IndexedDB set error:', request.error);
            resolve(false);
          };
        } catch (error) {
          console.error('[StorageManager] IndexedDB set exception:', error);
          resolve(false);
        }
      });
    }

    _removeFromIndexedDB(key, tier) {
      return new Promise((resolve) => {
        try {
          const transaction = this.db.transaction([tier], 'readwrite');
          const store = transaction.objectStore(tier);
          const request = store.delete(key);

          request.onsuccess = () => resolve(true);
          request.onerror = () => resolve(false);
        } catch (error) {
          resolve(false);
        }
      });
    }

    _clearIndexedDBStore(tier) {
      return new Promise((resolve) => {
        try {
          const transaction = this.db.transaction([tier], 'readwrite');
          const store = transaction.objectStore(tier);
          const request = store.clear();

          request.onsuccess = () => resolve(true);
          request.onerror = () => resolve(false);
        } catch (error) {
          resolve(false);
        }
      });
    }

    _getIndexedDBKeys(tier) {
      return new Promise((resolve) => {
        try {
          const transaction = this.db.transaction([tier], 'readonly');
          const store = transaction.objectStore(tier);
          const request = store.getAllKeys();

          request.onsuccess = () => resolve(request.result || []);
          request.onerror = () => resolve([]);
        } catch (error) {
          resolve([]);
        }
      });
    }

    // ════════════════════════════════════════════════════════════════════
    // localStorage Private Methods
    // ════════════════════════════════════════════════════════════════════

    _makeLocalStorageKey(key, tier) {
      return `${this.namespace}_${tier}_${key}`;
    }

    _getFromLocalStorage(key, tier) {
      try {
        const storageKey = this._makeLocalStorageKey(key, tier);
        const json = localStorage.getItem(storageKey);
        if (!json) {
          return null;
        }

        const entry = JSON.parse(json);
        return entry.value || null;
      } catch (error) {
        console.error('[StorageManager] localStorage get error:', error);
        return null;
      }
    }

    _setInLocalStorage(entry, tier) {
      try {
        const storageKey = this._makeLocalStorageKey(entry.key, tier);
        localStorage.setItem(storageKey, JSON.stringify(entry));
        return true;
      } catch (error) {
        console.error('[StorageManager] localStorage set error (quota exceeded?):', error);
        return false;
      }
    }

    _removeFromLocalStorage(key, tier) {
      try {
        const storageKey = this._makeLocalStorageKey(key, tier);
        localStorage.removeItem(storageKey);
        return true;
      } catch (error) {
        return false;
      }
    }

    _clearLocalStorageTier(tier) {
      try {
        const prefix = `${this.namespace}_${tier}_`;
        const keysToRemove = [];

        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith(prefix)) {
            keysToRemove.push(key);
          }
        }

        keysToRemove.forEach(key => localStorage.removeItem(key));
        return true;
      } catch (error) {
        return false;
      }
    }

    _getLocalStorageKeys(tier) {
      try {
        const prefix = `${this.namespace}_${tier}_`;
        const keys = [];

        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith(prefix)) {
            // Remove prefix to get original key
            keys.push(key.substring(prefix.length));
          }
        }

        return keys;
      } catch (error) {
        return [];
      }
    }
  }

  // ════════════════════════════════════════════════════════════════════════
  // Export
  // ════════════════════════════════════════════════════════════════════════

  return StorageManager;
}));

