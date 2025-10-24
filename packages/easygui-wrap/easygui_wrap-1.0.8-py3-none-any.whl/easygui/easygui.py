import dearpygui.dearpygui as dpg

class EasyGUI:
    def __init__(self, title="EasyGUI App", size=(800,600), bg_color="gray", decorated=True, viewport_decorated=True):
        self.main_window_tag = dpg.generate_uuid()
        self.dpg_module = dpg
        self._fullscreen_target = None
        self._fullscreen_handler = None

        dpg.create_context()
        dpg.create_viewport(title=title, width=size[0], height=size[1], decorated=viewport_decorated)

        with dpg.window(tag=self.main_window_tag, label=title, width=size[0], height=size[1], no_title_bar=not decorated) as main_win:
            self.main_window_tag = main_win

        dpg.setup_dearpygui()

    # --- Widget methods ---
    def add_label(self, text, tag=None, fg="white", font_size=None):
        tag = tag or dpg.generate_uuid()
        lbl = dpg.add_text(text, color=fg, tag=tag, parent=self.main_window_tag)
        return lbl

    def add_entry(self, label="", default_value="", tag=None, width=200):
        tag = tag or dpg.generate_uuid()
        ent = dpg.add_input_text(label=label, default_value=default_value, tag=tag, width=width, parent=self.main_window_tag)
        return ent

    def add_button(self, text, callback=None, args=None, args_tags=None, fg="white", bg="gray", font_size=None, tag=None):
        tag = tag or dpg.generate_uuid()

        def wrapped_callback():
            call_args = args or []
            if args_tags:
                for t in args_tags:
                    call_args.append(self.get(t))
            if callback:
                callback(*call_args)

        btn = dpg.add_button(label=text, callback=wrapped_callback, tag=tag, parent=self.main_window_tag)
        return btn

    # --- Fullscreen method ---
    def fullscreen(self, window_tag=None, enable=True):
        if window_tag is None:
            window_tag = self.main_window_tag
        self._fullscreen_target = window_tag
        dpg.set_viewport_fullscreen(enable)

        if enable:
            def resize_callback(sender, app_data):
                w, h = dpg.get_viewport_width(), dpg.get_viewport_height()
                dpg.set_item_width(self._fullscreen_target, w)
                dpg.set_item_height(self._fullscreen_target, h)

            if self._fullscreen_handler:
                dpg.delete_handler_registry(self._fullscreen_handler)
            self._fullscreen_handler = dpg.add_handler_registry()
            dpg.add_viewport_resize_handler(callback=resize_callback, parent=self._fullscreen_handler)

    # --- Get/Set values ---
    def get(self, tag):
        return dpg.get_value(tag)

    def set(self, tag, value):
        dpg.set_value(tag, value)

    def register_widget(self, tag, dpg_id):
        # Optional for manual DPG widgets
        pass

    def show(self):
        dpg.show_viewport()
        dpg.start_dearpygui()
        dpg.destroy_context()
