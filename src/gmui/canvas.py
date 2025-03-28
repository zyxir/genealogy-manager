"""家谱树显示区域。"""

from typing import ClassVar, Optional

from gmlib.models import Node, Tree
from PySide6.QtCore import QRectF, Signal
from PySide6.QtGui import QBrush, QPen, Qt
from PySide6.QtWidgets import (
    QGraphicsItemGroup,
    QGraphicsLineItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QGraphicsTextItem,
    QGraphicsView,
)

from gmui.app import AppColors


class SignalScene(QGraphicsScene):
    """支持点击信号的 scene。"""

    # 被点击信号
    clicked = Signal(object)


class Box(QGraphicsItemGroup):
    """代表家谱树节点的方块。

    继承 QObject 方可使用信号。
    """

    # 宽度
    WIDTH: ClassVar[int] = 30
    # 高度
    HEIGHT: ClassVar[int] = 60
    # 普通填充
    NORMAL_BRUSH: ClassVar[QBrush] = QBrush(AppColors.FILL)
    # 鼠标悬浮填充
    HOVER_BRUSH: ClassVar[QBrush] = QBrush(AppColors.HOVER)
    # 普通边框
    NORMAL_PEN: ClassVar[QPen] = QPen(AppColors.LINE, 1)
    # 被查看时的边框
    INSPECTED_PEN: ClassVar[QPen] = QPen(AppColors.FOCUS, 4)

    # 对应的树节点
    node: Node
    # 矩形边框
    rect: QGraphicsRectItem
    # 文字
    text: QGraphicsTextItem
    # 是否正在被查看
    inspected: bool
    # 所在的 SignalScene
    signal_scene: SignalScene

    def __init__(self, x: float, y: float, node: Node, signal_scene: SignalScene):
        super().__init__()
        self.node = node
        self.inspected = False
        self.signal_scene = signal_scene

        # 矩形边框
        self.rect = QGraphicsRectItem(QRectF(0, 0, Box.WIDTH, Box.HEIGHT))
        self.rect.setBrush(Box.NORMAL_BRUSH)
        self.rect.setPen(Box.NORMAL_PEN)

        # 文字
        self.text = QGraphicsTextItem(node.card.name)
        self.text.setPos(
            (Box.WIDTH - self.text.boundingRect().width()) / 2,
            (Box.HEIGHT - self.text.boundingRect().height()) / 2,
        )

        # 整体设置位置
        self.addToGroup(self.rect)
        self.addToGroup(self.text)
        self.setPos(x - Box.WIDTH / 2, y - Box.HEIGHT / 2)

        # 接受鼠标悬停事件
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self.rect.setBrush(Box.HOVER_BRUSH)
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self.rect.setBrush(Box.NORMAL_BRUSH)
        return super().hoverLeaveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.signal_scene.clicked.emit(self)
        return super().mousePressEvent(event)

    def inspect(self):
        """进入被查看状态。"""
        self.inspected = True
        self.rect.setPen(Box.INSPECTED_PEN)

    def uninspect(self):
        """取消被查看状态。"""
        self.inspected = False
        self.rect.setPen(Box.NORMAL_PEN)


class Canvas(QGraphicsView):
    """家谱树显示区域。"""

    # 方块横向间距
    BOX_SPACING: ClassVar[float] = Box.WIDTH * 1.5
    # 层距
    LAYER_SPACING: ClassVar[float] = Box.HEIGHT * 2

    # 查看节点信号
    view_node = Signal(Node)

    # 所有方块的列表
    boxes: list[Box]
    # 所有连线的列表
    lines: list[QGraphicsLineItem]
    # 当前查看的方块
    inspected_box: Optional[Box]
    # 可发信号的 scene
    signal_scene: SignalScene

    def __init__(self):
        super().__init__()
        self.boxes = []
        self.lines = []
        self.inspected_box = None
        self.signal_scene = SignalScene()
        self.signal_scene.clicked.connect(self.clicked_slot)
        self.setScene(self.signal_scene)

    def sync_tree(self, tree: Tree):
        """根据家谱树更新图形。"""

        # TODO 解决 box 复用问题

        # 更新家谱树的绘图坐标，并重绘所有元素
        for line in self.lines:
            self.signal_scene.removeItem(line)
            del line
        tree.update_xs()
        for i, layer in enumerate(tree.layers):
            for node in layer:
                # 绘制向上的连线
                if node.parent is not None:
                    self.lines.append(
                        self.signal_scene.addLine(
                            node.draw.x * Canvas.BOX_SPACING,
                            i * Canvas.LAYER_SPACING,
                            node.draw.x * Canvas.BOX_SPACING,
                            (i - 0.5) * Canvas.LAYER_SPACING,
                            QPen(AppColors.LINE, 1),
                        )
                    )
                # 绘制向下的连线
                if len(node.children) > 0:
                    self.lines.append(
                        self.signal_scene.addLine(
                            node.draw.x * Canvas.BOX_SPACING,
                            i * Canvas.LAYER_SPACING,
                            node.draw.x * Canvas.BOX_SPACING,
                            (i + 0.5) * Canvas.LAYER_SPACING,
                            QPen(AppColors.LINE, 1),
                        )
                    )
                if len(node.children) > 1:
                    lchild, rchild = node.children[0], node.children[-1]
                    self.lines.append(
                        self.signal_scene.addLine(
                            lchild.draw.x * Canvas.BOX_SPACING,
                            (i + 0.5) * Canvas.LAYER_SPACING,
                            rchild.draw.x * Canvas.BOX_SPACING,
                            (i + 0.5) * Canvas.LAYER_SPACING,
                            QPen(AppColors.LINE, 1),
                        )
                    )
                # 绘制方块
                box = Box(
                    node.draw.x * Canvas.BOX_SPACING,
                    i * Canvas.LAYER_SPACING,
                    node,
                    self.signal_scene,
                )
                self.scene().addItem(box)

        # 让 scene 比实际用到的面积更大一点
        rect = self.sceneRect()
        rect.adjust(-Box.WIDTH, -Box.HEIGHT, Box.WIDTH, Box.HEIGHT)
        self.setSceneRect(rect)

    def clicked_slot(self, obj: object):
        """点击信号处理。"""
        # 点击方块
        if isinstance(obj, Box):
            if self.inspected_box is not None:
                self.inspected_box.uninspect()
            self.inspected_box = obj
            self.inspected_box.inspect()
            self.view_node.emit(obj.node)
