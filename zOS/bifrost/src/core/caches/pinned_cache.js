/**
 * Pinned Cache - User bookmarks (no eviction, user-controlled)
 */
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['./base_cache'], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./base_cache'));
  } else {
    root.PinnedCache = factory(root.BaseCache);
  }
}(typeof self !== 'undefined' ? self : this, (BaseCache) => {
  'use strict';

  class PinnedCache extends BaseCache {
    constructor(storage) {
      super(storage, 'pinned', null);  // No limit (user-controlled)
    }
  }

  return PinnedCache;
}));

