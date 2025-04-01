"""信息侧栏。"""

from typing import ClassVar, Optional, Tuple

from gmlib import Card
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QFont, QTextDocument, Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from gmui.app import AppFonts


class YearsDisplay(QWidget):
    """生卒年展示组件。"""

    def __init__(self, font: QFont):
        super().__init__()
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._birth_year = QLabel()
        self._birth_year.setFont(font)
        layout.addWidget(self._birth_year)

        _separator = QLabel("\u2013")
        _separator.setFont(font)
        layout.addWidget(_separator)

        self._death_year = QLabel()
        self._death_year.setFont(font)
        layout.addWidget(self._death_year)

        self.setLayout(layout)

    def set_years(self, birth_year: Optional[int], death_year: Optional[int]):
        """设置生卒年。"""
        if birth_year is None and death_year is None:
            self.setVisible(False)
        else:
            self.setVisible(True)
            if birth_year is None:
                self._birth_year.setText("    ")
            else:
                self._birth_year.setText(str(birth_year))
            if death_year is None:
                self._death_year.setText("    ")
            else:
                self._death_year.setText(str(death_year))


class YearsEdit(QWidget):
    """生卒年编辑组件。"""

    def __init__(self, font: QFont):
        super().__init__()
        layout = QHBoxLayout()

        _indicator = QLabel(self.tr("生卒年:"))
        layout.addWidget(_indicator)

        self._birth_year = QLineEdit()
        self._birth_year.setFont(font)
        layout.addWidget(self._birth_year)

        _separator = QLabel("\u2013")
        _separator.setFont(font)
        layout.addWidget(_separator)

        self._death_year = QLineEdit()
        self._death_year.setFont(font)
        layout.addWidget(self._death_year)

        self.setLayout(layout)

    def set_years(self, birth_year: Optional[int], death_year: Optional[int]):
        """设置生卒年。"""
        if birth_year is None:
            self._birth_year.setText("    ")
        else:
            self._birth_year.setText(str(birth_year))
        if death_year is None:
            self._death_year.setText("    ")
        else:
            self._death_year.setText(str(death_year))

    def get_years(self) -> Tuple[Optional[int], Optional[int]]:
        """获取生卒年。"""
        try:
            birth_year = int(self._birth_year.text())
        except Exception:
            birth_year = None
        try:
            death_year = int(self._death_year.text())
        except Exception:
            death_year = None
        return (birth_year, death_year)


class CardDisplay(QWidget):
    """名片展示组件。"""

    # 姓名字体
    NAME_FONT = AppFonts.name_font(extra_point=7, bold=True)
    # 生卒年字体
    YEAR_FONT = AppFonts.main_font(extra_point=3)

    # 「编辑」按钮
    edit_btn: QPushButton
    # 「关闭」按钮
    close_btn: QPushButton

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 姓名
        self._name = QLabel()
        self._name.setFont(CardDisplay.NAME_FONT)
        self._name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._name)

        # 生卒年
        self._years = YearsDisplay(CardDisplay.YEAR_FONT)
        layout.addWidget(self._years)

        # 生平
        _bio_indicator = QLabel("- 生平 -")
        _bio_indicator.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(_bio_indicator)
        self._bio = QLabel()
        self._bio.setWordWrap(True)
        layout.addWidget(self._bio)

        # 「编辑」按钮
        self.edit_btn = QPushButton(self.tr("编辑"))
        layout.addWidget(self.edit_btn)

        # 「关闭」按钮
        self.close_btn = QPushButton(self.tr("关闭"))
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    def display_card(self, card: Card):
        """展示某名片。"""
        self._name.setText(card.name)
        self._years.set_years(card.birth_year, card.death_year)
        self._bio.setText(card.bio)
        # 生平的文字总是无法完全显示，只好手动计算其高度并手动设置
        self._bio.setFixedHeight(CardDisplay._get_minimum_height(self._bio))

    @classmethod
    def _get_minimum_height(cls, label: QLabel) -> int:
        doc = QTextDocument()
        doc.setHtml(label.text())
        doc.setTextWidth(label.width())
        doc.setDefaultFont(label.font())
        return round(doc.size().height())


class CardEdit(QFrame):
    """名片编辑组件。"""

    # 「保存」按钮
    save_btn: QPushButton
    # 「放弃编辑」按钮
    discard_btn: QPushButton
    # 「关闭」按钮
    close_btn: QPushButton

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 姓名
        name_widget = QWidget()
        name_widget_layout = QHBoxLayout()
        _name_indicator = QLabel(self.tr("姓名:"))
        name_widget_layout.addWidget(_name_indicator)
        self._name = QLineEdit()
        self._name.setFont(CardDisplay.NAME_FONT)
        self._name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        name_widget_layout.addWidget(self._name)
        name_widget.setLayout(name_widget_layout)
        layout.addWidget(name_widget)

        # 生卒年
        self._years = YearsEdit(CardDisplay.YEAR_FONT)
        layout.addWidget(self._years)

        # 生平
        _bio_indicator = QLabel("- 生平 -")
        _bio_indicator.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(_bio_indicator)
        self._bio = QTextEdit()
        layout.addWidget(self._bio)

        # 「保存」按钮
        self.save_btn = QPushButton(self.tr("保存"))
        layout.addWidget(self.save_btn)

        # 「放弃编辑」按钮
        self.discard_btn = QPushButton(self.tr("放弃编辑"))
        layout.addWidget(self.discard_btn)

        # 「关闭」按钮
        self.close_btn = QPushButton(self.tr("关闭"))
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    def edit_card(self, card: Card):
        """编辑某名片。"""
        self._name.setText(card.name)
        self._years.set_years(card.birth_year, card.death_year)
        self._bio.setHtml(card.bio)

    def get_card(self) -> Card:
        """获取编辑后的名片。"""
        name = self._name.text()
        birth_year, death_year = self._years.get_years()
        bio = self._bio.document().toHtml()
        card = Card(name=name, birth_year=birth_year, death_year=death_year, bio=bio)
        return card


class InfoDock(QDockWidget):
    """家族成员信息显示侧栏。"""

    # 固定宽度
    WIDTH: ClassVar[int] = 350

    # 「名片已关闭」信号
    card_closed = Signal()
    # 「名片已完成编辑」信号
    card_edited = Signal(Card)

    # 当前展示的名片
    _card: Card

    def __init__(self):
        super().__init__()
        self._card = Card()
        self.setWindowTitle(self.tr("家族成员信息"))
        self.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.setFixedWidth(InfoDock.WIDTH)

        # 可以在空组件、信息展示组件和信息编辑组件间切换
        self.empty_widget = QWidget()
        self.card_display = CardDisplay()
        self.card_display.edit_btn.clicked.connect(self.edit_card)
        self.card_display.close_btn.clicked.connect(self.close_card)
        self.card_edit = CardEdit()
        self.card_edit.save_btn.clicked.connect(self.save_card)
        self.card_edit.discard_btn.clicked.connect(self.discard_edits)
        self.card_edit.close_btn.clicked.connect(self.close_card)
        self.setWidget(self.empty_widget)

    def display_card(self, card: Card):
        """开始展示某名片。"""
        self._card = card
        self.setWidget(self.card_display)
        self.card_display.display_card(card)

    def edit_card(self):
        """开始编辑展示的名片。"""
        self.setWidget(self.card_edit)
        self.card_edit.edit_card(self._card)

    def save_card(self):
        """保存对某名片的编辑，发射相关信号。"""
        card = self.card_edit.get_card()
        self._card = card
        self.setWidget(self.card_display)
        self.card_display.display_card(card)
        self.card_edited.emit(card)

    def discard_edits(self):
        """放弃所有编辑，回到展示状态。"""
        self.setWidget(self.card_display)

    def close_card(self):
        """关闭当前名片，并发送相关信号。"""
        self.setWidget(self.empty_widget)
        self.card_closed.emit()
