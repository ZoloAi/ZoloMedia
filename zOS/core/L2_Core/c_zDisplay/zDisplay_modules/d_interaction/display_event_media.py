# zCLI/subsystems/zDisplay/zDisplay_modules/events/display_event_media.py

"""
MediaEvents - Media Display Event Package for zDisplay
=====================================================

This event package provides structured media display (images) with
comprehensive formatting options, building on the BasicOutputs foundation.

Composition Architecture
------------------------
MediaEvents builds on BasicOutputs:

Layer 3: display_delegates.py (PRIMARY API)
    ↓
Layer 2: display_events.py (ORCHESTRATOR)
    ↓
Layer 2: events/display_event_media.py (MediaEvents) ← THIS MODULE
    ↓
Layer 2: events/display_event_outputs.py (BasicOutputs) ← FOUNDATION
    ↓
Layer 1: display_primitives.py (FOUNDATION I/O)

Composition Flow:
1. MediaEvents.image() method called
2. If GUI mode (Bifrost):
   a. Send clean JSON event with essential image data (src, alt_text, caption)
   b. Returns immediately (GUI handles async)
3. If terminal mode:
   a. Format image metadata (path, alt text, caption)
   b. Apply styling (indentation, color)
   c. Display via BasicOutputs.text() for consistent I/O
   d. Display button with action="#" (placeholder for future zOpen integration)
4. Return control to caller

Dual-Mode I/O Pattern
----------------------
All methods implement the same dual-mode pattern:

1. **GUI Mode (Bifrost):** Try send_gui_event() first
   - Send clean JSON event with data (src, alt_text, caption)
   - Returns immediately (GUI handles async)
   - GUI frontend will display data

2. **Terminal Mode (Fallback):** Format and display locally
   - Format image metadata (path, alt, caption)
   - Apply styling (indentation, colors)
   - Display via BasicOutputs.text() for consistent I/O
   - Show button with action="#" as placeholder

Terminal-First Philosophy
--------------------------
In terminal mode, images display as:
- 📷 Icon + alt text header
- Path display
- Caption (if provided)
- Button with action="#" (if open_prompt=True)

This ensures terminal users get full metadata even if they can't view the image inline.
"""

from zOS import Any, Dict, Optional

# Import constants from centralized module
from ..display_constants import (
    _EVENT_IMAGE,
    _EVENT_VIDEO,
    _EVENT_AUDIO,
    _EVENT_PICTURE,
    _DEFAULT_IMAGE_ICON,
    _DEFAULT_VIDEO_ICON,
    _DEFAULT_AUDIO_ICON,
    _DEFAULT_PICTURE_ICON,
)

class MediaEvents:
    """Event package for displaying media (e.g., images)."""

    display: Any  # Parent zDisplay instance
    zPrimitives: Any  # Primitives instance for I/O operations
    zColors: Any  # Colors instance for terminal styling
    BasicOutputs: Any # BasicOutputs instance for consistent text output
    BasicInputs: Any # BasicInputs instance for button logic

    def __init__(self, display_instance: Any) -> None:
        """Initialize MediaEvents with parent display reference.

        Args:
            display_instance: Parent zDisplay instance providing primitives and colors.
        """
        self.display = display_instance
        self.zPrimitives = display_instance.zPrimitives
        self.zColors = display_instance.zColors
        self.logger = display_instance.logger # Access logger from display instance

    def image(
        self,
        src: str,
        alt_text: str = "",
        caption: str = "",
        open_prompt: bool = True,
        indent: int = 0,
        color: Optional[str] = None,
        _context: Optional[dict] = None,  # NEW v1.5.12: Context for %data.* resolution
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Display an image event.

        In Bifrost mode, sends a clean event with src, alt_text, and caption.
        In Terminal mode, displays formatted text with path, alt_text, caption,
        and a button with action="#" (placeholder for future zOpen integration).

        Args:
            src: The source URL or path of the image.
            alt_text: Alternative text for the image (accessibility).
            caption: An optional caption for the image.
            open_prompt: If True (default), displays a button in terminal mode (with action="#").
                        Set to False to disable the prompt.
            indent: Indentation level for terminal output.
            color: Color for terminal output text.
            **kwargs: Additional parameters to pass through to the event.

        Returns:
            Optional[Dict[str, Any]]: The event dictionary if sent to GUI,
                                     or None for terminal mode.
        """
        if not src:
            self.logger.error("[MediaEvents] image() requires 'src' parameter")
            return None

        # NEW: Resolve %variable references in src, alt_text, and caption (v1.5.12)
        if "%" in src:
            from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_variables
            src = resolve_variables(src, self.display.zcli, _context)
        
        if "%" in alt_text:
            from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_variables
            alt_text = resolve_variables(alt_text, self.display.zcli, _context)
        
        if "%" in caption:
            from zOS.L2_Core.g_zParser.parser_modules.parser_functions import resolve_variables
            caption = resolve_variables(caption, self.display.zcli, _context)

        # NEW: Resolve zPath references in src (v1.5.15: @ and ~ workspace/home paths)
        # The beauty of zPath: declarative approach that resolves based on execution context
        if src.startswith(("@", "~")):
            from pathlib import Path
            
            # Step 1: Resolve zPath to absolute filesystem path
            resolved_path = self.display.zcli.zparser.resolve_data_path(src)
            self.logger.debug(f"[MediaEvents] Resolved zPath: {src} → {resolved_path}")
            
            # Step 2: Convert based on execution mode
            if self.display.mode == "zBifrost":
                # Bifrost mode: Convert to web-relative URL for zServer
                zserver = getattr(self.display.zcli, 'server', None)
                if zserver:
                    serve_path = Path(zserver.serve_path).resolve()
                    resolved_path_obj = Path(resolved_path)
                    
                    try:
                        if resolved_path_obj.is_relative_to(serve_path):
                            # Convert to URL path relative to serve_path
                            rel_path = resolved_path_obj.relative_to(serve_path)
                            src = "/" + str(rel_path).replace("\\", "/")
                            self.logger.debug(f"[MediaEvents] Bifrost mode - web path: {src}")
                        else:
                            # Path is outside serve_path - keep as absolute for fallback
                            src = str(resolved_path_obj)
                            self.logger.warning(f"[MediaEvents] Path outside serve_path: {src}")
                    except (ValueError, AttributeError) as e:
                        # Fallback to absolute path
                        src = str(resolved_path_obj)
                        self.logger.warning(f"[MediaEvents] Error converting path: {e}")
                else:
                    # No zServer - keep absolute path (shouldn't happen in Bifrost mode)
                    src = resolved_path
                    self.logger.warning(f"[MediaEvents] Bifrost mode but no zServer: {src}")
            else:
                # Terminal mode: Use absolute filesystem path for local file access
                src = resolved_path
                self.logger.debug(f"[MediaEvents] Terminal mode - absolute path: {src}")

        # Base event for both modes (after variable and zPath resolution)
        base_event = {
            "src": src,
            "alt_text": alt_text,
            "caption": caption,
            **kwargs
        }

        if self.display.mode == "zBifrost":
            # Bifrost gets clean image data
            return self.zPrimitives.send_gui_event(_EVENT_IMAGE, base_event)
        else:
            # Terminal mode: format and display locally
            indent_str = "  " * indent
            display_color = color if color else self.display.mycolor

            # Display icon + alt text header
            header = f"{indent_str}{_DEFAULT_IMAGE_ICON} {alt_text}" if alt_text else f"{indent_str}{_DEFAULT_IMAGE_ICON} Image"
            self.BasicOutputs.text(header, indent=0, color=display_color, break_after=False)

            # Display path
            path_line = f"{indent_str}   Path: {src}"
            self.BasicOutputs.text(path_line, indent=0, color="muted", break_after=False)

            # Display caption (if provided)
            if caption:
                caption_line = f"{indent_str}   Caption: {caption}"
                self.BasicOutputs.text(caption_line, indent=0, color="muted", break_after=False)

            # Display button (if open_prompt enabled)
            if open_prompt:
                # Add spacing before button
                self.zPrimitives.write_line("")
                
                # Direct prompt (NOT using button event to avoid conflict with UI placeholder buttons)
                # Use centralized color mapping (INFO = cyan for informational prompts)
                prompt_color = self.zColors.get_semantic_color('INFO')
                prompt_text = f"{prompt_color}Click [Open image file]? (y/n): {self.zColors.RESET}"
                response = self.zPrimitives.read_string(prompt_text).strip().lower()
                
                confirmed = response in ('y', 'yes')
                if confirmed:
                    # Phase 3: Call zOpen.open_image(src)
                    self.logger.info(f"[MediaEvents] User confirmed open for: {src}")
                    result = self.display.zcli.open.open_image(src)
                    if result == "zBack":
                        self.logger.info(f"[MediaEvents] Successfully opened image: {src}")
                    else:
                        self.logger.warning(f"[MediaEvents] Failed to open image: {src}")
                else:
                    self.BasicOutputs.text("  Open image file cancelled.", indent=0, break_after=False)
            else:
                # Add break after last line if no open prompt
                self.zPrimitives.write_line("")

            return None

    def video(
        self,
        src: str,
        alt_text: str = "",
        caption: str = "",
        open_prompt: bool = True,
        indent: int = 0,
        color: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Display a video event.

        In Bifrost mode, sends a clean event with src, alt_text, and caption.
        In Terminal mode, displays formatted text with path, alt_text, caption,
        and a button (calls zOpen.open_video()).

        Args:
            src: The source URL or path of the video.
            alt_text: Alternative text for the video (accessibility).
            caption: An optional caption for the video.
            open_prompt: If True (default), displays a button in terminal mode.
                        Set to False to disable the prompt.
            indent: Indentation level for terminal output.
            color: Color for terminal output text.
            **kwargs: Additional parameters to pass through to the event.

        Returns:
            Optional[Dict[str, Any]]: The event dictionary if sent to GUI,
                                     or None for terminal mode.
        """
        if not src:
            self.logger.error("[MediaEvents] video() requires 'src' parameter")
            return None

        # Base event for both modes
        base_event = {
            "type": _EVENT_VIDEO,
            "src": src,
            "alt_text": alt_text,
            "caption": caption,
            **kwargs
        }

        if self.display.mode == "zBifrost":
            # Bifrost gets clean video data
            return self.zPrimitives.send_gui_event(base_event)
        else:
            # Terminal mode: format and display locally
            indent_str = "  " * indent
            display_color = color if color else self.display.mycolor

            # Display icon + alt text header
            header = f"{indent_str}{_DEFAULT_VIDEO_ICON} {alt_text}" if alt_text else f"{indent_str}{_DEFAULT_VIDEO_ICON} Video"
            self.BasicOutputs.text(header, indent=0, color=display_color, break_after=False)

            # Display path
            path_line = f"{indent_str}   Path: {src}"
            self.BasicOutputs.text(path_line, indent=0, color="muted", break_after=False)

            # Display caption (if provided)
            if caption:
                caption_line = f"{indent_str}   Caption: {caption}"
                self.BasicOutputs.text(caption_line, indent=0, color="muted", break_after=False)

            # Display button (if open_prompt enabled)
            if open_prompt:
                # Add spacing before button
                self.zPrimitives.write_line("")
                # Use built-in button logic
                confirmed = self.BasicInputs.button("Play video", action="#", color="info")
                if confirmed:
                    # Call zOpen.open_video(src)
                    self.logger.info(f"[MediaEvents] User confirmed play for: {src}")
                    result = self.display.zcli.open.open_video(src)
                    if result == "zBack":
                        self.logger.info(f"[MediaEvents] Successfully opened video: {src}")
                    else:
                        self.logger.warning(f"[MediaEvents] Failed to open video: {src}")
            else:
                # Add break after last line if no button
                self.zPrimitives.write_line("")

            return None

    def audio(
        self,
        src: str,
        alt_text: str = "",
        caption: str = "",
        open_prompt: bool = True,
        indent: int = 0,
        color: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Display an audio event.

        In Bifrost mode, sends a clean event with src, alt_text, and caption.
        In Terminal mode, displays formatted text with path, alt_text, caption,
        and a button (calls zOpen.open_audio()).

        Args:
            src: The source URL or path of the audio file.
            alt_text: Alternative text for the audio (accessibility).
            caption: An optional caption for the audio.
            open_prompt: If True (default), displays a button in terminal mode.
                        Set to False to disable the prompt.
            indent: Indentation level for terminal output.
            color: Color for terminal output text.
            **kwargs: Additional parameters to pass through to the event.

        Returns:
            Optional[Dict[str, Any]]: The event dictionary if sent to GUI,
                                     or None for terminal mode.
        """
        if not src:
            self.logger.error("[MediaEvents] audio() requires 'src' parameter")
            return None

        # Base event for both modes
        base_event = {
            "type": _EVENT_AUDIO,
            "src": src,
            "alt_text": alt_text,
            "caption": caption,
            **kwargs
        }

        if self.display.mode == "zBifrost":
            # Bifrost gets clean audio data
            return self.zPrimitives.send_gui_event(base_event)
        else:
            # Terminal mode: format and display locally
            indent_str = "  " * indent
            display_color = color if color else self.display.mycolor

            # Display icon + alt text header
            header = f"{indent_str}{_DEFAULT_AUDIO_ICON} {alt_text}" if alt_text else f"{indent_str}{_DEFAULT_AUDIO_ICON} Audio"
            self.BasicOutputs.text(header, indent=0, color=display_color, break_after=False)

            # Display path
            path_line = f"{indent_str}   Path: {src}"
            self.BasicOutputs.text(path_line, indent=0, color="muted", break_after=False)

            # Display caption (if provided)
            if caption:
                caption_line = f"{indent_str}   Caption: {caption}"
                self.BasicOutputs.text(caption_line, indent=0, color="muted", break_after=False)

            # Display button (if open_prompt enabled)
            if open_prompt:
                # Add spacing before button
                self.zPrimitives.write_line("")
                # Use built-in button logic
                confirmed = self.BasicInputs.button("Play audio", action="#", color="info")
                if confirmed:
                    # Call zOpen.open_audio(src)
                    self.logger.info(f"[MediaEvents] User confirmed play for: {src}")
                    result = self.display.zcli.open.open_audio(src)
                    if result == "zBack":
                        self.logger.info(f"[MediaEvents] Successfully opened audio: {src}")
                    else:
                        self.logger.warning(f"[MediaEvents] Failed to open audio: {src}")
            else:
                # Add break after last line if no button
                self.zPrimitives.write_line("")

            return None

    def picture(
        self,
        sources: list,
        fallback: str,
        alt_text: str = "",
        caption: str = "",
        open_prompt: bool = True,
        indent: int = 0,
        color: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Display a picture element (responsive image with source selection).

        In Bifrost mode, sends a clean event with sources, fallback, alt_text, and caption.
        In Terminal mode, displays formatted list of sources with interactive selection.

        Args:
            sources: List of source dicts with 'srcset' and 'media' keys
                    e.g., [{"srcset": "large.jpg", "media": "(min-width: 1024px)"}]
            fallback: Fallback image path (required, used as default)
            alt_text: Alternative text for the picture (accessibility).
            caption: An optional caption for the picture.
            open_prompt: If True (default), displays interactive selection in terminal mode.
                        Set to False to disable the prompt.
            indent: Indentation level for terminal output.
            color: Color for terminal output text.
            **kwargs: Additional parameters to pass through to the event.

        Returns:
            Optional[Dict[str, Any]]: The event dictionary if sent to GUI,
                                     or None for terminal mode.
                                     
        Terminal Interaction:
            User can:
            - Enter number (1-N) + Enter: Opens that source
            - Just Enter: Opens fallback (default)
            - 'done' + Enter: Skips, no open
        """
        if not sources and not fallback:
            self.logger.error("[MediaEvents] picture() requires 'sources' or 'fallback' parameter")
            return None

        # Base event for both modes
        base_event = {
            "type": _EVENT_PICTURE,
            "sources": sources,
            "fallback": fallback,
            "alt_text": alt_text,
            "caption": caption,
            **kwargs
        }

        if self.display.mode == "zBifrost":
            # Bifrost gets clean picture data with all sources
            return self.zPrimitives.send_gui_event(base_event)
        else:
            # Terminal mode: format and display with interactive selection
            indent_str = "  " * indent
            display_color = color if color else self.display.mycolor

            # Display icon + alt text header with "Responsive Image" indicator
            header = f"{indent_str}{_DEFAULT_PICTURE_ICON} {alt_text} (Responsive Image)" if alt_text else f"{indent_str}{_DEFAULT_PICTURE_ICON} Responsive Image"
            self.BasicOutputs.text(header, indent=0, color=display_color, break_after=False)

            # Build complete list of all sources including fallback
            all_sources = list(sources) if sources else []
            
            # Display numbered sources
            self.BasicOutputs.text(f"{indent_str}   Sources:", indent=0, color="muted", break_after=False)
            for idx, src in enumerate(all_sources, 1):
                media = src.get('media', 'default')
                srcset = src.get('srcset')
                self.BasicOutputs.text(
                    f"{indent_str}   {idx}. {media}: {srcset}",
                    indent=0,
                    color="muted",
                    break_after=False
                )
            
            # Display fallback as the default option (last in list)
            fallback_idx = len(all_sources) + 1
            self.BasicOutputs.text(
                f"{indent_str}   {fallback_idx}. Fallback: {fallback} [default]",
                indent=0,
                color="muted",
                break_after=False
            )

            # Display caption (if provided)
            if caption:
                caption_line = f"{indent_str}   Caption: {caption}"
                self.BasicOutputs.text(caption_line, indent=0, color="muted", break_after=False)

            # Interactive selection
            if open_prompt:
                # Add spacing before prompt
                self.zPrimitives.write_line("")
                
                # Custom input prompt
                prompt = f"Select source (1-{fallback_idx}, Enter=fallback, 'done'=skip): "
                
                try:
                    # Use read_string primitive directly (like button does)
                    choice = self.zPrimitives.read_string(prompt).strip().lower()
                    
                    # Parse and handle input
                    selected_src = None
                    
                    if choice == 'done':
                        # User chose to skip
                        self.logger.info("[MediaEvents] User skipped picture")
                        return None
                    elif choice == '':
                        # Default to fallback
                        selected_src = fallback
                        self.logger.info(f"[MediaEvents] User selected fallback (default): {fallback}")
                    elif choice.isdigit():
                        # User selected a specific source
                        idx = int(choice) - 1
                        if 0 <= idx < len(all_sources):
                            # Selected a source from the list
                            selected_src = all_sources[idx].get('srcset')
                            media = all_sources[idx].get('media', 'unknown')
                            self.logger.info(f"[MediaEvents] User selected {media}: {selected_src}")
                        elif idx == len(all_sources):
                            # Selected fallback explicitly
                            selected_src = fallback
                            self.logger.info(f"[MediaEvents] User selected fallback: {fallback}")
                        else:
                            # Invalid index
                            self.logger.warning(f"[MediaEvents] Invalid choice: {choice} (out of range)")
                            self.BasicOutputs.text(
                                f"{indent_str}   Invalid choice. Please enter 1-{fallback_idx}.",
                                indent=0,
                                color="warning",
                                break_after=False
                            )
                            return None
                    else:
                        # Invalid input
                        self.logger.warning(f"[MediaEvents] Invalid input: {choice}")
                        self.BasicOutputs.text(
                            f"{indent_str}   Invalid input. Please enter a number, press Enter, or type 'done'.",
                            indent=0,
                            color="warning",
                            break_after=False
                        )
                        return None
                    
                    # Open selected source
                    if selected_src:
                        result = self.display.zcli.open.open_image(selected_src)
                        if result == "zBack":
                            self.logger.info(f"[MediaEvents] Successfully opened: {selected_src}")
                        else:
                            self.logger.warning(f"[MediaEvents] Failed to open: {selected_src}")
                
                except KeyboardInterrupt:
                    # User cancelled
                    self.logger.info("[MediaEvents] User cancelled picture selection")
                    return None
            else:
                # Add break after last line if no prompt
                self.zPrimitives.write_line("")

            return None

