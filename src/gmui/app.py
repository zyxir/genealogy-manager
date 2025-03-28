"""应用及相关配置定义。"""

import sys
from typing import Sequence

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


class App(QApplication):
    """家谱通应用程序。"""

    def __init__(self, arguments: Sequence[str] = sys.argv):
        super().__init__(arguments)

        # 程序默认字体
        font = QFont()
        font.setStyleHint(QFont.StyleHint.SansSerif)
        font.setPointSize(11)
        self.setFont(font)

        # 设置信息从而获得设置保存路径
        self.setOrganizationName("Zyxir")
        self.setOrganizationDomain("ericzhuochen.com")
        self.setApplicationName("Genealogy Manager")
