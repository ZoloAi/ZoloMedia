/**
 * ═══════════════════════════════════════════════════════════════
 * zTheme JavaScript Utilities
 * ═══════════════════════════════════════════════════════════════
 * 
 * Handles interactive features for zTheme CSS framework.
 * 
 * TODO: INTEGRATE WITH zBIFROST CLIENT
 * -------------------------------------
 * This standalone file should be integrated into the zBifrost client
 * rendering system when connecting zTheme to the zBifrost client.
 * 
 * Integration points:
 * - zCLI/subsystems/zBifrost/zBifrost_modules/bifrost/client/src/rendering/theme_loader.js
 * - Should be loaded automatically alongside CSS when ThemeLoader.load() is called
 * - Consider adding as a module export for better integration
 * 
 * See: Documentation/zBifrost_GUIDE.md for client integration patterns
 */

(function() {
    'use strict';

    /**
     * ═══════════════════════════════════════════════════════════
     * Form Validation Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes all forms with .zValidation class.
     * 
     * Usage:
     *   <form class="zValidation" novalidate>
     *     <input type="email" class="zInput" required>
     *     <div class="zInvalid-feedback">Please enter email.</div>
     *     <button type="submit">Submit</button>
     *   </form>
     * 
     * How it works:
     * 1. Finds all forms with .zValidation class
     * 2. On submit, checks if form is valid using HTML5 validation API
     * 3. If invalid, prevents submission and adds .zWas-validated class
     * 4. The .zWas-validated class triggers CSS to show/hide feedback messages
     */
    function initValidation() {
        const forms = document.querySelectorAll('.zValidation');
        
        if (forms.length === 0) {
            return; // No validation forms on this page
        }

        Array.prototype.slice.call(forms).forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('zWas-validated');
            }, false);
        });

        console.log(`✅ zTheme: Initialized validation for ${forms.length} form(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Accordion Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes all accordions with .zAccordion class.
     * 
     * Usage:
     *   <div class="zAccordion" id="myAccordion">
     *     <div class="zAccordion-item">
     *       <h3 class="zAccordion-header">
     *         <button class="zAccordion-button">Panel Title</button>
     *       </h3>
     *       <div class="zAccordion-collapse">
     *         <div class="zAccordion-body">Content...</div>
     *       </div>
     *     </div>
     *   </div>
     * 
     * How it works:
     * 1. Finds all elements with .zAccordion class
     * 2. Adds click handlers to .zAccordion-button elements
     * 3. When clicked, toggles .zCollapsed class
     * 4. Auto-closes other panels in the same accordion group
     */
    function initAccordion() {
        const accordions = document.querySelectorAll('.zAccordion');
        
        if (accordions.length === 0) {
            return; // No accordions on this page
        }

        accordions.forEach(accordion => {
            const buttons = accordion.querySelectorAll('.zAccordion-button');
            
            buttons.forEach(button => {
                button.addEventListener('click', function() {
                    // Find the target panel
                    const header = button.closest('.zAccordion-header');
                    const item = header.closest('.zAccordion-item');
                    const panel = item.querySelector('.zAccordion-collapse');
                    
                    if (!panel) return;
                    
                    // Check if this panel is currently open
                    const isOpen = !panel.classList.contains('zCollapsed');
                    
                    // Close all panels in this accordion
                    const allPanels = accordion.querySelectorAll('.zAccordion-collapse');
                    const allButtons = accordion.querySelectorAll('.zAccordion-button');
                    
                    allPanels.forEach(p => p.classList.add('zCollapsed'));
                    allButtons.forEach(b => {
                        b.classList.add('zCollapsed');
                        b.setAttribute('aria-expanded', 'false');
                    });
                    
                    // If panel was closed, open it (toggle behavior)
                    if (isOpen) {
                        panel.classList.add('zCollapsed');
                        button.classList.add('zCollapsed');
                        button.setAttribute('aria-expanded', 'false');
                    } else {
                        panel.classList.remove('zCollapsed');
                        button.classList.remove('zCollapsed');
                        button.setAttribute('aria-expanded', 'true');
                    }
                });
            });
        });

        console.log(`✅ zTheme: Initialized ${accordions.length} accordion(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Carousel Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes all carousels with .zCarousel class.
     * 
     * Usage:
     *   <div class="zCarousel" data-interval="5000" data-ride="true">
     *     <div class="zCarousel-inner">
     *       <div class="zCarousel-item zActive">Slide 1</div>
     *       <div class="zCarousel-item">Slide 2</div>
     *     </div>
     *     <button class="zCarousel-control-prev">Previous</button>
     *     <button class="zCarousel-control-next">Next</button>
     *   </div>
     * 
     * Options (data attributes):
     * - data-interval: Time between slides in ms (default: 5000)
     * - data-ride: Auto-start cycling (default: false)
     * - data-wrap: Loop back to start (default: true)
     * - data-pause: Pause on hover (default: true)
     */
    function initCarousel() {
        const carousels = document.querySelectorAll('.zCarousel');
        
        if (carousels.length === 0) {
            return; // No carousels on this page
        }

        carousels.forEach(carousel => {
            const inner = carousel.querySelector('.zCarousel-inner');
            const items = carousel.querySelectorAll('.zCarousel-item');
            const prevBtn = carousel.querySelector('.zCarousel-control-prev');
            const nextBtn = carousel.querySelector('.zCarousel-control-next');
            const indicators = carousel.querySelectorAll('.zCarousel-indicators button');
            const progressBar = carousel.querySelector('.zCarousel-progress-bar');
            
            if (items.length === 0) return;
            
            // Configuration
            const interval = parseInt(carousel.dataset.interval) || 5000;
            const autoRide = carousel.dataset.ride === 'true';
            const wrap = carousel.dataset.wrap !== 'false';
            const pauseOnHover = carousel.dataset.pause !== 'false';
            const touch = carousel.dataset.touch !== 'false';
            
            // Custom event hooks (user can override these)
            const hooks = {
                onSlideChange: carousel.dataset.onSlideChange ? window[carousel.dataset.onSlideChange] : null,
                onTransitionStart: carousel.dataset.onTransitionStart ? window[carousel.dataset.onTransitionStart] : null,
                onTransitionEnd: carousel.dataset.onTransitionEnd ? window[carousel.dataset.onTransitionEnd] : null,
            };
            
            // Detect transition type
            const isFade = carousel.classList.contains('zCarousel-fade');
            const isVertical = carousel.classList.contains('zCarousel-vertical');
            
            let currentIndex = Array.from(items).findIndex(item => item.classList.contains('zActive'));
            if (currentIndex === -1) currentIndex = 0;
            
            let intervalId = null;
            let isTransitioning = false;
            
            // Touch swipe support
            let touchStartX = 0;
            let touchStartY = 0;
            let touchEndX = 0;
            let touchEndY = 0;
            
            // Show slide at index
            function showSlide(index) {
                if (isTransitioning) return;
                
                if (!wrap) {
                    if (index < 0 || index >= items.length) return;
                }
                
                // Wrap around
                if (index < 0) index = items.length - 1;
                if (index >= items.length) index = 0;
                
                if (index === currentIndex) return;
                
                isTransitioning = true;
                const direction = index > currentIndex ? 'next' : 'prev';
                const oldIndex = currentIndex;
                const activeItem = items[oldIndex];
                const nextItem = items[index];
                
                // Fire transition start hook
                if (hooks.onTransitionStart) {
                    hooks.onTransitionStart({ from: oldIndex, to: index, direction });
                }
                
                // For fade transition, need both slides visible and transitioning
                if (isFade) {
                    // Step 1: Make next item visible but transparent/small
                    nextItem.classList.add('zCarousel-item-next');
                    
                    // Step 2: Mark outgoing slide for fade-out (keeps it visible)
                    activeItem.classList.add('zCarousel-item-prev');
                    
                    // Step 3: Force reflow
                    nextItem.offsetHeight;
                    
                    // Step 4: Start BOTH transitions simultaneously
                    // Incoming: transparent → opaque (or small → large)
                    nextItem.classList.add('zActive');
                    // Outgoing: opaque → transparent (or large → small)
                    activeItem.classList.remove('zActive');
                    
                    currentIndex = index;
                    
                    // Fire slide change hook
                    if (hooks.onSlideChange) {
                        hooks.onSlideChange({ index: currentIndex, direction });
                    }
                    
                    updateControls();
                    
                    // Step 5: Clean up after BOTH transitions complete
                    setTimeout(() => {
                        // Remove all transition classes
                        nextItem.classList.remove('zCarousel-item-next');
                        activeItem.classList.remove('zCarousel-item-prev');
                        
                        isTransitioning = false;
                        if (hooks.onTransitionEnd) {
                            hooks.onTransitionEnd({ index: currentIndex, direction });
                        }
                    }, 1200); // Fade duration
                    
                    return;
                }
                
                // For slide transitions (horizontal/vertical), use proper transition sequencing
                const directionalClassName = direction === 'next' ? 'zCarousel-item-next' : 'zCarousel-item-prev';
                const orderClassName = direction === 'next' ? 'zCarousel-item-start' : 'zCarousel-item-end';
                
                // Step 1: Position the next item off-screen in the correct direction
                nextItem.classList.add(directionalClassName);
                
                // Step 2: Force reflow to ensure the positioning is applied
                nextItem.offsetHeight; // Force reflow
                
                // Step 3: Start the transition
                activeItem.classList.add(orderClassName);
                nextItem.classList.add(orderClassName);
                
                // Step 4: Wait for transition to complete, then clean up
                setTimeout(() => {
                    // Clean up all transition classes
                    activeItem.classList.remove('zActive', orderClassName);
                    nextItem.classList.remove(directionalClassName, orderClassName);
                    nextItem.classList.add('zActive');
                    
                    currentIndex = index;
                    
                    // Fire slide change hook
                    if (hooks.onSlideChange) {
                        hooks.onSlideChange({ index: currentIndex, direction });
                    }
                    
                    updateControls();
                    
                    isTransitioning = false;
                    
                    // Fire transition end hook
                    if (hooks.onTransitionEnd) {
                        hooks.onTransitionEnd({ index: currentIndex, direction });
                    }
                }, 600); // Match CSS transition duration
            }
            
            // Update indicators and progress bar
            function updateControls() {
                // Update indicators
                indicators.forEach((indicator, i) => {
                    if (i === currentIndex) {
                        indicator.classList.add('zActive');
                        indicator.setAttribute('aria-current', 'true');
                    } else {
                        indicator.classList.remove('zActive');
                        indicator.removeAttribute('aria-current');
                    }
                });
                
                // Update progress bar
                if (progressBar) {
                    const progress = ((currentIndex + 1) / items.length) * 100;
                    progressBar.style.width = progress + '%';
                }
            }
            
            // Next slide
            function next() {
                showSlide(currentIndex + 1);
            }
            
            // Previous slide
            function prev() {
                showSlide(currentIndex - 1);
            }
            
            // Start auto-cycling
            function startCycle() {
                if (intervalId) return;
                intervalId = setInterval(next, interval);
            }
            
            // Stop auto-cycling
            function stopCycle() {
                if (intervalId) {
                    clearInterval(intervalId);
                    intervalId = null;
                }
            }
            
            // Previous button
            if (prevBtn) {
                prevBtn.addEventListener('click', () => {
                    prev();
                    stopCycle();
                });
            }
            
            // Next button
            if (nextBtn) {
                nextBtn.addEventListener('click', () => {
                    next();
                    stopCycle();
                });
            }
            
            // Indicators
            indicators.forEach((indicator, index) => {
                indicator.addEventListener('click', () => {
                    showSlide(index);
                    stopCycle();
                });
            });
            
            // Pause on hover
            if (pauseOnHover) {
                carousel.addEventListener('mouseenter', stopCycle);
                carousel.addEventListener('mouseleave', () => {
                    if (autoRide) startCycle();
                });
            }
            
            // Keyboard navigation
            carousel.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowLeft' || (isVertical && e.key === 'ArrowUp')) {
                    prev();
                    stopCycle();
                } else if (e.key === 'ArrowRight' || (isVertical && e.key === 'ArrowDown')) {
                    next();
                    stopCycle();
                }
            });
            
            // Touch swipe support
            if (touch) {
                carousel.addEventListener('touchstart', (e) => {
                    touchStartX = e.changedTouches[0].screenX;
                    touchStartY = e.changedTouches[0].screenY;
                }, { passive: true });
                
                carousel.addEventListener('touchend', (e) => {
                    touchEndX = e.changedTouches[0].screenX;
                    touchEndY = e.changedTouches[0].screenY;
                    handleSwipe();
                }, { passive: true });
            }
            
            function handleSwipe() {
                const diffX = touchStartX - touchEndX;
                const diffY = touchStartY - touchEndY;
                const threshold = 50; // Minimum swipe distance
                
                if (isVertical) {
                    // Vertical swipe
                    if (Math.abs(diffY) > threshold && Math.abs(diffY) > Math.abs(diffX)) {
                        if (diffY > 0) {
                            // Swipe up - next slide
                            next();
                        } else {
                            // Swipe down - previous slide
                            prev();
                        }
                        stopCycle();
                    }
                } else {
                    // Horizontal swipe
                    if (Math.abs(diffX) > threshold && Math.abs(diffX) > Math.abs(diffY)) {
                        if (diffX > 0) {
                            // Swipe left - next slide
                            next();
                        } else {
                            // Swipe right - previous slide
                            prev();
                        }
                        stopCycle();
                    }
                }
            }
            
            // Auto-start if requested
            if (autoRide) {
                startCycle();
            }
        });

        console.log(`✅ zTheme: Initialized ${carousels.length} carousel(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Collapse Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes all collapse toggle buttons with data-bs-toggle="collapse".
     * 
     * Usage:
     *   <button data-bs-toggle="collapse" data-bs-target="#myCollapse" 
     *           aria-expanded="false" aria-controls="myCollapse">
     *     Toggle
     *   </button>
     *   <div id="myCollapse" class="zCollapse">
     *     Hidden content here
     *   </div>
     * 
     * How it works:
     * 1. Finds all elements with data-bs-toggle="collapse"
     * 2. Attaches click handlers to toggle target elements
     * 3. Animates height from 0 to full height (or reverse)
     * 4. Updates aria-expanded attribute for accessibility
     */
    function initCollapse() {
        const triggers = document.querySelectorAll('[data-bs-toggle="collapse"]');
        
        if (triggers.length === 0) {
            return;
        }
        
        triggers.forEach(trigger => {
            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Get target element(s)
                const targetSelector = this.getAttribute('data-bs-target') || this.getAttribute('href');
                if (!targetSelector) return;
                
                const targets = document.querySelectorAll(targetSelector);
                
                targets.forEach(target => {
                    // Check if this is a navbar collapse (simpler show/hide, no animation)
                    const isNavbarCollapse = target.classList.contains('zNavbar-collapse');
                    
                    if (isNavbarCollapse) {
                        // Navbar: simple toggle with .show class
                        const isCollapsed = !target.classList.contains('show');
                        
                        if (isCollapsed) {
                            target.classList.add('show');
                            this.setAttribute('aria-expanded', 'true');
                        } else {
                            target.classList.remove('show');
                            this.setAttribute('aria-expanded', 'false');
                        }
                    } else {
                        // Standard collapse: animated height transition
                        const isCollapsed = !target.classList.contains('zShow');
                        
                        if (isCollapsed) {
                            // Expand
                            target.style.height = '0px';
                            target.classList.remove('zCollapse');
                            target.classList.add('zCollapsing');
                            
                            // Force reflow
                            target.offsetHeight;
                            
                            // Get full height
                            target.style.height = target.scrollHeight + 'px';
                            
                            // After transition, clean up
                            setTimeout(() => {
                                target.classList.remove('zCollapsing');
                                target.classList.add('zCollapse', 'zShow');
                                target.style.height = '';
                            }, 350); // Match CSS transition duration
                            
                        } else {
                            // Collapse
                            target.style.height = target.scrollHeight + 'px';
                            
                            // Force reflow
                            target.offsetHeight;
                            
                            target.classList.remove('zCollapse', 'zShow');
                            target.classList.add('zCollapsing');
                            target.style.height = '0px';
                            
                            // After transition, clean up
                            setTimeout(() => {
                                target.classList.remove('zCollapsing');
                                target.classList.add('zCollapse');
                                target.style.height = '';
                            }, 350);
                        }
                        
                        // Update aria-expanded
                        this.setAttribute('aria-expanded', isCollapsed);
                    }
                });
            });
        });
        
        console.log(`✅ zTheme: Initialized ${triggers.length} collapse trigger(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Navbar Dropdown Handler (Mobile)
     * ═══════════════════════════════════════════════════════════
     * 
     * Handles click-to-toggle for navbar dropdowns on mobile/touch devices.
     * On desktop, dropdowns open on hover (CSS only).
     * On mobile, dropdowns toggle on click.
     */
    function initNavbarDropdowns() {
        const navbarDropdowns = document.querySelectorAll('.zNavbar .zNav-dropdown');
        
        if (navbarDropdowns.length === 0) {
            return;
        }
        
        navbarDropdowns.forEach(dropdown => {
            const link = dropdown.querySelector('.zNav-link');
            if (!link) return;
            
            link.addEventListener('click', function(e) {
                // Only prevent default and toggle on mobile (≤768px)
                if (window.innerWidth <= 768) {
                    e.preventDefault();
                    
                    // Close other dropdowns in the same navbar
                    const navbar = dropdown.closest('.zNavbar');
                    const otherDropdowns = navbar.querySelectorAll('.zNav-dropdown.show');
                    otherDropdowns.forEach(other => {
                        if (other !== dropdown) {
                            other.classList.remove('show');
                        }
                    });
                    
                    // Toggle this dropdown
                    dropdown.classList.toggle('show');
                }
                // On desktop (>768px), let the link navigate normally, hover handles dropdown
            });
        });
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                const isDropdownClick = e.target.closest('.zNav-dropdown');
                if (!isDropdownClick) {
                    navbarDropdowns.forEach(dropdown => {
                        dropdown.classList.remove('show');
                    });
                }
            }
        });
        
        console.log(`✅ zTheme: Initialized ${navbarDropdowns.length} navbar dropdown(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Dropdown Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes all dropdown toggle buttons with data-bs-toggle="dropdown".
     * 
     * Usage:
     *   <div class="zDropdown">
     *     <button class="zBtn zDropdown-toggle" data-bs-toggle="dropdown">
     *       Dropdown
     *     </button>
     *     <ul class="zDropdown-menu">
     *       <li><a class="zDropdown-item" href="#">Action</a></li>
     *     </ul>
     *   </div>
     * 
     * How it works:
     * 1. Finds all elements with data-bs-toggle="dropdown"
     * 2. Attaches click handlers to toggle dropdown menus
     * 3. Closes dropdown when clicking outside
     * 4. Supports keyboard navigation (Escape to close, Arrow keys to navigate)
     */
    function initDropdown() {
        const toggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        
        if (toggles.length === 0) {
            return;
        }
        
        // Close all dropdowns
        function closeAllDropdowns() {
            document.querySelectorAll('.zDropdown-menu.zShow').forEach(menu => {
                menu.classList.remove('zShow');
                const toggle = menu.previousElementSibling;
                if (toggle) {
                    toggle.setAttribute('aria-expanded', 'false');
                }
            });
        }
        
        // Toggle dropdown
        toggles.forEach(toggle => {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Find the dropdown menu
                const menu = this.nextElementSibling;
                if (!menu || !menu.classList.contains('zDropdown-menu')) {
                    return;
                }
                
                // If this menu is already open, close it
                const isOpen = menu.classList.contains('zShow');
                
                // Close all other dropdowns first
                closeAllDropdowns();
                
                // Toggle this dropdown
                if (!isOpen) {
                    menu.classList.add('zShow');
                    this.setAttribute('aria-expanded', 'true');
                    
                    // Focus first item
                    const firstItem = menu.querySelector('.zDropdown-item');
                    if (firstItem) {
                        firstItem.focus();
                    }
                } else {
                    menu.classList.remove('zShow');
                    this.setAttribute('aria-expanded', 'false');
                }
            });
            
            // Initialize aria-expanded
            toggle.setAttribute('aria-expanded', 'false');
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.zDropdown, .zDropup, .zDropend, .zDropstart')) {
                closeAllDropdowns();
            }
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', function(e) {
            const openMenu = document.querySelector('.zDropdown-menu.zShow');
            if (!openMenu) return;
            
            // Escape key - close dropdown
            if (e.key === 'Escape') {
                e.preventDefault();
                closeAllDropdowns();
                // Return focus to toggle
                const toggle = openMenu.previousElementSibling;
                if (toggle) toggle.focus();
                return;
            }
            
            // Arrow keys - navigate items
            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                
                const items = Array.from(openMenu.querySelectorAll('.zDropdown-item:not(.zDisabled)'));
                if (items.length === 0) return;
                
                const currentIndex = items.findIndex(item => item === document.activeElement);
                
                if (e.key === 'ArrowDown') {
                    const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
                    items[nextIndex].focus();
                } else if (e.key === 'ArrowUp') {
                    const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
                    items[prevIndex].focus();
                }
            }
        });
        
        console.log(`✅ zTheme: Initialized ${toggles.length} dropdown(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * List Group Tab Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes list group items with data-bs-toggle="list".
     * Allows list groups to function as tab navigation.
     * 
     * Usage:
     *   <div class="zList-group">
     *     <a class="zList-group-item zList-group-item-action zActive" 
     *        data-bs-toggle="list" 
     *        href="#home">Home</a>
     *   </div>
     *   <div class="zTab-content">
     *     <div class="zTab-pane zActive" id="home">...</div>
     *   </div>
     * 
     * How it works:
     * 1. Finds all elements with data-bs-toggle="list"
     * 2. Attaches click handlers to switch tabs
     * 3. Updates active states on list items and tab panes
     */
    function initListGroup() {
        const triggers = document.querySelectorAll('[data-bs-toggle="list"]');
        
        if (triggers.length === 0) {
            return;
        }
        
        triggers.forEach(trigger => {
            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Don't do anything if clicking already active tab
                if (this.classList.contains('zActive')) {
                    return;
                }
                
                // Get target pane
                const targetId = this.getAttribute('href') || this.getAttribute('data-bs-target');
                if (!targetId) return;
                
                const targetPane = document.querySelector(targetId);
                if (!targetPane) return;
                
                // Get containers
                const listGroup = this.closest('.zList-group');
                const tabContent = targetPane.closest('.zTab-content');
                
                // Remove active from all items in this list group
                if (listGroup) {
                    listGroup.querySelectorAll('.zList-group-item').forEach(item => {
                        item.classList.remove('zActive');
                        item.setAttribute('aria-selected', 'false');
                    });
                }
                
                // Add active to clicked item
                this.classList.add('zActive');
                this.setAttribute('aria-selected', 'true');
                
                // Hide all tab panes in the same container
                if (tabContent) {
                    tabContent.querySelectorAll('.zTab-pane').forEach(pane => {
                        pane.classList.remove('zActive', 'zShow');
                    });
                }
                
                // Show target pane immediately
                targetPane.classList.add('zActive');
                
                // Add fade effect if pane has zFade class
                if (targetPane.classList.contains('zFade')) {
                    // Force reflow to restart CSS transition
                    targetPane.offsetHeight;
                    // Use requestAnimationFrame for smoother transition
                    requestAnimationFrame(() => {
                        targetPane.classList.add('zShow');
                    });
                } else {
                    targetPane.classList.add('zShow');
                }
            });
            
            // Initialize aria-selected based on current state
            if (trigger.classList.contains('zActive')) {
                trigger.setAttribute('aria-selected', 'true');
            } else {
                trigger.setAttribute('aria-selected', 'false');
            }
        });
        
        console.log(`✅ zTheme: Initialized ${triggers.length} list group tab(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Modal Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes modal dialogs with data-bs-toggle="modal".
     * Handles opening, closing, backdrop, focus trap, and keyboard navigation.
     * 
     * Usage:
     *   <button data-bs-toggle="modal" data-bs-target="#myModal">
     *     Launch modal
     *   </button>
     *   <div class="zModal zFade" id="myModal" tabindex="-1">
     *     <div class="zModal-dialog">
     *       <div class="zModal-content">...</div>
     *     </div>
     *   </div>
     * 
     * Features:
     * - Backdrop overlay with fade
     * - Body scroll lock
     * - ESC key to close
     * - Click outside to close (unless data-bs-backdrop="static")
     * - Focus trap within modal
     * - Smooth fade animations
     */
    function initModal() {
        const triggers = document.querySelectorAll('[data-bs-toggle="modal"]');
        const activeModals = new Set();
        
        if (triggers.length === 0) {
            return;
        }
        
        // Show modal
        function showModal(modal, triggerButton) {
            if (activeModals.has(modal)) return;
            
            const isStatic = modal.getAttribute('data-bs-backdrop') === 'static';
            // Check for any animation class
            const hasAnimation = modal.classList.contains('zFade') || 
                                 modal.classList.contains('zSlideUp') ||
                                 modal.classList.contains('zZoomIn') ||
                                 modal.classList.contains('zSlideLeft') ||
                                 modal.classList.contains('zSlideRight') ||
                                 modal.classList.contains('zFadeOnly');
            
            // Create backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'zModal-backdrop' + (hasAnimation ? ' zFade' : '');
            backdrop.setAttribute('data-modal-id', modal.id);
            document.body.appendChild(backdrop);
            
            // Lock body scroll
            document.body.classList.add('zModal-open');
            
            // Show modal
            modal.setAttribute('aria-hidden', 'false');
            modal.setAttribute('aria-modal', 'true');
            
            if (hasAnimation) {
                // Step 1: Make modal visible (to render initial animation state)
                modal.style.display = 'block';
                
                // Step 2: Force reflow so browser renders the initial transform state
                modal.offsetHeight;
                
                // Step 3: Add .zShow class to trigger animation to final state
                requestAnimationFrame(() => {
                    modal.classList.add('zShow');
                    backdrop.classList.add('zShow');
                    // Remove inline style after .zShow is applied
                    requestAnimationFrame(() => {
                        modal.style.display = '';
                    });
                });
            } else {
                // No animation: just show immediately
                modal.classList.add('zShow');
                backdrop.classList.add('zShow');
            }
            
            activeModals.add(modal);
            
            // Focus first focusable element in modal
            setTimeout(() => {
                const focusable = modal.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                if (focusable.length > 0) {
                    focusable[0].focus();
                }
            }, hasAnimation ? 300 : 0);
            
            // Close on backdrop click (unless static)
            if (!isStatic) {
                backdrop.addEventListener('click', () => hideModal(modal));
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        hideModal(modal);
                    }
                });
            } else {
                // Static backdrop: animate modal on click outside
                backdrop.addEventListener('click', () => {
                    modal.classList.add('zModal-static');
                    setTimeout(() => modal.classList.remove('zModal-static'), 300);
                });
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        modal.classList.add('zModal-static');
                        setTimeout(() => modal.classList.remove('zModal-static'), 300);
                    }
                });
            }
            
            // Close on ESC key (unless data-bs-keyboard="false")
            const closeOnEsc = modal.getAttribute('data-bs-keyboard') !== 'false';
            if (closeOnEsc) {
                const escHandler = (e) => {
                    if (e.key === 'Escape' && activeModals.has(modal)) {
                        hideModal(modal);
                        document.removeEventListener('keydown', escHandler);
                    }
                };
                document.addEventListener('keydown', escHandler);
                modal._escHandler = escHandler;
            }
            
            // Close buttons
            const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
            closeButtons.forEach(btn => {
                const clickHandler = () => hideModal(modal);
                btn.addEventListener('click', clickHandler);
                btn._modalCloseHandler = clickHandler;
            });
        }
        
        // Hide modal
        function hideModal(modal) {
            if (!activeModals.has(modal)) return;
            
            // Check for any animation class
            const hasAnimation = modal.classList.contains('zFade') || 
                                 modal.classList.contains('zSlideUp') ||
                                 modal.classList.contains('zZoomIn') ||
                                 modal.classList.contains('zSlideLeft') ||
                                 modal.classList.contains('zSlideRight') ||
                                 modal.classList.contains('zFadeOnly');
            const backdrop = document.querySelector(`.zModal-backdrop[data-modal-id="${modal.id}"]`);
            
            // Remove show class
            modal.classList.remove('zShow');
            if (backdrop) {
                backdrop.classList.remove('zShow');
            }
            
            // Wait for transition, then cleanup
            const cleanupDelay = hasAnimation ? 300 : 0;
            setTimeout(() => {
                // CSS .zShow removal already handles display: none
                modal.setAttribute('aria-hidden', 'true');
                modal.removeAttribute('aria-modal');
                
                if (backdrop) {
                    backdrop.remove();
                }
                
                activeModals.delete(modal);
                
                // Unlock body scroll if no modals are open
                if (activeModals.size === 0) {
                    document.body.classList.remove('zModal-open');
                }
                
                // Clean up ESC handler
                if (modal._escHandler) {
                    document.removeEventListener('keydown', modal._escHandler);
                    delete modal._escHandler;
                }
            }, cleanupDelay);
        }
        
        // Initialize trigger buttons
        triggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                
                const targetId = trigger.getAttribute('data-bs-target') || trigger.getAttribute('href');
                if (!targetId) return;
                
                const modal = document.querySelector(targetId);
                if (!modal) return;
                
                showModal(modal, trigger);
            });
        });
        
        console.log(`✅ zTheme: Initialized ${triggers.length} modal(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Offcanvas Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes offcanvas slide-out panels.
     * 
     * Usage:
     *   <button data-bs-toggle="offcanvas" data-bs-target="#offcanvasMenu">
     *     Open Menu
     *   </button>
     *   
     *   <div class="zOffcanvas zOffcanvas-start" id="offcanvasMenu">
     *     <div class="zOffcanvas-header">
     *       <h5 class="zOffcanvas-title">Menu</h5>
     *       <button type="button" class="zBtn-close" data-bs-dismiss="offcanvas"></button>
     *     </div>
     *     <div class="zOffcanvas-body">
     *       Content here...
     *     </div>
     *   </div>
     * 
     * Options (data attributes):
     *   data-bs-backdrop="false" - Disable backdrop
     *   data-bs-scroll="true"     - Allow body scroll while open
     * 
     * How it works:
     * 1. Finds all elements with data-bs-toggle="offcanvas"
     * 2. Adds click handlers to show offcanvas
     * 3. Manages backdrop, body scroll lock, and animations
     * 4. Handles ESC key, click-outside, and close buttons
     */
    function initOffcanvas() {
        const triggers = document.querySelectorAll('[data-bs-toggle="offcanvas"]');
        const activeOffcanvas = new Set();
        
        if (triggers.length === 0) {
            return;
        }
        
        // Show offcanvas
        function showOffcanvas(offcanvas, triggerButton) {
            if (activeOffcanvas.has(offcanvas)) return;
            
            const showBackdrop = offcanvas.getAttribute('data-bs-backdrop') !== 'false';
            const allowScroll = offcanvas.getAttribute('data-bs-scroll') === 'true';
            
            // Create backdrop if enabled
            let backdrop = null;
            if (showBackdrop) {
                backdrop = document.createElement('div');
                backdrop.className = 'zOffcanvas-backdrop';
                backdrop.setAttribute('data-offcanvas-id', offcanvas.id);
                document.body.appendChild(backdrop);
                
                // Force reflow to ensure initial state is rendered
                backdrop.offsetHeight;
                
                // Trigger animation
                requestAnimationFrame(() => {
                    backdrop.classList.add('zShow');
                });
                
                // Close on backdrop click
                backdrop.addEventListener('click', () => hideOffcanvas(offcanvas));
            }
            
            // Lock body scroll unless scroll is enabled
            if (!allowScroll) {
                document.body.classList.add('zOffcanvas-open');
            } else {
                // Mark body for scroll-enabled mode (for CSS purposes if needed)
                document.body.setAttribute('data-offcanvas-scroll', 'true');
            }
            
            // Show offcanvas with animation
            offcanvas.setAttribute('aria-hidden', 'false');
            
            // Step 1: Make visible with display
            offcanvas.style.display = 'block';
            
            // Step 2: Force reflow
            offcanvas.offsetHeight;
            
            // Step 3: Add .zShow to trigger slide animation
            requestAnimationFrame(() => {
                offcanvas.classList.add('zShow');
                // Remove inline style after .zShow is applied
                requestAnimationFrame(() => {
                    offcanvas.style.display = '';
                });
            });
            
            activeOffcanvas.add(offcanvas);
            
            // Focus first focusable element
            setTimeout(() => {
                const focusable = offcanvas.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                if (focusable.length > 0) {
                    focusable[0].focus();
                }
            }, 300);
            
            // Close on ESC key
            const escHandler = (e) => {
                if (e.key === 'Escape' && activeOffcanvas.has(offcanvas)) {
                    hideOffcanvas(offcanvas);
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
            offcanvas._escHandler = escHandler;
            
            // Close buttons
            const closeButtons = offcanvas.querySelectorAll('[data-bs-dismiss="offcanvas"]');
            closeButtons.forEach(btn => {
                const clickHandler = () => hideOffcanvas(offcanvas);
                btn.addEventListener('click', clickHandler);
                btn._offcanvasCloseHandler = clickHandler;
            });
        }
        
        // Hide offcanvas
        function hideOffcanvas(offcanvas) {
            if (!activeOffcanvas.has(offcanvas)) return;
            
            const backdrop = document.querySelector(`.zOffcanvas-backdrop[data-offcanvas-id="${offcanvas.id}"]`);
            
            // Remove show class to trigger slide-out animation
            offcanvas.classList.remove('zShow');
            if (backdrop) {
                backdrop.classList.remove('zShow');
            }
            
            // Wait for transition, then cleanup
            setTimeout(() => {
                offcanvas.setAttribute('aria-hidden', 'true');
                
                if (backdrop) {
                    backdrop.remove();
                }
                
                activeOffcanvas.delete(offcanvas);
                
                // Unlock body scroll if no offcanvas are open
                if (activeOffcanvas.size === 0) {
                    document.body.classList.remove('zOffcanvas-open');
                    document.body.removeAttribute('data-offcanvas-scroll');
                }
                
                // Clean up ESC handler
                if (offcanvas._escHandler) {
                    document.removeEventListener('keydown', offcanvas._escHandler);
                    delete offcanvas._escHandler;
                }
                
                // Clean up close button handlers
                const closeButtons = offcanvas.querySelectorAll('[data-bs-dismiss="offcanvas"]');
                closeButtons.forEach(btn => {
                    if (btn._offcanvasCloseHandler) {
                        btn.removeEventListener('click', btn._offcanvasCloseHandler);
                        delete btn._offcanvasCloseHandler;
                    }
                });
            }, 300);
        }
        
        // Initialize trigger buttons
        triggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                
                const targetId = trigger.getAttribute('data-bs-target') || trigger.getAttribute('href');
                if (!targetId) return;
                
                const offcanvas = document.querySelector(targetId);
                if (!offcanvas) return;
                
                showOffcanvas(offcanvas, trigger);
            });
        });
        
        console.log(`✅ zTheme: Initialized ${triggers.length} offcanvas panel(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Popover Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes popovers with rich content overlays.
     * 
     * Usage:
     *   <button data-bs-toggle="popover" 
     *           data-bs-content="Popover content"
     *           data-bs-title="Title"
     *           data-bs-placement="top">
     *     Click me
     *   </button>
     * 
     * How it works:
     * 1. Finds all elements with data-bs-toggle="popover"
     * 2. Creates popover overlay with title and content
     * 3. Handles positioning (top, bottom, start, end)
     * 4. Manages show/hide with click, hover, or focus triggers
     * 5. Auto-closes when clicking outside
     */
    function initPopover() {
        const triggers = document.querySelectorAll('[data-bs-toggle="popover"]');
        
        if (triggers.length === 0) {
            return;
        }
        
        // Store active popovers for cleanup
        const activePopovers = new Map();
        
        function createPopover(trigger) {
            const content = trigger.getAttribute('data-bs-content') || '';
            const title = trigger.getAttribute('data-bs-title') || '';
            const placement = trigger.getAttribute('data-bs-placement') || 'bottom';
            const customClass = trigger.getAttribute('data-bs-custom-class') || '';
            
            const popover = document.createElement('div');
            popover.className = `zPopover zPopover-${placement} ${customClass}`.trim();
            popover.setAttribute('role', 'tooltip');
            
            // Create arrow
            const arrow = document.createElement('div');
            arrow.className = 'zPopover-arrow';
            popover.appendChild(arrow);
            
            // Create header (if title exists)
            if (title) {
                const header = document.createElement('div');
                header.className = 'zPopover-header';
                header.textContent = title;
                popover.appendChild(header);
            }
            
            // Create body
            const body = document.createElement('div');
            body.className = 'zPopover-body';
            body.innerHTML = content;
            popover.appendChild(body);
            
            return popover;
        }
        
        function positionPopover(popover, trigger) {
            const placement = trigger.getAttribute('data-bs-placement') || 'bottom';
            const triggerRect = trigger.getBoundingClientRect();
            const popoverRect = popover.getBoundingClientRect();
            
            let top, left;
            
            switch (placement) {
                case 'top':
                    top = triggerRect.top + window.scrollY - popoverRect.height - 8;
                    left = triggerRect.left + window.scrollX + (triggerRect.width / 2) - (popoverRect.width / 2);
                    // Position arrow
                    popover.querySelector('.zPopover-arrow').style.left = '50%';
                    popover.querySelector('.zPopover-arrow').style.transform = 'translateX(-50%)';
                    break;
                
                case 'bottom':
                    top = triggerRect.bottom + window.scrollY + 8;
                    left = triggerRect.left + window.scrollX + (triggerRect.width / 2) - (popoverRect.width / 2);
                    // Position arrow
                    popover.querySelector('.zPopover-arrow').style.left = '50%';
                    popover.querySelector('.zPopover-arrow').style.transform = 'translateX(-50%)';
                    break;
                
                case 'start':
                    top = triggerRect.top + window.scrollY + (triggerRect.height / 2) - (popoverRect.height / 2);
                    left = triggerRect.left + window.scrollX - popoverRect.width - 8;
                    // Position arrow
                    popover.querySelector('.zPopover-arrow').style.top = '50%';
                    popover.querySelector('.zPopover-arrow').style.transform = 'translateY(-50%)';
                    break;
                
                case 'end':
                    top = triggerRect.top + window.scrollY + (triggerRect.height / 2) - (popoverRect.height / 2);
                    left = triggerRect.right + window.scrollX + 8;
                    // Position arrow
                    popover.querySelector('.zPopover-arrow').style.top = '50%';
                    popover.querySelector('.zPopover-arrow').style.transform = 'translateY(-50%)';
                    break;
            }
            
            // Keep popover in viewport
            const maxLeft = window.innerWidth + window.scrollX - popoverRect.width - 10;
            const maxTop = window.innerHeight + window.scrollY - popoverRect.height - 10;
            
            left = Math.max(10, Math.min(left, maxLeft));
            top = Math.max(10, Math.min(top, maxTop));
            
            popover.style.top = `${top}px`;
            popover.style.left = `${left}px`;
        }
        
        function showPopover(trigger) {
            // Hide any existing popovers
            hideAllPopovers();
            
            const popover = createPopover(trigger);
            document.body.appendChild(popover);
            
            // Position after adding to DOM (so we can get dimensions)
            requestAnimationFrame(() => {
                positionPopover(popover, trigger);
                
                // Show with animation
                requestAnimationFrame(() => {
                    popover.classList.add('zShow');
                });
            });
            
            // Store reference
            activePopovers.set(trigger, popover);
            
            // Add outside click handler to close
            setTimeout(() => {
                document.addEventListener('click', outsideClickHandler);
            }, 10);
        }
        
        function hidePopover(trigger) {
            const popover = activePopovers.get(trigger);
            if (!popover) return;
            
            popover.classList.remove('zShow');
            
            setTimeout(() => {
                if (popover.parentNode) {
                    popover.parentNode.removeChild(popover);
                }
                activePopovers.delete(trigger);
                
                // Remove outside click handler if no popovers are active
                if (activePopovers.size === 0) {
                    document.removeEventListener('click', outsideClickHandler);
                }
            }, 150);
        }
        
        function hideAllPopovers() {
            activePopovers.forEach((popover, trigger) => {
                hidePopover(trigger);
            });
        }
        
        function outsideClickHandler(e) {
            // Close popover if clicking outside
            let clickedTrigger = false;
            let clickedPopover = false;
            
            activePopovers.forEach((popover, trigger) => {
                if (trigger.contains(e.target)) {
                    clickedTrigger = true;
                }
                if (popover.contains(e.target)) {
                    clickedPopover = true;
                }
            });
            
            if (!clickedTrigger && !clickedPopover) {
                hideAllPopovers();
            }
        }
        
        // Initialize all popover triggers
        triggers.forEach(trigger => {
            const triggerType = trigger.getAttribute('data-bs-trigger') || 'click';
            
            if (triggerType === 'click') {
                trigger.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const popover = activePopovers.get(trigger);
                    if (popover) {
                        hidePopover(trigger);
                    } else {
                        showPopover(trigger);
                    }
                });
            } else if (triggerType === 'hover') {
                trigger.addEventListener('mouseenter', () => {
                    showPopover(trigger);
                });
                
                trigger.addEventListener('mouseleave', () => {
                    // Delay hiding to allow moving mouse to popover
                    setTimeout(() => {
                        const popover = activePopovers.get(trigger);
                        if (popover && !popover.matches(':hover')) {
                            hidePopover(trigger);
                        }
                    }, 100);
                });
                
                // Keep popover open when hovering over it
                trigger.addEventListener('mouseenter', function addPopoverHover() {
                    const popover = activePopovers.get(trigger);
                    if (popover) {
                        popover.addEventListener('mouseleave', () => {
                            hidePopover(trigger);
                        });
                    }
                });
            } else if (triggerType === 'focus') {
                trigger.addEventListener('focus', () => {
                    showPopover(trigger);
                });
                
                trigger.addEventListener('blur', () => {
                    hidePopover(trigger);
                });
            }
        });
        
        console.log(`✅ zTheme: Initialized ${triggers.length} popover(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Scrollspy Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-highlights navigation links based on scroll position.
     * 
     * Usage:
     *   <body data-bs-spy="scroll" data-bs-target="#navbar" data-bs-offset="10">
     *     <nav id="navbar">
     *       <a href="#section1">Section 1</a>
     *       <a href="#section2">Section 2</a>
     *     </nav>
     *     <div id="section1">Content...</div>
     *     <div id="section2">Content...</div>
     *   </body>
     * 
     * How it works:
     * 1. Finds elements with data-bs-spy="scroll"
     * 2. Watches scroll position on that element
     * 3. Updates .zActive class on nav links based on visible sections
     * 4. Works with nested navs and dropdowns
     * 5. Fires activate.bs.scrollspy event when items change
     */
    function initScrollspy() {
        const spyElements = document.querySelectorAll('[data-bs-spy="scroll"]');
        
        if (spyElements.length === 0) {
            return;
        }
        
        spyElements.forEach(spyElement => {
            const targetSelector = spyElement.getAttribute('data-bs-target');
            const offset = parseInt(spyElement.getAttribute('data-bs-offset') || '10');
            
            if (!targetSelector) {
                console.warn('zTheme Scrollspy: data-bs-target is required');
                return;
            }
            
            const navElement = document.querySelector(targetSelector);
            if (!navElement) {
                console.warn(`zTheme Scrollspy: Target not found: ${targetSelector}`);
                return;
            }
            
            // Get all navigation links
            const navLinks = navElement.querySelectorAll('a[href^="#"]');
            const sections = [];
            
            // Build sections array with their corresponding nav links
            navLinks.forEach(link => {
                const href = link.getAttribute('href');
                if (href && href !== '#') {
                    const section = document.querySelector(href);
                    if (section) {
                        sections.push({
                            id: href,
                            element: section,
                            link: link
                        });
                    }
                }
            });
            
            if (sections.length === 0) {
                return;
            }
            
            // Function to update active states
            function updateActive() {
                const scrollPos = spyElement.scrollTop || window.pageYOffset;
                const containerTop = spyElement === document.body ? 0 : spyElement.getBoundingClientRect().top;
                
                let current = null;
                
                // Find the current section
                for (let i = sections.length - 1; i >= 0; i--) {
                    const section = sections[i];
                    const rect = section.element.getBoundingClientRect();
                    const sectionTop = rect.top - containerTop - offset;
                    
                    if (sectionTop <= 0) {
                        current = section;
                        break;
                    }
                }
                
                // If we're at the very top, activate the first section
                if (!current && scrollPos < offset) {
                    current = sections[0];
                }
                
                // Update active states
                sections.forEach(section => {
                    const wasActive = section.link.classList.contains('zActive');
                    
                    if (section === current) {
                        if (!wasActive) {
                            section.link.classList.add('zActive');
                            
                            // Also activate parent nav items (for nested navs)
                            let parent = section.link.closest('.zNav-item');
                            while (parent) {
                                const parentLink = parent.querySelector('.zNav-link');
                                if (parentLink) {
                                    parentLink.classList.add('zActive');
                                }
                                parent = parent.parentElement.closest('.zNav-item');
                            }
                            
                            // Fire custom event
                            const event = new CustomEvent('activate.bs.scrollspy', {
                                detail: { relatedTarget: section.link }
                            });
                            spyElement.dispatchEvent(event);
                        }
                    } else {
                        section.link.classList.remove('zActive');
                    }
                });
                
                // Handle list-group items
                const listGroupItems = navElement.querySelectorAll('.zList-group-item');
                listGroupItems.forEach(item => {
                    if (current && item.getAttribute('href') === current.id) {
                        item.classList.add('zActive');
                    } else {
                        item.classList.remove('zActive');
                    }
                });
            }
            
            // Throttle scroll events for performance
            let ticking = false;
            function onScroll() {
                if (!ticking) {
                    window.requestAnimationFrame(() => {
                        updateActive();
                        ticking = false;
                    });
                    ticking = true;
                }
            }
            
            // Listen to scroll events
            if (spyElement === document.body || spyElement === document.documentElement) {
                window.addEventListener('scroll', onScroll, { passive: true });
            } else {
                spyElement.addEventListener('scroll', onScroll, { passive: true });
            }
            
            // Initial update
            updateActive();
            
            // Store refresh method for public API
            spyElement._scrollspyRefresh = updateActive;
        });
        
        console.log(`✅ zTheme: Initialized ${spyElements.length} scrollspy element(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Toast Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes toast notifications with show/hide/auto-dismiss.
     * 
     * Usage:
     *   <div class="zToast" role="alert" aria-live="assertive" aria-atomic="true">
     *     <div class="zToast-header">
     *       <strong class="zMe-auto">Title</strong>
     *       <button type="button" class="zBtn-close" data-bs-dismiss="toast"></button>
     *     </div>
     *     <div class="zToast-body">Message</div>
     *   </div>
     * 
     * How it works:
     * 1. Finds all .zToast elements
     * 2. Handles show/hide with fade animations
     * 3. Auto-hides after delay (default 5000ms)
     * 4. Supports dismiss buttons
     * 5. Fires custom events (show, shown, hide, hidden)
     */
    function initToast() {
        const toasts = document.querySelectorAll('.zToast');
        
        if (toasts.length === 0) {
            return;
        }
        
        // Store toast instances
        const toastInstances = new Map();
        
        function showToast(toast) {
            const autohide = toast.getAttribute('data-bs-autohide') !== 'false';
            const delay = parseInt(toast.getAttribute('data-bs-delay') || '5000');
            const animation = toast.getAttribute('data-bs-animation') !== 'false';
            
            // Fire show event
            const showEvent = new CustomEvent('show.bs.toast', { cancelable: true });
            toast.dispatchEvent(showEvent);
            if (showEvent.defaultPrevented) return;
            
            // Add fade class if animation enabled
            if (animation && !toast.classList.contains('zFade')) {
                toast.classList.add('zFade');
            }
            
            // Show toast
            toast.classList.add('zShow');
            
            // Fire shown event after animation
            setTimeout(() => {
                const shownEvent = new CustomEvent('shown.bs.toast');
                toast.dispatchEvent(shownEvent);
            }, animation ? 150 : 0);
            
            // Auto-hide if enabled
            if (autohide) {
                const timeout = setTimeout(() => {
                    hideToast(toast);
                }, delay);
                
                toastInstances.set(toast, { timeout });
            }
        }
        
        function hideToast(toast) {
            // Fire hide event
            const hideEvent = new CustomEvent('hide.bs.toast', { cancelable: true });
            toast.dispatchEvent(hideEvent);
            if (hideEvent.defaultPrevented) return;
            
            // Clear auto-hide timeout
            const instance = toastInstances.get(toast);
            if (instance && instance.timeout) {
                clearTimeout(instance.timeout);
            }
            
            // Hide toast
            toast.classList.remove('zShow');
            
            // Fire hidden event after animation
            const animation = toast.classList.contains('zFade');
            setTimeout(() => {
                const hiddenEvent = new CustomEvent('hidden.bs.toast');
                toast.dispatchEvent(hiddenEvent);
            }, animation ? 150 : 0);
        }
        
        // Initialize all toasts
        toasts.forEach(toast => {
            // Store instance
            toastInstances.set(toast, {});
            
            // Add public methods
            toast._show = () => showToast(toast);
            toast._hide = () => hideToast(toast);
            
            // Handle dismiss buttons
            const dismissButtons = toast.querySelectorAll('[data-bs-dismiss="toast"]');
            dismissButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    hideToast(toast);
                });
            });
            
            // Auto-show if data-bs-autohide is set
            if (toast.hasAttribute('data-bs-autoshow')) {
                setTimeout(() => showToast(toast), 100);
            }
        });
        
        console.log(`✅ zTheme: Initialized ${toasts.length} toast(s)`);
        
        // Return public API
        return {
            show: (toastElement) => {
                if (typeof toastElement === 'string') {
                    toastElement = document.querySelector(toastElement);
                }
                if (toastElement) showToast(toastElement);
            },
            hide: (toastElement) => {
                if (typeof toastElement === 'string') {
                    toastElement = document.querySelector(toastElement);
                }
                if (toastElement) hideToast(toastElement);
            }
        };
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Tooltip Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes tooltips on hover/focus.
     * 
     * Usage:
     *   <button data-bs-toggle="tooltip" title="Helpful hint">Hover me</button>
     * 
     * Options (data attributes):
     *   data-bs-placement="top|bottom|start|end" - Tooltip position
     *   data-bs-trigger="hover|focus|click" - Trigger event
     *   title="..." - Tooltip text content
     * 
     * How it works:
     * 1. Finds all [data-bs-toggle="tooltip"] elements
     * 2. Creates tooltip on hover/focus/click
     * 3. Positions automatically with arrow
     * 4. Auto-hides on mouse leave / blur
     * 5. Supports keyboard navigation
     */
    function initTooltip() {
        const triggers = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        
        if (triggers.length === 0) {
            return;
        }
        
        // Store active tooltips
        const activeTooltips = new Map();
        
        function createTooltip(trigger) {
            const title = trigger.getAttribute('title') || trigger.getAttribute('data-bs-original-title');
            
            if (!title || title.trim() === '') {
                return null;
            }
            
            // Store original title and remove it (prevents browser default tooltip)
            if (!trigger.hasAttribute('data-bs-original-title')) {
                trigger.setAttribute('data-bs-original-title', title);
                trigger.removeAttribute('title');
            }
            
            const placement = trigger.getAttribute('data-bs-placement') || 'top';
            
            const tooltip = document.createElement('div');
            tooltip.className = `zTooltip zTooltip-${placement} zFade`;
            tooltip.setAttribute('role', 'tooltip');
            
            const arrow = document.createElement('div');
            arrow.className = 'zTooltip-arrow';
            
            const inner = document.createElement('div');
            inner.className = 'zTooltip-inner';
            inner.textContent = title;
            
            tooltip.appendChild(arrow);
            tooltip.appendChild(inner);
            
            return tooltip;
        }
        
        function positionTooltip(trigger, tooltip) {
            const placement = trigger.getAttribute('data-bs-placement') || 'top';
            const triggerRect = trigger.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            const arrow = tooltip.querySelector('.zTooltip-arrow');
            
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
            
            let top, left, arrowPos;
            
            switch (placement) {
                case 'top':
                    top = triggerRect.top + scrollTop - tooltipRect.height - 8;
                    left = triggerRect.left + scrollLeft + (triggerRect.width / 2) - (tooltipRect.width / 2);
                    
                    // Keep tooltip within viewport horizontally
                    const minLeft = scrollLeft + 10;
                    const maxLeft = scrollLeft + window.innerWidth - tooltipRect.width - 10;
                    if (left < minLeft) left = minLeft;
                    if (left > maxLeft) left = maxLeft;
                    
                    // Position arrow to point at center of trigger
                    const triggerCenter = triggerRect.left + scrollLeft + (triggerRect.width / 2);
                    arrowPos = triggerCenter - left - 6; // 6 = half of arrow width (0.8rem = ~12px)
                    if (arrow) arrow.style.left = `${arrowPos}px`;
                    break;
                    
                case 'bottom':
                    top = triggerRect.bottom + scrollTop + 8;
                    left = triggerRect.left + scrollLeft + (triggerRect.width / 2) - (tooltipRect.width / 2);
                    
                    // Keep tooltip within viewport
                    const minLeftB = scrollLeft + 10;
                    const maxLeftB = scrollLeft + window.innerWidth - tooltipRect.width - 10;
                    if (left < minLeftB) left = minLeftB;
                    if (left > maxLeftB) left = maxLeftB;
                    
                    // Position arrow
                    const triggerCenterB = triggerRect.left + scrollLeft + (triggerRect.width / 2);
                    arrowPos = triggerCenterB - left - 6;
                    if (arrow) arrow.style.left = `${arrowPos}px`;
                    break;
                    
                case 'start':
                    top = triggerRect.top + scrollTop + (triggerRect.height / 2) - (tooltipRect.height / 2);
                    left = triggerRect.left + scrollLeft - tooltipRect.width - 8;
                    
                    // Position arrow vertically
                    const triggerMiddle = triggerRect.top + scrollTop + (triggerRect.height / 2);
                    arrowPos = triggerMiddle - top - 4; // 4 = half of arrow height
                    if (arrow) arrow.style.top = `${arrowPos}px`;
                    break;
                    
                case 'end':
                    top = triggerRect.top + scrollTop + (triggerRect.height / 2) - (tooltipRect.height / 2);
                    left = triggerRect.right + scrollLeft + 8;
                    
                    // Position arrow vertically
                    const triggerMiddleE = triggerRect.top + scrollTop + (triggerRect.height / 2);
                    arrowPos = triggerMiddleE - top - 4;
                    if (arrow) arrow.style.top = `${arrowPos}px`;
                    break;
                    
                default:
                    top = triggerRect.top + scrollTop - tooltipRect.height - 8;
                    left = triggerRect.left + scrollLeft + (triggerRect.width / 2) - (tooltipRect.width / 2);
            }
            
            tooltip.style.top = `${top}px`;
            tooltip.style.left = `${left}px`;
        }
        
        function showTooltip(trigger) {
            // Don't show if already active
            if (activeTooltips.has(trigger)) {
                return;
            }
            
            const tooltip = createTooltip(trigger);
            if (!tooltip) return;
            
            document.body.appendChild(tooltip);
            
            // Position tooltip
            requestAnimationFrame(() => {
                positionTooltip(trigger, tooltip);
                
                // Show with fade
                requestAnimationFrame(() => {
                    tooltip.classList.add('zShow');
                });
            });
            
            activeTooltips.set(trigger, tooltip);
        }
        
        function hideTooltip(trigger) {
            const tooltip = activeTooltips.get(trigger);
            if (!tooltip) return;
            
            tooltip.classList.remove('zShow');
            
            // Remove after animation
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
                activeTooltips.delete(trigger);
            }, 150);
        }
        
        // Initialize all tooltip triggers
        triggers.forEach(trigger => {
            const triggerType = trigger.getAttribute('data-bs-trigger') || 'hover focus';
            const triggerEvents = triggerType.split(' ');
            
            triggerEvents.forEach(eventType => {
                const trimmedEvent = eventType.trim();
                
                if (trimmedEvent === 'hover') {
                    trigger.addEventListener('mouseenter', () => {
                        showTooltip(trigger);
                    });
                    trigger.addEventListener('mouseleave', () => {
                        hideTooltip(trigger);
                    });
                } else if (trimmedEvent === 'focus') {
                    trigger.addEventListener('focus', () => {
                        showTooltip(trigger);
                    });
                    trigger.addEventListener('blur', () => {
                        hideTooltip(trigger);
                    });
                } else if (trimmedEvent === 'click') {
                    trigger.addEventListener('click', (e) => {
                        e.stopPropagation();
                        if (activeTooltips.has(trigger)) {
                            hideTooltip(trigger);
                        } else {
                            showTooltip(trigger);
                        }
                    });
                }
            });
            
            // Update position on scroll/resize
            window.addEventListener('scroll', () => {
                if (activeTooltips.has(trigger)) {
                    const tooltip = activeTooltips.get(trigger);
                    positionTooltip(trigger, tooltip);
                }
            });
            
            window.addEventListener('resize', () => {
                if (activeTooltips.has(trigger)) {
                    const tooltip = activeTooltips.get(trigger);
                    positionTooltip(trigger, tooltip);
                }
            });
        });
        
        console.log(`✅ zTheme: Initialized ${triggers.length} tooltip(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Tabs Handler
     * ═══════════════════════════════════════════════════════════
     * 
     * Auto-initializes tab switching for navigation tabs.
     * 
     * Usage:
     *   <ul class="zNav zNav-tabs">
     *     <li class="zNav-item">
     *       <a class="zNav-link zActive" data-bs-toggle="tab" href="#home">Home</a>
     *     </li>
     *     <li class="zNav-item">
     *       <a class="zNav-link" data-bs-toggle="tab" href="#profile">Profile</a>
     *     </li>
     *   </ul>
     *   <div class="zTab-content">
     *     <div class="zTab-pane zActive" id="home">...</div>
     *     <div class="zTab-pane" id="profile">...</div>
     *   </div>
     * 
     * How it works:
     * 1. Finds all elements with data-bs-toggle="tab"
     * 2. Adds click handlers to switch tabs
     * 3. Manages .zActive class and aria attributes
     * 4. Supports fade animations with .zFade class
     */
    function initTabs() {
        const tabTriggers = document.querySelectorAll('[data-bs-toggle="tab"]');
        
        if (tabTriggers.length === 0) {
            return;
        }
        
        function showTab(trigger) {
            // Get target pane
            const targetSelector = trigger.getAttribute('data-bs-target') || trigger.getAttribute('href');
            if (!targetSelector) return;
            
            const targetPane = document.querySelector(targetSelector);
            if (!targetPane) return;
            
            // Find the tab content container
            const tabContent = targetPane.closest('.zTab-content');
            
            // Find all triggers in the same nav group
            const nav = trigger.closest('.zNav');
            const allTriggers = nav ? nav.querySelectorAll('[data-bs-toggle="tab"]') : [];
            
            // Deactivate all tabs in this group
            allTriggers.forEach(t => {
                t.classList.remove('zActive');
                t.setAttribute('aria-selected', 'false');
                t.setAttribute('tabindex', '-1');
            });
            
            // Activate clicked tab
            trigger.classList.add('zActive');
            trigger.setAttribute('aria-selected', 'true');
            trigger.removeAttribute('tabindex');
            
            // Hide all panes in the content container
            if (tabContent) {
                const allPanes = tabContent.querySelectorAll('.zTab-pane');
                allPanes.forEach(pane => {
                    pane.classList.remove('zActive', 'zShow');
                });
            }
            
            // Show target pane
            const hasFade = targetPane.classList.contains('zFade');
            
            if (hasFade) {
                // For fade animation, add zActive first, then zShow after reflow
                targetPane.classList.add('zActive');
                requestAnimationFrame(() => {
                    targetPane.classList.add('zShow');
                });
            } else {
                // No animation, just show
                targetPane.classList.add('zActive');
            }
            
            // Fire custom event
            const event = new CustomEvent('zTabShown', { 
                detail: { 
                    trigger: trigger, 
                    pane: targetPane 
                }
            });
            trigger.dispatchEvent(event);
        }
        
        // Initialize all tab triggers
        tabTriggers.forEach(trigger => {
            // Set initial aria attributes
            if (trigger.classList.contains('zActive')) {
                trigger.setAttribute('aria-selected', 'true');
                trigger.setAttribute('role', 'tab');
            } else {
                trigger.setAttribute('aria-selected', 'false');
                trigger.setAttribute('role', 'tab');
                trigger.setAttribute('tabindex', '-1');
            }
            
            // Add click handler
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                showTab(trigger);
            });
            
            // Add keyboard navigation (left/right arrows)
            trigger.addEventListener('keydown', (e) => {
                const nav = trigger.closest('.zNav');
                if (!nav) return;
                
                const allTriggers = Array.from(nav.querySelectorAll('[data-bs-toggle="tab"]'));
                const currentIndex = allTriggers.indexOf(trigger);
                
                let nextIndex = currentIndex;
                
                if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    nextIndex = (currentIndex + 1) % allTriggers.length;
                } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                    e.preventDefault();
                    nextIndex = (currentIndex - 1 + allTriggers.length) % allTriggers.length;
                } else if (e.key === 'Home') {
                    e.preventDefault();
                    nextIndex = 0;
                } else if (e.key === 'End') {
                    e.preventDefault();
                    nextIndex = allTriggers.length - 1;
                }
                
                if (nextIndex !== currentIndex) {
                    allTriggers[nextIndex].focus();
                    showTab(allTriggers[nextIndex]);
                }
            });
        });
        
        console.log(`✅ zTheme: Initialized ${tabTriggers.length} tab(s)`);
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Initialize All Features
     * ═══════════════════════════════════════════════════════════
     * 
     * Runs when DOM is ready and initializes all zTheme features.
     * 
     * TODO: Add more interactive features as needed:
     * - Tooltips (.zTooltip)
     * - Alerts with close buttons (.zAlert)
     */
    function init() {
        console.log('🎨 zTheme: Initializing JavaScript utilities...');
        
        // Initialize form validation
        initValidation();
        
        // Initialize accordions
        initAccordion();
        
        // Initialize carousels
        initCarousel();
        
        // Initialize collapse
        initCollapse();
        
        // Initialize navbar dropdowns (mobile touch handling)
        initNavbarDropdowns();
        
        // Initialize dropdowns
        initDropdown();
        
        // Initialize list group tabs
        initListGroup();
        
        // Initialize modals
        initModal();
        
        // Initialize offcanvas
        initOffcanvas();
        
        // Initialize popovers
        initPopover();
        
        // Initialize scrollspy
        initScrollspy();
        
        // Initialize tabs
        initTabs();
        
        // Initialize toasts
        const toastAPI = initToast();
        if (toastAPI) {
            window.zTheme.toast = toastAPI;
        }
        
        // Initialize tooltips
        initTooltip();
        
        // TODO: Initialize other features here as they're added
        
        console.log('✅ zTheme: JavaScript initialization complete');
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Auto-Initialize on DOM Ready
     * ═══════════════════════════════════════════════════════════
     */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // DOM already loaded (script loaded late)
        init();
    }

    /**
     * ═══════════════════════════════════════════════════════════
     * Public API (Optional)
     * ═══════════════════════════════════════════════════════════
     * 
     * Expose methods for manual re-initialization if needed.
     * Useful for dynamically added forms or SPA scenarios.
     * 
     * TODO: When integrating with zBifrost, consider exporting
     * these as ES6 modules instead of global namespace.
     */
    window.zTheme = window.zTheme || {};
    window.zTheme.initValidation = initValidation;
    window.zTheme.initAccordion = initAccordion;
    window.zTheme.initTabs = initTabs;
    window.zTheme.initCarousel = initCarousel;
    window.zTheme.initCollapse = initCollapse;
    window.zTheme.initNavbarDropdowns = initNavbarDropdowns;
    window.zTheme.initDropdown = initDropdown;
    window.zTheme.initListGroup = initListGroup;
    window.zTheme.initModal = initModal;
    window.zTheme.initOffcanvas = initOffcanvas;
    window.zTheme.initPopover = initPopover;
    window.zTheme.initScrollspy = initScrollspy;
    window.zTheme.initToast = initToast;
    window.zTheme.initTooltip = initTooltip;
    window.zTheme.version = '1.0.0';

})();

