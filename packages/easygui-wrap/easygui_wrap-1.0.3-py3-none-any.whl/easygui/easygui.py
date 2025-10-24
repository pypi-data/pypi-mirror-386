import dearpygui.dearpygui as dpg

class EasyGUI:
    """
    EasyGUI — Beginner-friendly, stylish Python GUI wrapper using DearPyGui v2.x.
    Features:
      - Tag-based widgets
      - Buttons, sliders, checkboxes, labels, entries
      - Callbacks with static args or dynamic args_tags
      - Fullscreen viewport toggle
      - QOL helpers: get_value(tag) / set_value(tag, value)
    """

    def __init__(self, title="EasyGUI", size=(600, 400), bg_color=[50,50,50],
                 fullscreen_window=False):
        self.title = title
        self.width, self.height = size
        self.bg_color = bg_color
        self.fullscreen_window = fullscreen_window
        self._tags = {}

        # Create DearPyGui context
        dpg.create_context()

        # Create viewport
        dpg.create_viewport(title=self.title, width=self.width, height=self.height)

        # Main window container for all widgets
        self._main_window = dpg.add_window(label=self.title)

        if self.fullscreen_window:
            dpg.set_viewport_resize_callback(self._resize_viewport)
        dpg.setup_dearpygui()
        dpg.show_viewport()

    # ==================== Callback Wrapper ====================
    def _wrap_callback(self, callback, args_tags=None, args=None):
        args_tags = args_tags or []
        args = args or ()

        def wrapper():
            tag_values = [self.get_value(tag) for tag in args_tags]
            callback(*tag_values, *args)

        return wrapper

    # ==================== Widget Methods ====================
    def add_label(self, text, tag=None, fg=None):
        """Add a text label."""
        tag = tag or text
        lbl = dpg.add_text(default_value=text, tag=tag, color=fg or [255,255,255], parent=self._main_window)
        self._tags[tag] = lbl
        return lbl

    def add_entry(self, default_value="", tag=None, width=200):
        """Add a text input field."""
        tag = tag or f"entry_{len(self._tags)}"
        ent = dpg.add_input_text(default_value=default_value, tag=tag, width=width, parent=self._main_window)
        self._tags[tag] = ent
        return ent

    def add_button(self, text, callback, args_tags=None, args=None, fg=None, bg=None, tag=None):
        """Add a button with dynamic/static args callback support."""
        tag = tag or f"btn_{len(self._tags)}"
        btn = dpg.add_button(label=text, tag=tag,
                             callback=self._wrap_callback(callback, args_tags, args),
                             parent=self._main_window)
        if fg or bg:
            dpg.set_item_style_var(btn, dpg.mvStyleVar_FrameRounding, 5)
        self._tags[tag] = btn
        return btn

    def add_slider(self, label="", tag=None, min_value=0, max_value=100, default_value=0):
        """Add a slider widget."""
        tag = tag or f"slider_{len(self._tags)}"
        s = dpg.add_slider_int(label=label, tag=tag, min_value=min_value, max_value=max_value,
                               default_value=default_value, parent=self._main_window)
        self._tags[tag] = s
        return s

    def add_checkbox(self, label="", tag=None, default_value=False):
        """Add a checkbox widget."""
        tag = tag or f"chk_{len(self._tags)}"
        chk = dpg.add_checkbox(label=label, tag=tag, default_value=default_value, parent=self._main_window)
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

