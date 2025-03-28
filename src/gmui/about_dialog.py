"""「关于」对话框之定义。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout


class AboutDialog(QDialog):
    """「关于」对话框。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("关于家谱通")

        layout = QVBoxLayout()
        layout.setSpacing(20)

        title = QLabel(self.tr("<b><big>家谱通</big><br/>Genealogy Manager</b>"))
        font = title.font()
        font.setPointSize(font.pointSize() + 2)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(self.tr("开源的家谱管理软件，基于 Python 和 Qt 6 (PySide6)。"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        links = QLabel(
            self.tr(
                '<a href="https://github.com/zyxir/genealogy-manager">GitHub 主页</a>'
                "&nbsp;&nbsp;&nbsp;&nbsp;"
                '<a href="https://baike.baidu.com/item/%E5%AE%B6%E8%B0%B1/607190">家谱-百度百科</a>'
            )
        )
        links.setOpenExternalLinks(True)
        links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(links)

        author = QLabel(
            "@2025 陈卓 (Eric Zhuo Chen)<br>"
            "&lt;<a href=mailto:ericzhuochen@outlook.com>"
            "ericzhuochen@outlook.com</a>&gt;"
        )
        author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        layout.addWidget(ok_button)

        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())
