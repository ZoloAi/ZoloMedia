/**
 * Emoji Accessibility Module for Bifrost
 * 
 * Provides ARIA labels for emojis to make them accessible to screen readers.
 * Uses the CLDR-based emoji-a11y.en.json data file.
 * 
 * Features:
 * - Lazy loading of emoji descriptions
 * - Auto-wrap emojis with aria-label spans
 * - Graceful fallback if data unavailable
 * - Singleton pattern for efficient loading
 * 
 * Phase 5: Bifrost ARIA Integration
 * Author: zOS Framework
 * Version: 1.0.0
 */

class EmojiAccessibility {
    constructor() {
        this.descriptions = null;
        this.loading = null;
        this.enabled = true;
    }
    
    /**
     * Lazy load emoji descriptions from JSON file.
     * 
     * @returns {Promise<void>}
     */
    async load() {
        // Already loaded
        if (this.descriptions) {
            return;
        }
        
        // Already loading (prevent duplicate requests)
        if (this.loading) {
            return this.loading;
        }
        
        // Start loading
        this.loading = (async () => {
            try {
                const response = await fetch('/static/js/emoji-a11y.en.json');
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                this.descriptions = await response.json();
                console.log(`[EmojiA11y] Loaded ${Object.keys(this.descriptions).length} emoji descriptions`);
            } catch (e) {
                console.warn('[EmojiA11y] Failed to load descriptions:', e);
                this.descriptions = {};
                this.enabled = false;
            } finally {
                this.loading = null;
            }
        })();
        
        return this.loading;
    }
    
    /**
     * Get description for an emoji character.
     * 
     * @param {string} emoji - Emoji character
     * @returns {string|null} - Description or null if not found
     */
    getDescription(emoji) {
        if (!this.descriptions) {
            return null;
        }
        
        return this.descriptions[emoji] || null;
    }
    
    /**
     * Wrap emoji with accessible ARIA span.
     * 
     * @param {string} emoji - Emoji character
     * @returns {string} - HTML string with aria-label or plain emoji
     * 
     * @example
     * wrapWithAria('📱') → '<span aria-label="mobile phone" role="img">📱</span>'
     * wrapWithAria('A')  → 'A' (not an emoji)
     */
    wrapWithAria(emoji) {
        if (!this.enabled) {
            return emoji;
        }
        
        const desc = this.getDescription(emoji);
        
        if (desc) {
            // Escape HTML in description to prevent XSS
            const safeDesc = this._escapeHtml(desc);
            return `<span aria-label="${safeDesc}" role="img">${emoji}</span>`;
        }
        
        return emoji;
    }
    
    /**
     * Enhance text by wrapping all emojis with ARIA labels.
     * 
     * @param {string} text - Plain or HTML text with emojis
     * @returns {string} - Text with emojis wrapped in accessible spans
     * 
     * @example
     * enhanceText('Mobile: 📱') → 'Mobile: <span aria-label="mobile phone" role="img">📱</span>'
     */
    enhanceText(text) {
        if (!this.enabled || !this.descriptions) {
            return text;
        }
        
        // Emoji Unicode ranges (same as Python version)
        // Matches: emoji characters only (excludes ASCII)
        const emojiRegex = /[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F000}-\u{1F0FF}\u{1F200}-\u{1F2FF}\u{1F600}-\u{1F64F}\u{1F680}-\u{1F6FF}\u{1F900}-\u{1F9FF}\u{2300}-\u{23FF}\u{2B00}-\u{2BFF}\u{FE00}-\u{FE0F}]/gu;
        
        return text.replace(emojiRegex, (emoji) => {
            return this.wrapWithAria(emoji);
        });
    }
    
    /**
     * Escape HTML entities to prevent XSS.
     * 
     * @private
     * @param {string} text - Text to escape
     * @returns {string} - Escaped text
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Check if emoji accessibility is enabled and loaded.
     * 
     * @returns {boolean}
     */
    isReady() {
        return this.enabled && this.descriptions !== null;
    }
    
    /**
     * Get statistics about loaded descriptions.
     * 
     * @returns {object} - Stats object
     */
    getStats() {
        return {
            enabled: this.enabled,
            loaded: this.descriptions !== null,
            count: this.descriptions ? Object.keys(this.descriptions).length : 0
        };
    }
}

// Global singleton instance
const emojiAccessibility = new EmojiAccessibility();

// Auto-load on module import (non-blocking)
emojiAccessibility.load().catch(console.error);

// Export for use in Bifrost
export default emojiAccessibility;
export { EmojiAccessibility };
