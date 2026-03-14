import json
import os
from pathlib import Path
from datetime import datetime


TRANSLATIONS = {
    "en": {
        "app_title": "BI Loader - WHL Package Manager",
        "title": "BI Loader",
        "subtitle": "Python Package Manager",
        
        # Tabs
        "tab_install": "📥 Install",
        "tab_uninstall": "🗑 Uninstall",
        "tab_update": "🔄 Update",
        "tab_history": "📜 History",
        
        # Install tab
        "select_files": "📁 Select WHL Files",
        "clear": "🗑 Clear",
        "files_not_selected": "No files selected",
        "files_selected": "Files selected: {count} | {names}",
        "install": "🚀 Install Packages",
        "drop_zone": "📂 Drag & Drop WHL files here\nor use buttons below",
        "added_files": "Added {count} file(s)",
        
        # Validation
        "validation_results": "Validation Results",
        "continue": "Continue",
        "ok": "OK",
        
        # Uninstall tab
        "installed_packages": "Installed Packages",
        "uninstall": "🗑 Uninstall",
        "refresh": "🔄 Refresh",
        "search_package": "Search package...",
        "no_installed": "No packages found",
        "confirm_uninstall": "Uninstall {package}?",
        "uninstall_success": "✓ {package} uninstalled",
        "uninstall_error": "✗ Error uninstalling {package}",
        
        # Update tab
        "check_updates": "🔍 Check Updates",
        "update": "🔄 Update",
        "update_all": "🔄 Update All",
        "current_version": "Current",
        "latest_version": "Latest",
        "no_updates": "All packages are up to date",
        "update_success": "✓ {package} updated",
        "update_error": "✗ Error updating {package}",
        
        # History tab
        "history": "Installation History",
        "no_history": "No installation history",
        "date": "Date",
        "package": "Package",
        "version": "Version",
        "clear_history": "🗑 Clear History",
        
        # Common
        "log_frame": "Log",
        "settings": "Settings",
        "language": "Language",
        "theme": "Theme",
        "dark": "Dark",
        "light": "Light",
        "file": "File",
        "exit": "Exit",
        "about": "About",
        "version": "Version",
        "choose_language": "Choose Language",
        "welcome": "Welcome to BI Loader",
        "preparing": "Preparing...",
        "installing": "Installing {i} of {total}...",
        "installing_package": "Installing package {i}/{total}",
        "install_success": "✓ Installation complete",
        "install_error": "✗ Installation error",
        "complete": "All operations completed!",
        "ready": "Ready",
        "no_files": "No files selected",
        "processing": "Processing...",
        "select_package": "Select a package",
        "cancel": "Cancel",
        "ok": "OK",
        "yes": "Yes",
        "no": "No",
        "validation_results": "Validation Results",
        "continue": "Continue"
    },
    "zh": {
        "app_title": "BI Loader - WHL 包管理器",
        "title": "BI Loader",
        "subtitle": "Python 包管理器",
        
        # Tabs
        "tab_install": "📥 安装",
        "tab_uninstall": "🗑 卸载",
        "tab_update": "🔄 更新",
        "tab_history": "📜 历史",
        
        # Install tab
        "select_files": "📁 选择 WHL 文件",
        "clear": "🗑 清除",
        "files_not_selected": "未选择文件",
        "files_selected": "已选择: {count} | {names}",
        "install": "🚀 安装包",
        "drop_zone": "📂 将 WHL 文件拖放到此处\n或使用下方按钮",
        "added_files": "已添加 {count} 个文件",
        
        # Uninstall tab
        "installed_packages": "已安装的包",
        "uninstall": "🗑 卸载",
        "refresh": "🔄 刷新",
        "search_package": "搜索包...",
        "no_installed": "未找到包",
        "confirm_uninstall": "卸载 {package}？",
        "uninstall_success": "✓ {package} 已卸载",
        "uninstall_error": "✗ 卸载 {package} 错误",
        
        # Update tab
        "check_updates": "🔍 检查更新",
        "update": "🔄 更新",
        "update_all": "🔄 更新全部",
        "current_version": "当前",
        "latest_version": "最新",
        "no_updates": "所有包都是最新的",
        "update_success": "✓ {package} 已更新",
        "update_error": "✗ 更新 {package} 错误",
        
        # History tab
        "history": "安装历史",
        "no_history": "没有安装历史",
        "date": "日期",
        "package": "包",
        "version": "版本",
        "clear_history": "🗑 清除历史",
        
        # Common
        "log_frame": "日志",
        "settings": "设置",
        "language": "语言",
        "theme": "主题",
        "dark": "深色",
        "light": "浅色",
        "file": "文件",
        "exit": "退出",
        "about": "关于",
        "version": "版本",
        "choose_language": "选择语言",
        "welcome": "欢迎使用 BI Loader",
        "preparing": "准备中...",
        "installing": "正在安装 {i} / {total}...",
        "installing_package": "正在安装第 {i}/{total} 个包",
        "install_success": "✓ 安装完成",
        "install_error": "✗ 安装错误",
        "complete": "所有操作已完成！",
        "ready": "就绪",
        "no_files": "未选择文件",
        "processing": "处理中...",
        "select_package": "选择一个包",
        "cancel": "取消",
        "ok": "确定",
        "yes": "是",
        "no": "否",
        "validation_results": "验证结果",
        "continue": "继续"
    },
    "ru": {
        "app_title": "BI Loader - Менеджер WHL пакетов",
        "title": "BI Loader",
        "subtitle": "Менеджер Python пакетов",
        
        # Tabs
        "tab_install": "📥 Установить",
        "tab_uninstall": "🗑 Удалить",
        "tab_update": "🔄 Обновить",
        "tab_history": "📜 История",
        
        # Install tab
        "select_files": "📁 Выбрать WHL файлы",
        "clear": "🗑 Очистить",
        "files_not_selected": "Файлы не выбраны",
        "files_selected": "Выбрано файлов: {count} | {names}",
        "install": "🚀 Установить пакеты",
        "drop_zone": "📂 Перетащите WHL файлы сюда\nили используйте кнопки ниже",
        "added_files": "Добавлено {count} файл(ов)",
        
        # Uninstall tab
        "installed_packages": "Установленные пакеты",
        "uninstall": "🗑 Удалить",
        "refresh": "🔄 Обновить",
        "search_package": "Поиск пакета...",
        "no_installed": "Пакеты не найдены",
        "confirm_uninstall": "Удалить {package}?",
        "uninstall_success": "✓ {package} удалён",
        "uninstall_error": "✗ Ошибка удаления {package}",
        
        # Update tab
        "check_updates": "🔍 Проверить обновления",
        "update": "🔄 Обновить",
        "update_all": "🔄 Обновить все",
        "current_version": "Текущая",
        "latest_version": "Последняя",
        "no_updates": "Все пакеты обновлены",
        "update_success": "✓ {package} обновлён",
        "update_error": "✗ Ошибка обновления {package}",
        
        # History tab
        "history": "История установок",
        "no_history": "История пуста",
        "date": "Дата",
        "package": "Пакет",
        "version": "Версия",
        "clear_history": "🗑 Очистить историю",
        
        # Common
        "log_frame": "Лог",
        "settings": "Настройки",
        "language": "Язык",
        "theme": "Тема",
        "dark": "Тёмная",
        "light": "Светлая",
        "file": "Файл",
        "exit": "Выход",
        "about": "О программе",
        "version": "Версия",
        "choose_language": "Выберите язык",
        "welcome": "Добро пожаловать в BI Loader",
        "preparing": "Подготовка...",
        "installing": "Установка {i} из {total}...",
        "installing_package": "Установка пакета {i}/{total}",
        "install_success": "✓ Установка завершена",
        "install_error": "✗ Ошибка установки",
        "complete": "Все операции завершены!",
        "ready": "Готов",
        "no_files": "Файлы не выбраны",
        "processing": "Обработка...",
        "select_package": "Выберите пакет",
        "cancel": "Отмена",
        "ok": "ОК",
        "yes": "Да",
        "no": "Нет",
        "validation_results": "Результаты проверки",
        "continue": "Продолжить"
    }
}

LANGUAGE_NAMES = [
    ("en", "English"),
    ("ru", "Русский"),
    ("zh", "中文")
]

DEFAULT_SETTINGS = {
    "language": "en",
    "first_run": True
}


def get_settings_path():
    app_dir = Path(__file__).parent
    return app_dir / "settings.json"


def get_history_path():
    app_dir = Path(__file__).parent
    return app_dir / "history.json"


def load_settings():
    settings_path = get_settings_path()
    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    settings_path = get_settings_path()
    try:
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except:
        pass


def load_history():
    history_path = get_history_path()
    if history_path.exists():
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def save_history(history):
    history_path = get_history_path()
    try:
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except:
        pass


def add_to_history(package_name, version, whl_path=None):
    history = load_history()
    history.insert(0, {
        "name": package_name,
        "version": version,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "whl": whl_path
    })
    if len(history) > 100:
        history = history[:100]
    save_history(history)


def clear_history():
    save_history([])


def get_text(key, lang=None):
    settings = load_settings()
    if lang is None:
        lang = settings.get("language", "en")
    
    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return translations.get(key, key)


def format_text(key, lang=None, **kwargs):
    text = get_text(key, lang)
    try:
        return text.format(**kwargs)
    except:
        return text


def get_current_language():
    settings = load_settings()
    return settings.get("language", "en")
