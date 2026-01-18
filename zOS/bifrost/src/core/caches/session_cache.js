/**
 * Session Cache - In-memory user state (no persistence, no limit)
 */
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['./base_cache'], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./base_cache'));
  } else {
    root.SessionCache = factory(root.BaseCache);
  }
}(typeof self !== 'undefined' ? self : this, (BaseCache) => {
  'use strict';

  class SessionCache extends BaseCache {
    constructor(storage) {
      super(storage, 'session', null);  // No limit (in-memory only)
    }
  }

  return SessionCache;
}));

