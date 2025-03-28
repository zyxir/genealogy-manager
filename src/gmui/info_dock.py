"""信息侧栏。"""

from typing import ClassVar, Optional

from gmlib.models import Node
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class InfoArea(QWidget):
    """家族成员信息区，作为侧栏的内容组件。"""

    def __init__(self, node: Node, parent: QWidget):
        super().__init__()
        self.setParent(parent)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        name = QLabel(f"<h2>{node.card.name}</h2>")
        name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(name)

        def year_text(year: Optional[int]) -> str:
            if year is None:
                return self.tr("未知")
            else:
                return str(year)

        years = QLabel(
            "<h2>{}–{}</h2>".format(
                year_text(node.card.birth_year), year_text(node.card.death_year)
            )
        )
        years.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(years)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        bio_title = QLabel(self.tr("<h3>生平</h3>"))
        bio_title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(bio_title)

        biography = QLabel(node.card.biography)
        layout.addWidget(biography)

        self.setLayout(layout)


class InfoDock(QDockWidget):
    """家族成员信息显示侧栏。"""

    # 最小宽度
    MIN_WIDTH: ClassVar[int] = 250

    def __init__(self):
        super().__init__()
        self.setFeatures(
            ~QDockWidget.DockWidgetFeature.DockWidgetClosable
            & ~QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(InfoDock.MIN_WIDTH)
        self.setVisible(False)

    def view_node(self, node: Node):
        """查看某一家谱树节点。"""
        if self.widget() is not None:
            self.widget().destroy()
        info_area = InfoArea(node, self)
        self.setWidget(info_area)
        self.setVisible(True)
