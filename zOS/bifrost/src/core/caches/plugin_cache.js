/**
 * Plugin Cache - JS modules (LRU: 50 items)
 */
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['./base_cache'], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./base_cache'));
  } else {
    root.PluginCache = factory(root.BaseCache);
  }
}(typeof self !== 'undefined' ? self : this, (BaseCache) => {
  'use strict';

  class PluginCache extends BaseCache {
    constructor(storage) {
      super(storage, 'plugin', 50);  // LRU: 50 items
    }
  }

  return PluginCache;
}));

