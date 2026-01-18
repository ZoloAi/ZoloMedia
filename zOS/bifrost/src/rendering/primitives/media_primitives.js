/**
 * ═══════════════════════════════════════════════════════════════
 * Media Primitives - Rich Content Elements
 * ═══════════════════════════════════════════════════════════════
 *
 * HTML media elements for images, video, audio, and responsive images.
 * Used for displaying rich content with native browser controls.
 *
 * @module rendering/media_primitives
 * @layer 0.0 (RAWEST - media elements)
 * @pattern Pure Factory Functions
 *
 * Philosophy:
 * - Native media elements with browser controls
 * - Responsive images via <picture> + <source>
 * - Accessibility (alt text, captions)
 * - NO styling, NO classes (dress up later)
 *
 * Media Types:
 * - <img>: Single image with src/alt
 * - <video>: Video player with controls
 * - <audio>: Audio player with controls
 * - <picture> + <source>: Responsive images (art direction)
 * - <source>: Source element for picture/video/audio
 *
 * Accessibility:
 * - Images REQUIRE alt text (enforced)
 * - Video/audio support captions via <track> elements
 * - Native controls are keyboard accessible
 *
 * Dependencies:
 * - utils/dom_utils.js (createElement, setAttributes)
 *
 * Exports:
 * - createImage(src, alt, attributes) → HTMLImageElement
 * - createVideo(src, attributes) → HTMLVideoElement
 * - createAudio(src, attributes) → HTMLAudioElement
 * - createPicture(attributes) → HTMLPictureElement
 * - createSource(srcset, media, type) → HTMLSourceElement
 *
 * Example:
 * ```javascript
 * import { createImage, createPicture, createSource } from './media_primitives.js';
 *
 * // Simple image
 * const img = createImage('photo.jpg', 'A beautiful sunset');
 *
 * // Responsive image
 * const picture = createPicture();
 * const srcLarge = createSource('large.jpg', '(min-width: 1024px)');
 * const srcMedium = createSource('medium.jpg', '(min-width: 640px)');
 * const fallback = createImage('small.jpg', 'Responsive image');
 * picture.appendChild(srcLarge);
 * picture.appendChild(srcMedium);
 * picture.appendChild(fallback);
 * ```
 */

import { createElement, setAttributes } from '../../utils/dom_utils.js';

// ─────────────────────────────────────────────────────────────────
// Image Element
// ─────────────────────────────────────────────────────────────────

/**
 * Create an <img> element
 *
 * Used for displaying images with required alt text for accessibility.
 * The most common media element in web documents.
 *
 * Semantic Meaning:
 * - Single image source
 * - Alt text is REQUIRED (accessibility)
 * - Can be styled with width/height attributes or CSS
 *
 * Accessibility:
 * - Alt text should describe the image content
 * - Decorative images can use alt="" (empty string)
 * - Complex images may need longer descriptions
 *
 * @param {string} src - Image source URL or path (REQUIRED)
 * @param {string} [alt=''] - Alternative text for accessibility (defaults to empty for decorative)
 * @param {Object} [attributes={}] - Additional HTML attributes (id, class, width, height, loading, etc.)
 * @returns {HTMLImageElement} The created img element
 *
 * @example
 * // Basic image
 * const photo = createImage('sunset.jpg', 'A beautiful sunset over the ocean');
 *
 * // Image with dimensions
 * const thumbnail = createImage('thumb.jpg', 'Product thumbnail', {
 *   width: '150',
 *   height: '150'
 * });
 *
 * // Lazy-loaded image
 * const lazyImg = createImage('large.jpg', 'High-res photo', {
 *   loading: 'lazy'
 * });
 *
 * // Decorative image (empty alt)
 * const decoration = createImage('pattern.png', '', { class: 'bg-pattern' });
 */
export function createImage(src, alt = '', attributes = {}) {
  if (!src) {
    console.error('[media_primitives] createImage: src is required');
    return null;
  }

  const img = createElement('img');

  // Set required attributes
  img.src = src;
  img.alt = alt;

  // Set additional attributes
  if (Object.keys(attributes).length > 0) {
    setAttributes(img, attributes);
  }

  return img;
}

// ─────────────────────────────────────────────────────────────────
// Video Element
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <video> element
 *
 * Used for displaying video content with native browser controls.
 * Supports multiple source formats for cross-browser compatibility.
 *
 * Semantic Meaning:
 * - Video player with native controls
 * - Can contain multiple <source> elements for format fallback
 * - Can include <track> elements for captions/subtitles
 *
 * Native Attributes:
 * - controls: Show playback controls (recommended)
 * - autoplay: Start playing automatically (avoid - accessibility concern)
 * - loop: Loop the video
 * - muted: Mute audio (required for autoplay in most browsers)
 * - poster: Placeholder image before playback
 * - preload: 'none' | 'metadata' | 'auto'
 *
 * @param {string} [src] - Optional video source URL (can also use <source> children)
 * @param {Object} [attributes={}] - HTML attributes (controls, width, height, poster, etc.)
 * @returns {HTMLVideoElement} The created video element
 *
 * @example
 * // Basic video with controls
 * const video = createVideo('movie.mp4', { controls: true });
 *
 * // Video with poster and dimensions
 * const videoWithPoster = createVideo('demo.mp4', {
 *   controls: true,
 *   poster: 'poster.jpg',
 *   width: '640',
 *   height: '360'
 * });
 *
 * // Video with multiple sources (append <source> elements after creation)
 * const responsiveVideo = createVideo(null, { controls: true });
 * // Then append createSource() elements for format fallback
 */
export function createVideo(src = null, attributes = {}) {
  const video = createElement('video');

  // Set src if provided (optional - can use <source> children instead)
  if (src) {
    video.src = src;
  }

  // Set additional attributes (controls, width, height, etc.)
  if (Object.keys(attributes).length > 0) {
    setAttributes(video, attributes);
  }

  return video;
}

// ─────────────────────────────────────────────────────────────────
// Audio Element
// ─────────────────────────────────────────────────────────────────

/**
 * Create an <audio> element
 *
 * Used for displaying audio content with native browser controls.
 * Supports multiple source formats for cross-browser compatibility.
 *
 * Semantic Meaning:
 * - Audio player with native controls
 * - Can contain multiple <source> elements for format fallback
 * - Can include <track> elements for captions
 *
 * Native Attributes:
 * - controls: Show playback controls (recommended)
 * - autoplay: Start playing automatically (avoid - accessibility concern)
 * - loop: Loop the audio
 * - muted: Mute audio
 * - preload: 'none' | 'metadata' | 'auto'
 *
 * @param {string} [src] - Optional audio source URL (can also use <source> children)
 * @param {Object} [attributes={}] - HTML attributes (controls, loop, etc.)
 * @returns {HTMLAudioElement} The created audio element
 *
 * @example
 * // Basic audio with controls
 * const audio = createAudio('song.mp3', { controls: true });
 *
 * // Looping audio
 * const bgMusic = createAudio('background.mp3', {
 *   controls: true,
 *   loop: true
 * });
 *
 * // Audio with multiple sources (append <source> elements after creation)
 * const compatAudio = createAudio(null, { controls: true });
 * // Then append createSource() elements for format fallback
 */
export function createAudio(src = null, attributes = {}) {
  const audio = createElement('audio');

  // Set src if provided (optional - can use <source> children instead)
  if (src) {
    audio.src = src;
  }

  // Set additional attributes (controls, loop, etc.)
  if (Object.keys(attributes).length > 0) {
    setAttributes(audio, attributes);
  }

  return audio;
}

// ─────────────────────────────────────────────────────────────────
// Picture Element (Responsive Images)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <picture> element
 *
 * Used for responsive images with art direction (different images for different contexts).
 * Contains multiple <source> elements and a fallback <img> element.
 *
 * Semantic Meaning:
 * - Container for responsive image sources
 * - Browser selects best source based on media queries and formats
 * - Fallback <img> is REQUIRED (last child)
 *
 * Usage Pattern:
 * 1. Create <picture> element
 * 2. Append <source> elements (most specific first)
 * 3. Append fallback <img> element (REQUIRED, always last)
 *
 * Art Direction vs Resolution Switching:
 * - Art direction: Different crops/compositions for different screens
 * - Resolution switching: Same image at different resolutions (use <img srcset> instead)
 *
 * @param {Object} [attributes={}] - HTML attributes (id, class, etc.)
 * @returns {HTMLPictureElement} The created picture element
 *
 * @example
 * // Responsive image with art direction
 * const picture = createPicture({ id: 'hero-image' });
 *
 * // Add sources (desktop, tablet, mobile)
 * const desktop = createSource('wide.jpg', '(min-width: 1024px)');
 * const tablet = createSource('medium.jpg', '(min-width: 640px)');
 * const fallback = createImage('small.jpg', 'Hero image');
 *
 * picture.appendChild(desktop);
 * picture.appendChild(tablet);
 * picture.appendChild(fallback); // REQUIRED - always last
 *
 * @example
 * // Modern image format fallback (WebP → JPEG)
 * const modernPicture = createPicture();
 * const webp = createSource('photo.webp', null, 'image/webp');
 * const jpeg = createImage('photo.jpg', 'Photo');
 *
 * modernPicture.appendChild(webp);
 * modernPicture.appendChild(jpeg); // REQUIRED fallback
 */
export function createPicture(attributes = {}) {
  const picture = createElement('picture');

  if (Object.keys(attributes).length > 0) {
    setAttributes(picture, attributes);
  }

  return picture;
}

// ─────────────────────────────────────────────────────────────────
// Source Element (for picture/video/audio)
// ─────────────────────────────────────────────────────────────────

/**
 * Create a <source> element
 *
 * Used within <picture>, <video>, or <audio> elements to provide
 * multiple source options with media queries or format fallbacks.
 *
 * Semantic Meaning:
 * - Specifies alternative media sources
 * - Browser selects first compatible source
 * - Can filter by media query (responsive) or format (compatibility)
 *
 * Usage Contexts:
 * - <picture>: Responsive images (srcset + media query)
 * - <video>: Format fallback (src + type: video/mp4, video/webm, etc.)
 * - <audio>: Format fallback (src + type: audio/mp3, audio/ogg, etc.)
 *
 * @param {string} srcset - Source URL or srcset value
 * @param {string} [media=null] - Media query for responsive images (e.g., "(min-width: 768px)")
 * @param {string} [type=null] - MIME type for format fallback (e.g., "image/webp", "video/mp4")
 * @returns {HTMLSourceElement} The created source element
 *
 * @example
 * // Responsive image source (for <picture>)
 * const desktop = createSource('large.jpg', '(min-width: 1024px)');
 * const tablet = createSource('medium.jpg', '(min-width: 640px)');
 *
 * @example
 * // Modern format source (for <picture>)
 * const webp = createSource('photo.webp', null, 'image/webp');
 * const avif = createSource('photo.avif', null, 'image/avif');
 *
 * @example
 * // Video format sources (for <video>)
 * const webm = createSource('movie.webm', null, 'video/webm');
 * const mp4 = createSource('movie.mp4', null, 'video/mp4');
 *
 * @example
 * // Audio format sources (for <audio>)
 * const ogg = createSource('song.ogg', null, 'audio/ogg');
 * const mp3 = createSource('song.mp3', null, 'audio/mpeg');
 */
export function createSource(srcset, media = null, type = null) {
  if (!srcset) {
    console.error('[media_primitives] createSource: srcset is required');
    return null;
  }

  const source = createElement('source');

  // For <picture>: use srcset attribute
  // For <video>/<audio>: srcset becomes src attribute
  source.srcset = srcset;

  // Media query for responsive images (optional)
  if (media) {
    source.media = media;
  }

  // MIME type for format fallback (optional)
  if (type) {
    source.type = type;
  }

  return source;
}

// ─────────────────────────────────────────────────────────────────
// Default Export (for convenience)
// ─────────────────────────────────────────────────────────────────
export default {
  createImage,
  createVideo,
  createAudio,
  createPicture,
  createSource
};

