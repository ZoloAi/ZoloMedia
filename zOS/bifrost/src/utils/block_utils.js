/**
 * ═══════════════════════════════════════════════════════════════
 * Block Wrapper Utilities
 * ═══════════════════════════════════════════════════════════════
 *
 * Helper functions for creating and managing zBlock wrappers with metadata.
 * Supports both static and progressive rendering patterns.
 *
 * @module utils/block_utils
 * @version 1.0.0
 * @author Gal Nachshon
 *
 * ───────────────────────────────────────────────────────────────
 * Architecture:
 * - Uses primitives for DOM creation (createDiv)
 * - Handles _zClass and _zStyle metadata
 * - Supports progressive rendering with data attributes
 * ───────────────────────────────────────────────────────────────
 */

import { createDiv } from './dom_utils.js';

/**
 * Create a block wrapper with metadata
 * @param {Object} blockData - Block data object (may contain _zClass, _zStyle)
 * @param {string} blockName - Block name for data attribute (default: 'zBlock')
 * @param {boolean} isProgressive - Whether this is for progressive rendering (default: false)
 * @returns {HTMLElement|null} Block wrapper div, or null if no metadata
 */
export function createBlockWrapper(blockData, blockName = 'zBlock', isProgressive = false) {
  if (!blockData || typeof blockData !== 'object' || !blockData._zClass) {
    return null;
  }

  const blockLevelDiv = createDiv();

  // Apply block-level classes
  const classes = Array.isArray(blockData._zClass)
    ? blockData._zClass
    : blockData._zClass.split(',').map(c => c.trim());
  blockLevelDiv.className = classes.join(' ');

  // Set data attribute
  blockLevelDiv.setAttribute('data-zblock', isProgressive ? 'progressive' : blockName);

  // Set id for named blocks (not progressive)
  if (!isProgressive && blockName && blockName !== 'zBlock') {
    blockLevelDiv.setAttribute('id', blockName);
  }

  // Apply inline styles if present
  if (blockData._zStyle) {
    blockLevelDiv.setAttribute('style', blockData._zStyle);
  }

  return blockLevelDiv;
}

/**
 * Apply block metadata to an existing wrapper
 * @param {HTMLElement} wrapper - The wrapper element
 * @param {Object} metadata - Metadata object (may contain _zClass, _zStyle)
 */
export function applyBlockMetadata(wrapper, metadata) {
  if (!wrapper || !metadata) {
    return;
  }

  if (metadata._zClass) {
    wrapper.className = metadata._zClass;
  }

  if (metadata._zStyle) {
    wrapper.setAttribute('style', metadata._zStyle);
  }
}

/**
 * Find existing progressive block wrapper in container
 * @param {HTMLElement} container - Container to search in
 * @returns {HTMLElement|null} Existing wrapper, or null
 */
export function findProgressiveBlockWrapper(container) {
  if (!container) {
    return null;
  }
  return container.querySelector('[data-zblock="progressive"]');
}

/**
 * Check if block data has metadata (_zClass or _zStyle)
 * @param {Object} blockData - Block data object
 * @returns {boolean} True if has metadata
 */
export function hasBlockMetadata(blockData) {
  return blockData &&
         typeof blockData === 'object' &&
         (blockData._zClass || blockData._zStyle);
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createBlockWrapper,
  applyBlockMetadata,
  findProgressiveBlockWrapper,
  hasBlockMetadata
};

