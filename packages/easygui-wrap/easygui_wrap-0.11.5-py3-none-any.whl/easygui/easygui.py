"""
EasyGUI — a ridiculously simplified wrapper around Dear PyGui or Tkinter.

Features:
- Simple widget creation (labels, buttons, entries)
- Callback argument passing (normal + tag-based)
- Simple theming & colors
- Auto-resizing fullscreen window mode
- QOL helpers for getting/setting widget values
- Works purely on DearPyGui backend for now
"""

import dearpygui.dearpygui as dpg

class EasyGUI:
    def __init__(
        self,
        title: str = "EasyGUI App",
        size=(600, 400),
        bg_color=None,
        fullscreen_window=False,
        decorated=True,
    ):
        """Create an EasyGUI application window."""
        dpg.create_context()
        dpg.create_viewport(title=title, width=size[0], height=size[1])
        dpg.setup_dearpygui()

        self.elements = {}
        self.bg_color = bg_color
        self.fullscreen = fullscreen_window

        # Create main GUI window inside viewport
        self.main_window_tag = "main_window"
        with dpg.window(
            tag=self.main_window_tag,
            no_title_bar=self.fullscreen,
            no_move=self.fullscreen,
            no_resize=self.fullscreen,
        ):
            pass

        if self.bg_color:
            with dpg.theme() as bg_theme:
                with dpg.theme_component(dpg.mvAll):
                    dpg.add_theme_color(dpg.mvThemeCol_WindowBg, self._parse_color(self.bg_color))
            dpg.bind_theme(bg_theme)

        # Handle fullscreen behavior
        if self.fullscreen:
            dpg.set_viewport_resize_callback(self._resize_window)
            dpg.configure_item(self.main_window_tag, width=size[0], height=size[1])
            dpg.configure_viewport("main_viewport", decorated=decorated)

        dpg.show_viewport()

    # ====== CORE METHODS ======

    def show(self):
        """Run the app."""
        dpg.set_primary_window(self.main_window_tag, True)
        dpg.start_dearpygui()
        dpg.destroy_context()

    def _resize_window(self, sender, app_data):
        """Match window size to viewport."""
        if not self.fullscreen:
            return
        width, height = app_data
        dpg.configure_item(self.main_window_tag, width=width, height=height)

    # ====== ELEMENT CREATION ======

    def add_label(self, text, tag=None, fg=None, font_size=None):
        """Add a label (text) to the GUI."""
        tag = tag or f"label_{len(self.elements)}"
        lbl = dpg.add_text(text, tag=tag, parent=self.main_window_tag)
        if fg:
            dpg.configure_item(tag, color=self._parse_color(fg))
        if font_size:
            dpg.bind_item_font(tag, self._make_font(font_size))
        self.elements[tag] = lbl
        return tag

    def add_entry(self, label="", tag=None, default_value=""):
        """Add an input text box."""
        tag = tag or f"entry_{len(self.elements)}"
        entry = dpg.add_input_text(label=label, default_value=default_value, tag=tag, parent=self.main_window_tag)
        self.elements[tag] = entry
        return tag

    def add_button(
        self,
        text,
        callback=None,
        args=(),
        args_tags=(),
        fg=None,
        bg=None,
        font_size=None,
        tag=None,
    ):
        """Add a button with a callback and easy argument handling."""
        tag = tag or f"button_{len(self.elements)}"

        def wrapped_callback():
            call_args = []
            # collect values from tagged elements
            for t in args_tags:
                if t in self.elements:
                    call_args.append(dpg.get_value(self.elements[t]))
            # add normal args
            if args:
                call_args.extend(args)
            if callback:
                try:
                    callback(*call_args)
                except TypeError:
                    callback()

        btn = dpg.add_button(label=text, tag=tag, parent=self.main_window_tag, callback=wrapped_callback)
        if fg or bg:
            dpg.bind_item_theme(tag, self._make_theme(fg, bg))
        if font_size:
            dpg.bind_item_font(tag, self._make_font(font_size))
        self.elements[tag] = btn
        return tag

    def add_slider(self, label="", tag=None, min_value=0, max_value=100, default_value=0):
        """Add a slider (int)."""
        tag = tag or f"slider_{len(self.elements)}"
        slider = dpg.add_slider_int(
            label=label,
            tag=tag,
            default_value=default_value,
            min_value=min_value,
            max_value=max_value,
            parent=self.main_window_tag,
        )
        self.elements[tag] = slider
        return tag

    def add_checkbox(self, label="", tag=None, default_value=False):
        """Add a checkbox."""
        tag = tag or f"checkbox_{len(self.elements)}"
        cb = dpg.add_checkbox(label=label, default_value=default_value, tag=tag, parent=self.main_window_tag)
        self.elements[tag] = cb
        return tag

    # ====== VALUE CONTROL ======

    def get_value(self, tag):
        """Get value of a tagged element."""
        if tag in self.elements:
            return dpg.get_value(self.elements[tag])
        return None

    def set_value(self, tag, value):
        """Set value of a tagged element."""
        if tag in self.elements:
            dpg.set_value(self.elements[tag], value)

    # ====== THEMING & UTILS ======

    def _parse_color(self, color):
        """Convert color name or list to RGBA."""
        if isinstance(color, str):
            import webcolors
            try:
                rgb = webcolors.name_to_rgb(color)
                return [rgb.red, rgb.green, rgb.blue, 255]
            except ValueError:
                return [255, 255, 255, 255]
        elif isinstance(color, (list, tuple)) and len(color) in (3, 4):
            if len(color) == 3:
                return list(color) + [255]
            return list(color)
        return [255, 255, 255, 255]

    def _make_theme(self, fg=None, bg=None):
        """Generate theme for buttons/labels."""
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                if bg:
                    dpg.add_theme_color(dpg.mvThemeCol_Button, self._parse_color(bg))
                if fg:
                    dpg.add_theme_color(dpg.mvThemeCol_Text, self._parse_color(fg))
            with dpg.theme_component(dpg.mvAll):
                if fg:
                    dpg.add_theme_color(dpg.mvThemeCol_Text, self._parse_color(fg))
        return theme

    def _make_font(self, size):
        """Create simple font of given size."""
        with dpg.font_registry():
            with dpg.font(dpg.get_system_font_name(), size):
                return dpg.last_item()
        return None

    # ====== ADVANCED FEATURES ======

    def toggle_fullscreen(self, state=None):
        """Toggle fullscreen dynamically."""
        if state is None:
            state = not self.fullscreen
        self.fullscreen = state
        dpg.configure_viewport("main_viewport", decorated=not state)
        if state:
            self._resize_window(None, dpg.get_viewport_client_width(), dpg.get_viewport_client_height())
