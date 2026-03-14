import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import tkinter.ttk as ttk
import threading
from pathlib import Path
from installer import WheelInstaller


class BILoaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BI Loader - Установщик WHL пакетов")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        self.installer = WheelInstaller()
        self.selected_files = []
        
        self._create_ui()

    def _create_ui(self):
        main_frame = tk.Frame(self.root, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = tk.Label(
            main_frame, 
            text="BI Loader", 
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_label = tk.Label(
            main_frame, 
            text="Установщик Python WHL пакетов", 
            font=("Segoe UI", 10),
            fg="gray"
        )
        subtitle_label.pack(pady=(0, 15))

        select_frame = tk.Frame(main_frame)
        select_frame.pack(fill=tk.X, pady=10)

        self.btn_select = tk.Button(
            select_frame,
            text="📁 Выбрать WHL файлы",
            command=self.select_files,
            font=("Segoe UI", 11),
            padx=20,
            pady=8,
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            bd=0,
            cursor="hand2"
        )
        self.btn_select.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_clear = tk.Button(
            select_frame,
            text="🗑 Очистить",
            command=self.clear_files,
            font=("Segoe UI", 10),
            padx=15,
            pady=8,
            bg="#f44336",
            fg="white",
            activebackground="#d32f2f",
            activeforeground="white",
            bd=0,
            cursor="hand2"
        )
        self.btn_clear.pack(side=tk.LEFT)

        self.files_label = tk.Label(
            main_frame,
            text="Файлы не выбраны",
            font=("Segoe UI", 9),
            fg="gray",
            anchor="w"
        )
        self.files_label.pack(fill=tk.X, pady=(0, 10))

        self.btn_install = tk.Button(
            main_frame,
            text="🚀 Установить пакеты",
            command=self.start_installation,
            font=("Segoe UI", 12, "bold"),
            padx=30,
            pady=12,
            bg="#2196F3",
            fg="white",
            activebackground="#1976D2",
            activeforeground="white",
            bd=0,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_install.pack(fill=tk.X, pady=(0, 10))

        self.progress_frame = tk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Segoe UI", 9),
            fg="gray"
        )
        self.progress_label.pack(side=tk.TOP, anchor="w")

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=100
        )
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))

        log_frame = tk.LabelFrame(main_frame, text="Лог установки", font=("Segoe UI", 10))
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

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

    def select_files(self):
        file_types = [("WHL файлы", "*.whl")]
        files = filedialog.askopenfilenames(
            title="Выберите WHL файлы",
            filetypes=file_types
        )
        
        if files:
            self.selected_files = list(files)
            files_count = len(self.selected_files)
            self.files_label.config(
                text=f"Выбрано файлов: {files_count} | {', '.join([Path(f).name for f in files[:3]])}{'...' if files_count > 3 else ''}"
            )
            self.btn_install.config(state=tk.NORMAL)

    def clear_files(self):
        self.selected_files = []
        self.files_label.config(text="Файлы не выбраны")
        self.btn_install.config(state=tk.DISABLED)

    def log(self, message, tag=None):
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        self.root.update()

    def start_installation(self):
        if not self.selected_files:
            return

        self.btn_install.config(state=tk.DISABLED)
        self.btn_select.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.progress_label.config(text="Подготовка к установке...")
        self.log("=" * 50, "info")
        self.log("Начало установки пакетов...", "info")
        self.log("=" * 50, "info")

        thread = threading.Thread(target=self._install_worker, daemon=True)
        thread.start()

    def _install_worker(self):
        total = len(self.selected_files)
        
        for i, whl_file in enumerate(self.selected_files, 1):
            progress_percent = ((i - 1) / total) * 100
            self.root.after(0, lambda p=progress_percent: self.progress_bar.config(value=p))
            self.root.after(0, lambda: self.progress_label.config(
                text=f"Установка {i} из {total}: {Path(whl_file).name}"
            ))
            self.root.after(0, lambda: self.log(f"\n--- Пакет {i}/{total} ---", "info"))
            
            success = self.installer.install_whl(whl_file, callback=self.log)
            
            if success:
                self.root.after(0, lambda: self.log(f"✓ Установка завершена", "success"))
            else:
                self.root.after(0, lambda: self.log(f"✗ Ошибка установки", "error"))

        self.root.after(0, lambda: self.progress_bar.config(value=100))
        self.root.after(0, self._installation_complete)

    def _installation_complete(self):
        self.progress_label.config(text="Установка завершена!")
        self.btn_install.config(state=tk.NORMAL)
        self.btn_select.config(state=tk.NORMAL)
        
        self.log("\n" + "=" * 50, "info")
        self.log("✓ Все операции завершены!", "success")
        self.log("=" * 50, "info")
        
        messagebox.showinfo("Готово", "Установка пакетов завершена!")


def main():
    root = tk.Tk()
    
    try:
        root.iconname("BI Loader")
    except:
        pass
    
    app = BILoaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
