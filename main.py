import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import tkinter.ttk as ttk
import threading
import subprocess
import sys
import os
import json
from pathlib import Path

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

from installer import WheelInstaller
from i18n import (
    load_settings, save_settings, get_text, format_text, 
    LANGUAGE_NAMES, get_current_language, load_history, clear_history
)


class NotificationManager:
    @staticmethod
    def send(title, message):
        if NOTIFICATIONS_AVAILABLE:
            try:
                notification.notify(title=title, message=message, timeout=5)
            except:
                pass


class TitleBar:
    def __init__(self, parent, root, title_text, settings_cmd):
        self.root = root
        self.parent = parent
        self.settings_cmd = settings_cmd
        self.is_maximized = False
        
        self.frame = tk.Frame(parent, bg="#1e1e1e", height=40, cursor="fleur")
        self.frame.pack(fill=tk.X)
        self.frame.pack_propagate(False)
        
        self.frame.bind("<Button-1>", self._on_drag_start)
        self.frame.bind("<B1-Motion>", self._on_drag_motion)
        self.frame.bind("<Double-Button-1>", self._on_double_click)
        
        title_label = tk.Label(
            self.frame,
            text=f"  {title_text}",
            font=("Segoe UI", 12, "bold"),
            bg="#1e1e1e",
            fg="#ffffff"
        )
        title_label.pack(side=tk.LEFT, padx=(10, 0))
        title_label.bind("<Button-1>", self._on_drag_start)
        title_label.bind("<B1-Motion>", self._on_drag_motion)
        title_label.bind("<Double-Button-1>", self._on_double_click)
        
        btn_frame = tk.Frame(self.frame, bg="#1e1e1e")
        btn_frame.pack(side=tk.RIGHT, padx=(0, 5))
        
        self._create_button(btn_frame, "⚙", self._on_settings, "#1e1e1e", "#808080", "#3d3d3d", "#ffffff")
        self._create_button(btn_frame, "□", self._on_maximize, "#1e1e1e", "#808080", "#3d3d3d", "#ffffff")
        self._create_button(btn_frame, "✕", self._on_close, "#e81123", "#ffffff", "#c42b1c", "#ffffff")
    
    def _create_button(self, parent, text, cmd, bg, fg, hover_bg, hover_fg):
        btn = tk.Label(
            parent,
            text=text,
            font=("Segoe UI Symbol", 11),
            bg=bg,
            fg=fg,
            width=3,
            height=1,
            cursor="hand2"
        )
        btn.pack(side=tk.LEFT)
        
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg, fg=hover_fg))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg, fg=fg))
        btn.bind("<Button-1>", lambda e: cmd())
        
        return btn
    
    def _on_drag_start(self, event):
        self._drag_data = {"x": event.x, "y": event.y}
    
    def _on_drag_motion(self, event):
        if self.is_maximized:
            return
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        new_x = self.root.winfo_x() + delta_x
        new_y = self.root.winfo_y() + delta_y
        self.root.geometry(f"+{new_x}+{new_y}")
    
    def _on_double_click(self, event):
        self._on_maximize()
    
    def _on_settings(self):
        self.settings_cmd()
    
    def _on_maximize(self):
        if self.is_maximized:
            self.root.state("normal")
            self.is_maximized = False
        else:
            self.root.state("zoomed")
            self.is_maximized = True
    
    def _on_close(self):
        self.root.destroy()


class SplashScreen:
    def __init__(self, on_complete):
        self.on_complete = on_complete
        
        if DND_AVAILABLE:
            self.window = TkinterDnD.Tk()
        else:
            self.window = tk.Tk()
        
        self.window.overrideredirect(True)
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width, height = 400, 300
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.configure(bg="#1e1e1e")
        
        self._create_ui()
        self._animate()
    
    def _create_ui(self):
        main_frame = tk.Frame(self.window, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(
            main_frame,
            text="BI Loader",
            font=("Segoe UI", 36, "bold"),
            bg="#1e1e1e",
            fg="#ffffff"
        )
        title_label.pack(pady=(60, 5))
        
        subtitle_label = tk.Label(
            main_frame,
            text="by asarkus",
            font=("Segoe UI", 12),
            bg="#1e1e1e",
            fg="#808080"
        )
        subtitle_label.pack(pady=(0, 30))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "splash.Horizontal.TProgressbar",
            troughcolor="#2d2d2d",
            background="#2196F3",
            borderwidth=0,
            thickness=8
        )
        
        self.progress = ttk.Progressbar(
            main_frame,
            style="splash.Horizontal.TProgressbar",
            mode='determinate',
            length=250
        )
        self.progress.pack(pady=(0, 15))
        
        self.status_label = tk.Label(
            main_frame,
            text=get_text("loading"),
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#808080"
        )
        self.status_label.pack()
    
    def _animate(self):
        self.progress['value'] = 0
        
        steps = [
            (20, get_text("loading")),
            (50, get_text("loading")),
            (80, get_text("loading")),
            (100, get_text("complete"))
        ]
        
        def animate_step(index=0):
            if index < len(steps):
                value, status = steps[index]
                self.progress['value'] = value
                self.status_label.config(text=status)
                self.window.update()
                self.window.after(1200, lambda: animate_step(index + 1))
            else:
                self.window.after(500, self.close)
        
        animate_step()
    
    def close(self):
        self.window.destroy()
        self.on_complete()


class LanguageScreen:
    def __init__(self, on_select):
        self.on_select = on_select
        self.window = tk.Toplevel()
        self.window.overrideredirect(True)
        
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width, height = 400, 350
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        self.window.configure(bg="#1e1e1e")
        self._create_ui()
    
    def _create_ui(self):
        main_frame = tk.Frame(self.window, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        welcome_label = tk.Label(
            main_frame,
            text=get_text("welcome"),
            font=("Segoe UI", 24, "bold"),
            bg="#1e1e1e",
            fg="#ffffff"
        )
        welcome_label.pack(pady=(50, 20))
        
        choose_label = tk.Label(
            main_frame,
            text=get_text("choose_language"),
            font=("Segoe UI", 14),
            bg="#1e1e1e",
            fg="#b0b0b0"
        )
        choose_label.pack(pady=(0, 30))
        
        btn_frame = tk.Frame(main_frame, bg="#1e1e1e")
        btn_frame.pack(pady=20)
        
        for lang_code, lang_name in LANGUAGE_NAMES:
            btn = tk.Button(
                btn_frame,
                text=lang_name,
                font=("Segoe UI", 13),
                bg="#3a3a3a",
                fg="#ffffff",
                activebackground="#4a4a4a",
                activeforeground="#ffffff",
                bd=0,
                padx=50,
                pady=14,
                cursor="hand2",
                relief="flat",
                command=lambda c=lang_code: self.select_language(c)
            )
            btn.pack(pady=10, fill=tk.X, padx=30)
    
    def select_language(self, lang):
        settings = load_settings()
        settings["language"] = lang
        settings["first_run"] = False
        save_settings(settings)
        self.window.destroy()
        self.on_select()


class BILoaderApp:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.title(get_text("app_title"))
        self.root.geometry("800x650")
        self.root.minsize(700, 550)
        self.root.configure(bg="#1e1e1e")
        
        self.title_bar = TitleBar(self.root, self.root, get_text("title"), self.show_settings)
        
        self.installer = WheelInstaller()
        self.selected_files = []
        self.current_tab = 0
        self.installed_packages = []
        self.packages_with_updates = []
        
        self._setup_styles()
        self._create_ui()
    
    def debug_log(self, message):
        settings = load_settings()
        if settings.get("debug_mode", False):
            messagebox.showinfo("DEBUG", message)
        print(f"[DEBUG] {message}")
    
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Horizontal.TProgressbar",
            background="#2196F3",
            troughcolor="#2d2d2d",
            borderwidth=0,
            thickness=8
        )
    
    def _create_ui(self):
        self.tab_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.tab_frame.pack(fill=tk.X, padx=20, pady=(10, 0))
        
        tabs = ["tab_install", "tab_uninstall", "tab_update", "tab_history"]
        
        self.tab_buttons = []
        for i, key in enumerate(tabs):
            btn = tk.Button(
                self.tab_frame,
                text=get_text(key),
                font=("Segoe UI", 11),
                bg="#2d2d2d" if i != 0 else "#2196F3",
                fg="#ffffff",
                activebackground="#3d3d3d" if i != 0 else "#1976D2",
                activeforeground="#ffffff",
                bd=0,
                padx=20,
                pady=10,
                cursor="hand2",
                relief="flat",
                command=lambda idx=i: self.switch_tab(idx)
            )
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.tab_buttons.append(btn)
        
        self.content_frame = tk.Frame(self.root, bg="#1e1e1e", padx=20, pady=15)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.progress_frame = tk.Frame(self.root, bg="#1e1e1e", padx=20)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#808080"
        )
        self.progress_label.pack(side=tk.TOP, anchor="w")

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            style="Horizontal.TProgressbar",
            mode='determinate',
            length=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))

        log_frame = tk.LabelFrame(
            self.root,
            text=get_text("log_frame"),
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#ffffff",
            padx=10,
            pady=5
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            wrap=tk.WORD,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.tag_config("info", foreground="#4fc3f7")
        self.log_text.tag_config("success", foreground="#81c784")
        self.log_text.tag_config("error", foreground="#e57373")
        self.log_text.tag_config("warning", foreground="#ffb74d")
        
        self.switch_tab(0)
    
    def switch_tab(self, index):
        self.current_tab = index
        
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.configure(bg="#2196F3", activebackground="#1976D2")
            else:
                btn.configure(bg="#2d2d2d", activebackground="#3d3d3d")
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        if index == 0:
            self._create_install_tab()
        elif index == 1:
            self._create_uninstall_tab()
        elif index == 2:
            self._create_update_tab()
        elif index == 3:
            self._create_history_tab()
    
    def _create_install_tab(self):
        drop_frame = tk.Frame(self.content_frame, bg="#2d2d2d", bd=2, relief="solid")
        drop_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        drop_label = tk.Label(drop_frame, text=get_text("drop_zone"), font=("Segoe UI", 12), bg="#2d2d2d", fg="#808080")
        drop_label.pack(pady=30)
        
        self.drop_label = drop_label
        self.drop_frame = drop_frame
        
        if DND_AVAILABLE:
            drop_frame.drop_target_register(DND_FILES)
            drop_frame.dnd_bind('<<Drop>>', self._on_drop)
        
        self.files_label = tk.Label(self.content_frame, text=get_text("files_not_selected"), font=("Segoe UI", 10), bg="#1e1e1e", fg="#808080", anchor="w")
        self.files_label.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_select = tk.Button(btn_frame, text=get_text("select_files"), command=self.select_files, font=("Segoe UI", 11, "bold"), padx=15, pady=10, bg="#4CAF50", fg="#ffffff", activebackground="#45a049", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_select.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        self.btn_pypi = tk.Button(btn_frame, text=get_text("search_pypi"), command=self.show_pypi_search, font=("Segoe UI", 11, "bold"), padx=15, pady=10, bg="#FF9800", fg="#ffffff", activebackground="#F57C00", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_pypi.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        self.btn_requirements = tk.Button(btn_frame, text="📄 Requirements.txt", command=self.select_requirements, font=("Segoe UI", 11, "bold"), padx=15, pady=10, bg="#9C27B0", fg="#ffffff", activebackground="#7B1FA2", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_requirements.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        self.btn_clear = tk.Button(btn_frame, text=get_text("clear"), command=self.clear_files, font=("Segoe UI", 11, "bold"), padx=15, pady=10, bg="#f44336", fg="#ffffff", activebackground="#d32f2f", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_clear.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_install = tk.Button(self.content_frame, text=get_text("install"), command=self.validate_before_install, font=("Segoe UI", 13, "bold"), padx=30, pady=14, bg="#2196F3", fg="#ffffff", activebackground="#1976D2", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat", state=tk.DISABLED)
        self.btn_install.pack(fill=tk.X)
    
    def _create_uninstall_tab(self):
        search_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_packages())
        
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffffff", insertbackground="white", relief="flat", bd=0)
        search_entry.pack(fill=tk.X, ipadx=10, ipady=8)
        
        list_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.packages_list = tk.Listbox(list_frame, font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffffff", selectbackground="#2196F3", selectforeground="#ffffff", bd=0, relief="flat", yscrollcommand=scrollbar.set)
        self.packages_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.packages_list.yview)
        
        btn_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        btn_frame.pack(fill=tk.X)
        
        self.btn_refresh = tk.Button(btn_frame, text=get_text("refresh"), command=self.load_installed_packages, font=("Segoe UI", 11, "bold"), padx=20, pady=10, bg="#2d2d2d", fg="#ffffff", activebackground="#3d3d3d", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_refresh.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_uninstall = tk.Button(btn_frame, text=get_text("uninstall"), command=self.uninstall_selected, font=("Segoe UI", 11, "bold"), padx=20, pady=10, bg="#f44336", fg="#ffffff", activebackground="#d32f2f", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_uninstall.pack(side=tk.LEFT)
        
        self.load_installed_packages()
    
    def _create_update_tab(self):
        list_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.updates_list = tk.Listbox(list_frame, font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffffff", selectbackground="#2196F3", selectforeground="#ffffff", bd=0, relief="flat", yscrollcommand=scrollbar.set)
        self.updates_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.updates_list.yview)
        
        btn_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        btn_frame.pack(fill=tk.X)
        
        self.btn_check_updates = tk.Button(btn_frame, text=get_text("check_updates"), command=self.check_updates, font=("Segoe UI", 11, "bold"), padx=20, pady=10, bg="#2d2d2d", fg="#ffffff", activebackground="#3d3d3d", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_check_updates.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_update = tk.Button(btn_frame, text=get_text("update"), command=self.update_selected, font=("Segoe UI", 11, "bold"), padx=20, pady=10, bg="#2196F3", fg="#ffffff", activebackground="#1976D2", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_update.pack(side=tk.LEFT)
    
    def _create_history_tab(self):
        list_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_list = tk.Listbox(list_frame, font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffffff", bd=0, relief="flat", yscrollcommand=scrollbar.set)
        self.history_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_list.yview)
        
        btn_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        btn_frame.pack(fill=tk.X)
        
        self.btn_export = tk.Button(btn_frame, text=get_text("export"), command=self.export_history, font=("Segoe UI", 11, "bold"), padx=20, pady=10, bg="#4CAF50", fg="#ffffff", activebackground="#45a049", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_export.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_clear_history = tk.Button(btn_frame, text=get_text("clear_history"), command=self.clear_history_click, font=("Segoe UI", 11, "bold"), padx=20, pady=10, bg="#f44336", fg="#ffffff", activebackground="#d32f2f", activeforeground="#ffffff", bd=0, cursor="hand2", relief="flat")
        self.btn_clear_history.pack(side=tk.LEFT)
        
        self.load_history()
    
    def log(self, message, tag=None):
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.root.update()
    
    def _on_drop(self, event):
        if DND_AVAILABLE:
            files = self.root.tk.splitlist(event.data)
            for f in files:
                f = f.strip('{').strip('}')
                if f.lower().endswith('.whl'):
                    if f not in self.selected_files:
                        self.selected_files.append(f)
            self._update_files_label()
            if self.selected_files:
                self.log(format_text("added_files", count=len(files)), "info")
    
    def _update_files_label(self):
        whl_count = len([f for f in self.selected_files if f.lower().endswith('.whl')])
        req_count = len([f for f in self.selected_files if f.startswith("__req:")])
        
        if whl_count == 0 and req_count == 0:
            self.files_label.config(text=get_text("files_not_selected"))
            self.btn_install.config(state=tk.DISABLED)
        else:
            parts = []
            if whl_count > 0:
                parts.append(f"{whl_count} WHL")
            if req_count > 0:
                parts.append(f"{req_count} requirements")
            self.files_label.config(text=" | ".join(parts))
            self.btn_install.config(state=tk.NORMAL)
    
    def select_files(self):
        file_types = [("WHL файлы", "*.whl")]
        files = filedialog.askopenfilenames(title=get_text("select_files"), filetypes=file_types)
        
        if files:
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
            self._update_files_label()
    
    def select_requirements(self):
        file_path = filedialog.askopenfilename(title="Select requirements.txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        
        if file_path:
            self.log(f"Reading requirements from: {file_path}", "info")
            deps, error = self.installer.parse_requirements(file_path)
            
            if error:
                messagebox.showerror("Error", f"Failed to parse requirements:\n{error}")
                return
            
            if not deps:
                messagebox.showwarning("Warning", "No dependencies found in file")
                return
            
            for dep in deps:
                req_str = f"{dep['name']}{dep['spec']}" if dep['spec'] else dep['name']
                whl_path = f"__req:{req_str}"
                if whl_path not in self.selected_files:
                    self.selected_files.append(whl_path)
            
            self._update_files_label()
            messagebox.showinfo("Success", f"Added {len(deps)} packages to installation queue")
    
    def clear_files(self):
        self.selected_files = []
        self._update_files_label()
    
    def validate_before_install(self):
        whl_files = [f for f in self.selected_files if f.lower().endswith('.whl')]
        
        if not whl_files:
            if self.selected_files:
                self.start_requirements_install()
            else:
                messagebox.showwarning(get_text("ready"), get_text("no_files"))
            return
        
        validation_results = []
        
        for whl_file in whl_files:
            valid, errors, warnings = self.installer.validate_whl(whl_file)
            validation_results.append({'file': Path(whl_file).name, 'valid': valid, 'errors': errors, 'warnings': warnings})
        
        self._show_validation_dialog(validation_results)
    
    def _show_validation_dialog(self, results):
        dialog = tk.Toplevel(self.root)
        dialog.title(get_text("validation_results"))
        dialog.geometry("500x400")
        dialog.configure(bg="#1e1e1e")
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg="#1e1e1e", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = tk.Label(frame, text=get_text("validation_results"), font=("Segoe UI", 14, "bold"), bg="#1e1e1e", fg="#ffffff")
        title.pack(pady=(0, 15))
        
        scroll = tk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        text = tk.Text(frame, font=("Consolas", 10), bg="#2d2d2d", fg="#d4d4d4", yscrollcommand=scroll.set, height=15)
        text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=text.yview)
        
        has_critical_errors = False
        
        for r in results:
            if r['errors']:
                has_critical_errors = True
                text.insert(tk.END, f"❌ {r['file']}\n", "error")
                for err in r['errors']:
                    text.insert(tk.END, f"   {err}\n", "error")
            elif r['warnings']:
                text.insert(tk.END, f"⚠ {r['file']}\n", "warning")
                for warn in r['warnings']:
                    text.insert(tk.END, f"   {warn}\n", "warning")
            else:
                text.insert(tk.END, f"✅ {r['file']} - OK\n", "success")
        
        text.tag_config("success", foreground="#81c784")
        text.tag_config("warning", foreground="#ffb74d")
        text.tag_config("error", foreground="#e57373")
        
        btn_frame = tk.Frame(frame, bg="#1e1e1e")
        btn_frame.pack(pady=(15, 0))
        
        def proceed():
            dialog.destroy()
            self.start_installation()
        
        cancel_btn = tk.Button(btn_frame, text=get_text("cancel"), command=dialog.destroy, font=("Segoe UI", 11), padx=20, pady=8, bg="#f44336", fg="#ffffff", activebackground="#d32f2f", bd=0, cursor="hand2", relief="flat")
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        proceed_btn = tk.Button(btn_frame, text=get_text("continue"), command=proceed, font=("Segoe UI", 11), padx=20, pady=8, bg="#4CAF50" if not has_critical_errors else "#f44336", fg="#ffffff", activebackground="#45a049", bd=0, cursor="hand2", relief="flat")
        proceed_btn.pack(side=tk.LEFT, padx=5)
        
        if has_critical_errors:
            proceed_btn.config(state=tk.DISABLED)
    
    def start_installation(self):
        whl_files = [f for f in self.selected_files if f.lower().endswith('.whl')]
        
        if not whl_files:
            return

        self.btn_install.config(state=tk.DISABLED)
        self.btn_select.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.progress_label.config(text=get_text("preparing"))
        
        self.log("=" * 50, "info")
        self.log(format_text("installing", i=1, total=len(whl_files)), "info")
        self.log("=" * 50, "info")

        thread = threading.Thread(target=self._install_worker, args=(whl_files,), daemon=True)
        thread.start()
    
    def _install_worker(self, whl_files):
        total = len(whl_files)
        
        for i, whl_file in enumerate(whl_files, 1):
            progress_percent = ((i - 1) / total) * 100
            self.root.after(0, lambda p=progress_percent: self.progress_bar.config(value=p))
            self.root.after(0, lambda: self.progress_label.config(text=format_text("installing", i=i, total=total)))
            self.root.after(0, lambda: self.log(f"\n--- {format_text('installing_package', i=i, total=total)} ---", "info"))
            
            success, info = self.installer.install_whl(whl_file, callback=self.log)
            
            if success and info:
                from i18n import add_to_history
                add_to_history(info['name'], info['version'], whl_file)
                self.root.after(0, lambda: self.log(get_text("install_success"), "success"))
            else:
                self.root.after(0, lambda: self.log(get_text("install_error"), "error"))

        self.root.after(0, lambda: self.progress_bar.config(value=100))
        self.root.after(0, self._install_complete)

    def _install_complete(self):
        self.progress_label.config(text=get_text("complete"))
        self.btn_install.config(state=tk.NORMAL)
        self.btn_select.config(state=tk.NORMAL)
        
        self.log("\n" + "=" * 50, "info")
        self.log(get_text("complete"), "success")
        self.log("=" * 50, "info")
        
        messagebox.showinfo(get_text("ready"), get_text("complete"))
    
    def start_requirements_install(self):
        req_files = [f for f in self.selected_files if f.startswith("__req:")]
        
        if not req_files:
            return
        
        self.btn_install.config(state=tk.DISABLED)
        self.btn_select.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Installing from requirements...")
        
        self.log("=" * 50, "info")
        self.log("Installing from requirements.txt...", "info")
        self.log("=" * 50, "info")
        
        thread = threading.Thread(target=self._requirements_install_worker, args=(req_files,), daemon=True)
        thread.start()
    
    def _requirements_install_worker(self, req_files):
        total = len(req_files)
        
        for i, req_str in enumerate(req_files, 1):
            pkg_spec = req_str.replace("__req:", "")
            progress_percent = ((i - 1) / total) * 100
            self.root.after(0, lambda p=progress_percent: self.progress_bar.config(value=p))
            self.root.after(0, lambda: self.progress_label.config(text=f"Installing {i}/{total}: {pkg_spec}"))
            self.root.after(0, lambda: self.log(f"\n--- Installing: {pkg_spec} ---", "info"))
            
            try:
                result = subprocess.run([sys.executable, '-m', 'pip', 'install', pkg_spec], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
                
                if result.returncode == 0:
                    self.root.after(0, lambda: self.log(f"✓ {pkg_spec} installed", "success"))
                    name = pkg_spec.split('==')[0].split('>=')[0].split('<=')[0]
                    from i18n import add_to_history
                    add_to_history(name, "latest", None)
                else:
                    err_msg = result.stderr[:100] if result.stderr else "Unknown error"
                    self.root.after(0, lambda msg=err_msg: self.log(f"✗ Error: {msg}", "error"))
            except Exception as e:
                err_msg = str(e)
                self.root.after(0, lambda msg=err_msg: self.log(f"✗ Exception: {msg}", "error"))
        
        self.root.after(0, lambda: self.progress_bar.config(value=100))
        self.root.after(0, self._install_complete)
    
    def load_installed_packages(self):
        self.packages_list.delete(0, tk.END)
        self.installed_packages = self.installer.list_installed_packages()
        
        for pkg in self.installed_packages:
            self.packages_list.insert(tk.END, f"{pkg['name']} ({pkg['version']})")
    
    def filter_packages(self):
        try:
            if not hasattr(self, 'packages_list') or not self.packages_list.winfo_exists():
                return
            
            search = self.search_var.get().lower()
            if search == get_text("search_package").lower():
                search = ""
            
            self.packages_list.delete(0, tk.END)
            
            for pkg in self.installed_packages:
                if search in pkg['name'].lower():
                    self.packages_list.insert(tk.END, f"{pkg['name']} ({pkg['version']})")
        except:
            pass
    
    def uninstall_selected(self):
        selection = self.packages_list.curselection()
        if not selection:
            messagebox.showwarning(get_text("ready"), get_text("select_package"))
            return
        
        pkg_text = self.packages_list.get(selection[0])
        pkg_name = pkg_text.split(" (")[0]
        
        if messagebox.askyesno(get_text("uninstall"), format_text("confirm_uninstall", package=pkg_name)):
            self.btn_uninstall.config(state=tk.DISABLED)
            thread = threading.Thread(target=self._uninstall_worker, args=(pkg_name,), daemon=True)
            thread.start()
    
    def _uninstall_worker(self, pkg_name):
        success = self.installer.uninstall_package(pkg_name, callback=self.log)
        
        self.root.after(0, lambda: self.btn_uninstall.config(state=tk.NORMAL))
        
        if success:
            self.root.after(0, lambda: self.load_installed_packages())
    
    def check_updates(self):
        self.btn_check_updates.config(state=tk.DISABLED)
        self.updates_list.delete(0, tk.END)
        self.log("Checking for updates...", "info")
        
        thread = threading.Thread(target=self._check_updates_worker, daemon=True)
        thread.start()
    
    def _check_updates_worker(self):
        packages = self.installer.list_installed_packages()
        self.packages_with_updates = []
        
        for i, pkg in enumerate(packages):
            progress = (i / len(packages)) * 100
            self.root.after(0, lambda p=progress: self.progress_bar.config(value=p))
            
            update_info = self.installer.check_package_update(pkg['name'])
            if update_info and update_info.get('has_update'):
                self.packages_with_updates.append(update_info)
                self.root.after(0, lambda u=update_info: self.updates_list.insert(tk.END, f"{u['name']} ({u['current']} → {u['latest']})"))
        
        self.root.after(0, lambda: self.progress_bar.config(value=100))
        self.root.after(0, lambda: self.btn_check_updates.config(state=tk.NORMAL))
        
        if not self.packages_with_updates:
            self.root.after(0, lambda: self.updates_list.insert(tk.END, get_text("no_updates")))
    
    def update_selected(self):
        selection = self.updates_list.curselection()
        if not selection:
            messagebox.showwarning(get_text("ready"), get_text("select_package"))
            return
        
        pkg_text = self.updates_list.get(selection[0])
        pkg_name = pkg_text.split(" (")[0]
        
        self.btn_update.config(state=tk.DISABLED)
        thread = threading.Thread(target=self._update_worker, args=(pkg_name,), daemon=True)
        thread.start()
    
    def _update_worker(self, pkg_name):
        success = self.installer.update_package(pkg_name, callback=self.log)
        
        self.root.after(0, lambda: self.btn_update.config(state=tk.NORMAL))
        
        if success:
            from i18n import add_to_history
            version = self.installer.get_package_version(pkg_name)
            if version:
                add_to_history(pkg_name, version)
            self.root.after(0, lambda: self.check_updates())
    
    def load_history(self):
        self.history_list.delete(0, tk.END)
        history = load_history()
        
        if not history:
            self.history_list.insert(tk.END, get_text("no_history"))
            return
        
        for item in history:
            self.history_list.insert(tk.END, f"{item['date']} - {item['name']} ({item['version']})")
    
    def clear_history_click(self):
        if messagebox.askyesno(get_text("clear_history"), "Clear all history?"):
            clear_history()
            self.load_history()
    
    def export_history(self):
        history = load_history()
        if not history:
            messagebox.showwarning(get_text("ready"), get_text("no_history"))
            return
        
        export_window = tk.Toplevel(self.root)
        export_window.title(get_text("export_history"))
        export_window.geometry("300x200")
        export_window.configure(bg="#1e1e1e")
        
        export_window.transient(self.root)
        export_window.grab_set()
        
        frame = tk.Frame(export_window, bg="#1e1e1e", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        label = tk.Label(frame, text=get_text("select_format"), font=("Segoe UI", 12), bg="#1e1e1e", fg="#ffffff")
        label.pack(pady=(0, 15))
        
        def export_as(fmt):
            if fmt == "txt":
                file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        for item in history:
                            f.write(f"{item['name']}=={item['version']}\n")
            elif fmt == "json":
                file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(history, f, indent=4)
            elif fmt == "csv":
                file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
                if file_path:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write("Date,Package,Version\n")
                        for item in history:
                            f.write(f"{item['date']},{item['name']},{item['version']}\n")
            
            if file_path:
                NotificationManager.send("BI Loader", get_text("export_success"))
                messagebox.showinfo(get_text("export_history"), get_text("export_success"))
                export_window.destroy()
        
        btn_txt = tk.Button(frame, text=get_text("txt_format"), command=lambda: export_as("txt"), font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffffff", activebackground="#3d3d3d", bd=0, padx=20, pady=10, cursor="hand2", relief="flat")
        btn_txt.pack(fill=tk.X, pady=5)
        
        btn_json = tk.Button(frame, text=get_text("json_format"), command=lambda: export_as("json"), font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffffff", activebackground="#3d3d3d", bd=0, padx=20, pady=10, cursor="hand2", relief="flat")
        btn_json.pack(fill=tk.X, pady=5)
        
        btn_csv = tk.Button(frame, text=get_text("csv_format"), command=lambda: export_as("csv"), font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffffff", activebackground="#3d3d3d", bd=0, padx=20, pady=10, cursor="hand2", relief="flat")
        btn_csv.pack(fill=tk.X, pady=5)
    
    def show_pypi_search(self):
        search_window = tk.Toplevel(self.root)
        search_window.title(get_text("search_pypi"))
        search_window.geometry("500x450")
        search_window.configure(bg="#1e1e1e")
        
        search_window.transient(self.root)
        search_window.grab_set()
        
        frame = tk.Frame(search_window, bg="#1e1e1e", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        hint_label = tk.Label(frame, text=get_text("search_hint"), font=("Segoe UI", 10), bg="#1e1e1e", fg="#808080")
        hint_label.pack(pady=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(frame, textvariable=self.search_var, font=("Segoe UI", 12), bg="#2d2d2d", fg="#ffffff", insertbackground="white", relief="flat", bd=0)
        search_entry.pack(fill=tk.X, ipadx=10, ipady=8, pady=(0, 10))
        
        def do_search():
            query = self.search_var.get().strip()
            if not query:
                return
            
            results_list.delete(0, tk.END)
            results_list.insert(tk.END, "Searching...")
            search_window.update()
            
            results = self.installer.search_pypi(query)
            
            results_list.delete(0, tk.END)
            
            if not results:
                results_list.insert(tk.END, get_text("no_results"))
            else:
                for r in results:
                    name = r.get('name', 'unknown')
                    version = r.get('version', 'unknown')
                    results_list.insert(tk.END, f"{name} ({version})")
        
        search_btn = tk.Button(frame, text=get_text("search"), command=do_search, font=("Segoe UI", 11, "bold"), bg="#FF9800", fg="#ffffff", activebackground="#F57C00", bd=0, padx=20, pady=8, cursor="hand2", relief="flat")
        search_btn.pack(fill=tk.X, pady=(0, 10))
        
        results_list = tk.Listbox(frame, font=("Segoe UI", 11), bg="#2d2d2d", fg="#ffffff", selectbackground="#FF9800", selectforeground="#ffffff", bd=0, relief="flat")
        results_list.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        def install_selected():
            selection = results_list.curselection()
            if not selection:
                return
            
            pkg_text = results_list.get(selection[0])
            if pkg_text in [get_text("no_results"), "Searching..."]:
                return
            
            pkg_name = pkg_text.split(" (")[0]
            
            search_btn.config(state=tk.DISABLED)
            search_window.update()
            
            success = self.installer.install_from_pypi(pkg_name, callback=self.log)
            
            if success:
                NotificationManager.send("BI Loader", f"{pkg_name} installed")
                self.log(f"✓ {pkg_name} installed from PyPI", "success")
            else:
                self.log(f"✗ Error installing {pkg_name}", "error")
            
            search_btn.config(state=tk.NORMAL)
        
        install_btn = tk.Button(frame, text=get_text("install_selected"), command=install_selected, font=("Segoe UI", 11, "bold"), bg="#4CAF50", fg="#ffffff", activebackground="#45a049", bd=0, padx=20, pady=10, cursor="hand2", relief="flat")
        install_btn.pack(fill=tk.X)
    
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title(get_text("settings"))
        settings_window.geometry("320x400")
        settings_window.resizable(False, False)
        settings_window.configure(bg="#1e1e1e")
        
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        frame = tk.Frame(settings_window, bg="#1e1e1e", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title = tk.Label(frame, text=get_text("settings"), font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="#ffffff")
        title.pack(pady=(0, 20))
        
        settings = load_settings()
        notifications_enabled = settings.get("notifications", True)
        
        self.notif_var = tk.BooleanVar(value=notifications_enabled)
        
        notif_row = tk.Frame(frame, bg="#1e1e1e")
        notif_row.pack(fill=tk.X, pady=(0, 20))
        
        notif_label = tk.Label(notif_row, text=get_text("notifications"), font=("Segoe UI", 12), bg="#1e1e1e", fg="#808080")
        notif_label.pack(side=tk.LEFT)
        
        class ToggleSwitch:
            def __init__(self, parent, var, on_change):
                self.var = var
                self.on_change = on_change
                self.canvas = tk.Canvas(parent, width=40, height=22, bg="#1e1e1e", highlightthickness=0, cursor="hand2")
                self.canvas.pack(side=tk.RIGHT)
                
                self.bg_off = "#4a4a4a"
                self.bg_on = "#2196F3"
                
                self.draw_rounded_rect(1, 1, 39, 21, 10, self.bg_off)
                self.knob = self.canvas.create_oval(3, 3, 19, 19, fill="#ffffff", outline="")
                
                self.canvas.bind("<Button-1>", self.click)
                self.update_state()
            
            def draw_rounded_rect(self, x1, y1, x2, y2, r, color):
                self.canvas.create_arc((x1, y1, x1 + 2*r, y1 + 2*r), start=90, extent=180, fill=color, outline="")
                self.canvas.create_arc((x2 - 2*r, y2 - 2*r, x2, y2), start=270, extent=180, fill=color, outline="")
                self.canvas.create_rectangle((x1 + r, y1, x2 - r, y2), fill=color, outline="")
            
            def click(self, event=None):
                self.var.set(not self.var.get())
                self.update_state()
                self.on_change()
            
            def update_state(self):
                self.canvas.delete("all")
                if self.var.get():
                    self.draw_rounded_rect(1, 1, 39, 21, 10, self.bg_on)
                    self.knob = self.canvas.create_oval(21, 3, 37, 19, fill="#ffffff", outline="")
                else:
                    self.draw_rounded_rect(1, 1, 39, 21, 10, self.bg_off)
                    self.knob = self.canvas.create_oval(3, 3, 19, 19, fill="#ffffff", outline="")
        
        def toggle_notifications():
            settings = load_settings()
            settings["notifications"] = self.notif_var.get()
            save_settings(settings)
        
        toggle = ToggleSwitch(notif_row, self.notif_var, toggle_notifications)
        
        debug_row = tk.Frame(frame, bg="#1e1e1e")
        debug_row.pack(fill=tk.X, pady=(0, 20))
        
        debug_label = tk.Label(debug_row, text=get_text("debug_mode"), font=("Segoe UI", 12), bg="#1e1e1e", fg="#808080")
        debug_label.pack(side=tk.LEFT)
        
        debug_enabled = settings.get("debug_mode", False)
        self.debug_var = tk.BooleanVar(value=debug_enabled)
        
        def toggle_debug():
            settings = load_settings()
            settings["debug_mode"] = self.debug_var.get()
            save_settings(settings)
        
        debug_toggle = ToggleSwitch(debug_row, self.debug_var, toggle_debug)
        
        debug_hint = tk.Label(frame, text=get_text("debug_hint"), font=("Segoe UI", 9), bg="#1e1e1e", fg="#666666")
        debug_hint.pack(anchor="w", pady=(0, 20))
        
        lang_label = tk.Label(frame, text=get_text("language"), font=("Segoe UI", 12), bg="#1e1e1e", fg="#808080")
        lang_label.pack(anchor="w", pady=(0, 10))
        
        lang_frame = tk.Frame(frame, bg="#1e1e1e")
        lang_frame.pack(fill=tk.X, pady=(0, 20))
        
        for lang_code, lang_name in LANGUAGE_NAMES:
            btn = tk.Button(lang_frame, text=lang_name, font=("Segoe UI", 10), bg="#2d2d2d", fg="#ffffff", activebackground="#3d3d3d", activeforeground="#ffffff", bd=0, padx=15, pady=8, cursor="hand2", relief="flat", command=lambda c=lang_code: self.change_language(c, settings_window))
            btn.pack(side=tk.LEFT, padx=(0, 5), expand=True, fill=tk.X)
        
        close_btn = tk.Button(frame, text=get_text("exit"), font=("Segoe UI", 11), bg="#2196F3", fg="#ffffff", activebackground="#1976D2", activeforeground="#ffffff", bd=0, padx=20, pady=10, cursor="hand2", relief="flat", command=settings_window.destroy)
        close_btn.pack(fill=tk.X, pady=(20, 0))

    def change_language(self, lang, settings_window=None):
        if settings_window:
            settings_window.destroy()
        settings = load_settings()
        settings["language"] = lang
        save_settings(settings)
        self.root.destroy()
        main()


def main():
    splash = SplashScreen(lambda: after_splash())
    splash.window.mainloop()


def after_splash():
    settings = load_settings()
    
    if settings.get("first_run", True):
        if DND_AVAILABLE:
            root = TkinterDnD.Tk()
        else:
            root = tk.Tk()
        root.withdraw()
        LanguageScreen(lambda: root.destroy() or run_main_app())
        root.mainloop()
    else:
        run_main_app()


def run_main_app():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = BILoaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
