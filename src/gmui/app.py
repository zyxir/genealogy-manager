"""应用及相关配置定义。"""

import sys
from typing import Any, Sequence

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QApplication


class AppColors:
    """用于整个应用的颜色。"""
    # 被选中/焦点
    FOCUS = QColor("darkcyan")
    # 普通边框/线
    LINE = QColor("black")
    # 普通填充色
    FILL = QColor("white")
    # 悬停填充色
    HOVER = QColor("lightblue")
    # 画布背景色一
    BG1 = QColor("#f0f0f0")
    # 画布背景色二
    BG2 = QColor("#d5d5d5")


class AppFonts:
    """用于整个应用的字体。"""

    @classmethod
    def main_font(cls, extra_point: float = 0, bold: bool = False):
        """主字体，无衬线体。"""
        font = QFont()
        font.setStyleHint(QFont.StyleHint.SansSerif)
        font.setPointSizeF(11 + extra_point)
        if bold:
            font.setBold(True)
        return font

    @classmethod
    def name_font(cls, extra_point: float = 0, bold: bool = False):
        """名字字体，中文用楷体，英文用 Times New Roman。"""
        font = QFont(["KaiTi_GB2312", "KaiTi", "Times New Roman"])
        font.setStyleHint(QFont.StyleHint.Serif)
        font.setPointSizeF(12 + extra_point)
        if bold:
            font.setBold(True)
        return font


class Debuggable:
    """可以设置 debug 信息的组件。"""

    def __init__(self):
        self._debug_info: dict[str, Any] = {}

    def set_debug_info(self, **kwargs):
        """设置 debug 信息。"""
        self._debug_info.update(kwargs)

    def get_debug_str(self) -> str:
        """获取 debug 信息为字符串。"""
        ...


class App(QApplication):
    """家谱通应用程序。"""

    def __init__(self, arguments: Sequence[str] = sys.argv):
        super().__init__(arguments)

        # 程序默认字体
        self.setFont(AppFonts.main_font())

        # 设置信息从而获得设置保存路径
        self.setOrganizationName("Zyxir")
        self.setOrganizationDomain("ericzhuochen.com")
        self.setApplicationName("Genealogy Manager")
