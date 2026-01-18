/**
 * Rendered Cache - DOM for offline mode (LRU: 20 items, TTL: 30 min)
 */
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['./base_cache'], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./base_cache'));
  } else {
    root.RenderedCache = factory(root.BaseCache);
  }
}(typeof self !== 'undefined' ? self : this, (BaseCache) => {
  'use strict';

  class RenderedCache extends BaseCache {
    constructor(storage) {
      super(storage, 'rendered', 20);  // LRU: 20 items (HTML is large)
    }
  }

  return RenderedCache;
}));

