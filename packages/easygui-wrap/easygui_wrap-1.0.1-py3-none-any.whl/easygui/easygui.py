import dearpygui.dearpygui as dpg
import os

class EasyGUI:
    """
    EasyGUI — A beginner-friendly, stylish Python GUI wrapper using DearPyGui v2.x.
    Supports tags, callbacks with dynamic values, fullscreen viewport, and QOL helpers.
    """

    def __init__(self, title="EasyGUI", size=(600, 400), bg_color=[50,50,50],
                 fullscreen_window=False, font_path=None):
        self.title = title
        self.width, self.height = size
        self.bg_color = bg_color
        self.fullscreen_window = fullscreen_window
        self._fonts = {}
        self._tags = {}
        self._font_path = font_path or os.path.join(os.path.dirname(__file__), "Roboto-Regular.ttf")

        # Create DearPyGui context
        dpg.create_context()

        # Font registry
        with dpg.font_registry():
            self._default_font = dpg.add_font(self._font_path, 16)

        # Create main viewport
        dpg.create_viewport(title=self.title, width=self.width, height=self.height)
        if self.fullscreen_window:
            dpg.set_viewport_resize_callback(self._resize_viewport)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    # ==================== Font Helper ====================
    def _make_font(self, size):
        """Create or reuse a font of given size."""
        if size not in self._fonts:
            self._fonts[size] = dpg.add_font(self._font_path, size)
        return self._fonts[size]

    # ==================== Callback Wrapper ====================
    def _wrap_callback(self, callback, args_tags=None, args=None):
        args_tags = args_tags or []
        args = args or ()

        def wrapper():
            tag_values = [self.get_value(tag) for tag in args_tags]
            callback(*tag_values, *args)

        return wrapper

    # ==================== Widget Methods ====================
    def add_label(self, text, tag=None, fg=None, font_size=16):
        """Add a text label."""
        tag = tag or text
        lbl = dpg.add_text(default_value=text, tag=tag, color=fg or [255,255,255])
        dpg.bind_item_font(lbl, self._make_font(font_size))
        self._tags[tag] = lbl
        return lbl

    def add_entry(self, default_value="", tag=None, width=200):
        """Add a text input field."""
        tag = tag or f"entry_{len(self._tags)}"
        ent = dpg.add_input_text(default_value=default_value, tag=tag, width=width)
        self._tags[tag] = ent
        return ent

    def add_button(self, text, callback, args_tags=None, args=None, fg=None, bg=None, font_size=14, tag=None):
        """Add a button with dynamic/static args callback support."""
        tag = tag or f"btn_{len(self._tags)}"
        btn = dpg.add_button(label=text, tag=tag, callback=self._wrap_callback(callback, args_tags, args))
        if fg or bg:
            dpg.set_item_style_var(btn, dpg.mvStyleVar_FrameRounding, 5)
        dpg.bind_item_font(btn, self._make_font(font_size))
        self._tags[tag] = btn
        return btn

    def add_slider(self, label="", tag=None, min_value=0, max_value=100, default_value=0):
        """Add a slider widget."""
        tag = tag or f"slider_{len(self._tags)}"
        s = dpg.add_slider_int(label=label, tag=tag, min_value=min_value, max_value=max_value, default_value=default_value)
        self._tags[tag] = s
        return s

    def add_checkbox(self, label="", tag=None, default_value=False):
        """Add a checkbox widget."""
        tag = tag or f"chk_{len(self._tags)}"
        chk = dpg.add_checkbox(label=label, tag=tag, default_value=default_value)
        self._tags[tag] = chk
        return chk

    # ==================== Value Helpers ====================
    def get_value(self, tag):
        """Get the current value of a widget by tag."""
        return dpg.get_value(tag)

    def set_value(self, tag, value):
        """Set the value of a widget by tag."""
        dpg.set_value(tag, value)

    # ==================== Fullscreen / Resize ====================
    def toggle_fullscreen(self, state=None):
        """Enable/disable fullscreen viewport mode."""
        if state is None:
            state = not self.fullscreen_window
        self.fullscreen_window = state
        if state:
            dpg.set_viewport_width(dpg.get_viewport_client_width())
            dpg.set_viewport_height(dpg.get_viewport_client_height())
        else:
            dpg.set_viewport_width(self.width)
            dpg.set_viewport_height(self.height)

    def _resize_viewport(self, sender, app_data):
        """Auto-resize viewport if fullscreen mode is active."""
        if self.fullscreen_window:
            dpg.set_viewport_width(dpg.get_viewport_client_width())
            dpg.set_viewport_height(dpg.get_viewport_client_height())

    # ==================== Show GUI ====================
    def show(self):
        """Start the GUI main loop."""
        dpg.start_dearpygui()
        dpg.destroy_context()
