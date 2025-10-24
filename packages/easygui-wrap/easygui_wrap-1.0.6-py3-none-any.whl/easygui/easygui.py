try:
    import dearpygui.dearpygui as dpg
    GUI_BACKEND = "dpg"
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    GUI_BACKEND = "tk"

class EasyGUI:
    """
    EasyGUI — Super-simplified cross-backend GUI wrapper.
    Features:
      - DearPyGui or Tkinter backend
      - Tag system
      - Callbacks with args/args_tags
      - get_value/set_value helpers
      - Optional fullscreen
      - NEW: decorated=False → removes title bar & borders
    """

    def __init__(self, title="EasyGUI", size=(600,400), bg_color=None,
                 fullscreen_window=False, decorated=True):
        self.width, self.height = size
        self.bg_color = bg_color or [50,50,50]
        self.fullscreen_window = fullscreen_window
        self.decorated = decorated
        self._tags = {}

        if GUI_BACKEND == "dpg":
            dpg.create_context()
            dpg.create_viewport(title=title, width=self.width, height=self.height)
            dpg.setup_dearpygui()

            if not decorated:
                dpg.set_viewport_decorated(False)

            self._main_window = dpg.add_window(label=title, no_title_bar=not decorated, no_move=False)
            if fullscreen_window:
                dpg.set_viewport_resize_callback(self._resize_viewport)
            dpg.show_viewport()
        else:
            self._root = tk.Tk()
            self._root.title(title)
            self._root.geometry(f"{self.width}x{self.height}")
            if not decorated:
                self._root.overrideredirect(True)
            self._widgets = {}

    # ==================== Callback Wrapper ====================
    def _wrap_callback(self, callback, args_tags=None, args=None):
        args_tags = args_tags or []
        args = args or ()
        def wrapper():
            values = [self.get_value(tag) for tag in args_tags]
            callback(*values, *args)
        return wrapper

    # ==================== Widgets ====================
    def add_label(self, text, tag=None, fg=None, font_size=16):
        tag = tag or text
        if GUI_BACKEND == "dpg":
            lbl = dpg.add_text(default_value=text, tag=tag, color=fg or [255,255,255], parent=self._main_window)
        else:
            lbl = tk.Label(self._root, text=text, fg=fg or "black")
            lbl.pack()
            self._widgets[tag] = lbl
        self._tags[tag] = lbl
        return lbl

    def add_entry(self, default_value="", tag=None, width=200):
        tag = tag or f"entry_{len(self._tags)}"
        if GUI_BACKEND == "dpg":
            ent = dpg.add_input_text(default_value=default_value, tag=tag, width=width, parent=self._main_window)
        else:
            ent = tk.Entry(self._root, width=width//10)
            ent.insert(0, default_value)
            ent.pack()
            self._widgets[tag] = ent
        self._tags[tag] = ent
        return ent

    def add_button(self, text, callback, args_tags=None, args=None, fg=None, bg=None, font_size=14, tag=None):
        tag = tag or f"btn_{len(self._tags)}"
        if GUI_BACKEND == "dpg":
            btn = dpg.add_button(label=text, tag=tag,
                                 callback=self._wrap_callback(callback, args_tags, args),
                                 parent=self._main_window)
        else:
            btn = tk.Button(self._root, text=text, command=self._wrap_callback(callback, args_tags, args),
                            fg=fg or "black", bg=bg or "lightgray")
            btn.pack()
            self._widgets[tag] = btn
        self._tags[tag] = btn
        return btn

    def add_slider(self, label="", tag=None, min_value=0, max_value=100, default_value=0):
        tag = tag or f"slider_{len(self._tags)}"
        if GUI_BACKEND == "dpg":
            s = dpg.add_slider_int(label=label, tag=tag, min_value=min_value, max_value=max_value,
                                   default_value=default_value, parent=self._main_window)
        else:
            s_var = tk.IntVar(value=default_value)
            s = ttk.Scale(self._root, from_=min_value, to=max_value, orient="horizontal", variable=s_var)
            s.pack()
            self._widgets[tag] = s_var
        self._tags[tag] = s
        return s

    def add_checkbox(self, label="", tag=None, default_value=False):
        tag = tag or f"chk_{len(self._tags)}"
        if GUI_BACKEND == "dpg":
            chk = dpg.add_checkbox(label=label, tag=tag, default_value=default_value, parent=self._main_window)
        else:
            var = tk.BooleanVar(value=default_value)
            chk = tk.Checkbutton(self._root, text=label, variable=var)
            chk.pack()
            self._widgets[tag] = var
        self._tags[tag] = chk
        return chk

    # ==================== Value Helpers ====================
    def get_value(self, tag):
        if GUI_BACKEND == "dpg":
            return dpg.get_value(tag)
        else:
            w = self._widgets.get(tag)
            if isinstance(w, tk.Entry):
                return w.get()
            elif isinstance(w, (tk.BooleanVar, tk.IntVar)):
                return w.get()
            return None

    def set_value(self, tag, value):
        if GUI_BACKEND == "dpg":
            dpg.set_value(tag, value)
        else:
            w = self._widgets.get(tag)
            if isinstance(w, tk.Entry):
                w.delete(0, "end")
                w.insert(0, value)
            elif isinstance(w, (tk.BooleanVar, tk.IntVar)):
                w.set(value)

    # ==================== Fullscreen / Resize ====================
    def toggle_fullscreen(self, state=None):
        if GUI_BACKEND == "dpg":
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
        if self.fullscreen_window:
            dpg.set_viewport_width(dpg.get_viewport_client_width())
            dpg.set_viewport_height(dpg.get_viewport_client_height())

    # ==================== Show GUI ====================
    def show(self):
        if GUI_BACKEND == "dpg":
            dpg.start_dearpygui()
            dpg.destroy_context()
        else:
            self._root.mainloop()
