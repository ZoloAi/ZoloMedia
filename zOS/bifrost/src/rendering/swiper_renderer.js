/**
 * SwiperRenderer - Render interactive content carousels/slideshows
 *
 * Terminal-first implementation matching backend zDisplay.swiper()
 *
 * Backend Events (from display_event_timebased.py):
 * - swiper_init: Initialize swiper with slides
 * - swiper_update: Update current slide
 * - swiper_complete: Finish swiper
 *
 * Terminal Paradigm:
 * - Box-drawing UI: ╔═══╗║╠╣╚═══╝ for beautiful bordered display
 * - Arrow keys: ◀▶ for navigation (via termios + select)
 * - Number keys: 1-9 for direct jump to slide
 * - Pause toggle: 'p' key
 * - Quit: 'q' key
 * - Auto-advance: Background thread cycles through slides every N seconds
 * - Loop mode: Optional wrap around to start
 *
 * Bifrost Paradigm:
 * - WebSocket events trigger initialization and updates
 * - Touch gestures: Swipe left/right for navigation
 * - Auto-advance: CSS animations + JavaScript intervals
 * - Indicators: Dots showing position (1/N, 2/N, etc.)
 * - zTheme carousel: Full CSS transitions and responsive design
 *
 * Features:
 * - Slide/fade/vertical transitions (zTheme variants)
 * - Auto-advance with configurable delay
 * - Loop mode
 * - Prev/next controls with keyboard shortcuts
 * - Indicators (dots or progress bar)
 * - Pause on hover
 * - Caption support
 * - Multiple concurrent swipers
 *
 * @see https://github.com/ZoloAi/zTheme/blob/main/Manual/ztheme-carousel.html
 */

import { createDiv } from './primitives/generic_containers.js';
import { createButton } from './primitives/interactive_primitives.js';
import { createSpan } from './primitives/generic_containers.js';
import { createList } from './primitives/lists_primitives.js';

export default class SwiperRenderer {
  /**
   * @param {Object} logger - Logger instance
   */
  constructor(logger) {
    this.logger = logger;
    this._activeSwipers = new Map(); // Track active swipers by swiperId
  }

  /**
   * Initialize a swiper (swiper_init event)
   * @param {Object} event - Swiper init event
   * @param {string} event.swiperId - Unique swiper ID
   * @param {string} event.label - Swiper label/title
   * @param {Array<string>} event.slides - Array of slide content
   * @param {number} [event.currentSlide=0] - Initial slide index
   * @param {number} event.totalSlides - Total number of slides
   * @param {boolean} [event.autoAdvance=true] - Enable auto-advance
   * @param {number} [event.delay=3] - Delay between slides (seconds)
   * @param {boolean} [event.loop=false] - Loop back to first slide
   * @param {string} [event.container='#app'] - Target container selector
   * @param {string} [event.variant='slide'] - Transition variant (slide, fade, vertical)
   * @param {boolean} [event.showIndicators=true] - Show dot indicators
   * @param {boolean} [event.showControls=true] - Show prev/next controls
   * @returns {HTMLElement} Swiper container element
   */
  init(event) {
    const {
      swiperId,
      label = 'Slides',
      slides = [],
      currentSlide = 0,
      _totalSlides,
      autoAdvance = true,
      delay = 3,
      loop = false,
      container = '#app',
      variant = 'slide',
      showIndicators = true,
      showControls = true
    } = event;

    this.logger.log('[SwiperRenderer] Initializing swiper:', {
      swiperId,
      label,
      slidesCount: slides.length
    });

    if (!slides || slides.length === 0) {
      this.logger.warn('[SwiperRenderer] No slides provided');
      return null;
    }

    // Create swiper structure using primitives and zTheme classes
    const swiperContainer = this._createSwiperContainer(
      swiperId,
      label,
      slides,
      currentSlide,
      variant,
      showIndicators,
      showControls
    );

    // Find target container
    const targetElement = document.querySelector(container) || document.body;
    targetElement.appendChild(swiperContainer);

    // Track active swiper
    const swiperData = {
      element: swiperContainer,
      label,
      slides,
      currentSlide,
      totalSlides: slides.length,
      autoAdvance,
      delay,
      loop,
      variant,
      intervalId: null
    };

    this._activeSwipers.set(swiperId, swiperData);

    // Start auto-advance if enabled
    if (autoAdvance && delay > 0) {
      this._startAutoAdvance(swiperId);
    }

    // Add keyboard navigation
    this._addKeyboardNav(swiperId);

    this.logger.log('[SwiperRenderer] Swiper initialized successfully');
    return swiperContainer;
  }

  /**
   * Update swiper to show specific slide (swiper_update event)
   * @param {Object} event - Swiper update event
   * @param {string} event.swiperId - Unique swiper ID
   * @param {number} event.currentSlide - Target slide index
   */
  update(event) {
    const { swiperId, currentSlide } = event;

    this.logger.log('[SwiperRenderer] Updating swiper:', { swiperId, currentSlide });

    const swiperData = this._activeSwipers.get(swiperId);
    if (!swiperData) {
      this.logger.warn('[SwiperRenderer] Swiper not found:', swiperId);
      return;
    }

    this._goToSlide(swiperId, currentSlide);
  }

  /**
   * Complete and remove swiper (swiper_complete event)
   * @param {Object} event - Swiper complete event
   * @param {string} event.swiperId - Unique swiper ID
   */
  complete(event) {
    const { swiperId } = event;

    this.logger.log('[SwiperRenderer] Completing swiper:', swiperId);

    const swiperData = this._activeSwipers.get(swiperId);
    if (!swiperData) {
      this.logger.warn('[SwiperRenderer] Swiper not found:', swiperId);
      return;
    }

    // Stop auto-advance
    if (swiperData.intervalId) {
      clearInterval(swiperData.intervalId);
    }

    // Fade out and remove
    const { element } = swiperData;
    element.style.transition = 'opacity 0.3s';
    element.style.opacity = '0';
    setTimeout(() => {
      if (element.parentNode) {
        element.parentNode.removeChild(element);
      }
    }, 300);

    // Remove from active swipers
    this._activeSwipers.delete(swiperId);

    this.logger.log('[SwiperRenderer] Swiper completed successfully');
  }

  /**
   * Create swiper container using primitives and zTheme classes
   * @private
   */
  _createSwiperContainer(swiperId, label, slides, currentSlide, variant, showIndicators, showControls) {
    // Main container with wrapper for label
    const wrapper = createDiv({
      id: `${swiperId}-wrapper`,
      class: 'zMy-3'
    });

    // Label/title (using primitive)
    if (label) {
      const labelEl = createDiv({
        class: 'zH4 zMb-2'
      });
      labelEl.textContent = label;
      wrapper.appendChild(labelEl);
    }

    // Carousel container (using primitive + zTheme classes)
    const carousel = createDiv({
      id: swiperId,
      class: `zCarousel ${variant === 'fade' ? 'zCarousel-fade' : ''} ${variant === 'vertical' ? 'zCarousel-vertical' : ''}`,
      'data-ride': 'false', // We control it manually
      'data-swiper-id': swiperId
    });

    // Carousel inner (slide container)
    const carouselInner = createDiv({
      class: 'zCarousel-inner'
    });

    // Create slides
    slides.forEach((slideContent, index) => {
      const slideItem = createDiv({
        class: `zCarousel-item ${index === currentSlide ? 'zActive' : ''}`,
        'data-slide-index': index
      });

      // Slide content wrapper
      const slideContentDiv = createDiv({
        class: 'zP-5 zBg-light zText-center',
        style: 'min-height: 200px; display: flex; align-items: center; justify-content: center;'
      });
      slideContentDiv.innerHTML = slideContent; // Allow HTML in slides

      slideItem.appendChild(slideContentDiv);
      carouselInner.appendChild(slideItem);
    });

    carousel.appendChild(carouselInner);

    // Add controls (prev/next buttons)
    if (showControls) {
      const prevControl = this._createControl('prev', swiperId);
      const nextControl = this._createControl('next', swiperId);
      carousel.appendChild(prevControl);
      carousel.appendChild(nextControl);
    }

    // Add indicators (dots)
    if (showIndicators) {
      const indicators = this._createIndicators(swiperId, slides.length, currentSlide);
      carousel.appendChild(indicators);
    }

    wrapper.appendChild(carousel);
    return wrapper;
  }

  /**
   * Create prev/next control button
   * @private
   */
  _createControl(direction, swiperId) {
    const control = createButton('button', {
      class: `zCarousel-control-${direction}`,
      type: 'button',
      'data-swiper-id': swiperId,
      'data-direction': direction
    });

    // Icon span
    const icon = createSpan({
      class: `zCarousel-control-${direction}-icon`,
      'aria-hidden': 'true'
    });

    // Screen reader text
    const srText = createSpan({
      class: 'zVisually-hidden'
    });
    srText.textContent = direction === 'prev' ? 'Previous' : 'Next';

    control.appendChild(icon);
    control.appendChild(srText);

    // Add click handler
    control.addEventListener('click', () => {
      if (direction === 'prev') {
        this._prevSlide(swiperId);
      } else {
        this._nextSlide(swiperId);
      }
    });

    return control;
  }

  /**
   * Create indicators (dots)
   * @private
   */
  _createIndicators(swiperId, totalSlides, currentSlide) {
    const indicatorsList = createList(false, {
      class: 'zCarousel-indicators'
    });

    for (let i = 0; i < totalSlides; i++) {
      const indicator = createButton('button', {
        type: 'button',
        class: i === currentSlide ? 'zActive' : '',
        'data-swiper-id': swiperId,
        'data-slide-to': i,
        'aria-label': `Slide ${i + 1}`
      });

      indicator.addEventListener('click', () => {
        this._goToSlide(swiperId, i);
      });

      indicatorsList.appendChild(indicator);
    }

    return indicatorsList;
  }

  /**
   * Go to specific slide
   * @private
   */
  _goToSlide(swiperId, targetIndex) {
    const swiperData = this._activeSwipers.get(swiperId);
    if (!swiperData) {
      return;
    }

    const { element, currentSlide, totalSlides } = swiperData;

    // Validate index
    if (targetIndex < 0 || targetIndex >= totalSlides) {
      return;
    }
    if (targetIndex === currentSlide) {
      return;
    }

    // Find carousel element
    const carousel = element.querySelector(`[data-swiper-id="${swiperId}"]`);
    if (!carousel) {
      return;
    }

    // Get all slides
    const slides = carousel.querySelectorAll('.zCarousel-item');
    const currentSlideEl = slides[currentSlide];
    const targetSlideEl = slides[targetIndex];

    if (!currentSlideEl || !targetSlideEl) {
      return;
    }

    // Apply transition classes (zTheme CSS handles animations)
    currentSlideEl.classList.remove('zActive');
    targetSlideEl.classList.add('zActive');

    // Update indicators
    const indicators = carousel.querySelectorAll('.zCarousel-indicators button');
    if (indicators.length > 0) {
      indicators[currentSlide]?.classList.remove('zActive');
      indicators[targetIndex]?.classList.add('zActive');
    }

    // Update swiper data
    swiperData.currentSlide = targetIndex;

    this.logger.log(`[SwiperRenderer] Moved to slide ${targetIndex + 1}/${totalSlides}`);
  }

  /**
   * Go to previous slide
   * @private
   */
  _prevSlide(swiperId) {
    const swiperData = this._activeSwipers.get(swiperId);
    if (!swiperData) {
      return;
    }

    const { currentSlide, totalSlides, loop } = swiperData;
    let targetIndex = currentSlide - 1;

    if (targetIndex < 0) {
      if (loop) {
        targetIndex = totalSlides - 1; // Wrap to last slide
      } else {
        return; // Can't go before first slide
      }
    }

    this._goToSlide(swiperId, targetIndex);
  }

  /**
   * Go to next slide
   * @private
   */
  _nextSlide(swiperId) {
    const swiperData = this._activeSwipers.get(swiperId);
    if (!swiperData) {
      return;
    }

    const { currentSlide, totalSlides, loop } = swiperData;
    let targetIndex = currentSlide + 1;

    if (targetIndex >= totalSlides) {
      if (loop) {
        targetIndex = 0; // Wrap to first slide
      } else {
        return; // Can't go past last slide
      }
    }

    this._goToSlide(swiperId, targetIndex);
  }

  /**
   * Start auto-advance interval
   * @private
   */
  _startAutoAdvance(swiperId) {
    const swiperData = this._activeSwipers.get(swiperId);
    if (!swiperData) {
      return;
    }

    const { delay } = swiperData;

    // Clear any existing interval
    if (swiperData.intervalId) {
      clearInterval(swiperData.intervalId);
    }

    // Start new interval
    swiperData.intervalId = setInterval(() => {
      this._nextSlide(swiperId);
    }, delay * 1000);

    this.logger.log(`[SwiperRenderer] Auto-advance started (${delay}s delay)`);
  }

  /**
   * Stop auto-advance interval
   * @private
   */
  _stopAutoAdvance(swiperId) {
    const swiperData = this._activeSwipers.get(swiperId);
    if (!swiperData) {
      return;
    }

    if (swiperData.intervalId) {
      clearInterval(swiperData.intervalId);
      swiperData.intervalId = null;
      this.logger.log('[SwiperRenderer] Auto-advance stopped');
    }
  }

  /**
   * Add keyboard navigation (arrow keys, number keys)
   * @private
   */
  _addKeyboardNav(swiperId) {
    const swiperData = this._activeSwipers.get(swiperId);
    if (!swiperData) {
      return;
    }

    const keyHandler = (e) => {
      // Only handle if this swiper is still active
      if (!this._activeSwipers.has(swiperId)) {
        document.removeEventListener('keydown', keyHandler);
        return;
      }

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          this._prevSlide(swiperId);
          break;
        case 'ArrowRight':
          e.preventDefault();
          this._nextSlide(swiperId);
          break;
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
        case '8':
        case '9': {
          const targetIndex = parseInt(e.key, 10) - 1;
          if (targetIndex < swiperData.totalSlides) {
            this._goToSlide(swiperId, targetIndex);
          }
          break;
        }
        case 'p':
        case 'P':
          // Toggle pause
          if (swiperData.intervalId) {
            this._stopAutoAdvance(swiperId);
          } else if (swiperData.autoAdvance) {
            this._startAutoAdvance(swiperId);
          }
          break;
      }
    };

    document.addEventListener('keydown', keyHandler);

    // Store handler for cleanup
    swiperData.keyHandler = keyHandler;
  }

  /**
   * Get active swiper count
   * @returns {number} Number of active swipers
   */
  getActiveCount() {
    return this._activeSwipers.size;
  }

  /**
   * Stop all active swipers (cleanup utility)
   */
  stopAll() {
    this.logger.log('[SwiperRenderer] Stopping all swipers');

    for (const [swiperId, _data] of this._activeSwipers) {
      this.complete({ swiperId });
    }
  }
}

