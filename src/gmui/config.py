"""程序配置管理。"""

from PySide6.QtCore import QSettings


def get_recent_files() -> list[str]:
    """获取最近打开文件列表。"""
    settings = QSettings()
    recent_files = settings.value("recentFiles")
    if recent_files is None:
        return []
    elif isinstance(recent_files, list):
        return recent_files
    else:
        raise ValueError("invalid recent file list")


def add_recent_file(fpath: str):
    """添加文件到最近文件列表。"""
    recent_files = get_recent_files()
    settings = QSettings()
    if fpath in recent_files:
        recent_files.remove(fpath)
        recent_files = [fpath] + recent_files
        settings.setValue("recentFiles", recent_files)
    else:
        recent_files = ([fpath] + recent_files)[:5]
        settings.setValue("recentFiles", recent_files)
