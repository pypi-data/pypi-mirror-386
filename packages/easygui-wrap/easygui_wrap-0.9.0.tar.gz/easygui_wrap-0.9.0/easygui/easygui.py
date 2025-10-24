# easygui/easygui.py
try:
    import dearpygui.dearpygui as dpg
    GUI_BACKEND = "dearpygui"
except ImportError:
    import tkinter as tk
    from tkinter import font as tkfont
    from tkinter import colorchooser as tkcolor
    GUI_BACKEND = "tkinter"

class EasyGUI:
    def __init__(self, title="EasyGUI Window", size=(400, 300), bg_color=None):
        self.backend = GUI_BACKEND
        self.title = title
        self.size = size
        self.tag_map = {}

        if self.backend == "tkinter":
            self.root = tk.Tk()
            self.root.title(title)
            self.root.geometry(f"{size[0]}x{size[1]}")
            if bg_color:
                self.root.configure(bg=bg_color)
        else:
            dpg.create_context()
            self.main_window = dpg.add_window(label=title, width=size[0], height=size[1])

    # --- Font helper ---
    def _get_font(self, size=12, bold=False, italic=False):
        if self.backend == "tkinter":
            weight = "bold" if bold else "normal"
            slant = "italic" if italic else "roman"
            return tkfont.Font(size=size, weight=weight, slant=slant)
        return None

    # --- Fetch value by tag ---
    def get_value(self, tag):
        widget = self.tag_map[tag]
        if self.backend == "tkinter":
            if isinstance(widget, tk.Entry):
                return widget.get()
            elif isinstance(widget, tk.Text):
                return widget.get("1.0", tk.END).rstrip("\n")
            elif isinstance(widget, tk.Scale):
                return widget.get()
            elif isinstance(widget, tk.Checkbutton):
                return widget.var.get()
            elif isinstance(widget, tk.Label):
                return widget.cget("text")
            else:
                return None
        else:
            return dpg.get_value(widget)

    # --- Update widget value dynamically ---
    def update_value(self, tag, value):
        widget = self.tag_map[tag]
        if self.backend == "tkinter":
            if isinstance(widget, (tk.Entry, tk.Text)):
                widget.delete(0, tk.END) if isinstance(widget, tk.Entry) else widget.delete("1.0", tk.END)
                widget.insert(0 if isinstance(widget, tk.Entry) else "1.0", value)
            elif isinstance(widget, tk.Scale):
                widget.set(value)
            elif isinstance(widget, tk.Checkbutton):
                widget.var.set(bool(value))
            elif isinstance(widget, tk.Label):
                widget.config(text=str(value))
        else:
            dpg.set_value(widget, value)

    # --- Wrap callback with tag + normal args support ---
    def _wrap_callback(self, callback, args_tags=None, args=None):
        def wrapped(*_):
            values = []
            if args_tags:
                values.extend([self.get_value(tag) for tag in args_tags])
            if args:
                values.extend(args)
            callback(*values)
        return wrapped

    # --- Widgets ---
    def add_label(self, text, tag=None, fg=None, bg=None, font_size=12, bold=False, italic=False, padding=5):
        if self.backend == "tkinter":
            lbl = tk.Label(self.root, text=text, fg=fg, bg=bg, font=self._get_font(font_size, bold, italic))
            lbl.pack(padx=padding, pady=padding)
            if tag: self.tag_map[tag] = lbl
            return lbl
        else:
            lbl = dpg.add_text(text, parent=self.main_window, color=fg if fg else [255,255,255])
            if tag: self.tag_map[tag] = lbl
            return lbl

    def add_entry(self, default_text="", tag=None, fg=None, bg=None, font_size=12, padding=5):
        if self.backend == "tkinter":
            e = tk.Entry(self.root, fg=fg, bg=bg, font=self._get_font(font_size))
            e.insert(0, default_text)
            e.pack(padx=padding, pady=padding)
            if tag: self.tag_map[tag] = e
            return e
        else:
            e = dpg.add_input_text(default_value=default_text, parent=self.main_window)
            if tag: self.tag_map[tag] = e
            return e

    def add_button(self, text, callback, args_tags=None, args=None, tag=None, fg=None, bg=None, font_size=12, bold=False, padding=5):
        cb = self._wrap_callback(callback, args_tags, args)
        if self.backend == "tkinter":
            b = tk.Button(self.root, text=text, command=cb, fg=fg, bg=bg, font=self._get_font(font_size, bold))
            b.pack(padx=padding, pady=padding)
            if tag: self.tag_map[tag] = b
            return b
        else:
            b = dpg.add_button(label=text, callback=cb, parent=self.main_window)
            if tag: self.tag_map[tag] = b
            return b

    def add_slider(self, min_value=0, max_value=100, default_value=0, tag=None, padding=5):
        if self.backend == "tkinter":
            s = tk.Scale(self.root, from_=min_value, to=max_value, orient=tk.HORIZONTAL)
            s.set(default_value)
            s.pack(padx=padding, pady=padding)
            if tag: self.tag_map[tag] = s
            return s
        else:
            s = dpg.add_slider_int(min_value=min_value, max_value=max_value, default_value=default_value, parent=self.main_window)
            if tag: self.tag_map[tag] = s
            return s

    def add_checkbox(self, text="Check me", default=False, tag=None, padding=5):
        if self.backend == "tkinter":
            var = tk.BooleanVar(value=default)
            chk = tk.Checkbutton(self.root, text=text, variable=var)
            chk.var = var
            chk.pack(padx=padding, pady=padding)
            if tag: self.tag_map[tag] = chk
            return chk
        else:
            chk = dpg.add_checkbox(label=text, default_value=default, parent=self.main_window)
            if tag: self.tag_map[tag] = chk
            return chk

    def add_text_area(self, default_text="", tag=None, padding=5):
        if self.backend == "tkinter":
            txt = tk.Text(self.root, height=5, width=40)
            txt.insert(tk.END, default_text)
            txt.pack(padx=padding, pady=padding)
            if tag: self.tag_map[tag] = txt
            return txt
        else:
            ta = dpg.add_input_text(multiline=True, default_value=default_text, parent=self.main_window)
            if tag: self.tag_map[tag] = ta
            return ta

    def add_color_picker(self, default=(255,255,255), tag=None, padding=5):
        if self.backend == "tkinter":
            def pick():
                color = tkcolor.askcolor(color=default)[0]
                return color
            btn = tk.Button(self.root, text="Pick Color", command=pick)
            btn.pack(padx=padding, pady=padding)
            if tag: self.tag_map[tag] = btn
            return pick
        else:
            cp = dpg.add_color_picker(default_value=default, parent=self.main_window)
            if tag: self.tag_map[tag] = cp
            return cp

    # --- Show GUI ---
    def show(self):
        if self.backend == "tkinter":
            self.root.mainloop()
        else:
            dpg.create_viewport(title=self.title, width=self.size[0], height=self.size[1])
            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.start_dearpygui()
            dpg.destroy_context()
