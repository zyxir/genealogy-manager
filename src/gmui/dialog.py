"""各种对话框定义。"""

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ErrorDialog(QDialog):
    """错误提示对话框。"""

    def __init__(self, title: str, info: str):
        super().__init__()
        self.setWindowTitle(title)

        layout = QVBoxLayout()

        label = QLabel(info)
        layout.addWidget(label)

        ok_button = QPushButton(self.tr("OK"))
        ok_button.clicked.connect(self.close)
        layout.addWidget(ok_button)

        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())


def error_dialog(title: str, info: str):
    """用对话框提示错误。"""
    ErrorDialog(title, info).exec()


class ConfirmationDialog(QDialog):
    """确定对话框。"""

    # 确认结果
    confirmed: bool

    def __init__(self, title: str, info: str):
        super().__init__()
        self.confirmed = False
        self.setWindowTitle(title)

        layout = QVBoxLayout()

        label = QLabel(info)
        layout.addWidget(label)

        btns_layout = QHBoxLayout()
        yes_btn = QPushButton(self.tr("确认"))
        yes_btn.clicked.connect(self._yes)
        btns_layout.addWidget(yes_btn)
        no_btn = QPushButton(self.tr("取消"))
        no_btn.clicked.connect(self._no)
        btns_layout.addWidget(no_btn)

        btns = QWidget()
        btns.setLayout(btns_layout)
        layout.addWidget(btns)

        self.setLayout(layout)
        self.adjustSize()
        self.setFixedSize(self.size())

    def _yes(self):
        self.confirmed = True
        self.close()

    def _no(self):
        self.confirmed = False
        self.close()


def confirmation_dialog(title: str, info: str) -> bool:
    """用对话框询问用户是否要进行某操作。"""
    dialog = ConfirmationDialog(title, info)
    dialog.exec()
    return dialog.confirmed
