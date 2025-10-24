import sys

# Try importing DearPyGui
try:
    import dearpygui.dearpygui as dpg
    BACKEND = "dearpygui"
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    BACKEND = "tkinter"


class EasyGUI:
    def __init__(self, title="EasyGUI App", size=(400, 300),
                 bg_color=None, window_frame=True):
        self.title = title
        self.size = size
        self.bg_color = bg_color
        self.window_frame = window_frame
        self.backend = BACKEND
        self.widgets = {}

        if self.backend == "dearpygui":
            self._setup_dpg()
        else:
            self._setup_tk()

    # -------------------- DPG SETUP --------------------
    def _setup_dpg(self):
        dpg.create_context()
        dpg.create_viewport(title=self.title, width=self.size[0], height=self.size[1])

        if self.bg_color:
            bg_rgb = self._parse_color(self.bg_color)
            dpg.set_viewport_clear_color(bg_rgb)

        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Create invisible or framed window
        self.parent_window = dpg.add_window(
            label="" if not self.window_frame else self.title,
            no_close=not self.window_frame,
            no_title_bar=not self.window_frame,
            no_move=not self.window_frame,
            no_resize=not self.window_frame,
            width=self.size[0],
            height=self.size[1]
        )

    # -------------------- TK SETUP --------------------
    def _setup_tk(self):
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry(f"{self.size[0]}x{self.size[1]}")
        if self.bg_color:
            self.root.configure(bg=self.bg_color)

    # -------------------- ADD LABEL --------------------
    def add_label(self, text, tag=None, fg=None, bg=None,
                  font_size=12, bold=False, italic=False, padding=5):
        font_style = ("Arial", font_size, ("bold" if bold else "") + (" italic" if italic else ""))
        if self.backend == "dearpygui":
            lbl = dpg.add_text(text, color=self._parse_color(fg),
                               parent=self.parent_window)
        else:
            lbl = tk.Label(self.root, text=text, fg=fg, bg=bg or self.bg_color, font=font_style)
            lbl.pack(pady=padding)
        if tag:
            self.widgets[tag] = lbl
        return lbl

    # -------------------- ADD ENTRY --------------------
    def add_entry(self, default_text="", tag=None, fg=None, bg=None,
                  font_size=12, padding=5):
        if self.backend == "dearpygui":
            entry = dpg.add_input_text(default_value=default_text,
                                       parent=self.parent_window)
        else:
            entry = tk.Entry(self.root, fg=fg, bg=bg or "white", font=("Arial", font_size))
            entry.insert(0, default_text)
            entry.pack(pady=padding)
        if tag:
            self.widgets[tag] = entry
        return entry

    # -------------------- ADD BUTTON --------------------
    def add_button(self, text, callback, args_tags=None, args=None,
                   tag=None, fg=None, bg=None, font_size=12, bold=False, padding=5):
        wrapped_cb = self._wrap_callback(callback, args_tags, args)

        if self.backend == "dearpygui":
            btn = dpg.add_button(label=text, callback=wrapped_cb,
                                 parent=self.parent_window)
        else:
            btn = tk.Button(self.root, text=text, command=wrapped_cb,
                            fg=fg, bg=bg, font=("Arial", font_size, "bold" if bold else "normal"))
            btn.pack(pady=padding)
        if tag:
            self.widgets[tag] = btn
        return btn

    # -------------------- ADD SLIDER --------------------
    def add_slider(self, min_value=0, max_value=100, default_value=0, tag=None):
        if self.backend == "dearpygui":
            slider = dpg.add_slider_int(label="", min_value=min_value, max_value=max_value,
                                        default_value=default_value, parent=self.parent_window)
        else:
            slider = tk.Scale(self.root, from_=min_value, to=max_value, orient="horizontal")
            slider.set(default_value)
            slider.pack(pady=5)
        if tag:
            self.widgets[tag] = slider
        return slider

    # -------------------- ADD CHECKBOX --------------------
    def add_checkbox(self, text="Check me", default=False, tag=None):
        if self.backend == "dearpygui":
            chk = dpg.add_checkbox(label=text, default_value=default,
                                   parent=self.parent_window)
        else:
            var = tk.BooleanVar(value=default)
            chk = tk.Checkbutton(self.root, text=text, variable=var)
            chk.var = var
            chk.pack(pady=5)
        if tag:
            self.widgets[tag] = chk
        return chk

    # -------------------- ADD TEXT AREA --------------------
    def add_text_area(self, default_text="", tag=None):
        if self.backend == "dearpygui":
            txt = dpg.add_input_text(default_value=default_text, multiline=True,
                                     parent=self.parent_window)
        else:
            txt = tk.Text(self.root, height=5)
            txt.insert("1.0", default_text)
            txt.pack(pady=5)
        if tag:
            self.widgets[tag] = txt
        return txt

    # -------------------- ADD COLOR PICKER --------------------
    def add_color_picker(self, default=(255, 255, 255), tag=None):
        if self.backend == "dearpygui":
            col = dpg.add_color_picker(default_value=default,
                                       parent=self.parent_window)
        else:
            col = self.add_label("Color picker (not supported in Tkinter)", fg="gray")
        if tag:
            self.widgets[tag] = col
        return col

    # -------------------- GET / UPDATE --------------------
    def get_value(self, tag):
        widget = self.widgets.get(tag)
        if not widget:
            return None
        if self.backend == "dearpygui":
            return dpg.get_value(widget)
        elif isinstance(widget, tk.Entry):
            return widget.get()
        elif isinstance(widget, tk.Text):
            return widget.get("1.0", "end-1c")
        elif isinstance(widget, tk.Scale):
            return widget.get()
        elif isinstance(widget, tk.Checkbutton):
            return widget.var.get()
        elif isinstance(widget, tk.Label):
            return widget.cget("text")
        return None

    def update_value(self, tag, new_value):
        widget = self.widgets.get(tag)
        if not widget:
            return
        if self.backend == "dearpygui":
            dpg.set_value(widget, new_value)
        elif isinstance(widget, tk.Label):
            widget.config(text=new_value)
        elif isinstance(widget, (tk.Entry, tk.Text)):
            widget.delete(0, "end")
            widget.insert(0, new_value)

    # -------------------- CALLBACK WRAPPER --------------------
    def _wrap_callback(self, callback, args_tags=None, args=None):
        args_tags = args_tags or []
        args = args or []

        def wrapped(sender=None, data=None):
            tag_values = [self.get_value(tag) for tag in args_tags]
            callback(*tag_values, *args)

        return wrapped

    # -------------------- SHOW --------------------
    def show(self):
        if self.backend == "dearpygui":
            dpg.start_dearpygui()
            dpg.destroy_context()
        else:
            self.root.mainloop()

    # -------------------- COLOR PARSER --------------------
    def _parse_color(self, color):
        if not color:
            return (255, 255, 255)
        if isinstance(color, (list, tuple)):
            return color
        color_map = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "yellow": (255, 255, 0),
            "purple": (128, 0, 128),
            "gray": (128, 128, 128),
            "lightblue": (173, 216, 230),
            "orange": (255, 165, 0),
        }
        return color_map.get(color.lower(), (255, 255, 255))
