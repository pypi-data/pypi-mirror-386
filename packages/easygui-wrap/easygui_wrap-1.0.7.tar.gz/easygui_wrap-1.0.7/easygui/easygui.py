# easygui.py
import dearpygui.dearpygui as dpg
import webcolors


class EasyGUI:
    def __init__(self, title="EasyGUI App", size=(800, 600), bg_color="gray",
                 decorated=True, viewport_decorated=True):
        """
        EasyGUI constructor.
        :param title: Window title
        :param size: Tuple (width, height)
        :param bg_color: Background color (name or RGB)
        :param decorated: Whether the window has a title bar
        :param viewport_decorated: Whether the OS viewport has decorations
        """
        dpg.create_context()
        self.title = title
        self.size = size
        self.bg_color = self._parse_color(bg_color)
        self.decorated = decorated
        self.viewport_decorated = viewport_decorated
        self.widgets = {}

        # Create viewport
        dpg.create_viewport(title=title, width=size[0], height=size[1])
        dpg.setup_dearpygui()
        dpg.set_viewport_decorated(self.viewport_decorated)
        dpg.set_viewport_clear_color(self.bg_color)

        # Main window
        with dpg.window(label=title, width=size[0], height=size[1],
                        no_title_bar=not self.decorated, tag="__main_window__") as self.main_window:
            pass

        # Dynamic resizing
        dpg.set_viewport_resize_callback(self._resize_to_viewport)

    # --------------------
    # Internal helpers
    # --------------------
    def _resize_to_viewport(self, sender, app_data):
        w, h = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
        dpg.set_item_width(self.main_window, w)
        dpg.set_item_height(self.main_window, h)

    def _parse_color(self, color):
        if isinstance(color, str):
            try:
                rgb = webcolors.name_to_rgb(color)
                return [rgb.red / 255, rgb.green / 255, rgb.blue / 255, 1.0]
            except ValueError:
                return [0.5, 0.5, 0.5, 1.0]
        elif isinstance(color, (tuple, list)) and len(color) in [3, 4]:
            if len(color) == 3:
                return [color[0]/255, color[1]/255, color[2]/255, 1.0]
            return [color[0]/255, color[1]/255, color[2]/255, color[3]]
        return [0.5, 0.5, 0.5, 1.0]

    def _safe_font(self, font_size):
        """Generate a safe font."""
        with dpg.font_registry():
            try:
                # You can replace this path with a bundled font if you want
                font = dpg.add_font("resources/NotoSans-Regular.ttf", font_size)
                return font
            except Exception:
                return None

    def _make_color_theme(self, color):
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvText):
                dpg.add_theme_color(dpg.mvThemeCol_Text, color)
        return theme

    def _make_button_theme(self, fg, bg):
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, bg)
                dpg.add_theme_color(dpg.mvThemeCol_Text, fg)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, bg)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, bg)
        return theme

    # --------------------
    # Core widgets
    # --------------------
    def add_label(self, text, tag=None, fg="white", font_size=None):
        color = self._parse_color(fg)
        with dpg.group(parent=self.main_window):
            lbl = dpg.add_text(text, tag=tag or text)
            if font_size:
                font = self._safe_font(font_size)
                if font:
                    dpg.bind_item_font(lbl, font)
            dpg.bind_item_theme(lbl, self._make_color_theme(color))
        self.widgets[tag or text] = lbl
        return lbl

    def add_entry(self, label="", default_value="", tag=None, width=200):
        with dpg.group(parent=self.main_window):
            ent = dpg.add_input_text(label=label, default_value=default_value,
                                     width=width, tag=tag)
        self.widgets[tag or label] = ent
        return ent

    def add_button(self, text, callback=None, args=None, args_tags=None,
                   fg="white", bg="gray", font_size=None, tag=None):
        color_fg = self._parse_color(fg)
        color_bg = self._parse_color(bg)

        def _wrapped_callback(sender, app_data):
            cb_args = []
            if args:
                cb_args.extend(args if isinstance(args, (list, tuple)) else [args])
            if args_tags:
                for t in args_tags:
                    cb_args.append(dpg.get_value(self.widgets[t]))
            if callback:
                callback(*cb_args)

        with dpg.group(parent=self.main_window):
            btn = dpg.add_button(label=text, callback=_wrapped_callback, tag=tag)
            if font_size:
                font = self._safe_font(font_size)
                if font:
                    dpg.bind_item_font(btn, font)
            dpg.bind_item_theme(btn, self._make_button_theme(color_fg, color_bg))
        self.widgets[tag or text] = btn
        return btn

    # --------------------
    # Accessors
    # --------------------
    def get(self, tag):
        return dpg.get_value(self.widgets[tag])

    def set(self, tag, value):
        dpg.set_value(self.widgets[tag], value)

    # --------------------
    # Direct DPG access
    # --------------------
    @property
    def dpg_module(self):
        """Access the underlying DearPyGui module."""
        return dpg

    @property
    def main_window_tag(self):
        """Get the main window tag for direct DPG parenting."""
        return self.main_window

    def register_widget(self, tag, dpg_id):
        """Register a manually created DPG widget into EasyGUI tracking."""
        self.widgets[tag] = dpg_id

    # --------------------
    # Run GUI
    # --------------------
    def show(self):
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
