/**
 * System Cache - UI files, configs, YAML (LRU: 100 items)
 */
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['./base_cache'], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./base_cache'));
  } else {
    root.SystemCache = factory(root.BaseCache);
  }
}(typeof self !== 'undefined' ? self : this, (BaseCache) => {
  'use strict';

  class SystemCache extends BaseCache {
    constructor(storage) {
      super(storage, 'system', 100);  // LRU: 100 items
    }
  }

  return SystemCache;
}));

