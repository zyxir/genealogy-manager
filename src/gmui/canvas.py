"""家谱树显示区域。"""

from typing import ClassVar, Optional, Tuple

from gmlib import Card, Tree
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

from gmui.app import AppColors, AppFonts


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
    # 高亮边框
    HIGHLIGHTED_PEN: ClassVar[QPen] = QPen(AppColors.FOCUS, 3)

    # 对应的节点 ID
    id: int
    # 高亮状态
    highlighted: bool
    # 所在的画布
    canvas: "Canvas"

    def __init__(self, x: float, y: float, id: int, canvas: "Canvas"):
        super().__init__()
        self.id = id
        self.highlighted = False
        self.canvas = canvas

        # 矩形边框
        self._rect = QGraphicsRectItem(
            QRectF(-Box.WIDTH / 2, -Box.HEIGHT / 2, Box.WIDTH, Box.HEIGHT)
        )
        self._rect.setBrush(Box.NORMAL_BRUSH)
        self._rect.setPen(Box.NORMAL_PEN)

        # 文字
        self._text = QGraphicsTextItem()
        self._text.setFont(AppFonts.name_font())
        option = self._text.document().defaultTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text.document().setDefaultTextOption(option)

        # 整体设置位置
        self.addToGroup(self._rect)
        self.addToGroup(self._text)
        self.setPos(x, y)

        # 接受鼠标悬停事件
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, _: QGraphicsSceneHoverEvent):
        self._rect.setBrush(Box.HOVER_BRUSH)

    def hoverLeaveEvent(self, _: QGraphicsSceneHoverEvent):
        self._rect.setBrush(Box.NORMAL_BRUSH)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.canvas.handle_box_click(self)

    def highlight(self):
        """进入高亮状态。"""
        self.highlighted = True
        self._rect.setPen(Box.HIGHLIGHTED_PEN)

    def dehighlight(self):
        """取消高亮状态。"""
        self.highlighted = False
        self._rect.setPen(Box.NORMAL_PEN)

    def update_info(self, card: Card):
        """更新节点信息。

        用作 `core.Core.card_updated` 之槽。
        """
        # 让每个汉字占一行（暂不考虑汉字外的情况）
        self._text.setHtml("<br>".join(card.name))
        # 更新位置让文字位于方块中央
        bounding_rect = self._text.boundingRect()
        self._text.setPos(-bounding_rect.width() / 2, -bounding_rect.height() / 2)


class Canvas(QGraphicsScene):
    """画布。"""

    # 方块横向间距
    BOX_SPACING: ClassVar[float] = Box.WIDTH * 1.5
    # 层距
    LAYER_SPACING: ClassVar[float] = Box.HEIGHT * 2

    # 方块被高亮信号 (节点 ID)
    box_highlighted = Signal(int)

    # 节点 ID-方块映射
    boxes: dict[int, Box]
    # 所有连线的列表
    lines: list[QGraphicsLineItem]
    # 所有背景条的列表
    stripes: list[QGraphicsRectItem]
    # 当前高亮的方块
    highlighted_box: Optional[Box]

    def __init__(self):
        super().__init__()
        self.boxes = {}
        self.lines = []
        self.stripes = []
        self.highlighted_box = None

    def _to_canvas_xy(self, painting_x: float, index_y: float) -> Tuple[float, float]:
        """将家谱树坐标转换为画布上的坐标。

        `painting_x` 是使用 `Tree.compute_painting_xs()` 算出的绘图横坐标，
        `index_y` 是节点的纵向索引。
        """
        canvas_x = painting_x * Canvas.BOX_SPACING
        canvas_y = index_y * Canvas.LAYER_SPACING
        return (canvas_x, canvas_y)

    def sync_tree(self, tree: Tree):
        """根据更新图形。"""

        # 移除所有连线和背景条
        for line in self.lines:
            self.removeItem(line)
        self.lines = []
        for stripe in self.stripes:
            self.removeItem(stripe)
        self.stripes = []

        # 计算家谱树各节点之绘图坐标
        xs = tree.compute_painting_xs()

        # 删去不再使用的方块，并增加新方块
        tree_ids = tree.ids()
        box_ids = self.boxes.keys()
        for id, box in self.boxes.items():
            if id not in tree_ids:
                self.removeItem(box)
                del self.boxes[id]
        for id in tree_ids:
            if id not in box_ids:
                index_y, _ = tree.get_node_yx(id)
                x, y = self._to_canvas_xy(xs[id], index_y)
                box = Box(x, y, id, self)
                box.setZValue(3)
                box.update_info(tree.get_node_card(id))
                self.boxes[id] = box
                self.addItem(box)

        # 移动所有现有方块，并绘制连线
        for id, box in self.boxes.items():
            painting_x = xs[id]
            index_y, _ = tree.get_node_yx(id)
            parent_id = tree.get_node_parent_id(id)
            child_ids = tree.get_node_child_ids(id)
            # 移动方块的位置
            x, y = self._to_canvas_xy(painting_x, index_y)
            self.boxes[id].setPos(x, y)
            # 绘制向上的竖线
            if parent_id >= 0:
                x1, y1 = self._to_canvas_xy(painting_x, index_y)
                x2, y2 = self._to_canvas_xy(painting_x, index_y - 0.5)
                line = self.addLine(x1, y1, x2, y2, QPen(AppColors.LINE, 1))
                line.setZValue(2)
                self.lines.append(line)
            # 绘制向下的竖线
            if child_ids:
                x1, y1 = self._to_canvas_xy(painting_x, index_y)
                x2, y2 = self._to_canvas_xy(painting_x, index_y + 0.5)
                line = self.addLine(x1, y1, x2, y2, QPen(AppColors.LINE, 1))
                line.setZValue(2)
                self.lines.append(line)
            # 绘制横向的线
            if len(child_ids) > 1:
                lmost_id, rmost_id = child_ids[0], child_ids[-1]
                x1, y1 = self._to_canvas_xy(xs[lmost_id], index_y + 0.5)
                x2, y2 = self._to_canvas_xy(xs[rmost_id], index_y + 0.5)
                line = self.addLine(x1, y1, x2, y2, QPen(AppColors.LINE, 1))
                line.setZValue(2)
                self.lines.append(line)

        # 控制画布大小，并绘制背景条
        # index_x1 = min(xs) - 2
        # index_x2 = max(xs) + 2
        # x1, y1 = self._to_canvas_xy(index_x1, -1.5)
        # x2, y2 = self._to_canvas_xy(index_x2, tree.nlayers())
        # self.setSceneRect(QRectF(x1, y1, x2, y2))
        # for index_y in range(-1, tree.nlayers() + 1):
        #     x1, y1 = self._to_canvas_xy(index_x1, index_y - 0.5)
        #     x2, y2 = self._to_canvas_xy(index_x2, index_y + 0.5)
        #     stripe = QGraphicsRectItem(x1, y1, x2, y2)
        #     stripe.setPen(Qt.PenStyle.NoPen)
        #     if index_y % 2 == 0:
        #         stripe.setBrush(QBrush(AppColors.BG2))
        #     else:
        #         stripe.setBrush(QBrush(AppColors.BG1))
        #     stripe.setZValue(1)
        #     self.stripes.append(stripe)
        #     self.addItem(stripe)

    def handle_box_click(self, box: Box):
        """处理方块被点击事件。"""
        # 高亮该方块
        if self.highlighted_box is not None:
            self.highlighted_box.dehighlight()
        self.highlighted_box = box
        box.highlight()
        # 发送方块被高亮信号，通知其他模块协作
        self.box_highlighted.emit(box.id)

    def dehighlight_boxes(self):
        """取消高亮任何方块。"""
        if self.highlighted_box is not None:
            self.highlighted_box.dehighlight()
        self.highlighted_box = None

    def update_box_info(self, id: int, card: Card):
        """更新指定 ID 方块的信息。"""
        self.boxes[id].update_info(card)


class CanvasView(QGraphicsView):
    """画布控件，展示完整画布的一部分。"""

    # 对应的画布
    canvas: Canvas

    def __init__(self):
        super().__init__()
        self.canvas = Canvas()
        self.setScene(self.canvas)
