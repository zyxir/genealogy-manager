"""错误提示对话框定义。"""


from PySide6.QtWidgets import QPushButton, QVBoxLayout, QDialog, QLabel


class ErrorDialog(QDialog):
    """错误提示对话框。"""

    def __init__(self, title: str, info: str):
        super().__init__()
        self.setWindowTitle(title)

        layout = QVBoxLayout()

        label = QLabel(info)
        layout.addWidget(label)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        layout.addWidget(ok_button)

        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())

def error_dialog(title: str, info: str):
    """用对话框提示错误。"""
    ErrorDialog(title, info).exec()
